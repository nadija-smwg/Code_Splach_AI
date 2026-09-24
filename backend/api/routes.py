# backend/api/routes.py
from fastapi import APIRouter, UploadFile, File
from fastapi.responses import Response
from typing import List
import uuid, os

router = APIRouter(prefix="/api")
UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

@router.post("/shipments/upload")
async def upload_shipment(files: List[UploadFile] = File(...)):
    from fastapi import HTTPException

    # Validate all files are PDFs before processing any
    for file in files:
        if not file.filename.lower().endswith(".pdf"):
            raise HTTPException(
                status_code=400,
                detail=f"Only PDF files accepted. '{file.filename}' is not a PDF."
            )

    shipment_id = str(uuid.uuid4())
    # Save to uploads/{shipment_id}/ subfolder (per-shipment)
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
    return {
        "shipment_id": shipment_id, "status": "completed", "progress": 100,
        "documents": [
            {"document_id": "doc_001", "filename": "commercial_invoice.pdf", "document_type": "commercial_invoice", "classification_confidence": 0.97},
            {"document_id": "doc_002", "filename": "packing_list.pdf", "document_type": "packing_list", "classification_confidence": 0.96},
            {"document_id": "doc_003", "filename": "awb.pdf", "document_type": "awb", "classification_confidence": 0.95}
        ],
        "processing_time_ms": 8500
    }

@router.get("/shipments/{shipment_id}/extraction")
async def get_extraction(shipment_id: str):
    return {
        "shipment_id": shipment_id,
        "documents": [
            {"document_id": "doc_001", "document_type": "commercial_invoice", "classification_confidence": 0.97,
             "entities": [
                {"entity_type": "INVOICE_NUMBER", "value": "INV-2024-1023", "normalized_value": "INV-2024-1023", "unit": None, "page": 1, "bbox": [45,120,280,145], "extraction_confidence": 0.96, "classification_confidence": 0.97},
                {"entity_type": "CONSIGNEE_NAME", "value": "ABC Textiles Ltd", "normalized_value": "ABC Textiles Ltd", "unit": None, "page": 1, "bbox": [50,200,320,225], "extraction_confidence": 0.91, "classification_confidence": 0.97},
                {"entity_type": "GROSS_WEIGHT", "value": "450.00 KG", "normalized_value": 450.0, "unit": "kg", "page": 1, "bbox": [400,350,550,375], "extraction_confidence": 0.94, "classification_confidence": 0.97},
                {"entity_type": "NET_WEIGHT", "value": "420.00 KG", "normalized_value": 420.0, "unit": "kg", "page": 1, "bbox": [400,380,550,405], "extraction_confidence": 0.93, "classification_confidence": 0.97},
                {"entity_type": "PACKAGE_COUNT", "value": "25 Cartons", "normalized_value": 25, "unit": "cartons", "page": 1, "bbox": [400,410,550,435], "extraction_confidence": 0.95, "classification_confidence": 0.97},
                {"entity_type": "INCOTERM", "value": "FOB Colombo", "normalized_value": "FOB", "unit": None, "page": 1, "bbox": [50,300,200,325], "extraction_confidence": 0.92, "classification_confidence": 0.97},
                {"entity_type": "TOTAL_AMOUNT", "value": "45,230.00 USD", "normalized_value": 45230.0, "unit": None, "page": 1, "bbox": [400,500,580,530], "extraction_confidence": 0.94, "classification_confidence": 0.97}
             ]},
            {"document_id": "doc_002", "document_type": "packing_list", "classification_confidence": 0.96,
             "entities": [
                {"entity_type": "GROSS_WEIGHT", "value": "450.00 KG", "normalized_value": 450.0, "unit": "kg", "page": 1, "bbox": [350,400,500,425], "extraction_confidence": 0.95, "classification_confidence": 0.96},
                {"entity_type": "NET_WEIGHT", "value": "420.00 KG", "normalized_value": 420.0, "unit": "kg", "page": 1, "bbox": [350,430,500,455], "extraction_confidence": 0.93, "classification_confidence": 0.96},
                {"entity_type": "TARE_WEIGHT", "value": "25.00 KG", "normalized_value": 25.0, "unit": "kg", "page": 1, "bbox": [350,460,500,485], "extraction_confidence": 0.90, "classification_confidence": 0.96},
                {"entity_type": "PACKAGE_COUNT", "value": "25 Cartons", "normalized_value": 25, "unit": "cartons", "page": 1, "bbox": [350,490,500,515], "extraction_confidence": 0.96, "classification_confidence": 0.96}
             ]},
            {"document_id": "doc_003", "document_type": "awb", "classification_confidence": 0.95,
             "entities": [
                {"entity_type": "AWB_NUMBER", "value": "631-12345678", "normalized_value": "631-12345678", "unit": None, "page": 1, "bbox": [200,50,400,80], "extraction_confidence": 0.97, "classification_confidence": 0.95},
                {"entity_type": "GROSS_WEIGHT", "value": "448.50 KG", "normalized_value": 448.5, "unit": "kg", "page": 1, "bbox": [350,300,500,325], "extraction_confidence": 0.93, "classification_confidence": 0.95},
                {"entity_type": "PACKAGE_COUNT", "value": "25 Pieces", "normalized_value": 25, "unit": "pieces", "page": 1, "bbox": [350,330,500,355], "extraction_confidence": 0.94, "classification_confidence": 0.95},
                {"entity_type": "CONSIGNEE_NAME", "value": "ABC Textiles Ltd.", "normalized_value": "ABC Textiles Ltd.", "unit": None, "page": 1, "bbox": [50,200,350,225], "extraction_confidence": 0.89, "classification_confidence": 0.95}
             ]}
        ]
    }

@router.get("/shipments/{shipment_id}/graph")
async def get_knowledge_graph(shipment_id: str):
    from backend.reasoning.knowledge_builder import KnowledgeBuilder
    from backend.xai_types import ExtractedEntity
    
    kb = KnowledgeBuilder()
    kb.add_document_node("doc_001", "commercial_invoice")
    kb.add_document_node("doc_003", "awb")
    
    ent1 = ExtractedEntity(entity_type="GROSS_WEIGHT", value="450.0", normalized_value=450.0, unit="KG", page=1, bbox=[400,350,550,375], extraction_confidence=0.94)
    ent2 = ExtractedEntity(entity_type="GROSS_WEIGHT", value="448.5", normalized_value=448.5, unit="KG", page=1, bbox=[350,300,500,325], extraction_confidence=0.93)
    ent3 = ExtractedEntity(entity_type="CONSIGNEE_NAME", value="ABC Textiles Ltd", normalized_value="ABC Textiles Ltd", unit=None, page=1, bbox=[50,200,320,225], extraction_confidence=0.91)
    ent4 = ExtractedEntity(entity_type="CONSIGNEE_NAME", value="ABC Textiles Ltd.", normalized_value="ABC Textiles Ltd.", unit=None, page=1, bbox=[50,200,350,225], extraction_confidence=0.89)
    
    kb.add_entity_node("node_w_inv", ent1, "doc_001")
    kb.add_entity_node("node_w_awb", ent2, "doc_003")
    kb.add_relationship("node_w_inv", "node_w_awb", "MUST_MATCH")
    kb.add_entity_node("node_c_inv", ent3, "doc_001")
    kb.add_entity_node("node_c_awb", ent4, "doc_003")
    kb.add_relationship("node_c_inv", "node_c_awb", "MUST_MATCH")
    
    return kb.to_vis_json()

@router.get("/shipments/{shipment_id}/discrepancies")
async def get_discrepancies(shipment_id: str):
    from backend.reasoning.knowledge_builder import KnowledgeBuilder
    from backend.reasoning.rule_evaluator import RuleEvaluator
    from backend.reasoning.xai_compiler import XAICompiler
    from backend.xai_types import ExtractedEntity
    import dataclasses
    
    # 1. Mock Extraction Pipeline
    kb = KnowledgeBuilder()
    kb.add_document_node("doc_001", "commercial_invoice")
    kb.add_document_node("doc_003", "awb")
    
    ent1 = ExtractedEntity(entity_type="GROSS_WEIGHT", value="450.0", normalized_value=450.0, unit="KG", page=1, bbox=[400,350,550,375], extraction_confidence=0.94)
    ent2 = ExtractedEntity(entity_type="GROSS_WEIGHT", value="448.5", normalized_value=448.5, unit="KG", page=1, bbox=[350,300,500,325], extraction_confidence=0.93)
    ent3 = ExtractedEntity(entity_type="CONSIGNEE_NAME", value="ABC Textiles Ltd", normalized_value="ABC Textiles Ltd", unit=None, page=1, bbox=[50,200,320,225], extraction_confidence=0.91)
    ent4 = ExtractedEntity(entity_type="CONSIGNEE_NAME", value="ABC Textiles Ltd.", normalized_value="ABC Textiles Ltd.", unit=None, page=1, bbox=[50,200,350,225], extraction_confidence=0.89)
    
    kb.add_entity_node("node_w_inv", ent1, "doc_001")
    kb.add_entity_node("node_w_awb", ent2, "doc_003")
    kb.add_relationship("node_w_inv", "node_w_awb", "MUST_MATCH")
    
    kb.add_entity_node("node_c_inv", ent3, "doc_001")
    kb.add_entity_node("node_c_awb", ent4, "doc_003")
    kb.add_relationship("node_c_inv", "node_c_awb", "MUST_MATCH")
    
    # 2. Neuro-Symbolic Evaluation
    evaluator = RuleEvaluator(kb.get_graph())
    failures = evaluator.evaluate()
    
    # 3. Compile 4-Layer XAI Payload
    compiler = XAICompiler(kb.get_graph())
    
    discrepancies = []
    for f in failures:
        xai_block = compiler.compile(f)
        discrepancies.append({
            "discrepancy_id": f.rule_id,
            "field": f.rule_id,
            "severity": "high",
            "status": "open",
            "xai_block": dataclasses.asdict(xai_block)
        })
        
    return {
        "shipment_id": shipment_id,
        "total_discrepancies": len(discrepancies),
        "discrepancies": discrepancies
    }

@router.get("/shipments/{shipment_id}/audit-trail")
async def get_audit_trail(shipment_id: str):
    return {
        "shipment_id": shipment_id,
        "entries": [
            {"timestamp": "2024-09-14T10:30:01", "module": "classifier", "action": "Classified doc_001 as commercial_invoice", "confidence": 0.97, "outcome": "accepted"},
            {"timestamp": "2024-09-14T10:30:02", "module": "classifier", "action": "Classified doc_002 as packing_list", "confidence": 0.96, "outcome": "accepted"},
            {"timestamp": "2024-09-14T10:30:03", "module": "classifier", "action": "Classified doc_003 as awb", "confidence": 0.95, "outcome": "accepted"},
            {"timestamp": "2024-09-14T10:30:05", "module": "extractor", "action": "Extracted GROSS_WEIGHT=450.00kg from doc_001", "confidence": 0.94, "outcome": "accepted"},
            {"timestamp": "2024-09-14T10:30:06", "module": "extractor", "action": "Extracted GROSS_WEIGHT=450.00kg from doc_002", "confidence": 0.95, "outcome": "accepted"},
            {"timestamp": "2024-09-14T10:30:07", "module": "extractor", "action": "Extracted GROSS_WEIGHT=448.50kg from doc_003", "confidence": 0.93, "outcome": "accepted"},
            {"timestamp": "2024-09-14T10:30:10", "module": "reconciler", "action": "Compared GROSS_WEIGHT across 3 documents", "confidence": 0.72, "outcome": "conflict_detected"},
            {"timestamp": "2024-09-14T10:30:11", "module": "reconciler", "action": "PL internal check: net+tare=445 != gross=450", "confidence": None, "outcome": "inconsistency_flagged"},
            {"timestamp": "2024-09-14T10:30:12", "module": "counterfactual", "action": "Generated 3 resolution options", "confidence": None, "outcome": "generated"}
        ]
    }

@router.get("/shipments/{shipment_id}/asycuda-export")
async def export_asycuda(shipment_id: str):
    xml = '<?xml version="1.0" encoding="UTF-8"?><CUSDEC><DeclarationHeader><DeclarationType>IM</DeclarationType><DeclarationOffice>LKCMB01</DeclarationOffice></DeclarationHeader><ConsigneeInfo><Name>ABC Textiles Ltd</Name><Address>42 Galle Road, Colombo 03</Address></ConsigneeInfo><TransportInfo><AWBNumber>631-12345678</AWBNumber><GrossWeight unit="KG">450.00</GrossWeight><PackageCount>25</PackageCount></TransportInfo></CUSDEC>'
    return Response(content=xml, media_type="application/xml", headers={"Content-Disposition": f"attachment; filename=CUSDEC_{shipment_id}.xml"})
