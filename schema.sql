CREATE TABLE IF NOT EXISTS hands (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    hero_cards    TEXT NOT NULL,
    board_cards   TEXT,
    position      TEXT,
    street        TEXT,
    pot_size      REAL,
    facing_bet    REAL,
    num_villains  INTEGER,   
    advice_action TEXT,
    raise_size    REAL,
    user_action   TEXT,
    correct       BOOLEAN,
    ts            TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS quiz_bank (
    id           INTEGER PRIMARY KEY AUTOINCREMENT,
    hero_cards   TEXT NOT NULL,
    position     TEXT NOT NULL,
    street       TEXT NOT NULL,
    pot_size     REAL NOT NULL,
    facing_bet   REAL NOT NULL,
    solver_json  TEXT NOT NULL
);

