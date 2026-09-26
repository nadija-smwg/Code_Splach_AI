from reasoning.cusdec_readiness import (
    EXTRACTED_REQUIREMENTS,
    PROFILE_REQUIREMENTS,
    build_cusdec_readiness,
)


def _field(entity_type, value, status="match"):
    return {
        "entity_type": entity_type,
        "consensus_value": value,
        "status": status,
    }


def _complete_fields():
    values = {
        "INVOICE_NUMBER": "INV-100",
        "CONSIGNEE_NAME": "Example Imports (Pvt) Ltd",
        "SHIPPER_NAME": "Example Exporter Ltd",
        "TOTAL_AMOUNT": 1250.5,
        "CURRENCY_CODE": "USD",
        "INCOTERM": "CIF",
        "GROSS_WEIGHT": 250.0,
        "PACKAGE_COUNT": 10,
        "COUNTRY_OF_ORIGIN": "India",
        "PORT_OF_LOADING": "Chennai",
        "PORT_OF_DISCHARGE": "Colombo",
        "HS_CODE": "61091000",
        "AWB_NUMBER": "12345678901",
    }
    return [_field(name, values[name]) for name in EXTRACTED_REQUIREMENTS] + [
        _field("AWB_NUMBER", values["AWB_NUMBER"]),
    ]


def _complete_document():
    return {
        "line_items": [{"description": "Cotton T-shirts", "quantity": 10}],
        "declaration_profile": {
            key: f"value-{key}" for key in PROFILE_REQUIREMENTS
        },
    }


def test_missing_documents_are_blocked():
    readiness = build_cusdec_readiness([], [])
    assert readiness["status"] == "blocked"
    assert any(blocker["code"] == "NO_DOCUMENTS" for blocker in readiness["blockers"])
    assert readiness["export_allowed"] is False


def test_pending_source_field_blocks_export():
    fields = _complete_fields()
    fields[0]["status"] = "pending"
    readiness = build_cusdec_readiness([_complete_document()], fields)
    assert any(
        blocker["code"] == "UNRESOLVED_FIELD" and blocker["field"] == "INVOICE_NUMBER"
        for blocker in readiness["blockers"]
    )


def test_schema_validation_remains_a_hard_blocker_after_data_checks_pass():
    readiness = build_cusdec_readiness([_complete_document()], _complete_fields())
    assert readiness["blocker_count"] == 1
    assert readiness["blockers"][0]["code"] == "OFFICIAL_SCHEMA_VALIDATION_REQUIRED"


def test_reviewer_declaration_metadata_satisfies_profile_requirements():
    document = _complete_document()
    document.pop("declaration_profile")
    readiness = build_cusdec_readiness(
        [document],
        _complete_fields(),
        {key: f"verified-{key}" for key in PROFILE_REQUIREMENTS},
    )

    assert not any(blocker["code"] == "MISSING_DECLARATION_METADATA" for blocker in readiness["blockers"])
    assert readiness["profile"]["consignee_code"] == "verified-consignee_code"
