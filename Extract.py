from flask import Flask, request, send_file, render_template_string         # Flask imports
from pathlib import Path
from PIL import Image, ImageEnhance, ImageFilter  # Pillow image processing
from reportlab.lib.pagesizes import letter        # For PDF Size
from reportlab.pdfgen import canvas               # PDF generation library

import pytesseract                                # Tesseract OCR wrapper
import platform
import os
import math
import re

# HTML Script for Webpage UI accessible at https://four201-project.onrender.com/upload
HTML = """
<!doctype html>
<html>
    <head>
        <title>CSCE 4201 Project</title>
        <style>
        body {
            margin: 0;
            font-family: Arial, sans-serif;
            background: #f5f5f5;
            display: flex;
            align-items: center;
            justify-content: center;
            min-height: 100vh;
        }
        .container {
            background: #ffffff;
            padding: 24px 32px;
            border-radius: 8px;
            box-shadow: 0 2px 8px rgba(0,0,0,0.15);
            text-align: center;
            max-width: 800px;
            width: 100%;
        }
        form {
            margin-bottom: 16px;
        }
        pre {
            text-align: left;
            background: #f0f0f0;
            padding: 12px;
            border-radius: 4px;
            max-height: 400px;
            overflow: auto;
        }
        .actions {
            margin-top: 12px;            
        }
        button {
            padding: 8px 16px;
            border: none;
            border-radius: 4px;
            cursor: pointer;
        }
        button[type="submit"] {
            background: #007BFF;
            color: #ffffff;
        }
        .download-button {
            background: #28A745;
            color: #ffffff;
            margin-left: 8px;
        }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>Intro to AI CSCE 4201 <br> Picture to Text Scanner</h1>
            <form method="POST" action="/upload" enctype="multipart/form-data">
                <input type="file" name="file" accept="image/*,.pdf">
                <button type="submit">Extract Text</button>
            </form>
            
            {% if pdf_ready %}
            <div class="actions">
                <form method="GET" action="/download">
                    <button type="submit" class="download-button">Download as PDF</button>
                </form>
            </div>
            {% endif %}
            
            <hr>
            <h3>Extracted Text:</h3>
            <pre>{{ text }}</pre>
        </div>
    </body>
</html>
"""

#If the program is ran on Windows in the command line/terminal, set the Tesseract command path
if platform.system() == "Windows":
    pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'
    
# Constant to minimize image size for processing, 2000 pixels on the longest side
MAXSIDE = 2000

#defintion for loading and normalizing image
def loadAndNormalize(path: Path) -> Image.Image:
    
    img = Image.open(path)
    img = img.convert("L")  # Convert to grayscale, taking color away to focus on text, makes it easier for OCR
    
    width, height = img.size
    scale = min(1.0, MAXSIDE / max(width, height)) # Scale factor to fit within MAXSIDE
    
    # Resize image if necessary
    if scale < 1.0:
        img = img.resize((int(width * scale), int(height * scale)), Image.LANCZOS)
        
    return img


# Defintion for soft variant of image preprocessing, makes the image cleared with small contrast boost
def softVariant(img: Image.Image) -> Image.Image:
    
    out = ImageEnhance.Contrast(img).enhance(1.5)  # Boost contrast
    out = out.filter(ImageFilter.MedianFilter(size=3))  # Apply median filter
    
    return out

# Deftinition for hard variant of image preprocessing, makes the image very clear with high contrast boost, and binarization
# Binarization is converting the image to pure black and white, removing all gray areas
def hardVariant(img: Image.Image) -> Image.Image:
    
    out = ImageEnhance.Contrast(img).enhance(2.2)  # Strong contrast boost
    out = out.filter(ImageFilter.MedianFilter(size = 3))  # Apply median filter
    out = out.point(lambda x: 255 if x > 160 else 0)  # Binarization
    
    return out

# Defintion for scoring text based on its content/clarity/correctness, heuristic scoring to determine quality of OCR result
def scoreText(text: str) -> float:
    
    if not text:
        return -math.inf  # Return negative infinity for empty text
    
    alnum = sum(char.isalnum() for char in text)                                # letters/digits count
    weird = sum((not char.isalnum()) and (not char.isspace()) for char in text) # weird characters count (punctuation, symbols, etc)
    total = len(text)                                                           # total characters count
    
    # calculate density of alphanumeric characters
    density = alnum / total
    
    # returning final score based on weighted factors, higher is better
    return alnum + 40 * density - 3 * weird

# Defintion for cleaning up text, removing dragging newlines, excessive spaces, unnecessary characters
def cleanText(text: str) -> str:
    text = text.replace("\x0c", "").strip()  # Remove form feed characters, clean edges

    return re.sub(r'[ \t]+', ' ', text)      # Replace multiple spaces/tabs with single space

# Defintion for OCR calculation
def ocrCalculate(path: str, lang: str = "eng") -> str:
    
    image = loadAndNormalize(Path(path))
    
    # Generate different preprocessed variants
    variants = [
        image,
        softVariant(image),
        hardVariant(image)
    ]
    
    configuration = [
        f"--oem 3 --psm 6 -l {lang}",  # Default configuration
        f"--oem 3 --psm 6 -l {lang}",  # Assume a single column of text
    ]
    
    bestText = ""
    bestScore = -math.inf
    
    # Perform OCR on each variant and select the best result based on scoring
    for variant in variants:
        for config in configuration:
            text = pytesseract.image_to_string(variant, config = config)
            currentScore = scoreText(text)
            if currentScore > bestScore:
                bestScore = currentScore
                bestText = text
    
    # If the best score is low, try resizing the image larger and re-running OCR
    if bestScore < 25:
        increase = image.resize((int(image.width * 1.5), int(image.height * 1.5)), Image.LANCZOS)
        
        # Re-evaluate OCR on the upscaled image
        for config in configuration:
            text2 = pytesseract.image_to_string(increase, config = config)
            currentScore2 = scoreText(text2)
            # If the new score is better, update best result
            if currentScore2 > bestScore:
                bestScore = currentScore2
                bestText = text2

    return cleanText(bestText)  # Return cleaned best text

# Definition for pdf creation for the extracted text
def makePDF(text: str, pdfFile: Path):
    
    # Create a PDF canvas
    c = canvas.Canvas(str(pdfFile), pagesize=letter)
    c.setFont("Helvetica", 16)
    y = 750  # Starting vertical position
    
    # Loop through each line of text and write to PDF
    for line in (text or "[EMPTY]").split("\n"):
        c.drawString(10, y, line)
        y -= 14  # Move down for next line
        if y < 40:  # Check for page overflow
            c.showPage()
            c.setFont("Helvetica", 16)
            y = 750
    c.save()
    
# Flask app initialization, where web server is made, upload is the route for file uploading
app = Flask(__name__)
UPLOAD_DIR = Path("uploads")
UPLOAD_DIR.mkdir(exist_ok = True)

# App route for home page, renders the HTML template listed above at start of this file
@app.get("/")
def Home():
    return render_template_string(HTML, text = "", pdf_ready = False)

# App route for file upload handling, this is where the OCR and PDF generation happens
@app.post("/upload")
def Upload():
    
    file = request.files.get("file")
    if not file or file.filename == "":
        return render_template_string(HTML, text = "No File Was Uploaded.", pdf_ready = False)
    
    # Save uploaded file to upload directory
    filename = file.filename
    path = UPLOAD_DIR / filename
    file.save(path)
    
    # Check file type from the tail extension from filename
    lower = filename.lower()
    
    # If the file is a PDF
    if lower.endswith(".pdf"):
      return render_template_string(HTML, text = "PDF File Type Not Supported For This Program.", pdf_ready = False)
  
    # Perform OCR on the uploaded image file
    extracted_text = ocrCalculate(str(path))
    
    # Generate PDF with the extracted text
    pdfPath = UPLOAD_DIR / "ExtractedTextOutput.pdf"
    makePDF(extracted_text, pdfPath)

    return render_template_string(HTML, text = extracted_text, pdf_ready = True)

# App route for downloading the generated PDF
@app.get("/download")
def Download():
    pdfPath = UPLOAD_DIR / "ExtractedTextOutput.pdf"
    if not pdfPath.exists():
        return "No PDF Was Made Available for Download, Sorry.", 404

    return send_file(pdfPath, as_attachment = True)

# Main called to run the Flask app, ****if this file is run directly**** (deployed on Render.com)
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(debug = True, port = port, host = "0.0.0.0")