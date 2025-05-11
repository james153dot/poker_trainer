"""solver.py
=============
High‑level “brain” of the trainer.

Responsibilities
----------------
1. Compute **equity** – chooses heads‑up evaluator vs multi‑way treys.
2. Compute **pot‑odds** given pot size and facing bet.
3. Apply *very simple* no‑limit decision rule to output:
     • advice      – 'bet', 'call', 'raise', 'fold'
     • raise_size  – numeric only when advice == 'raise'

The function signature `solve(req: dict) -> dict` is **stable** so the
front‑end and quiz seeder rely on it.

All numbers are rounded for UI friendliness (3‑dp equity, 2‑dp money).
"""

import random
from typing import List

from . import evaluator as myeval             # pure‑Python HU evaluator
from treys import Card, Deck, Evaluator as TreysEval

# Pre‑computed full deck as list of "As", "2d", … – used by HU Monte‑Carlo
_FULL_DECK = [r + s for r in "23456789TJQKA" for s in "shdc"]

# ----------------------------------------------------------------------
# Heads‑up equity via our Python evaluator
# ----------------------------------------------------------------------


def _equity_hu(hero: List[str], board: List[str], trials: int = 2500):
    """Monte‑Carlo equity vs ONE random villain."""
    used = set(hero + board)
    wins = ties = 0
    for _ in range(trials):
        # sample opp + runout in one go for performance
        avail = [c for c in _FULL_DECK if c not in used]
        sample = random.sample(avail, 2 + (5 - len(board)))
        opp = sample[:2]
        runout = board + sample[2:]

        hero_rank = myeval.best_rank(hero + runout)
        opp_rank = myeval.best_rank(opp + runout)

        if hero_rank > opp_rank:
            wins += 1
        elif hero_rank == opp_rank:
            ties += 1
    return (wins + 0.5 * ties) / trials

# ----------------------------------------------------------------------
# Multi‑way equity via treys (fast C evaluator)
# ----------------------------------------------------------------------


def _equity_multi(hero: List[str], board: List[str], villains: int,
                  trials: int = 3000):
    """Monte‑Carlo equity vs *villains* random ranges using treys."""
    ev = TreysEval()
    hero_c = [Card.new(c) for c in hero]
    board_c = [Card.new(c) for c in board]

    wins = ties = 0
    for _ in range(trials):
        deck = Deck()
        # Remove known cards so we don’t draw duplicates
        for c in hero + board:
            deck.cards.remove(Card.new(c))

        # deal opponent hole cards
        opp_hands = [deck.draw(2) for _ in range(villains)]

        # complete the board
        runout = board_c + deck.draw(5 - len(board_c))

        hero_rank = ev.evaluate(runout, hero_c)
        opp_ranks = [ev.evaluate(runout, h) for h in opp_hands]
        best_opp = min(opp_ranks)          # lower == better rank in treys

        if hero_rank < best_opp:
            wins += 1
        elif hero_rank == best_opp:
            ties += 1
    return (wins + 0.5 * ties) / trials

# ----------------------------------------------------------------------
# Public API
# ----------------------------------------------------------------------


def solve(req: dict) -> dict:
    """Top‑level solver consumed by /api/solve and seed_quiz.py."""

    # --- unpack request dict ---
    hero = req["hero_cards"]
    board = req.get("board_cards", [])
    villains = int(req.get("num_villains", 1))

    # --- compute equity ---
    equity = (
        _equity_hu(hero, board)
        if villains == 1
        else _equity_multi(hero, board, villains)
    )

    # --- compute pot‑odds ---
    pot = float(req["pot_size"])
    bet = float(req["facing_bet"])
    pot_odds = bet / (pot + bet) if bet else 0.0

    # --- decision rule (extremely simplified) ---
    if bet == 0:
        advice, raise_size = "bet", pot * 0.75          # open ¾‑pot
    elif equity > pot_odds + 0.05:
        if bet < pot * 0.5:
            advice, raise_size = "call", None
        else:
            advice, raise_size = "raise", pot + 2 * bet  # standard pot raise
    else:
        advice, raise_size = "fold", None

    # --- build response payload ---
    out = {
        "equity": round(equity, 3),
        "pot_odds": round(pot_odds, 3),
        "advice": advice,
    }
    if raise_size:
        out["raise_size"] = round(raise_size, 2)
    return out
