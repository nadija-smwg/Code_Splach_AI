from xml.etree import ElementTree as ET

from reasoning.cusdec_xml import TEMPLATE_VERSION, generate_cusdec_xml


def test_generate_cusdec_xml_uses_the_confirmed_template_structure():
    fields = [
        {"entity_type": "CONSIGNEE_NAME", "consensus_value": "Lanka Textiles"},
        {"entity_type": "SHIPPER_NAME", "consensus_value": "Shanghai Exporter"},
        {"entity_type": "CURRENCY_CODE", "consensus_value": "USD"},
        {"entity_type": "TOTAL_AMOUNT", "consensus_value": 125.0},
        {"entity_type": "INCOTERM", "consensus_value": "CIF"},
        {"entity_type": "COUNTRY_OF_ORIGIN", "consensus_value": "CN"},
        {"entity_type": "PORT_OF_DISCHARGE", "consensus_value": "Colombo Port"},
        {"entity_type": "HS_CODE", "consensus_value": "61091000"},
        {"entity_type": "PACKAGE_COUNT", "consensus_value": 2},
        {"entity_type": "GROSS_WEIGHT", "consensus_value": 30},
    ]
    metadata = {
        "customs_office_code": "CBCOL", "declaration_type": "IM",
        "general_procedure_code": "4", "exporter_code": "EXP01",
        "consignee_code": "TIN01", "declarant_code": "CHA01",
        "declarant_name": "Clearance Agent", "transport_mode": "1",
        "container_flag": "true", "currency_rate": "305.00",
    }
    line_items = [{"row_index": 1, "description": "Cotton fabric", "total_price": 125.0}]

    root = ET.fromstring(generate_cusdec_xml(fields, metadata, line_items))

    assert root.tag == "ASYCUDA"
    assert TEMPLATE_VERSION == "user-confirmed-asycuda-template-v1"
    assert root.findtext("Identification/Office_segment/Customs_clearance_office_code") == "CBCOL"
    assert root.findtext("Traders/Consignee/Consignee_code") == "TIN01"
    assert root.findtext("Item/Tariff/Commodity_code") == "61091000"
    assert root.findtext("Item/Valuation_item/Statistical_value") == "38125.0"
