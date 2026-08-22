import sqlite3
from datetime import datetime

FILING_DATE = "2026-07-29"
TICKER = "VFC"
BENCHMARK = "SPY"
DB_PATH = "data/filings.db"
THRESHOLD = 0.005  # 0.5% — tune this later

def get_prices(conn, ticker):
    rows = conn.execute(
        "SELECT date, adj_close FROM prices WHERE ticker = ? ORDER BY date",
        (ticker,)
    ).fetchall()
    return {date: adj_close for date, adj_close in rows}

def main():
    conn = sqlite3.connect(DB_PATH)
    vfc = get_prices(conn, TICKER)
    spy = get_prices(conn, BENCHMARK)

    dates = sorted(set(vfc.keys()) & set(spy.keys()))
    event_idx = dates.index(FILING_DATE)

    # 3-trading-day window: filing date + next 2 trading days
    window_dates = dates[event_idx: event_idx + 3]
    print("Event window:", window_dates)

    abnormal_return = 0.0
    for i in range(1, len(window_dates)):
        d0, d1 = window_dates[i - 1], window_dates[i]
        vfc_ret = (vfc[d1] - vfc[d0]) / vfc[d0]
        spy_ret = (spy[d1] - spy[d0]) / spy[d0]
        ar = vfc_ret - spy_ret
        abnormal_return += ar
        print(f"{d0} -> {d1}: VFC {vfc_ret:.4f}, SPY {spy_ret:.4f}, AR {ar:.4f}")

    if abnormal_return > THRESHOLD:
        label = "Positive"
    elif abnormal_return < -THRESHOLD:
        label = "Negative"
    else:
        label = "Neutral"

    print(f"\nCumulative abnormal return: {abnormal_return:.4f}")
    print(f"Label: {label}")

    conn.execute(
        "UPDATE filings SET abnormal_return = ?, label = ? WHERE ticker = ? AND filing_date = ?",
        (abnormal_return, label, TICKER, FILING_DATE)
    )
    conn.commit()
    conn.close()

if __name__ == "__main__":
    main()