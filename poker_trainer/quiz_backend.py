"""
quiz_backend.py
===============

Thin helper layer that hides *all* SQL used by the Quiz endpoints.
Keeps app.py clean and unit-testable.
"""
import sqlite3
import json
import pathlib
from contextlib import closing

# Path to database = project_root/poker.db (same rule as app.py)
DB_PATH = pathlib.Path(__file__).with_name("poker.db")

# -------------------------------------------------------------------
#  Small helper: open connection with Row factory
# -------------------------------------------------------------------


def get_conn():
    conn = sqlite3.connect(DB_PATH, detect_types=sqlite3.PARSE_DECLTYPES)
    conn.row_factory = sqlite3.Row   # dict-like rows
    return conn


# -------------------------------------------------------------------
#  Column map for inserting quiz attempts into `hands`
# -------------------------------------------------------------------
COLS = (
    "hero_cards", "position", "street", "pot_size", "facing_bet",
    "advice_action", "raise_size", "user_action", "correct"
)
# Build "?, ?, ?, …" string dynamically so we can’t get counts wrong
PLACEHOLDERS = ", ".join("?" for _ in COLS)
INSERT_SQL = f"INSERT INTO hands ({', '.join(COLS)}) VALUES ({PLACEHOLDERS})"

# -------------------------------------------------------------------
#                 ─── Public helper functions ───
# -------------------------------------------------------------------


def random_quiz_row():
    """Return a random quiz_bank row as dict or None if empty."""
    with closing(get_conn()) as conn, conn:
        row = conn.execute(
            "SELECT * FROM quiz_bank ORDER BY RANDOM() LIMIT 1"
        ).fetchone()
        return dict(row) if row else None


def grade_and_log(quiz_id: int, user_action: str):
    """
    1. Look up solver JSON for quiz_id
    2. Compare to user_action
    3. INSERT a row into hands with the outcome
    4. Return (correct:boolean, solver_action:str)
    """
    with closing(get_conn()) as conn, conn:
        q = conn.execute(
            "SELECT solver_json FROM quiz_bank WHERE id = ?", (quiz_id,)
        ).fetchone()
        if not q:
            # Caller will turn this into 400 Bad Request
            raise ValueError("bad id")

        solver = json.loads(q[0])                 # JSON → dict
        correct = solver["advice"] == user_action  # bool

        # Persist attempt
        conn.execute(
            INSERT_SQL,
            (
                "".join(solver["hero_cards"]),    # hero_cards (text)
                solver["position"],
                solver["street"],
                solver["pot_size"],
                solver["facing_bet"],
                solver["advice"],
                solver.get("raise_size"),         # may be None
                user_action,
                correct,
            ),
        )
        return correct, solver["advice"]
