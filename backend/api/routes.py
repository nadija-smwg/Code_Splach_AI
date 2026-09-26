# backend/api/routes.py
#
# Smart routing: DB-first with demo fallback
# - Real dossier_id (UUID in PostgreSQL)  → query DB extraction results
# - Demo IDs ("demo-shipment", "demo")    → run MockPipeline on demo PDFs
# - Unknown IDs / DB unavailable          → fall back to demo

from fastapi import APIRouter, UploadFile, File, HTTPException
from typing import List
import uuid, os, dataclasses, logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api")
UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)


# ══════════════════════════════════════════════════════════════════
# HELPERS — Data Resolution (DB vs Demo)
# ══════════════════════════════════════════════════════════════════

DEMO_IDS = {"demo-shipment", "demo"}

DOCUMENT_LABELS = {
    "commercial_invoice": "Commercial Invoice",
    "packing_list": "Packing List",
    "awb": "Air Waybill",
    "bl": "Bill of Lading",
    "freight_invoice": "Freight Invoice",
    "delivery_order": "Delivery Order",
}


def _document_label(document_type: str) -> str:
    return DOCUMENT_LABELS.get(document_type, document_type.replace("_", " ").title())


def _is_demo(shipment_id: str) -> bool:
    """Return True for known demo/test fixture IDs."""
    return shipment_id in DEMO_IDS


def _fetch_dossier_documents(shipment_id: str):
    """
    Query PostgreSQL for completed extraction results for a real dossier.

    Returns:
        list[dict] — pipeline result dicts (one per document), or
        None       — if dossier not found, not yet done, or DB unavailable.
    """
    try:
        from database.connection import SessionLocal
        from database.models import DossierDocument, Dossier
        import uuid as _uuid

        try:
            dossier_uuid = _uuid.UUID(shipment_id)
        except ValueError:
            return None

        db = SessionLocal()
        try:
            dossier = db.query(Dossier).filter(Dossier.id == dossier_uuid).first()
            if dossier is None:
                return None

            docs = (
                db.query(DossierDocument)
                .filter(
                    DossierDocument.dossier_id == dossier_uuid,
                    DossierDocument.status == "done",
                )
                .order_by(DossierDocument.created_at)
                .all()
            )
            if not docs:
                return None

            results = []
            for doc in docs:
                extraction = doc.extraction_json
                if extraction is None:
                    continue
                if isinstance(extraction, str):
                    import json as _json
                    extraction = _json.loads(extraction)
                if not isinstance(extraction, dict):
                    continue
                if "document_id" not in extraction:
                    extraction["document_id"] = str(doc.id)
                extraction["document_type"] = (
                    doc.document_type or extraction.get("document_type", "unknown")
                )
                extraction["source_filename"] = doc.original_name
                type_label = _document_label(extraction["document_type"])
                extraction["source_label"] = f"{type_label} — {doc.original_name}"
                results.append(extraction)

            return results if results else None
        finally:
            db.close()
    except Exception as exc:
        logger.warning("_fetch_dossier_documents(%s): %s", shipment_id, exc)
        return None


def _get_demo_documents() -> list:
    """Run MockPipeline on the three demo PDFs."""
    from ai_pipeline.mock_pipeline import MockPipeline

    mp = MockPipeline()
    demo_docs = [
        ("demo/commercial_invoice.pdf", "doc_001"),
        ("demo/packing_list.pdf",       "doc_002"),
        ("demo/awb.pdf",                "doc_003"),
    ]
    results = []
    for path, doc_id in demo_docs:
        document = mp.process_document(path, doc_id)
        document["source_filename"] = os.path.basename(path)
        document["source_label"] = _document_label(document["document_type"])
        results.append(document)
    return results


def _get_documents_for_shipment(shipment_id: str) -> list:
    """
    Resolve pipeline result dicts for a shipment.
    Always uses real DB data. Never falls back to demo.
    """
    if _is_demo(shipment_id):
        return _get_demo_documents()
    real = _fetch_dossier_documents(shipment_id)
    return real if real is not None else []


def _get_field_resolutions(shipment_id: str) -> dict:
    """Load reviewer decisions keyed by canonical field ID."""
    try:
        from database.connection import SessionLocal
        from database.models import FieldResolution

        db = SessionLocal()
        try:
            rows = db.query(FieldResolution).filter(FieldResolution.shipment_id == shipment_id).all()
            return {
                row.canonical_field_id: {
                    "resolved_value": row.resolved_value,
                    "source_assertion_id": row.source_assertion_id,
                    "reason": row.reason,
                    "resolved_by": row.resolved_by,
                }
                for row in rows
            }
        finally:
            db.close()
    except Exception as exc:
        logger.warning("Could not load field resolutions for %s: %s", shipment_id, exc)
        return {}


def _get_declaration_metadata(shipment_id: str) -> dict:
    """Load reviewer-supplied Customs/profile details for the active dossier."""
    try:
        from database.connection import SessionLocal
        from database.models import DeclarationMetadata

        db = SessionLocal()
        try:
            rows = db.query(DeclarationMetadata).filter(
                DeclarationMetadata.shipment_id == shipment_id
            ).all()
            return {row.field_name: row.value for row in rows if row.value not in (None, "")}
        finally:
            db.close()
    except Exception as exc:
        logger.warning("Could not load declaration metadata for %s: %s", shipment_id, exc)
        return {}


def _resolve_shipment_fields(shipment_id: str, documents: list) -> list:
    """Resolve source assertions, then apply persisted reviewer decisions."""
    from reasoning.entity_resolution import apply_manual_resolutions, resolve_documents

    fields = resolve_documents(shipment_id, documents)
    return apply_manual_resolutions(fields, _get_field_resolutions(shipment_id))


# ══════════════════════════════════════════════════════════════════
# HELPERS — Knowledge Graph Building
# ══════════════════════════════════════════════════════════════════

def _build_graph_from_documents(shipment_id: str, documents: list):
    """
    Generic graph builder: works with any list of pipeline result dicts.
    Resolves source entities into canonical shipment fields. Each raw value is
    retained as a source assertion, rather than being overwritten by a merge.

    Returns (KnowledgeBuilder, documents).
    """
    from reasoning.knowledge_builder import KnowledgeBuilder

    kb = KnowledgeBuilder()
    kb.add_shipment_node(shipment_id)

    for doc in documents:
        kb.add_document_node(doc["document_id"], doc.get("document_type", "unknown"))

    for field in _resolve_shipment_fields(shipment_id, documents):
        kb.add_canonical_field_node(field, shipment_id)
        for assertion in field["assertions"]:
            kb.add_source_assertion_node(assertion)

    return kb, documents


def _build_demo_graph(shipment_id: str):
    """
    Demo-specific graph builder: runs MockPipeline on demo PDFs and builds
    a curated knowledge graph with specific MUST_MATCH edges.
    Preserved for backward compatibility with the demo scenario.
    """
    from ai_pipeline.mock_pipeline import MockPipeline
    from reasoning.knowledge_builder import KnowledgeBuilder
    from xai_types import ExtractedEntity

    mp = MockPipeline()
    demo_docs = [
        ("demo/commercial_invoice.pdf", "doc_001"),
        ("demo/packing_list.pdf",       "doc_002"),
        ("demo/awb.pdf",                "doc_003"),
    ]
    documents = [mp.process_document(path, doc_id) for path, doc_id in demo_docs]

    kb = KnowledgeBuilder()
    for doc in documents:
        kb.add_document_node(doc["document_id"], doc["document_type"])

    def to_entity(e: dict) -> ExtractedEntity:
        return ExtractedEntity(
            entity_type=e["entity_type"],
            value=e["value"],
            normalized_value=e.get("normalized_value", e["value"]),
            unit=e.get("unit"),
            page=e.get("page", 1),
            bbox=e.get("bbox", []),
            extraction_confidence=e.get("extraction_confidence", 0.9),
            ocr_text=e.get("value", ""),
        )

    # GROSS_WEIGHT: invoice vs packing list vs AWB
    inv_gw = next((e for e in documents[0]["entities"] if e["entity_type"] == "GROSS_WEIGHT"), None)
    awb_gw = next((e for e in documents[2]["entities"] if e["entity_type"] == "GROSS_WEIGHT"), None)
    pl_gw  = next((e for e in documents[1]["entities"] if e["entity_type"] == "GROSS_WEIGHT"), None)

    if inv_gw:
        kb.add_entity_node("n_inv_gw", to_entity(inv_gw), "doc_001")
    if awb_gw:
        kb.add_entity_node("n_awb_gw", to_entity(awb_gw), "doc_003")
    if pl_gw:
        kb.add_entity_node("n_pl_gw",  to_entity(pl_gw),  "doc_002")

    if inv_gw and awb_gw:
        kb.add_relationship("n_inv_gw", "n_awb_gw", "MUST_MATCH")
    if inv_gw and pl_gw:
        kb.add_relationship("n_inv_gw", "n_pl_gw", "MUST_MATCH")

    # CONSIGNEE_NAME: invoice vs AWB
    inv_cn = next((e for e in documents[0]["entities"] if e["entity_type"] == "CONSIGNEE_NAME"), None)
    awb_cn = next((e for e in documents[2]["entities"] if e["entity_type"] == "CONSIGNEE_NAME"), None)

    if inv_cn:
        kb.add_entity_node("n_inv_cn", to_entity(inv_cn), "doc_001")
    if awb_cn:
        kb.add_entity_node("n_awb_cn", to_entity(awb_cn), "doc_003")
    if inv_cn and awb_cn:
        kb.add_relationship("n_inv_cn", "n_awb_cn", "MUST_MATCH")

    return kb, documents


def _get_graph_for_shipment(shipment_id: str):
    """
    Smart graph router:
    Always uses real DB data. Never falls back to demo.
    """
    return _build_graph_from_documents(shipment_id, _get_documents_for_shipment(shipment_id))


# ══════════════════════════════════════════════════════════════════
# ENDPOINTS
# ══════════════════════════════════════════════════════════════════


@router.post("/shipments/upload")
async def upload_shipment(files: List[UploadFile] = File(...)):
    """Legacy upload fallback — kept for compatibility."""
    for file in files:
        if not (file.filename or "").lower().endswith(".pdf"):
            raise HTTPException(
                status_code=400,
                detail=f"Only PDF files accepted. '{file.filename}' is not a PDF.",
            )

    shipment_id = str(uuid.uuid4())
    shipment_dir = os.path.join(UPLOAD_DIR, shipment_id)
    os.makedirs(shipment_dir, exist_ok=True)

    documents = []
    for file in files:
        doc_id = str(uuid.uuid4())
        file_path = os.path.join(shipment_dir, f"{doc_id}_{file.filename}")
        with open(file_path, "wb") as f:
            f.write(await file.read())
        documents.append({"document_id": doc_id, "filename": file.filename, "status": "uploaded"})

    return {"shipment_id": shipment_id, "status": "processing", "documents": documents}


@router.get("/shipments/{shipment_id}/status")
async def get_shipment_status(shipment_id: str):
    # Real dossier — query PostgreSQL
    try:
        from database.connection import SessionLocal
        from database.models import DossierDocument, Dossier
        import uuid as _uuid

        dossier_uuid = _uuid.UUID(shipment_id)
        db = SessionLocal()
        try:
            dossier = db.query(Dossier).filter(Dossier.id == dossier_uuid).first()
            if dossier is not None:
                docs = (
                    db.query(DossierDocument)
                    .filter(DossierDocument.dossier_id == dossier_uuid)
                    .order_by(DossierDocument.created_at)
                    .all()
                )
                doc_list = []
                for doc in docs:
                    conf = None
                    if doc.extraction_json and isinstance(doc.extraction_json, dict):
                        conf = doc.extraction_json.get("classification_confidence")
                    doc_list.append({
                        "document_id": str(doc.id),
                        "filename": doc.original_name,
                        "document_type": doc.document_type or "unknown",
                        "classification_confidence": conf,
                        "status": doc.status,
                    })
                progress = 100 if dossier.status == "done" else (50 if dossier.status == "processing" else 0)
                return {
                    "shipment_id": shipment_id,
                    "status": "completed" if dossier.status == "done" else dossier.status,
                    "progress": progress,
                    "documents": doc_list,
                    "processing_time_ms": None,
                }
        finally:
            db.close()
    except Exception:
        pass

    # Fallback: check uploads directory
    shipment_dir = os.path.join(UPLOAD_DIR, shipment_id)
    if not os.path.isdir(shipment_dir):
        raise HTTPException(status_code=404, detail=f"Shipment '{shipment_id}' not found.")

    documents = []
    for fname in sorted(os.listdir(shipment_dir)):
        if fname.lower().endswith(".pdf"):
            parts = fname.split("_", 1)
            display_name = parts[1] if len(parts) == 2 else fname
            documents.append({
                "document_id": parts[0] if len(parts) == 2 else fname,
                "filename": display_name,
                "document_type": "unknown",
                "classification_confidence": None,
            })

    return {
        "shipment_id": shipment_id, "status": "completed", "progress": 100,
        "documents": documents, "processing_time_ms": None,
    }


@router.get("/shipments/{shipment_id}/extraction")
async def get_extraction(shipment_id: str):
    documents = _get_documents_for_shipment(shipment_id)
    return {"shipment_id": shipment_id, "documents": documents}


@router.get("/shipments/{shipment_id}/graph")
async def get_knowledge_graph(shipment_id: str):
    kb, _ = _get_graph_for_shipment(shipment_id)
    return kb.to_vis_json()


@router.get("/shipments/{shipment_id}/key-fields")
async def get_key_fields(shipment_id: str):
    """Return canonical shipment fields with every document assertion."""
    fields = _resolve_shipment_fields(shipment_id, _get_documents_for_shipment(shipment_id))
    counts = {status: sum(field["status"] == status for field in fields)
              for status in ("match", "conflict", "warning", "pending", "resolved")}
    return {
        "shipment_id": shipment_id,
        "summary": {"total_fields": len(fields), **counts},
        "fields": fields,
    }


@router.post("/shipments/{shipment_id}/field-resolutions")
async def save_field_resolution(shipment_id: str, resolution: dict):
    """Persist a reviewer-selected source value or a verified manual value."""
    documents = _get_documents_for_shipment(shipment_id)
    if not documents:
        raise HTTPException(status_code=404, detail="No processed documents were found for this dossier.")

    canonical_field_id = str(resolution.get("canonical_field_id", "")).strip()
    if not canonical_field_id:
        raise HTTPException(status_code=400, detail="canonical_field_id is required.")

    # Validate against unmodified source evidence. Existing overrides must not
    # be the sole evidence for a subsequent decision.
    from reasoning.entity_resolution import resolve_documents
    source_fields = resolve_documents(shipment_id, documents)
    field = next((item for item in source_fields if item["canonical_field_id"] == canonical_field_id), None)
    if field is None:
        raise HTTPException(status_code=404, detail="The selected canonical field was not found.")

    source_assertion_id = str(resolution.get("source_assertion_id", "")).strip() or None
    if source_assertion_id:
        assertion = next(
            (item for item in field["assertions"] if item["assertion_id"] == source_assertion_id), None
        )
        if assertion is None:
            raise HTTPException(status_code=400, detail="The selected source assertion does not belong to this field.")
        resolved_value = assertion["normalized_value"]
    else:
        manual_value = resolution.get("manual_value")
        if manual_value in (None, ""):
            raise HTTPException(status_code=400, detail="Choose a source value or enter a corrected value.")
        from ai_pipeline.normalizer import EntityNormalizer
        normalized = EntityNormalizer().normalize(field["entity_type"], str(manual_value))
        resolved_value = normalized.get("normalized_value")
        if resolved_value in (None, ""):
            raise HTTPException(status_code=400, detail="The corrected value could not be validated.")

    reason = str(resolution.get("reason", "")).strip()[:1000] or None
    try:
        from database.connection import SessionLocal
        from database.models import FieldResolution

        db = SessionLocal()
        try:
            row = db.query(FieldResolution).filter(
                FieldResolution.shipment_id == shipment_id,
                FieldResolution.canonical_field_id == canonical_field_id,
            ).first()
            if row is None:
                row = FieldResolution(
                    shipment_id=shipment_id,
                    canonical_field_id=canonical_field_id,
                    entity_type=field["entity_type"],
                )
                db.add(row)
            row.resolved_value = resolved_value
            row.source_assertion_id = source_assertion_id
            row.reason = reason
            row.resolved_by = "reviewer"
            db.commit()
        finally:
            db.close()
    except Exception as exc:
        logger.exception("Could not save field resolution for %s", shipment_id)
        raise HTTPException(status_code=503, detail="The resolution could not be saved.") from exc

    resolved_fields = _resolve_shipment_fields(shipment_id, documents)
    saved = next(item for item in resolved_fields if item["canonical_field_id"] == canonical_field_id)
    return {"status": "resolved", "field": saved}


@router.post("/shipments/{shipment_id}/declaration-metadata")
async def save_declaration_metadata(shipment_id: str, payload: dict):
    """Save verified Customs/profile fields supplied by the declarant or reviewer."""
    documents = _get_documents_for_shipment(shipment_id)
    if not documents:
        raise HTTPException(status_code=404, detail="No processed documents were found for this dossier.")

    from reasoning.cusdec_readiness import PROFILE_REQUIREMENTS, build_cusdec_readiness

    values = payload.get("values")
    if not isinstance(values, dict):
        raise HTTPException(status_code=400, detail="values must be an object of declaration fields.")

    invalid = set(values) - set(PROFILE_REQUIREMENTS)
    if invalid:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported declaration field(s): {', '.join(sorted(invalid))}.",
        )

    cleaned = {
        key: str(value).strip()
        for key, value in values.items()
        if value is not None and str(value).strip()
    }
    if not cleaned:
        raise HTTPException(status_code=400, detail="Enter at least one declaration value to save.")
    if any(len(value) > 200 for value in cleaned.values()):
        raise HTTPException(status_code=400, detail="Declaration values must be 200 characters or fewer.")

    try:
        from database.connection import SessionLocal
        from database.models import DeclarationMetadata

        db = SessionLocal()
        try:
            for field_name, value in cleaned.items():
                row = db.query(DeclarationMetadata).filter(
                    DeclarationMetadata.shipment_id == shipment_id,
                    DeclarationMetadata.field_name == field_name,
                ).first()
                if row is None:
                    row = DeclarationMetadata(shipment_id=shipment_id, field_name=field_name)
                    db.add(row)
                row.value = value
                row.updated_by = "reviewer"
            db.commit()
        finally:
            db.close()
    except Exception as exc:
        logger.exception("Could not save declaration metadata for %s", shipment_id)
        raise HTTPException(status_code=503, detail="The declaration details could not be saved.") from exc

    fields = _resolve_shipment_fields(shipment_id, documents)
    metadata = _get_declaration_metadata(shipment_id)
    return {
        "status": "saved",
        "profile": metadata,
        "readiness": build_cusdec_readiness(documents, fields, metadata),
    }


@router.get("/shipments/{shipment_id}/discrepancies")
async def get_discrepancies(shipment_id: str):
    from reasoning.rule_evaluator import RuleEvaluator
    from reasoning.xai_compiler import XAICompiler
    from reasoning.audit_trail import build_demo_trail

    kb, documents = _get_graph_for_shipment(shipment_id)
    graph = kb.get_graph()

    build_demo_trail(shipment_id, documents)

    evaluator = RuleEvaluator(graph)
    failures = evaluator.evaluate()

    compiler = XAICompiler(graph)
    discrepancies = []
    for f in failures:
        xai_block = compiler.compile(f)
        discrepancies.append({
            "discrepancy_id": f"{f.rule_id}_{f.node_a_id}_{f.node_b_id}",
            "field": f.entity_type,
            "field_label": f.entity_type.replace("_", " ").title(),
            "canonical_field_id": f.canonical_field_id,
            "rule_id": f.rule_id,
            "severity": "high" if "NUMERIC" in f.rule_id else "medium",
            "severity_score": round(1.0 - xai_block.layer3.overall_confidence, 4),
            "status": "open",
            "value_a": str(f.value_a),
            "value_b": str(f.value_b),
            "delta": f.delta,
            "sources": [
                {
                    "document_id": graph.nodes[node_id].get("source_doc", ""),
                    "document_label": graph.nodes[node_id].get("source_doc_label", "Unknown document"),
                    "document_type": graph.nodes[node_id].get("source_doc_type", "unknown"),
                    "raw_value": graph.nodes[node_id].get("raw_value", ""),
                    "normalized_value": graph.nodes[node_id].get("value", ""),
                    "page": graph.nodes[node_id].get("page", 1),
                    "bbox": graph.nodes[node_id].get("bbox", []),
                    "extraction_confidence": graph.nodes[node_id].get("extraction_confidence", 0.0),
                }
                for node_id in (f.node_a_id, f.node_b_id)
            ],
            "xai_block": dataclasses.asdict(xai_block),
        })

    return {
        "shipment_id": shipment_id,
        "total_discrepancies": len(discrepancies),
        "discrepancies": discrepancies,
    }


@router.get("/shipments/{shipment_id}/audit-trail")
async def get_audit_trail(shipment_id: str):
    from reasoning.audit_trail import get_trail, build_demo_trail

    trail = get_trail(shipment_id)
    if trail is None:
        documents = _get_documents_for_shipment(shipment_id)
        build_demo_trail(shipment_id, documents)
        trail = get_trail(shipment_id)

    return {
        "shipment_id": shipment_id,
        "total_events": len(trail) if trail else 0,
        "entries": trail or [],
    }


@router.get("/shipments/{shipment_id}/asycuda-export")
async def export_asycuda(shipment_id: str):
    """Export only a declaration that passed the CUSDEC readiness gate.

    A valid HTTP response must never contain fabricated declaration data.  The
    official ASYCUDA serializer is deliberately not enabled until its message
    schema is configured and validated.
    """
    documents = _get_documents_for_shipment(shipment_id)
    if not documents:
        raise HTTPException(status_code=404, detail="No processed documents were found for this dossier.")

    from reasoning.cusdec_readiness import build_cusdec_readiness

    readiness = build_cusdec_readiness(
        documents,
        _resolve_shipment_fields(shipment_id, documents),
        _get_declaration_metadata(shipment_id),
    )
    if not readiness["export_allowed"]:
        raise HTTPException(
            status_code=422,
            detail={
                "message": "CUSDEC export is blocked until all readiness checks pass.",
                "readiness": readiness,
            },
        )

    # This path is unreachable until an approved schema validator is added to
    # the readiness gate. Keep an explicit response instead of silently
    # emitting the former demo-shaped XML.
    raise HTTPException(
        status_code=501,
        detail="An official ASYCUDA XML serializer has not been configured for this environment.",
    )


@router.get("/shipments/{shipment_id}/cusdec-readiness")
async def get_cusdec_readiness(shipment_id: str):
    """Return field-level blockers before the user attempts an export."""
    documents = _get_documents_for_shipment(shipment_id)
    if not documents:
        raise HTTPException(status_code=404, detail="No processed documents were found for this dossier.")

    from reasoning.cusdec_readiness import build_cusdec_readiness

    fields = _resolve_shipment_fields(shipment_id, documents)
    return {
        "shipment_id": shipment_id,
        **build_cusdec_readiness(documents, fields, _get_declaration_metadata(shipment_id)),
    }


# ══════════════════════════════════════════════════════════════════
# GET /api/dossiers — overview dashboard: list all dossiers
# ══════════════════════════════════════════════════════════════════

@router.get("/dossiers")
async def list_dossiers():
    """List all dossiers with per-document status for the overview dashboard."""
    try:
        from database.connection import SessionLocal
        from database.models import Dossier, DossierDocument

        db = SessionLocal()
        try:
            dossiers = (
                db.query(Dossier)
                .order_by(Dossier.created_at.desc())
                .limit(50)
                .all()
            )
            result = []
            for d in dossiers:
                docs = (
                    db.query(DossierDocument)
                    .filter(DossierDocument.dossier_id == d.id)
                    .order_by(DossierDocument.created_at)
                    .all()
                )
                result.append({
                    "dossier_id": str(d.id),
                    "status": d.status,
                    "created_at": d.created_at.isoformat() if d.created_at else None,
                    "document_count": len(docs),
                    "documents": [
                        {
                            "document_id": str(doc.id),
                            "original_name": doc.original_name,
                            "document_type": doc.document_type,
                            "status": doc.status,
                        }
                        for doc in docs
                    ],
                })
            return {"dossiers": result}
        finally:
            db.close()
    except Exception as exc:
        logger.warning("list_dossiers error: %s", exc)
        return {"dossiers": []}


# ══════════════════════════════════════════════════════════════════
# GET /api/rules/active — return dynamic rules for Pre-Check Matrix
# ══════════════════════════════════════════════════════════════════

from pydantic import BaseModel

class RuleMetadata(BaseModel):
    id: str
    label: str
    description: str
    status: str = "Ready"

ACTIVE_RULES = [
    RuleMetadata(
        id="RULE_HS_CODE",
        label="HS Code Concordance",
        description="Cotton apparel harmonized between Commercial Invoice and AWB cargo description."
    ),
    RuleMetadata(
        id="RULE_INCOTERMS",
        label="Incoterms & Apportionment",
        description="Ocean freight breakdown mapped without duty base variance (CIF Colombo)."
    ),
    RuleMetadata(
        id="RULE_TIN_REGISTRY",
        label="TIN/EORI Registry",
        description="Declarant TIN validated with Inland Revenue Department."
    ),
    RuleMetadata(
        id="RULE_WEIGHT_TOL",
        label="Weight Tolerance Check",
        description="Cross-document weight comparison queued for Rule Evaluator."
    ),
]

@router.get("/rules/active", response_model=List[dict])
async def get_active_rules():
    """Returns the list of active checks for the Pre-Check Matrix Engine."""
    return [rule.dict() for rule in ACTIVE_RULES]

@router.post('/shipments/{shipment_id}/discrepancies/{discrepancy_id}/resolve')
async def resolve_discrepancy(shipment_id: str, discrepancy_id: str, decision: dict):
    del shipment_id, discrepancy_id, decision
    raise HTTPException(
        status_code=410,
        detail="Use the field-resolution workflow to select source evidence or enter a corrected value.",
    )

