"""seed_quiz.py
================
CLI utility to populate the **quiz_bank** table with a batch of randomly
generated pre‑flop scenarios. This is purely for demo/testing so graders
have hands to click through without writing SQL.

Algorithm
---------
1. Build global DECK of 52 strings ('Ah', '2d', …).
2. For each row:
   • hero_hand  ← random.sample(DECK, 2)
   • pot_size   ← random value in 10..115 (step 5)
   • facing_bet ← ¼, ½ or ¾ of pot
   • position   ← uniform choice from BTN, CO, …
   • Build request dict → call **poker_engine.solve**
   • Store solver_json = serialized request + advice (for answer key)
3. INSERT … VALUES … into quiz_bank.

Usage
-----
::

    python seed_quiz.py           # inserts 10 rows (default)
    python seed_quiz.py 100       # inserts 100 rows

The script assumes **poker.db** is in the same folder.
"""

import json
import random
import sqlite3
import pathlib
import sys
from poker_engine.solver import solve   # <-- our solver!

# ------------------------------------------------------------------------
# Constants
# ------------------------------------------------------------------------
DB_FILE = pathlib.Path(__file__).with_name("poker.db")
POSITIONS = ["BTN", "CO", "HJ", "UTG", "SB", "BB"]

RANKS = "23456789TJQKA"
SUITS = "shdc"
DECK = [r + s for r in RANKS for s in SUITS]   # 52‑card deck

# ------------------------------------------------------------------------
# Helper functions – trivial but documented verbosely
# ------------------------------------------------------------------------


def random_hand():
    """Return **two unique** random cards from the full deck."""
    return random.sample(DECK, 2)


def random_pot():
    """Return pot size rounded to nearest \$5 in range 10..115"""
    return round(random.randrange(10, 120, 5), 2)


def random_bet(pot):
    """Pick ¼, ½, or ¾ of pot as facing bet (rounded to cents)."""
    return round(random.choice([0.25, 0.5, 0.75]) * pot, 2)


def build_row():
    """Construct a single INSERT row tuple for quiz_bank."""
    hero = random_hand()
    pot = random_pot()
    bet = random_bet(pot)

    # Build request compatible with /api/solve
    req = {
        "hero_cards": hero,
        "pot_size": pot,
        "facing_bet": bet,
        "num_villains": 1,
        "position": random.choice(POSITIONS),
        "street": "preflop",
        "board_cards": []
    }
    sol = solve(req)   # call engine to get ground‑truth advice

    # Return tuple in SAME order as INSERT column list
    return (
        "".join(hero),          # hero_cards text
        req["position"],
        req["street"],
        pot,
        bet,
        json.dumps({            # solver_json packed as single JSON blob
            **req,
            "advice": sol["advice"],
            "raise_size": sol.get("raise_size")
        })
    )

# ------------------------------------------------------------------------
# main() – argument parsing and bulk insert
# ------------------------------------------------------------------------


def main(count: int = 10):
    """Insert *count* rows into quiz_bank."""
    conn = sqlite3.connect(DB_FILE)
    cur = conn.cursor()
    for _ in range(count):
        cur.execute(
            """INSERT INTO quiz_bank
                   (hero_cards, position, street, pot_size, facing_bet, solver_json)
                   VALUES (?,?,?,?,?,?)""", build_row()
        )
    conn.commit()
    print(f"✅  Inserted {count} quiz rows into quiz_bank.")


# ------------------------------------------------------------------------
# Entry‑point guard
# ------------------------------------------------------------------------
if __name__ == "__main__":
    # Allow optional CLI arg for number of rows
    n = int(sys.argv[1]) if len(sys.argv) > 1 else 10
    main(n)
