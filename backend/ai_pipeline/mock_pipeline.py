# backend/ai_pipeline/mock_pipeline.py
"""
Mock pipeline for ClearanceX.
Returns realistic fake ExtractionResult JSON so Aloka and Kaveen
can build their modules without waiting for the real AI pipeline.
"""

from typing import List, Dict, Any


MOCK_EXTRACTION_RESULT: Dict[str, Any] = {
    "document_id": "doc_001",
    "document_type": "commercial_invoice",
    "classification_confidence": 0.97,
    "entities": [
        {
            "entity_type": "GROSS_WEIGHT",
            "value": "450.00",
            "normalized_value": 450.0,
            "unit": "kg",
            "page": 2,
            "bbox": [120, 240, 410, 290],
            "extraction_confidence": 0.94
        },
        {
            "entity_type": "NET_WEIGHT",
            "value": "420.00",
            "normalized_value": 420.0,
            "unit": "kg",
            "page": 2,
            "bbox": [120, 300, 410, 350],
            "extraction_confidence": 0.93
        },
        {
            "entity_type": "PACKAGE_COUNT",
            "value": "24",
            "normalized_value": 24,
            "unit": "cartons",
            "page": 1,
            "bbox": [200, 150, 380, 190],
            "extraction_confidence": 0.98
        },
        {
            "entity_type": "INVOICE_NUMBER",
            "value": "INV-2026-00451",
            "normalized_value": "INV-2026-00451",
            "unit": None,
            "page": 1,
            "bbox": [300, 80, 550, 110],
            "extraction_confidence": 0.99
        },
        {
            "entity_type": "INCOTERM",
            "value": "FOB",
            "normalized_value": "FOB",
            "unit": None,
            "page": 1,
            "bbox": [100, 400, 200, 430],
            "extraction_confidence": 0.96
        },
        {
            "entity_type": "CONSIGNEE",
            "value": "MAS Holdings (Pvt) Ltd, Colombo 03, Sri Lanka",
            "normalized_value": "MAS Holdings (Pvt) Ltd",
            "unit": None,
            "page": 1,
            "bbox": [100, 200, 500, 260],
            "extraction_confidence": 0.91
        }
    ],
    "raw_ocr": [
        {
            "text": "Gross Weight: 450.00 KG",
            "page": 2,
            "bbox": [100, 230, 430, 300],
            "ocr_confidence": 0.98
        },
        {
            "text": "Net Weight: 420.00 KG",
            "page": 2,
            "bbox": [100, 290, 430, 360],
            "ocr_confidence": 0.97
        },
        {
            "text": "Total Cartons: 24",
            "page": 1,
            "bbox": [190, 140, 390, 200],
            "ocr_confidence": 0.99
        },
        {
            "text": "Invoice No: INV-2026-00451",
            "page": 1,
            "bbox": [290, 70, 560, 120],
            "ocr_confidence": 0.99
        }
    ]
}

# A second mock document (e.g. Packing List) with a deliberate weight discrepancy
MOCK_PACKING_LIST_RESULT: Dict[str, Any] = {
    "document_id": "doc_002",
    "document_type": "packing_list",
    "classification_confidence": 0.95,
    "entities": [
        {
            "entity_type": "GROSS_WEIGHT",
            "value": "455.00",          # ← Deliberate mismatch vs invoice (450.00)
            "normalized_value": 455.0,
            "unit": "kg",
            "page": 1,
            "bbox": [150, 310, 420, 360],
            "extraction_confidence": 0.92
        },
        {
            "entity_type": "PACKAGE_COUNT",
            "value": "24",
            "normalized_value": 24,
            "unit": "cartons",
            "page": 1,
            "bbox": [150, 370, 380, 410],
            "extraction_confidence": 0.97
        }
    ],
    "raw_ocr": [
        {
            "text": "Gross Weight: 455.00 KG",
            "page": 1,
            "bbox": [140, 300, 430, 370],
            "ocr_confidence": 0.96
        }
    ]
}


def run_mock_pipeline(file_path: str) -> Dict[str, Any]:
    """
    Drop-in mock for the real pipeline.
    Returns a fake ExtractionResult regardless of the input file.
    Replace this function with the real OCR pipeline when ready.
    """
    if "packing" in file_path.lower():
        return MOCK_PACKING_LIST_RESULT
    return MOCK_EXTRACTION_RESULT


def run_mock_pipeline_batch(file_paths: List[str]) -> List[Dict[str, Any]]:
    """
    Batch version — returns one mock result per file.
    """
    return [run_mock_pipeline(fp) for fp in file_paths]
