"""CUSDEC export readiness checks.

This module is intentionally conservative.  It distinguishes values extracted
from commercial documents from declaration metadata that must be supplied by a
registered declarant.  A document value must never be replaced with a default
when a submission-ready declaration is requested.
"""
from __future__ import annotations

import re
from typing import Any


EXTRACTED_REQUIREMENTS: dict[str, str] = {
    "INVOICE_NUMBER": "Commercial invoice number",
    "CONSIGNEE_NAME": "Consignee name",
    "SHIPPER_NAME": "Exporter or shipper name",
    "TOTAL_AMOUNT": "Invoice value",
    "CURRENCY_CODE": "Invoice currency",
    "INCOTERM": "Delivery terms (Incoterm)",
    "GROSS_WEIGHT": "Gross weight",
    "PACKAGE_COUNT": "Total package count",
    "COUNTRY_OF_ORIGIN": "Country of origin",
    "PORT_OF_LOADING": "Place of loading",
    "PORT_OF_DISCHARGE": "Place of discharge",
    "HS_CODE": "Commodity HS code",
}

# These do not reliably appear in the commercial documents processed by the
# current pipeline. They must come from a registered declarant/profile and are
# never inferred or hard-coded by the exporter.
PROFILE_REQUIREMENTS: dict[str, str] = {
    "consignee_code": "Registered consignee code / TIN",
    "exporter_code": "Registered exporter code",
    "declarant_code": "Registered declarant code / TIN",
    "declarant_name": "Registered declarant name",
    "customs_office_code": "Customs clearance office code",
    "declaration_type": "Declaration type",
    "general_procedure_code": "Declaration general procedure code",
    "manifest_reference": "Manifest reference number",
    "transport_mode": "Means of transport code",
    "container_flag": "Container flag",
    "currency_rate": "Applicable currency exchange rate",
}

NUMERIC_FIELDS = {"TOTAL_AMOUNT", "GROSS_WEIGHT", "PACKAGE_COUNT"}
KNOWN_INCOTERMS = {"EXW", "FCA", "FAS", "FOB", "CFR", "CIF", "CPT", "CIP", "DAP", "DPU", "DDP"}


def _issue(code: str, field: str, message: str, *, source: str = "documents") -> dict[str, str]:
    return {"code": code, "field": field, "message": message, "source": source}


def _field_index(fields: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    return {str(field.get("entity_type")): field for field in fields}


def _profile(documents: list[dict[str, Any]]) -> dict[str, Any]:
    """Collect explicit declaration metadata without inventing any values."""
    profile: dict[str, Any] = {}
    for document in documents:
        candidate = document.get("declaration_profile")
        if isinstance(candidate, dict):
            profile.update({key: value for key, value in candidate.items() if value not in (None, "")})
    return profile


def _has_line_items(documents: list[dict[str, Any]]) -> bool:
    for document in documents:
        items = document.get("line_items") or document.get("items")
        if isinstance(items, list) and any(isinstance(item, dict) and item.get("description") for item in items):
            return True
    return False


def _positive_number(value: Any) -> bool:
    try:
        return float(value) > 0
    except (TypeError, ValueError):
        return False


def build_cusdec_readiness(documents: list[dict[str, Any]], fields: list[dict[str, Any]]) -> dict[str, Any]:
    """Return a UI-safe and API-safe submission readiness assessment."""
    blockers: list[dict[str, str]] = []
    resolved = _field_index(fields)

    if not documents:
        blockers.append(_issue("NO_DOCUMENTS", "dossier", "No processed source documents are available."))

    for entity_type, label in EXTRACTED_REQUIREMENTS.items():
        field = resolved.get(entity_type)
        if field is None or field.get("consensus_value") in (None, ""):
            blockers.append(_issue("MISSING_FIELD", entity_type, f"{label} is missing."))
            continue
        status = field.get("status")
        if status in {"conflict", "warning", "pending"}:
            blockers.append(_issue(
                "UNRESOLVED_FIELD", entity_type,
                f"{label} is {status}; review or corroborate it before export.",
            ))
        if entity_type in NUMERIC_FIELDS and not _positive_number(field.get("consensus_value")):
            blockers.append(_issue("INVALID_NUMBER", entity_type, f"{label} must be greater than zero."))

    currency = resolved.get("CURRENCY_CODE", {}).get("consensus_value")
    if currency not in (None, "") and not re.fullmatch(r"[A-Z]{3}", str(currency).upper()):
        blockers.append(_issue("INVALID_CURRENCY", "CURRENCY_CODE", "Currency must use a three-letter code."))

    incoterm = resolved.get("INCOTERM", {}).get("consensus_value")
    if incoterm not in (None, "") and str(incoterm).upper() not in KNOWN_INCOTERMS:
        blockers.append(_issue("INVALID_INCOTERM", "INCOTERM", "Incoterm must be a recognised three-letter code."))

    if not (resolved.get("AWB_NUMBER") or resolved.get("BL_NUMBER")):
        blockers.append(_issue("MISSING_TRANSPORT_DOCUMENT", "transport_document", "An AWB or bill of lading is required."))

    if not _has_line_items(documents):
        blockers.append(_issue(
            "MISSING_LINE_ITEMS", "line_items",
            "No extracted goods line items are available for commodity and valuation validation.",
        ))

    profile = _profile(documents)
    for key, label in PROFILE_REQUIREMENTS.items():
        if profile.get(key) in (None, ""):
            blockers.append(_issue("MISSING_DECLARATION_METADATA", key, f"{label} has not been supplied.", source="declaration profile"))

    # This project does not yet ship a Customs-approved XSD/message validator.
    # Treat that as a hard safety gate instead of presenting custom XML as an
    # ASYCUDA-importable declaration.
    blockers.append(_issue(
        "OFFICIAL_SCHEMA_VALIDATION_REQUIRED", "xml_schema",
        "The official ASYCUDA message schema has not been configured and validated for this export.",
        source="export configuration",
    ))

    return {
        "status": "ready" if not blockers else "blocked",
        "export_allowed": not blockers,
        "blocker_count": len(blockers),
        "blockers": blockers,
        "resolved_field_count": len(fields),
        "required_extracted_field_count": len(EXTRACTED_REQUIREMENTS),
        "profile": {key: profile.get(key) for key in PROFILE_REQUIREMENTS if profile.get(key) not in (None, "")},
        "notice": "Exports are blocked until source evidence, declaration metadata, and official ASYCUDA schema validation are complete.",
    }
