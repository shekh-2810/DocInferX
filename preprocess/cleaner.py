# preprocess/cleaner.py
# Handles text cleaning and normalization for RAG pipeline.

import re
import unicodedata


class TextCleaner:
    """
    Cleans and normalizes raw text.
    """

    def __init__(self):
        pass

    def remove_extra_whitespace(self, text: str) -> str:
        
        return re.sub(r'\s+', ' ', text).strip()

    def normalize_unicode(self, text: str) -> str:
        
        return unicodedata.normalize('NFKC', text)

    def remove_special_characters(self, text: str) -> str:
        
        return re.sub(r'[^a-zA-Z0-9.,;:!?()\s]', '', text)

    def clean_text(self, text: str) -> str:
        """
        Full pipeline: normalize, remove special characters, clean whitespace.
        """
        text = self.normalize_unicode(text)
        text = self.remove_special_characters(text)
        text = self.remove_extra_whitespace(text)
        return text
