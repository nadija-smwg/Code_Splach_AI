"""
Create realistic shipping document PDFs and run them through the pipeline.
Output: JSON result per document, saved to demo_pipeline_output.json

Run: py backend/create_and_test_pdfs.py
"""

import sys
import json
from pathlib import Path
from fpdf import FPDF

sys.path.insert(0, str(Path(__file__).parent))

OUTPUT_DIR = Path(__file__).parent.parent / "demo"
OUTPUT_DIR.mkdir(exist_ok=True)


# ─────────────────────────────────────────────────────────────
# PDF BUILDERS — realistic shipping document content
# ─────────────────────────────────────────────────────────────

def make_invoice(path: str):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Helvetica", "B", 16)
    pdf.cell(0, 10, "COMMERCIAL INVOICE", ln=True, align="C")
    pdf.ln(4)

    pdf.set_font("Helvetica", "", 11)
    pdf.cell(0, 8, "Supplier: Pacific Garments (Pvt) Ltd", ln=True)
    pdf.cell(0, 8, "Address:  No. 12, Biyagama EPZ, Colombo, Sri Lanka", ln=True)
    pdf.ln(3)
    pdf.cell(0, 8, "Consignee: Burlington Industries Inc.", ln=True)
    pdf.cell(0, 8, "Address:   1345 Avenue of Fashion, New York, NY 10018, USA", ln=True)
    pdf.ln(6)

    pdf.set_font("Helvetica", "B", 11)
    pdf.cell(90, 8, "Invoice No:", border=0)
    pdf.set_font("Helvetica", "", 11)
    pdf.cell(0, 8, "INV-2024-1023", ln=True)

    pdf.set_font("Helvetica", "B", 11)
    pdf.cell(90, 8, "Invoice Date:", border=0)
    pdf.set_font("Helvetica", "", 11)
    pdf.cell(0, 8, "15 January 2024", ln=True)

    pdf.set_font("Helvetica", "B", 11)
    pdf.cell(90, 8, "Incoterm:", border=0)
    pdf.set_font("Helvetica", "", 11)
    pdf.cell(0, 8, "FOB Colombo", ln=True)

    pdf.set_font("Helvetica", "B", 11)
    pdf.cell(90, 8, "Payment Terms:", border=0)
    pdf.set_font("Helvetica", "", 11)
    pdf.cell(0, 8, "60 Days from B/L Date", ln=True)
    pdf.ln(4)

    # Item table
    pdf.set_font("Helvetica", "B", 10)
    pdf.set_fill_color(220, 220, 220)
    pdf.cell(70, 8, "Description", border=1, fill=True)
    pdf.cell(25, 8, "Qty (Pcs)", border=1, fill=True)
    pdf.cell(25, 8, "Unit (USD)", border=1, fill=True)
    pdf.cell(30, 8, "Total (USD)", border=1, fill=True, ln=True)

    pdf.set_font("Helvetica", "", 10)
    items = [
        ("100% Cotton T-Shirts (Assorted Colors)", "3600", "4.50", "16,200.00"),
        ("Polo Shirts (Navy / White)", "2400", "7.20", "17,280.00"),
        ("Casual Shorts", "1800", "6.53", "11,754.00"),
    ]
    for desc, qty, unit, total in items:
        pdf.cell(70, 8, desc, border=1)
        pdf.cell(25, 8, qty, border=1, align="C")
        pdf.cell(25, 8, unit, border=1, align="R")
        pdf.cell(30, 8, total, border=1, align="R", ln=True)

    pdf.set_font("Helvetica", "B", 11)
    pdf.cell(120, 8, "")
    pdf.cell(30, 8, "TOTAL USD:", border=1)
    pdf.cell(30, 8, "45,234.00", border=1, align="R", ln=True)
    pdf.ln(6)

    pdf.set_font("Helvetica", "", 11)
    pdf.cell(0, 8, "Gross Weight:  450.00 KG", ln=True)
    pdf.cell(0, 8, "Net Weight:    420.00 KG", ln=True)
    pdf.cell(0, 8, "Package Count: 25 Cartons", ln=True)
    pdf.cell(0, 8, "Currency:      USD", ln=True)

    pdf.output(path)
    print(f"  Created: {path}")


def make_packing_list(path: str):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Helvetica", "B", 16)
    pdf.cell(0, 10, "PACKING LIST", ln=True, align="C")
    pdf.ln(4)

    pdf.set_font("Helvetica", "", 11)
    pdf.cell(0, 8, "Exporter: Pacific Garments (Pvt) Ltd", ln=True)
    pdf.cell(0, 8, "Consignee: Burlington Industries Inc.", ln=True)
    pdf.ln(5)

    pdf.set_font("Helvetica", "B", 11)
    pdf.cell(90, 8, "Reference No:", border=0)
    pdf.set_font("Helvetica", "", 11)
    pdf.cell(0, 8, "PL-2024-1023", ln=True)

    pdf.set_font("Helvetica", "B", 10)
    pdf.set_fill_color(220, 220, 220)
    pdf.cell(60, 8, "Description", border=1, fill=True)
    pdf.cell(20, 8, "Ctns", border=1, fill=True)
    pdf.cell(30, 8, "Gross Wt (KG)", border=1, fill=True)
    pdf.cell(30, 8, "Net Wt (KG)", border=1, fill=True)
    pdf.cell(25, 8, "CBM", border=1, fill=True, ln=True)

    pdf.set_font("Helvetica", "", 10)
    rows = [
        ("Cotton T-Shirts", "10", "180.00", "168.00", "0.600"),
        ("Polo Shirts", "8", "160.00", "150.00", "0.480"),
        ("Casual Shorts", "7", "110.00", "102.00", "0.360"),
    ]
    for r in rows:
        pdf.cell(60, 8, r[0], border=1)
        pdf.cell(20, 8, r[1], border=1, align="C")
        pdf.cell(30, 8, r[2], border=1, align="R")
        pdf.cell(30, 8, r[3], border=1, align="R")
        pdf.cell(25, 8, r[4], border=1, align="R", ln=True)

    pdf.set_font("Helvetica", "B", 11)
    pdf.cell(80, 8, "TOTALS:")
    pdf.cell(0, 8, "25 Ctns    450.00 KG    420.00 KG    1.440 CBM", ln=True)
    pdf.ln(4)
    pdf.set_font("Helvetica", "", 11)
    pdf.cell(0, 8, "Gross Weight:  450.00 KG", ln=True)
    pdf.cell(0, 8, "Net Weight:    420.00 KG", ln=True)
    pdf.cell(0, 8, "Tare Weight:   30.00 KG", ln=True)
    pdf.cell(0, 8, "Volume:        1.440 CBM", ln=True)
    pdf.cell(0, 8, "Package Count: 25 Cartons", ln=True)
    pdf.cell(0, 8, "Shipping Marks: PG/BUR/2024/NY", ln=True)

    pdf.output(path)
    print(f"  Created: {path}")


def make_awb(path: str):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Helvetica", "B", 16)
    pdf.cell(0, 10, "AIR WAYBILL (AWB)", ln=True, align="C")
    pdf.ln(4)

    pdf.set_font("Helvetica", "", 11)
    rows = [
        ("AWB Number:",     "179 - 34561234"),
        ("Flight Number:",  "EK 655"),
        ("Origin:",         "Colombo (CMB)"),
        ("Destination:",    "Los Angeles (LAX)"),
        ("Shipper Name:",   "Pacific Garments (Pvt) Ltd"),
        ("Consignee Name:", "Burlington Industries Inc."),
        ("Gross Weight:",   "450.00 KG"),
        ("Package Count:",  "25 Cartons"),
        ("Nature of Goods:","Cotton Garments"),
    ]
    for label, value in rows:
        pdf.set_font("Helvetica", "B", 11)
        pdf.cell(60, 9, label)
        pdf.set_font("Helvetica", "", 11)
        pdf.cell(0, 9, value, ln=True)

    pdf.output(path)
    print(f"  Created: {path}")


def make_bol(path: str):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Helvetica", "B", 16)
    pdf.cell(0, 10, "BILL OF LADING", ln=True, align="C")
    pdf.ln(4)

    pdf.set_font("Helvetica", "", 11)
    rows = [
        ("B/L Number:",      "MSCU1234567890"),
        ("Vessel Name:",     "MSC BEATRICE"),
        ("Port of Loading:",  "Colombo (LKCMB)"),
        ("Port of Discharge:","Los Angeles (USLAX)"),
        ("Shipper:",         "Pacific Garments (Pvt) Ltd"),
        ("Consignee:",       "Burlington Industries Inc."),
        ("Container No:",    "MSCU1234567"),
        ("Gross Weight:",    "448.00 KG"),
        ("Package Count:",   "25 Cartons"),
    ]
    for label, value in rows:
        pdf.set_font("Helvetica", "B", 11)
        pdf.cell(60, 9, label)
        pdf.set_font("Helvetica", "", 11)
        pdf.cell(0, 9, value, ln=True)

    pdf.output(path)
    print(f"  Created: {path}")


def make_delivery_order(path: str):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Helvetica", "B", 16)
    pdf.cell(0, 10, "DELIVERY ORDER", ln=True, align="C")
    pdf.ln(4)

    pdf.set_font("Helvetica", "", 11)
    rows = [
        ("DO Number:",        "DO-2024-5678"),
        ("Consignee:",        "Burlington Industries Inc."),
        ("Container No:",     "MSCU1234567"),
        ("Port of Discharge:","Los Angeles (USLAX)"),
        ("Gross Weight:",     "448.00 KG"),
        ("Package Count:",    "25 Cartons"),
        ("Release Date:",     "20 January 2024"),
    ]
    for label, value in rows:
        pdf.set_font("Helvetica", "B", 11)
        pdf.cell(60, 9, label)
        pdf.set_font("Helvetica", "", 11)
        pdf.cell(0, 9, value, ln=True)

    pdf.output(path)
    print(f"  Created: {path}")


# ─────────────────────────────────────────────────────────────
# GENERATE ALL PDFS
# ─────────────────────────────────────────────────────────────

print("\n[1] Generating realistic shipping document PDFs...")
make_invoice(str(OUTPUT_DIR / "commercial_invoice.pdf"))
make_packing_list(str(OUTPUT_DIR / "packing_list.pdf"))
make_awb(str(OUTPUT_DIR / "awb.pdf"))
make_bol(str(OUTPUT_DIR / "bill_of_lading.pdf"))
make_delivery_order(str(OUTPUT_DIR / "delivery_order.pdf"))
print("    Done.\n")


# ─────────────────────────────────────────────────────────────
# RUN THROUGH MOCK PIPELINE + REAL NORMALIZER
# ─────────────────────────────────────────────────────────────

print("[2] Running documents through pipeline + normalizer...\n")

from ai_pipeline.mock_pipeline import MockPipeline
from ai_pipeline.normalizer import EntityNormalizer
from ai_pipeline.confidence import ConfidenceScorer
from ai_pipeline.contract_validator import validate_extraction_result

pipe = MockPipeline()
norm = EntityNormalizer()
scorer = ConfidenceScorer()

# Map each PDF to the correct mock document type it represents
DOC_MAP = {
    "commercial_invoice":  ("commercial_invoice.pdf", "invoice_001"),
    "packing_list":        ("packing_list.pdf",       "packing_001"),
    "awb":                 ("awb.pdf",                "awb_001"),
    "bill_of_lading":      ("bill_of_lading.pdf",     "bol_001"),
    "delivery_order":      ("delivery_order.pdf",     "do_001"),
}

all_results = {}

for doc_name, (filename, doc_id) in DOC_MAP.items():
    pdf_path = OUTPUT_DIR / filename

    # Run pipeline (mock — gives us the contract-compliant structure)
    result = pipe.process_document(str(pdf_path), doc_id)

    # Overwrite document_type to match the actual document
    type_map = {
        "invoice_001": "commercial_invoice",
        "packing_001": "packing_list",
        "awb_001":     "awb",
        "bol_001":     "bl",
        "do_001":      "delivery_order",
    }
    result["document_type"] = type_map[doc_id]

    # Run real Tier 1 normalizer on every entity
    for entity in result["entities"]:
        try:
            n = norm.normalize(entity["entity_type"], entity["value"])
            entity["normalized_value"]    = n["normalized_value"]
            entity["unit"]                = n["unit"]
            entity["normalization_warning"] = n["warn"]
        except Exception as e:
            entity["normalization_warning"] = True

    # Apply confidence scoring
    result["entities"] = scorer.score_entities(result["entities"])

    # Validate against master contract
    validate_extraction_result(result)

    all_results[doc_name] = result

    print(f"  {doc_name}")
    print(f"    Type        : {result['document_type']}")
    print(f"    Class Conf  : {result['classification_confidence']}")
    print(f"    Entities    : {len(result['entities'])}")
    print(f"    Errors      : {result['errors']}")
    for e in result["entities"]:
        print(f"      [{e['entity_type']:25}] {str(e['value']):25} -> norm={e['normalized_value']!r:15} unit={e['unit']!r} conf={e['extraction_confidence']}")
    print()


# ─────────────────────────────────────────────────────────────
# SAVE JSON OUTPUT
# ─────────────────────────────────────────────────────────────

output_path = Path("demo_pipeline_output.json")
output_path.write_text(json.dumps(all_results, indent=2), encoding="utf-8")

print(f"[3] JSON output saved to: {output_path.resolve()}")
print(f"    Total documents: {len(all_results)}")
print(f"    Total entities:  {sum(len(r['entities']) for r in all_results.values())}")
print()
print("SUCCESS - Pipeline produced valid JSON for all 5 documents!")
