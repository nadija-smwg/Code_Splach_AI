# backend/ai_pipeline/mock_pipeline.py
"""
MOCK pipeline — returns realistic fake ExtractionResult data.

Use this until the real pipeline (pipeline.py) is ready.
Aloka and Kaveen: call MockPipeline().process_document(pdf_path, document_id)

The schema returned by MockPipeline.process_document() is IDENTICAL
to the real AIPipeline — same keys, same types.

Switch is a one-liner:
    # Before
    from ai_pipeline.mock_pipeline import MockPipeline
    pipeline = MockPipeline()

    # After
    from ai_pipeline.pipeline import get_pipeline
    pipeline = get_pipeline()
"""

from copy import deepcopy
from pathlib import Path


# ---------------------------------------------------------------------------
# MOCK RESULTS — one template per document type.
# Intentional discrepancies are seeded (e.g. AWB GROSS_WEIGHT=448.5 vs
# invoice GROSS_WEIGHT=450.0) so the Rule Evaluator has real conflicts to
# detect during the demo.
# ---------------------------------------------------------------------------

MOCK_COMMERCIAL_INVOICE = {
    "document_id": "mock_001",
    "document_type": "commercial_invoice",
    "classification_confidence": 0.97,
    "classification_evidence": ["invoice", "unit price", "total amount"],
    "entities": [
        {
            "entity_type": "INVOICE_NUMBER",
            "value": "INV-2024-1023",
            "normalized_value": "INV20241023",
            "unit": None,
            "page": 1,
            "bbox": [45, 120, 280, 145],
            "extraction_confidence": 0.96,
            "classification_confidence": 0.97,
            "normalization_warning": False,
        },
        {
            "entity_type": "CONSIGNEE_NAME",
            "value": "ABC Textiles Ltd",
            "normalized_value": "ABC Textiles Ltd",
            "unit": None,
            "page": 1,
            "bbox": [50, 200, 320, 225],
            "extraction_confidence": 0.91,
            "classification_confidence": 0.97,
            "normalization_warning": False,
        },
        {
            "entity_type": "GROSS_WEIGHT",
            "value": "450.00 KG",
            "normalized_value": 450.0,
            "unit": "kg",
            "page": 1,
            "bbox": [400, 350, 550, 375],
            "extraction_confidence": 0.94,
            "classification_confidence": 0.97,
            "normalization_warning": False,
        },
        {
            "entity_type": "NET_WEIGHT",
            "value": "420.00 KG",
            "normalized_value": 420.0,
            "unit": "kg",
            "page": 1,
            "bbox": [400, 380, 550, 405],
            "extraction_confidence": 0.93,
            "classification_confidence": 0.97,
            "normalization_warning": False,
        },
        {
            "entity_type": "PACKAGE_COUNT",
            "value": "25 Cartons",
            "normalized_value": 25,
            "unit": "cartons",
            "page": 1,
            "bbox": [400, 410, 550, 435],
            "extraction_confidence": 0.95,
            "classification_confidence": 0.97,
            "normalization_warning": False,
        },
        {
            "entity_type": "INCOTERM",
            "value": "FOB Colombo",
            "normalized_value": "FOB",
            "unit": None,
            "page": 1,
            "bbox": [50, 300, 200, 325],
            "extraction_confidence": 0.92,
            "classification_confidence": 0.97,
            "normalization_warning": False,
        },
        {
            "entity_type": "TOTAL_AMOUNT",
            "value": "45,230.00 USD",
            "normalized_value": 45230.0,
            "unit": None,
            "page": 1,
            "bbox": [400, 500, 580, 530],
            "extraction_confidence": 0.94,
            "classification_confidence": 0.97,
            "normalization_warning": False,
        },
    ],
    "raw_ocr": [
        {"text": "Gross Weight: 450.00 KG", "page": 1, "bbox": [100, 340, 560, 380], "ocr_confidence": 0.98},
        {"text": "COMMERCIAL INVOICE", "page": 1, "bbox": [100, 50, 400, 80], "ocr_confidence": 0.99},
    ],
    "processing_time_ms": 1200,
    "errors": [],
}

# AWB: GROSS_WEIGHT intentionally 448.5 (vs invoice 450.0) to seed a real discrepancy.
# CONSIGNEE_NAME has trailing period to test SemanticFallback.
MOCK_AWB = {
    "document_id": "mock_awb",
    "document_type": "awb",
    "classification_confidence": 0.95,
    "classification_evidence": ["air waybill", "awb number", "flight", "airline"],
    "entities": [
        {
            "entity_type": "AWB_NUMBER",
            "value": "631-12345678",
            "normalized_value": "631-12345678",
            "unit": None,
            "page": 1,
            "bbox": [200, 50, 400, 80],
            "extraction_confidence": 0.97,
            "classification_confidence": 0.95,
            "normalization_warning": False,
        },
        {
            "entity_type": "CONSIGNEE_NAME",
            "value": "ABC Textiles Ltd.",
            "normalized_value": "ABC Textiles Ltd.",
            "unit": None,
            "page": 1,
            "bbox": [50, 200, 350, 225],
            "extraction_confidence": 0.89,
            "classification_confidence": 0.95,
            "normalization_warning": False,
        },
        {
            "entity_type": "GROSS_WEIGHT",
            "value": "448.50 KG",
            "normalized_value": 448.5,
            "unit": "kg",
            "page": 1,
            "bbox": [350, 300, 500, 325],
            "extraction_confidence": 0.93,
            "classification_confidence": 0.95,
            "normalization_warning": False,
        },
        {
            "entity_type": "PACKAGE_COUNT",
            "value": "25 Pieces",
            "normalized_value": 25,
            "unit": "pieces",
            "page": 1,
            "bbox": [350, 330, 500, 355],
            "extraction_confidence": 0.94,
            "classification_confidence": 0.95,
            "normalization_warning": False,
        },
    ],
    "raw_ocr": [
        {"text": "Gross Weight: 448.50 KG", "page": 1, "bbox": [300, 290, 510, 330], "ocr_confidence": 0.97},
        {"text": "AIR WAYBILL", "page": 1, "bbox": [100, 50, 350, 80], "ocr_confidence": 0.99},
    ],
    "processing_time_ms": 950,
    "errors": [],
}

MOCK_PACKING_LIST = {
    "document_id": "mock_pl",
    "document_type": "packing_list",
    "classification_confidence": 0.96,
    "classification_evidence": ["packing list", "carton", "net weight", "gross weight"],
    "entities": [
        {
            "entity_type": "GROSS_WEIGHT",
            "value": "450.00 KG",
            "normalized_value": 450.0,
            "unit": "kg",
            "page": 1,
            "bbox": [350, 400, 500, 425],
            "extraction_confidence": 0.95,
            "classification_confidence": 0.96,
            "normalization_warning": False,
        },
        {
            "entity_type": "NET_WEIGHT",
            "value": "420.00 KG",
            "normalized_value": 420.0,
            "unit": "kg",
            "page": 1,
            "bbox": [350, 430, 500, 455],
            "extraction_confidence": 0.93,
            "classification_confidence": 0.96,
            "normalization_warning": False,
        },
        {
            "entity_type": "TARE_WEIGHT",
            "value": "30.00 KG",
            "normalized_value": 30.0,
            "unit": "kg",
            "page": 1,
            "bbox": [350, 460, 500, 485],
            "extraction_confidence": 0.90,
            "classification_confidence": 0.96,
            "normalization_warning": False,
        },
        {
            "entity_type": "PACKAGE_COUNT",
            "value": "25 Cartons",
            "normalized_value": 25,
            "unit": "cartons",
            "page": 1,
            "bbox": [350, 490, 500, 515],
            "extraction_confidence": 0.96,
            "classification_confidence": 0.96,
            "normalization_warning": False,
        },
    ],
    "raw_ocr": [
        {"text": "Gross Weight: 450.00 KG", "page": 1, "bbox": [300, 390, 510, 430], "ocr_confidence": 0.98},
        {"text": "PACKING LIST", "page": 1, "bbox": [100, 50, 300, 80], "ocr_confidence": 0.99},
    ],
    "processing_time_ms": 880,
    "errors": [],
}

MOCK_BILL_OF_LADING = {
    "document_id": "mock_bol",
    "document_type": "bl",
    "classification_confidence": 0.94,
    "classification_evidence": ["bill of lading", "vessel", "port of discharge", "shipper"],
    "entities": [
        {
            "entity_type": "BL_NUMBER",
            "value": "COSU6301882LK",
            "normalized_value": "COSU6301882LK",
            "unit": None,
            "page": 1,
            "bbox": [200, 60, 420, 85],
            "extraction_confidence": 0.96,
            "classification_confidence": 0.94,
            "normalization_warning": False,
        },
        {
            "entity_type": "CONSIGNEE_NAME",
            "value": "ABC Textiles Ltd",
            "normalized_value": "ABC Textiles Ltd",
            "unit": None,
            "page": 1,
            "bbox": [50, 200, 320, 225],
            "extraction_confidence": 0.90,
            "classification_confidence": 0.94,
            "normalization_warning": False,
        },
        {
            "entity_type": "GROSS_WEIGHT",
            "value": "450.00 KG",
            "normalized_value": 450.0,
            "unit": "kg",
            "page": 1,
            "bbox": [380, 310, 530, 335],
            "extraction_confidence": 0.91,
            "classification_confidence": 0.94,
            "normalization_warning": False,
        },
    ],
    "raw_ocr": [
        {"text": "BILL OF LADING", "page": 1, "bbox": [100, 50, 350, 80], "ocr_confidence": 0.99},
    ],
    "processing_time_ms": 1050,
    "errors": [],
}

MOCK_DELIVERY_ORDER = {
    "document_id": "mock_do",
    "document_type": "delivery_order",
    "classification_confidence": 0.93,
    "classification_evidence": ["delivery order", "release", "port", "agent"],
    "entities": [
        {
            "entity_type": "DO_NUMBER",
            "value": "DO-LK-2024-4892",
            "normalized_value": "DO-LK-2024-4892",
            "unit": None,
            "page": 1,
            "bbox": [200, 70, 400, 95],
            "extraction_confidence": 0.94,
            "classification_confidence": 0.93,
            "normalization_warning": False,
        },
        {
            "entity_type": "CONSIGNEE_NAME",
            "value": "ABC Textiles Ltd",
            "normalized_value": "ABC Textiles Ltd",
            "unit": None,
            "page": 1,
            "bbox": [50, 200, 320, 225],
            "extraction_confidence": 0.92,
            "classification_confidence": 0.93,
            "normalization_warning": False,
        },
    ],
    "raw_ocr": [
        {"text": "DELIVERY ORDER", "page": 1, "bbox": [100, 50, 320, 80], "ocr_confidence": 0.98},
    ],
    "processing_time_ms": 700,
    "errors": [],
}


# ---------------------------------------------------------------------------
# Dispatch map keyed by document_type string
# ---------------------------------------------------------------------------
_TYPE_TEMPLATES = {
    "commercial_invoice": MOCK_COMMERCIAL_INVOICE,
    "awb":                MOCK_AWB,
    "packing_list":       MOCK_PACKING_LIST,
    "bl":                 MOCK_BILL_OF_LADING,
    "delivery_order":     MOCK_DELIVERY_ORDER,
}

# Filename keyword sets => document type (first match wins)
_FILENAME_KEYWORDS = [
    (["awb", "airway", "air_way"],               "awb"),
    (["packing", "pack_list"],                   "packing_list"),
    (["bill_of_lading", "bol"],                  "bl"),
    (["delivery_order", "delivery"],             "delivery_order"),
    (["invoice", "commercial"],                   "commercial_invoice"),
]


class MockPipeline:
    """
    Drop-in replacement for AIPipeline.
    Dispatches by filename keyword to return the correct document type/entities.
    Intentional discrepancies seeded: AWB GROSS_WEIGHT=448.5 vs Invoice 450.0.
    """

    def process_document(self, pdf_path: str, document_id: str) -> dict:
        doc_type = self._infer_type(pdf_path)
        template = _TYPE_TEMPLATES.get(doc_type, MOCK_COMMERCIAL_INVOICE)
        result = deepcopy(template)
        result["document_id"] = document_id
        return result

    def _infer_type(self, pdf_path: str) -> str:
        name = Path(pdf_path).stem.lower().replace(" ", "_").replace("-", "_")
        for keywords, doc_type in _FILENAME_KEYWORDS:
            if any(kw in name for kw in keywords):
                return doc_type
        return "commercial_invoice"


# ── Singleton ──────────────────────────────────────────────────────────
_mock_instance: MockPipeline | None = None


def get_mock_pipeline() -> MockPipeline:
    global _mock_instance
    if _mock_instance is None:
        _mock_instance = MockPipeline()
    return _mock_instance


# ---------------------------------------------------------------------------
# Legacy helpers — kept for backwards compatibility
# ---------------------------------------------------------------------------

def run_mock_pipeline(file_path: str) -> dict:
    """Legacy function — use get_mock_pipeline().process_document() instead."""
    import uuid
    return get_mock_pipeline().process_document(file_path, str(uuid.uuid4()))


def run_mock_pipeline_batch(file_paths: list[str]) -> list[dict]:
    """Legacy batch helper."""
    return [run_mock_pipeline(fp) for fp in file_paths]
