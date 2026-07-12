import os
import sys
from pathlib import Path
from flask import Flask, render_template_string, request, send_file, flash
from werkzeug.utils import secure_filename

_BASE = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_BASE))

from pipeline.batch_processor import process_single_pdf

app = Flask(__name__)
app.secret_key = os.urandom(24).hex()

UPLOAD_DIR = _BASE / "uploads"
OUTPUT_DIR = _BASE / "results"
UPLOAD_DIR.mkdir(exist_ok=True)
OUTPUT_DIR.mkdir(exist_ok=True)

FORMATS = ["xlsx", "json", "txt", "xml"]

HTML = """<!doctype html>
<title>PDF Data Extractor</title>
<style>
  *{box-sizing:border-box}
  body{font-family:system-ui,sans-serif;max-width:720px;margin:3rem auto;padding:0 1rem;color:#1e293b}
  h2{font-weight:600}
  .box{border:2px dashed #cbd5e1;padding:2.5rem;text-align:center;border-radius:16px;background:#f8fafc}
  input[type=file],select{margin:1rem 0;padding:.4rem}
  select{border:1px solid #cbd5e1;border-radius:8px;background:#fff;font-size:.9rem}
  button{background:#2563eb;color:#fff;border:none;padding:.7rem 2rem;border-radius:10px;font-size:1rem;cursor:pointer}
  button:hover{background:#1d4ed8}
  .flash{margin:1rem 0;padding:.8rem 1.2rem;border-radius:10px}
  .flash.success{background:#dcfce7;border:1px solid #86efac}
  .flash.err{background:#fee2e2;border:1px solid #fca5a5}
  ul{list-style:none;padding:0;margin:1rem 0}
  li{padding:.6rem 0;border-bottom:1px solid #e2e8f0;display:flex;justify-content:space-between;align-items:center}
  a{color:#2563eb;text-decoration:none;font-weight:500}
  .tag{font-size:.75rem;background:#e2e8f0;padding:.2rem .6rem;border-radius:20px;color:#475569}
</style>
<h2>PDF Data Extractor</h2>
<div class=box>
  <form method=post enctype=multipart/form-data>
    <input type=file name=file accept=.pdf required><br>
    <label>Format:
    <select name=format>
      {% for f in formats %}
      <option value="{{ f }}" {{ 'selected' if f == 'xlsx' else '' }}>{{ f.upper() }}</option>
      {% endfor %}
    </select>
    </label><br>
    <button type=submit>Upload & Extract</button>
  </form>
</div>
{% for cat, msg in get_flashed_messages(with_categories=true) %}
  <div class="flash {{ cat }}">{{ msg }}</div>
{% endfor %}
{% if files %}
<h3>Extracted files</h3>
<ul>
{% for f in files %}
  <li><span>{{ f }}</span> <a href="/download/{{ f }}">Download</a></li>
{% endfor %}
</ul>
{% endif %}"""


def _find_results():
    exts = ["*.xlsx", "*.json", "*.txt", "*.xml"]
    files = []
    for ext in exts:
        files.extend(OUTPUT_DIR.glob(ext))
    return sorted((p.name for p in files), reverse=True)


@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        f = request.files.get("file")
        fmt = request.form.get("format", "xlsx")

        if not f or not f.filename.lower().endswith(".pdf"):
            flash("Please upload a PDF file", "err")
            return render_template_string(HTML, formats=FORMATS, files=_find_results())

        name = secure_filename(f.filename)
        in_path = UPLOAD_DIR / name
        f.save(str(in_path))

        try:
            process_single_pdf(str(in_path), str(OUTPUT_DIR), fmt=fmt)
            flash(f"Done: {name} ({fmt})", "success")
        except Exception as e:
            flash(f"Error: {e}", "err")

    return render_template_string(HTML, formats=FORMATS, files=_find_results())


@app.route("/download/<name>")
def download(name: str):
    return send_file(str(OUTPUT_DIR / name), as_attachment=True)


def main():
    app.run(host="0.0.0.0", port=5000, debug=False)


if __name__ == "__main__":
    main()
