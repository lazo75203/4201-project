from flask import Flask, request, jsonify, send_file
import pytesseract
from PIL import Image, ImageEnhance, ImageFilter
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
import os
#THIS IS STILL IN TESTING PHASE BUT WILL BE IMPLEMENTED IN THE NEXT STEP
app = Flask(__name__)
pytesseract.pytesseract.tesseract_cmd = r"/usr/local/bin/tesseract"

def fix_image(img_path):
    img = Image.open(img_path)
    img = img.convert('L')
    enhance = ImageEnhance.Contrast(img)
    img = enhance.enhance(2)
    img = img.filter(ImageFilter.MedianFilter())
    return img

def get_text(img_path):
    img = fix_image(img_path)
    text = pytesseract.image_to_string(img)
    return text

def make_pdf(text, pdf_file):
    c = canvas.Canvas(pdf_file, pagesize=letter)
    c.setFont("Helvetica", 10)
    y = 750
    for line in text.split('\n'):
        c.drawString(10, y, line)
        y -= 12
        if y < 40:
            c.showPage()
            c.setFont("Helvetica", 10)
            y = 750
    c.save()

@app.route('/')
def home():
    return "OCR App Running!"

@app.route('/upload', methods=['POST'])
def upload():
    if 'image' not in request.files:
        return jsonify({'error': 'No image found'}), 400
    
    file = request.files['image']
    os.makedirs('uploads', exist_ok=True)
    path = os.path.join('uploads', file.filename)
    file.save(path)

    text = get_text(path)
    pdf_path = os.path.join('uploads', 'text_output.pdf')
    make_pdf(text, pdf_path)

    return jsonify({
        'msg': 'ok!',
        'text': text,
        'pdf': '/download'
    })

@app.route('/download')
def download():
    return send_file('uploads/text_output.pdf', as_attachment=True)

if __name__ == '__main__':
    app.run(debug=True)
