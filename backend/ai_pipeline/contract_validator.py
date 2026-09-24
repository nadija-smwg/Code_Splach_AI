# backend/ai_pipeline/contract_validator.py

def validate_extraction_result(result: dict) -> None:
    required_fields = {
        "document_id",
        "document_type",
        "classification_confidence",
        "classification_evidence",
        "entities",
        "raw_ocr",
        "processing_time_ms",
        "errors",
    }

    missing = required_fields - result.keys()

    if missing:
        raise AssertionError(
            f"Missing result fields: {sorted(missing)}"
        )

    classification_confidence = float(
        result["classification_confidence"]
    )

    assert 0.0 <= classification_confidence <= 1.0

    for entity in result["entities"]:
        required_entity_fields = {
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

        missing_entity = required_entity_fields - entity.keys()

        if missing_entity:
            raise AssertionError(
                "Missing entity fields: "
                f"{sorted(missing_entity)}"
            )

        extraction_confidence = float(
            entity["extraction_confidence"]
        )

        classification_confidence = float(
            entity["classification_confidence"]
        )

        assert 0.0 <= extraction_confidence <= 1.0
        assert 0.0 <= classification_confidence <= 1.0

        # BBox must either be null or [x1, y1, x2, y2].
        bbox = entity["bbox"]

        if bbox is not None:
            assert isinstance(bbox, list)
            assert len(bbox) == 4
            assert all(
                isinstance(v, (int, float))
                for v in bbox
            )

    for token in result["raw_ocr"]:
        assert "text" in token
        assert "page" in token
        assert "bbox" in token
        assert "ocr_confidence" in token

        ocr_confidence = float(
            token["ocr_confidence"]
        )

        assert 0.0 <= ocr_confidence <= 1.0

def numeric_close(actual, expected, tolerance=0.005):
    return abs(actual - expected) <= max(
        abs(expected) * tolerance,
        1e-9,
    )
