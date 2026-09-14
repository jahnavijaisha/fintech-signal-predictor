"""
Step 6c rework: re-verify each confirmed CFO-departure candidate by checking
real proximity between 'Chief Financial Officer' and the matched departure
phrase within the full submission text (not just co-occurrence anywhere
in the accession).

Exhibit-type fix: the full submission .txt is a concatenation of multiple
SEC <DOCUMENT> blocks (the primary 8-K body plus every exhibit). Searching
the whole blob let unrelated "chief financial officer" mentions inside
EX-3.x bylaws/charter exhibits (officer-title boilerplate) and EX-10.x
contract exhibits (defined terms like "Resignation Effective Date") land
within the proximity window of an unrelated departure phrase elsewhere in
the filing, producing false verified=True rows. This version splits the
raw submission on <DOCUMENT>/<TYPE> tags first and only runs the proximity
check inside the primary 8-K document and EX-99.x exhibits (press
releases), where genuine CFO-departure language actually lives.
"""

import pandas as pd
import requests
import time
import re
import os

HEADERS = {"User-Agent": "Jaanu Research jaanu@example.com"}  # match your working UA
INPUT_PATH = "data/raw/confirmed_cfo_departures.csv"
OUTPUT_PATH = "data/raw/verified_cfo_departures.csv"
FAILED_LOG_PATH = "data/raw/verify_fetch_failures.csv"

WINDOW = 200  # characters on each side of a CFO mention to search for the departure phrase
DELAY = 0.15  # seconds between requests, matching 6b/6c rate limiting

CFO_PATTERN = re.compile(r"chief financial officer", re.IGNORECASE)

# Document types whose text we trust for CFO-departure language.
# Primary 8-K body + press-release exhibits only. Explicitly excludes
# EX-3.x (bylaws/charter) and EX-10.x (contracts) even though they're not
# listed here — this is an allowlist, so anything not matching is dropped.
DOCUMENT_BLOCK_RE = re.compile(r"<DOCUMENT>(.*?)</DOCUMENT>", re.DOTALL | re.IGNORECASE)
TYPE_RE = re.compile(r"<TYPE>([^\r\n<]+)", re.IGNORECASE)
TEXT_BLOCK_RE = re.compile(r"<TEXT>(.*?)</TEXT>", re.DOTALL | re.IGNORECASE)


def is_allowed_type(doc_type):
    doc_type = doc_type.strip().upper()
    if doc_type == "8-K":
        return True
    if doc_type.startswith("EX-99"):
        return True
    return False


def clean_text(raw_html):
    text = re.sub(r"<[^>]+>", " ", raw_html)
    text = re.sub(r"&nbsp;|&#160;", " ", text)
    text = re.sub(r"\s+", " ", text)
    return text


def extract_filtered_text(raw_submission_text):
    """Split the full SEC submission into <DOCUMENT> blocks, keep only the
    primary 8-K and EX-99.x exhibits, strip HTML from each, and concatenate.
    Returns '' if no allowed document blocks are found (e.g. unexpected
    submission format), so callers can fall back or log it."""
    kept_chunks = []

    for doc_match in DOCUMENT_BLOCK_RE.finditer(raw_submission_text):
        doc_block = doc_match.group(1)

        type_match = TYPE_RE.search(doc_block)
        if not type_match:
            continue
        doc_type = type_match.group(1)
        if not is_allowed_type(doc_type):
            continue

        text_match = TEXT_BLOCK_RE.search(doc_block)
        if not text_match:
            continue

        kept_chunks.append(clean_text(text_match.group(1)))

    return " ".join(kept_chunks)


def check_proximity(text, departure_phrase):
    """Return the first snippet where departure_phrase falls within WINDOW
    chars of a 'Chief Financial Officer' mention, or None if no match."""
    phrase_lower = departure_phrase.lower()
    text_lower = text.lower()

    for m in CFO_PATTERN.finditer(text):
        start = max(0, m.start() - WINDOW)
        end = min(len(text), m.end() + WINDOW)
        window_text = text_lower[start:end]
        if phrase_lower in window_text:
            return text[start:end]
    return None


def load_done_accessions():
    if os.path.exists(OUTPUT_PATH):
        done_df = pd.read_csv(OUTPUT_PATH)
        return set(done_df["accession_no"].tolist())
    return set()


def main():
    df = pd.read_csv(INPUT_PATH, dtype={"cik_padded": str})
    done = load_done_accessions()
    print(f"{len(done)} accessions already verified — resuming from there.")

    results = []
    failures = []

    remaining = df[~df["accession_no"].isin(done)]
    print(f"Processing {len(remaining)} remaining rows...")

    for i, (_, row) in enumerate(remaining.iterrows()):
        cik = row["cik_padded"]
        accession_no = row["accession_no"]
        accession_nodash = accession_no.replace("-", "")
        departure_phrase = row["matched_phrase"]

        url = f"https://www.sec.gov/Archives/edgar/data/{int(cik)}/{accession_nodash}/{accession_no}.txt"

        try:
            resp = requests.get(url, headers=HEADERS, timeout=15)
            if resp.status_code != 200:
                failures.append({"accession_no": accession_no, "ticker": row["ticker"], "error": f"HTTP {resp.status_code}"})
                time.sleep(DELAY)
                continue

            text = extract_filtered_text(resp.text)

            if not text:
                # No 8-K / EX-99.x block found — log it rather than silently
                # marking verified=False on an empty search space.
                failures.append({
                    "accession_no": accession_no,
                    "ticker": row["ticker"],
                    "error": "no primary 8-K or EX-99.x document block found"
                })
                time.sleep(DELAY)
                continue

            snippet = check_proximity(text, departure_phrase)

            verified = snippet is not None
            results.append({
                "accession_no": accession_no,
                "ticker": row["ticker"],
                "cik_padded": cik,
                "file_date": row["file_date"],
                "matched_phrase": departure_phrase,
                "verified": verified,
                "snippet": snippet[:400] if snippet else ""
            })

        except Exception as e:
            failures.append({"accession_no": accession_no, "ticker": row["ticker"], "error": str(e)})

        # flush every 50 rows so a crash doesn't lose progress
        if len(results) >= 50:
            pd.DataFrame(results).to_csv(OUTPUT_PATH, mode="a", header=not os.path.exists(OUTPUT_PATH), index=False)
            results = []

        if (i + 1) % 100 == 0:
            print(f"  {i+1}/{len(remaining)} processed...")

        time.sleep(DELAY)

    # flush any remainder
    if results:
        pd.DataFrame(results).to_csv(OUTPUT_PATH, mode="a", header=not os.path.exists(OUTPUT_PATH), index=False)

    if failures:
        pd.DataFrame(failures).to_csv(FAILED_LOG_PATH, index=False)
        print(f"\n{len(failures)} fetch failures logged to {FAILED_LOG_PATH}")

    # summary
    final_df = pd.read_csv(OUTPUT_PATH)
    verified_count = final_df["verified"].sum()
    print(f"\nDone. {verified_count} / {len(final_df)} rows verified as true CFO-departure proximity matches.")


if __name__ == "__main__":
    main()