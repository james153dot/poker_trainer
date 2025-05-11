"""
app.py
======

Flask entry-point *and only* place where HTTP routing lives.
Every other file contains “business logic” so this module stays thin.

Rule of thumb used here:
    • Accept JSON  → validate → hand off to helper layer
    • Return JSON  ← helper layer
    • Handle DB via helper or one-liner SQL
"""
import os
import json
import sqlite3
import pathlib
from contextlib import closing
from flask import Flask, render_template, request, jsonify
from flask_session import Session

from poker_engine.solver import solve          # equity + advice engine
from quiz_backend import (                      # quiz DB helpers
    random_quiz_row,
    grade_and_log,
)

# ────────────────────────────────────────────────────────────────────
#  Flask application factory (we don’t actually need a factory func)
# ────────────────────────────────────────────────────────────────────
app = Flask(__name__)

# Minimal runtime configuration
app.config.update(
    SECRET_KEY=os.urandom(16),      # session signing key
    TEMPLATES_AUTO_RELOAD=True,     # dev convenience
    SESSION_PERMANENT=False,        # browser-session cookie only
    SESSION_TYPE="filesystem",      # simplest server-side store
)

# Activate Flask-Session so we can use `session` if ever needed
Session(app)

# ────────────────────────────────────────────────────────────────────
#  SQLite helper — returns a *context-managed* connection
#    with Row-factory ⇒ rows behave like dicts.
# ────────────────────────────────────────────────────────────────────
DB_PATH = pathlib.Path(__file__).with_name("poker.db")


def get_conn():
    """
    Open an SQLite connection whose rows behave like dicts.

    We intentionally **do not** cache the connection at module scope;
    letting `with closing(get_conn()) as conn:` handle lifetime
    avoids cross-thread issues once we move to gunicorn.
    """
    conn = sqlite3.connect(DB_PATH, detect_types=sqlite3.PARSE_DECLTYPES)
    conn.row_factory = sqlite3.Row   # SELECT returns sqlite3.Row → dict-like
    return conn


# -------------------------------------------------------------------
#                      ─── HTML PAGES ───
# -------------------------------------------------------------------
@app.route("/")
def index():
    """Main Play page."""
    return render_template("index.html")


@app.route("/quiz")
def quiz():
    """Quiz mode page."""
    return render_template("quiz.html")


# -------------------------------------------------------------------
#          ─── JSON API  – Play Mode (Solver) ───
# -------------------------------------------------------------------
@app.post("/api/solve")
def api_solve():
    """
    Accept JSON describing a poker spot, return equity + advice.

    Expected JSON payload (all strings/numbers):
        {
          hero_cards  : ["Ah","Kd"],
          board_cards : [],              # optional
          pot_size    : 40,
          facing_bet  : 20,
          num_villains: 1,
          position    : "BTN",
          street      : "preflop"
        }
    """
    data = request.get_json()
    result = solve(data)               # heavy lifting in poker_engine

    # Persist the hand to history for later analytics
    with closing(get_conn()) as conn, conn:
        conn.execute(
            """INSERT INTO hands
               (hero_cards, board_cards, position, street,
                pot_size, facing_bet, advice_action, raise_size)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                "".join(data["hero_cards"]),           # compact store
                "".join(data.get("board_cards", [])),  # may be empty
                data["position"],
                data["street"],
                data["pot_size"],
                data["facing_bet"],
                result["advice"],
                result.get("raise_size"),
            ),
        )
    return jsonify(result)


# -------------------------------------------------------------------
#          ─── JSON API  – Play History (last 30) ───
# -------------------------------------------------------------------
@app.get("/api/history")
def api_history():
    """Return last 30 rows from `hands` table in reverse-chron order."""
    with closing(get_conn()) as conn:
        rows = conn.execute(
            "SELECT * FROM hands ORDER BY ts DESC LIMIT 30"
        ).fetchall()
    # Convert sqlite3.Row objects → dict for easy JSON serialisation
    return jsonify([dict(row) for row in rows])


# -------------------------------------------------------------------
#          ─── JSON API  – Quiz History (last 30) ───
# -------------------------------------------------------------------
@app.get("/api/quiz/history")
def api_quiz_history():
    """
    Same idea as /api/history but filtered to rows that came from the Quiz
    (those have non-null user_action).
    """
    with closing(get_conn()) as conn:
        rows = conn.execute(
            """SELECT hero_cards, position, user_action,
                     advice_action, correct, ts
               FROM hands
               WHERE user_action IS NOT NULL
               ORDER BY ts DESC LIMIT 30"""
        ).fetchall()
    return jsonify([dict(r) for r in rows])


# -------------------------------------------------------------------
#              ─── JSON API  – Quiz Endpoints ───
# -------------------------------------------------------------------
@app.get("/api/quiz/next")
def api_quiz_next():
    """Return one random row from quiz_bank as JSON."""
    row = random_quiz_row()
    return (jsonify(row) if row else
            (jsonify({"error": "no quiz hands"}), 404))


@app.post("/api/quiz/answer")
def api_quiz_answer():
    """
    Payload: {"id": <quiz_bank id>, "user_action": "fold|call|raise"}

    Returns: {"correct": true/false, "solver": "fold|call|raise"}
    """
    data = request.get_json()
    try:
        correct, solver_action = grade_and_log(
            data["id"], data["user_action"]
        )
        return jsonify({"correct": correct, "solver": solver_action})
    except ValueError as e:
        # quiz id not found – likely stale client
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        # log stack-trace, return generic 500 to client
        app.logger.exception("quiz insert failed")
        return jsonify({"error": "server error"}), 500


# -------------------------------------------------------------------
#             ─── Dev only: flask run fallback ───
# -------------------------------------------------------------------
if __name__ == "__main__":
    # Running via `python app.py` is handy during local hacking;
    # for production use `gunicorn -k gevent -w 4 "app:app"`
    app.run(debug=True)
