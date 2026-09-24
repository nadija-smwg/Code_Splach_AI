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


# ---------------------------------------------------------------------------
# Canonical mock result — commercial invoice with realistic entities.
# Intentional discrepancies are seeded here so Aloka's reasoning engine
# has something to detect during development.
# ---------------------------------------------------------------------------

MOCK_RESULT = {
    "document_id": "mock_001",
    "document_type": "commercial_invoice",
    "classification_confidence": 0.97,
    "classification_evidence": [
        "invoice",
        "unit price",
        "total amount",
    ],
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
        {
            "text": "Gross Weight: 450.00 KG",
            "page": 1,
            "bbox": [100, 340, 560, 380],
            "ocr_confidence": 0.98,
        }
    ],
    "processing_time_ms": 1200,
    "errors": [],
}


class MockPipeline:
    """
    Drop-in replacement for AIPipeline.
    Returns a deepcopy of MOCK_RESULT with the correct document_id stamped.
    """

    def process_document(
        self,
        pdf_path: str,
        document_id: str,
    ) -> dict:
        result = deepcopy(MOCK_RESULT)
        result["document_id"] = document_id
        return result


# ── Singleton ──────────────────────────────────────────────────────────
_mock_instance: MockPipeline | None = None


def get_mock_pipeline() -> MockPipeline:
    global _mock_instance
    if _mock_instance is None:
        _mock_instance = MockPipeline()
    return _mock_instance


# ---------------------------------------------------------------------------
# Legacy helpers — kept for backwards compatibility with older imports
# ---------------------------------------------------------------------------

def run_mock_pipeline(file_path: str) -> dict:
    """Legacy function — use get_mock_pipeline().process_document() instead."""
    import uuid
    return get_mock_pipeline().process_document(file_path, str(uuid.uuid4()))


def run_mock_pipeline_batch(file_paths: list[str]) -> list[dict]:
    """Legacy batch helper."""
    return [run_mock_pipeline(fp) for fp in file_paths]
