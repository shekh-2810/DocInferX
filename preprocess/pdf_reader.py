# preprocess/pdf_reader.py
import fitz  
from typing import List, Tuple
from PIL import Image
import io

class PDFReader:
    def __init__(self, dpi: int = 200):
        self.dpi = dpi

    def extract_images(self, pdf_path: str) -> List[Image.Image]:
        doc = fitz.open(pdf_path)
        images = []
        zoom = self.dpi / 72
        mat = fitz.Matrix(zoom, zoom)
        for page in doc:
            pix = page.get_pixmap(matrix=mat)
            img = Image.open(io.BytesIO(pix.tobytes("png")))
            images.append(img)
        return images

    def extract_text_from_images(self, images: List[Image.Image], ocr_extractor) -> str:
        text_list = []
        for idx, img in enumerate(images, start=1):
            tmp = io.BytesIO()
            img.save(tmp, format="PNG")
            tmp.seek(0)
            # pass bytes path to OCR extractor which expects a path
            with open(f"/tmp/docinferx_page_{idx}.png", "wb") as f:
                f.write(tmp.read())
            page_text = ocr_extractor.extract_from_image(f"/tmp/docinferx_page_{idx}.png")
            text_list.append(f"### PAGE {idx} ###\n{page_text}")
            try:
                import os
                os.remove(f"/tmp/docinferx_page_{idx}.png")
            except:
                pass
        return "\n\n".join(text_list)

    def extract_text(
        self,
        pdf_path: str,
        return_pages: bool = False,
        ocr_extractor=None
    ):
        doc = fitz.open(pdf_path)
        num_pages = doc.page_count

        full_text = []
        for page in doc:
            text = page.get_text("text") or ""
            if text and text.strip():
                full_text.append(text)
            else:
                full_text.append("")

        if any(p.strip() for p in full_text):
            native_text = "\n\n".join([f"### PAGE {i+1} ###\n{t.strip()}" for i, t in enumerate(full_text)])
            if return_pages:
                return native_text, num_pages
            return native_text

        # fallback to OCR if no native text
        if ocr_extractor is None:
            raise ValueError("[PDFReader] PDF appears scanned but no OCR extractor provided.")

        images = self.extract_images(pdf_path)
        ocr_text = self.extract_text_from_images(images, ocr_extractor)
        if return_pages:
            return ocr_text, num_pages
        return ocr_text
