"""Role evidence for organisations extracted from trade documents.

This module deliberately has no OCR or model dependencies so extraction and
reasoning can apply the same party-role safeguards to both new and stored
dossiers.
"""
from __future__ import annotations

import re
from typing import Optional


_PARTY_ROLE_LABELS: tuple[tuple[str, tuple[str, ...]], ...] = (
    ("issuing_bank", ("issuing bank", "advising bank", "bank")),
    ("freight_forwarder", ("freight forwarder", "forwarder", "handling agent")),
    ("carrier", ("issuing carrier", "airline", "carrier", "cargo agent", "agent")),
    ("notify_party", ("notify party", "notify")),
    ("beneficiary", ("beneficiary",)),
    ("shipper", ("exporter / shipper", "exporter", "shipper", "seller")),
    ("consignee", ("consignee name", "consignee", "bill to", "deliver to", "buyer")),
)

PARTY_ROLE_ENTITY_TYPES = {
    "carrier": "CARRIER_NAME",
    "freight_forwarder": "FREIGHT_FORWARDER_NAME",
    "issuing_bank": "ISSUING_BANK",
    "beneficiary": "BENEFICIARY",
    "notify_party": "NOTIFY_PARTY_NAME",
    "shipper": "SHIPPER_NAME",
}


def _party_role_from_label(text: str) -> Optional[str]:
    normalized = re.sub(r"[^a-z0-9]+", " ", text.lower()).strip()
    for role, labels in _PARTY_ROLE_LABELS:
        if any(label in normalized for label in labels):
            return role
    return None


def classify_party_role(value: str, bbox: list, page: int, tokens: list) -> Optional[str]:
    """Return the role assigned by the closest explicit source label.

    OCR order is unreliable for multi-column AWBs.  This uses label/value
    geometry instead: same-token labels, labels immediately to the left, and
    labels immediately above in the same column are accepted.  A small set of
    unambiguous organisation-name signatures protects legacy dossiers where a
    role label was not preserved in stored OCR.
    """
    value_text = value.lower().strip()
    if re.search(r"\b(bank|bancorp|banking)\b", value_text):
        return "issuing_bank"
    if re.search(r"\b(air|airlines?|air cargo|airways|cargo)\b", value_text):
        return "carrier"
    if not bbox or len(bbox) != 4:
        return None

    x1, y1, _, y2 = bbox
    value_center_y = (y1 + y2) / 2
    best: tuple[float, str] | None = None

    for token in tokens:
        if token.page != page:
            continue
        role = _party_role_from_label(token.text)
        if role is None:
            continue

        tx1, ty1, tx2, ty2 = token.bbox
        token_text = token.text.lower().strip()
        if value_text and value_text in token_text and ":" in token.text:
            score = 1.0
        else:
            token_center_y = (ty1 + ty2) / 2
            same_row = abs(value_center_y - token_center_y) <= 48 and x1 >= tx2 - 16
            below_label = y1 >= ty2 - 16 and y1 - ty2 <= 180 and abs(x1 - tx1) <= 180
            if same_row:
                score = 0.92 - min(max(x1 - tx2, 0), 300) / 3000
            elif below_label:
                score = 0.82 - min(y1 - ty2, 160) / 1600
            else:
                continue

        if best is None or score > best[0]:
            best = (score, role)

    return best[1] if best and best[0] >= 0.75 else None


def resolve_party_entity(
    entity_type: str, value: str, bbox: list, page: int, tokens: list
) -> tuple[Optional[str], Optional[str], bool]:
    """Return (effective_type, party_role, resolver_eligible) for party data."""
    if entity_type != "CONSIGNEE_NAME":
        return entity_type, None, True

    role = classify_party_role(value, bbox, page, tokens)
    if role == "consignee":
        return "CONSIGNEE_NAME", role, True
    if role in PARTY_ROLE_ENTITY_TYPES:
        return PARTY_ROLE_ENTITY_TYPES[role], role, False
    return None, None, False
