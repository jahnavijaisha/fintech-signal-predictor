import requests

HEADERS = {"User-Agent": "jahnavitulluru8@gmail.com"}
SEARCH_URL = "https://efts.sec.gov/LATEST/search-index"

# Test on Apple (CIK 0000320193) — a company we know has CFO-related 8-Ks
test_cik = "0000320193"

# Test 1: just "Chief Financial Officer" alone
params_broad = {
    "q": '"Chief Financial Officer"',
    "forms": "8-K",
    "ciks": test_cik,
}
resp_broad = requests.get(SEARCH_URL, headers=HEADERS, params=params_broad)
total_broad = resp_broad.json().get("hits", {}).get("total", {}).get("value", 0)

# Test 2: "Chief Financial Officer" AND "resignation"
params_narrow = {
    "q": '"Chief Financial Officer" "resignation"',
    "forms": "8-K",
    "ciks": test_cik,
}
resp_narrow = requests.get(SEARCH_URL, headers=HEADERS, params=params_narrow)
total_narrow = resp_narrow.json().get("hits", {}).get("total", {}).get("value", 0)

print(f"'Chief Financial Officer' alone: {total_broad} results")
print(f"'Chief Financial Officer' + 'resignation': {total_narrow} results")