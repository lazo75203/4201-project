# connectTest.py
import os
from flask import Flask, request, render_template_string
from PIL import Image
import numpy as np
import cv2
import pytesseract

# If Tesseract isn’t on PATH on Windows, uncomment and set the path:
# pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"

HTML = """
<!doctype html>
<title>OCR Demo</title>
<h1>OCR Demo</h1>
<form method="POST" action="/upload" enctype="multipart/form-data">
  <input type="file" name="file" accept="image/*,.pdf">
  <button type="submit">Extract Text</button>
</form>
<hr>
<h3>OCR Text</h3>
<pre>{{ text }}</pre>
"""

app = Flask(__name__)

def _bytes_to_mat(b: bytes) -> np.ndarray:
    arr = np.frombuffer(b, dtype=np.uint8)
    img = cv2.imdecode(arr, cv2.IMREAD_COLOR)
    if img is None:
        raise ValueError("Unable to decode image")
    return img

def _preprocess(mat: np.ndarray) -> np.ndarray:
    g = cv2.cvtColor(mat, cv2.COLOR_BGR2GRAY)
    h, w = g.shape
    if max(h, w) < 1200:
        g = cv2.resize(g, None, fx=2.0, fy=2.0, interpolation=cv2.INTER_CUBIC)
    g = cv2.fastNlMeansDenoising(g, h=7, templateWindowSize=7, searchWindowSize=21)
    thr = cv2.adaptiveThreshold(
        g, 255,
        cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
        cv2.THRESH_BINARY, 31, 10
    )
    return thr

@app.get("/")
def index():
    return render_template_string(HTML, text="")

@app.post("/upload")
def upload():
    f = request.files.get("file")
    if not f or f.filename == "":
        return render_template_string(HTML, text="ERROR: no file provided")

    data = f.read()

    try:
        mat = _bytes_to_mat(data)
        proc = _preprocess(mat)
        pil = Image.fromarray(proc)
        text = pytesseract.image_to_string(
            pil, lang="eng", config="--oem 3 --psm 6"
        ).strip()
        if not text:
            text = "(no text detected)"
        return render_template_string(HTML, text=f"Uploaded: {f.filename}\n\n{text}")
    except Exception as e:
        return render_template_string(HTML, text=f"ERROR: {e}")

if __name__ == "__main__":
    print("Serving on http://127.0.0.1:5000/")
    app.run(host="127.0.0.1", port=5000, debug=True)
