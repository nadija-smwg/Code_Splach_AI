# Kaveen — Full Frontend Lead (15 Phases)

> **Role:** Full Frontend Lead + Supporting Backend
> **Focus:** React UI, PDF Viewer, Graph Visualization, Upload Flow, XAI Components, API Integration
> **Workload:** Heavy — you own the ENTIRE user-facing experience (all frontend components)

---

## Your Mission

You own **everything the user sees and interacts with**. The judges will evaluate ClearanceX primarily through your UI — if the frontend looks polished and the demo flows smoothly, we win. If it's glitchy or ugly, no amount of good AI matters.

---

## Phase Overview

![ClearanceX UI Reference](../Docs/screen.png)

| Phase | Title | Priority | Estimated Time |
|-------|-------|----------|----------------|
| ~~01~~ | ~~Project Setup (React + Vite + TypeScript)~~ — ✅ **DONE BY NADIJA — skip this** | ~~MUST~~ | ~~1 hour~~ |
| ~~02~~ | ~~FastAPI Skeleton + Upload Endpoint~~ — ✅ **DONE BY NADIJA — skip this** | ~~MUST~~ | ~~1 hour~~ |
| ~~03~~ | ~~Application Shell + Routing + Navigation~~ — ✅ **DONE** | ~~MUST~~ | ~~2 hours~~ |
| ~~04~~ | ~~Upload Page (Drag & Drop Multi-PDF)~~ — ✅ **DONE** | ~~MUST~~ | ~~2–3 hours~~ |
| ~~05~~ | ~~Shipment Dashboard / Status Page~~ — ✅ **DONE** | ~~MUST~~ | ~~2 hours~~ |
| ~~06~~ | ~~Dual-Pane Review Layout~~ — ✅ **DONE** | ~~MUST~~ | ~~3–4 hours~~ |
| ~~07~~ | ~~PDF Viewer with BBox Overlay (Layer 1)~~ — ✅ **DONE** | ~~MUST~~ | ~~4–5 hours~~ |
| ~~08~~ | ~~Extraction Data Table~~ — ✅ **DONE** | ~~MUST~~ | ~~2–3 hours~~ |
| ~~09~~ | ~~Knowledge Graph Visualization (vis.js)~~ — ✅ **DONE** | ~~MUST~~ | ~~4–5 hours~~ |
| ~~10~~ | ~~Discrepancy List Panel~~ — ✅ **DONE** | ~~MUST~~ | ~~2–3 hours~~ |
| ~~11~~ | ~~Confidence Badges (Layer 3)~~ — ✅ **DONE** | ~~MUST~~ | ~~1–2 hours~~ |
| ~~12~~ | ~~Loading / Error / Empty States~~ — ✅ **DONE** | ~~MUST~~ | ~~1–2 hours~~ |
| ~~12b~~ | ~~Reasoning Chain Panel (XAI)~~ — ✅ **DONE** | ~~MUST~~ | ~~2–3 hours~~ |
| ~~13~~ | ~~ASYCUDA Download + Audit Export Buttons~~ — ✅ **DONE** | ~~MUST~~ | ~~1 hour~~ |
| ~~13b~~ | ~~Counterfactual Cards (XAI)~~ — ✅ **DONE** | ~~MUST~~ | ~~2–3 hours~~ |
| ~~14~~ | ~~Frontend ↔ Backend API Integration~~ — ✅ **DONE** | ~~MUST~~ | ~~2–3 hours~~ |
| ~~15~~ | ~~UI Polish + Responsive + Demo Prep~~ — ✅ **DONE** | ~~MUST~~ | ~~3–4 hours~~ |
| ~~16~~ | ~~Fresh Evaluator Simulation~~ — ✅ **DONE** | ~~MUST~~ | ~~1 hour~~ |
| ~~17~~ | ~~README Audit~~ — ✅ **DONE** | ~~MUST~~ | ~~1 hour~~ |
| ~~18~~ | ~~Git Repository Audit~~ — ✅ **DONE** | ~~MUST~~ | ~~1 hour~~ |
| ~~19~~ | ~~Build / Test Verification~~ — ✅ **DONE** | ~~MUST~~ | ~~1 hour~~ |
| ~~20~~ | ~~Security Sanity Check~~ — ✅ **DONE** | ~~MUST~~ | ~~1 hour~~ |
| ~~21~~ | ~~Code Quality / Maintainability Audit~~ — ✅ **DONE** | ~~MUST~~ | ~~1 hour~~ |
| ~~22~~ | ~~Fix Issues~~ — ✅ **DONE** | ~~MUST~~ | ~~1 hour~~ |
| ~~23~~ | ~~Final Requirement Matrix~~ — ✅ **DONE** | ~~MUST~~ | ~~1 hour~~ |
| ~~24~~ | ~~Final Docker Commands~~ — ✅ **DONE** | ~~MUST~~ | ~~30 min~~ |
| ~~25~~ | ~~Exact Evaluator Instructions~~ — ✅ **DONE** | ~~MUST~~ | ~~30 min~~ |
| ~~26~~ | ~~Final Report~~ — ✅ **DONE** 🏁 **READY FOR SUBMISSION** | ~~MUST~~ | ~~1 hour~~ |
| ~~27~~ | ~~Canonical Key Field Reconciliation UI~~ — ✅ **DONE** Added the Review Workspace reconciliation panel, consensus/outlier display, assertion-driven red highlighting, and canonical graph visual semantics. | ~~MUST~~ | ~~2–3 hours~~ |

**Total estimated: ~30–42 hours across 3–4 days**

---

## Your Key Dependencies

| You Need From | What | When |
|---|---|---|
| Aloka | Mock API endpoints (Phase 02) | Your Phase 04 |
| Aloka | Graph data format for vis.js | Your Phase 09 |
| Aloka | Reasoning chain + counterfactual **data** from backend API | Your Phase 10, 12b, 13b |
| Nadija | BBox coordinate format for PDF overlay | Your Phase 07 |

---

## Files You Own

```
frontend/
  src/
    App.tsx
    main.tsx
    index.css
    pages/
      UploadPage.tsx            ← Phase 04
      DashboardPage.tsx         ← Phase 05
      ReviewPage.tsx            ← Phase 06
    components/
      Navbar.tsx                ← Phase 03
      FileUploader.tsx          ← Phase 04
      ShipmentCard.tsx          ← Phase 05
      DualPaneLayout.tsx        ← Phase 06
      PdfViewer.tsx             ← Phase 07
      BBoxOverlay.tsx           ← Phase 07
      ExtractionTable.tsx       ← Phase 08
      KnowledgeGraph.tsx        ← Phase 09
      DiscrepancyList.tsx       ← Phase 10
      ConfidenceBadge.tsx       ← Phase 11
      LoadingSpinner.tsx        ← Phase 12
      ErrorState.tsx            ← Phase 12
      ReasoningChainPanel.tsx   ← Phase 12b (moved from Aloka)
      ExportButtons.tsx         ← Phase 13
      AuditTrailExport.tsx      ← Phase 13 (moved from Aloka)
      CounterfactualCards.tsx   ← Phase 13b (moved from Aloka)
    hooks/
      useShipment.ts            ← Phase 14
      useApi.ts                 ← Phase 14
    types/
      index.ts                  ← Shared TypeScript types
    utils/
      api.ts                    ← API client
  public/
  package.json
  vite.config.ts
  tsconfig.json

backend/
  main.py                       ← Phase 02 (shared with Aloka)
```

> **Rule:** Do NOT modify files in `backend/ai_pipeline/` (Nadija's area) or `backend/reasoning/` (Aloka's area). For API routes, coordinate with Aloka.

---

## Design System

Use these consistently across all components:

### Colors
```css
:root {
  /* Dark theme (canonical — matches Phase 01) */
  --bg-primary: #0a0a1a;
  --bg-secondary: #12122e;
  --bg-card: #1a1a3e;
  --bg-hover: #252550;
  
  /* Accent */
  --accent-primary: #6366f1;     /* Indigo */
  --accent-secondary: #8b5cf6;   /* Purple */
  --accent-glow: rgba(99, 102, 241, 0.3);
  
  /* Confidence colors */
  --confidence-high: #10b981;    /* Green */
  --confidence-medium: #f59e0b;  /* Yellow/Amber */
  --confidence-low: #ef4444;     /* Red */
  
  /* Severity colors */
  --severity-high: #ef4444;
  --severity-medium: #f59e0b;
  --severity-low: #6366f1;
  
  /* Document type colors */
  --doc-invoice: #4A90D9;
  --doc-packing-list: #50C878;
  --doc-awb: #FFB347;
  --doc-bl: #DDA0DD;
  
  /* Text */
  --text-primary: #f1f5f9;
  --text-secondary: #94a3b8;
  --text-muted: #64748b;
  
  /* Borders */
  --border-subtle: rgba(255, 255, 255, 0.08);
  --border-accent: rgba(99, 102, 241, 0.4);
}
```

### Typography
```css
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=JetBrains+Mono:wght@400;500&display=swap');

body {
  font-family: 'Inter', sans-serif;
}

code, .mono {
  font-family: 'JetBrains Mono', monospace;
}
```

### Key Design Principles
- **Dark mode only** — looks more technical, hides imperfections
- **Glassmorphism cards** — `backdrop-filter: blur(12px); background: rgba(30, 30, 74, 0.7);`
- **Subtle glow effects** — `box-shadow: 0 0 20px var(--accent-glow);`
- **Smooth transitions** — `transition: all 0.3s ease;`
- **Animated knowledge graph** — nodes and edges should animate on load
