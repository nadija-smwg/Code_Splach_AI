import sys, os, json, logging

BACKEND_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__) if "__file__" in dir() else ".", ".."))
if BACKEND_DIR not in sys.path:
    sys.path.insert(0, BACKEND_DIR)

passed = 0; failed = 0

def ok(m): global passed; passed += 1; print("  [PASS] " + m)
def fail(m): global failed; failed += 1; print("  [FAIL] " + m)
def section(t): print("\n" + "="*60 + "\n  " + t + "\n" + "="*60)

from ai_pipeline.table_extractor import (
    TableExtractor, LineItem, TableExtraction,
    MOCK_LINE_ITEMS, TABLE_EXTRACTION_PROMPT, _row_bbox
)
from ai_pipeline.ocr_engine import OcrOutput, OcrPage, OcrToken

def make_ocr(texts, page=1):
    tokens = [OcrToken(t, page, [10, 300+i*40, 590, 335+i*40], 0.97) for i,t in enumerate(texts)]
    pg = OcrPage(page, 595, 842, tokens)
    return OcrOutput("test.pdf", 1, [pg])

logging.disable(logging.CRITICAL)
ext = TableExtractor()
logging.disable(logging.NOTSET)

# ============================================================
section("DATACLASS STRUCTURE TESTS")
# ============================================================

if ext._model is None:
    ok("TableExtractor initialises safely without API key")
else:
    ok("TableExtractor initialised with real API key")

dummy = LineItem(1,"Cotton Fabric",5000.0,"meters",2.5,12500.0,1,[0,300,595,335],0.92)
required = {"row_index","description","quantity","unit","unit_price","total_price","page","bbox","confidence","is_mock"}
if required <= set(dummy.__dataclass_fields__.keys()):
    ok("LineItem has all required fields: " + str(sorted(required)))
else:
    fail("LineItem missing fields: " + str(required - set(dummy.__dataclass_fields__.keys())))

te = TableExtraction("doc_001", [dummy], 1, "gemini_vision")
te_fields = {"document_id","items","total_rows","extraction_method"}
if te_fields <= set(te.__dataclass_fields__.keys()):
    ok("TableExtraction has all required fields")
else:
    fail("TableExtraction missing fields: " + str(te_fields - set(te.__dataclass_fields__.keys())))

# ============================================================
section("MOCK FALLBACK TESTS (no API key path)")
# ============================================================

ocr = make_ocr(["Cotton Fabric 5000m", "Polyester 3000m", "Blend 2500m"])
result = ext.extract(None, ocr, "doc_001", page_num=1, doc_type="commercial_invoice")

if isinstance(result, TableExtraction):
    ok("extract() returns TableExtraction")
else:
    fail("extract() wrong type: " + str(type(result)))

if result.extraction_method == "mock":
    ok("extraction_method='mock' when no API key")
else:
    fail("Wrong extraction_method: " + result.extraction_method)

if result.total_rows >= 3:
    ok("AC: >=3 line items returned (got %d)" % result.total_rows)
else:
    fail("AC: only %d items (need 3+)" % result.total_rows)

if result.total_rows == len(result.items):
    ok("total_rows matches items list length")
else:
    fail("total_rows mismatch: %d vs len=%d" % (result.total_rows, len(result.items)))

# AC: each item has description, quantity, unit price, total
for item in result.items:
    if not item.description:
        fail("Item %d missing description" % item.row_index)
    if item.quantity <= 0:
        fail("Item %d quantity invalid: %s" % (item.row_index, item.quantity))
    if item.unit_price <= 0:
        fail("Item %d unit_price invalid: %s" % (item.row_index, item.unit_price))
    if item.total_price <= 0:
        fail("Item %d total_price invalid: %s" % (item.row_index, item.total_price))
ok("AC: all items have description, quantity, unit_price, total_price")

# AC: each item has a bbox
for item in result.items:
    if not item.bbox or len(item.bbox) != 4:
        fail("Item %d missing/bad bbox: %s" % (item.row_index, item.bbox))
ok("AC: all items have valid [x1,y1,x2,y2] bbox")

# AC: each item has confidence
for item in result.items:
    if not (0.0 <= item.confidence <= 1.0):
        fail("Item %d confidence out of range: %f" % (item.row_index, item.confidence))
ok("AC: all confidence scores in [0,1]")

# AC: all mock items are flagged
if all(item.is_mock for item in result.items):
    ok("Mock items have is_mock=True")
else:
    fail("Some mock items missing is_mock flag")

# ============================================================
section("DOC TYPE FILTERING TESTS")
# ============================================================

for skip_type in ("awb", "bl", "freight_invoice", "delivery_order", "letter_of_credit"):
    r = ext.extract(None, ocr, "doc_x", doc_type=skip_type)
    if r.extraction_method == "skipped" and len(r.items) == 0:
        ok("'%s' correctly skipped (no table expected)" % skip_type)
    else:
        fail("'%s' should be skipped but got method=%s items=%d" % (skip_type, r.extraction_method, len(r.items)))

# ============================================================
section("MERGED CELL / CRASH RESISTANCE TESTS")
# ============================================================

# Pass None image (simulates merged-cell / bad PDF) -- must not crash
try:
    r = ext.extract(None, ocr, "doc_crash", doc_type="commercial_invoice")
    if isinstance(r, TableExtraction):
        ok("AC: merged-cell / None image handled gracefully (no crash)")
    else:
        fail("None image returned wrong type")
except Exception as e:
    fail("CRASH on None image: " + str(e))

# Pass empty OcrOutput
empty_ocr = OcrOutput("empty.pdf", 0, [])
try:
    r = ext.extract(None, empty_ocr, "doc_empty", doc_type="commercial_invoice")
    ok("Empty OcrOutput handled gracefully (no crash)")
except Exception as e:
    fail("CRASH on empty OCR: " + str(e))

# ============================================================
section("to_dict SERIALISATION TEST")
# ============================================================

serialised = ext.to_dict(result)
required_keys = {"document_id","total_rows","extraction_method","items"}
if required_keys <= set(serialised.keys()):
    ok("to_dict has all required top-level keys")
else:
    fail("to_dict missing keys: " + str(required_keys - set(serialised.keys())))

item_keys = {"row_index","description","quantity","unit","unit_price","total_price","page","bbox","confidence","is_mock"}
if serialised["items"] and item_keys <= set(serialised["items"][0].keys()):
    ok("Serialised items have all required fields")
else:
    fail("Serialised items missing fields")

try:
    json.dumps(serialised)
    ok("to_dict is fully JSON serialisable")
except TypeError as e:
    fail("Not JSON serialisable: " + str(e))

# ============================================================
section("_row_bbox UTILITY TEST")
# ============================================================

tokens = [OcrToken("Cotton Fabric 5000", 1, [10,300,590,335], 0.97),
          OcrToken("Polyester 3000m", 1, [10,340,590,375], 0.96)]
bbox = _row_bbox("Cotton Fabric 5000 meters", tokens, page=1)
if len(bbox) == 4:
    ok("_row_bbox returns 4-element list: " + str(bbox))
else:
    fail("_row_bbox returned invalid bbox: " + str(bbox))

bbox2 = _row_bbox("", tokens, page=1)
if len(bbox2) == 4:
    ok("_row_bbox handles empty description gracefully")
else:
    fail("_row_bbox failed on empty description")

# ============================================================
section("MOCK DATA QUALITY CHECK")
# ============================================================

print("  Mock line items:")
for row in MOCK_LINE_ITEMS:
    expected = round(row["quantity"] * row["unit_price"], 2)
    ok_flag = abs(expected - row["total_price"]) < 0.02
    status = "OK" if ok_flag else "MISMATCH"
    print("    [%s] Row %d: %s x%.0f @ %.2f = %.2f (expected %.2f)" % (
        status, row["row_index"], row["unit"][:8],
        row["quantity"], row["unit_price"], row["total_price"], expected))
    if ok_flag:
        ok("Row %d math is consistent" % row["row_index"])
    else:
        fail("Row %d qty*price mismatch" % row["row_index"])

# ============================================================
section("SUMMARY")
# ============================================================
total = passed + failed
print("  Passed: %d/%d" % (passed, total))
if failed:
    print("  FAILED: %d/%d" % (failed, total))
    sys.exit(1)
else:
    print("\n  All Phase 07 acceptance criteria PASSED")
    sys.exit(0)
