# Poker Trainer – README

## 1  Overview
Poker Trainer is an interactive **no‑limit Texas Hold’em trainer** that runs entirely in your browser and a lightweight Flask server.  
It has two core modes:

1. **Play / Solver** – pick any two hole cards, set up a betting scenario (pot, facing bet, position, street, number of villains) and click **Solve**. You instantly get:
   * Monte‑Carlo **equity** (win %)
   * **Pot‑odds** vs bet size
   * Optimal action (`BET`, `CALL`, `RAISE-to $X`, or `FOLD`)  
     *Heads‑up uses our own pure‑Python evaluator; multi‑way uses the C‑powered* **treys** *library.*

2. **Quiz** – the site deals you a random scenario from `quiz_bank` (or one you played earlier), you choose Fold/Call/Raise, and it grades you in real‑time.  
   * Your last 30 quiz attempts are listed with ✅/❌, solver answer, and timestamp.
   * All attempts are persisted in `hands` for later analytics.

-----

## 2  Quick Start

1. **Clone & install**

```bash
git clone https://github.com/your‑username/poker_trainer.git
cd poker_trainer
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt
```

2. **Create the database** # THIS STEP CAN BE SKIPPED, DATABASE INCLUDED

```bash
sqlite3 poker.db < schema.sql
python seed_quiz.py   # optional: insert 20 curated quiz spots
```

3. **Run**

```bash
python -m flask --app app.py run    # dev server
```

Visit <http://127.0.0.1:5000>

-----

## 3  File Layout

```
poker_trainer/
│
├── app.py                Flask entry point (routes only)
├── schema.sql            SQLite schema
├── requirements.txt
│
├── poker_engine/         # “business logic”
│   ├── solver.py         picks evaluator, equity, advice
│   ├── evaluator.py      pure‑Python 5‑card ranker
│   └── __init__.py
│
├── quiz_backend.py       DB helper for /quiz endpoints
│
├── seed_quiz.py          Helps with creating quiz problems
│
├── static/
│   ├── css/styles.css
│   └── js/
│       ├── cardpicker.js  52‑card UI component
│       └── main.js        front‑end controller
│
├── templates/            Jinja2 pages
│   ├── layout.html
│   ├── index.html
│   └── quiz.html
│
├── seed_quiz.py          CLI: populate quiz_bank
│
├── poker.dc              Database, included for ease of use
│
├── README.md             Guide
│
└── DESIGN.md             Design Choices
```

-----

## 4  Usage Guide

### 4.1 Play Mode
| Step | Action |
|------|--------|
| 1 | Click any **two** mini cards. |
| 2 | Fill in Situation: Pot size (before bet), Facing bet, Villains, Position, Street. |
| 3 | Click **Solve Hand**. |
| 4 | Read advice card; green highlight = recommended action. |

`RAISE` shows the **raise‑to amount** (pot‑size formula).  
All solved hands are logged in *Play History* (right‑side panel).

### 4.2 Quiz Mode
1. Navigate to `/quiz`.  
2. Read the scenario line (“Hand: AhKd  Pot $40 facing $20”).  
3. Click **Fold / Call / Raise**.  
4. See ✅/❌ feedback, solver’s action, and the next hand after 1.5 s.  
5. Check **Recent Quiz Hands** list for your last 30 attempts.

### 4.3 Admin – adding quiz hands
*CLI option*:

```bash
python seed_quiz.py --count 50 --street flop
```

*Manual SQL*:

```sql
INSERT INTO quiz_bank
(hero_cards, position, street, pot_size, facing_bet, solver_json)
VALUES
('JhTs', 'BTN', 'flop', 60, 30,
 '{"hero_cards":["Jh","Ts"],"position":"BTN","street":"flop",
   "pot_size":60,"facing_bet":30,"advice":"raise","raise_size":180}');
```

-----

## 5  Configuration & Deployment

| Setting | Where | Default | Notes |
|---------|-------|---------|-------|
| `DB_PATH` | quiz_backend.py & app.py | `poker.db` | Change to PostgreSQL URI for production. |
| `PORT` | CLI | 5000 | Render/Fly.io will inject `$PORT`. |
| `FLASK_ENV` | env var | development | Use `production` to disable debugger. |

**Render .com** deploy:

```
Start command: python -m flask --app app.py run --host=0.0.0.0 --port=$PORT
Build: pip install -r requirements.txt
```

-----

## 6  Frequently Asked Questions

| Question | Answer |
|----------|--------|
| *Why are equities slightly different each solve?* | Monte‑Carlo uses 2 500 trials by default; expect ±1 % noise. |
| *Can I add board cards?* | Yes. Add a 5‑card picker, pass `board_cards` to `/api/solve`; DB already supports it. |
| *Is authentication supported?* | No; history is global. Add Flask‑Login & a `user_id` FK to `hands` if needed. |
| *How do I reset the DB?* | `rm poker.db && sqlite3 poker.db < schema.sql`. |

Enjoy the trainer—may your EV lines be positive!

