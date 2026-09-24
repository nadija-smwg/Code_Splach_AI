# backend/api/upload_router.py
# Phase 09 — Dossier Upload API
#
# POST /api/upload          — accept 1-N PDFs for one shipment, return dossier_id (202)
# GET  /api/upload/{id}/status — poll per-document processing status + results

import logging
import uuid
from pathlib import Path

from fastapi import APIRouter, BackgroundTasks, File, HTTPException, UploadFile
from fastapi.responses import JSONResponse

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/upload", tags=["upload"])

UPLOAD_DIR = Path("uploads")
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

# Lazy singleton — avoids loading heavy AI deps at import time
_manager = None


def _get_manager():
    global _manager
    if _manager is None:
        from ai_pipeline.dossier_manager import DossierManager

        _manager = DossierManager()
    return _manager


# ======================================================================
# POST /api/upload
# ======================================================================


@router.post("", summary="Upload one shipment dossier (1–N PDFs)")
async def upload_dossier(
    background_tasks: BackgroundTasks,
    files: list[UploadFile] = File(...),
) -> JSONResponse:
    """
    Upload all documents belonging to ONE shipment in a single request.

    - Validates all files are PDFs before saving any.
    - Generates a UUID dossier_id.
    - Saves files to uploads/{dossier_id}/{filename}.
    - Creates DB rows (dossiers + dossier_documents).
    - Queues background processing (OCR → Classify → Extract → Normalize).
    - Returns 202 immediately with the dossier_id and a status URL.
    """
    if not files:
        raise HTTPException(
            status_code=422,
            detail="At least one PDF file is required.",
        )

    # Validate all PDFs before touching the filesystem
    for upload in files:
        if not (upload.filename or "").lower().endswith(".pdf"):
            raise HTTPException(
                status_code=422,
                detail=f"'{upload.filename}' is not a PDF. Only PDF files are accepted.",
            )

    dossier_id = str(uuid.uuid4())
    dossier_dir = UPLOAD_DIR / dossier_id
    dossier_dir.mkdir(parents=True, exist_ok=True)

    saved: list[dict] = []

    for upload in files:
        dest = dossier_dir / upload.filename
        content = await upload.read()
        dest.write_bytes(content)
        saved.append(
            {
                "original_name": upload.filename,
                "file_path": str(dest),
            }
        )
        logger.info(
            "Saved %s → %s (%d bytes)", upload.filename, dest, len(content)
        )

    manager = _get_manager()

    doc_ids = manager.create_dossier(
        dossier_id=dossier_id,
        documents=saved,
    )

    background_tasks.add_task(
        manager.process_dossier,
        dossier_id=dossier_id,
    )

    logger.info(
        "Dossier %s created with %d document(s)", dossier_id, len(saved)
    )

    return JSONResponse(
        status_code=202,
        content={
            "dossier_id": dossier_id,
            "document_count": len(saved),
            "document_ids": doc_ids,
            "status": "processing",
            "status_url": f"/api/upload/{dossier_id}/status",
        },
    )


# ======================================================================
# GET /api/upload/{dossier_id}/status
# ======================================================================


@router.get("/{dossier_id}/status", summary="Poll dossier processing status")
async def dossier_status(dossier_id: str) -> JSONResponse:
    """
    Returns the current processing state for each document in the dossier.

    Document status values:
        pending     — queued, not yet started
        processing  — pipeline running
        done        — ExtractionResult available in extraction_result
        error       — failed; error_message contains the reason

    Dossier status:
        pending     — no documents started yet
        processing  — at least one document still running
        done        — all documents completed successfully
        error       — at least one document failed
    """
    manager = _get_manager()
    result = manager.get_status(dossier_id)

    if result is None:
        raise HTTPException(
            status_code=404,
            detail=f"Dossier '{dossier_id}' not found.",
        )

    return JSONResponse(content=result)
