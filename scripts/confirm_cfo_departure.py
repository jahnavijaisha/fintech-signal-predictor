"""
Step 6c-2: Fetch actual filing text for CFO-departure candidates and confirm
that a CFO-role mention and a departure phrase appear in the same sentence
(or an adjacent one), not just somewhere in the same document.
"""
import csv
import re
import time
from pathlib import Path

import pandas as pd
import requests
from bs4 import BeautifulSoup

# --- Config ---------------------------------------------------------------
SEC_USER_AGENT = "T Jahnavi Jaisha   jahnavitulluru8@gmail.com"  # SEC requires this format
REQUEST_DELAY = 0.15  # ~6-7 req/sec, safely under SEC's 10/sec cap
WINDOW = 1  # check current sentence + this many neighbors on each side

CFO_PATTERN = re.compile(r"\bchief financial officer\b|\bCFO\b", re.IGNORECASE)
DEPARTURE_PATTERN = re.compile(
    r"\bresignation\b|\bresigned\b|\bstepping down\b|"
    r"\btermination of employment\b|\bwill depart\b",
    re.IGNORECASE,
)

CANDIDATES_PATH = Path("data/raw/cfo_mention_8k.csv")
ALL_FILINGS_PATH = Path("data/raw/all_8k_filings.csv")
OUTPUT_PATH = Path("data/raw/cfo_departure_confirmed.csv")

HEADERS = {"User-Agent": SEC_USER_AGENT}


def build_url(cik_padded: str, accession_no: str, primary_doc: str) -> str:
    cik_unpadded = str(int(cik_padded))
    accession_nodash = accession_no.replace("-", "")
    return f"https://www.sec.gov/Archives/edgar/data/{cik_unpadded}/{accession_nodash}/{primary_doc}"


def split_sentences(text: str) -> list[str]:
    # Simple regex splitter -- good enough for filing prose; not perfect on abbreviations.
    text = re.sub(r"\s+", " ", text).strip()
    return re.split(r"(?<=[.!?])\s+", text)


def fetch_filing_text(url: str) -> str | None:
    resp = requests.get(url, headers=HEADERS, timeout=15)
    if resp.status_code == 429:
        time.sleep(2)
        resp = requests.get(url, headers=HEADERS, timeout=15)
    if resp.status_code != 200:
        return None
    soup = BeautifulSoup(resp.text, "html.parser")
    return soup.get_text(separator=" ")


def confirm_cooccurrence(text: str) -> tuple[bool, str]:
    sentences = split_sentences(text)
    for i, sentence in enumerate(sentences):
        lo = max(0, i - WINDOW)
        hi = min(len(sentences), i + WINDOW + 1)
        window_text = " ".join(sentences[lo:hi])
        if CFO_PATTERN.search(window_text) and DEPARTURE_PATTERN.search(window_text):
            return True, window_text.strip()
    return False, ""


def main():
    candidates = pd.read_csv(CANDIDATES_PATH, dtype={"cik_padded": str})
    all_filings = pd.read_csv(
        ALL_FILINGS_PATH, dtype={"cik_padded": str, "accessionNumber": str}
    )

    merged = candidates.merge(
        all_filings[["accessionNumber", "primaryDocument"]],
        left_on="accession_no",
        right_on="accessionNumber",
        how="left",
    )

    missing_doc = merged["primaryDocument"].isna().sum()
    if missing_doc:
        print(f"Warning: {missing_doc} candidates had no matching primaryDocument — skipping those.")
    merged = merged.dropna(subset=["primaryDocument"])

    # Resume support: skip accession numbers already written to the output file
    done = set()
    write_header = not OUTPUT_PATH.exists()
    if OUTPUT_PATH.exists():
        done = set(pd.read_csv(OUTPUT_PATH)["accession_no"].astype(str))
        print(f"Resuming — {len(done)} already processed.")

    fieldnames = list(candidates.columns) + ["confirmed", "matched_sentence"]

    with open(OUTPUT_PATH, "a", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        if write_header:
            writer.writeheader()

        total = len(merged)
        processed_count = 0
        confirmed_count = len(done)  # so the running total stays accurate across resumes
        for idx, row in merged.iterrows():
            acc_no = str(row["accession_no"])
            if acc_no in done:
                continue

            url = build_url(row["cik_padded"], acc_no, row["primaryDocument"])
            try:
                text = fetch_filing_text(url)
            except requests.RequestException as e:
                print(f"[{idx}/{total}] {acc_no}: request failed ({e}), skipping")
                continue

            if text is None:
                print(f"[{idx}/{total}] {acc_no}: fetch failed, skipping")
                confirmed, matched = False, ""
            else:
                confirmed, matched = confirm_cooccurrence(text)

            out_row = {col: row[col] for col in candidates.columns}
            out_row["confirmed"] = confirmed
            out_row["matched_sentence"] = matched
            writer.writerow(out_row)
            f.flush()

            processed_count += 1
            if confirmed:
                confirmed_count += 1
            if processed_count % 10 == 0:
                print(f"[{processed_count}/{total}] processed | confirmed so far: {confirmed_count}")
            time.sleep(REQUEST_DELAY)

    print("Done.")


if __name__ == "__main__":
    main()