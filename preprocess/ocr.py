# preprocess/ocr.py
from pathlib import Path
import tempfile
from pdf2image import convert_from_path
from paddleocr import PaddleOCR
from PIL import Image
import os

class OCRExtractor:
    def __init__(self):
        # Initialize PaddleOCR in the most compatible way for multiple versions
        print("[PaddleOCR] Initializing (compat mode)...")
        try:
            # minimal args
            self.reader = PaddleOCR(lang="en")
        except TypeError:
            # more fallback
            self.reader = PaddleOCR()
        print("[PaddleOCR] Loaded (legacy-compatible mode).")

    def _clean_lines_from_result(self, result):
        lines = []
        # result structure differs by version; handle common formats
        for block in result:
            # sometimes result is [ [ (box, (text, score)), ... ] ]
            if isinstance(block, list):
                for item in block:
                    try:
                        text = item[1][0]
                    except Exception:
                        
                        try:
                            text = item[1]["text"]
                        except Exception:
                            continue
                    if len(text.strip()) > 1:
                        lines.append(text.strip())
            else:
                # fallback: try to stringify
                try:
                    t = str(block)
                    if len(t.strip()) > 1:
                        lines.append(t.strip())
                except:
                    continue
        return lines

    def extract_from_image(self, image_path: str) -> str:
        # Ensure Pillow can open large images without crazy memory blowups
        img = Image.open(image_path)
        w, h = img.size
        max_side = 4000
        if max(w, h) > max_side:
            ratio = max_side / max(w, h)
            new_size = (int(w * ratio), int(h * ratio))
            img = img.resize(new_size, Image.LANCZOS)
            tmp_path = image_path + ".resized.png"
            img.save(tmp_path, format="PNG")
            image_to_process = tmp_path
        else:
            image_to_process = image_path

        result = self.reader.ocr(image_to_process)
        if image_to_process.endswith(".resized.png"):
            try:
                os.remove(image_to_process)
            except:
                pass

        lines = self._clean_lines_from_result(result)
        return "\n".join(lines).strip()

    def extract_from_scanned_pdf(self, pdf_path: str) -> str:
        pages = convert_from_path(pdf_path, dpi=200)
        out_pages = []
        for i, page in enumerate(pages, start=1):
            with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as tmp:
                page.save(tmp.name, "PNG")
                text = self.extract_from_image(tmp.name)
                out_pages.append(f"### PAGE {i} ###\n{text}")
                try:
                    os.remove(tmp.name)
                except:
                    pass
        return "\n\n".join(out_pages).strip()

    def is_scanned_pdf(self, pdf_path: Path) -> bool:
        # conservative: prefer PyPDF2 for text detection
        try:
            from PyPDF2 import PdfReader
        except Exception:
            # if PyPDF2 missing, fallback to pdfplumber if available
            try:
                import pdfplumber
            except Exception:
                return True

            try:
                with pdfplumber.open(pdf_path) as pdf:
                    for p in pdf.pages:
                        t = p.extract_text()
                        if t and t.strip():
                            return False
            except:
                return True
            return True

        try:
            reader = PdfReader(str(pdf_path))
            for p in reader.pages:
                txt = p.extract_text()
                if txt and txt.strip():
                    return False
        except:
            return True
        return True

    def extract(self, file_path: Path) -> str:
        ext = file_path.suffix.lower()
        if ext in [".png", ".jpg", ".jpeg"]:
            return self.extract_from_image(str(file_path))
        if ext == ".pdf":
            # This extractor only performs OCR; prefer PDFReader for native text.
            if self.is_scanned_pdf(file_path):
                return self.extract_from_scanned_pdf(str(file_path))
            else:
                return ""  # signal: not scanned (PDFReader should be used)
        return f"[OCR ERROR] Unsupported file type: {ext}"
