from flask import Flask, request, redirect, render_template_string, abort, jsonify
from flask_cors import CORS
import sqlite3
import secrets
import threading
from datetime import datetime, timedelta, timezone

app = Flask(__name__)
DATABASE = "pastes.db"
DEFAULT_EXPIRY_HOURS = 24
CLEANUP_INTERVAL_SECONDS = 3600
CORS(app)

def get_db():
    return sqlite3.connect(DATABASE)

def now_utc():
    return datetime.now(timezone.utc)

def initialize_database():
    with get_db() as db:
        db.execute("""
            CREATE TABLE IF NOT EXISTS pastes (
                id TEXT PRIMARY KEY,
                content TEXT NOT NULL,
                expires_at TEXT NOT NULL
            )
        """)
        columns = {row[1] for row in db.execute("PRAGMA table_info(pastes)")}
        if "expires_at" not in columns:
            db.execute("ALTER TABLE pastes ADD COLUMN expires_at TEXT")
            default_expiry = (now_utc() + timedelta(hours=DEFAULT_EXPIRY_HOURS)).isoformat()
            db.execute(
                "UPDATE pastes SET expires_at = ? WHERE expires_at IS NULL",
                (default_expiry,),
            )
        db.commit()

def save_paste(content, expiry_hours=DEFAULT_EXPIRY_HOURS):
    paste_id = secrets.token_urlsafe(6)
    expires_at = (now_utc() + timedelta(hours=expiry_hours)).isoformat()

    with get_db() as db:
        db.execute(
            "INSERT INTO pastes (id, content, expires_at) VALUES (?, ?, ?)",
            (paste_id, content, expires_at),
        )
        db.commit()

    return paste_id

def delete_expired_pastes():
    with get_db() as db:
        db.execute(
            "DELETE FROM pastes WHERE expires_at <= ?",
            (now_utc().isoformat(),),
        )
        db.commit()

def cleanup_loop():
    while True:
        threading.Event().wait(CLEANUP_INTERVAL_SECONDS)
        delete_expired_pastes()

@app.route("/", methods=["GET", "POST"])
def home():
    if request.method == "POST":
        content = request.form["content"].strip()

        if not content:
            return "Paste cannot be empty", 400

        paste_id = save_paste(content)
        return redirect(f"/paste/{paste_id}")

    return """
        <form method="post">
            <textarea name="content"></textarea>
            <button type="submit">Save paste</button>
        </form>
    """

@app.route("/paste/<paste_id>")
def view_paste(paste_id):
    with get_db() as db:
        paste = db.execute(
            "SELECT content, expires_at FROM pastes WHERE id = ?",
            (paste_id,)
        ).fetchone()

    if paste is None:
        abort(404)

    if datetime.fromisoformat(paste[1]) <= now_utc():
        with get_db() as db:
            db.execute("DELETE FROM pastes WHERE id = ?", (paste_id,))
            db.commit()
        abort(404)

    return render_template_string("""
        <h1>Paste</h1>
        <pre>{{ content }}</pre>
    """, content=paste[0])

@app.post("/api/pastes")
def create_paste():
    data = request.get_json(silent=True) or {}
    content = data.get("content", "").strip()

    if not content:
        return jsonify({"error": "Paste cannot be empty"}), 400

    try:
        expiry_hours = float(data.get("expires_in_hours", DEFAULT_EXPIRY_HOURS))
    except (TypeError, ValueError):
        return jsonify({"error": "expires_in_hours must be a number"}), 400

    if expiry_hours <= 0:
        return jsonify({"error": "expires_in_hours must be greater than zero"}), 400

    paste_id = save_paste(content, expiry_hours)

    return jsonify({"id": paste_id}), 201

if __name__ == "__main__":
    initialize_database()
    delete_expired_pastes()
    threading.Thread(target=cleanup_loop, daemon=True).start()
    app.run(debug=True, use_reloader=False)