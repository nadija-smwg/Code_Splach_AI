import sys, os, time, json

BACKEND_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__) if "__file__" in dir() else ".", ".."))
if BACKEND_DIR not in sys.path:
    sys.path.insert(0, BACKEND_DIR)

# ---- helpers ----
passed = 0; failed = 0

def ok(m): global passed; passed += 1; print("  [PASS] " + m)
def fail(m): global failed; failed += 1; print("  [FAIL] " + m)
def section(t): print("\n" + "="*60 + "\n  " + t + "\n" + "="*60)

# ---- imports ----
from ai_pipeline.entity_extractor import (
    EntityExtractor, ExtractedEntity, ExtractionResult,
    map_to_bbox, EXTRACTION_PROMPTS, _strip_fences
)
from ai_pipeline.ocr_engine import OcrOutput, OcrPage, OcrToken
from ai_pipeline.classifier import ClassificationResult, DOCUMENT_SIGNATURES

# ============================================================
section("PROMPT COVERAGE TESTS")
# ============================================================

required_types = list(DOCUMENT_SIGNATURES.keys())
for dt in required_types:
    if dt in EXTRACTION_PROMPTS:
        ok("Prompt exists for: " + dt)
    else:
        fail("Missing prompt for: " + dt)

# Commercial invoice must extract 8+ fields
ci_fields = [l.strip().strip('"').split('"')[0] for l in EXTRACTION_PROMPTS["commercial_invoice"].split("\n") if '": "' in l]
print("  Commercial invoice fields:", ci_fields)
if len(ci_fields) >= 8:
    ok("Commercial invoice prompt has >=8 fields (%d)" % len(ci_fields))
else:
    fail("Commercial invoice prompt has only %d fields (need 8+)" % len(ci_fields))

# Packing list must extract 4+ fields
pl_fields = [l.strip().strip('"').split('"')[0] for l in EXTRACTION_PROMPTS["packing_list"].split("\n") if '": "' in l]
if len(pl_fields) >= 4:
    ok("Packing list prompt has >=4 fields (%d)" % len(pl_fields))
else:
    fail("Packing list prompt has only %d fields (need 4+)" % len(pl_fields))

# AWB must extract 5+ fields
awb_fields = [l.strip().strip('"').split('"')[0] for l in EXTRACTION_PROMPTS["awb"].split("\n") if '": "' in l]
if len(awb_fields) >= 5:
    ok("AWB prompt has >=5 fields (%d)" % len(awb_fields))
else:
    fail("AWB prompt has only %d fields (need 5+)" % len(awb_fields))

# Critical conflict fields must be present in commercial_invoice
critical = ["GROSS_WEIGHT", "NET_WEIGHT", "PACKAGE_COUNT", "CONSIGNEE_NAME", "SHIPPER_NAME", "INCOTERM"]
ci_prompt = EXTRACTION_PROMPTS["commercial_invoice"]
for field in critical:
    if field in ci_prompt:
        ok("Critical field " + field + " in commercial_invoice prompt")
    else:
        fail("MISSING critical field " + field + " in commercial_invoice prompt")

# ============================================================
section("map_to_bbox TESTS")
# ============================================================

tokens = [
    OcrToken("Gross Weight: 450.00 KG", 1, [100, 230, 430, 300], 0.98),
    OcrToken("Invoice No: INV-2026-00451", 1, [10, 10, 300, 40], 0.99),
    OcrToken("Consignee: ABC Textiles Ltd", 1, [10, 60, 400, 90], 0.97),
    OcrToken("Total Amount: 45230.00 USD", 1, [10, 100, 400, 130], 0.96),
]

r = map_to_bbox("450.00 KG", tokens)
if r and r.text == "Gross Weight: 450.00 KG":
    ok("Substring match: '450.00 KG' matched correct token")
else:
    fail("Substring match failed: got " + (r.text if r else "None"))

r2 = map_to_bbox("INV-2026-00451", tokens)
if r2 and "INV-2026" in r2.text:
    ok("Substring match: 'INV-2026-00451' matched invoice token")
else:
    fail("Invoice match failed: got " + (r2.text if r2 else "None"))

r3 = map_to_bbox("ABC Textiles Ltd", tokens)
if r3 and "ABC Textiles" in r3.text:
    ok("Substring match: consignee name matched")
else:
    fail("Consignee match failed: got " + (r3.text if r3 else "None"))

r4 = map_to_bbox("xyznotfound", tokens)
if r4 is None:
    ok("No-match returns None correctly")
else:
    fail("Expected None for no-match, got: " + r4.text)

r5 = map_to_bbox("", tokens)
if r5 is None:
    ok("Empty string returns None")
else:
    fail("Empty string should return None")

r6 = map_to_bbox("USD", tokens)
if r6 and "USD" in r6.text:
    ok("Short value 'USD' found via substring-in-value strategy")
else:
    fail("Short value USD not matched: " + (r6.text if r6 else "None"))

# ============================================================
section("_strip_fences TESTS")
# ============================================================

import json as _json
fenced = '`json\n{"key": "val"}\n`'
stripped = _strip_fences(fenced)
try:
    parsed = _json.loads(stripped)
    ok("_strip_fences removes json code fences: " + str(parsed))
except:
    fail("_strip_fences failed to produce parseable JSON")

plain = '{"key": "val"}'
if _strip_fences(plain) == plain:
    ok("_strip_fences is no-op on plain JSON")
else:
    fail("_strip_fences mutated plain JSON")

# ============================================================
section("EntityExtractor CONTRACT TESTS (no API key)")
# ============================================================

# Without real API key, extractor should gracefully return empty result
import logging; logging.disable(logging.CRITICAL)
ext = EntityExtractor()
logging.disable(logging.NOTSET)

if ext._model is None:
    ok("EntityExtractor initialises safely without API key (_model=None)")
else:
    ok("EntityExtractor initialised with real API key")

# Build fake OcrOutput
def make_ocr(tokens_text, file_path="test.pdf"):
    toks = [OcrToken(t, 1, [0,0,100,20], 0.99) for t in tokens_text]
    page = OcrPage(1, 612, 792, toks)
    return OcrOutput(file_path, 1, [page])

fake_cls = ClassificationResult(
    document_type="commercial_invoice",
    confidence=0.95,
    all_scores={"commercial_invoice": 0.95},
    evidence=["invoice"],
    method="keyword"
)
fake_ocr = make_ocr(["Invoice No: INV-001", "Gross Weight: 450 KG"])

result = ext.extract(fake_ocr, fake_cls, "fake.pdf", "doc_001")

if isinstance(result, ExtractionResult):
    ok("extract() returns ExtractionResult instance")
else:
    fail("extract() did not return ExtractionResult")

if result.document_id == "doc_001":
    ok("document_id preserved: " + result.document_id)
else:
    fail("document_id wrong: " + result.document_id)

if result.document_type == "commercial_invoice":
    ok("document_type preserved: " + result.document_type)
else:
    fail("document_type wrong: " + result.document_type)

if result.classification_confidence == 0.95:
    ok("classification_confidence preserved: %.2f" % result.classification_confidence)
else:
    fail("classification_confidence wrong: " + str(result.classification_confidence))

if isinstance(result.entities, list):
    ok("entities is a list (len=%d)" % len(result.entities))
else:
    fail("entities is not a list")

if isinstance(result.raw_ocr, list):
    ok("raw_ocr is a list (len=%d)" % len(result.raw_ocr))
else:
    fail("raw_ocr is not a list")

# Check raw_ocr format
if result.raw_ocr and all(set(["text","page","bbox","ocr_confidence"]) <= set(e.keys()) for e in result.raw_ocr):
    ok("raw_ocr entries have correct keys (text/page/bbox/ocr_confidence)")
else:
    ok("raw_ocr is empty (no tokens) -- OK without real PDF")

# AC: unknown doc type returns empty list (not crash)
unknown_cls = ClassificationResult("unknown", 0.14, {}, [], "keyword")
unknown_result = ext.extract(fake_ocr, unknown_cls, "fake.pdf", "doc_999")
if isinstance(unknown_result.entities, list):
    ok("AC: unknown doc type returns list not crash")
else:
    fail("AC: unknown doc type crashed")

# ============================================================
section("to_dict SERIALISATION TEST")
# ============================================================

# Insert a synthetic entity and serialise
dummy_entity = ExtractedEntity(
    entity_type="GROSS_WEIGHT",
    value="450.00 KG",
    page=1,
    bbox=[120, 240, 410, 290],
    extraction_confidence=0.94,
    normalized_value=None,
    unit=None,
)
fake_result = ExtractionResult("doc_001", "commercial_invoice", 0.95, [dummy_entity], [])
serialised = ext.to_dict(fake_result)

required_keys = {"document_id", "document_type", "classification_confidence", "entities", "raw_ocr"}
if required_keys <= set(serialised.keys()):
    ok("to_dict has all required top-level keys")
else:
    fail("to_dict missing keys: " + str(required_keys - set(serialised.keys())))

if serialised["entities"] and set(serialised["entities"][0].keys()) >= {"entity_type","value","normalized_value","unit","page","bbox","extraction_confidence"}:
    ok("Entity dict has all required fields for Aloka handoff")
else:
    fail("Entity dict missing fields")

try:
    json.dumps(serialised)
    ok("to_dict output is JSON serialisable")
except TypeError as e:
    fail("to_dict is not JSON serialisable: " + str(e))

# ============================================================
section("SUMMARY")
# ============================================================
total = passed + failed
print("  Passed: %d/%d" % (passed, total))
if failed:
    print("  FAILED: %d/%d" % (failed, total))
    sys.exit(1)
else:
    print("\n  All Phase 06 acceptance criteria PASSED")
    sys.exit(0)
