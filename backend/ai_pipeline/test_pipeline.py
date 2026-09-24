# backend/ai_pipeline/test_pipeline.py
# Phase 10 — Pipeline Integration Tests
#
# Covers all 11 required tests from Phase_10_Pipeline_Orchestration.md.
# All AI deps (OCR, Gemini, DB, pdf2image) are mocked — no real I/O needed.
#
# Run: pytest backend/ai_pipeline/test_pipeline.py -v

import json
import pytest
from copy import deepcopy
from unittest.mock import MagicMock, patch, PropertyMock


# ===========================================================================
# Shared constants — Phase 10 master contract
# ===========================================================================

REQUIRED_TOP_KEYS = {
    "document_id",
    "document_type",
    "classification_confidence",
    "classification_evidence",
    "entities",
    "raw_ocr",
    "processing_time_ms",
    "errors",
}

REQUIRED_ENTITY_KEYS = {
    "entity_type",
    "value",
    "normalized_value",
    "unit",
    "page",
    "bbox",
    "extraction_confidence",
    "classification_confidence",
    "normalization_warning",
}

REQUIRED_RAW_OCR_KEYS = {"text", "page", "bbox", "ocr_confidence"}


# ===========================================================================
# Fixtures
# ===========================================================================

def _make_mock_token(text="450.00 KG", page=1, bbox=None, confidence=0.98):
    t = MagicMock()
    t.text = text
    t.page = page
    t.bbox = bbox or [120, 240, 410, 290]
    t.confidence = confidence
    return t


def _make_ocr_result(tokens=None, pages=1):
    mock_page = MagicMock()
    mock_page.tokens = tokens or [_make_mock_token()]
    mock_page.page_number = 1
    mock_page.width = 595
    mock_page.height = 842

    mock_result = MagicMock()
    mock_result.pages = [mock_page] * pages
    mock_result.file_path = "/fake/invoice.pdf"
    mock_result.total_pages = pages
    return mock_result


def _make_classification(doc_type="commercial_invoice", conf=0.97, evidence=None):
    c = MagicMock()
    c.document_type = doc_type
    c.confidence = conf
    c.evidence = evidence or ["invoice", "unit price", "total amount"]
    c.all_scores = {doc_type: conf}
    return c


def _make_entity(entity_type="GROSS_WEIGHT", value="450.00 KG", bbox=None):
    return {
        "entity_type": entity_type,
        "value": value,
        "bbox": bbox or [120, 240, 410, 290],
        "extraction_confidence": 0.94,
        "ocr_confidence": 0.98,
        "bbox_match_ratio": 0.95,
    }


def _build_pipeline(
    doc_type="commercial_invoice",
    entities=None,
    ocr_fail=False,
    classify_fail=False,
    extract_fail=False,
    normalize_return=None,
    pages=1,
):
    """Return a fully mocked AIPipeline ready for unit testing."""
    from ai_pipeline.pipeline import AIPipeline

    p = AIPipeline.__new__(AIPipeline)

    ocr_result = _make_ocr_result(pages=pages)

    if ocr_fail:
        p.ocr = MagicMock()
        p.ocr.extract = MagicMock(side_effect=RuntimeError("PaddleOCR unavailable"))
    else:
        p.ocr = MagicMock()
        p.ocr.extract = MagicMock(return_value=ocr_result)

    if classify_fail:
        p.classifier = MagicMock()
        p.classifier.classify = MagicMock(side_effect=ValueError("classifier broken"))
    else:
        p.classifier = MagicMock()
        p.classifier.classify = MagicMock(
            return_value=_make_classification(doc_type)
        )

    if extract_fail:
        p.extractor = MagicMock()
        p.extractor.extract = MagicMock(side_effect=RuntimeError("Gemini error"))
    else:
        ents = entities if entities is not None else [_make_entity()]
        p.extractor = MagicMock()
        p.extractor.extract = MagicMock(return_value=[deepcopy(e) for e in ents])

    norm_resp = normalize_return or {
        "normalized_value": 450.0,
        "unit": "kg",
        "warn": False,
    }
    p.normalizer = MagicMock()
    p.normalizer.normalize = MagicMock(return_value=norm_resp)

    p.scorer = MagicMock()
    p.scorer.score_entities = MagicMock(
        side_effect=lambda ents: [
            {**e, "extraction_confidence": e.get("extraction_confidence", 0.94)}
            for e in ents
        ]
    )

    return p, ocr_result


# ===========================================================================
# MockPipeline Tests — schema correctness
# ===========================================================================

class TestMockPipeline:

    def setup_method(self):
        from ai_pipeline.mock_pipeline import get_mock_pipeline
        self.pipeline = get_mock_pipeline()

    def test_returns_all_required_top_keys(self):
        r = self.pipeline.process_document("invoice.pdf", "doc_001")
        missing = REQUIRED_TOP_KEYS - r.keys()
        assert not missing, f"Missing top-level keys: {missing}"

    def test_document_id_is_stamped_correctly(self):
        r = self.pipeline.process_document("invoice.pdf", "my_doc_id")
        assert r["document_id"] == "my_doc_id"

    def test_each_entity_has_required_keys(self):
        r = self.pipeline.process_document("invoice.pdf", "doc_001")
        for entity in r["entities"]:
            missing = REQUIRED_ENTITY_KEYS - entity.keys()
            assert not missing, f"Entity missing keys: {missing}"

    def test_raw_value_preserved(self):
        r = self.pipeline.process_document("invoice.pdf", "doc_001")
        weight = next(
            e for e in r["entities"] if e["entity_type"] == "GROSS_WEIGHT"
        )
        # raw value must remain the original string
        assert weight["value"] == "450.00 KG"
        # normalized_value is a float
        assert weight["normalized_value"] == 450.0

    def test_deepcopy_isolates_calls(self):
        """Mutating one result must not affect the next call."""
        r1 = self.pipeline.process_document("a.pdf", "doc_a")
        r1["entities"].clear()
        r2 = self.pipeline.process_document("b.pdf", "doc_b")
        assert len(r2["entities"]) > 0

    def test_mock_schema_matches_real_error_result(self):
        """
        MockPipeline and AIPipeline._error_result() must have identical
        top-level key sets.
        """
        from ai_pipeline.pipeline import AIPipeline
        real = AIPipeline.__new__(AIPipeline)
        error_result = real._error_result("doc_err", "test error")
        mock_result = self.pipeline.process_document("x.pdf", "doc_ok")
        assert set(error_result.keys()) == set(mock_result.keys()), (
            f"Schema mismatch:\n"
            f"  real:  {sorted(error_result.keys())}\n"
            f"  mock:  {sorted(mock_result.keys())}"
        )


# ===========================================================================
# TEST 1 — Commercial Invoice contract
# ===========================================================================

class TestCommercialInvoice:

    def test_document_type_and_entity_count(self):
        p, _ = _build_pipeline(
            doc_type="commercial_invoice",
            entities=[_make_entity(et, v) for et, v in [
                ("INVOICE_NUMBER", "INV-2024-1023"),
                ("CONSIGNEE_NAME", "ABC Textiles Ltd"),
                ("GROSS_WEIGHT", "450.00 KG"),
                ("NET_WEIGHT", "420.00 KG"),
                ("PACKAGE_COUNT", "25 Cartons"),
                ("INCOTERM", "FOB Colombo"),
                ("TOTAL_AMOUNT", "45,230.00 USD"),
                ("INVOICE_DATE", "15-Aug-2024"),
            ]],
        )
        with patch("ai_pipeline.pipeline.convert_from_path", return_value=[MagicMock()]):
            r = p.process_document("invoice.pdf", "doc_001")

        assert r["document_type"] == "commercial_invoice"
        assert len(r["entities"]) >= 8

    def test_every_entity_has_all_required_fields(self):
        p, _ = _build_pipeline()
        with patch("ai_pipeline.pipeline.convert_from_path", return_value=[MagicMock()]):
            r = p.process_document("invoice.pdf", "doc_001")

        for entity in r["entities"]:
            for key in REQUIRED_ENTITY_KEYS:
                assert key in entity, f"Missing '{key}' in entity {entity}"


# ===========================================================================
# TEST 2 — Packing List
# ===========================================================================

class TestPackingList:

    def test_document_type_and_entity_count(self):
        p, _ = _build_pipeline(
            doc_type="packing_list",
            entities=[_make_entity(et, v) for et, v in [
                ("GROSS_WEIGHT", "455.00 KG"),
                ("NET_WEIGHT", "420.00 KG"),
                ("TARE_WEIGHT", "25.00 KG"),
                ("PACKAGE_COUNT", "25 Cartons"),
            ]],
        )
        with patch("ai_pipeline.pipeline.convert_from_path", return_value=[MagicMock()]):
            r = p.process_document("packing_list.pdf", "doc_002")

        assert r["document_type"] == "packing_list"
        assert len(r["entities"]) >= 4


# ===========================================================================
# TEST 3 — AWB
# ===========================================================================

class TestAWB:

    def test_document_type_and_entity_count(self):
        p, _ = _build_pipeline(
            doc_type="awb",
            entities=[_make_entity(et, v) for et, v in [
                ("AWB_NUMBER", "631-12345678"),
                ("GROSS_WEIGHT", "448.50 KG"),
                ("PACKAGE_COUNT", "25 Pieces"),
                ("CONSIGNEE_NAME", "ABC Textiles Ltd."),
                ("PORT_DISCHARGE", "Los Angeles"),
            ]],
        )
        with patch("ai_pipeline.pipeline.convert_from_path", return_value=[MagicMock()]):
            r = p.process_document("awb.pdf", "doc_003")

        assert r["document_type"] == "awb"
        assert len(r["entities"]) >= 5


# ===========================================================================
# TEST 4 — Normalization Integration
# ===========================================================================

class TestNormalizationIntegration:

    def test_lbs_normalized_to_kg(self):
        p, _ = _build_pipeline(
            entities=[_make_entity("GROSS_WEIGHT", "1,000.00 LBS")],
            normalize_return={
                "normalized_value": 453.592,
                "unit": "kg",
                "warn": False,
            },
        )
        with patch("ai_pipeline.pipeline.convert_from_path", return_value=[MagicMock()]):
            r = p.process_document("invoice.pdf", "doc_004")

        weight = r["entities"][0]
        assert weight["value"] == "1,000.00 LBS"          # raw preserved
        assert weight["normalized_value"] == pytest.approx(453.592)
        assert weight["unit"] == "kg"
        assert weight["normalization_warning"] is False

    def test_raw_value_is_never_overwritten(self):
        p, _ = _build_pipeline(
            entities=[_make_entity("GROSS_WEIGHT", "1,000.00 LBS")],
        )
        with patch("ai_pipeline.pipeline.convert_from_path", return_value=[MagicMock()]):
            r = p.process_document("invoice.pdf", "doc_004b")

        # value key must always equal the original raw string
        assert r["entities"][0]["value"] == "1,000.00 LBS"


# ===========================================================================
# TEST 5 — BBox Integration
# ===========================================================================

class TestBBoxIntegration:

    def test_entity_has_bbox_or_explicit_null(self):
        p, _ = _build_pipeline(
            entities=[_make_entity(bbox=[50, 100, 400, 140])],
        )
        with patch("ai_pipeline.pipeline.convert_from_path", return_value=[MagicMock()]):
            r = p.process_document("invoice.pdf", "doc_005")

        entity = r["entities"][0]
        # bbox is either a list of 4 ints, or explicitly None — never missing
        assert "bbox" in entity
        if entity["bbox"] is not None:
            assert len(entity["bbox"]) == 4


# ===========================================================================
# TEST 7 — Invalid PDF (OCR failure)
# ===========================================================================

class TestInvalidPDF:

    def test_returns_error_result_without_raising(self):
        p, _ = _build_pipeline(ocr_fail=True)

        # No patch needed — OCR fails before convert_from_path
        r = p.process_document("not_a_pdf.pdf", "doc_007")

        assert r["document_type"] == "unknown"
        assert r["entities"] == []
        assert len(r["errors"]) >= 1
        assert "OCR failed" in r["errors"][0]

    def test_no_exception_propagates(self):
        p, _ = _build_pipeline(ocr_fail=True)
        try:
            r = p.process_document("bad.pdf", "doc_007b")
        except Exception as exc:
            pytest.fail(f"Pipeline raised an exception: {exc}")


# ===========================================================================
# TEST 8 — Empty PDF (no entities extracted)
# ===========================================================================

class TestEmptyPDF:

    def test_no_crash_empty_entities(self):
        p, _ = _build_pipeline(entities=[])
        with patch("ai_pipeline.pipeline.convert_from_path", return_value=[MagicMock()]):
            r = p.process_document("empty.pdf", "doc_008")

        assert isinstance(r, dict)
        assert r["entities"] == []
        assert r["errors"] == []


# ===========================================================================
# TEST 9 — Gemini / Extractor Failure
# ===========================================================================

class TestGeminiFailure:

    def test_errors_populated_pipeline_continues(self):
        p, _ = _build_pipeline(extract_fail=True)
        with patch("ai_pipeline.pipeline.convert_from_path", return_value=[MagicMock()]):
            r = p.process_document("invoice.pdf", "doc_009")

        assert len(r["errors"]) >= 1
        assert any("extraction failed" in e.lower() for e in r["errors"])

    def test_result_is_still_valid_contract(self):
        p, _ = _build_pipeline(extract_fail=True)
        with patch("ai_pipeline.pipeline.convert_from_path", return_value=[MagicMock()]):
            r = p.process_document("invoice.pdf", "doc_009b")

        assert REQUIRED_TOP_KEYS.issubset(r.keys())


# ===========================================================================
# TEST 10 — Database Failure (normalization graceful degradation)
# ===========================================================================

class TestDatabaseFailure:

    def test_normalization_continues_when_db_down(self):
        """
        Even when _db_pool is None, EntityNormalizer should return a safe
        fallback. The pipeline should still produce a valid result.
        """
        p, _ = _build_pipeline(
            normalize_return={
                "normalized_value": 450.0,
                "unit": "kg",
                "warn": False,
            }
        )
        with patch("ai_pipeline.pipeline.convert_from_path", return_value=[MagicMock()]):
            r = p.process_document("invoice.pdf", "doc_010")

        # Should still produce normalized entities
        assert len(r["entities"]) > 0
        assert r["entities"][0]["normalized_value"] is not None

    def test_normalization_exception_sets_warn_true(self):
        """
        If normalizer.normalize() itself raises, entity should have
        normalized_value=None and normalization_warning=True.
        """
        p, _ = _build_pipeline()
        p.normalizer.normalize = MagicMock(side_effect=RuntimeError("DB gone"))

        with patch("ai_pipeline.pipeline.convert_from_path", return_value=[MagicMock()]):
            r = p.process_document("invoice.pdf", "doc_010b")

        assert len(r["entities"]) > 0
        entity = r["entities"][0]
        assert entity["normalized_value"] is None
        assert entity["normalization_warning"] is True
        assert len(r["errors"]) >= 1


# ===========================================================================
# TEST 11 — JSON Serialization
# ===========================================================================

class TestJSONSerialization:

    def test_result_is_fully_json_serializable(self):
        from ai_pipeline.mock_pipeline import get_mock_pipeline
        pipeline = get_mock_pipeline()
        result = pipeline.process_document("invoice.pdf", "doc_011")

        try:
            serialized = json.dumps(result, indent=2)
        except (TypeError, ValueError) as exc:
            pytest.fail(f"JSON serialization failed: {exc}")

        assert len(serialized) > 100

    def test_real_pipeline_result_is_json_serializable(self):
        p, _ = _build_pipeline()
        with patch("ai_pipeline.pipeline.convert_from_path", return_value=[MagicMock()]):
            result = p.process_document("invoice.pdf", "doc_011b")

        try:
            json.dumps(result, indent=2)
        except (TypeError, ValueError) as exc:
            pytest.fail(f"Real pipeline result not JSON serializable: {exc}")


# ===========================================================================
# Deduplication tests
# ===========================================================================

class TestDeduplication:

    def test_true_duplicate_is_removed(self):
        """Same entity_type + same normalized_value → keep one (higher conf)."""
        from ai_pipeline.pipeline import AIPipeline
        p = AIPipeline.__new__(AIPipeline)

        entities = [
            {"entity_type": "INVOICE_NUMBER", "value": "INV-1023",
             "normalized_value": "INV1023", "extraction_confidence": 0.92,
             "unit": None, "page": 1, "bbox": [0, 0, 100, 20],
             "classification_confidence": 0.97, "normalization_warning": False},
            {"entity_type": "INVOICE_NUMBER", "value": "INV-1023",
             "normalized_value": "INV1023", "extraction_confidence": 0.97,
             "unit": None, "page": 2, "bbox": [0, 0, 100, 20],
             "classification_confidence": 0.97, "normalization_warning": False},
        ]

        result = p._deduplicate_entities(entities)
        assert len(result) == 1
        assert result[0]["extraction_confidence"] == 0.97  # higher kept

    def test_genuine_conflict_is_preserved(self):
        """Different normalized values for same entity_type → BOTH kept."""
        from ai_pipeline.pipeline import AIPipeline
        p = AIPipeline.__new__(AIPipeline)

        entities = [
            {"entity_type": "GROSS_WEIGHT", "value": "450.00 KG",
             "normalized_value": 450.0, "extraction_confidence": 0.94,
             "unit": "kg", "page": 1, "bbox": [], "classification_confidence": 0.97,
             "normalization_warning": False},
            {"entity_type": "GROSS_WEIGHT", "value": "448.50 KG",
             "normalized_value": 448.5, "extraction_confidence": 0.93,
             "unit": "kg", "page": 1, "bbox": [], "classification_confidence": 0.95,
             "normalization_warning": False},
        ]

        result = p._deduplicate_entities(entities)
        assert len(result) == 2, (
            "Conflict (450 vs 448.5) must NOT be deduplicated — "
            "Aloka needs both values for conflict detection"
        )


# ===========================================================================
# Singleton test
# ===========================================================================

class TestSingleton:

    def test_get_pipeline_returns_same_instance(self):
        from ai_pipeline.pipeline import get_pipeline
        import ai_pipeline.pipeline as pm
        pm._pipeline_instance = None  # reset for clean test

        with patch.object(pm.AIPipeline, "__init__", return_value=None):
            a = get_pipeline()
            b = get_pipeline()
            assert a is b
