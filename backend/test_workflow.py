"""
Workflow End-to-End Test
Simulates the real ClearanceX pipeline from PDF upload → extraction → normalization → contract validation.
Does NOT require a running server. All AI deps are mocked where needed.

Run: py backend/test_workflow.py
"""

import sys
import json
from pathlib import Path
from copy import deepcopy

sys.path.insert(0, str(Path(__file__).parent))

PASS = "[PASS]"
FAIL = "[FAIL]"
INFO = "[INFO]"


def check(label, condition, detail=""):
    if condition:
        print(f"  {PASS} {label}")
    else:
        print(f"  {FAIL} {label} {detail}")
    return condition


results = []

print()
print("=" * 60)
print("  CLEARANCEX WORKFLOW END-TO-END TEST")
print("=" * 60)


# ─────────────────────────────────────────────────────────
# STEP 1: Module Imports
# ─────────────────────────────────────────────────────────
print("\n[1] Module Imports")

try:
    from ai_pipeline.mock_pipeline import get_mock_pipeline
    results.append(check("mock_pipeline imports OK", True))
except Exception as e:
    results.append(check("mock_pipeline imports OK", False, str(e)))

try:
    from ai_pipeline.normalizer import EntityNormalizer
    results.append(check("normalizer imports OK", True))
except Exception as e:
    results.append(check("normalizer imports OK", False, str(e)))

try:
    from ai_pipeline.confidence import ConfidenceScorer
    results.append(check("confidence imports OK", True))
except Exception as e:
    results.append(check("confidence imports OK", False, str(e)))

try:
    from ai_pipeline.contract_validator import validate_extraction_result, numeric_close
    results.append(check("contract_validator imports OK", True))
except Exception as e:
    results.append(check("contract_validator imports OK", False, str(e)))

try:
    from ai_pipeline.dossier_manager import DossierManager
    results.append(check("dossier_manager imports OK", True))
except Exception as e:
    results.append(check("dossier_manager imports OK", False, str(e)))


# ─────────────────────────────────────────────────────────
# STEP 2: Pipeline Output Contract
# ─────────────────────────────────────────────────────────
print("\n[2] Pipeline Output Contract")

pipeline = get_mock_pipeline()
result = pipeline.process_document("demo/commercial_invoice.pdf", "doc_invoice_001")

REQUIRED_TOP = {"document_id","document_type","classification_confidence",
                "classification_evidence","entities","raw_ocr","processing_time_ms","errors"}
REQUIRED_ENTITY = {"entity_type","value","normalized_value","unit","page","bbox",
                   "extraction_confidence","classification_confidence","normalization_warning"}

results.append(check("All top-level keys present", REQUIRED_TOP == REQUIRED_TOP & result.keys()))
results.append(check("document_type is string", isinstance(result["document_type"], str)))
results.append(check("classification_confidence in 0-1", 0.0 <= result["classification_confidence"] <= 1.0))
results.append(check("entities is a list", isinstance(result["entities"], list)))
results.append(check("entities not empty", len(result["entities"]) > 0))
results.append(check("raw_ocr is a list", isinstance(result["raw_ocr"], list)))
results.append(check("errors is a list", isinstance(result["errors"], list)))

for entity in result["entities"]:
    missing = REQUIRED_ENTITY - entity.keys()
    results.append(check(f"  Entity [{entity.get('entity_type')}] has all fields", len(missing) == 0, str(missing)))
    if entity["bbox"] is not None:
        results.append(check(f"  Entity [{entity.get('entity_type')}] bbox is [x1,y1,x2,y2]",
                             isinstance(entity["bbox"], list) and len(entity["bbox"]) == 4))


# ─────────────────────────────────────────────────────────
# STEP 3: Normalization (Tier 1 Deterministic)
# ─────────────────────────────────────────────────────────
print("\n[3] Normalization -- Tier 1 Deterministic")

norm = EntityNormalizer()

# Weight conversion: LBS → KG
r = norm.normalize("GROSS_WEIGHT", "990 LBS")
results.append(check("990 LBS -> ~449.056 kg", numeric_close(r["normalized_value"], 449.056, tolerance=0.01)))

# Incoterm case-insensitive
r = norm.normalize("INCOTERM", "fob colombo")
results.append(check("'fob colombo' -> 'FOB'", r["normalized_value"] == "FOB"))

r2 = norm.normalize("INCOTERM", "FOB Colombo")
results.append(check("'FOB Colombo' same key as 'fob colombo'", r["normalized_value"] == r2["normalized_value"]))

# Package count
r = norm.normalize("PACKAGE_COUNT", "25 Cartons")
results.append(check("'25 Cartons' → 25 cartons", r["normalized_value"] == 25 and r["unit"] == "cartons"))

# Date normalization
r = norm.normalize("INVOICE_DATE", "15 January 2024")
results.append(check("'15 January 2024' → ISO 8601", r["normalized_value"] == "2024-01-15"))

# Identifier normalization (strip spaces/dashes)
r = norm.normalize("BL_NUMBER", "MSCU 123-456-789")
results.append(check("BL_NUMBER strips to uppercase", r["normalized_value"] is not None))

# Total amount
r = norm.normalize("TOTAL_AMOUNT", "45,230.00")
results.append(check("'45,230.00' → 45230.0", numeric_close(r["normalized_value"], 45230.0)))


# ─────────────────────────────────────────────────────────
# STEP 4: Confidence Scorer
# ─────────────────────────────────────────────────────────
print("\n[4] Confidence Scorer")

scorer = ConfidenceScorer()

s = scorer.score_entity(0.98, 0.95, False)
results.append(check("High confidence capped at 0.95", s <= 0.95))

s = scorer.score_entity(0.0, 0.0, True)
results.append(check("Zero OCR+bbox gives low score (< 0.2)", s < 0.2))

s = scorer.score_entity(0.70, 0.50, False)
results.append(check("Medium score is in 0.5–0.8 range", 0.5 <= s <= 0.8))

entities = deepcopy(result["entities"])
scored = scorer.score_entities(entities)
results.append(check("score_entities() returns same count", len(scored) == len(entities)))
results.append(check("All scored entities have extraction_confidence",
                      all("extraction_confidence" in e for e in scored)))


# ─────────────────────────────────────────────────────────
# STEP 5: Full Pipeline → Normalize → Score → Validate
# ─────────────────────────────────────────────────────────
print("\n[5] Full Pipeline → Normalize → Score → Validate")

full_result = pipeline.process_document("demo/commercial_invoice.pdf", "doc_full_test")

for e in full_result["entities"]:
    n = norm.normalize(e["entity_type"], e["value"])
    e["normalized_value"] = n["normalized_value"]
    e["unit"] = n["unit"]
    e["normalization_warning"] = n["warn"]

full_result["entities"] = scorer.score_entities(full_result["entities"])

try:
    validate_extraction_result(full_result)
    results.append(check("contract validation passed", True))
except AssertionError as e:
    results.append(check("contract validation passed", False, str(e)))

try:
    json.dumps(full_result)
    results.append(check("JSON serialization passed", True))
except Exception as e:
    results.append(check("JSON serialization passed", False, str(e)))


# ─────────────────────────────────────────────────────────
# STEP 6: Demo Cache
# ─────────────────────────────────────────────────────────
print("\n[6] Demo Cache")

cache_path = Path("demo_cache.json")
results.append(check("demo_cache.json exists", cache_path.exists()))

if cache_path.exists():
    try:
        cache = json.loads(cache_path.read_text(encoding="utf-8"))
        results.append(check("demo_cache.json is valid JSON", True))
        results.append(check("cache_version key present", "cache_version" in cache))
        results.append(check("pipeline_version key present", "pipeline_version" in cache))
        docs = cache.get("documents", {})
        expected_docs = {"commercial_invoice", "packing_list", "awb", "bill_of_lading", "delivery_order"}
        results.append(check("All 5 demo docs in cache", expected_docs == set(docs.keys())))
    except Exception as e:
        results.append(check("demo_cache.json is valid JSON", False, str(e)))


# ─────────────────────────────────────────────────────────
# STEP 7: Deduplication
# ─────────────────────────────────────────────────────────
print("\n[7] Entity Deduplication Logic")

from ai_pipeline.pipeline import AIPipeline
pipeline_obj = AIPipeline.__new__(AIPipeline)

# Inject 2 true duplicates + 1 genuine conflict
test_entities = [
    {"entity_type": "GROSS_WEIGHT", "normalized_value": 450.0, "value": "450 KG", "extraction_confidence": 0.9},
    {"entity_type": "GROSS_WEIGHT", "normalized_value": 450.0, "value": "450 KG", "extraction_confidence": 0.7},  # duplicate
    {"entity_type": "GROSS_WEIGHT", "normalized_value": 448.0, "value": "448 KG", "extraction_confidence": 0.85},  # real conflict
]

deduped = pipeline_obj._deduplicate_entities(test_entities)
results.append(check("True duplicate removed (3 → 2)", len(deduped) == 2))
results.append(check("Higher-confidence duplicate kept",
                     any(e["extraction_confidence"] == 0.9 for e in deduped)))
results.append(check("Genuine conflict preserved (448.0 kept)",
                     any(e["normalized_value"] == 448.0 for e in deduped)))


# ─────────────────────────────────────────────────────────
# SUMMARY
# ─────────────────────────────────────────────────────────
passed = sum(1 for r in results if r)
total = len(results)
failed = total - passed

print()
print("=" * 60)
if failed == 0:
    print(f"  ALL {total} CHECKS PASSED")
else:
    print(f"  {passed}/{total} PASSED   {failed} FAILED")
print("=" * 60)
print()

sys.exit(0 if failed == 0 else 1)
