# All libraries and packages used listed:

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
    </style>
  </head>
  <body>
    <div class="container">
      <h1>Intro to AI CSCE 4201 <br> Picture to Text Scanner</h1>
      <form method="POST" action="/upload" enctype="multipart/form-data">
        <input type="file" name="file" accept="image/*,.pdf">
        <button type="submit">Extract Text</button>
      </form>
      <hr>
      <h3>Extracted Text:</h3>
      <pre>{{ text }}</pre>
    </div>
  </body>
</html>
"""




# If the program is ran on Windows in the command line/terminal, set the Tesseract command path
if platform.system() == "Windows":
  
    pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"


# Constant to minimize image size for OCR processing, 2000 pixels on the longest side
MAX_SIDE = 2000  


# defintion for loading and normalizing image
def _load_and_normalize(path: Path) -> Image.Image:
    img = Image.open(path)
    img = img.convert("L")  # Convert to grayscale, taking color away to focus on text, makes it easier for OCR

    
    width, height = img.size
    scale = min(1.0, MAX_SIDE / max(width, height)) # Scale factor to fit within MAX_SIDE
    
    # Resize image if necessary
    if scale < 1.0:
        img = img.resize((int(width * scale), int(height * scale)), Image.LANCZOS)

    return img


# definition for soft variant of image preprocessing, pretty much makes the image clearer with small contrast boost
def _soft_variant(img: Image.Image) -> Image.Image:
  
    # Soft variant formula below: mild contrast + median filter
    out = ImageEnhance.Contrast(img).enhance(1.5)
    out = out.filter(ImageFilter.MedianFilter())
    return out


# definition for hard variant of image preprocessing, strong contrast boost, and middle amount of contrast, then binarization
# binarization converts pixels to either black or white based on its amount of lightness/darkness
def _hard_variant(img: Image.Image) -> Image.Image:
  
    # Hard variant formula below: strong contrast + median filter + binarization
    out = ImageEnhance.Contrast(img).enhance(2.2)
    out = out.filter(ImageFilter.MedianFilter(size=3))
    out = out.point(lambda x: 255 if x > 160 else 0)
    return out


# definition for scoring text based on its content, heuristic scoring to determine quality of results
def _score_text(text: str) -> float:
  
    alnum = sum(ch.isalnum() for ch in text)                              # alphanumeric characters counting
    weird = sum((not ch.isalnum()) and (not ch.isspace()) for ch in text) # weird symbols counting
    length_penalty = 0.1 * len(text)                                      # some points are taken off if text is too long
    return alnum - 2 * weird + 0.01 * length_penalty


# definition for cleaning text (removing unnecessary characters and spaces)
def _clean_text(text: str) -> str:
  
    text = text.replace("\x0c", "").strip()     
    return re.sub(r"[ \t]+", " ", text)         # replace long stretches of spaces/tabs with single space


# definition for the OCR calculation, called hybrid becuase it is the middle line between accuracy and speed
def ocr_hybrid(path: str, lang: str = "eng") -> str:
   
   # Load and normalize image
    base = _load_and_normalize(Path(path))

    # Generate preprocessing variants, soft and hard, soft being more gentle on image, hard being more aggressive
    variants = [
        _soft_variant(base),
        _hard_variant(base),
    ]

    # Tesseract library configuration for OCR engine and page segmentation mode
    config = f"--oem 3 --psm 6 -l {lang}"

    best_text = ""
    best_score = -math.inf

    # For loop through each variant, perform OCR and score the results, keeping the best one, heuristic approach to improve accuracy
    for v in variants:
        txt = pytesseract.image_to_string(v, config=config)
        s = _score_text(txt)
        if s > best_score:
            best_score, best_text = s, txt

    # If statement to check if the best score is below a certain threshold, indicating sub-par OCR results
    if best_score < 25:   # if score is below threshold, try upscaling the base image and re-running OCR
        up = base.resize(
            (int(base.width * 1.5), int(base.height * 1.5)),
            Image.LANCZOS,
        )
        txt2 = pytesseract.image_to_string(up, config=config)
        s2 = _score_text(txt2)
        if s2 > best_score:
            best_score, best_text = s2, txt2

    return _clean_text(best_text)

# definition for creating PDF from extracted text, generates a simple PDF document with the extracted text content for upload folder
def make_pdf(text: str, pdf_file: Path):
  
    # Create a simple PDF with the extracted text
    c = canvas.Canvas(str(pdf_file), pagesize=letter)
    c.setFont("Helvetica", 10)
    y = 750                                           # vertical position for text placement
    
    # for loop to write each line of text to the PDF, handling page breaks as necessary
    for line in (text or "[EMPTY]").split("\n"):
        c.drawString(10, y, line)
        y -= 12
        if y < 40:                                    # check if a new page is needed because of spacing                
            c.showPage()
            c.setFont("Helvetica", 10)
            y = 750
    c.save()


# Flask app initialization, where the web server is made, upload is the route for file uploading 
app = Flask(__name__)
UPLOAD_DIR = Path("uploads")
UPLOAD_DIR.mkdir(exist_ok=True)

# route for home page, renders HTML template listed above at start of this file
@app.get("/")
def home():
  
    # Basic home page rendering with empty text so there's something to show when starting
    return render_template_string(HTML, text="")

# route for file upload handling, this is where the OCR and PDF generation happens
@app.post("/upload")
def upload():
  
    f = request.files.get("file")
    # if there isn't a file uploaded, user is shown message letting them know
    if not f or f.filename == "":
        return render_template_string(HTML, text="No file uploaded.")

    # Save uploaded file to upload directory
    filename = f.filename
    path = UPLOAD_DIR / filename
    f.save(path)

    # Check file type from the tail extension from filename
    lower = filename.lower()
    if lower.endswith(".pdf"):
      
        # if the file is a PDF, return message letting the user know that PDFs are not allowed
        return render_template_string(HTML, text="PDF not allowed. Please upload an image (jpg, png, etc.).")

    # Apply the OCR hybrid function 
    text = ocr_hybrid(str(path))

    # PDF made and saved in upload directory
    pdf_path = UPLOAD_DIR / "text_output.pdf"
    make_pdf(text, pdf_path)

    return render_template_string(HTML, text=text)

# route for downloading the generated PDF file, gives user the option to download the PDF after main purpose of the text extraction is done
@app.get("/download")

# definition for downloading the generated PDF file
def download():
  
    pdf_path = UPLOAD_DIR / "text_output.pdf"
    if not pdf_path.exists():
        # if the PDF doesn't exist through up the 404 error
        return "No PDF generated yet.", 404
    return send_file(pdf_path, as_attachment=True)


# main call to run the Flask app, ****if this file is run directly**** (aiming to deploy on Render.com)
if __name__ == "__main__":
    port = int(os.environ.get("PORT", "5000"))
    app.run(host="0.0.0.0", port=port)
