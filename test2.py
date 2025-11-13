# test2.py  (CLI: image -> text + PDF)

from pathlib import Path
import sys

from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas

from connectTest import ocr_hybrid  # reuse hybrid OCR & tesseract config

def make_pdf(text: str, pdf_file: Path):
    c = canvas.Canvas(str(pdf_file), pagesize=letter)
    c.setFont("Helvetica", 10)
    y = 750
    line_height = 12

    for line in (text or "[EMPTY]").split("\n"):
        c.drawString(10, y, line)
        y -= line_height
        if y < 40:
            c.showPage()
            c.setFont("Helvetica", 10)
            y = 750
    c.save()

def main():
    # image path
    if len(sys.argv) > 1:
        img_path = Path(sys.argv[1])
    else:
        img_path = Path("sample.png")

    # output pdf path
    if len(sys.argv) > 2:
        pdf_path = Path(sys.argv[2])
    else:
        pdf_path = Path("output.pdf")

    if not img_path.exists():
        raise FileNotFoundError(f"Image not found: {img_path.resolve()}")

    text = ocr_hybrid(str(img_path))
    make_pdf(text, pdf_path)

    print(f"OCR complete. Text length = {len(text)} characters.")
    print(f"PDF written to: {pdf_path.resolve()}")

if __name__ == "__main__":
    main()
