import pytesseract
from PIL import Image, ImageEnhance, ImageFilter
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas

#change this line to your filepath
pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"

# preprocess the image to improve recognition 
def preprocess_image(image_path):
    # Open the image
    image = Image.open(image_path)
    
    # Convert to grayscale
    image = image.convert('L')
    
    # Enhance the contrast
    enhancer = ImageEnhance.Contrast(image)
    image = enhancer.enhance(2)  # Increase contrast to make text more prominent
    
    # Apply median filter
    image = image.filter(ImageFilter.MedianFilter())
    
    return image

# Function to extract text from the image using Tesseract OCR
def extract_text_from_image(image_path):
    # Preprocess the image to improve text extraction
    image = preprocess_image(image_path)
    
    # Extract text using Tesseract OCR
    text = pytesseract.image_to_string(image)
    return text

# Function to create a PDF with the extracted text
def create_pdf_from_text(text, output_pdf_path):
    # Create a PDF 
    c = canvas.Canvas(output_pdf_path, pagesize=letter)
    
    # setting font and size
    c.setFont("Helvetica", 10)
    
    # Start writing text at a specific position (x, y)
    y_position = 750  # Start near top of page
    line_height = 12  # Space between lines
    
    # Split the text into lines and write them to the PDF
    for line in text.split('\n'):
        c.drawString(10, y_position, line)  # Write the text line
        y_position -= line_height  # Move down for the next line
        
        # If the text goes past the page, create a new page
        if y_position < 40:
            c.showPage()  # Create a new page
            c.setFont("Helvetica", 10)  # Reset font on the new page
            y_position = 750  # Reset to top of new page

    # Save the PDF
    c.save()

# Main function to process the image and generate the PDF
def image_to_pdf_with_text(image_path, output_pdf_path):
    # Extract text from the image
    extracted_text = extract_text_from_image(image_path)
    
    # Create a PDF with the extracted text
    create_pdf_from_text(extracted_text, output_pdf_path)

# Usage
image_to_pdf_with_text('sample.png', 'output.pdf')#first input is image path second is document name for output
