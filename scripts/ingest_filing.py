"""
Step 4b: Insert the VFC 2026-07-29 filing (already saved in data/raw/)
into the filings table as a first row.

Run init_db.py before this.
"""

import sqlite3
from pathlib import Path

DB_PATH = Path("data/filings.db")

# Metadata for the filing you already pulled in step 3.
FILING_ROW = {
    "accession_no": "0000103379-26-000113",
    "cik": "0000103379",
    "ticker": "VFC",
    "filing_date": "2026-07-29",
    "item_codes": "2.02,5.02,7.01,9.01",
    "is_confounded": 1,  # bundled with same-day Q1 earnings release (Item 2.02)
    "raw_path": "data/raw/VFC_8K_2026-07-29.htm",
    "label": None,
    "abnormal_return": None,
}


def insert_filing(row: dict) -> None:
    conn = sqlite3.connect(DB_PATH)
    try:
        conn.execute(
            """
            INSERT OR REPLACE INTO filings
                (accession_no, cik, ticker, filing_date, item_codes,
                 is_confounded, raw_path, label, abnormal_return)
            VALUES (:accession_no, :cik, :ticker, :filing_date, :item_codes,
                    :is_confounded, :raw_path, :label, :abnormal_return)
            """,
            row,
        )
        conn.commit()
        print(f"Inserted/updated filing {row['accession_no']} ({row['ticker']}, {row['filing_date']})")
    finally:
        conn.close()


def show_filings() -> None:
    conn = sqlite3.connect(DB_PATH)
    try:
        rows = conn.execute("SELECT * FROM filings").fetchall()
        cols = [d[0] for d in conn.execute("SELECT * FROM filings").description]
        print("\nCurrent filings table:")
        print(cols)
        for r in rows:
            print(r)
    finally:
        conn.close()


if __name__ == "__main__":
    insert_filing(FILING_ROW)
    show_filings()