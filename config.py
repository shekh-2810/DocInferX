# config.py
"""
Global Configuration File
Central place for all project settings.
"""

import os


# BASE PATHS

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

DATA_DIR = os.path.join(BASE_DIR, "data")
os.makedirs(DATA_DIR, exist_ok=True)

# FAISS + Metadata store
INDEX_PATH = os.path.join(DATA_DIR, "vector_index.faiss")
META_PATH = os.path.join(DATA_DIR, "metadata.npy")

# Library metadata DB
LIBRARY_META_PATH = os.path.join(DATA_DIR, "library_metadata.json")

# Uploaded PDFs/images (optional)
UPLOAD_DIR = os.path.join(DATA_DIR, "uploads")
os.makedirs(UPLOAD_DIR, exist_ok=True)


# OCR SETTINGS

OCR_LANGS = ["en"]
OCR_BATCH_SIZE = 4

# For PDFReader (text-based vs OCR)
PDF_TEXT_MODE = "auto"     # auto / text-only / image-only


# TEXT CLEANING

CLEAN_REMOVE_EXTRA_SPACES = True
CLEAN_NORMALIZE_QUOTES = True


# CHUNKING

CHUNK_SIZE = 600
CHUNK_OVERLAP = 120


# EMBEDDING MODEL (FAISS)

EMBED_MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"


# GENERATION MODEL 

GENERATOR_MODEL = "microsoft/phi-2"

MAX_GENERATION_TOKENS = 1024
TEMPERATURE = 0.6
TOP_P = 0.9

DEVICE = "auto"  


# APP METADATA

APP_TITLE = "DocInferX – Local RAG Engine"
APP_DESCRIPTION = "Multi-document searchable AI assistant."
