from types import SimpleNamespace

from ai_pipeline.party_roles import classify_party_role, resolve_party_entity


def _token(text: str, bbox: list[int], page: int = 1):
    return SimpleNamespace(text=text, bbox=bbox, page=page)


def test_explicit_consignee_is_eligible_for_resolution():
    tokens = [_token("Consignee: MARTEK M F G (PVT) LTD", [50, 100, 420, 130])]

    entity_type, role, eligible = resolve_party_entity(
        "CONSIGNEE_NAME", "MARTEK M F G (PVT) LTD", [50, 100, 420, 130], 1, tokens
    )

    assert entity_type == "CONSIGNEE_NAME"
    assert role == "consignee"
    assert eligible is True


def test_carrier_never_becomes_a_consignee():
    tokens = [
        _token("Carrier", [50, 100, 130, 125]),
        _token("MSA AIR PVT LTD", [50, 135, 260, 160]),
    ]

    assert classify_party_role("MSA AIR PVT LTD", [50, 135, 260, 160], 1, tokens) == "carrier"
    entity_type, role, eligible = resolve_party_entity(
        "CONSIGNEE_NAME", "MSA AIR PVT LTD", [50, 135, 260, 160], 1, tokens
    )

    assert entity_type == "CARRIER_NAME"
    assert role == "carrier"
    assert eligible is False


def test_bank_never_becomes_a_consignee():
    tokens = [
        _token("Issuing Bank", [310, 100, 430, 125]),
        _token("STANDARD CHARTERED BANK", [310, 135, 580, 160]),
    ]

    entity_type, role, eligible = resolve_party_entity(
        "CONSIGNEE_NAME", "STANDARD CHARTERED BANK", [310, 135, 580, 160], 1, tokens
    )

    assert entity_type == "ISSUING_BANK"
    assert role == "issuing_bank"
    assert eligible is False


def test_unlabelled_organisation_is_not_emitted_as_a_consignee():
    tokens = [_token("MSA AIR PVT LTD", [50, 135, 260, 160])]

    entity_type, role, eligible = resolve_party_entity(
        "CONSIGNEE_NAME", "MSA AIR PVT LTD", [50, 135, 260, 160], 1, tokens
    )

    assert entity_type is None
    assert role is None
    assert eligible is False
