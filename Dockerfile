# ---------------------------------------------------------
# Stage 1 — Base Builder
# ---------------------------------------------------------
FROM python:3.10-slim AS base

# Prevent Python from writing .pyc files & enable buffered output
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

# System packages required for FAISS, Tesseract OCR, PDFs
RUN apt-get update && apt-get install -y --no-install-recommends \
    tesseract-ocr \
    libtesseract-dev \
    poppler-utils \
    libgl1 \
    && rm -rf /var/lib/apt/lists/*

# Install pipx for cleaner virtual env handling
RUN pip install --no-cache-dir pipx && pipx ensurepath

WORKDIR /app

COPY requirements.txt .

# Install all Python dependencies (cached layer)
RUN pip install --no-cache-dir -r requirements.txt

# ---------------------------------------------------------
# Stage 2 — Final Runtime Image
# ---------------------------------------------------------
FROM python:3.10-slim AS runtime

# Install only required system dependencies (smaller image)
RUN apt-get update && apt-get install -y --no-install-recommends \
    tesseract-ocr \
    poppler-utils \
    libgl1 \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy installed Python packages from builder
COPY --from=base /usr/local/lib/python3.10 /usr/local/lib/python3.10
COPY --from=base /usr/local/bin /usr/local/bin

# Copy project files
COPY . .

EXPOSE 8501

# Streamlit config (prevents "headless mode" issues)
ENV STREAMLIT_SERVER_HEADLESS=true \
    STREAMLIT_BROWSER_GATHER_USAGE_STATS=false

# Run the app
CMD ["streamlit", "run", "streamlit_app.py"]
