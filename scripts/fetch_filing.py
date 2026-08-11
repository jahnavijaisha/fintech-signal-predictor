"""
Step 3: Pull a real SEC 8-K filing for VF Corp (VFC) and save it locally.

SEC EDGAR requires a descriptive User-Agent on every request (it will
403/block generic ones) — put your real name/email in USER_AGENT below.
Docs: https://www.sec.gov/os/webmaster-faq#developers
"""

import json
import re
import time
from pathlib import Path

import requests

USER_AGENT = "T Jahnavi Jaisha - fintech-signal-predictor research contact jahnavitulluru8@gmail.com"  # <-- edited 
HEADERS = {"User-Agent": USER_AGENT}

VFC_CIK = "0000103379"
RAW_DIR = Path("data/raw")


def get_filing_index(cik: str) -> dict:
    """Pull the full list of a company's filings from EDGAR's submissions API."""
    url = f"https://data.sec.gov/submissions/CIK{cik}.json"
    resp = requests.get(url, headers=HEADERS, timeout=30)
    resp.raise_for_status()
    return resp.json()


def find_8k_filings(index: dict) -> list[dict]:
    """Filter the submissions JSON down to Form 8-K filings, most recent first."""
    recent = index["filings"]["recent"]
    filings = []
    for i, form in enumerate(recent["form"]):
        if form == "8-K":
            filings.append(
                {
                    "accessionNumber": recent["accessionNumber"][i],
                    "filingDate": recent["filingDate"][i],
                    "primaryDocument": recent["primaryDocument"][i],
                }
            )
    return filings


def build_doc_url(cik: str, accession_no: str, primary_doc: str) -> str:
    acc_no_dashes_removed = accession_no.replace("-", "")
    cik_no_zeros = str(int(cik))
    return (
        f"https://www.sec.gov/Archives/edgar/data/"
        f"{cik_no_zeros}/{acc_no_dashes_removed}/{primary_doc}"
    )


def fetch_and_save(url: str, out_path: Path) -> str:
    resp = requests.get(url, headers=HEADERS, timeout=30)
    resp.raise_for_status()
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(resp.text, encoding="utf-8")
    return resp.text


def has_item_502(html_text: str) -> bool:
    return bool(re.search(r"Item\s*5\.02", html_text, re.IGNORECASE))


if __name__ == "__main__":
    print("Fetching VFC filing index from EDGAR...")
    index = get_filing_index(VFC_CIK)
    eightks = find_8k_filings(index)
    print(f"Found {len(eightks)} 8-K filings on record.")

    # SEC asks for <=10 requests/sec; we're doing far fewer, but pause
    # politely between calls anyway.
    for f in eightks[:15]:  # just scan the most recent 15 to start
        url = build_doc_url(VFC_CIK, f["accessionNumber"], f["primaryDocument"])
        print(f"  checking {f['filingDate']}  {url}")
        time.sleep(0.3)
        try:
            text = requests.get(url, headers=HEADERS, timeout=30).text
        except requests.RequestException as e:
            print(f"    fetch failed: {e}")
            continue

        if has_item_502(text):
            out_name = f"VFC_8K_{f['filingDate']}.htm"
            out_path = RAW_DIR / out_name
            out_path.parent.mkdir(parents=True, exist_ok=True)
            out_path.write_text(text, encoding="utf-8")
            print(f"    -> Item 5.02 found. Saved to {out_path}")
            break
    else:
        print("No Item 5.02 8-K found in the most recent 15 filings.")