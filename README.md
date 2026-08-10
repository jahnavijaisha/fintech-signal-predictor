# FinTech Signal Predictor

Predicts short-term abnormal stock returns following CFO departure 
announcements, using SEC EDGAR filings and market price data.

## Problem
Given a CFO departure announcement (SEC 8-K, Item 5.02) for an S&P 500 
company, predict whether the stock's abnormal return (vs. SPY) over 
the next 3 trading days will be Positive, Negative, or Neutral (±1%).

## Status
🚧 In progress — Day 1: environment setup + pipeline test on VFC

## Data Sources
- SEC EDGAR 8-K Item 5.02 filings (event timestamps)
- Yahoo Finance adjusted daily closes (target ticker + SPY benchmark)

## Success Metric
Beat 33% baseline accuracy, measured via macro F1 on held-out test set.