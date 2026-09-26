"""Canonical field resolution for multi-document shipment dossiers.

Raw extraction is deliberately preserved as a source assertion.  A canonical
field is the shipment-level component those assertions describe, allowing the
graph and review UI to show both consensus and conflicting evidence.
"""
from __future__ import annotations

import re
from types import SimpleNamespace
from typing import Any

from ai_pipeline.party_roles import classify_party_role


# These are the shipment-level values available to the CUSDEC readiness check.
# Source assertions stay in the graph, while this set defines which extracted
# values can influence a declaration draft. Do not silently add display-only
# fields here: every field in this set must have a declaration purpose.
CUSDEC_FIELDS = {
    "CONSIGNEE_NAME", "CONSIGNEE_ADDRESS", "SHIPPER_NAME",
    "GROSS_WEIGHT", "NET_WEIGHT", "PACKAGE_COUNT", "AWB_NUMBER",
    "BL_NUMBER", "INCOTERM", "TOTAL_AMOUNT", "INVOICE_NUMBER",
    "CURRENCY_CODE", "PAYMENT_TERMS", "COUNTRY_OF_ORIGIN",
    "PORT_OF_LOADING", "PORT_OF_DISCHARGE", "VESSEL_NAME",
    "FLIGHT_NUMBER", "ORIGIN", "DESTINATION", "FREIGHT_AMOUNT",
    "INSURANCE_AMOUNT", "CONTAINER_NUMBER", "SHIPPING_MARKS", "HS_CODE",
}

FIELD_LABELS = {
    "GROSS_WEIGHT": "Gross Weight", "NET_WEIGHT": "Net Weight",
    "PACKAGE_COUNT": "Package Count", "CONSIGNEE_NAME": "Consignee Name",
    "CONSIGNEE_ADDRESS": "Consignee Address", "SHIPPER_NAME": "Shipper Name",
    "INVOICE_NUMBER": "Invoice Number", "PAYMENT_TERMS": "Payment Terms",
    "AWB_NUMBER": "Air Waybill Number", "BL_NUMBER": "Bill of Lading Number",
    "HS_CODE": "HS Code", "INCOTERM": "Incoterm",
    "COUNTRY_OF_ORIGIN": "Country of Origin", "PORT_OF_LOADING": "Port of Loading",
    "PORT_OF_DISCHARGE": "Port of Discharge", "TOTAL_AMOUNT": "Total Amount",
    "CURRENCY_CODE": "Currency", "FREIGHT_AMOUNT": "Freight Amount",
    "INSURANCE_AMOUNT": "Insurance Amount", "VESSEL_NAME": "Vessel Name",
    "FLIGHT_NUMBER": "Flight Number", "ORIGIN": "Origin",
    "DESTINATION": "Destination", "CONTAINER_NUMBER": "Container Number",
    "SHIPPING_MARKS": "Shipping Marks",
}


def _display_document_type(document_type: str) -> str:
    labels = {"awb": "Air Waybill", "bl": "Bill of Lading"}
    return labels.get(document_type, document_type.replace("_", " ").title())


def _text_key(value: Any) -> str:
    """Conservative text normalization used before optional semantic matching."""
    return re.sub(r"[^a-z0-9]+", "", str(value or "").lower())


def _is_number(value: Any) -> bool:
    return isinstance(value, (int, float)) and not isinstance(value, bool)


def _same_numeric(left: float, right: float) -> bool:
    return abs(float(left) - float(right)) <= 0.01


def _legacy_consignee_role(document: dict[str, Any], entity: dict[str, Any]) -> str | None:
    """Recover party-role evidence from OCR saved before role metadata existed."""
    raw_tokens = document.get("raw_ocr") or []
    if not raw_tokens:
        return None
    tokens = [
        SimpleNamespace(
            text=str(token.get("text", "")),
            page=int(token.get("page", 1)),
            bbox=token.get("bbox", []),
        )
        for token in raw_tokens
        if isinstance(token, dict)
    ]
    return classify_party_role(
        str(entity.get("value", "")), entity.get("bbox", []), int(entity.get("page", 1)), tokens
    )


def _choose_consensus(assertions: list[dict[str, Any]]) -> tuple[Any, list[str]]:
    """Return a majority/high-confidence consensus and its assertion IDs."""
    numeric = all(_is_number(a["normalized_value"]) for a in assertions)
    clusters: list[list[dict[str, Any]]] = []
    for assertion in assertions:
        for cluster in clusters:
            exemplar = cluster[0]["normalized_value"]
            same = _same_numeric(exemplar, assertion["normalized_value"]) if numeric else (
                _text_key(exemplar) == _text_key(assertion["normalized_value"])
            )
            if same:
                cluster.append(assertion)
                break
        else:
            clusters.append([assertion])

    # Prefer most corroborated values, then the best extracted evidence.
    winner = max(
        clusters,
        key=lambda cluster: (len(cluster), sum(float(a["extraction_confidence"]) for a in cluster)),
    )
    return winner[0]["normalized_value"], [a["assertion_id"] for a in winner]


def resolve_documents(shipment_id: str, documents: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Resolve extracted header fields into canonical shipment-level fields.

    Line items are intentionally not merged here: they require SKU/HS-code
    identity resolution, which is a separate and stricter matching problem.
    """
    grouped: dict[str, list[dict[str, Any]]] = {}
    for document in documents:
        doc_id = str(document.get("document_id", "unknown"))
        doc_type = str(document.get("document_type", "unknown"))
        document_label = document.get("source_label") or _display_document_type(doc_type)
        for index, entity in enumerate(document.get("entities", [])):
            entity_type = entity.get("entity_type")
            if not entity_type or entity_type not in CUSDEC_FIELDS:
                continue
            # New extractions retain carriers, banks, and other organisations
            # as role-labelled evidence.  They must never be allowed to become
            # a shipment-level consignee assertion.  The default keeps older
            # stored dossiers compatible until they are reprocessed.
            if entity_type == "CONSIGNEE_NAME":
                if not entity.get("resolver_eligible", True):
                    continue
                # Existing dossiers predate party_role/resolver_eligible. Recheck
                # their persisted OCR before allowing a company into the CUSDEC
                # consignee field, so a carrier or bank stops creating a false
                # discrepancy as soon as this version is deployed.
                if "resolver_eligible" not in entity:
                    legacy_role = _legacy_consignee_role(document, entity)
                    if legacy_role and legacy_role != "consignee":
                        continue
            canonical_id = f"shipment:{shipment_id}:field:{entity_type}"
            assertion_id = f"assertion:{doc_id}:{entity_type}:{index}"
            grouped.setdefault(entity_type, []).append({
                "assertion_id": assertion_id,
                "document_id": doc_id,
                "document_type": doc_type,
                "document_label": document_label,
                "source_filename": document.get("source_filename"),
                "entity_type": entity_type,
                "raw_value": str(entity.get("value", "")),
                "normalized_value": entity.get("normalized_value", entity.get("value", "")),
                "unit": entity.get("unit"),
                "page": entity.get("page", 1),
                "bbox": entity.get("bbox", []),
                "extraction_confidence": float(entity.get("extraction_confidence", 0.0)),
                "ocr_text": entity.get("ocr_text", entity.get("value", "")),
                "canonical_field_id": canonical_id,
            })

    resolved: list[dict[str, Any]] = []
    for entity_type, assertions in grouped.items():
        consensus, consensus_ids = _choose_consensus(assertions)
        units = {str(a["unit"]).lower() for a in assertions if a.get("unit")}
        # A document may legitimately omit a field (for example, an AWB has no
        # invoice total). Absence is never represented as an assertion, so it
        # can never become a discrepancy. A single supplied value is simply
        # pending corroboration rather than a warning or conflict.
        status = "pending" if len(assertions) == 1 else (
            "match" if len(consensus_ids) == len(assertions) else "conflict"
        )
        # Equal numbers with different non-empty units need human review.
        if status == "match" and len(units) > 1:
            status = "warning"

        for assertion in assertions:
            is_consensus = assertion["assertion_id"] in consensus_ids
            assertion["is_consensus"] = is_consensus
            assertion["is_outlier"] = status == "conflict" and not is_consensus
            if _is_number(assertion["normalized_value"]) and _is_number(consensus):
                assertion["variance"] = round(abs(float(assertion["normalized_value"]) - float(consensus)), 4)
            else:
                assertion["variance"] = None

        resolved.append({
            "canonical_field_id": assertions[0]["canonical_field_id"],
            "entity_type": entity_type,
            "label": FIELD_LABELS.get(entity_type, entity_type.replace("_", " ").title()),
            "status": status,
            "consensus_value": consensus,
            "unit": assertions[0].get("unit"),
            "resolution_confidence": round(
                sum(a["extraction_confidence"] for a in assertions) / len(assertions), 4
            ),
            "assertions": assertions,
        })
    return sorted(resolved, key=lambda field: (field["status"] != "conflict", field["label"]))
