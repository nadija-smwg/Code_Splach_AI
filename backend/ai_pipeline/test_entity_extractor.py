"""
Phase 06 Acceptance Tests — Header Entity Extraction (Hybrid Strategy)
=======================================================================
Tests cover:
  - Commercial invoice >= 8 entities
  - Packing list >= 4 entities
  - AWB >= 5 entities
  - B/L schema coverage
  - BBox mapping correctness
  - Confidence in [0.0, 1.0]
  - Raw values NOT normalised
  - Unknown doc type safe return
  - Gemini API failure -> no crash
  - Malformed Gemini JSON -> no crash
  - map_to_bbox regression (substring, fuzzy, no-match)
  - multi-token bbox union
  - LocalExtractor unit tests
  - Phase 03-05 regression
  - End-to-end on sample PDFs
  - Telemetry fields_requested / local_extracted / gemini_* tracking
"""

import sys, os, json, time, logging

# Ensure UTF-8 output on Windows (avoid charmap codec errors with unicode chars)
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')

BACKEND = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if BACKEND not in sys.path:
    sys.path.insert(0, BACKEND)

logging.basicConfig(level=logging.WARNING)   # suppress info noise during tests

# ── helpers ───────────────────────────────────────────────────────────────────
passed = 0; failed = 0

def ok(msg):  global passed; passed += 1;  print("  [PASS]", msg)
def fail(msg): global failed; failed += 1; print("  [FAIL]", msg)
def section(t): print(f"\n{'='*62}\n  {t}\n{'='*62}")

# ── imports ───────────────────────────────────────────────────────────────────
from ai_pipeline.entity_extractor import (
    EntityExtractor, ExtractedEntity, ExtractionResult, ExtractionTelemetry,
    LocalExtractor, GeminiFallback,
    map_to_bbox, _bbox_union, _multi_token_bbox,
    ENTITY_SCHEMAS, EXTRACTION_PROMPTS, _DEFAULT_BBOX,
)
from ai_pipeline.ocr_engine import OcrOutput, OcrPage, OcrToken
from ai_pipeline.classifier import ClassificationResult, DOCUMENT_SIGNATURES

# ── builders ──────────────────────────────────────────────────────────────────

def tok(text, page=1, bbox=None, conf=0.97):
    if bbox is None:
        bbox = [0, 0, 100, 20]
    return OcrToken(text=text, page=page, bbox=bbox, confidence=conf)

def make_ocr(token_texts, file_path="test.pdf", page=1):
    tokens = [tok(t, page=page, bbox=[10, 30*i, 500, 30*i+25]) for i, t in enumerate(token_texts)]
    pg = OcrPage(page, 595, 842, tokens)
    return OcrOutput(file_path, 1, [pg])

def make_cls(doc_type, conf=0.92):
    return ClassificationResult(
        document_type=doc_type, confidence=conf,
        all_scores={doc_type: conf}, evidence=[], method="keyword"
    )


# =============================================================================
section("PHASE 03/04/05 REGRESSION")
# =============================================================================

# Phase 03 contract
t = OcrToken("Gross Weight: 450.00 KG", 1, [10, 230, 430, 300], 0.98)
if {"text","page","bbox","confidence"} <= set(t.__dataclass_fields__):
    ok("Phase03 OcrToken has correct fields")
else:
    fail("Phase03 OcrToken missing fields")

# Phase 04 contract
c = ClassificationResult("commercial_invoice", 0.95, {}, [], "keyword")
if {"document_type","confidence","all_scores","evidence","method"} <= set(c.__dataclass_fields__):
    ok("Phase04 ClassificationResult has correct fields")
else:
    fail("Phase04 ClassificationResult missing fields")

# Phase 05 map_to_bbox regression
tokens = [
    tok("Gross Weight: 450.00 KG", bbox=[100,230,430,300]),
    tok("Invoice No: INV-2026-00451", bbox=[10,10,300,40]),
]
r = map_to_bbox("450.00 KG", tokens)
if r and r.text == "Gross Weight: 450.00 KG":
    ok("map_to_bbox substring match works")
else:
    fail("map_to_bbox substring match failed: " + str(r))

r2 = map_to_bbox("INV-2026-00451", tokens)
if r2 and "INV" in r2.text:
    ok("map_to_bbox exact value match works")
else:
    fail("map_to_bbox exact match failed")

r3 = map_to_bbox("xyznotfound", tokens)
if r3 is None:
    ok("map_to_bbox returns None for no-match")
else:
    fail("map_to_bbox should return None, got: " + r3.text)

r4 = map_to_bbox("", tokens)
if r4 is None:
    ok("map_to_bbox empty string returns None")
else:
    fail("map_to_bbox empty string should return None")


# =============================================================================
section("_bbox_union TESTS")
# =============================================================================

union = _bbox_union([[10,20,100,40], [120,25,300,50]])
if union == [10,20,300,50]:
    ok(f"_bbox_union correct: {union}")
else:
    fail(f"_bbox_union wrong: {union}")

if _bbox_union([]) == _DEFAULT_BBOX:
    ok("_bbox_union([]) returns DEFAULT_BBOX")
else:
    fail("_bbox_union([]) should return DEFAULT_BBOX")


# =============================================================================
section("_multi_token_bbox TESTS")
# =============================================================================

tokens_m = [
    tok("440.00", bbox=[200,300,280,325]),
    tok("KG",     bbox=[285,300,320,325]),
    tok("Gross Weight:", bbox=[10,300,195,325]),
]
bbox, conf = _multi_token_bbox("440.00 KG", tokens_m)
if len(bbox) == 4 and bbox != _DEFAULT_BBOX:
    ok(f"_multi_token_bbox found span bbox: {bbox}")
else:
    fail(f"_multi_token_bbox failed: {bbox}")

bbox2, _ = _multi_token_bbox("", tokens_m)
if len(bbox2) == 4:
    ok("_multi_token_bbox empty value returns safe bbox")
else:
    fail("_multi_token_bbox empty value failed")


# =============================================================================
section("LOCAL EXTRACTOR UNIT TESTS")
# =============================================================================

local = LocalExtractor()

# Commercial invoice OCR tokens from sample_docs/commercial_invoice.pdf
ci_tokens = [
    tok("COMMERCIAL INVOICE"),
    tok("Invoice No: INV-2026-00451",         bbox=[10,50,300,70]),
    tok("Invoice Date: 15 September 2026",     bbox=[10,75,350,95]),
    tok("EXPORTER / SHIPPER",                  bbox=[10,100,200,120]),
    tok("Textured Jersey Lanka PLC",            bbox=[10,125,300,145]),
    tok("CONSIGNEE",                            bbox=[305,100,500,120]),
    tok("Burlington Industries Inc.",            bbox=[305,125,550,145]),
    tok("Incoterms: FOB Colombo",               bbox=[10,175,300,195]),
    tok("Payment Terms: 60 Days from B/L Date", bbox=[10,200,450,220]),
    tok("Currency: USD",                         bbox=[10,225,200,245]),
    tok("TOTAL INVOICE VALUE: USD 49,740.00",   bbox=[10,250,500,270]),
    tok("Total Gross Weight: 797.00 KG",         bbox=[10,275,400,295]),
    tok("Total Net Weight: 735.00 KG",           bbox=[10,300,400,320]),
    tok("Total Cartons: 240 Ctns",               bbox=[10,325,350,345]),
]

ci_schema = ENTITY_SCHEMAS["commercial_invoice"]
ci_result = local.extract(ci_schema, ci_tokens, "commercial_invoice")
print(f"  LocalExtractor found {len(ci_result)}/{len(ci_schema)} commercial invoice fields")
for k, (v, c, _) in ci_result.items():
    print(f"    {k}: {v!r}  (conf={c:.2f})")

if len(ci_result) >= 6:
    ok(f"Local extractor found >=6 CI fields ({len(ci_result)})")
else:
    fail(f"Local extractor only found {len(ci_result)} CI fields (need 6+)")

# Check specific key fields
if "INVOICE_NUMBER" in ci_result and "INV-2026" in ci_result["INVOICE_NUMBER"][0]:
    ok("INVOICE_NUMBER extracted correctly")
else:
    fail("INVOICE_NUMBER not extracted or wrong value: " +
         str(ci_result.get("INVOICE_NUMBER", ("MISSING",))[0]))

if "GROSS_WEIGHT" in ci_result and "797.00" in ci_result["GROSS_WEIGHT"][0]:
    ok("GROSS_WEIGHT extracted correctly")
else:
    fail("GROSS_WEIGHT not found or wrong: " +
         str(ci_result.get("GROSS_WEIGHT", ("MISSING",))[0]))

if "INCOTERM" in ci_result and "FOB" in ci_result["INCOTERM"][0]:
    ok("INCOTERM extracted correctly (FOB)")
else:
    fail("INCOTERM not found or wrong")

if "CURRENCY" in ci_result and "USD" in ci_result["CURRENCY"][0]:
    ok("CURRENCY extracted correctly")
else:
    fail("CURRENCY not found")

# Packing list tokens
pl_tokens = [
    tok("PACKING LIST"),
    tok("Total Net Weight: 735.00 KG",   bbox=[10,100,400,120]),
    tok("Total Gross Weight: 797.00 KG", bbox=[10,125,400,145]),
    tok("Total Cartons: 240 Ctns",        bbox=[10,150,350,170]),
    tok("Total Volume (CBM): 14.500 CBM", bbox=[10,175,400,195]),
    tok("Shipping Marks: TJL / BUR-8874", bbox=[10,200,450,220]),
]
pl_schema = ENTITY_SCHEMAS["packing_list"]
pl_result = local.extract(pl_schema, pl_tokens, "packing_list")
print(f"  PL local found: {list(pl_result.keys())}")
if len(pl_result) >= 3:
    ok(f"Local extractor found >=3 PL fields ({len(pl_result)})")
else:
    fail(f"Local extractor only found {len(pl_result)} PL fields")

# AWB tokens
awb_tokens = [
    tok("AIR WAYBILL"),
    tok("AWB Number: 526-1234 5678",        bbox=[10,50,350,70]),
    tok("Departure Airport: Bandaranaike Intl (CMB)", bbox=[10,75,450,95]),
    tok("Destination Airport: Los Angeles Intl (LAX)",bbox=[10,100,450,120]),
    tok("Flight No.: UL 504 / EK 215",       bbox=[10,125,350,145]),
    tok("SHIPPER",                            bbox=[10,150,150,170]),
    tok("Brandix Lanka Ltd.",                 bbox=[10,175,300,195]),
    tok("CONSIGNEE",                          bbox=[200,150,380,170]),
    tok("American Eagle Outfitters",          bbox=[200,175,480,195]),
    tok("440.00 KG",                          bbox=[10,240,200,260]),
    tok("40 Cartons",                         bbox=[10,265,200,285]),
]
awb_schema = ENTITY_SCHEMAS["awb"]
awb_result = local.extract(awb_schema, awb_tokens, "awb")
print(f"  AWB local found: {list(awb_result.keys())}")
if len(awb_result) >= 3:
    ok(f"Local extractor found >=3 AWB fields ({len(awb_result)})")
else:
    fail(f"Local extractor only found {len(awb_result)} AWB fields")


# =============================================================================
section("ENTITY_EXTRACTOR CONTRACT TESTS (no API key)")
# =============================================================================

logging.disable(logging.CRITICAL)
ext = EntityExtractor()
logging.disable(logging.NOTSET)

if ext._model is None:
    ok("EntityExtractor safe init without API key")
else:
    ok("EntityExtractor init with real Gemini API key")

# Test: unknown doc type returns empty list safely
unknown_cls = make_cls("unknown", 0.14)
unknown_ocr = make_ocr(["Some random text", "nothing relevant"])
result, tel = ext.extract(unknown_ocr, unknown_cls, "fake.pdf", "doc_unk")
if isinstance(result, ExtractionResult) and isinstance(result.entities, list):
    ok("Unknown doc type: returns ExtractionResult safely")
else:
    fail("Unknown doc type: crashed or wrong type")

if tel.fields_requested == 0 and tel.failed == 0:
    ok("Unknown doc type: telemetry zeros correctly")
else:
    fail(f"Telemetry wrong for unknown: req={tel.fields_requested} failed={tel.failed}")

# Test: empty OCR tokens
empty_ocr = OcrOutput("empty.pdf", 0, [])
empty_cls = make_cls("commercial_invoice", 0.90)
result_e, tel_e = ext.extract(empty_ocr, empty_cls, "empty.pdf", "doc_empty")
if isinstance(result_e.entities, list):
    ok("Empty OCR tokens: no crash, returns list")
else:
    fail("Empty OCR tokens: crashed")

# Test: ExtractionResult contract
dummy_entity = ExtractedEntity(
    entity_type="GROSS_WEIGHT", value="450.00 KG",
    page=1, bbox=[100,230,430,300], extraction_confidence=0.94
)
fake_result = ExtractionResult("doc_001","commercial_invoice",0.95,[dummy_entity],[])
req_keys = {"document_id","document_type","classification_confidence","entities","raw_ocr"}
d = ext.to_dict(fake_result)
if req_keys <= set(d.keys()):
    ok("to_dict has all required top-level keys")
else:
    fail("to_dict missing keys: " + str(req_keys - set(d.keys())))

ent_keys = {"entity_type","value","normalized_value","unit","page","bbox","extraction_confidence"}
if d["entities"] and ent_keys <= set(d["entities"][0].keys()):
    ok("to_dict entity dict has all required fields")
else:
    fail("Entity dict missing fields")

try:
    json.dumps(d)
    ok("to_dict is fully JSON-serialisable")
except TypeError as e:
    fail("Not JSON-serialisable: " + str(e))

# =============================================================================
section("GEMINI FAILURE / MALFORMED JSON TESTS")
# =============================================================================

# Mock a Gemini model that raises an exception
class MockFailModel:
    def generate_content(self, *a, **kw):
        raise RuntimeError("Simulated Gemini API failure")

class MockBadJsonModel:
    class FakeResp:
        text = "NOT VALID JSON {{{{ broken"
    def generate_content(self, *a, **kw):
        return self.FakeResp()

class MockGoodModel:
    class FakeResp:
        text = '{"CONSIGNEE_NAME": "Test Corp", "SHIPPER_NAME": "Ship Co"}'
    def generate_content(self, *a, **kw):
        return self.FakeResp()

gf_fail = GeminiFallback(MockFailModel())
try:
    result_fail = gf_fail.extract_missing(["CONSIGNEE_NAME"], "commercial_invoice", "fake_img")
    if isinstance(result_fail, dict):
        ok("Gemini API failure: GeminiFallback returns empty dict, no crash")
    else:
        fail("Gemini API failure: wrong return type")
except Exception as e:
    fail("Gemini API failure: CRASHED with: " + str(e))

gf_bad = GeminiFallback(MockBadJsonModel())
try:
    result_bad = gf_bad.extract_missing(["GROSS_WEIGHT"], "commercial_invoice", "fake_img")
    if isinstance(result_bad, dict):
        ok("Malformed Gemini JSON: GeminiFallback returns empty dict, no crash")
    else:
        fail("Malformed Gemini JSON: wrong return type")
except Exception as e:
    fail("Malformed Gemini JSON: CRASHED with: " + str(e))

gf_good = GeminiFallback(MockGoodModel())
result_good = gf_good.extract_missing(
    ["CONSIGNEE_NAME","SHIPPER_NAME"], "commercial_invoice", "fake_img"
)
if result_good.get("CONSIGNEE_NAME") == "Test Corp" and result_good.get("SHIPPER_NAME") == "Ship Co":
    ok("Good Gemini response: values correctly parsed")
else:
    fail("Good Gemini response: wrong values: " + str(result_good))


# =============================================================================
section("COMMERCIAL INVOICE — FULL EXTRACTION TEST (>= 8 entities)")
# =============================================================================

# Simulate realistic OCR output for commercial_invoice.pdf
ci_full_tokens = [
    tok("COMMERCIAL INVOICE",                        bbox=[100,10,500,35]),
    tok("Invoice No: INV-2026-00451",                bbox=[10,50,320,70]),
    tok("Invoice Date: 15 September 2026",           bbox=[10,75,380,95]),
    tok("EXPORTER / SHIPPER",                        bbox=[10,105,200,120]),
    tok("Textured Jersey Lanka PLC",                 bbox=[10,122,310,140]),
    tok("No. 200, Nawala Road, Narahenpita",         bbox=[10,142,370,160]),
    tok("Colombo 05, Sri Lanka",                     bbox=[10,162,280,180]),
    tok("CONSIGNEE",                                  bbox=[310,105,500,120]),
    tok("Burlington Industries Inc.",                 bbox=[310,122,550,140]),
    tok("3330 West Friendly Avenue",                  bbox=[310,142,570,160]),
    tok("Greensboro, NC 27410, USA",                  bbox=[310,162,550,180]),
    tok("Incoterms: FOB Colombo",                    bbox=[10,195,300,215]),
    tok("Payment Terms: 60 Days from B/L Date",      bbox=[10,220,480,240]),
    tok("Currency: USD",                              bbox=[310,195,450,215]),
    tok("TOTAL INVOICE VALUE: USD 49,740.00",         bbox=[10,250,510,270]),
    tok("Total Gross Weight: 797.00 KG",              bbox=[10,280,420,300]),
    tok("Total Net Weight: 735.00 KG",               bbox=[10,305,410,325]),
    tok("Total Cartons: 240 Ctns",                   bbox=[10,330,360,350]),
]

ci_ocr = OcrOutput("commercial_invoice.pdf", 1, [OcrPage(1,595,842, ci_full_tokens)])
ci_cls = make_cls("commercial_invoice", 0.97)

logging.disable(logging.CRITICAL)
ci_result, ci_tel = ext.extract(ci_ocr, ci_cls, "fake.pdf", "doc_ci")
logging.disable(logging.NOTSET)

print(f"  CI entities extracted: {len(ci_result.entities)}")
for e in ci_result.entities:
    bbox_ok = e.bbox != _DEFAULT_BBOX and e.bbox != [0,0,0,0]
    print(f"    {e.entity_type}: {e.value!r}  page={e.page} bbox={e.bbox} conf={e.extraction_confidence:.2f} bbox_mapped={'YES' if bbox_ok else 'NO'}")

if len(ci_result.entities) >= 8:
    ok(f"AC: Commercial Invoice >= 8 entities ({len(ci_result.entities)})")
else:
    fail(f"AC: Commercial Invoice only {len(ci_result.entities)} entities (need 8)")

for e in ci_result.entities:
    if not (0.0 <= e.extraction_confidence <= 1.0):
        fail(f"Confidence out of range for {e.entity_type}: {e.extraction_confidence}")
ok("All CI entity confidence scores in [0.0, 1.0]")

# No normalisation check
for e in ci_result.entities:
    if e.entity_type == "GROSS_WEIGHT":
        if "KG" in e.value:
            ok(f"GROSS_WEIGHT raw value preserved: {e.value!r}")
        else:
            fail(f"GROSS_WEIGHT value modified: {e.value!r}")
    if e.entity_type in ("INVOICE_NUMBER", "CURRENCY", "INCOTERM"):
        if e.normalized_value is not None:
            fail(f"Phase 06 must NOT set normalized_value (found on {e.entity_type})")
ok("normalized_value is None on all entities (Phase 09 responsibility)")

# Telemetry sanity
if isinstance(ci_tel, ExtractionTelemetry):
    ok(f"ExtractionTelemetry returned: fields_req={ci_tel.fields_requested}, local={ci_tel.local_extracted}, gemini_fallback={ci_tel.gemini_fallback_fields}")
else:
    fail("No ExtractionTelemetry returned")

if ci_tel.fields_requested == len(ENTITY_SCHEMAS["commercial_invoice"]):
    ok(f"Telemetry fields_requested matches schema ({ci_tel.fields_requested})")
else:
    fail(f"Telemetry fields_requested wrong: {ci_tel.fields_requested}")

if ci_tel.local_extracted + ci_tel.gemini_fallback_fields == ci_tel.fields_requested:
    ok("Telemetry: local + gemini = fields_requested")
else:
    fail(f"Telemetry split inconsistent: local={ci_tel.local_extracted} gemini={ci_tel.gemini_fallback_fields} req={ci_tel.fields_requested}")

print(f"\n  CI Hybrid Stats:\n  " + ci_tel.report().replace("\n", "\n  "))


# =============================================================================
section("PACKING LIST — FULL EXTRACTION TEST (>= 4 entities)")
# =============================================================================

pl_full_tokens = [
    tok("PACKING LIST"),
    tok("Consignee: Burlington Industries Inc.",        bbox=[10,60,450,80]),
    tok("Invoice No: INV-2026-00451",                  bbox=[10,85,320,105]),
    tok("Total Net Weight: 735.00 KG",                 bbox=[10,115,400,135]),
    tok("Total Gross Weight: 797.00 KG",               bbox=[10,140,400,160]),
    tok("Total Cartons: 240 Ctns",                     bbox=[10,165,360,185]),
    tok("Total Volume (CBM): 14.500 CBM",              bbox=[10,190,420,210]),
    tok("Shipping Marks: TJL / BUR-8874 COLOMBO",      bbox=[10,215,480,235]),
]

pl_ocr = OcrOutput("packing_list.pdf", 1, [OcrPage(1,595,842, pl_full_tokens)])
pl_cls = make_cls("packing_list", 0.95)

logging.disable(logging.CRITICAL)
pl_result, pl_tel = ext.extract(pl_ocr, pl_cls, "fake.pdf", "doc_pl")
logging.disable(logging.NOTSET)

print(f"  PL entities extracted: {len(pl_result.entities)}")
for e in pl_result.entities:
    print(f"    {e.entity_type}: {e.value!r}")

if len(pl_result.entities) >= 4:
    ok(f"AC: Packing List >= 4 entities ({len(pl_result.entities)})")
else:
    fail(f"AC: Packing List only {len(pl_result.entities)} entities (need 4)")

print(f"\n  PL Hybrid Stats:\n  " + pl_tel.report().replace("\n", "\n  "))


# =============================================================================
section("AWB — FULL EXTRACTION TEST (>= 5 entities)")
# =============================================================================

awb_full_tokens = [
    tok("AIR WAYBILL (NON-NEGOTIABLE)"),
    tok("AWB Number: 526-1234 5678",                          bbox=[10,50,380,70]),
    tok("Departure Airport: Bandaranaike Intl (CMB)",          bbox=[10,75,480,95]),
    tok("Destination Airport: Los Angeles Intl (LAX)",         bbox=[10,100,490,120]),
    tok("Flight No.: UL 504 / EK 215",                         bbox=[310,75,560,95]),
    tok("SHIPPER",                                             bbox=[10,140,120,158]),
    tok("Brandix Lanka Ltd.",                                  bbox=[10,160,280,180]),
    tok("CONSIGNEE",                                           bbox=[200,140,340,158]),
    tok("American Eagle Outfitters",                           bbox=[200,160,460,180]),
    tok("440.00",                                              bbox=[10,290,180,310]),
    tok("KG",                                                  bbox=[185,290,220,310]),
    tok("40 Cartons",                                          bbox=[10,315,220,335]),
]

awb_ocr = OcrOutput("air_waybill.pdf", 1, [OcrPage(1,595,842, awb_full_tokens)])
awb_cls = make_cls("awb", 0.96)

logging.disable(logging.CRITICAL)
awb_result, awb_tel = ext.extract(awb_ocr, awb_cls, "fake.pdf", "doc_awb")
logging.disable(logging.NOTSET)

print(f"  AWB entities extracted: {len(awb_result.entities)}")
for e in awb_result.entities:
    print(f"    {e.entity_type}: {e.value!r}")

if len(awb_result.entities) >= 5:
    ok(f"AC: AWB >= 5 entities ({len(awb_result.entities)})")
else:
    fail(f"AC: AWB only {len(awb_result.entities)} entities (need 5)")

print(f"\n  AWB Hybrid Stats:\n  " + awb_tel.report().replace("\n", "\n  "))


# =============================================================================
section("BILL OF LADING — SCHEMA COVERAGE TEST")
# =============================================================================

bl_schema = ENTITY_SCHEMAS["bl"]
if set(bl_schema) == {"BL_NUMBER","VESSEL_NAME","PORT_LOADING","PORT_DISCHARGE","GROSS_WEIGHT","PACKAGE_COUNT","CONTAINER_NUMBER"}:
    ok("B/L schema has all 7 required fields")
else:
    fail("B/L schema wrong: " + str(bl_schema))

if "bl" in EXTRACTION_PROMPTS:
    ok("B/L Gemini prompt exists")
else:
    fail("B/L Gemini prompt missing")

bl_tokens = [
    tok("BL Number: MAEU123456789",           bbox=[10,50,380,70]),
    tok("Vessel: MSC ANNA",                   bbox=[10,75,300,95]),
    tok("Port of Loading: Colombo",           bbox=[10,100,350,120]),
    tok("Port of Discharge: Felixstowe",      bbox=[10,125,380,145]),
    tok("Gross Weight: 797.00 KG",            bbox=[10,150,360,170]),
    tok("240 Cartons",                         bbox=[10,175,250,195]),
    tok("Container No: TCKU3456789",          bbox=[10,200,380,220]),
]
bl_ocr = OcrOutput("bl.pdf", 1, [OcrPage(1,595,842, bl_tokens)])
bl_cls  = make_cls("bl", 0.93)

logging.disable(logging.CRITICAL)
bl_result, bl_tel = ext.extract(bl_ocr, bl_cls, "fake.pdf", "doc_bl")
logging.disable(logging.NOTSET)

print(f"  B/L entities extracted: {len(bl_result.entities)}")
for e in bl_result.entities:
    print(f"    {e.entity_type}: {e.value!r}")

if len(bl_result.entities) >= 4:
    ok(f"B/L extraction works ({len(bl_result.entities)} entities)")
else:
    fail(f"B/L only {len(bl_result.entities)} entities")


# =============================================================================
section("BBOX CORRECTNESS TESTS")
# =============================================================================

# Every entity with a non-default bbox should match an OCR token
all_test_entities = ci_result.entities + pl_result.entities + awb_result.entities + bl_result.entities
bbox_ok_count = 0
bbox_default_count = 0
for e in all_test_entities:
    if e.bbox != _DEFAULT_BBOX and e.bbox != [0,0,0,0]:
        bbox_ok_count += 1
    else:
        bbox_default_count += 1

total_e = len(all_test_entities)
if total_e > 0:
    pct = 100 * bbox_ok_count / total_e
    if pct >= 70:
        ok(f"Bbox mapping: {bbox_ok_count}/{total_e} ({pct:.0f}%) entities have valid non-default bbox")
    else:
        fail(f"Bbox mapping too low: {bbox_ok_count}/{total_e} ({pct:.0f}%) (need >=70%)")
else:
    fail("No entities to check bbox")


# =============================================================================
section("NO NORMALISATION TESTS")
# =============================================================================

raw_cases = [
    ("450.00 KG", "GROSS_WEIGHT"),
    ("240 Ctns",  "PACKAGE_COUNT"),
    ("FOB Colombo", "INCOTERM"),
]
for raw_val, etype in raw_cases:
    tokens_n = [tok(raw_val, bbox=[10,10,200,30])]
    ocr_n = make_ocr([raw_val])
    cls_n = make_cls("commercial_invoice")
    logging.disable(logging.CRITICAL)
    res_n, _ = ext.extract(ocr_n, cls_n, "fake.pdf")
    logging.disable(logging.NOTSET)
    found = next((e for e in res_n.entities if e.entity_type == etype), None)
    if found:
        if found.normalized_value is None and found.unit is None:
            ok(f"No normalisation: {etype}={found.value!r} — normalized_value=None, unit=None")
        else:
            fail(f"Phase 06 set normalized_value/unit on {etype}: nv={found.normalized_value} unit={found.unit}")
    # Not a failure if field not found — normalisation test is still ok for fields that ARE found


# =============================================================================
section("END-TO-END TEST ON SAMPLE PDFs")
# =============================================================================

SAMPLE_DIR = os.path.join(BACKEND, "sample_docs")
sample_files = {
    "commercial_invoice": os.path.join(SAMPLE_DIR, "commercial_invoice.pdf"),
    "packing_list":       os.path.join(SAMPLE_DIR, "packing_list.pdf"),
    "awb":                os.path.join(SAMPLE_DIR, "air_waybill.pdf"),
}

# We need PaddleOCR + classifier for true E2E
try:
    from ai_pipeline.ocr_engine import OcrEngine
    from ai_pipeline.classifier import DocumentClassifier
    ocr_engine = OcrEngine()
    classifier = DocumentClassifier()
    HAS_OCR = True
    print("  OCR engine loaded -- running true end-to-end")
except Exception as e:
    HAS_OCR = False
    print(f"  OCR engine unavailable ({e}) -- skipping true E2E, using synthetic tokens")

if HAS_OCR:
    for doc_type, pdf_path in sample_files.items():
        if not os.path.exists(pdf_path):
            print(f"  [SKIP] {pdf_path} not found")
            continue
        t0 = time.time()
        try:
            logging.disable(logging.CRITICAL)
            ocr_out = ocr_engine.extract(pdf_path)
            cls_out = classifier.classify(ocr_out, pdf_path=pdf_path)
            e2e_result, e2e_tel = ext.extract(ocr_out, cls_out, pdf_path, f"e2e_{doc_type}")
            logging.disable(logging.NOTSET)
            elapsed = time.time() - t0

            print(f"\n  ── {os.path.basename(pdf_path)} ──")
            print(f"  Document type:           {cls_out.document_type}")
            print(f"  Classification conf:     {cls_out.confidence:.2%}")
            print(f"  Entities extracted:      {len(e2e_result.entities)}")
            for e in e2e_result.entities:
                bbox_flag = '' if (e.bbox and e.bbox != _DEFAULT_BBOX) else ' [no bbox]'
                print(f"    {e.entity_type}: {e.value!r}  conf={e.extraction_confidence:.2f}{bbox_flag}")
            print(f"  Local extraction:        {e2e_tel.local_extracted}")
            print(f"  Gemini fallback:         {e2e_tel.gemini_fallback_fields}")
            print(f"  Gemini calls:            {e2e_tel.gemini_calls}")
            print(f"  Failed:                  {e2e_tel.failed}")
            print(f"  Elapsed:                 {elapsed:.2f}s")

            if len(e2e_result.entities) >= 1:
                ok(f"E2E: {doc_type} extracted {len(e2e_result.entities)} entities in {elapsed:.1f}s")
            else:
                fail(f"E2E: {doc_type} extracted 0 entities")

        except Exception as ex:
            logging.disable(logging.NOTSET)
            fail(f"E2E CRASHED on {doc_type}: {ex}")
else:
    print("  [SKIP] End-to-end test skipped (no OCR engine)")

# =============================================================================
section("SCHEMA COVERAGE AND PROMPT COMPLETENESS")
# =============================================================================

required_doc_types = ["commercial_invoice", "packing_list", "awb", "bl"]
for dt in required_doc_types:
    if dt in ENTITY_SCHEMAS and dt in EXTRACTION_PROMPTS:
        ok(f"Schema + prompt both exist for: {dt}")
    else:
        fail(f"Missing schema or prompt for: {dt}")

ci_count = len(ENTITY_SCHEMAS["commercial_invoice"])
if ci_count >= 12:
    ok(f"Commercial Invoice schema has {ci_count} fields")
else:
    fail(f"CI schema has only {ci_count} fields (need 12)")

# Verify entity key names match downstream exactly
critical_keys = ["GROSS_WEIGHT", "NET_WEIGHT", "PACKAGE_COUNT",
                 "CONSIGNEE_NAME", "SHIPPER_NAME", "INCOTERM"]
for key in critical_keys:
    found = any(key in ENTITY_SCHEMAS[dt] for dt in ["commercial_invoice","packing_list","awb","bl"])
    if found:
        ok(f"Critical conflict field {key} present in at least one schema")
    else:
        fail(f"Critical conflict field {key} MISSING from all schemas")


# =============================================================================
section("SUMMARY")
# =============================================================================
total = passed + failed
print(f"\n  Passed: {passed}/{total}")
if failed:
    print(f"  FAILED: {failed}/{total}")
    sys.exit(1)
else:
    print("\n  All Phase 06 acceptance criteria PASSED")
    sys.exit(0)
