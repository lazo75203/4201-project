from flask import Flask, request, send_file, render_template_string
from pathlib import Path
from PIL import Image, ImageEnhance, ImageFilter
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
import pytesseract
import platform
import os
import math
import re

# ----------------- YOUR HTML LAYOUT (UNCHANGED) -----------------
HTML = """
<!doctype html>
<html>
  <head>
    <title>Intro to AI CSCE 4201 Picture to Text Scanner</title>
    <style>
      body {
        margin: 0;
        font-family: Arial, sans-serif;
        background: #f5f5f5;
        display: flex;
        align-items: center;      /* vertical center */
        justify-content: center;  /* horizontal center */
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
        text-align: left;       /* keep OCR text readable */
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
      <h1>Intro to AI CSCE 4201<br> Picture to Text Scanner</h1>
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



if platform.system() == "Windows":
    # Local dev
    pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"



MAX_SIDE = 2000  

def _load_and_normalize(path: Path) -> Image.Image:
    img = Image.open(path)
    img = img.convert("L") 

    
    w, h = img.size
    scale = min(1.0, MAX_SIDE / max(w, h))
    if scale < 1.0:
        img = img.resize((int(w * scale), int(h * scale)), Image.LANCZOS)

    return img

def _soft_variant(img: Image.Image) -> Image.Image:
    out = ImageEnhance.Contrast(img).enhance(1.5)
    out = out.filter(ImageFilter.MedianFilter())
    return out

def _hard_variant(img: Image.Image) -> Image.Image:
    out = ImageEnhance.Contrast(img).enhance(2.2)
    out = out.filter(ImageFilter.MedianFilter(size=3))
    out = out.point(lambda x: 255 if x > 160 else 0)
    return out

def _score_text(text: str) -> float:
    """
    Heuristic scoring algorithm:
      - reward letters/digits
      - penalize weird symbols
      - tiny outputs get a small penalty
    """
    alnum = sum(ch.isalnum() for ch in text)
    weird = sum((not ch.isalnum()) and (not ch.isspace()) for ch in text)
    length_penalty = 0.1 * len(text)
    return alnum - 2 * weird + 0.01 * length_penalty

def _clean_text(text: str) -> str:
    text = text.replace("\x0c", "").strip()
    return re.sub(r"[ \t]+", " ", text)

def ocr_hybrid(path: str, lang: str = "eng") -> str:
    """
    Hybrid OCR:
      1) normalize image
      2) run Tesseract on soft + hard variants
      3) score & pick best
      4) if score is low, upscale once and retry
    """
    base = _load_and_normalize(Path(path))

    variants = [
        _soft_variant(base),
        _hard_variant(base),
    ]

    config = f"--oem 3 --psm 6 -l {lang}"

    best_text = ""
    best_score = -math.inf

    # Pass 1 & 2: different preprocessings
    for v in variants:
        txt = pytesseract.image_to_string(v, config=config)
        s = _score_text(txt)
        if s > best_score:
            best_score, best_text = s, txt

    # Optional escalation: if still weak, upscale once and retry
    if best_score < 25:
        up = base.resize(
            (int(base.width * 1.5), int(base.height * 1.5)),
            Image.LANCZOS,
        )
        txt2 = pytesseract.image_to_string(up, config=config)
        s2 = _score_text(txt2)
        if s2 > best_score:
            best_score, best_text = s2, txt2

    return _clean_text(best_text)

# ----------------- PDF WRITER -----------------

def make_pdf(text: str, pdf_file: Path):
    c = canvas.Canvas(str(pdf_file), pagesize=letter)
    c.setFont("Helvetica", 10)
    y = 750
    for line in (text or "[EMPTY]").split("\n"):
        c.drawString(10, y, line)
        y -= 12
        if y < 40:
            c.showPage()
            c.setFont("Helvetica", 10)
            y = 750
    c.save()

# ----------------- FLASK APP -----------------

app = Flask(__name__)
UPLOAD_DIR = Path("uploads")
UPLOAD_DIR.mkdir(exist_ok=True)

@app.get("/")
def home():
    # initial page, no text yet
    return render_template_string(HTML, text="")

@app.post("/upload")
def upload():
    f = request.files.get("file")
    if not f or f.filename == "":
        return render_template_string(HTML, text="No file uploaded.")

    filename = f.filename
    path = UPLOAD_DIR / filename
    f.save(path)

    # basic file type gate: images only for now
    lower = filename.lower()
    if lower.endswith(".pdf"):
        # layout unchanged; just inform via text area
        return render_template_string(HTML, text="PDF input not supported yet. Please upload an image (jpg, png, etc.).")

    # run hybrid OCR
    text = ocr_hybrid(str(path))

    # write PDF in case you want /download or future link
    pdf_path = UPLOAD_DIR / "text_output.pdf"
    make_pdf(text, pdf_path)

    return render_template_string(HTML, text=text)

@app.get("/download")
def download():
    pdf_path = UPLOAD_DIR / "text_output.pdf"
    if not pdf_path.exists():
        # simple fallback: no pdf yet
        return "No PDF generated yet.", 404
    return send_file(pdf_path, as_attachment=True)

if __name__ == "__main__":
    port = int(os.environ.get("PORT", "5000"))
    app.run(host="0.0.0.0", port=port)
