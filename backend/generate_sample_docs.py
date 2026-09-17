"""
generate_sample_docs.py
Generates 3 realistic Sri Lankan trade documents as PDFs for OCR testing:
  1. Commercial Invoice
  2. Packing List
  3. Air Waybill (AWB)

Run with:
    python generate_sample_docs.py
"""

import os
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.units import mm
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import (
    SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, HRFlowable
)
from reportlab.lib.enums import TA_CENTER, TA_RIGHT, TA_LEFT

OUTPUT_DIR = "sample_docs"
os.makedirs(OUTPUT_DIR, exist_ok=True)

W, H = A4
styles = getSampleStyleSheet()

# ─── Shared Style Helpers ──────────────────────────────────────────────────────

def heading(text, size=14, bold=True, align=TA_CENTER):
    return Paragraph(text, ParagraphStyle(
        "h", fontName="Helvetica-Bold" if bold else "Helvetica",
        fontSize=size, alignment=align, spaceAfter=2
    ))

def body(text, size=9, align=TA_LEFT):
    return Paragraph(text, ParagraphStyle(
        "b", fontName="Helvetica", fontSize=size, alignment=align, leading=13
    ))

def label_val(label, val, size=9):
    return Paragraph(f"<b>{label}:</b> {val}", ParagraphStyle(
        "lv", fontName="Helvetica", fontSize=size, leading=13
    ))

HEADER_BG  = colors.HexColor("#1a3c5e")
ROW_ALT    = colors.HexColor("#eaf0f7")
ROW_WHITE  = colors.white
BORDER     = colors.HexColor("#bccad6")

def base_table_style():
    return TableStyle([
        ("BACKGROUND",    (0,0), (-1,0), HEADER_BG),
        ("TEXTCOLOR",     (0,0), (-1,0), colors.white),
        ("FONTNAME",      (0,0), (-1,0), "Helvetica-Bold"),
        ("FONTSIZE",      (0,0), (-1,0), 8),
        ("ROWBACKGROUNDS",(0,1), (-1,-1), [ROW_WHITE, ROW_ALT]),
        ("FONTSIZE",      (0,1), (-1,-1), 8),
        ("FONTNAME",      (0,1), (-1,-1), "Helvetica"),
        ("GRID",          (0,0), (-1,-1), 0.4, BORDER),
        ("VALIGN",        (0,0), (-1,-1), "MIDDLE"),
        ("TOPPADDING",    (0,0), (-1,-1), 4),
        ("BOTTOMPADDING", (0,0), (-1,-1), 4),
        ("LEFTPADDING",   (0,0), (-1,-1), 5),
    ])

# ─── 1. Commercial Invoice ─────────────────────────────────────────────────────

def generate_commercial_invoice():
    path = os.path.join(OUTPUT_DIR, "commercial_invoice.pdf")
    doc = SimpleDocTemplate(path, pagesize=A4,
                            leftMargin=18*mm, rightMargin=18*mm,
                            topMargin=15*mm, bottomMargin=15*mm)
    story = []

    story.append(heading("COMMERCIAL INVOICE", size=16))
    story.append(HRFlowable(width="100%", thickness=2, color=HEADER_BG))
    story.append(Spacer(1, 6))

    # Parties side-by-side
    party_data = [[
        Paragraph("<b>EXPORTER / SHIPPER</b>", ParagraphStyle("ph", fontName="Helvetica-Bold", fontSize=9)),
        Paragraph("<b>CONSIGNEE</b>", ParagraphStyle("ph", fontName="Helvetica-Bold", fontSize=9))
    ],[
        body("Textured Jersey Lanka PLC\n"
             "No. 200, Nawala Road, Narahenpita\n"
             "Colombo 05, Sri Lanka\n"
             "VAT Reg: 114-062-785\n"
             "Tel: +94 11 2368 500"),
        body("Burlington Industries Inc.\n"
             "3330 West Friendly Avenue\n"
             "Greensboro, NC 27410, USA\n"
             "Tel: +1 (336) 379-2000")
    ]]
    party_tbl = Table(party_data, colWidths=[85*mm, 85*mm])
    party_tbl.setStyle(TableStyle([
        ("BOX",        (0,0), (-1,-1), 0.5, BORDER),
        ("INNERGRID",  (0,0), (-1,-1), 0.5, BORDER),
        ("BACKGROUND", (0,0), (-1,0),  HEADER_BG),
        ("TEXTCOLOR",  (0,0), (-1,0),  colors.white),
        ("TOPPADDING", (0,0), (-1,-1), 5),
        ("BOTTOMPADDING", (0,0), (-1,-1), 5),
        ("LEFTPADDING",   (0,0), (-1,-1), 6),
    ]))
    story.append(party_tbl)
    story.append(Spacer(1, 8))

    # Reference numbers
    ref_data = [
        ["Invoice No:", "INV-2026-00451", "Invoice Date:", "15 September 2026"],
        ["P.O. Number:", "BUR-PO-2026-8874", "L/C Number:", "LC-BOFAUSA-2026-0091"],
        ["Port of Loading:", "Colombo (CMB), Sri Lanka", "Port of Discharge:", "Norfolk, VA, USA"],
        ["Country of Origin:", "Sri Lanka", "Incoterms:", "FOB Colombo"],
        ["Payment Terms:", "60 Days from B/L Date", "Currency:", "USD"],
    ]
    ref_tbl = Table(ref_data, colWidths=[38*mm, 55*mm, 38*mm, 42*mm])
    ref_tbl.setStyle(TableStyle([
        ("FONTNAME",      (0,0), (0,-1), "Helvetica-Bold"),
        ("FONTNAME",      (2,0), (2,-1), "Helvetica-Bold"),
        ("FONTSIZE",      (0,0), (-1,-1), 8),
        ("BOX",           (0,0), (-1,-1), 0.5, BORDER),
        ("INNERGRID",     (0,0), (-1,-1), 0.3, BORDER),
        ("ROWBACKGROUNDS",(0,0), (-1,-1), [ROW_WHITE, ROW_ALT]),
        ("TOPPADDING",    (0,0), (-1,-1), 4),
        ("BOTTOMPADDING", (0,0), (-1,-1), 4),
        ("LEFTPADDING",   (0,0), (-1,-1), 5),
    ]))
    story.append(ref_tbl)
    story.append(Spacer(1, 10))

    story.append(heading("DESCRIPTION OF GOODS", size=10, align=TA_LEFT))
    story.append(Spacer(1, 3))

    goods_header = ["HS Code", "Description", "Qty\n(pcs)", "Unit Price\n(USD)", "Amount\n(USD)"]
    goods_rows = [
        ["6109.10.10", "Men's Round Neck T-Shirt, 100% Cotton,\nSingle Jersey, 160GSM, Assorted Colours", "3,600", "4.25", "15,300.00"],
        ["6109.10.20", "Women's V-Neck T-Shirt, 95% Cotton 5%\nElastane, 180GSM, Assorted Colours", "2,400", "5.10", "12,240.00"],
        ["6110.20.10", "Men's Crew Neck Sweatshirt, 80% Cotton\n20% Polyester, 320GSM, Navy/Grey", "1,200", "8.75", "10,500.00"],
        ["6104.62.00", "Women's Yoga Leggings, 88% Polyester\n12% Elastane, 200GSM, Black", "1,800", "6.50", "11,700.00"],
    ]
    goods_data = [goods_header] + goods_rows + [
        ["", "TOTAL", "9,000", "", "49,740.00"],
    ]
    col_w = [24*mm, 74*mm, 16*mm, 22*mm, 22*mm]
    goods_tbl = Table(goods_data, colWidths=col_w, repeatRows=1)
    ts = base_table_style()
    ts.add("ALIGN", (2,0), (-1,-1), "RIGHT")
    ts.add("FONTNAME", (0,-1), (-1,-1), "Helvetica-Bold")
    ts.add("BACKGROUND", (0,-1), (-1,-1), ROW_ALT)
    ts.add("SPAN", (0,-1), (1,-1))
    goods_tbl.setStyle(ts)
    story.append(goods_tbl)
    story.append(Spacer(1, 10))

    # Totals + Shipping summary
    totals_data = [
        ["FOB Value (USD):", "49,740.00"],
        ["Freight Charges:", "COLLECT"],
        ["Insurance:", "COLLECT"],
        ["TOTAL INVOICE VALUE:", "USD 49,740.00"],
    ]
    tot_tbl = Table(totals_data, colWidths=[120*mm, 50*mm])
    tot_tbl.setStyle(TableStyle([
        ("FONTSIZE",      (0,0), (-1,-1), 9),
        ("ALIGN",         (1,0), (1,-1),  "RIGHT"),
        ("FONTNAME",      (0,-1),(-1,-1), "Helvetica-Bold"),
        ("FONTSIZE",      (0,-1),(-1,-1), 10),
        ("TOPPADDING",    (0,0), (-1,-1), 4),
        ("BOTTOMPADDING", (0,0), (-1,-1), 4),
        ("LINEABOVE",     (0,-1), (-1,-1), 1.5, HEADER_BG),
        ("BOX",           (0,0), (-1,-1), 0.5, BORDER),
    ]))
    story.append(tot_tbl)
    story.append(Spacer(1, 10))

    # Shipping marks + declaration
    marks = [
        [heading("SHIPPING MARKS", size=9, align=TA_LEFT), heading("DECLARATION", size=9, align=TA_LEFT)],
        [
            body("TJL / BUR-8874\nCOLOMBO\nMADE IN SRI LANKA\nCTNS: 1-240"),
            body("We hereby certify that the goods described herein are of Sri Lanka origin "
                 "and that the particulars given above are true and correct to the best of our "
                 "knowledge and belief.\n\nFor and on behalf of: Textured Jersey Lanka PLC\n\n\n"
                 "_____________________________\nAuthorised Signatory & Company Seal")
        ]
    ]
    marks_tbl = Table(marks, colWidths=[60*mm, 110*mm])
    marks_tbl.setStyle(TableStyle([
        ("BOX",       (0,0), (-1,-1), 0.5, BORDER),
        ("INNERGRID", (0,0), (-1,-1), 0.5, BORDER),
        ("BACKGROUND",(0,0), (-1,0),  ROW_ALT),
        ("TOPPADDING",(0,0), (-1,-1), 5),
        ("LEFTPADDING",(0,0),(-1,-1), 6),
    ]))
    story.append(marks_tbl)

    doc.build(story)
    print(f"  [OK] Created: {path}")


# ─── 2. Packing List ──────────────────────────────────────────────────────────

def generate_packing_list():
    path = os.path.join(OUTPUT_DIR, "packing_list.pdf")
    doc = SimpleDocTemplate(path, pagesize=A4,
                            leftMargin=18*mm, rightMargin=18*mm,
                            topMargin=15*mm, bottomMargin=15*mm)
    story = []

    story.append(heading("PACKING LIST", size=16))
    story.append(HRFlowable(width="100%", thickness=2, color=HEADER_BG))
    story.append(Spacer(1, 6))

    # Header info
    hdr_data = [
        ["Exporter:", "Textured Jersey Lanka PLC, Colombo 05, Sri Lanka"],
        ["Consignee:", "Burlington Industries Inc., Greensboro, NC 27410, USA"],
        ["Invoice No:", "INV-2026-00451"],
        ["Packing List No:", "PL-2026-00451"],
        ["Date:", "15 September 2026"],
        ["Port of Loading:", "Colombo (CMB), Sri Lanka"],
        ["Port of Discharge:", "Norfolk, VA, USA"],
        ["Vessel / Flight:", "MV Colombo Express / Voyage 0041W"],
    ]
    hdr_tbl = Table(hdr_data, colWidths=[40*mm, 132*mm])
    hdr_tbl.setStyle(TableStyle([
        ("FONTNAME",      (0,0), (0,-1), "Helvetica-Bold"),
        ("FONTSIZE",      (0,0), (-1,-1), 8),
        ("ROWBACKGROUNDS",(0,0), (-1,-1), [ROW_WHITE, ROW_ALT]),
        ("BOX",           (0,0), (-1,-1), 0.5, BORDER),
        ("INNERGRID",     (0,0), (-1,-1), 0.3, BORDER),
        ("TOPPADDING",    (0,0), (-1,-1), 4),
        ("BOTTOMPADDING", (0,0), (-1,-1), 4),
        ("LEFTPADDING",   (0,0), (-1,-1), 5),
    ]))
    story.append(hdr_tbl)
    story.append(Spacer(1, 10))

    story.append(heading("PACKING DETAILS", size=10, align=TA_LEFT))
    story.append(Spacer(1, 3))

    pk_header = ["Ctn\nNos.", "Style / Description", "Colour", "Size\nBreakdown", "Qty\n(pcs)", "Qty\n(ctn)", "Net Wt\n(kg)", "Gross Wt\n(kg)", "CBM"]
    pk_rows = [
        ["1–60",   "Men's Round Neck T-Shirt\n6109.10.10", "Assorted", "S/M/L/XL", "3,600", "60", "252.00", "270.00", "3.420"],
        ["61–100", "Women's V-Neck T-Shirt\n6109.10.20", "Assorted", "XS/S/M/L", "2,400", "40", "192.00", "208.00", "2.640"],
        ["101–130","Men's Crew Neck Sweatshirt\n6110.20.10", "Navy/Grey", "M/L/XL",  "1,200", "30", "120.00", "132.00", "2.280"],
        ["131–240","Women's Yoga Leggings\n6104.62.00", "Black", "XS/S/M/L/XL","1,800", "110","171.00", "187.00", "6.160"],
    ]
    totals_row = ["", "TOTAL", "", "", "9,000", "240", "735.00", "797.00", "14.500"]
    pk_data = [pk_header] + pk_rows + [totals_row]

    col_w = [14*mm, 52*mm, 18*mm, 20*mm, 14*mm, 12*mm, 15*mm, 16*mm, 13*mm]
    pk_tbl = Table(pk_data, colWidths=col_w, repeatRows=1)
    ts = base_table_style()
    ts.add("FONTNAME", (0,-1), (-1,-1), "Helvetica-Bold")
    ts.add("BACKGROUND",(0,-1),(-1,-1), ROW_ALT)
    ts.add("ALIGN", (4,0), (-1,-1), "RIGHT")
    pk_tbl.setStyle(ts)
    story.append(pk_tbl)
    story.append(Spacer(1, 10))

    # Summary box
    summary_data = [
        ["SUMMARY", ""],
        ["Total Cartons:",          "240 Ctns"],
        ["Total Pieces:",           "9,000 pcs"],
        ["Total Net Weight:",       "735.00 KG"],
        ["Total Gross Weight:",     "797.00 KG"],
        ["Total Volume (CBM):",     "14.500 CBM"],
        ["Container Type:",         "1 x 20' FCL"],
        ["Container No.:",          "TCKU3456789"],
        ["Seal No.:",               "SL-998874"],
    ]
    sum_tbl = Table(summary_data, colWidths=[80*mm, 90*mm])
    sum_tbl.setStyle(TableStyle([
        ("BACKGROUND",  (0,0), (-1,0), HEADER_BG),
        ("TEXTCOLOR",   (0,0), (-1,0), colors.white),
        ("FONTNAME",    (0,0), (-1,0), "Helvetica-Bold"),
        ("SPAN",        (0,0), (-1,0)),
        ("ALIGN",       (0,0), (-1,0), "CENTER"),
        ("FONTNAME",    (0,1), (0,-1), "Helvetica-Bold"),
        ("FONTSIZE",    (0,0), (-1,-1), 9),
        ("ROWBACKGROUNDS",(0,1),(-1,-1),[ROW_WHITE, ROW_ALT]),
        ("BOX",         (0,0), (-1,-1), 0.5, BORDER),
        ("INNERGRID",   (0,0), (-1,-1), 0.3, BORDER),
        ("TOPPADDING",  (0,0), (-1,-1), 5),
        ("BOTTOMPADDING",(0,0),(-1,-1), 5),
        ("LEFTPADDING", (0,0), (-1,-1), 6),
    ]))
    story.append(sum_tbl)
    story.append(Spacer(1, 10))
    story.append(body("Prepared by: Textured Jersey Lanka PLC\n\n\n"
                      "_____________________________\n"
                      "Authorised Signatory & Date: _______________"))

    doc.build(story)
    print(f"  [OK] Created: {path}")


# ─── 3. Air Waybill (AWB) ─────────────────────────────────────────────────────

def generate_air_waybill():
    path = os.path.join(OUTPUT_DIR, "air_waybill.pdf")
    doc = SimpleDocTemplate(path, pagesize=A4,
                            leftMargin=18*mm, rightMargin=18*mm,
                            topMargin=15*mm, bottomMargin=15*mm)
    story = []

    story.append(heading("AIR WAYBILL (NON-NEGOTIABLE)", size=15))
    story.append(HRFlowable(width="100%", thickness=2, color=HEADER_BG))
    story.append(Spacer(1, 4))

    # AWB reference header
    awb_ref = [
        ["AWB Number:", "526-1234 5678", "Issuing Carrier:", "SriLankan Airlines (UL)"],
        ["Departure Airport:", "Bandaranaike Intl (CMB)", "Destination Airport:", "Los Angeles Intl (LAX)"],
        ["Routing:", "CMB → DXB → LAX", "Flight No.:", "UL 504 / EK 215"],
        ["Date of Issue:", "15 September 2026", "Departure Date:", "17 September 2026"],
    ]
    awb_tbl = Table(awb_ref, colWidths=[38*mm, 55*mm, 38*mm, 42*mm])
    awb_tbl.setStyle(TableStyle([
        ("FONTNAME",     (0,0), (0,-1), "Helvetica-Bold"),
        ("FONTNAME",     (2,0), (2,-1), "Helvetica-Bold"),
        ("FONTSIZE",     (0,0), (-1,-1), 8),
        ("ROWBACKGROUNDS",(0,0),(-1,-1), [ROW_WHITE, ROW_ALT]),
        ("BOX",          (0,0), (-1,-1), 0.5, BORDER),
        ("INNERGRID",    (0,0), (-1,-1), 0.3, BORDER),
        ("TOPPADDING",   (0,0), (-1,-1), 4),
        ("BOTTOMPADDING",(0,0), (-1,-1), 4),
        ("LEFTPADDING",  (0,0), (-1,-1), 5),
    ]))
    story.append(awb_tbl)
    story.append(Spacer(1, 8))

    # Shipper and Consignee
    parties_data = [[
        Paragraph("<b>SHIPPER</b>", ParagraphStyle("ph", fontName="Helvetica-Bold", fontSize=9)),
        Paragraph("<b>CONSIGNEE</b>", ParagraphStyle("ph", fontName="Helvetica-Bold", fontSize=9)),
        Paragraph("<b>NOTIFY PARTY</b>", ParagraphStyle("ph", fontName="Helvetica-Bold", fontSize=9)),
    ],[
        body("Brandix Lanka Ltd.\nBrandix Campus, Narthupana\nPeliyagoda, Sri Lanka\nTel: +94 11 4 699 000"),
        body("American Eagle Outfitters\n77 Hot Metal Street\nPittsburgh, PA 15203\nUSA"),
        body("Expeditors International\n1015 Third Avenue\nSeattle, WA 98104\nUSA\nTel: +1 (206) 674-3400"),
    ]]
    parties_tbl = Table(parties_data, colWidths=[57*mm, 57*mm, 56*mm])
    parties_tbl.setStyle(TableStyle([
        ("BOX",        (0,0), (-1,-1), 0.5, BORDER),
        ("INNERGRID",  (0,0), (-1,-1), 0.5, BORDER),
        ("BACKGROUND", (0,0), (-1,0),  HEADER_BG),
        ("TEXTCOLOR",  (0,0), (-1,0),  colors.white),
        ("TOPPADDING", (0,0), (-1,-1), 5),
        ("BOTTOMPADDING",(0,0),(-1,-1),5),
        ("LEFTPADDING",(0,0), (-1,-1), 6),
    ]))
    story.append(parties_tbl)
    story.append(Spacer(1, 8))

    story.append(heading("CARGO DETAILS", size=10, align=TA_LEFT))
    story.append(Spacer(1, 3))

    cargo_header = ["No. of\nPieces", "Kind of\nPackaging", "Description of Goods", "Gross Weight\n(KG)", "Net Weight\n(KG)", "Chargeable\nWeight (KG)", "Rate\n(USD/KG)", "Amount\n(USD)"]
    cargo_rows = [
        ["24", "Cartons", "Women's Knit Dresses\n100% Cotton, HS: 6104.41.00\nCountry of Origin: Sri Lanka", "312.00", "288.00", "312.00", "3.85", "1,201.20"],
        ["16", "Cartons", "Men's Polo Shirts\n100% Cotton Pique, HS: 6105.10.00\nCountry of Origin: Sri Lanka", "128.00", "116.00", "128.00", "3.85", "492.80"],
    ]
    totals_row = ["40", "", "TOTAL", "440.00", "404.00", "440.00", "", "1,694.00"]
    cargo_data = [cargo_header] + cargo_rows + [totals_row]

    col_w = [14*mm, 20*mm, 60*mm, 20*mm, 18*mm, 22*mm, 14*mm, 18*mm]
    cargo_tbl = Table(cargo_data, colWidths=col_w, repeatRows=1)
    ts = base_table_style()
    ts.add("FONTNAME", (0,-1), (-1,-1), "Helvetica-Bold")
    ts.add("BACKGROUND",(0,-1),(-1,-1), ROW_ALT)
    ts.add("ALIGN",    (3,0),  (-1,-1), "RIGHT")
    cargo_tbl.setStyle(ts)
    story.append(cargo_tbl)
    story.append(Spacer(1, 8))

    # Charges
    charges_data = [
        ["CHARGES", "CURRENCY", "AMOUNT"],
        ["Airfreight",    "USD", "1,694.00"],
        ["Fuel Surcharge","USD",   "338.80"],
        ["Security Fee",  "USD",    "44.00"],
        ["TOTAL",         "USD", "2,076.80"],
    ]
    charges_tbl = Table(charges_data, colWidths=[80*mm, 30*mm, 60*mm])
    ts2 = base_table_style()
    ts2.add("ALIGN",    (1,0), (-1,-1), "RIGHT")
    ts2.add("FONTNAME", (0,-1),(-1,-1), "Helvetica-Bold")
    ts2.add("BACKGROUND",(0,-1),(-1,-1), ROW_ALT)
    charges_tbl.setStyle(ts2)
    story.append(charges_tbl)
    story.append(Spacer(1, 8))

    story.append(body(
        "Declared Value for Carriage: USD 45,000.00  |  Declared Value for Customs: USD 45,000.00\n\n"
        "I hereby certify that the particulars on the face hereof are correct and that insofar as any part "
        "of the consignment contains dangerous goods, such part is properly described by name and is in "
        "proper condition for carriage by air according to the applicable Dangerous Goods Regulations.\n\n\n"
        "Signature of Shipper or his Agent: _____________________________\n"
        "Executed on: 15 September 2026 at Peliyagoda, Sri Lanka"
    ))

    doc.build(story)
    print(f"  [OK] Created: {path}")


# ─── Main ──────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    print("Generating sample Sri Lankan trade documents...\n")
    generate_commercial_invoice()
    generate_packing_list()
    generate_air_waybill()
    print("\n[DONE] All 3 documents generated in the 'sample_docs/' folder.")
    print("   Run OCR on them with:")
    print("   python ai_pipeline/test_ocr.py sample_docs/commercial_invoice.pdf")
