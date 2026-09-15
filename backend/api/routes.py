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
    return {
        "nodes": [
            {"id": "doc_001", "label": "Commercial Invoice", "type": "document", "color": "#4A90D9"},
            {"id": "doc_002", "label": "Packing List", "type": "document", "color": "#50C878"},
            {"id": "doc_003", "label": "AWB", "type": "document", "color": "#FFB347"},
            {"id": "GROSS_WEIGHT", "label": "Gross Weight", "type": "entity", "status": "conflict", "color": "#FF6B6B"},
            {"id": "NET_WEIGHT", "label": "Net Weight", "type": "entity", "status": "match", "color": "#50C878"},
            {"id": "PACKAGE_COUNT", "label": "Package Count", "type": "entity", "status": "match", "color": "#50C878"},
            {"id": "CONSIGNEE_NAME", "label": "Consignee", "type": "entity", "status": "warning", "color": "#FFD700"},
            {"id": "INCOTERM", "label": "Incoterm", "type": "entity", "status": "match", "color": "#50C878"}
        ],
        "edges": [
            {"from": "doc_001", "to": "GROSS_WEIGHT", "label": "450.00 kg", "confidence": 0.94},
            {"from": "doc_002", "to": "GROSS_WEIGHT", "label": "450.00 kg", "confidence": 0.95},
            {"from": "doc_003", "to": "GROSS_WEIGHT", "label": "448.50 kg", "confidence": 0.93},
            {"from": "doc_001", "to": "NET_WEIGHT", "label": "420.00 kg", "confidence": 0.93},
            {"from": "doc_002", "to": "NET_WEIGHT", "label": "420.00 kg", "confidence": 0.93},
            {"from": "doc_001", "to": "PACKAGE_COUNT", "label": "25 cartons", "confidence": 0.95},
            {"from": "doc_002", "to": "PACKAGE_COUNT", "label": "25 cartons", "confidence": 0.96},
            {"from": "doc_003", "to": "PACKAGE_COUNT", "label": "25 pieces", "confidence": 0.94},
            {"from": "doc_001", "to": "CONSIGNEE_NAME", "label": "ABC Textiles Ltd", "confidence": 0.91},
            {"from": "doc_003", "to": "CONSIGNEE_NAME", "label": "ABC Textiles Ltd.", "confidence": 0.89},
            {"from": "doc_001", "to": "INCOTERM", "label": "FOB", "confidence": 0.92}
        ]
    }

@router.get("/shipments/{shipment_id}/discrepancies")
async def get_discrepancies(shipment_id: str):
    return {
        "shipment_id": shipment_id, "total_discrepancies": 2,
        "discrepancies": [
            {"discrepancy_id": "disc_001", "field": "GROSS_WEIGHT", "severity": "high", "severity_score": 0.87, "status": "open",
             "sources": [
                {"document_id": "doc_001", "document_type": "commercial_invoice", "value": "450.00 kg", "page": 1, "bbox": [400,350,550,375]},
                {"document_id": "doc_002", "document_type": "packing_list", "value": "450.00 kg", "page": 1, "bbox": [350,400,500,425]},
                {"document_id": "doc_003", "document_type": "awb", "value": "448.50 kg", "page": 1, "bbox": [350,300,500,325]}
             ],
             "reasoning_chain": {"steps": ["Invoice: 450.00 kg","Packing List: 450.00 kg","AWB: 448.50 kg","Invoice vs PL: MATCH","Invoice vs AWB: 0.33% variance","PL internal: net+tare=445 != gross=450 INCONSISTENCY"],"conclusion": "AWB deviates. PL has internal inconsistency."},
             "confidence": {"extraction": 0.94, "classification": 0.96, "matching": 0.72, "overall": 0.72},
             "counterfactual": {"options": ["If AWB were 450.00 kg, discrepancy resolves.","If PL tare were 30 kg, PL internal resolves."],"recommendation": "Verify at factory scale. Fix PL inconsistency first."}},
            {"discrepancy_id": "disc_002", "field": "CONSIGNEE_NAME", "severity": "low", "severity_score": 0.35, "status": "open",
             "sources": [
                {"document_id": "doc_001", "document_type": "commercial_invoice", "value": "ABC Textiles Ltd", "page": 1, "bbox": [50,200,320,225]},
                {"document_id": "doc_003", "document_type": "awb", "value": "ABC Textiles Ltd.", "page": 1, "bbox": [50,200,350,225]}
             ],
             "reasoning_chain": {"steps": ["Invoice: 'ABC Textiles Ltd'","AWB: 'ABC Textiles Ltd.'","Fuzzy match: 97%","Difference: trailing period"],"conclusion": "Minor typo. Same entity."},
             "confidence": {"extraction": 0.90, "classification": 0.96, "matching": 0.97, "overall": 0.90},
             "counterfactual": {"options": ["Remove trailing period from AWB consignee."],"recommendation": "Non-issue. Use Invoice version for CUSDEC."}}
        ]
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
