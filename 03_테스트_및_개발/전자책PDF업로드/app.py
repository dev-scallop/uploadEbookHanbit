import os
import json
from io import BytesIO
from flask import Flask, render_template, request, jsonify, redirect, url_for
from werkzeug.utils import secure_filename

try:
    from pypdf import PdfReader
except Exception:
    # pypdf may be installed as PyPDF2 in older environments; prefer pypdf
    from PyPDF2 import PdfReader

BASE_DIR = os.path.dirname(__file__)
PUBLIC_DIR = os.path.join(BASE_DIR, 'public')
RULES_PATH = os.path.join(PUBLIC_DIR, 'rules.json')
UPLOAD_DIR = os.path.join(BASE_DIR, 'uploads')
os.makedirs(UPLOAD_DIR, exist_ok=True)

app = Flask(__name__)
app.config['MAX_CONTENT_LENGTH'] = 200 * 1024 * 1024  # safety ceiling (200MB)


def load_rules():
    try:
        with open(RULES_PATH, 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        return {}


def save_rules(rules):
    with open(RULES_PATH, 'w', encoding='utf-8') as f:
        json.dump(rules, f, ensure_ascii=False, indent=2)


def points_to_mm(pt):
    return (pt / 72.0) * 25.4


@app.route('/')
def index():
    rules = load_rules()
    return render_template('index.html', rules=rules, errors=None, report=None)


@app.route('/upload', methods=['POST'])
def upload_form():
    # Handles regular form submission and renders results
    result = handle_file_from_request(request)
    rules = load_rules()
    if result.get('errors'):
        return render_template('index.html', rules=rules, errors=result['errors'], report=None)
    else:
        return render_template('index.html', rules=rules, errors=None, report=result.get('report'))


@app.route('/api/upload', methods=['POST'])
def api_upload():
    # Returns JSON (used if client wants AJAX)
    result = handle_file_from_request(request)
    if result.get('errors'):
        return jsonify({ 'errors': result['errors'] }), 400
    return jsonify({ 'message': 'OK', 'report': result.get('report', {}) })


def handle_file_from_request(req):
    rules = load_rules()
    if 'file' not in req.files:
        return { 'errors': [ { 'type': 'nofile', 'message': '파일이 업로드되지 않았습니다.' } ] }

    f = req.files['file']
    filename = secure_filename(f.filename or 'uploaded.pdf')
    data = f.read()

    errors = []
    size_mb = len(data) / 1024.0 / 1024.0
    max_mb = rules.get('maxFileSizeMB', 20)
    if size_mb > max_mb:
        errors.append({ 'type': 'size', 'message': f'파일 크기 초과: {size_mb:.2f}MB > {max_mb}MB' })

    # Try to parse PDF
    try:
        reader = PdfReader(BytesIO(data))

        # encryption
        is_encrypted = getattr(reader, 'is_encrypted', False)
        if is_encrypted and rules.get('disallowEncrypted', True):
            errors.append({ 'type': 'encrypted', 'message': '암호화된 PDF 또는 권한 제한됨' })

        # page count
        num_pages = len(reader.pages)
        if rules.get('minPages') and num_pages < rules.get('minPages'):
            errors.append({ 'type': 'pages', 'message': f'페이지 수가 너무 적음: {num_pages} < {rules.get("minPages")}' })
        if rules.get('maxPages') and num_pages > rules.get('maxPages'):
            errors.append({ 'type': 'pages', 'message': f'페이지 수가 너무 많음: {num_pages} > {rules.get("maxPages")}' })

        # page size (first page)
        if num_pages >= 1:
            page = reader.pages[0]
            try:
                # pypdf page.mediabox has width and height attributes
                width_pt = float(page.mediabox.width)
                height_pt = float(page.mediabox.height)
            except Exception:
                # fallback if attributes missing
                width_pt = float(page.mediabox.upper_right[0] - page.mediabox.lower_left[0])
                height_pt = float(page.mediabox.upper_right[1] - page.mediabox.lower_left[1])

            width_mm = points_to_mm(width_pt)
            height_mm = points_to_mm(height_pt)

            pageSize = rules.get('pageSize')
            if pageSize:
                wantW = pageSize.get('widthMm')
                wantH = pageSize.get('heightMm')
                tol = pageSize.get('toleranceMm', 5)
                if abs(width_mm - wantW) > tol or abs(height_mm - wantH) > tol:
                    errors.append({ 'type': 'pagesize',
                                    'message': f'페이지 사이즈 불일치: {round(width_mm)}x{round(height_mm)}mm (허용오차 {tol}mm). 기대: {wantW}x{wantH}mm' })

        # metadata
        req_meta = rules.get('requireMetadata', []) or []
        if req_meta:
            meta = getattr(reader, 'metadata', None)
            info = {}
            if meta:
                # pypdf metadata keys often start with '/'
                for k, v in meta.items():
                    key = k.strip('/') if isinstance(k, str) else str(k)
                    info[key] = v
            for key in req_meta:
                found = False
                for k, v in info.items():
                    if k.lower() == key.lower() and v:
                        found = True
                        break
                if not found:
                    errors.append({ 'type': 'metadata', 'message': f'메타데이터 누락: {key}' })

        # If no parse errors, save file
        if not errors:
            save_path = os.path.join(UPLOAD_DIR, filename)
            with open(save_path, 'wb') as out:
                out.write(data)

            report = { 'numPages': num_pages, 'widthMm': round(width_mm), 'heightMm': round(height_mm) }
            return { 'report': report }

    except Exception as e:
        errors.append({ 'type': 'parse', 'message': 'PDF 파싱 실패: 파일이 손상되었거나 지원되지 않는 형식일 수 있습니다. ' + str(e) })

    return { 'errors': errors }


@app.route('/admin', methods=['GET', 'POST'])
def admin():
    if request.method == 'POST':
        # Expect JSON body or form field 'rules'
        if request.is_json:
            new_rules = request.get_json()
        else:
            raw = request.form.get('rules')
            try:
                new_rules = json.loads(raw)
            except Exception:
                return 'Invalid JSON', 400
        save_rules(new_rules)
        return redirect(url_for('index'))

    rules = load_rules()
    # show raw JSON textarea for editing
    return render_template('admin.html', rules=json.dumps(rules, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    app.run(debug=True, port=5000)
