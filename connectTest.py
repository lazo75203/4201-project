# connectTest.py  — sanity UI
from flask import Flask, request, render_template_string
from pathlib import Path

app = Flask(__name__)

PAGE = """
<!doctype html>
<title>OCR Demo</title>
<h2>OCR Demo</h2>
<form action="/upload" method="post" enctype="multipart/form-data">
  <input type="file" name="image" accept="image/*">
  <button type="submit">Extract Text</button>
</form>
{% if text is defined %}
<hr><h3>OCR Text</h3>
<pre style="white-space:pre-wrap">{{ text }}</pre>
{% endif %}
"""

@app.get("/health")
def health():
    return "OK"

@app.get("/")
def home():
    return render_template_string(PAGE)

@app.post("/upload")
def upload():
    f = request.files.get("image")
    if not f:
        return render_template_string(PAGE, text="No file uploaded.")
    # echo filename only, on purpose (no OCR yet)
    return render_template_string(PAGE, text=f"Uploaded: {f.filename}")

if __name__ == "__main__":
    print("RUNNING FROM:", __file__)
    app.run(debug=True)
