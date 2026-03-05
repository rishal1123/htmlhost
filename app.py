from flask import Flask, request, redirect, url_for, send_from_directory, render_template_string, session
from werkzeug.security import generate_password_hash, check_password_hash
from functools import wraps
import os
import json
import secrets
import re
import shutil

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", secrets.token_hex(32))

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "data")
UPLOAD_DIR = os.path.join(BASE_DIR, "uploads")
USERS_FILE = os.path.join(DATA_DIR, "users.json")
SETTINGS_FILE = os.path.join(DATA_DIR, "settings.json")
os.makedirs(UPLOAD_DIR, exist_ok=True)
os.makedirs(DATA_DIR, exist_ok=True)

DEFAULT_EXTENSIONS = [".html", ".htm"]

# --- User helpers ---

def load_users():
    if os.path.exists(USERS_FILE):
        with open(USERS_FILE) as f:
            return json.load(f)
    return {}

def save_users(users):
    with open(USERS_FILE, "w") as f:
        json.dump(users, f, indent=2)

def init_admin():
    users = load_users()
    if not users:
        users["admin"] = generate_password_hash(os.environ.get("ADMIN_PASSWORD", "admin"))
        save_users(users)

init_admin()

def login_required(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        if "user" not in session:
            return redirect(url_for("index"))
        return f(*args, **kwargs)
    return wrapper

def load_settings():
    if os.path.exists(SETTINGS_FILE):
        with open(SETTINGS_FILE) as f:
            return json.load(f)
    return {"allowed_extensions": DEFAULT_EXTENSIONS}

def save_settings(settings):
    with open(SETTINGS_FILE, "w") as f:
        json.dump(settings, f, indent=2)

def get_allowed_extensions():
    return tuple(load_settings().get("allowed_extensions", DEFAULT_EXTENSIONS))

def safe_dirname(name):
    name = re.sub(r'[^a-zA-Z0-9_\-]', '', name)
    return name[:64] if name else None

# --- Templates ---

STYLE = """
* { box-sizing: border-box; margin: 0; padding: 0; }
body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif; background: #0f1117; color: #e1e4e8; min-height: 100vh; padding: 2rem; }
.container { max-width: 750px; margin: 0 auto; }
h1 { font-size: 1.8rem; margin-bottom: 1.5rem; color: #fff; }
h2 { font-size: 1.3rem; margin-bottom: .8rem; color: #c9d1d9; }
h3 { font-size: 1.1rem; margin-bottom: .5rem; color: #c9d1d9; }
.box { background: #1c1f2b; border: 2px dashed #30363d; border-radius: 12px; padding: 1.5rem; text-align: center; margin-bottom: 1.5rem; transition: border-color .2s; }
.box:hover { border-color: #58a6ff; }
input[type=text], input[type=password], select { background: #161b22; border: 1px solid #30363d; color: #e1e4e8; padding: .5rem .8rem; border-radius: 6px; font-size: .95rem; margin-bottom: .5rem; }
button, .btn { background: #238636; color: #fff; border: none; padding: .6rem 1.4rem; border-radius: 6px; cursor: pointer; font-size: .95rem; text-decoration: none; display: inline-block; }
button:hover, .btn:hover { background: #2ea043; }
.msg { padding: .8rem 1rem; border-radius: 8px; margin-bottom: 1.5rem; }
.msg.success { background: #1b3a2d; color: #56d364; }
.msg.error { background: #3d1f1f; color: #f85149; }
ul { list-style: none; }
li { padding: .5rem 0; border-bottom: 1px solid #21262d; display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: .4rem; }
li:last-child { border-bottom: none; }
a { color: #58a6ff; text-decoration: none; }
a:hover { text-decoration: underline; }
.delete-btn { background: #da3633; padding: .3rem .8rem; font-size: .8rem; border-radius: 4px; }
.delete-btn:hover { background: #f85149; }
.empty { color: #8b949e; font-style: italic; }
.topbar { display: flex; justify-content: space-between; align-items: center; margin-bottom: 1.5rem; }
.topbar .user { color: #8b949e; }
.logout-btn { background: #6e4000; padding: .4rem 1rem; font-size: .85rem; }
.logout-btn:hover { background: #845400; }
.dir-card { background: #161b22; border: 1px solid #21262d; border-radius: 10px; padding: 1.2rem; margin-bottom: 1rem; }
.dir-title { font-size: 1.1rem; color: #fff; margin-bottom: .6rem; }
.dir-title a { color: #58a6ff; }
.inline-form { display: inline; }
.section { margin-bottom: 2rem; }
"""

LOGIN_HTML = """
<!DOCTYPE html><html lang="en"><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Login - HTML Host</title><style>""" + STYLE + """
.login-box { max-width: 360px; margin: 4rem auto; }
.login-box input { width: 100%; margin-bottom: .8rem; }
.login-box button { width: 100%; }
</style></head><body>
<div class="login-box">
    <h1>HTML Host</h1>
    {% if msg %}<div class="msg {{ msg_type }}">{{ msg }}</div>{% endif %}
    <form method="POST">
        <input type="text" name="username" placeholder="Username" required autofocus><br>
        <input type="password" name="password" placeholder="Password" required><br>
        <button type="submit">Login</button>
    </form>
</div>
</body></html>
"""

DASHBOARD_HTML = """
<!DOCTYPE html><html lang="en"><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>HTML Host</title><style>""" + STYLE + """</style></head><body>
<div class="container">
    <div class="topbar">
        <h1>HTML Host</h1>
        <div>
            <span class="user">{{ user }}</span>
            <a href="/logout" class="btn logout-btn">Logout</a>
        </div>
    </div>
    {% if msg %}<div class="msg {{ msg_type }}">{{ msg }}</div>{% endif %}

    <div class="section">
        <h2>Allowed File Types</h2>
        <div class="box">
            <form method="POST" action="/settings" style="display:flex;align-items:center;justify-content:center;gap:.8rem;flex-wrap:wrap">
                <label style="color:#8b949e">Extensions:</label>
                <input type="text" name="extensions" value="{{ allowed_ext }}" style="width:320px" placeholder=".html, .htm, .css, .js">
                <button type="submit">Save</button>
            </form>
            <p style="color:#8b949e;font-size:.8rem;margin-top:.5rem">Comma-separated, e.g.: .html, .htm, .css, .js, .png, .jpg</p>
        </div>
    </div>

    <div class="section">
        <h2>Create Directory</h2>
        <div class="box">
            <form method="POST" action="/mkdir">
                <input type="text" name="dirname" placeholder="Directory name (alphanumeric, -, _)" required>
                <button type="submit">Create</button>
            </form>
        </div>
    </div>

    <div class="section">
        <h2>Upload Files</h2>
        <div class="box">
            <form method="POST" action="/upload" enctype="multipart/form-data">
                <div style="margin-bottom:.8rem">
                    <label style="color:#8b949e">Target directory:</label><br>
                    <select name="directory" style="width:220px;margin-top:.3rem">
                        {% for d in dirs %}
                        <option value="{{ d }}">{{ d }}/</option>
                        {% endfor %}
                    </select>
                </div>
                <input type="file" name="files" accept="{{ allowed_ext }}" multiple required><br>
                <button type="submit">Upload Files</button>
            </form>
        </div>
        <div class="box">
            <form method="POST" action="/upload" enctype="multipart/form-data">
                <div style="margin-bottom:.8rem">
                    <label style="color:#8b949e">Target directory:</label><br>
                    <select name="directory" style="width:220px;margin-top:.3rem">
                        {% for d in dirs %}
                        <option value="{{ d }}">{{ d }}/</option>
                        {% endfor %}
                    </select>
                </div>
                <input type="file" name="files" webkitdirectory multiple required><br>
                <button type="submit">Upload Folder</button>
            </form>
        </div>
    </div>

    <div class="section">
        <h2>Hosted Files</h2>
        {% if dirs %}
            {% for d in dirs %}
            <div class="dir-card">
                <div class="dir-title" style="display:flex;justify-content:space-between;align-items:center">
                    <span>{{ d }}/</span>
                    <form method="POST" action="/rmdir/{{ d }}" class="inline-form">
                        <button class="delete-btn" type="submit" onclick="return confirm('Delete directory {{ d }} and all files?')">Delete Dir</button>
                    </form>
                </div>
                {% set file_list = dir_files.get(d, []) %}
                {% if file_list %}
                <ul>
                    {% for f in file_list %}
                    <li>
                        <a href="/view/{{ d }}/{{ f }}" target="_blank">{{ f }}</a>
                        <form method="POST" action="/delete/{{ d }}/{{ f }}" class="inline-form">
                            <button class="delete-btn" type="submit">Delete</button>
                        </form>
                    </li>
                    {% endfor %}
                </ul>
                {% else %}
                <p class="empty">Empty directory.</p>
                {% endif %}
            </div>
            {% endfor %}
        {% else %}
        <p class="empty">No directories yet. Create one above to start uploading.</p>
        {% endif %}
    </div>
</div>
</body></html>
"""

# --- Routes ---

@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")
        users = load_users()
        if username in users and check_password_hash(users[username], password):
            session["user"] = username
            return redirect(url_for("dashboard"))
        return render_template_string(LOGIN_HTML, msg="Invalid credentials.", msg_type="error")
    if "user" in session:
        return redirect(url_for("dashboard"))
    return render_template_string(LOGIN_HTML, msg=None, msg_type=None)


@app.route("/logout")
def logout():
    session.pop("user", None)
    return redirect(url_for("index"))


@app.route("/dashboard")
@login_required
def dashboard():
    allowed = get_allowed_extensions()
    dirs = sorted(d for d in os.listdir(UPLOAD_DIR) if os.path.isdir(os.path.join(UPLOAD_DIR, d)))
    dir_files = {}
    for d in dirs:
        dpath = os.path.join(UPLOAD_DIR, d)
        found = []
        for root, _, filenames in os.walk(dpath):
            for fn in filenames:
                if fn.lower().endswith(allowed):
                    rel = os.path.relpath(os.path.join(root, fn), dpath).replace("\\", "/")
                    found.append(rel)
        dir_files[d] = sorted(found)
    allowed_ext = ", ".join(allowed)
    return render_template_string(
        DASHBOARD_HTML,
        user=session["user"], dirs=dirs, dir_files=dir_files, allowed_ext=allowed_ext,
        msg=request.args.get("msg"), msg_type=request.args.get("msg_type", "success"),
    )


@app.route("/mkdir", methods=["POST"])
@login_required
def mkdir():
    dirname = safe_dirname(request.form.get("dirname", ""))
    if not dirname:
        return redirect(url_for("dashboard", msg="Invalid directory name.", msg_type="error"))
    dirpath = os.path.join(UPLOAD_DIR, dirname)
    if os.path.exists(dirpath):
        return redirect(url_for("dashboard", msg=f"Directory '{dirname}' already exists.", msg_type="error"))
    os.makedirs(dirpath)
    return redirect(url_for("dashboard", msg=f"Created directory '{dirname}'.", msg_type="success"))


@app.route("/rmdir/<dirname>", methods=["POST"])
@login_required
def rmdir(dirname):
    dirname = safe_dirname(dirname)
    if not dirname:
        return redirect(url_for("dashboard", msg="Invalid directory.", msg_type="error"))
    dirpath = os.path.join(UPLOAD_DIR, dirname)
    if not os.path.isdir(dirpath):
        return redirect(url_for("dashboard", msg="Directory not found.", msg_type="error"))
    shutil.rmtree(dirpath)
    return redirect(url_for("dashboard", msg=f"Deleted directory '{dirname}'.", msg_type="success"))


@app.route("/settings", methods=["POST"])
@login_required
def settings():
    raw = request.form.get("extensions", "")
    exts = []
    for ext in raw.split(","):
        ext = ext.strip().lower()
        if ext and ext.startswith(".") and re.match(r'^\.[a-zA-Z0-9]+$', ext):
            exts.append(ext)
    if not exts:
        return redirect(url_for("dashboard", msg="Provide at least one valid extension (e.g. .html).", msg_type="error"))
    s = load_settings()
    s["allowed_extensions"] = exts
    save_settings(s)
    return redirect(url_for("dashboard", msg=f"Allowed extensions updated: {', '.join(exts)}", msg_type="success"))


@app.route("/upload", methods=["POST"])
@login_required
def upload():
    directory = safe_dirname(request.form.get("directory", ""))
    if not directory:
        return redirect(url_for("dashboard", msg="Select a directory.", msg_type="error"))
    dirpath = os.path.join(UPLOAD_DIR, directory)
    if not os.path.isdir(dirpath):
        return redirect(url_for("dashboard", msg="Directory does not exist.", msg_type="error"))

    allowed = get_allowed_extensions()
    files = request.files.getlist("files")
    if not files or all(f.filename == "" for f in files):
        return redirect(url_for("dashboard", msg="No files selected.", msg_type="error"))

    count = 0
    for file in files:
        if not file.filename:
            continue
        # Sanitize: keep only the relative path within the uploaded folder
        rel_path = file.filename.replace("\\", "/")
        # Only allow configured file types
        if not rel_path.lower().endswith(allowed):
            continue
        # Sanitize each path component
        parts = [p for p in rel_path.split("/") if p and p != ".." and not p.startswith(".")]
        if not parts:
            continue
        # Create subdirectories if folder upload
        if len(parts) > 1:
            subdir = os.path.join(dirpath, *parts[:-1])
            os.makedirs(subdir, exist_ok=True)
            file.save(os.path.join(subdir, parts[-1]))
        else:
            file.save(os.path.join(dirpath, parts[0]))
        count += 1

    if count == 0:
        return redirect(url_for("dashboard", msg=f"No files matching allowed types ({', '.join(allowed)}).", msg_type="error"))
    return redirect(url_for("dashboard", msg=f"Uploaded {count} file(s) to {directory}/.", msg_type="success"))


@app.route("/view/<directory>/<path:filename>")
def view(directory, filename):
    directory = safe_dirname(directory)
    if not directory:
        return "Not found", 404
    dirpath = os.path.join(UPLOAD_DIR, directory)
    # Prevent path traversal
    full = os.path.normpath(os.path.join(dirpath, filename))
    if not full.startswith(os.path.normpath(dirpath)):
        return "Not found", 404
    return send_from_directory(dirpath, filename)


@app.route("/delete/<directory>/<path:filename>", methods=["POST"])
@login_required
def delete(directory, filename):
    directory = safe_dirname(directory)
    if not directory:
        return redirect(url_for("dashboard", msg="Invalid directory.", msg_type="error"))
    filepath = os.path.normpath(os.path.join(UPLOAD_DIR, directory, filename))
    if not filepath.startswith(os.path.normpath(os.path.join(UPLOAD_DIR, directory))):
        return redirect(url_for("dashboard", msg="Invalid path.", msg_type="error"))
    if os.path.exists(filepath):
        os.remove(filepath)
        return redirect(url_for("dashboard", msg=f"Deleted '{filename}'.", msg_type="success"))
    return redirect(url_for("dashboard", msg="File not found.", msg_type="error"))


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5004, debug=True)
