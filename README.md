# Event-Driven Risk & Sentiment Signal Platform

Predicting short-term stock volatility risk around corporate disclosure events (starting with CFO departures), using SEC EDGAR filings and market price data — with an event-study methodology instead of naive price prediction.

## Problem
Corporate 8-K filings (leadership changes, litigation, etc.) often precede meaningful stock price moves, but there's no simple way to quantify *how much* of that move is attributable to the event itself versus broader market conditions. This project builds a labeled dataset and eventual prediction model to answer that.

## Approach
- **Event source:** SEC EDGAR 8-K filings, Item 5.02 (officer departures), starting with CFO transitions across the S&P 500
- **Label:** market-adjusted cumulative abnormal return (CAR) over a 3-trading-day window — stock return minus S&P 500 (SPY) return — classified Positive / Negative / Neutral
- **Why market-adjusted:** isolates the event's signal from a broad market move on the same days

## Status
Pipeline validated end-to-end on a real case (VF Corp, 2026-07-29 CFO-departure 8-K):

| Step | What it does | Status |
|---|---|---|
| 1. Filing ingestion | Pull 8-K from SEC EDGAR | ✅ |
| 2. Storage | SQLite schema for filings + prices | ✅ |
| 3. Price data | Pull adjusted daily closes (ticker + SPY) via Yahoo Finance | ✅ |
| 4. Labeling | Compute 3-day cumulative abnormal return, classify label | ✅ |
| 5. Scale to full S&P 500 CFO-departure history | — | 🔜 |

**Example result:** VFC's stock dropped ~17% on the filing date; after adjusting for market movement, the 3-day cumulative abnormal return was **-7.47%**, labeled **Negative**.

## Stack
Python, SQLite (SQL warehouse planned as volume grows), yfinance, SEC EDGAR API. PyTorch/HuggingFace planned for the modeling phase.

## Roadmap
1. Data pipeline & warehouse (current)
2. Baseline + LSTM/transformer modeling
3. NLP event classification (filing text → structured signal)
4. MLOps / cloud deployment
5. Documentation & model cards
