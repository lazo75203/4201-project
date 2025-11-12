# test.py
from pathlib import Path
from PIL import Image, ImageEnhance, ImageFilter
import pytesseract, sys, platform

# Windows path; safe no-op on other OSes
if platform.system() == "Windows":
    pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"

def preprocess(p: Path) -> Image.Image:
    img = Image.open(p).convert("L")
    w, h = img.size
    img = img.resize((w*2, h*2))
    img = ImageEnhance.Contrast(img).enhance(2.0)
    img = img.filter(ImageFilter.MedianFilter())
    return img.point(lambda x: 255 if x > 170 else 0)

def ocr(p: Path) -> str:
    img = preprocess(p)
    return pytesseract.image_to_string(img, config="--oem 3 --psm 6 -l eng")

# pick image: arg1 or test.png or sample.png
candidates = [Path(sys.argv[1])] if len(sys.argv) > 1 else []
candidates += [Path("test.png"), Path("sample.png")]
img_path = next((p for p in candidates if p.exists()), None)
if not img_path:
    raise FileNotFoundError("Provide an image or place test.png/sample.png next to test.py")

text = ocr(img_path)
print(text.replace("\x0c", "").strip())
