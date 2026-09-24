"""
Phase 08 Acceptance Tests — Counterfactual Generator
======================================================
Covers all spec acceptance criteria:
  - Every discrepancy gets >= 1 option
  - Numeric conflicts: what each doc's value would need to become
  - Text conflicts: exact string resolution
  - Internal conflicts: net + tare = gross explanation
  - Document names + values referenced in options
  - Domain recommendations included
  - Max 4 options per discrepancy
  - Output matches Kaveen's Counterfactual interface
  - generate_batch() populates discrepancy["counterfactual"] in-place
  - Unknown / edge-case discrepancies don't crash
"""

import sys, os, json

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

passed = 0; failed = 0

def ok(m):  global passed; passed += 1;  print("  [PASS]", m)
def fail(m): global failed; failed += 1; print("  [FAIL]", m)
def section(t): print(f"\n{'='*60}\n  {t}\n{'='*60}")

from reasoning.counterfactual import CounterfactualGenerator

gen = CounterfactualGenerator()


# =============================================================================
section("IMPORT + STRUCTURE")
# =============================================================================

if hasattr(gen, "generate") and hasattr(gen, "generate_batch"):
    ok("CounterfactualGenerator has generate() and generate_batch()")
else:
    fail("Missing generate() or generate_batch()")

if len(gen.DOMAIN_RECOMMENDATIONS) >= 10:
    ok(f"DOMAIN_RECOMMENDATIONS has {len(gen.DOMAIN_RECOMMENDATIONS)} entries")
else:
    fail(f"Too few domain recommendations: {len(gen.DOMAIN_RECOMMENDATIONS)}")


# =============================================================================
section("OUTPUT CONTRACT / FORMAT TESTS")
# =============================================================================

disc_numeric = {
    "field": "GROSS_WEIGHT",
    "conflict_type": "numeric_variance",
    "sources": [
        {"document_type": "packing_list",      "value": "797.00 KG"},
        {"document_type": "commercial_invoice", "value": "450.00 KG"},
    ]
}

result = gen.generate(disc_numeric)

if isinstance(result, dict):
    ok("generate() returns dict")
else:
    fail("generate() should return dict, got: " + str(type(result)))

if "options" in result and "recommendation" in result:
    ok("Output has 'options' and 'recommendation' keys (Kaveen interface)")
else:
    fail("Output missing required keys: " + str(result.keys()))

if isinstance(result["options"], list):
    ok("options is a list")
else:
    fail("options should be a list")

if isinstance(result["recommendation"], str) and len(result["recommendation"]) > 10:
    ok("recommendation is a non-empty string")
else:
    fail("recommendation is missing or too short")

try:
    json.dumps(result)
    ok("Output is fully JSON-serialisable")
except TypeError as e:
    fail("Not JSON-serialisable: " + str(e))


# =============================================================================
section("NUMERIC VARIANCE TESTS")
# =============================================================================

result_n = gen.generate(disc_numeric)
options = result_n["options"]
print(f"  Numeric options ({len(options)}):")
for o in options: print("   ", o)

if len(options) >= 1:
    ok(f"AC: >= 1 counterfactual option for numeric conflict ({len(options)} generated)")
else:
    fail("AC: 0 options generated for numeric conflict")

if len(options) <= 4:
    ok(f"AC: <= 4 options (got {len(options)})")
else:
    fail(f"AC: Too many options: {len(options)}")

# Options must reference document names
doc_refs = [o for o in options if "Packing List" in o or "Commercial Invoice" in o]
if doc_refs:
    ok("AC: Options reference specific document names")
else:
    fail("AC: Options do not mention document names")

# Options must reference values
val_refs = [o for o in options if "797" in o or "450" in o]
if val_refs:
    ok("AC: Options reference specific values")
else:
    fail("AC: Options do not mention specific values")

# Should have percentage note
pct_notes = [o for o in options if "%" in o]
if pct_notes:
    ok("Percentage difference note included in numeric options")
else:
    fail("No percentage difference note in numeric options")

# Domain recommendation
if "Packing List" in result_n["recommendation"] or "weight" in result_n["recommendation"].lower():
    ok("AC: Domain-specific recommendation for GROSS_WEIGHT")
else:
    fail("Domain recommendation not domain-specific: " + result_n["recommendation"][:80])

# 3-way numeric conflict
disc_3way = {
    "field": "GROSS_WEIGHT",
    "conflict_type": "numeric_variance",
    "sources": [
        {"document_type": "packing_list",      "value": "797.00 KG"},
        {"document_type": "commercial_invoice", "value": "795.50 KG"},
        {"document_type": "awb",               "value": "440.00 KG"},
    ]
}
result_3 = gen.generate(disc_3way)
if len(result_3["options"]) >= 1:
    ok(f"3-way numeric conflict generates options ({len(result_3['options'])})")
else:
    fail("3-way numeric conflict returned no options")


# =============================================================================
section("TEXT MISMATCH TESTS")
# =============================================================================

disc_text = {
    "field": "CONSIGNEE_NAME",
    "conflict_type": "text_mismatch",
    "sources": [
        {"document_type": "commercial_invoice", "value": "Burlington Industries Inc."},
        {"document_type": "bl",                 "value": "Burlington Industries Ltd."},
    ]
}
result_t = gen.generate(disc_text)
options_t = result_t["options"]
print(f"  Text options ({len(options_t)}):")
for o in options_t: print("   ", o)

if len(options_t) >= 1:
    ok(f"AC: >= 1 option for text mismatch ({len(options_t)})")
else:
    fail("AC: 0 options for text mismatch")

# Must show exact strings that would resolve
exact_refs = [o for o in options_t if "Burlington Industries Inc." in o or "Burlington Industries Ltd." in o]
if exact_refs:
    ok("AC: Exact string resolution shown in text options")
else:
    fail("AC: Exact strings not in text options")

# High similarity should produce a typo hint
sim_hints = [o for o in options_t if "similar" in o.lower() or "typograph" in o.lower() or "abbreviation" in o.lower()]
if sim_hints:
    ok("AC: Similarity hint for near-identical strings")
else:
    fail("AC: No similarity hint for near-identical strings (Inc. vs Ltd.)")

# Consignee recommendation
if "Letter of Credit" in result_t["recommendation"] or "LC" in result_t["recommendation"]:
    ok("AC: Domain recommendation for CONSIGNEE_NAME mentions LC")
else:
    fail("Consignee recommendation missing LC reference: " + result_t["recommendation"][:80])

# Very different text (no similarity hint)
disc_diff = {
    "field": "SHIPPER_NAME",
    "conflict_type": "text_mismatch",
    "sources": [
        {"document_type": "commercial_invoice", "value": "Textured Jersey Lanka PLC"},
        {"document_type": "awb",               "value": "Brandix Lanka Ltd."},
    ]
}
result_diff = gen.generate(disc_diff)
if len(result_diff["options"]) >= 1:
    ok(f"Dissimilar text conflict generates options ({len(result_diff['options'])})")
else:
    fail("Dissimilar text returned no options")

# Single-source text
disc_single = {
    "field": "CONSIGNEE_NAME",
    "conflict_type": "text_mismatch",
    "sources": [{"document_type": "commercial_invoice", "value": "Burlington Industries"}]
}
result_single = gen.generate(disc_single)
if result_single["options"]:
    ok("Single-source text: returns fallback option, no crash")
else:
    fail("Single-source text: returned empty options")


# =============================================================================
section("INTERNAL INCONSISTENCY TESTS")
# =============================================================================

disc_internal = {
    "field": "WEIGHT_CONSISTENCY",
    "conflict_type": "internal_inconsistency",
    "detail": "In Packing List: net(735.00) + tare(30.00) = 765.00, but gross=797.00",
    "sources": [{"document_type": "packing_list", "value": "internal check"}]
}
result_i = gen.generate(disc_internal)
options_i = result_i["options"]
print(f"  Internal options ({len(options_i)}):")
for o in options_i: print("   ", o)

if len(options_i) >= 1:
    ok(f"AC: >= 1 option for internal inconsistency ({len(options_i)})")
else:
    fail("AC: 0 options for internal inconsistency")

# Must explain net + tare = gross
net_tare_refs = [o for o in options_i if "net" in o.lower() and ("tare" in o.lower() or "gross" in o.lower())]
if net_tare_refs:
    ok("AC: net + tare = gross rule explained in internal options")
else:
    fail("AC: Internal options don't mention net/tare/gross relationship")

# Must reference the detail
detail_refs = [o for o in options_i if "735" in o or "797" in o or "Packing" in o or "specific" in o.lower()]
if detail_refs:
    ok("AC: Specific issue detail included in internal options")
else:
    fail("AC: Specific issue detail not in options")

if "net" in result_i["recommendation"].lower() or "tare" in result_i["recommendation"].lower():
    ok("Domain recommendation for WEIGHT_CONSISTENCY is relevant")
else:
    fail("Wrong domain recommendation for WEIGHT_CONSISTENCY: " + result_i["recommendation"][:80])


# =============================================================================
section("GENERIC / FALLBACK TESTS")
# =============================================================================

disc_unknown = {
    "field": "INVOICE_NUMBER",
    "conflict_type": "unknown_type",
    "sources": [
        {"document_type": "commercial_invoice", "value": "INV-2026-00451"},
        {"document_type": "packing_list",       "value": "PL-2026-00451"},
    ]
}
result_u = gen.generate(disc_unknown)
if len(result_u["options"]) >= 1:
    ok(f"Unknown conflict type: fallback generates options ({len(result_u['options'])})")
else:
    fail("Unknown conflict type: returned no options")

# No sources at all
disc_empty = {"field": "CURRENCY", "conflict_type": "numeric_variance", "sources": []}
result_empty = gen.generate(disc_empty)
if result_empty["options"]:
    ok("Empty sources: fallback option returned, no crash")
else:
    fail("Empty sources: returned empty options")

# Missing field key
disc_missing = {"conflict_type": "text_mismatch", "sources": []}
try:
    result_missing = gen.generate(disc_missing)
    if result_missing["options"]:
        ok("Missing 'field' key: handled gracefully, no crash")
    else:
        fail("Missing field: returned empty options")
except Exception as e:
    fail("Missing 'field' key: CRASHED: " + str(e))

# Very long source list
disc_many = {
    "field": "GROSS_WEIGHT",
    "conflict_type": "numeric_variance",
    "sources": [
        {"document_type": f"doc_type_{i}", "value": f"{400+i}.00 KG"}
        for i in range(10)
    ]
}
result_many = gen.generate(disc_many)
if len(result_many["options"]) <= 4:
    ok(f"AC: Max 4 options enforced on large source list (got {len(result_many['options'])})")
else:
    fail(f"AC: Too many options returned: {len(result_many['options'])}")


# =============================================================================
section("DOMAIN RECOMMENDATIONS COVERAGE")
# =============================================================================

critical_fields = ["GROSS_WEIGHT", "NET_WEIGHT", "PACKAGE_COUNT", "CONSIGNEE_NAME",
                   "SHIPPER_NAME", "INCOTERM", "TOTAL_AMOUNT", "WEIGHT_CONSISTENCY"]
for field in critical_fields:
    if field in gen.DOMAIN_RECOMMENDATIONS:
        ok(f"Domain recommendation exists for critical field: {field}")
    else:
        fail(f"Missing domain recommendation for: {field}")

# Default recommendation for unknown field
disc_unknown_field = {
    "field": "SOME_UNKNOWN_FIELD",
    "conflict_type": "text_mismatch",
    "sources": [
        {"document_type": "commercial_invoice", "value": "A"},
        {"document_type": "packing_list", "value": "B"},
    ]
}
result_uf = gen.generate(disc_unknown_field)
if result_uf["recommendation"]:
    ok("Unknown field gets default recommendation, no crash")
else:
    fail("Unknown field has no recommendation")


# =============================================================================
section("generate_batch() INTEGRATION TEST")
# =============================================================================

sample_discrepancies = [
    {
        "discrepancy_id": "disc_abc_001",
        "field": "GROSS_WEIGHT",
        "severity": "high",
        "conflict_type": "numeric_variance",
        "sources": [
            {"document_type": "packing_list",      "value": "797.00 KG"},
            {"document_type": "commercial_invoice", "value": "450.00 KG"},
        ],
        "reasoning_chain": None,
        "confidence": None,
        "counterfactual": None,
    },
    {
        "discrepancy_id": "disc_abc_002",
        "field": "CONSIGNEE_NAME",
        "severity": "low",
        "conflict_type": "text_mismatch",
        "sources": [
            {"document_type": "commercial_invoice", "value": "Burlington Industries Inc."},
            {"document_type": "bl",                 "value": "Burlington Industries Ltd."},
        ],
        "reasoning_chain": None,
        "confidence": None,
        "counterfactual": None,
    },
]

result_batch = gen.generate_batch(sample_discrepancies)

if result_batch is sample_discrepancies:
    ok("generate_batch() returns the same list (in-place update)")
else:
    fail("generate_batch() should return the same list object")

for disc in result_batch:
    cf = disc.get("counterfactual")
    if cf and "options" in cf and "recommendation" in cf:
        ok(f"Discrepancy '{disc['discrepancy_id']}' has counterfactual attached")
    else:
        fail(f"Discrepancy '{disc['discrepancy_id']}' missing counterfactual")

# Other XAI fields untouched
if result_batch[0]["reasoning_chain"] is None:
    ok("generate_batch() does not touch reasoning_chain (other XAI layers safe)")
else:
    fail("generate_batch() incorrectly modified reasoning_chain")

# Full serialisable check
try:
    json.dumps(result_batch)
    ok("Full batch result is JSON-serialisable")
except TypeError as e:
    fail("Batch not JSON-serialisable: " + str(e))


# =============================================================================
section("_parse_numeric UTILITY TEST")
# =============================================================================

cases = [
    ("450.00 KG", 450.0),
    ("797.00 KG", 797.0),
    ("25 Cartons", 25.0),
    ("USD 49,740.00", 49740.0),
    ("14.500 CBM", 14.5),
    ("some text", None),
    ("", None),
]
for raw, expected in cases:
    got = CounterfactualGenerator._parse_numeric(raw)
    if got == expected:
        ok(f"_parse_numeric({raw!r}) = {got}")
    else:
        fail(f"_parse_numeric({raw!r}) expected {expected}, got {got}")


# =============================================================================
section("FULL OUTPUT PREVIEW")
# =============================================================================

print("\n  Sample output for GROSS_WEIGHT numeric conflict:")
print("  " + json.dumps(gen.generate(disc_numeric), indent=2).replace("\n", "\n  "))


# =============================================================================
section("SUMMARY")
# =============================================================================
total = passed + failed
print(f"\n  Passed: {passed}/{total}")
if failed:
    print(f"  FAILED: {failed}/{total}")
    sys.exit(1)
else:
    print("\n  All Phase 08 acceptance criteria PASSED")
    sys.exit(0)
