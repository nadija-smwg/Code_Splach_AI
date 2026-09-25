import os
from pathlib import Path

# Minimal valid PDF string
MINIMAL_PDF_BYTES = b"""%PDF-1.1
%\xa2\xa2\xa2\xa2
1 0 obj
<< /Type /Catalog
/Pages 2 0 R
>>
endobj
2 0 obj
<< /Type /Pages
/Kids [3 0 R]
/Count 1
/MediaBox [0 0 595 842]
>>
endobj
3 0 obj
<<  /Type /Page
/Parent 2 0 R
/Resources
<< /Font
<< /F1
<< /Type /Font
/Subtype /Type1
/BaseFont /Times-Roman
>>
>>
>>
/Contents 4 0 R
>>
endobj
4 0 obj
<< /Length 55 >>
stream
  BT
    /F1 18 Tf
    50 750 Td
    (Fake Shipping Document) Tj
  ET
endstream
endobj
xref
0 5
0000000000 65535 f 
0000000018 00000 n 
0000000077 00000 n 
0000000178 00000 n 
0000000457 00000 n 
trailer
<<  /Root 1 0 R
/Size 5
>>
startxref
565
%%EOF
"""

def create_pdf(filepath):
    path = Path(filepath)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(MINIMAL_PDF_BYTES)
    print(f"Created fake PDF: {filepath}")

def main():
    demo_files = [
        "demo/commercial_invoice.pdf",
        "demo/packing_list.pdf",
        "demo/awb.pdf",
        "demo/bill_of_lading.pdf",
        "demo/delivery_order.pdf",
    ]
    
    synthetic_files = [
        "test_data/synthetic/test_commercial_invoice.pdf",
        "test_data/synthetic/test_packing_list.pdf",
        "test_data/synthetic/test_awb.pdf",
        "test_data/synthetic/test_bill_of_lading.pdf",
    ]

    for f in demo_files:
        create_pdf(f)
        
    for f in synthetic_files:
        create_pdf(f)

if __name__ == "__main__":
    main()
