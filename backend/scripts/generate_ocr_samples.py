"""Build four matching, clearly labelled synthetic sea-shipment PDFs.

Run with a Python environment containing reportlab:
    python backend/scripts/generate_ocr_samples.py
"""
import json
from pathlib import Path

from reportlab.lib.pagesizes import A4
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen import canvas

ROOT = Path(__file__).resolve().parents[2]
OUTPUT = ROOT / "output" / "pdf" / "ocr_samples"
WIDTH, HEIGHT = A4
MARGIN = 40
FONT_SIZE = 12.5

# Embed an ordinary sans-serif font; portable fallback uses PDF Helvetica.
ARIAL = Path("C:/Windows/Fonts/arial.ttf")
if ARIAL.exists():
    pdfmetrics.registerFont(TTFont("SampleSans", str(ARIAL)))
    pdfmetrics.registerFont(TTFont("SampleSansBold", str(ARIAL.with_name("arialbd.ttf"))))
    REGULAR, BOLD = "SampleSans", "SampleSansBold"
else:
    REGULAR, BOLD = "Helvetica", "Helvetica-Bold"

SHIPPER = "Meridian Textiles Ltd"
CONSIGNEE = "Lanka Apparel Ltd"
GROSS, NET, PACKAGES = "480.00 KG", "440.00 KG", "20 Cartons"
CONTAINER = "MSCU1234566"


class Document:
    def __init__(self, filename, title, document_type):
        self.path = OUTPUT / filename
        self.pdf = canvas.Canvas(str(self.path), pagesize=A4, pageCompression=1)
        self.pdf.setTitle(title + " - Synthetic OCR Sample")
        self.pdf.setAuthor("ClearanceX")
        self.pdf.setSubject("Fictional test document. Not valid for shipment or customs use.")
        self.pdf.setFillColorRGB(0, 0, 0)
        self.lines = []
        self.fields = {}
        self.document_type = document_type
        self.y = HEIGHT - MARGIN
        self.line("CLEARANCEX SAMPLE DOCUMENT", size=12, bold=True)
        self.y -= 7
        self.line(title, size=21, bold=True, leading=31)
        self.line("Synthetic test data - not valid for commercial use", size=11, leading=28)

    def line(self, text, size=FONT_SIZE, bold=False, leading=21):
        font = BOLD if bold else REGULAR
        text_width = pdfmetrics.stringWidth(text, font, size)
        if text_width > WIDTH - 2 * MARGIN:
            raise ValueError(f"Text too wide in {self.path.name}: {text}")
        if self.y < 70:
            raise ValueError(f"Page overflow in {self.path.name}")
        self.pdf.setFont(font, size)
        self.pdf.drawString(MARGIN, self.y, text)
        self.lines.append(text)
        self.y -= leading

    def field(self, label, value, entity_type=None):
        self.line(f"{label}: {value}")
        if entity_type:
            self.fields[entity_type] = {"label": label, "value": value}

    def section(self, title):
        self.y -= 8
        self.line(title, size=13, bold=True, leading=24)

    def table(self, headers, rows, widths):
        if sum(widths) > WIDTH - 2 * MARGIN:
            raise ValueError("Table exceeds the available page width")
        for index, row in enumerate([headers] + rows):
            x = MARGIN
            self.pdf.setFont(BOLD if index == 0 else REGULAR, 12)
            for cell, width in zip(row, widths):
                if pdfmetrics.stringWidth(cell, BOLD if index == 0 else REGULAR, 12) > width - 12:
                    raise ValueError(f"Table cell too wide: {cell}")
                self.pdf.drawString(x + 4, self.y, cell)
                x += width
            self.lines.append(" ".join(row))
            # Horizontal rules only, well clear of character baselines.
            self.pdf.setStrokeColorRGB(0.7, 0.7, 0.7)
            self.pdf.setLineWidth(0.4)
            self.pdf.line(MARGIN, self.y - 9, MARGIN + sum(widths), self.y - 9)
            self.y -= 30

    def save(self):
        footer = "Fictional OCR sample | Page 1 of 1"
        self.pdf.setFont(REGULAR, 11)
        self.pdf.drawString(MARGIN, 38, footer)
        self.lines.append(footer)
        self.pdf.save()
        return {"file": self.path.name, "document_type": self.document_type,
                "pages": 1, "expected_fields": self.fields, "expected_lines": self.lines}


def invoice():
    doc = Document("commercial_invoice.pdf", "COMMERCIAL INVOICE", "commercial_invoice")
    for label, value, key in [
        ("Invoice Number", "INV-2026-0930", "INVOICE_NUMBER"),
        ("Invoice Date", "30 September 2026", "INVOICE_DATE"),
        ("Shipper", SHIPPER, "SHIPPER_NAME"),
        ("Consignee", CONSIGNEE, "CONSIGNEE_NAME"),
        ("Consignee Address", "18 Lake Road, Colombo, Sri Lanka", "CONSIGNEE_ADDRESS"),
        ("Country of Origin", "India", "COUNTRY_OF_ORIGIN"),
        ("Incoterm", "CIF Colombo", "INCOTERM"),
        ("Payment Terms", "30 Days from Invoice Date", "PAYMENT_TERMS"),
        ("Currency", "USD", "CURRENCY_CODE"),
        ("Port of Loading", "Chennai", "PORT_OF_LOADING"),
        ("Port of Discharge", "Colombo", "PORT_OF_DISCHARGE"),
        ("Vessel Name", "MV MERIDIAN", "VESSEL_NAME"),
        ("HS Code", "520812", "HS_CODE"),
        ("Gross Weight", GROSS, "GROSS_WEIGHT"),
        ("Net Weight", NET, "NET_WEIGHT"),
        ("Package Count", PACKAGES, "PACKAGE_COUNT"),
    ]:
        doc.field(label, value, key)
    doc.section("DESCRIPTION OF GOODS")
    doc.table(["Description", "Qty (M)", "Unit Price", "Amount (USD)"], [
        ["Cotton Fabric A", "1200", "4.75", "5700.00"],
        ["Cotton Fabric B", "800", "4.75", "3800.00"],
    ], [205, 80, 105, 125])
    doc.field("Goods Subtotal", "USD 9500.00")
    doc.field("Freight Amount", "USD 400.00", "FREIGHT_AMOUNT")
    doc.field("Insurance Amount", "USD 100.00", "INSURANCE_AMOUNT")
    doc.field("Total Amount", "USD 10000.00", "TOTAL_AMOUNT")
    return doc.save()


def packing_list():
    doc = Document("packing_list.pdf", "PACKING LIST", "packing_list")
    for label, value, key in [
        ("Packing Reference", "PL-2026-0930", None),
        ("Shipment Reference", "CX-2026-0930", None),
        ("Shipper", SHIPPER, "SHIPPER_NAME"),
        ("Consignee", CONSIGNEE, "CONSIGNEE_NAME"),
        ("Gross Weight", GROSS, "GROSS_WEIGHT"),
        ("Net Weight", NET, "NET_WEIGHT"),
        ("Tare Weight", "40.00 KG", "TARE_WEIGHT"),
        ("Package Count", PACKAGES, "PACKAGE_COUNT"),
        ("Volume", "2.400 CBM", "VOLUME"),
        ("Shipping Marks", "CX-LKA-2026", "SHIPPING_MARKS"),
        ("Dimensions per Carton", "60 x 50 x 40 CM", None),
    ]:
        doc.field(label, value, key)
    doc.section("CARTON CONTENTS")
    doc.table(["Goods", "Cartons", "Gross KG", "Net KG", "CBM"], [
        ["Cotton Fabric A", "12", "288.00", "264.00", "1.440"],
        ["Cotton Fabric B", "8", "192.00", "176.00", "0.960"],
        ["TOTAL", "20", "480.00", "440.00", "2.400"],
    ], [175, 75, 95, 95, 75])
    doc.y -= 16
    doc.line("Packing: sealed export cartons")
    return doc.save()


def bill_of_lading():
    doc = Document("bill_of_lading.pdf", "BILL OF LADING", "bl")
    for label, value, key in [
        ("B/L Number", "BL-2026-0930", "BL_NUMBER"),
        ("Shipment Reference", "CX-2026-0930", None),
        ("Issue Date", "30 September 2026", None),
        ("Shipper", SHIPPER, "SHIPPER_NAME"),
        ("Consignee", CONSIGNEE, "CONSIGNEE_NAME"),
        ("Notify Party", "Lanka Apparel Ltd", None),
        ("Vessel Name", "MV MERIDIAN", "VESSEL_NAME"),
        ("Voyage Number", "0930E", None),
        ("Port of Loading", "Chennai", "PORT_OF_LOADING"),
        ("Port of Discharge", "Colombo", "PORT_OF_DISCHARGE"),
        ("Container Number", CONTAINER, "CONTAINER_NUMBER"),
        ("Seal No", "SEAL260930", None),
        ("Gross Weight", GROSS, "GROSS_WEIGHT"),
        ("Package Count", PACKAGES, "PACKAGE_COUNT"),
    ]:
        doc.field(label, value, key)
    doc.section("CARGO DETAILS")
    doc.field("Goods", "Cotton Fabric A and Cotton Fabric B")
    doc.field("Shipping Marks", "CX-LKA-2026")
    doc.field("Freight Terms", "Freight Prepaid")
    return doc.save()


def delivery_order():
    doc = Document("delivery_order.pdf", "DELIVERY ORDER", "delivery_order")
    for label, value, key in [
        ("DO Number", "DO-2026-0930", "DO_NUMBER"),
        ("Shipment Reference", "CX-2026-0930", None),
        ("Consignee", CONSIGNEE, "CONSIGNEE_NAME"),
        ("Container Number", CONTAINER, "CONTAINER_NUMBER"),
        ("Port of Discharge", "Colombo", "PORT_OF_DISCHARGE"),
        ("Gross Weight", GROSS, "GROSS_WEIGHT"),
        ("Package Count", PACKAGES, "PACKAGE_COUNT"),
        ("Release Date", "05 October 2026", None),
        ("Cargo Release", "Authorized for named consignee", None),
        ("Collect Cargo", "Colombo cargo terminal", None),
    ]:
        doc.field(label, value, key)
    doc.section("RELEASE INSTRUCTIONS")
    doc.line("Deliver the listed goods to Lanka Apparel Ltd.")
    doc.line("Goods: Cotton Fabric A and Cotton Fabric B")
    return doc.save()


def main():
    OUTPUT.mkdir(parents=True, exist_ok=True)
    documents = [invoice(), packing_list(), bill_of_lading(), delivery_order()]
    manifest = {"synthetic": True, "shipment_reference": "CX-2026-0930",
                "note": "Ground truth, not OCR results. No accuracy is assumed.",
                "documents": documents}
    (OUTPUT / "ground_truth.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    print(f"Created {len(documents)} PDFs in {OUTPUT}")


if __name__ == "__main__":
    main()
