from reasoning.entity_resolution import apply_manual_resolutions, resolve_documents


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


def test_missing_field_in_a_document_is_not_a_conflict():
    fields = resolve_documents("shipment-1", [
        _document("invoice", "commercial_invoice", [_entity("TOTAL_AMOUNT", "45,230.00 USD", 45230.0, "USD")]),
        _document("awb", "awb", [_entity("AWB_NUMBER", "631-12345678", "631-12345678", None)]),
    ])
    total = next(item for item in fields if item["entity_type"] == "TOTAL_AMOUNT")
    assert total["status"] == "pending"
    assert not total["assertions"][0]["is_outlier"]


def test_role_excluded_consignee_is_not_resolved_or_flagged():
    fields = resolve_documents("shipment-1", [
        _document("invoice", "commercial_invoice", [
            {**_entity("CONSIGNEE_NAME", "MARTEK M F G (PVT) LTD", "MARTEK M F G (PVT) LTD", None),
             "party_role": "consignee", "resolver_eligible": True},
        ]),
        _document("awb", "awb", [
            {**_entity("CONSIGNEE_NAME", "MSA AIR PVT LTD", "MSA AIR PVT LTD", None),
             "party_role": "carrier", "resolver_eligible": False},
        ]),
    ])

    field = next(item for item in fields if item["entity_type"] == "CONSIGNEE_NAME")
    assert field["status"] == "pending"
    assert field["consensus_value"] == "MARTEK M F G (PVT) LTD"
    assert len(field["assertions"]) == 1


def test_legacy_bank_value_is_excluded_using_saved_ocr_evidence():
    fields = resolve_documents("shipment-1", [
        _document("invoice", "commercial_invoice", [{
            **_entity("CONSIGNEE_NAME", "MARTEK M F G (PVT) LTD", "MARTEK M F G (PVT) LTD", None),
            "raw_ocr": [],
        }]),
        {
            "document_id": "awb",
            "document_type": "awb",
            "raw_ocr": [
                {"text": "Issuing Bank", "page": 1, "bbox": [300, 100, 430, 125]},
                {"text": "STANDARD CHARTERED BANK", "page": 1, "bbox": [300, 135, 580, 160]},
            ],
            "entities": [_entity("CONSIGNEE_NAME", "STANDARD CHARTERED BANK", "STANDARD CHARTERED BANK", None)],
        },
    ])

    field = next(item for item in fields if item["entity_type"] == "CONSIGNEE_NAME")
    assert field["status"] == "pending"
    assert len(field["assertions"]) == 1


def test_manual_resolution_replaces_consensus_but_preserves_source_assertions():
    fields = resolve_documents("shipment-1", [
        _document("invoice", "commercial_invoice", [_entity("GROSS_WEIGHT", "450.00 KG", 450.0)]),
        _document("awb", "awb", [_entity("GROSS_WEIGHT", "448.50 KG", 448.5)]),
    ])
    field = fields[0]
    resolved = apply_manual_resolutions(fields, {
        field["canonical_field_id"]: {
            "resolved_value": 448.5,
            "source_assertion_id": field["assertions"][1]["assertion_id"],
            "reason": "Verified against the signed air waybill.",
            "resolved_by": "reviewer",
        },
    })[0]

    assert resolved["status"] == "resolved"
    assert resolved["consensus_value"] == 448.5
    assert len(resolved["assertions"]) == 2
    assert resolved["assertions"][1]["is_consensus"] is True
