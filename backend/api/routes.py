# backend/api/routes.py
#
# Smart routing: DB-first with demo fallback
# - Real dossier_id (UUID in PostgreSQL)  → query DB extraction results
# - Demo IDs ("demo-shipment", "demo")    → run MockPipeline on demo PDFs
# - Unknown IDs / DB unavailable          → fall back to demo

from fastapi import APIRouter, UploadFile, File, HTTPException
from fastapi.responses import Response
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
    return [mp.process_document(path, doc_id) for path, doc_id in demo_docs]


def _get_documents_for_shipment(shipment_id: str) -> list:
    """
    Resolve pipeline result dicts for a shipment.
    Always uses real DB data. Never falls back to demo.
    """
    real = _fetch_dossier_documents(shipment_id)
    return real if real is not None else []


# ══════════════════════════════════════════════════════════════════
# HELPERS — Knowledge Graph Building
# ══════════════════════════════════════════════════════════════════

def _build_graph_from_documents(shipment_id: str, documents: list):
    """
    Generic graph builder: works with any list of pipeline result dicts.
    Adds all entities and creates MUST_MATCH edges across documents
    for the same entity_type.

    Returns (KnowledgeBuilder, documents).
    """
    from reasoning.knowledge_builder import KnowledgeBuilder
    from xai_types import ExtractedEntity

    kb = KnowledgeBuilder()

    for doc in documents:
        kb.add_document_node(doc["document_id"], doc.get("document_type", "unknown"))

    def _to_entity(e: dict) -> ExtractedEntity:
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

    # Collect entity nodes grouped by entity_type for cross-doc matching
    by_type: dict[str, list[tuple[str, str]]] = {}

    for doc in documents:
        doc_id = doc["document_id"]
        for idx, entity in enumerate(doc.get("entities", [])):
            etype = entity.get("entity_type")
            if not etype:
                continue
            node_id = f"n_{doc_id}_{etype}_{idx}"
            kb.add_entity_node(node_id, _to_entity(entity), doc_id)
            by_type.setdefault(etype, []).append((node_id, doc_id))

    # MUST_MATCH edges: connect first occurrence per document across documents
    for _etype, entries in by_type.items():
        seen: dict[str, str] = {}
        for node_id, doc_id in entries:
            if doc_id not in seen:
                seen[doc_id] = node_id
        unique_nodes = list(seen.values())
        if len(unique_nodes) > 1:
            for j in range(1, len(unique_nodes)):
                kb.add_relationship(unique_nodes[0], unique_nodes[j], "MUST_MATCH")

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
    real = _fetch_dossier_documents(shipment_id)
    return _build_graph_from_documents(shipment_id, real if real is not None else [])


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
            "field": f"{f.node_a_id}|{f.node_b_id}",
            "rule_id": f.rule_id,
            "severity": "high" if "NUMERIC" in f.rule_id else "medium",
            "severity_score": round(1.0 - xai_block.layer3.overall_confidence, 4),
            "status": "open",
            "value_a": str(f.value_a),
            "value_b": str(f.value_b),
            "delta": f.delta,
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
    from reasoning.asycuda_export import generate_cusdec_xml

    try:
        kb, _ = _get_graph_for_shipment(shipment_id)
        xml = generate_cusdec_xml(kb.get_graph(), shipment_id)
    except Exception as e:
        logger.warning("ASYCUDA export failed, falling back to demo: %s", e)
        from reasoning.asycuda_export import generate_demo_cusdec_xml
        xml = generate_demo_cusdec_xml(shipment_id)

    return Response(
        content=xml,
        media_type="application/xml",
        headers={"Content-Disposition": f"attachment; filename=CUSDEC_{shipment_id[:8]}.xml"},
    )


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
    return {'status': 'resolved'}

