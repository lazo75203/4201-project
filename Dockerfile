FROM python:3.11-slim

# System deps for Tesseract
RUN apt-get update && apt-get install -y --no-install-recommends \
    tesseract-ocr \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .
# Optional: if your code hardcodes Windows tesseract path, remove that line;
# pytesseract finds /usr/bin/tesseract in this image automatically.

ENV PYTHONUNBUFFERED=1
CMD ["python", "connectTest.py"]
