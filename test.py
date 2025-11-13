# test.py  (CLI: image -> text using the same hybrid algorithm as connectTest.py)

from pathlib import Path
import sys

# Reuse the algorithm + pytesseract config from connectTest
from connectTest import ocr_hybrid

def main():
    # choose image path: CLI arg or default
    if len(sys.argv) > 1:
        img_path = Path(sys.argv[1])
    else:
        img_path = Path("sample.png")

    if not img_path.exists():
        raise FileNotFoundError(f"Image not found: {img_path.resolve()}")

    text = ocr_hybrid(str(img_path))
    print(text)

if __name__ == "__main__":
    main()
