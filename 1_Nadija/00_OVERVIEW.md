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
| 04| Document Classification | MUST | 2–3 hours |
| 05| Entity Extraction Strategy Decision | MUST | 1 hour |
| 06| Header Entity Extraction | MUST | 3–4 hours |
| 07| Table / Line-Item Extraction | SHOULD | 3–4 hours |
| 08| Confidence Scoring | MUST | 1–2 hours |
| 09| Canonical Normalization | SHOULD | 2–3 hours |
| 10| Pipeline Orchestration | MUST | 2–3 hours |
| 11| Integration Testing + Demo Prep | MUST | 2–3 hours |

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
      "value": "450.00",
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
| Aloka | `ExtractionResult` JSON per document | Phase 09 |
| Kaveen | `bbox` coordinates for PDF overlay | Phase 05 |

---

## Files You Own

```
backend/
  ai_pipeline/
    __init__.py
    ocr_engine.py          ← Phase 02
    classifier.py           ← Phase 03
    entity_extractor.py     ← Phase 05, 06
    normalizer.py           ← Phase 08
    pipeline.py             ← Phase 09
    confidence.py           ← Phase 07
    models/                 ← model weights/configs
    mock_pipeline.py        ← Already exists (mock for team)
```

> **Rule:** Do NOT modify files outside `backend/ai_pipeline/`. If you need changes elsewhere, coordinate with Kaveen or Aloka.

---

## Key Decisions

1. **LayoutLMv3 vs Gemini Vision API:** If fine-tuning LayoutLMv3 takes too long, use Gemini Vision API as primary extractor. Demo quality matters more than model purity.
2. **PaddleOCR is non-negotiable:** It gives us bounding boxes for free — essential for Layer 1 XAI.
3. **Don't build training pipelines:** For the hackathon demo, pre-trained + API-based extraction is sufficient.
