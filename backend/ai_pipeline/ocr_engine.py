import os
import logging
from dataclasses import dataclass

# Fix for PaddlePaddle 3.x on Windows CPU â€” MUST be set before paddleocr import
os.environ["FLAGS_use_onednn"] = "0"

try:
    import pyclipper
    import cv2
    from paddleocr import PaddleOCR
except Exception as e:
    import logging
    logging.getLogger(__name__).error(f"PaddleOCR import failed: {e}")
    PaddleOCR = None

logger = logging.getLogger(__name__)

@dataclass
class OcrToken:
    text: str
    page: int
    bbox: list  # [x1, y1, x2, y2]
    confidence: float

@dataclass
class OcrPage:
    page_number: int
    width: int
    height: int
    tokens: list

@dataclass
class OcrOutput:
    file_path: str
    total_pages: int
    pages: list

class OcrEngine:
    def __init__(self):
        # Initialize PaddleOCR. use_angle_cls=True handles rotated text.
        # use_gpu=False is safe for broad compatibility, especially on Windows laptops.
        if PaddleOCR is None:
            raise ImportError(
                "PaddleOCR is not installed. Run: py -m pip install paddleocr"
            )
        self.ocr = PaddleOCR(use_angle_cls=True, lang='en')
    
    def extract(self, pdf_path: str) -> OcrOutput:
        """Extract text + bounding boxes from all pages of a PDF."""
        from pdf2image import convert_from_path  # lazy import â€” optional dep

        if not os.path.exists(pdf_path):
            raise FileNotFoundError(f"PDF file not found: {pdf_path}")

        try:
            # Extract OCR data using PaddleOCR
            result = self.ocr.ocr(pdf_path)
            
            # Get page dimensions using pdf2image
            images = convert_from_path(pdf_path)
            
            pages = []
            for page_idx, (page_result, img) in enumerate(zip(result, images)):
                tokens = []
                if page_result:
                    for line in page_result:
                        if not line or len(line) < 2:
                            continue
                        
                        bbox_raw = line[0]  # [[x1,y1],[x2,y2],[x3,y3],[x4,y4]]
                        text = line[1][0]
                        confidence = float(line[1][1])
                        
                        # Convert quadrilateral to [x1, y1, x2, y2] bounding box
                        x_coords = [p[0] for p in bbox_raw]
                        y_coords = [p[1] for p in bbox_raw]
                        bbox = [min(x_coords), min(y_coords), max(x_coords), max(y_coords)]
                        
                        tokens.append(OcrToken(
                            text=text,
                            page=page_idx + 1,
                            bbox=bbox,
                            confidence=confidence
                        ))
                
                pages.append(OcrPage(
                    page_number=page_idx + 1,
                    width=img.width,
                    height=img.height,
                    tokens=tokens
                ))
            
            return OcrOutput(
                file_path=pdf_path,
                total_pages=len(pages),
                pages=pages
            )
        except Exception as e:
            logger.error(f"Failed to process PDF {pdf_path}: {str(e)}")
            # Return an empty output on failure so the system doesn't crash completely
            return OcrOutput(file_path=pdf_path, total_pages=0, pages=[])
    
    def to_dict(self, output: OcrOutput) -> dict:
        """Convert to JSON-serializable dictionary."""
        return {
            "file_path": output.file_path,
            "total_pages": output.total_pages,
            "pages": [
                {
                    "page_number": p.page_number,
                    "width": p.width,
                    "height": p.height,
                    "tokens": [
                        {
                            "text": t.text,
                            "page": t.page,
                            "bbox": t.bbox,
                            "confidence": t.confidence
                        } for t in p.tokens
                    ]
                } for p in output.pages
            ]
        }
