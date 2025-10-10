from PIL import Image
import pytesseract

pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"

img = Image.open("sample.png")#image path

img = img.convert("L") #convert to greyscale for better reults

text = pytesseract.image_to_string(img)

print(text.replace("\x0c", "").strip())