"""CUSDEC XML serializer for the user-confirmed ASYCUDA compatibility template.

The structure in this module follows the accepted XML sample supplied for this
deployment.  Values are taken only from resolved evidence, reviewer-entered
declaration metadata, and reviewer-entered source-referenced goods rows.
"""
from __future__ import annotations

from datetime import date
from typing import Any
from xml.etree import ElementTree as ET


TEMPLATE_VERSION = "user-confirmed-asycuda-template-v1"
XSI_NAMESPACE = "http://www.w3.org/2001/XMLSchema-instance"
ET.register_namespace("xsi", XSI_NAMESPACE)


def _text(parent: ET.Element, tag: str, value: Any) -> ET.Element:
    element = ET.SubElement(parent, tag)
    element.text = "" if value is None else str(value)
    return element


def _field_values(fields: list[dict[str, Any]]) -> dict[str, Any]:
    return {
        str(field.get("entity_type")): field.get("consensus_value")
        for field in fields
        if field.get("consensus_value") not in (None, "")
    }


def _country_code(value: Any) -> str | None:
    """Use only an existing ISO-style two-character source value."""
    candidate = str(value or "").strip().upper()
    return candidate if len(candidate) == 2 and candidate.isalpha() else None


def _add_if_present(parent: ET.Element, tag: str, value: Any) -> None:
    if value not in (None, ""):
        _text(parent, tag, value)


def generate_cusdec_xml(
    fields: list[dict[str, Any]],
    declaration_metadata: dict[str, Any],
    line_items: list[dict[str, Any]],
) -> str:
    """Serialize the resolved declaration into the confirmed ASYCUDA template."""
    values = _field_values(fields)
    metadata = declaration_metadata

    root = ET.Element("ASYCUDA", {"xmlns:xsi": XSI_NAMESPACE})

    identification = ET.SubElement(root, "Identification")
    office = ET.SubElement(identification, "Office_segment")
    _text(office, "Customs_clearance_office_code", metadata["customs_office_code"])
    declaration_type = ET.SubElement(identification, "Type")
    _text(declaration_type, "Type_of_declaration", metadata["declaration_type"])
    _text(declaration_type, "Declaration_gen_procedure_code", metadata["general_procedure_code"])
    registration = ET.SubElement(identification, "Registration")
    _text(registration, "Number", "")
    _text(registration, "Date", date.today().isoformat())

    traders = ET.SubElement(root, "Traders")
    exporter = ET.SubElement(traders, "Exporter")
    _text(exporter, "Exporter_code", metadata["exporter_code"])
    _text(exporter, "Exporter_name", values.get("SHIPPER_NAME", ""))
    _add_if_present(exporter, "Exporter_address", metadata.get("exporter_address"))
    consignee = ET.SubElement(traders, "Consignee")
    _text(consignee, "Consignee_code", metadata["consignee_code"])
    _text(consignee, "Consignee_name", values.get("CONSIGNEE_NAME", ""))
    _add_if_present(consignee, "Consignee_address", metadata.get("consignee_address"))
    financial_code = metadata.get("financial_code")
    if financial_code:
        financial = ET.SubElement(traders, "Financial")
        _text(financial, "Financial_code", financial_code)

    declarant = ET.SubElement(root, "Declarant")
    _text(declarant, "Declarant_code", metadata["declarant_code"])
    _text(declarant, "Declarant_name", metadata["declarant_name"])
    _add_if_present(declarant, "Declarant_representative", metadata.get("declarant_representative"))

    general = ET.SubElement(root, "General_information")
    countries = ET.SubElement(general, "Country")
    origin_code = _country_code(values.get("COUNTRY_OF_ORIGIN"))
    _add_if_present(countries, "Country_first_destination", metadata.get("country_first_destination", "LK"))
    _add_if_present(countries, "Trading_country", metadata.get("trading_country") or origin_code)
    _add_if_present(countries, "Country_of_export_code", metadata.get("country_of_export_code") or origin_code)
    value_details = ET.SubElement(general, "Value_details")
    _text(value_details, "Invoice_currency_code", values.get("CURRENCY_CODE", ""))
    _text(value_details, "Invoice_total_amount", values.get("TOTAL_AMOUNT", ""))
    cap = ET.SubElement(general, "Cap")
    _text(cap, "Terms_code", values.get("INCOTERM", ""))

    transport = ET.SubElement(root, "Transport")
    means = ET.SubElement(transport, "Means_of_transport")
    departure = ET.SubElement(means, "Departure_arrival_information")
    _add_if_present(departure, "Identity", metadata.get("transport_identity"))
    _add_if_present(departure, "Nationality", metadata.get("transport_nationality"))
    border = ET.SubElement(means, "Border_information")
    _text(border, "Mode", metadata["transport_mode"])
    _text(transport, "Container_flag", metadata["container_flag"])
    _add_if_present(transport, "Delivery_place", values.get("PORT_OF_DISCHARGE"))
    _add_if_present(transport, "Location_of_goods", metadata.get("location_of_goods"))

    financial = ET.SubElement(root, "Financial")
    if metadata.get("financial_transaction_code"):
        transaction = ET.SubElement(financial, "Financial_transaction")
        _text(transaction, "Code", metadata["financial_transaction_code"])
    if financial_code:
        bank = ET.SubElement(financial, "Bank")
        _text(bank, "Code", financial_code)
        _add_if_present(bank, "Name", metadata.get("financial_name"))
        _add_if_present(bank, "Branch", metadata.get("financial_branch"))
    _add_if_present(financial, "Terms_of_payment", metadata.get("terms_of_payment"))

    hs_code = values.get("HS_CODE", "")
    package_count = values.get("PACKAGE_COUNT", "")
    gross_weight = values.get("GROSS_WEIGHT", "")
    currency = values.get("CURRENCY_CODE", "")
    exchange_rate = metadata["currency_rate"]
    for position, item in enumerate(line_items, start=1):
        declaration_item = ET.SubElement(root, "Item")
        _text(declaration_item, "Item_Number", item.get("row_index", position))
        tariff = ET.SubElement(declaration_item, "Tariff")
        _text(tariff, "Commodity_code", hs_code)
        _add_if_present(tariff, "National_customs_codes", metadata.get("national_customs_codes"))
        goods = ET.SubElement(declaration_item, "Goods_description")
        _text(goods, "Commercial_description", item["description"])
        _add_if_present(goods, "Country_of_origin_code", origin_code)
        packages = ET.SubElement(declaration_item, "Packages")
        _text(packages, "Number_of_packages", package_count)
        _add_if_present(packages, "Type_of_packages_code", metadata.get("package_type_code"))
        _add_if_present(packages, "Marks_and_numbers", metadata.get("marks_and_numbers"))
        weight = ET.SubElement(declaration_item, "Weight")
        _text(weight, "Gross_mass", gross_weight)
        _add_if_present(weight, "Net_mass", values.get("NET_WEIGHT"))
        valuation = ET.SubElement(declaration_item, "Valuation_item")
        _text(valuation, "Item_Invoice_amount", item["total_price"])
        _text(valuation, "Currency_code", currency)
        _text(valuation, "Rate_of_exchange", exchange_rate)
        try:
            statistical_value = round(float(item["total_price"]) * float(exchange_rate), 2)
        except (TypeError, ValueError):
            statistical_value = ""
        _text(valuation, "Statistical_value", statistical_value)

    return ET.tostring(root, encoding="unicode", xml_declaration=True)
