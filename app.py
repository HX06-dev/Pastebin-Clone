from flask import Flask, request, redirect, render_template_string, abort, jsonify
from flask_cors import CORS
import sqlite3
import secrets

app = Flask(__name__)
DATABASE = "pastes.db"
CORS(app)

def get_db():
    return sqlite3.connect(DATABASE)

def initialize_database():
    with get_db() as db:
        db.execute("""
            CREATE TABLE IF NOT EXISTS pastes (
                id TEXT PRIMARY KEY,
                content TEXT NOT NULL
            )
        """)
        db.commit()

@app.route("/", methods=["GET", "POST"])
def home():
    if request.method == "POST":
        content = request.form["content"].strip()

        if not content:
            return "Paste cannot be empty", 400

        paste_id = secrets.token_urlsafe(6)

        with get_db() as db:
            db.execute(
                "INSERT INTO pastes (id, content) VALUES (?, ?)",
                (paste_id, content)
            )
            db.commit()

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
            "SELECT content FROM pastes WHERE id = ?",
            (paste_id,)
        ).fetchone()

    if paste is None:
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

    paste_id = secrets.token_urlsafe(6)

    with get_db() as db:
        db.execute(
            "INSERT INTO pastes (id, content) VALUES (?, ?)",
            (paste_id, content),
        )
        db.commit()

    return jsonify({"id": paste_id}), 201

if __name__ == "__main__":
    initialize_database()
    app.run(debug=True)