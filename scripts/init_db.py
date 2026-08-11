"""
Step 4a: Set up the SQLite database and schema.

Run this once to create data/filings.db with empty `filings` and `prices`
tables. Safe to re-run — uses CREATE TABLE IF NOT EXISTS.
"""

import sqlite3
from pathlib import Path

DB_PATH = Path("data/filings.db")

SCHEMA = """
CREATE TABLE IF NOT EXISTS filings (
    accession_no  TEXT PRIMARY KEY,   -- e.g. '0000103379-26-000113'
    cik           TEXT NOT NULL,      -- e.g. '0000103379'
    ticker        TEXT NOT NULL,      -- e.g. 'VFC'
    filing_date   TEXT NOT NULL,      -- ISO date 'YYYY-MM-DD'
    item_codes    TEXT,               -- comma-separated, e.g. '2.02,5.02,7.01'
    is_confounded INTEGER NOT NULL DEFAULT 0,  -- 1 if bundled w/ other material items (e.g. earnings)
    raw_path      TEXT NOT NULL,      -- path to the saved .htm file
    label         TEXT,               -- filled in later: 'Positive' / 'Negative' / 'Neutral'
    abnormal_return REAL              -- filled in later: computed 3-day abnormal return
);

CREATE TABLE IF NOT EXISTS prices (
    ticker    TEXT NOT NULL,
    date      TEXT NOT NULL,   -- ISO date 'YYYY-MM-DD'
    adj_close REAL NOT NULL,
    PRIMARY KEY (ticker, date)
);
"""


def init_db() -> None:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    try:
        conn.executescript(SCHEMA)
        conn.commit()
        print(f"Database ready at {DB_PATH}")
        tables = conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table'"
        ).fetchall()
        print("Tables:", [t[0] for t in tables])
    finally:
        conn.close()


if __name__ == "__main__":
    init_db()