# library/manager.py
import os
import time
from pathlib import Path  
from preprocess.pdf_reader import PDFReader
from preprocess.ocr import OCRExtractor
from preprocess.cleaner import TextCleaner
from embed.chunker import TextChunker
from library.metadata import MetadataDB
import config

class DocumentManager:
    def __init__(self, db_path):
        self.db = MetadataDB(db_path)

        self.pdf_reader = PDFReader()
        self.ocr = OCRExtractor()
        self.cleaner = TextCleaner()
        self.chunker = TextChunker(
            chunk_size=config.CHUNK_SIZE,
            overlap=config.CHUNK_OVERLAP
        )

    def ingest_document(self, path, doc_id):
        file_name = os.path.basename(path)

        if path.lower().endswith(".pdf"):
            # let PDFReader decide native text vs scanned (it will use ocr_extractor)
            text, page_count = self.pdf_reader.extract_text(path, return_pages=True, ocr_extractor=self.ocr)
        else:
            # images -> OCR directly
            text = self.ocr.extract(Path(path))
            page_count = 1

        cleaned_text = self.cleaner.clean_text(text)
        chunks = self.chunker.split(cleaned_text)

        self.db.add_document({
            "doc_id": doc_id,
            "name": file_name,
            "path": path,
            "timestamp": time.time(),
            "pages": page_count,
            "chunks": len(chunks)
        })

        return chunks

    def list_documents(self):
        docs = self.db.get_all()
        for d in docs:
            d.setdefault("pages", "unknown")
            d.setdefault("chunks", 0)
        return docs
