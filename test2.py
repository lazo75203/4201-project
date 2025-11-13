# library and path imports for PDF generation

from pathlib import Path
import sys                      # for command-line arguments

from reportlab.lib.pagesizes import letter  # standard letter size from reportlab
from reportlab.pdfgen import canvas         # canvas for PDF creation from reportlab

from connectTest import ocr_hybrid  # importing the OCR function from connectTest module

# definition for creating PDF from extracted text,
def make_pdf(text: str, pdf_file: Path):
  
    # Creates a simple PDF with the extracted text
    c = canvas.Canvas(str(pdf_file), pagesize=letter)
    c.setFont("Helvetica", 10)
    y = 750                                           # vertical positioning 
    
    # looping through each line of text to write to the PDF
    for line in (text or "[EMPTY]").split("\n"):
        c.drawString(10, y, line)
        y -= 12
        if y < 40:                                    # check if a new page is needed because of spacing                
            c.showPage()
            c.setFont("Helvetica", 10)
            y = 750
    c.save()


# main function to handle command-line arguments and execute OCR and PDF generation
def main():
    # if there is a first command-line argument, use it as the image path
    if len(sys.argv) > 1:
        img_path = Path(sys.argv[1])
    else:
        img_path = Path("sample.png")

    # if there is a second command-line argument, use it as the PDF output path
    if len(sys.argv) > 2:
        pdf_path = Path(sys.argv[2])
    else:
        pdf_path = Path("output.pdf")

    # check if the image file exists, if it isn't, raise a FileNotFoundError
    if not img_path.exists():
        raise FileNotFoundError(f"Image not found: {img_path.resolve()}")

    text = ocr_hybrid(str(img_path))
    make_pdf(text, pdf_path)

    # print statements to indicate finish of OCR and PDF
    print(f"OCR complete. Text length = {len(text)} characters.")
    print(f"PDF written to: {pdf_path.resolve()}")

# main call to execute the main function
if __name__ == "__main__":
    main()
