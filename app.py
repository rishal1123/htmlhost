from flask import Flask, request, redirect, url_for, send_from_directory, render_template_string
import os

app = Flask(__name__)
UPLOAD_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "uploads")
os.makedirs(UPLOAD_DIR, exist_ok=True)

INDEX_HTML = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>HTML Host</title>
    <style>
        * { box-sizing: border-box; margin: 0; padding: 0; }
        body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif; background: #0f1117; color: #e1e4e8; min-height: 100vh; padding: 2rem; }
        .container { max-width: 700px; margin: 0 auto; }
        h1 { font-size: 1.8rem; margin-bottom: 1.5rem; color: #fff; }
        .upload-box { background: #1c1f2b; border: 2px dashed #30363d; border-radius: 12px; padding: 2rem; text-align: center; margin-bottom: 2rem; transition: border-color .2s; }
        .upload-box:hover { border-color: #58a6ff; }
        .upload-box input[type=file] { margin-bottom: 1rem; }
        button { background: #238636; color: #fff; border: none; padding: .6rem 1.4rem; border-radius: 6px; cursor: pointer; font-size: .95rem; }
        button:hover { background: #2ea043; }
        .msg { padding: .8rem 1rem; border-radius: 8px; margin-bottom: 1.5rem; }
        .msg.success { background: #1b3a2d; color: #56d364; }
        .msg.error { background: #3d1f1f; color: #f85149; }
        h2 { font-size: 1.3rem; margin-bottom: .8rem; color: #c9d1d9; }
        ul { list-style: none; }
        li { padding: .5rem 0; border-bottom: 1px solid #21262d; display: flex; justify-content: space-between; align-items: center; }
        li:last-child { border-bottom: none; }
        a { color: #58a6ff; text-decoration: none; }
        a:hover { text-decoration: underline; }
        .delete-btn { background: #da3633; padding: .3rem .8rem; font-size: .8rem; border-radius: 4px; }
        .delete-btn:hover { background: #f85149; }
        .empty { color: #8b949e; font-style: italic; }
    </style>
</head>
<body>
    <div class="container">
        <h1>HTML Host</h1>
        {% if msg %}
        <div class="msg {{ msg_type }}">{{ msg }}</div>
        {% endif %}
        <div class="upload-box">
            <form method="POST" action="/upload" enctype="multipart/form-data">
                <input type="file" name="file" accept=".html,.htm" required><br>
                <button type="submit">Upload</button>
            </form>
        </div>
        <h2>Hosted Files</h2>
        {% if files %}
        <ul>
            {% for f in files %}
            <li>
                <a href="/view/{{ f }}" target="_blank">{{ f }}</a>
                <form method="POST" action="/delete/{{ f }}" style="display:inline">
                    <button class="delete-btn" type="submit">Delete</button>
                </form>
            </li>
            {% endfor %}
        </ul>
        {% else %}
        <p class="empty">No files uploaded yet.</p>
        {% endif %}
    </div>
</body>
</html>
"""


@app.route("/")
def index():
    files = sorted(f for f in os.listdir(UPLOAD_DIR) if f.endswith((".html", ".htm")))
    return render_template_string(INDEX_HTML, files=files, msg=request.args.get("msg"), msg_type=request.args.get("msg_type", "success"))


@app.route("/upload", methods=["POST"])
def upload():
    file = request.files.get("file")
    if not file or file.filename == "":
        return redirect(url_for("index", msg="No file selected.", msg_type="error"))

    filename = os.path.basename(file.filename)
    if not filename.endswith((".html", ".htm")):
        return redirect(url_for("index", msg="Only .html/.htm files allowed.", msg_type="error"))

    file.save(os.path.join(UPLOAD_DIR, filename))
    return redirect(url_for("index", msg=f"Uploaded {filename} successfully.", msg_type="success"))


@app.route("/view/<path:filename>")
def view(filename):
    return send_from_directory(UPLOAD_DIR, filename)


@app.route("/delete/<path:filename>", methods=["POST"])
def delete(filename):
    filepath = os.path.join(UPLOAD_DIR, os.path.basename(filename))
    if os.path.exists(filepath):
        os.remove(filepath)
        return redirect(url_for("index", msg=f"Deleted {filename}.", msg_type="success"))
    return redirect(url_for("index", msg="File not found.", msg_type="error"))


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
