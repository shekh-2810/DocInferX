# embed/chunker.py
import re
from typing import List

class TextChunker:
    def __init__(self, chunk_size: int = 600, overlap: int = 120):
        self.chunk_size = chunk_size
        self.overlap = overlap

    def clean_spaces(self, text: str) -> str:
        # preserve newlines for page boundaries, collapse multiple newlines to one
        text = re.sub(r"\r\n?", "\n", text)
        text = re.sub(r"\n{2,}", "\n\n", text)
        return text.strip()

    def _sliding_chunks(self, text: str) -> List[str]:
        text = re.sub(r"\s+", " ", text).strip()
        if not text:
            return []
        chunks = []
        start = 0
        length = len(text)
        while start < length:
            end = start + self.chunk_size
            chunk = text[start:end].strip()
            if chunk:
                chunks.append(chunk)
            start = start + self.chunk_size - self.overlap
        return chunks

    def split(self, text: str) -> List[str]:
        text = self.clean_spaces(text)
        if not text:
            return []

        # If pages present, split per page first
        if "### PAGE" in text.upper() or "### Page" in text:
            # split on markers like ### PAGE 1 ### (case-insensitive)
            parts = re.split(r"(?:###\s*PAGE\s*\d+\s*###)", text, flags=re.IGNORECASE)
            # re.split keeps separators out; we reconstruct pages by looking for markers
            pages = []
            # Try to find markers with findall to align pages
            markers = re.findall(r"(###\s*PAGE\s*\d+\s*###)", text, flags=re.IGNORECASE)
            # If markers count matches parts-1: then assemble
            # parts example: ['', 'content1', 'content2', ...] -> align
            idx = 0
            for p in parts:
                p = p.strip()
                if p:
                    pages.append(p)
            # for each page, either treat as single chunk or further chunk if long
            out_chunks = []
            for page_text in pages:
                if len(page_text) <= self.chunk_size:
                    out_chunks.append(page_text)
                else:
                    out_chunks.extend(self._sliding_chunks(page_text))
            return out_chunks

        # otherwise sliding-window on whole text
        return self._sliding_chunks(text)
