# backend/reasoning/asycuda_export.py
"""
Dynamic ASYCUDA CUSDEC XML Generator.

Builds a standards-compliant CUSDEC XML from the knowledge graph's
verified entity nodes, replacing the hardcoded static string in routes.py.

Usage:
    from backend.reasoning.asycuda_export import generate_cusdec_xml
    xml_str = generate_cusdec_xml(graph, shipment_id)
"""

import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from typing import Optional
import networkx as nx


def _get_entity_value(graph: nx.Graph, entity_type: str, default: str = "") -> str:
    """Extract the first matching entity value from the knowledge graph."""
    for node_id, data in graph.nodes(data=True):
        if data.get("node_type") in {"canonical_field", "entity"} and data.get("entity_type") == entity_type:
            val = data.get("value", default)
            return str(val) if val is not None else default
    return default


def generate_cusdec_xml(graph: nx.Graph, shipment_id: str) -> str:
    """
    Generate a CUSDEC XML string from knowledge graph entity nodes.
    Falls back to default values for missing entities.
    """
    # Extract entities from graph
    consignee    = _get_entity_value(graph, "CONSIGNEE_NAME", "Unknown Consignee")
    gross_weight = _get_entity_value(graph, "GROSS_WEIGHT", "0.00")
    net_weight   = _get_entity_value(graph, "NET_WEIGHT", "0.00")
    pkg_count    = _get_entity_value(graph, "PACKAGE_COUNT", "0")
    awb_number   = _get_entity_value(graph, "AWB_NUMBER", "N/A")
    bl_number    = _get_entity_value(graph, "BL_NUMBER", "")
    incoterm     = _get_entity_value(graph, "INCOTERM", "FOB")
    total_amount = _get_entity_value(graph, "TOTAL_AMOUNT", "0.00")
    currency     = _get_entity_value(graph, "CURRENCY_CODE", "USD")
    invoice_num  = _get_entity_value(graph, "INVOICE_NUMBER", "N/A")

    # Strip numeric part from weight strings like "450.00 KG" or "448.5"
    def extract_num(s: str) -> str:
        parts = s.split()
        return parts[0] if parts else s

    timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

    # ── Build XML tree ────────────────────────────────────────────────────
    root = ET.Element("CUSDEC", attrib={
        "xmlns": "urn:asycuda:declaration:v4",
        "version": "4.2",
        "shipment_id": shipment_id,
        "generated": timestamp,
    })

    # Declaration Header
    header = ET.SubElement(root, "DeclarationHeader")
    ET.SubElement(header, "DeclarationType").text = "IM"
    ET.SubElement(header, "DeclarationOffice").text = "LKCMB01"
    ET.SubElement(header, "ReferenceNumber").text = shipment_id[:12].upper()
    ET.SubElement(header, "DeclarationDate").text = timestamp[:10]
    ET.SubElement(header, "InvoiceNumber").text = invoice_num

    # Consignee
    consignee_el = ET.SubElement(root, "ConsigneeInfo")
    ET.SubElement(consignee_el, "Name").text = consignee
    ET.SubElement(consignee_el, "Address").text = "Sri Lanka"

    # Transport
    transport = ET.SubElement(root, "TransportInfo")
    if awb_number and awb_number != "N/A":
        ET.SubElement(transport, "AWBNumber").text = awb_number
    if bl_number:
        ET.SubElement(transport, "BLNumber").text = bl_number
    ET.SubElement(transport, "GrossWeight", attrib={"unit": "KG"}).text = extract_num(gross_weight)
    ET.SubElement(transport, "NetWeight", attrib={"unit": "KG"}).text = extract_num(net_weight)
    ET.SubElement(transport, "PackageCount").text = extract_num(pkg_count)

    # Valuation
    valuation = ET.SubElement(root, "Valuation")
    ET.SubElement(valuation, "Incoterm").text = incoterm
    ET.SubElement(valuation, "TotalInvoiceValue", attrib={"currency": currency}).text = extract_num(total_amount)

    # Serialize to string with XML declaration
    ET.indent(root, space="  ")
    xml_bytes = ET.tostring(root, encoding="unicode", xml_declaration=False)
    return f'<?xml version="1.0" encoding="UTF-8"?>\n{xml_bytes}'


def generate_demo_cusdec_xml(shipment_id: str) -> str:
    """
    Fallback: generate a hardcoded-but-realistic CUSDEC XML for demo
    when no graph is available (e.g. the route is called without prior processing).
    """
    timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    return f"""<?xml version="1.0" encoding="UTF-8"?>
<CUSDEC xmlns="urn:asycuda:declaration:v4" version="4.2" shipment_id="{shipment_id}" generated="{timestamp}">
  <DeclarationHeader>
    <DeclarationType>IM</DeclarationType>
    <DeclarationOffice>LKCMB01</DeclarationOffice>
    <ReferenceNumber>{shipment_id[:12].upper()}</ReferenceNumber>
    <DeclarationDate>{timestamp[:10]}</DeclarationDate>
    <InvoiceNumber>INV-2024-1023</InvoiceNumber>
  </DeclarationHeader>
  <ConsigneeInfo>
    <Name>ABC Textiles Ltd</Name>
    <Address>42 Galle Road, Colombo 03, Sri Lanka</Address>
  </ConsigneeInfo>
  <TransportInfo>
    <AWBNumber>631-12345678</AWBNumber>
    <GrossWeight unit="KG">450.00</GrossWeight>
    <NetWeight unit="KG">420.00</NetWeight>
    <PackageCount>25</PackageCount>
  </TransportInfo>
  <Valuation>
    <Incoterm>FOB</Incoterm>
    <TotalInvoiceValue currency="USD">45230.00</TotalInvoiceValue>
  </Valuation>
</CUSDEC>"""
