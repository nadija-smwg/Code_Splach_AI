# backend/ai_pipeline/test_ocr.py
from ocr_engine import OcrEngine
import json
import sys

def main():
    if len(sys.argv) > 1:
        pdf_path = sys.argv[1]
    else:
        print("Usage: python test_ocr.py <path_to_pdf>")
        return

    print(f"Running OCR on: {pdf_path}")
    engine = OcrEngine()
    result = engine.extract(pdf_path)

    if result.total_pages == 0:
        print("Failed to process PDF or PDF is empty.")
        return

    # Print summary
    for page in result.pages:
        print(f"\n--- Page {page.page_number} ({page.width}x{page.height}) ---")
        for token in page.tokens[:10]:  # First 10 tokens
            print(f"  [{token.confidence:.2f}] {token.text}")
            print(f"    BBox: {token.bbox}")
        
        if len(page.tokens) > 10:
            print(f"  ... and {len(page.tokens) - 10} more tokens.")

    # Save full output
    output_filename = "ocr_output_sample.json"
    with open(output_filename, "w") as f:
        json.dump(engine.to_dict(result), f, indent=2)
    
    print(f"\n✅ Full output saved to {output_filename}")

if __name__ == "__main__":
    main()
