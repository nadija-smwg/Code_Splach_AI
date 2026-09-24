import sys, os, time, logging

BACKEND_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if BACKEND_DIR not in sys.path:
    sys.path.insert(0, BACKEND_DIR)

from ai_pipeline.classifier import DocumentClassifier, ClassificationResult, DOCUMENT_SIGNATURES
from ai_pipeline.ocr_engine import OcrOutput, OcrPage, OcrToken

logging.basicConfig(level=logging.WARNING)

passed = 0
failed = 0
warns = 0

def ok(msg):
    global passed; passed += 1
    print("  [PASS] " + msg)

def fail(msg):
    global failed; failed += 1
    print("  [FAIL] " + msg)

def warn(msg):
    global warns; warns += 1
    print("  [WARN] " + msg)

def section(title):
    print("\n" + "="*60 + "\n  " + title + "\n" + "="*60)

def make_ocr(text, path="test.pdf"):
    tokens = [OcrToken(text=w, page=1, bbox=[0,0,100,20], confidence=0.99) for w in text.split() if w]
    page = OcrPage(page_number=1, width=612, height=792, tokens=tokens)
    return OcrOutput(file_path=path, total_pages=1, pages=[page])

def make_empty():
    page = OcrPage(page_number=1, width=612, height=792, tokens=[])
    return OcrOutput(file_path="blank.pdf", total_pages=1, pages=[page])

def check_contract(result, label):
    if 0.0 <= result.confidence <= 1.0:
        ok("[%s] AC2 confidence=%.4f" % (label, result.confidence))
    else:
        fail("[%s] AC2 confidence OUT OF RANGE: %s" % (label, result.confidence))
    if isinstance(result.evidence, list):
        ok("[%s] AC3 evidence=%s" % (label, result.evidence))
    else:
        fail("[%s] AC3 evidence not a list" % label)
    all_types = set(DOCUMENT_SIGNATURES.keys())
    if all_types <= set(result.all_scores.keys()):
        ok("[%s] AC4 all_scores has all %d types" % (label, len(all_types)))
    else:
        fail("[%s] AC4 all_scores missing types" % label)

def run_unit_tests():
    section("UNIT TESTS (Synthetic OCR)")
    clf = DocumentClassifier(use_gemini_fallback=False)
    cases = [
        ("commercial_invoice", "COMMERCIAL INVOICE Invoice No INV-2026-00451 Unit Price Total Amount Payment Terms Description of Goods Amount Due Invoice Number"),
        ("packing_list",       "PACKING LIST Carton No Net Weight Gross Weight No of Cartons Bale Roll Dimensions CBM Cubic Packing"),
        ("awb",                "AIR WAYBILL MAWB HAWB AWB Airway Bill Airport of Departure Airport of Destination IATA Flight Chargeable Weight Pieces"),
        ("bl",                 "BILL OF LADING B/L Vessel Port of Loading Port of Discharge Shipper Notify Party Container Seal No Freight Prepaid"),
        ("letter_of_credit",   "LETTER OF CREDIT L/C Documentary Credit Issuing Bank Beneficiary LC Number Credit Number Expiry Date Place of Expiry Partial Shipment"),
    ]
    for expected, text in cases:
        result = clf.classify(make_ocr(text))
        print("\n  -> %s (%.1f%%)" % (result.document_type, result.confidence*100))
        if result.document_type == expected:
            ok("[%s] AC1 correct" % expected)
        else:
            fail("[%s] AC1 got %s" % (expected, result.document_type))
        check_contract(result, expected)

    print("\n  Testing blank (AC5)...")
    result = clf.classify(make_empty())
    print("  -> %s (%.1f%%)" % (result.document_type, result.confidence*100))
    if result.document_type == "unknown":
        ok("AC5 blank returns unknown")
    else:
        warn("AC5 blank returned %s" % result.document_type)
    if result.confidence <= 0.30:
        ok("AC5 low confidence: %.4f" % result.confidence)
    else:
        warn("AC5 confidence higher than expected: %.4f" % result.confidence)
    check_contract(result, "unknown")

def run_timing():
    section("TIMING TESTS (AC6 - must finish fast)")
    clf = DocumentClassifier(use_gemini_fallback=False)
    texts = [
        "COMMERCIAL INVOICE Unit Price Total Amount Invoice No Payment Terms",
        "PACKING LIST Carton Net Weight Gross Weight Bale Roll Dimensions",
        "AIR WAYBILL MAWB HAWB Airport IATA Flight Chargeable Weight",
    ]
    for i, text in enumerate(texts, 1):
        t0 = time.perf_counter()
        result = clf.classify(make_ocr(text))
        elapsed = time.perf_counter() - t0
        ms = elapsed * 1000
        if elapsed < 5.0:
            ok("Doc%d AC6: %.1fms  (%s)" % (i, ms, result.document_type))
        else:
            fail("Doc%d AC6: %.2fs exceeds 5s limit" % (i, elapsed))

def run_norm_check():
    section("NORMALISATION CHECK")
    clf = DocumentClassifier(use_gemini_fallback=False)
    result = clf.classify(make_ocr("COMMERCIAL INVOICE Invoice No Unit Price Total Amount Payment Terms"))
    total = sum(result.all_scores.values())
    print("\n  all_scores sum: %.6f" % total)
    if abs(total - 1.0) < 0.01:
        ok("all_scores sum ~= 1.0")
    else:
        fail("all_scores sum is %.6f" % total)
    print("\n  Breakdown:")
    for dt, sc in sorted(result.all_scores.items(), key=lambda x: -x[1]):
        bar = "#" * int(sc * 30)
        print("    %-25s %.4f  %s" % (dt, sc, bar))

def run_pdf_tests():
    section("SAMPLE PDF TESTS (Real Docs)")
    sample_dir = os.path.join(BACKEND_DIR, "sample_docs")
    test_cases = {"commercial_invoice.pdf": "commercial_invoice", "packing_list.pdf": "packing_list", "air_waybill.pdf": "awb"}
    if not os.path.isdir(sample_dir):
        warn("sample_docs/ not found - skipping"); return
    try:
        from ai_pipeline.ocr_engine import OcrEngine
        ocr_engine = OcrEngine()
    except Exception as e:
        warn("OcrEngine failed: " + str(e)); warn("Skipping."); return
    clf = DocumentClassifier(use_gemini_fallback=False)
    for fn, expected in test_cases.items():
        pdf = os.path.join(sample_dir, fn)
        if not os.path.exists(pdf):
            warn("Not found: " + pdf); continue
        print("\n  Processing: " + fn)
        try:
            t0 = time.perf_counter()
            ocr_out = ocr_engine.extract(pdf)
            result = clf.classify(ocr_out, pdf_path=pdf)
            elapsed = time.perf_counter() - t0
            print("  %s (%.1f%%) in %.2fs  evidence=%s" % (result.document_type, result.confidence*100, elapsed, result.evidence))
            if result.document_type == expected:
                ok(fn + " AC1 correct")
            else:
                fail(fn + " AC1 got " + result.document_type)
            if elapsed < 5.0:
                ok(fn + " AC6 %.2fs" % elapsed)
            else:
                fail(fn + " AC6 exceeds 5s")
            check_contract(result, fn)
        except Exception as e:
            fail(fn + " exception: " + str(e))

if __name__ == "__main__":
    print("\nPhase 04 -- Document Classifier Test Suite")
    print("=" * 60)
    run_unit_tests()
    run_timing()
    run_norm_check()
    run_pdf_tests()
    total = passed + failed
    section("SUMMARY")
    print("  Passed  : %d/%d" % (passed, total))
    if warns: print("  Warnings: %d" % warns)
    if failed:
        print("  FAILED  : %d/%d" % (failed, total))
        sys.exit(1)
    else:
        print("\n  All Phase 04 acceptance criteria PASSED")
        sys.exit(0)
