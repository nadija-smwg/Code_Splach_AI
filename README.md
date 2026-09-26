# ClearanceX 🚢

**Intelligent Decision Support for Customs Declaration Compliance**

ClearanceX is an **Explainable AI (XAI)** copilot that automates the ingestion, reconciliation, and validation of complex shipping dossiers for Sri Lankan apparel imports and exports. It reads unstructured customs documents, cross-references data across sources, flags discrepancies with human-understandable reasoning, and generates one-click ASYCUDA-compliant export files — eliminating hours of manual data entry and preventing costly declaration errors.

> **Team Ants** — CodeSplash'26 Hackathon

---

## 📋 Table of Contents

- [The Problem](#-the-problem)
- [The Solution](#-the-solution)
- [Key Features](#-key-features)
- [Architecture](#-architecture)
- [Technology Stack](#-technology-stack)
- [Quick Start — Docker](#-quick-start--docker-recommended)
- [Local Development](#-local-development-without-docker)
- [Environment Variables](#-environment-variables)
- [Database & Migrations](#-database--migrations)
- [Demo Mode](#-demo-mode)
- [Project Structure](#-project-structure)
- [Troubleshooting](#-troubleshooting)
- [Team Information](#-team-information)
- [Limitations & Assumptions](#-limitations--assumptions)
- [Change Log](#-change-log)
- [License](#-license)

---

## 🎯 The Problem

In Sri Lanka's apparel manufacturing sector, clearing imported raw materials or exporting finished goods requires preparing a detailed **Customs Declaration (CUSDEC)** via the **ASYCUDA World** system. This is an entirely manual process today:

1. Shipping executives receive multi-page dossiers containing **Commercial Invoices**, **Packing Lists**, **Airway Bills (AWBs)**, and **Bills of Lading (B/Ls)**.
2. These documents arrive in different formats from different parties — each with varying terminology, inconsistent units, and potential discrepancies.
3. Executives must manually cross-reference values (Gross Weight, Net Weight, Package Count, Consignee details, Incoterms) across documents — a process that is **slow, error-prone, and high-stakes**.
4. A single mismatch — e.g., weight discrepancy between the Invoice and AWB — can result in **rejected declarations, port demurrage fees, bank payment freezes**, or customs penalties.

**There is no existing tool** that automates this cross-document verification with explainable reasoning.

---

## 🚀 The Solution

ClearanceX replaces this manual workflow with an automated, AI-powered pipeline:

| Step | What ClearanceX Does |
|------|---------------------|
| **1. Upload** | Accept multi-page PDF shipping documents (Invoice, Packing List, AWB, B/L) |
| **2. Classify** | Automatically identify each document type using OCR + OpenAI Vision |
| **3. Extract** | Pull structured entities (weights, consignee, incoterms, item tables) with spatial-aware OCR |
| **4. Normalize** | Standardize units, date formats, and terminology across all documents |
| **5. Reconcile** | Build a Knowledge Graph linking entities, then apply deterministic rules to flag mismatches |
| **6. Explain** | Generate 4-layer XAI explanations for every discrepancy (Provenance → Reasoning → Confidence → Counterfactuals) |
| **7. Export** | Produce ASYCUDA-compliant CUSDEC XML for Direct Trader Input (DTI) bulk upload |

---

## ✨ Key Features

### Document Intelligence
- **AI-Powered Classification** — Automatically classifies documents (Commercial Invoice, Packing List, AWB, B/L) with confidence scoring via OpenAI GPT-4o Vision
- **Spatial OCR Extraction** — Extracts entities with bounding box coordinates using PaddleOCR, preserving document layout for visual attribution
- **Multi-Line Table Extraction** — Parses complex tabular data (item descriptions, quantities, HS codes) from invoices and packing lists
- **Entity Normalization** — Converts varying terminologies into canonical forms (e.g., "Kgs" → KG, "CIF Colombo" → CIF)

### Cross-Document Reconciliation
- **Knowledge Graph Engine** — Builds a NetworkX graph linking entities across documents, with edges representing semantic relationships
- **Deterministic Rule Evaluator** — Applies domain-specific customs rules (weight tolerance ±1%, consignee match, package count consistency) to detect conflicts
- **Entity Resolution** — Resolves near-matches using fuzzy string matching and semantic similarity

### Explainable AI (XAI) — 4-Layer Framework
| Layer | Name | What It Shows |
|-------|------|--------------|
| **Layer 1** | **Provenance** | Source documents, OCR snippets, and bounding boxes for every extracted value |
| **Layer 2** | **Reasoning Chain** | Step-by-step logical deduction showing how the discrepancy was detected |
| **Layer 3** | **Confidence Scoring** | Color-coded scores (🟢 ≥90%, 🟡 70–89%, 🔴 <70%) combining OCR and extraction confidence |
| **Layer 4** | **Counterfactual** | Actionable fix suggestions — "What would need to change for this to pass?" |

### Compliance & Export
- **ASYCUDA CUSDEC XML Generator** — Produces standards-compliant XML directly from the validated Knowledge Graph
- **SHA-256 Audit Trail** — Every pipeline event (classification, extraction, rule evaluation) is timestamped and hashed for tamper-evident traceability
- **Batch Filing** — Process multiple dossiers in parallel with status tracking

### Modern Frontend
- **Cinematic Scroll Animations** — GSAP + ScrollTrigger-powered smooth transitions with `prefers-reduced-motion` support
- **Interactive Knowledge Graph** — Zoomable vis.js network visualization of entity relationships
- **Review Workspace** — Side-by-side document viewer with highlighted discrepancies and one-click resolution
- **Responsive Design** — Tailwind CSS v4 design system optimized for desktop and tablet workflows

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                     Browser (localhost:3000)                     │
│            React 19 + TypeScript + Vite  (nginx in Docker)      │
│   ┌────────────┐ ┌──────────┐ ┌──────────┐ ┌───────────────┐   │
│   │  Overview   │ │ Dossiers │ │  Review  │ │ Knowledge     │   │
│   │  Dashboard  │ │ Manager  │ │Workspace │ │ Graph Viewer  │   │
│   └────────────┘ └──────────┘ └──────────┘ └───────────────┘   │
│   ┌────────────┐ ┌──────────┐ ┌──────────┐ ┌───────────────┐   │
│   │Discrepancy │ │  Batch   │ │  CUSDEC  │ │  Audit Trail  │   │
│   │  Explorer  │ │  Filing  │ │  Export  │ │  + Hash Log   │   │
│   └────────────┘ └──────────┘ └──────────┘ └───────────────┘   │
└──────────────────────────┬──────────────────────────────────────┘
                           │ HTTP / REST (Axios)
                           ▼
┌─────────────────────────────────────────────────────────────────┐
│                FastAPI Backend (localhost:8000)                   │
│                                                                  │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │                    AI Pipeline Layer                      │   │
│  │  PaddleOCR → Classifier → Entity Extractor → Normalizer │   │
│  │              (OpenAI GPT-4o / GPT-4o-mini)               │   │
│  └──────────────────────────────────────────────────────────┘   │
│                                                                  │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │               Neuro-Symbolic Reasoning Layer             │   │
│  │  Knowledge Graph Builder → Rule Evaluator → XAI Compiler │   │
│  │  Counterfactual Generator → Entity Resolution            │   │
│  └──────────────────────────────────────────────────────────┘   │
│                                                                  │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │                   Compliance Layer                        │   │
│  │  ASYCUDA XML Export → Audit Trail → Batch Filing Engine  │   │
│  └──────────────────────────────────────────────────────────┘   │
└──────────────────────────┬──────────────────────────────────────┘
                           │ SQLAlchemy ORM
                           ▼
┌─────────────────────────────────────────────────────────────────┐
│              PostgreSQL 15 (localhost:5433)                       │
│   shipments · documents · extractions · discrepancies · cache   │
└─────────────────────────────────────────────────────────────────┘
```

---

## 🧰 Technology Stack

| Layer | Technology | Why This Choice |
|-------|-----------|----------------|
| **Frontend** | React 19, TypeScript 6, Vite 8, Tailwind CSS v4 | Modern, type-safe UI with instant HMR and utility-first styling |
| **Animations** | GSAP 3 + ScrollTrigger | GPU-accelerated scroll animations with `prefers-reduced-motion` support |
| **Visualization** | vis.js (vis-network + vis-data) | Interactive, zoomable Knowledge Graph rendering in the browser |
| **HTTP Client** | Axios | Promise-based HTTP with interceptors for error handling |
| **Backend** | Python 3.10, FastAPI, Pydantic v2 | Async-native REST framework with automatic OpenAPI docs and validation |
| **AI / Vision** | OpenAI GPT-4o (Vision), GPT-4o-mini (Text) | Multi-modal document understanding and structured JSON extraction |
| **OCR** | PaddleOCR 2.7 | High-accuracy spatial OCR with bounding box extraction |
| **Graph Engine** | NetworkX 3.x | In-memory graph for entity linking and cross-document reconciliation |
| **Database** | PostgreSQL 15 (Alpine) | Robust relational DB with JSONB support for flexible entity storage |
| **ORM** | SQLAlchemy 2.0 | Declarative ORM with automatic schema creation |
| **Containerization** | Docker + Docker Compose | One-command full-stack deployment with health checks |
| **Web Server** | nginx (Alpine) | Production-grade static file serving with API proxy |

### 🧠 AI Model Strategy — Cost-Efficient Routing

ClearanceX uses a **tiered model routing strategy** to minimize API costs while maximizing accuracy where it matters most:

```
┌─────────────────────────────────────────────────────────────────────┐
│                    OpenAI Model Routing                             │
│                                                                     │
│  📄 Document Image Analysis          →  GPT-4o (Vision)            │
│     └─ Only used when reading PDF pages as images                  │
│     └─ Most expensive, but required for spatial document layout     │
│                                                                     │
│  ✏️ Text Tasks (Classification,       →  GPT-4o-mini               │
│     Entity Extraction, Normalization)                               │
│     └─ Handles 80%+ of all API calls                               │
│     └─ ~15× cheaper than GPT-4o                                    │
│                                                                     │
│  🔗 Semantic Similarity               →  text-embedding-3-small    │
│     └─ Used for fuzzy entity matching                              │
│     └─ Cheapest model in the stack (~$0.02/1M tokens)              │
└─────────────────────────────────────────────────────────────────────┘
```

| Model | Role in Pipeline | Cost (per 1M tokens) | Why This Model |
|-------|-----------------|---------------------|----------------|
| **GPT-4o** | Document Vision — reads PDF page images to extract layout-aware data | ~$2.50 input / $10.00 output | Only model with multi-modal vision capable of understanding shipping document layouts, stamps, and tabular structures |
| **GPT-4o-mini** | Text processing — classification, structured extraction, normalization, counterfactual generation | ~$0.15 input / $0.60 output | Handles the bulk of API calls at a fraction of GPT-4o cost, while maintaining high accuracy for structured JSON extraction |
| **text-embedding-3-small** | Semantic similarity — fuzzy entity matching during reconciliation | ~$0.02 input | Cheapest embedding model; sufficient for matching near-identical entity strings (e.g., "ABC Textiles Ltd" vs "ABC Textiles Ltd.") |

> **Result:** By routing ~80% of calls through GPT-4o-mini and reserving GPT-4o only for vision tasks, a typical 3-document dossier costs **under $0.05** to process end-to-end.

---

## 🐳 Quick Start — Docker (Recommended)

> **Prerequisites:** [Docker Desktop](https://docs.docker.com/get-docker/) (v24+) and [Git](https://git-scm.com/). That's it — no Python or Node.js required.

**Step 1 — Clone the repository:**
```bash
git clone https://github.com/codesplash26-hackathon/ants.git
cd ants
```

**Step 2 — Set up environment variables:**
```bash
cp .env.example .env
```

Edit `.env` and add your **OpenAI API key**:
```env
OPENAI_API_KEY=sk-your_openai_api_key_here
OPENAI_BASE_URL=https://api.openai.com/v1
OPENAI_FAST_MODEL=gpt-4o-mini
OPENAI_VISION_MODEL=gpt-4o
OPENAI_EMBEDDING_MODEL=text-embedding-3-small
DATABASE_URL=postgresql://postgres:postgres@db:5432/clearancex
CORS_ORIGINS=http://localhost:3000,http://localhost:5173
```

> **Get an OpenAI API key:** [https://platform.openai.com/api-keys](https://platform.openai.com/api-keys)  
> If you don't have an API key, contact us: **072-2254703**

**Step 3 — Build and start all services:**
```bash
docker compose up --build
```

This will:
1. Pull PostgreSQL 15 and start the database with automatic health checks
2. Build the FastAPI backend (auto-creates all DB tables on startup)
3. Build the React frontend and serve it via nginx

**Step 4 — Open the app:**

| Service | URL |
|---------|-----|
| 🖥️ Frontend (React) | [http://localhost:3000](http://localhost:3000) |
| ⚙️ Backend API | [http://localhost:8000](http://localhost:8000) |
| 📖 API Docs (Swagger) | [http://localhost:8000/docs](http://localhost:8000/docs) |
| 🩺 Health Check | [http://localhost:8000/health](http://localhost:8000/health) |

**To stop:**
```bash
docker compose down        # Stop containers (keeps data)
docker compose down -v     # Stop + wipe database
```

---

## 💻 Local Development (Without Docker)

### Prerequisites

| Tool | Version | Install |
|------|---------|---------|
| Python | 3.10+ | [python.org](https://www.python.org/) |
| Node.js | 20+ | [nodejs.org](https://nodejs.org/) |
| PostgreSQL | 15+ | [postgresql.org](https://www.postgresql.org/) |

### Backend Setup

```bash
cd backend

# Create and activate virtual environment
python -m venv venv
venv\Scripts\activate          # Windows
# source venv/bin/activate     # macOS / Linux

# Install dependencies
pip install -r requirements.txt

# Set environment variables
cp .env.example .env
# Edit .env → set OPENAI_API_KEY and DATABASE_URL

# Start the backend
uvicorn main:app --reload --port 8000
```

Backend available at: **http://localhost:8000**

### Frontend Setup

```bash
cd frontend

# Install dependencies
npm install

# Start the dev server
npm run dev
```

Frontend available at: **http://localhost:5173**

---

## 🔑 Environment Variables

### Root `.env` (used by Docker Compose)

| Variable | Required | Description | Example |
|----------|----------|-------------|---------|
| `OPENAI_API_KEY` | ✅ | OpenAI API key for Vision + Text models | `sk-proj-...` |
| `OPENAI_BASE_URL` | No | OpenAI API base URL | `https://api.openai.com/v1` |
| `OPENAI_FAST_MODEL` | No | Model for text tasks (classification, extraction) | `gpt-4o-mini` |
| `OPENAI_VISION_MODEL` | No | Model for document image analysis | `gpt-4o` |
| `OPENAI_EMBEDDING_MODEL` | No | Model for semantic similarity | `text-embedding-3-small` |
| `DATABASE_URL` | ✅ | PostgreSQL connection string | `postgresql://postgres:postgres@db:5432/clearancex` |
| `CORS_ORIGINS` | No | Comma-separated allowed frontend origins | `http://localhost:3000` |

> **Templates:** [`/.env.example`](.env.example) · [`backend/.env.example`](backend/.env.example)

### Frontend (build-time)

| Variable | Default | Description |
|----------|---------|-------------|
| `VITE_API_URL` | `http://localhost:8000/api` | Backend API base URL (set at Docker build time) |

---

## 🗄️ Database & Migrations

**No manual migration steps required.** ClearanceX uses automatic schema creation.

On startup, FastAPI calls `init_db()` via a lifespan hook, which creates all required PostgreSQL tables if they don't exist:

| Table | Purpose |
|-------|---------|
| `dossiers` | Shipment dossier records and processing status |
| `dossier_documents` | Per-document classification and extraction state |
| `norm_cache` | Normalization cache for canonical entity values |

This works identically in Docker (`docker compose up`) and local development (`uvicorn main:app --reload`).

---

## 🧪 Demo Mode

ClearanceX includes a **built-in demo** that works without uploading documents or configuring an API key. The demo ships with pre-processed PDFs from the `demo/` folder and showcases:

- **3 Documents:** Commercial Invoice, Packing List, and Airway Bill with intentional discrepancies
- **Discrepancy #1:** Gross Weight mismatch — `450.0 kg` (Invoice) vs `448.5 kg` (AWB)
- **Discrepancy #2:** Consignee Name mismatch — `"ABC Textiles Ltd"` vs `"ABC Textiles Ltd."` (trailing period)
- **Full Pipeline Output:** Knowledge Graph visualization, XAI Reasoning cards, Counterfactual suggestions, and ASYCUDA XML export

The demo loads automatically when no dossiers have been uploaded.

---

## 📁 Project Structure

```
ants/
├── backend/                          # FastAPI backend
│   ├── ai_pipeline/                  # AI processing engine
│   │   ├── openai_client.py          #   OpenAI Vision + Text API wrapper
│   │   ├── classifier.py             #   Document type classifier
│   │   ├── entity_extractor.py       #   Structured entity extraction
│   │   ├── table_extractor.py        #   Multi-line table parser
│   │   ├── normalizer.py             #   Unit/date/term normalization
│   │   ├── ocr_engine.py             #   PaddleOCR spatial text extraction
│   │   ├── confidence.py             #   Confidence score calculation
│   │   ├── pipeline.py               #   Full pipeline orchestrator
│   │   ├── mock_pipeline.py          #   Demo mode pipeline (no API key)
│   │   └── test_*.py                 #   Unit tests for each module
│   ├── reasoning/                    # Neuro-symbolic reasoning engine
│   │   ├── knowledge_builder.py      #   NetworkX graph construction
│   │   ├── rule_evaluator.py         #   Deterministic customs rules
│   │   ├── discrepancy_engine.py     #   Cross-document conflict detector
│   │   ├── entity_resolution.py      #   Fuzzy matching + resolution
│   │   ├── xai_compiler.py           #   4-layer XAI payload generator
│   │   ├── counterfactual.py         #   "What-if" fix suggestions
│   │   ├── audit_trail.py            #   SHA-256 tamper-evident event log
│   │   ├── asycuda_export.py         #   CUSDEC XML generator
│   │   ├── semantic_fallback.py      #   Semantic similarity fallback
│   │   └── test_*.py                 #   Unit tests for reasoning
│   ├── api/                          # REST API layer
│   │   ├── routes.py                 #   Main API endpoints (21 routes)
│   │   └── upload_router.py          #   Document upload + status polling
│   ├── database/                     # Data access layer
│   │   └── connection.py             #   SQLAlchemy engine + init_db()
│   ├── xai_types.py                  # Shared XAI data structures
│   ├── schema.sql                    # Full PostgreSQL schema reference
│   ├── main.py                       # FastAPI app entry point
│   ├── requirements.txt              # Python dependencies
│   ├── Dockerfile                    # Backend container build
│   └── .env.example                  # Environment variable template
│
├── frontend/                         # React + TypeScript frontend
│   ├── src/
│   │   ├── components/
│   │   │   ├── screens/              # 11 page-level views
│   │   │   │   ├── ScreenOverview.tsx          # Hero + dashboard
│   │   │   │   ├── ScreenDossiers.tsx          # Dossier management
│   │   │   │   ├── ScreenReviewWorkspace.tsx   # Document review + resolution
│   │   │   │   ├── ScreenDiscrepancies.tsx     # Discrepancy explorer
│   │   │   │   ├── ScreenKnowledgeGraph.tsx    # Interactive graph viewer
│   │   │   │   ├── ScreenBatchFiling.tsx       # Batch processing
│   │   │   │   ├── ScreenAsycudaGateway.tsx    # CUSDEC XML export
│   │   │   │   ├── ScreenAuditTrail.tsx        # SHA-256 event log
│   │   │   │   ├── ScreenTariffDirectory.tsx   # HS code lookup
│   │   │   │   ├── ScreenAuth.tsx              # Authentication
│   │   │   │   └── ScreenSettings.tsx          # App settings
│   │   │   ├── layout/
│   │   │   │   └── Header.tsx        # Navigation + sidebar drawer
│   │   │   └── review/
│   │   │       └── KeyFieldReconciliationPanel.tsx
│   │   ├── hooks/
│   │   │   ├── useScrollAnimations.ts  # GSAP ScrollTrigger utilities
│   │   │   └── useShipment.tsx         # Shipment context provider
│   │   ├── utils/
│   │   │   └── api.ts                  # Axios API client (typed)
│   │   └── types/
│   │       └── index.ts                # Shared TypeScript interfaces
│   ├── Dockerfile                    # Multi-stage build (node → nginx)
│   ├── nginx.conf                    # Reverse proxy config
│   └── package.json                  # Frontend dependencies
│
├── demo/                             # Pre-processed demo shipping PDFs
├── docker-compose.yml                # Full-stack orchestration
├── .env.example                      # Root environment template
├── .gitignore
├── LICENSE
└── README.md
```

---

## 🔧 Troubleshooting

### Docker Issues

**`docker compose up` fails with "port already in use"**
```bash
# Check which process is using the port:
netstat -ano | findstr :3000     # Windows
lsof -i :3000                    # macOS / Linux

# Or change the host port in docker-compose.yml:
# ports: - "3001:80"   ← change left side only
```

**Container exits immediately / backend crashes on startup**
```bash
# Check logs:
docker compose logs backend

# Most common cause: missing OPENAI_API_KEY in .env
# The app still works in demo mode without a key, but real
# document processing requires a valid OpenAI API key.
```

**Database tables not created**
```bash
# Force-recreate from scratch:
docker compose down -v       # wipes DB volume
docker compose up --build
```

**Build fails with ECONNRESET / network timeout**
```bash
# Retry — this is a transient npm/pip network issue inside Docker.
docker compose up --build
```

### Local Development Issues

**`uvicorn` crashes with `ModuleNotFoundError`**
```bash
# Ensure you activated the virtual environment:
venv\Scripts\activate           # Windows
source venv/bin/activate        # macOS / Linux
pip install -r requirements.txt
```

**Frontend shows "Failed to connect to backend"**
```bash
# Verify the backend is running on port 8000:
curl http://localhost:8000/health

# Check that VITE_API_URL in frontend/.env matches the backend:
# Default: VITE_API_URL=http://localhost:8000/api
```

---

## 👥 Team Information

**Team Name:** Ants

| Member | Primary Contribution |
|--------|---------------------|
| **Nadija** | AI Pipeline — Document classification, entity extraction, OCR engine, table extractor, and frontend UI |
| **Kaveen** | Neuro-Symbolic Engine — Knowledge graph builder, rule evaluator, discrepancy engine, entity resolution, and frontend integration |
| **Aloka** | XAI Compiler — 4-layer XAI payload generation, counterfactual reasoning, and audit trail |

---

## ⚠️ Limitations & Assumptions

### Limitations
- **Document Format:** Currently optimized for PDF documents. Image-only inputs (JPEG/PNG) may have reduced OCR accuracy.
- **Language:** OCR and entity extraction are optimized for English-language documents. Non-English documents are not supported.
- **Document Types:** The classifier is trained on 4 document types: Commercial Invoice, Packing List, Airway Bill, and Bill of Lading. Other document types (e.g., Certificate of Origin, Insurance Certificate) are not yet handled.
- **Concurrency:** The demo uses a single PostgreSQL instance. For production-scale batch processing, connection pooling and worker scaling would be needed.
- **ASYCUDA Format:** The CUSDEC XML generator follows the general ASYCUDA World DTI schema. Country-specific field mappings may require adjustment for non-Sri Lankan customs authorities.

### Assumptions
- Users have a valid **OpenAI API key** with access to GPT-4o and GPT-4o-mini models (for real document processing; demo mode works without a key).
- Documents within a dossier belong to the **same shipment** and share common reference data (consignee, weights, etc.).
- Weight tolerances follow industry-standard thresholds (±1% for gross weight, exact match for package count).
- The target ASYCUDA system accepts **DTI bulk upload** via XML/TXT file import.

---

## 📝 Change Log

### Technology Changes from Original Proposal

| What Changed | From (Proposal) | To (Final) | Why |
|-------------|-----------------|------------|-----|
| **AI Provider** | Google Gemini 2.0 Flash | OpenAI GPT-4o / GPT-4o-mini | OpenAI's structured output mode (`response_format`) provides more reliable JSON extraction for document entities. GPT-4o Vision also showed better spatial understanding of complex shipping documents. |
| **OCR Engine** | LayoutLMv3 + Spatial OCR | PaddleOCR 2.7 | PaddleOCR provided more stable and accurate bounding box extraction out-of-the-box without requiring GPU-intensive model fine-tuning. It integrates directly with our pipeline as a lightweight dependency. |
| **Frontend Animations** | None specified | GSAP 3 + ScrollTrigger | Added to create a premium, enterprise-grade user experience with scroll-driven animations, parallax effects, and cinematic hero transitions — while respecting `prefers-reduced-motion`. |
| **CSS Framework** | Not specified | Tailwind CSS v4 | Chosen for its utility-first approach and design token system, enabling rapid, consistent UI development across all 11 screens. |

> The **core problem**, **target users** (shipping executives), and **core solution** (AI-powered customs document reconciliation with XAI) remain unchanged from the original proposal.

---

## 📜 License

This project is the intellectual property of **Team Ants**. See the [LICENSE](LICENSE) file for full terms.

Submitted for evaluation at the **CodeSplash'26 Hackathon**. The CodeSplash Organizing Committee is granted permission to access this repository for evaluation and to showcase submitted materials for promotional, educational, and event-related purposes with appropriate acknowledgment.
