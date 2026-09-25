# backend/api/routes.py
from fastapi import APIRouter, UploadFile, File
from fastapi.responses import Response
from typing import List
import uuid, os, dataclasses

router = APIRouter(prefix="/api")
UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

# ── Shared graph builder helper ────────────────────────────────────────
# Used by /graph, /discrepancies, /asycuda-export, /audit-trail to build
# a consistent knowledge graph from mock pipeline output.

def _build_demo_graph(shipment_id: str):
    """
    Runs MockPipeline on the demo PDFs and builds the knowledge graph.
    Returns (kb, documents) where kb is a KnowledgeBuilder and documents is
    the list of pipeline result dicts.
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

    # Build cross-document MUST_MATCH edges for shared fields
    # GROSS_WEIGHT: invoice vs awb (intentional discrepancy: 450.0 vs 448.5)
    inv_gw  = next((e for e in documents[0]["entities"] if e["entity_type"] == "GROSS_WEIGHT"), None)
    awb_gw  = next((e for e in documents[2]["entities"] if e["entity_type"] == "GROSS_WEIGHT"), None)
    pl_gw   = next((e for e in documents[1]["entities"] if e["entity_type"] == "GROSS_WEIGHT"), None)

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

    # CONSIGNEE_NAME: invoice vs awb ("ABC Textiles Ltd" vs "ABC Textiles Ltd.")
    inv_cn  = next((e for e in documents[0]["entities"] if e["entity_type"] == "CONSIGNEE_NAME"), None)
    awb_cn  = next((e for e in documents[2]["entities"] if e["entity_type"] == "CONSIGNEE_NAME"), None)

    if inv_cn:
        kb.add_entity_node("n_inv_cn", to_entity(inv_cn), "doc_001")
    if awb_cn:
        kb.add_entity_node("n_awb_cn", to_entity(awb_cn), "doc_003")
    if inv_cn and awb_cn:
        kb.add_relationship("n_inv_cn", "n_awb_cn", "MUST_MATCH")

    return kb, documents


# ======================================================================
# POST /api/shipments/upload
# ======================================================================

@router.post("/shipments/upload")
async def upload_shipment(files: List[UploadFile] = File(...)):
    from fastapi import HTTPException

    for file in files:
        if not (file.filename or "").lower().endswith(".pdf"):
            raise HTTPException(
                status_code=400,
                detail=f"Only PDF files accepted. '{file.filename}' is not a PDF."
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


# ======================================================================
# GET /api/shipments/{shipment_id}/status
# ======================================================================

@router.get("/shipments/{shipment_id}/status")
async def get_shipment_status(shipment_id: str):
    from fastapi import HTTPException

    # Demo fixture — always available even without real uploads
    DEMO_DOCS = [
        {"document_id": "doc_001", "filename": "commercial_invoice.pdf", "document_type": "commercial_invoice", "classification_confidence": 0.97},
        {"document_id": "doc_002", "filename": "packing_list.pdf",       "document_type": "packing_list",       "classification_confidence": 0.96},
        {"document_id": "doc_003", "filename": "awb.pdf",                "document_type": "awb",                "classification_confidence": 0.95},
    ]

    # For demo/test shipment IDs return the fixture immediately
    if shipment_id in ("demo-shipment", "demo"):
        return {
            "shipment_id": shipment_id,
            "status": "completed",
            "progress": 100,
            "documents": DEMO_DOCS,
            "processing_time_ms": 3150,
        }

    # For real uploaded shipments — inspect the uploads directory
    shipment_dir = os.path.join(UPLOAD_DIR, shipment_id)
    if not os.path.isdir(shipment_dir):
        raise HTTPException(
            status_code=404,
            detail=f"Shipment '{shipment_id}' not found.",
        )

    # Build a document list from whatever PDFs are on disk
    documents = []
    for fname in sorted(os.listdir(shipment_dir)):
        if fname.lower().endswith(".pdf"):
            # Strip the leading UUID prefix added during upload (uuid4_filename.pdf)
            parts = fname.split("_", 1)
            display_name = parts[1] if len(parts) == 2 else fname
            documents.append({
                "document_id": parts[0] if len(parts) == 2 else fname,
                "filename": display_name,
                "document_type": "unknown",
                "classification_confidence": None,
            })

    return {
        "shipment_id": shipment_id,
        "status": "completed",
        "progress": 100,
        "documents": documents,
        "processing_time_ms": None,
    }


# ======================================================================
# GET /api/shipments/{shipment_id}/extraction
# ======================================================================

@router.get("/shipments/{shipment_id}/extraction")
async def get_extraction(shipment_id: str):
    from ai_pipeline.mock_pipeline import MockPipeline
    mp = MockPipeline()
    demo_docs = [
        ("demo/commercial_invoice.pdf", "doc_001"),
        ("demo/packing_list.pdf",       "doc_002"),
        ("demo/awb.pdf",                "doc_003"),
    ]
    documents = [mp.process_document(path, doc_id) for path, doc_id in demo_docs]
    # Inject classification_confidence into each entity dict (already present from mock)
    return {"shipment_id": shipment_id, "documents": documents}


# ======================================================================
# GET /api/shipments/{shipment_id}/graph
# ======================================================================

@router.get("/shipments/{shipment_id}/graph")
async def get_knowledge_graph(shipment_id: str):
    kb, _ = _build_demo_graph(shipment_id)
    return kb.to_vis_json()


# ======================================================================
# GET /api/shipments/{shipment_id}/discrepancies
# ======================================================================

@router.get("/shipments/{shipment_id}/discrepancies")
async def get_discrepancies(shipment_id: str):
    from reasoning.rule_evaluator import RuleEvaluator
    from reasoning.xai_compiler import XAICompiler
    from reasoning.audit_trail import build_demo_trail

    kb, documents = _build_demo_graph(shipment_id)
    graph = kb.get_graph()

    # Seed the audit trail for this shipment
    build_demo_trail(shipment_id, documents)

    # Neuro-Symbolic Evaluation
    evaluator = RuleEvaluator(graph)
    failures = evaluator.evaluate()

    # Compile 4-Layer XAI Payload
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


# ======================================================================
# GET /api/shipments/{shipment_id}/audit-trail
# ======================================================================

@router.get("/shipments/{shipment_id}/audit-trail")
async def get_audit_trail(shipment_id: str):
    from reasoning.audit_trail import get_trail, build_demo_trail

    # Seed demo trail if not yet built (e.g. if discrepancies endpoint not called first)
    trail = get_trail(shipment_id)
    if trail is None:
        build_demo_trail(shipment_id, [
            {"document_id": "doc_001", "document_type": "commercial_invoice", "classification_confidence": 0.97, "entities": []},
            {"document_id": "doc_002", "document_type": "packing_list",       "classification_confidence": 0.96, "entities": []},
            {"document_id": "doc_003", "document_type": "awb",                "classification_confidence": 0.95, "entities": []},
        ])
        trail = get_trail(shipment_id)

    return {
        "shipment_id": shipment_id,
        "total_events": len(trail),
        "entries": trail,
    }


# ======================================================================
# GET /api/shipments/{shipment_id}/asycuda-export
# ======================================================================

@router.get("/shipments/{shipment_id}/asycuda-export")
async def export_asycuda(shipment_id: str):
    from reasoning.asycuda_export import generate_cusdec_xml

    try:
        kb, _ = _build_demo_graph(shipment_id)
        xml = generate_cusdec_xml(kb.get_graph(), shipment_id)
    except Exception as e:
        import logging
        logging.getLogger(__name__).warning("ASYCUDA real export failed, falling back to demo: %s", e)
        from reasoning.asycuda_export import generate_demo_cusdec_xml
        xml = generate_demo_cusdec_xml(shipment_id)

    return Response(
        content=xml,
        media_type="application/xml",
        headers={"Content-Disposition": f"attachment; filename=CUSDEC_{shipment_id[:8]}.xml"},
    )
