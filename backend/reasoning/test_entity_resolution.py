from reasoning.entity_resolution import resolve_documents


def _document(document_id, document_type, entities):
    return {"document_id": document_id, "document_type": document_type, "entities": entities}


def _entity(entity_type, value, normalized_value, unit="kg"):
    return {"entity_type": entity_type, "value": value, "normalized_value": normalized_value,
            "unit": unit, "page": 1, "bbox": [1, 2, 3, 4], "extraction_confidence": 0.95}


def test_majority_value_becomes_consensus_and_outlier_is_preserved():
    fields = resolve_documents("shipment-1", [
        _document("invoice", "commercial_invoice", [_entity("GROSS_WEIGHT", "450.00 KG", 450.0)]),
        _document("packing", "packing_list", [_entity("GROSS_WEIGHT", "450.00 KG", 450.0)]),
        _document("awb", "awb", [_entity("GROSS_WEIGHT", "448.50 KG", 448.5)]),
    ])

    field = next(item for item in fields if item["entity_type"] == "GROSS_WEIGHT")
    assert field["status"] == "conflict"
    assert field["consensus_value"] == 450.0
    assert len(field["assertions"]) == 3
    assert [item["document_id"] for item in field["assertions"] if item["is_outlier"]] == ["awb"]


def test_punctuation_only_name_difference_is_a_match():
    fields = resolve_documents("shipment-1", [
        _document("invoice", "commercial_invoice", [_entity("CONSIGNEE_NAME", "ABC Textiles Ltd", "ABC Textiles Ltd", None)]),
        _document("awb", "awb", [_entity("CONSIGNEE_NAME", "ABC Textiles Ltd.", "ABC Textiles Ltd.", None)]),
    ])
    field = next(item for item in fields if item["entity_type"] == "CONSIGNEE_NAME")
    assert field["status"] == "match"
