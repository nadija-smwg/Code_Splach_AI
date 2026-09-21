# Aloka — Reasoning Engine + Data + Supporting Frontend (15 Phases)

> **Role:** Reasoning Engine + Data Engineer + Supporting Frontend
> **Focus:** Knowledge Graph, XAI Layers 2–5, Discrepancy Detection, Data Pipeline, ASYCUDA Export
> **Workload:** Heavy — you carry the XAI core that makes this project unique

---

## Your Mission

You own the **reasoning brain** of ClearanceX. Your engine takes Nadija's raw extraction output and produces everything that makes this system an XAI powerhouse: knowledge graphs, reasoning chains, counterfactuals, confidence decomposition, audit trails, discrepancy detection, and ASYCUDA export. You also build the supporting frontend components for your reasoning output.

---

## Phase Overview

| Phase | Title | Priority | Estimated Time |
|-------|-------|----------|----------------|
| ~~01~~ | ~~Database Schema + Setup~~ — ✅ **DONE** | ~~MUST~~ | ~~1–2 hours~~ |
| ~~02~~ | ~~Mock API Endpoints~~ — ✅ **DONE BY NADIJA — skip this** | ~~MUST~~ | ~~2–3 hours~~ |
| 03 | Synthetic Data Generator | MUST | 3–4 hours |
| ~~04~~ | ~~Knowledge Graph Construction~~ — ✅ **DONE** | ~~MUST~~ | ~~3–4 hours~~ |
| 05 | Discrepancy Detection Engine | MUST | 3–4 hours |
| 06 | Layer 2: Reasoning Chain Generator | MUST | 2–3 hours |
| 07 | Layer 3: Confidence Decomposition | MUST | 1–2 hours |
| 08 | Layer 4: Counterfactual Generator | MUST | 2–3 hours |
| 09 | Layer 5: Audit Trail System | MUST | 1–2 hours |
| 10 | Layer 6: Graph Data Serialization | MUST | 2–3 hours |
| 11 | ASYCUDA Export Generator | MUST | 2–3 hours |
| 12 | Reasoning Chain UI Panel | SHOULD | 2–3 hours |
| 13 | Counterfactual Cards UI | SHOULD | 2–3 hours |
| 14 | Backend API Integration | MUST | 2–3 hours |
| 15 | Integration Testing | MUST | 2–3 hours |

**Total estimated: ~30–42 hours across 3–4 days**

---

## Your Output Contracts

### Discrepancy (with all XAI layers)
```json
{
  "discrepancy_id": "disc_001",
  "field": "GROSS_WEIGHT",
  "severity": "high",
  "severity_score": 0.87,
  "sources": [...],
  "reasoning_chain": { "steps": [...], "conclusion": "..." },
  "confidence": { "extraction": 0.94, "classification": 0.97, "matching": 0.72, "overall": 0.72 },
  "counterfactual": { "options": [...], "recommendation": "..." }
}
```

### Knowledge Graph (for vis.js)
```json
{
  "nodes": [
    { "id": "GROSS_WEIGHT", "label": "Gross Weight", "type": "entity", "status": "conflict" }
  ],
  "edges": [
    { "from": "doc_001", "to": "GROSS_WEIGHT", "label": "450.00 kg", "confidence": 0.94 }
  ]
}
```

---

## Dependencies

| You Need From | What | When |
|---|---|---|
| Nadija | `ExtractionResult` JSON per document | Phase 04 (use mock until then) |
| Kaveen | Upload API storing files + creating shipment records | Phase 02 |

| Others Need From You | What | When |
|---|---|---|
| Kaveen | All API response data (graph, discrepancies, audit trail) | Phase 14 |
| Kaveen | React components for reasoning chain + counterfactual panels | Phase 12, 13 |

---

## Files You Own

```
backend/
  reasoning/
    __init__.py
    knowledge_graph.py      ← Phase 04
    discrepancy_engine.py   ← Phase 05
    reasoning_chains.py     ← Phase 06
    confidence_decomp.py    ← Phase 07
    counterfactual.py       ← Phase 08
    audit_trail.py          ← Phase 09
    graph_serializer.py     ← Phase 10
    asycuda_export.py       ← Phase 11
  data/
    synthetic_generator.py  ← Phase 03
    sample_documents/       ← Generated PDFs
  api/
    routes.py               ← Phase 14 (shared with Kaveen)
  database/
    schema.sql              ← Phase 01
    models.py               ← Phase 01

frontend/src/
  components/
    ReasoningChainPanel.tsx  ← Phase 12
    CounterfactualCards.tsx  ← Phase 13
    AuditTrailExport.tsx     ← Phase 09 (simple download button)
```

> **Rule:** Do NOT modify files in `backend/ai_pipeline/` (Nadija's area) or frontend components outside your assigned ones. Coordinate with the team for shared files.
