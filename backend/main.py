# backend/main.py
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import os

from api.routes import router
from api.upload_router import router as upload_router

app = FastAPI(
    title="ClearanceX API",
    description="6-Layer Explainable AI Copilot for Customs Declaration Compliance",
    version="0.1.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173","http://localhost:3000","http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

os.makedirs("uploads", exist_ok=True)
app.mount("/uploads", StaticFiles(directory="uploads"), name="uploads")

# Existing routes (mock extraction / graph / discrepancy endpoints)
app.include_router(router)

# Phase 09 — Dossier Upload + status polling
# POST /api/upload
# GET  /api/upload/{dossier_id}/status
app.include_router(upload_router)

@app.get("/health")
async def health():
    return {"status": "ok", "service": "clearancex", "version": "0.1.0"}

