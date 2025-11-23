FROM python:3.10-slim

WORKDIR /app

# Install system packages (for PDF + OCR)
RUN apt-get update && apt-get install -y \
    libmagic-dev \
    tesseract-ocr \
    poppler-utils \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8501

CMD ["streamlit", "run", "streamlit_app.py", "--server.port=8501", "--server.address=0.0.0.0"]
