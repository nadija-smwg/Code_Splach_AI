# ClearanceX 🚢

**ClearanceX** is an Intelligent Decision Support System that automates the ingestion, reconciliation, and validation of complex shipping dossiers for both **Imports** and **Exports**. Built with **Explainable AI (XAI)** at its core, it acts as a copilot for shipping executives to instantly flag discrepancies, verify data via traceable visual attributions, and generate one-click ASYCUDA-compliant export files for Sri Lanka Customs.

---

## 🎯 The Problem

In the apparel manufacturing sector, clearing imported raw materials or exporting finished goods requires compiling a detailed Customs Declaration (CUSDEC) via the ASYCUDA system. This manual process relies on unstructured, multi-page shipping dossiers (Commercial Invoices, Packing Lists, Airway Bills, etc.), leading to frequent discrepancies, human error, rejected declarations, and severe financial penalties (e.g., port demurrage or bank payment freezes).

## 🚀 The Solution

ClearanceX mitigates these risks by providing an automated pipeline that:
- Reads unstructured supply chain documents using LayoutLMv3 and Spatial OCR.
- Extracts multi-line tabular items and header-level metadata.
- Cross-references values (e.g., Gross Weight, Package Count, Incoterms) across different documents to flag mismatches.
- Compiles validated data into standard ASYCUDA-compliant XML/TXT files for Direct Trader Input (DTI) bulk upload.

---

## ✨ Key Features

- **Document Ingestion & OCR:** Automatic classification of shipping documents with $\ge 95\%$ confidence and bounding box coordinate extraction.
- **Entity Extraction & Normalization:** Extracts critical details like Consignee details, Incoterms, Gross/Net weights, and item descriptions, normalizing varying terminologies into canonical forms.
- **Cross-Document Reconciliation Engine:** Compares data points across multiple documents (e.g., Packing List vs. Transport Documents) and highlights variances.
- **Explainable AI (XAI) Interface:**
  - **Visual Attribution:** Split-screen view highlighting the exact location in the original PDF source.
  - **Conflict Explanations:** Natural language explanations and actionable recommendations for every mismatch.
  - **Confidence Scoring:** Color-coded confidence scores (Green $\ge 90\%$, Yellow $70\text{--}89\%$, Red $< 70\%$) for extracted values.
- **One-Click ASYCUDA Export:** Generates bulk upload files (XML/TXT) to eliminate manual copy-pasting during customs declarations.

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    Browser (localhost:3000)                  │
│          React + TypeScript + Vite  (nginx in Docker)       │
└──────────────────────────┬──────────────────────────────────┘
                           │ HTTP / REST
                           ▼
┌─────────────────────────────────────────────────────────────┐
│               FastAPI Backend (localhost:8000)               │
│  ┌──────────────┐  ┌───────────────┐  ┌─────────────────┐  │
│  │  AI Pipeline │  │ Neuro-Symbolic│  │  ASYCUDA Export │  │
│  │  (LayoutLMv3 │  │ Rule Evaluator│  │  (XML/TXT gen.) │  │
│  │   + Gemini)  │  │ + XAI Compiler│  │                 │  │
│  └──────────────┘  └───────────────┘  └─────────────────┘  │
└──────────────────────────┬──────────────────────────────────┘
                           │ SQLAlchemy ORM
                           ▼
┌─────────────────────────────────────────────────────────────┐
│             PostgreSQL 15  (localhost:5433)                  │
└─────────────────────────────────────────────────────────────┘
```

### Tech Stack

| Layer | Technology |
|-------|-----------|
| **Frontend** | React 19, TypeScript, Vite, vis.js (Knowledge Graph) |
| **Backend** | Python 3.11, FastAPI, SQLAlchemy |
| **AI/ML Core** | Google Gemini 2.0 Flash, LayoutLMv3, Spatial OCR |
| **Database** | PostgreSQL 15 |
| **Containerisation** | Docker + Docker Compose |

---

## 🛠️ Getting Started

### Prerequisites

| Tool | Minimum Version | Install |
|------|----------------|---------|
| Docker Desktop | 24.x | https://docs.docker.com/get-docker/ |
| Docker Compose | v2.x (bundled with Docker Desktop) | — |
| Git | Any | https://git-scm.com/ |

> **Note:** Node.js and Python are only required for local development without Docker. For the standard demo setup, Docker is all you need.

---

## 🐳 Quick Start — Docker (Recommended)

This is the fastest way to run the full stack. One command starts the database, backend, and frontend together.

**Step 1 — Clone the repository:**
```bash
git clone https://github.com/codesplash26-hackathon/ants.git
cd ants
```

**Step 2 — Set up environment variables:**
```bash
# Copy the example env file and fill in your Gemini API key
cp .env.example .env      # (or manually create .env at the project root)
```

Edit `.env` and set your key:
```env
GEMINI_API_KEY=your_real_gemini_api_key_here
GEMINI_MODEL=gemini-2.0-flash
DATABASE_URL=postgresql://postgres:postgres@db:5432/clearancex
CORS_ORIGINS=http://localhost:3000,http://localhost:5173
```

> **Where to get a Gemini API key:** https://aistudio.google.com/app/apikey

**Step 3 — Build and start all services:**
```bash
docker compose up --build
```

This will:
1. Pull the PostgreSQL 15 image and start the database
2. Build and start the FastAPI backend (auto-creates all DB tables on startup)
3. Build and start the React frontend via nginx

**Step 4 — Open the app:**

| Service | URL |
|---------|-----|
| 🖥️ Frontend (React UI) | http://localhost:3000 |
| ⚙️ Backend API | http://localhost:8000 |
| 📖 API Docs (Swagger) | http://localhost:8000/docs |
| 🩺 Health Check | http://localhost:8000/health |

**To stop:**
```bash
docker compose down
```

**To stop and wipe the database:**
```bash
docker compose down -v
```

---

## 💻 Local Development (Without Docker)

If you prefer to run services individually without Docker:

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
# Edit .env and fill in GEMINI_API_KEY and DATABASE_URL

# Start the backend
uvicorn main:app --reload --port 8000
```

Backend will be available at: **http://localhost:8000**

### Frontend Setup

```bash
cd frontend

# Install dependencies
npm install

# Set environment variables
cp .env.example .env
# .env already contains: VITE_API_URL=http://localhost:8000/api

# Start the dev server
npm run dev
```

Frontend will be available at: **http://localhost:5173**

---

## 🗄️ Database & Migrations

**ClearanceX uses automatic schema creation** — no manual migration steps required.

On startup, the FastAPI backend calls `init_db()` via a lifespan hook, which creates all required PostgreSQL tables if they do not exist:

- `dossiers` — shipment dossier records
- `dossier_documents` — per-document processing state
- `norm_cache` — normalization cache for entity values

This happens automatically whether you use Docker (`docker compose up`) or run locally (`uvicorn main:app --reload`).

---

## 🔑 Environment Variables

### Root `.env` / `backend/.env`

| Variable | Required | Description | Example |
|----------|----------|-------------|---------|
| `GEMINI_API_KEY` | ✅ Yes | Google Gemini API key for AI extraction | `AIsomething...` |
| `GEMINI_MODEL` | No | Gemini model to use (defaults to `gemini-2.0-flash`) | `gemini-2.0-flash` |
| `DATABASE_URL` | ✅ Yes | PostgreSQL connection string | `postgresql://postgres:postgres@localhost:5432/clearancex` |
| `CORS_ORIGINS` | No | Comma-separated allowed frontend origins | `http://localhost:3000,http://localhost:5173` |

> Template: [`backend/.env.example`](backend/.env.example)

### `frontend/.env`

| Variable | Required | Description | Default |
|----------|----------|-------------|---------|
| `VITE_API_URL` | No | Backend API base URL | `http://localhost:8000/api` |

> Template: [`frontend/.env.example`](frontend/.env.example)

---

## 🧪 Demo Mode

The app includes a built-in **demo mode** that works without uploading real shipping documents. The demo uses pre-processed PDFs from the `demo/` folder and showcases:

- A Commercial Invoice, Packing List, and Airway Bill with intentional discrepancies
- A Gross Weight mismatch (450.0 kg vs 448.5 kg) between Invoice and AWB
- A Consignee Name mismatch ("ABC Textiles Ltd" vs "ABC Textiles Ltd.")
- Full Knowledge Graph, XAI Reasoning, and ASYCUDA export output

To use demo mode, sign in with the demo credentials shown on the login screen.

---

## 🔧 Troubleshooting

### Docker Issues

**`docker compose up` fails with "port already in use"**
```bash
# The database port 5433 or backend port 8000 is taken.
# Check what's using it:
netstat -ano | findstr :5433   # Windows
lsof -i :5433                  # macOS / Linux

# Or change the host port in docker-compose.yml:
# ports: - "5434:5432"  ← change left side only
```

**Container exits immediately / backend crashes on startup**
```bash
# Check logs:
docker compose logs backend

# Most likely cause: missing GEMINI_API_KEY in .env
# Ensure .env exists at the project root with a valid key.
```

**Database tables not created**
```bash
# Force-recreate from scratch:
docker compose down -v   # wipes DB volume
docker compose up --build
```

### Local Dev Issues

**`uvicorn` crashes with `ModuleNotFoundError`**
```bash
# Ensure you activated the virtual environment first:
venv\Scripts\activate        # Windows
source venv/bin/activate     # macOS / Linux
pip install -r requirements.txt
```

**Frontend shows "Failed to connect to backend"**
```bash
# Check that the backend is running on port 8000.
# Check that VITE_API_URL in frontend/.env matches the backend URL.
# Default: VITE_API_URL=http://localhost:8000/api
```

**`npm run dev` fails with "Cannot find module"**
```bash
cd frontend
npm install   # reinstall all dependencies
npm run dev
```

---

## 📁 Project Structure

```
ants/
├── backend/                  # FastAPI backend
│   ├── ai_pipeline/          # OCR, classification, entity extraction (Nadija)
│   ├── reasoning/            # Neuro-symbolic engine, XAI compiler (Aloka)
│   ├── api/                  # REST API routes
│   ├── database/             # SQLAlchemy models + DB connection
│   ├── demo/                 # Pre-processed demo PDFs
│   ├── main.py               # FastAPI app entry point
│   ├── requirements.txt
│   ├── Dockerfile
│   └── .env.example
├── frontend/                 # React + TypeScript frontend (Kaveen)
│   ├── src/
│   │   ├── components/       # All UI components
│   │   ├── pages/            # Page-level views
│   │   ├── hooks/            # Custom React hooks
│   │   ├── utils/api.ts      # API client
│   │   └── types/index.ts    # Shared TypeScript types
│   ├── Dockerfile
│   ├── nginx.conf
│   └── .env.example
├── demo/                     # Demo shipping PDFs
├── docker-compose.yml        # One-command full-stack setup
├── .env.example              # Root env template (for Docker)
└── README.md
```

---

## 📜 License

This project is licensed under the terms of the [LICENSE](LICENSE) file included in the repository.
