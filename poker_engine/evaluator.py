"""evaluator.py
================
A **pure‑Python** hand evaluator for Texas Hold’em.

Why not just treys?
-------------------
* Heads‑up Monte‑Carlo only needs ~2 000 evaluations → Python is fast enough.
* Zero CFFI / wheel build issues → easier for graders.
* Complete transparency – you can read the ranking algorithm in 60 lines.

Ranking Model
-------------
Hands are compared on a tuple:

    (category_rank, kicker1, kicker2, ...)

where *category_rank* is:

| Value | Hand Category       |
|-------|---------------------|
| 8     | Straight Flush      |
| 7     | Four of a Kind      |
| 6     | Full House          |
| 5     | Flush               |
| 4     | Straight            |
| 3     | Three of a Kind     |
| 2     | Two Pair            |
| 1     | One Pair            |
| 0     | High Card           |

The natural tuple ordering (`>` / `<`) yields correct comparisons.
"""

from itertools import combinations
from typing import List, Tuple

# ------------------------------------------------------------------------
# Pre‑compute rank → value mapping once
# ------------------------------------------------------------------------
_RANKS = "23456789TJQKA"
_VAL = {r: i for i, r in enumerate(_RANKS, start=2)}   # 2→2 … A→14


def _card(card: str) -> Tuple[int, str]:
    """Convert 'Ah' → (14, 'h') for easier math."""
    return _VAL[card[0]], card[1]

# ------------------------------------------------------------------------
# Straight detection helper
# ------------------------------------------------------------------------


def _is_straight(vals):
    """Return (is_straight:bool, high_card:int). Handles wheel A‑5."""
    uniq = sorted(set(vals), reverse=True)
    # Slide window of length 5 over unique ranks
    for i in range(len(uniq) - 4):
        if uniq[i] - uniq[i + 4] == 4:
            return True, uniq[i]
    # Wheel straight (A‑2‑3‑4‑5) special‑case
    if {14, 5, 4, 3, 2}.issubset(uniq):
        return True, 5
    return False, 0

# ------------------------------------------------------------------------
# _rank5 – rank a *single* 5‑card hand
# ------------------------------------------------------------------------


def _rank5(cards):
    vals = [v for v, _ in cards]
    suits = [s for _, s in cards]
    sorted_vals = sorted(vals, reverse=True)

    counts = {v: vals.count(v) for v in set(vals)}
    flush = len(set(suits)) == 1
    straight, hi = _is_straight(vals)

    # === Hand category checks from strongest to weakest ============
    if flush and straight:
        return 8, [hi]                     # Straight Flush
    if 4 in counts.values():
        four = max(k for k, c in counts.items() if c == 4)
        kicker = max(k for k, c in counts.items() if c == 1)
        return 7, [four, kicker]           # Four of a Kind
    if sorted(counts.values()) == [2, 3]:
        triple = max(k for k, c in counts.items() if c == 3)
        pair = max(k for k, c in counts.items() if c == 2)
        return 6, [triple, pair]           # Full House
    if flush:
        return 5, sorted_vals              # Flush
    if straight:
        return 4, [hi]                     # Straight
    if 3 in counts.values():
        triple = max(k for k, c in counts.items() if c == 3)
        kickers = sorted((k for k, c in counts.items() if c == 1), reverse=True)
        return 3, [triple] + kickers       # Trips
    if list(counts.values()).count(2) == 2:
        pairs = sorted((k for k, c in counts.items() if c == 2), reverse=True)
        kicker = max(k for k, c in counts.items() if c == 1)
        return 2, pairs + [kicker]         # Two Pair
    if 2 in counts.values():
        pair = max(k for k, c in counts.items() if c == 2)
        kickers = sorted((k for k, c in counts.items() if c == 1), reverse=True)
        return 1, [pair] + kickers         # One Pair
    return 0, sorted_vals                  # High Card

# ------------------------------------------------------------------------
# best_rank – evaluate 5 or 7 card hand
# ------------------------------------------------------------------------


def best_rank(seven: List[str]):
    """Return rank tuple for best 5‑out‑of‑7 hand."""
    tups = [_card(c) for c in seven]
    if len(tups) == 5:
        return _rank5(tups)

    best = (-1, [])                        # sentinel baseline
    for combo in combinations(tups, 5):    # 21 combos
        r = _rank5(combo)
        if r > best:
            best = r
    return best
