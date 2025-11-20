
# Dockerfile for the Flask OCR application
FROM python:3.11-slim                       

# Install Tesseract OCR
RUN apt-get update && apt-get install -y tesseract-ocr

# Set working directory and install dependencies when container is built through Dockerfile
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .

# Set environment variable to make sure Python output isn't buffereing, makes the logs appear immediately //feature :)
ENV PYTHONUNBUFFERED=1

# Command to run the Flask application when the container starts
CMD ["python", "connectTest.py"]