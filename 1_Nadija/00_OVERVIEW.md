# Nadija — AI/ML Pipeline (10 Phases)

> **Role:** AI/ML Engineer
> **Focus:** Document Intelligence — OCR, Classification, Entity Extraction
> **Workload:** Intentionally lighter due to university exams

---

## Your Mission

You own the **AI brain** of ClearanceX. Your pipeline takes raw PDF files and produces structured extraction results with bounding boxes and confidence scores. Everything downstream (reasoning, graph, XAI layers 2–6, frontend) depends on YOUR output format — but not on your real implementation. Mocks are provided so the team can work in parallel.

---

## Phase Overview

| Phase | Title | Priority | Estimated Time |
|-------|-------|----------|----------------|
| ~~01~~ | ~~Project Setup (React + Vite + TypeScript)~~ — ✅ **DONE** | ~~MUST~~ | ~~1 hour~~ | 
| ~~02~~ | ~~Environment Setup + PaddleOCR Install~~ — ✅ **DONE** | ~~MUST~~ | ~~1–2 hours~~ |
| ~~03~~| ~~OCR Integration — Text + Bounding Boxes~~ — ✅ **DONE** | ~~MUST~~ | ~~2–3 hours~~ |
| ~~04~~| ~~Document Classification~~ — ✅ **DONE** | ~~MUST~~ | ~~2–3 hours~~ |
| ~~05~~| ~~Entity Extraction Strategy Decision~~ — ✅ **DONE** | ~~MUST~~ | ~~1 hour~~ |
| ~~06~~| ~~Header Entity Extraction~~ — ✅ **DONE** | ~~MUST~~ | ~~3–4 hours~~ |
| ~~07~~| ~~Table / Line-Item Extraction~~ — ✅ **DONE** | ~~SHOULD~~ | ~~3–4 hours~~ |
| ~~08~~| ~~Confidence Scoring~~ — ✅ **DONE** | ~~MUST~~ | ~~1–2 hours~~ |
| ~~09~~| ~~Canonical Normalization + Dossier Upload~~ — ✅ **DONE** Three-tier: token sort → PostgreSQL cache → Gemini fallback. Deterministic rules for weights/volumes/dates/numbers/identifiers. `POST /api/upload` multi-file dossier endpoint. `GET /api/upload/{dossier_id}/status` polling. `DossierManager` background processing. `norm_cache` + `dossiers` + `dossier_documents` DB tables. | ~~**MUST**~~ | ~~3–4 hours~~ |
| ~~10~~| ~~Pipeline Orchestration~~ — ✅ **DONE** `AIPipeline.process_document()` wires OCR→Classify→Extract→Normalize→Score. `ConfidenceScorer` called. `MockPipeline` schema-compatible. `test_pipeline.py` + `pipeline_output_sample.json` delivered to Aloka/Kaveen. | ~~MUST~~ | ~~2–3 hours~~ |
| ~~12~~| ~~OpenAI Migration + UI API Failure Warnings~~ - ✅ **DONE** Migrated the AI pipeline from Gemini to OpenAI, removing retry loops, fixing PaddleOCR zlib issues, resolving Pydantic tuple extraction errors, and implementing UI warnings for fallback API failures. | ~~MUST~~ | ~~3-4 hours~~ |
| ~~13~~| ~~Party-Role-Aware Consignee Extraction~~ — ✅ **DONE** Consignee values now require explicit source-label evidence. Carriers, freight forwarders, banks, beneficiaries, shippers, and notify parties are retained under their own roles and excluded from CUSDEC consignee resolution; stored dossiers are rechecked against saved OCR role evidence. | ~~MUST~~ | ~~2–3 hours~~ |
| ~~11~~| ~~Integration Testing + Demo Prep~~ — ✅ **DONE** Syntheic document tests, master schema contract validation, edge case resilience tests, normalizer fallback cache script (`clear_demo_cache.py`), pipeline verifier script (`verify_ai_pipeline.py`), and deterministic demo fallback cache (`demo_cache.json`) are generated and fully verified. | ~~MUST~~ | ~~2–3 hours~~ |
| ~~34~~ | ~~Shared Finalist Presentation and Viva Preparation Pack~~ — ✅ **DONE** Team preparation artifacts: 10-minute English deck, timed script, project limitations review, 62 viva Q&A, and demo checklist in `Presentation_&_Viva/`. Prepared with assistant support; individual speaking roles and rehearsal remain to be confirmed. | ~~MUST~~ | ~~Preparation pack~~ |
| ~~35~~ | ~~Clear Shipping PDF Samples and Real OCR Benchmark~~ — ✅ **DONE** Four matched, single-page sea-shipment PDFs (invoice, packing list, B/L, delivery order) in `output/pdf/ocr_samples/`, reproducible generator, 42-field ground truth, and real PaddleOCR CPU benchmark. All 42 labelled fields recovered; normalized character error rate 0%; mean token confidence 99.76-99.91% per document. These are clean synthetic fixtures; end-to-end extraction accuracy and UI confidence are separate, with runtime compatibility and scoring limitations documented in the sample README. | ~~MUST~~ | ~~Sample generation and verification~~ |

**Total estimated: ~20–28 hours across 3–4 days**

---

## Your Output Contract

Everything you build must produce this exact JSON structure. Aloka and Kaveen are already building against it:

```json
{
  "document_id": "doc_001",
  "document_type": "commercial_invoice",
  "classification_confidence": 0.97,
  "entities": [
    {
      "entity_type": "GROSS_WEIGHT",
      "value": "450.00 KG",
      "normalized_value": 450.0,
      "unit": "kg",
      "page": 2,
      "bbox": [120, 240, 410, 290],
      "extraction_confidence": 0.94
    }
  ],
  "raw_ocr": [
    {
      "text": "Gross Weight: 450.00 KG",
      "page": 2,
      "bbox": [100, 230, 430, 300],
      "ocr_confidence": 0.98
    }
  ]
}
```

---

## Dependencies

| You Need From | What | When |
|---|---|---|
| Kaveen | Uploaded PDF file paths from `POST /api/shipments/upload` | Phase 02 |
| Aloka | Sample synthetic PDFs to test against | Phase 02 |

| Others Need From You | What | When |
|---|---|---|
| Aloka | `ExtractionResult` JSON per document (with `normalized_value`) | Phase 06 onwards (mocks first, real by Phase 10) |
| Kaveen | `bbox` coordinates for PDF overlay | Phase 06 |

---

## Files You Own

```
backend/
  ai_pipeline/
    __init__.py
    ocr_engine.py          ← Phase 03
    classifier.py           ← Phase 04
    entity_extractor.py     ← Phase 06, 07
    normalizer.py           ← Phase 09  ⚠️ populates normalized_value + unit
    pipeline.py             ← Phase 10
    confidence.py           ← Phase 08
    models/                 ← model weights/configs
    mock_pipeline.py        ← Already exists (mock for team)
  data/
    norm_cache.json         ← Phase 09  Tier 2 persistent LLM cache (auto-created)
  scripts/
    clear_demo_cache.py     ← Phase 11  run before live demo to force Tier 3 LLM calls
```

> **Rule:** Do NOT modify files outside `backend/ai_pipeline/`. If you need changes elsewhere, coordinate with Kaveen or Aloka.

---

## Key Decisions

1. **LayoutLMv3 vs Gemini Vision API:** If fine-tuning LayoutLMv3 takes too long, use Gemini Vision API as primary extractor. Demo quality matters more than model purity.
2. **PaddleOCR is non-negotiable:** It gives us bounding boxes for free — essential for Layer 1 XAI.
3. **Don't build training pipelines:** For the hackathon demo, pre-trained + API-based extraction is sufficient.
4. **Three-tier normalizer (Phase 09):** Tier 1 = token-sort pre-check (zero cost), Tier 2 = local JSON cache (1 ms), Tier 3 = LLM canonicalization on cache miss (persisted immediately). All weights normalize to `kg`, volumes to `cbm`, dates to ISO 8601. Raw `value` is always preserved; standardized form lives in `normalized_value`.
5. **Clear Tier 2 cache before demo (Phase 11):** Run `clear_demo_cache.py` to remove port/company name entries so judges see Tier 3 LLM calls fire live. Keep numeric unit conversions cached for speed.
