# Model Card: Event-Driven Risk & Sentiment Signal Platform — Baseline Model

## Overview
Predicts short-term stock volatility risk following CFO departure announcements in
S&P 500 companies. Output is a 3-class label (Negative / Neutral / Positive) describing
the 3-trading-day market-adjusted abnormal return after the filing date.

## Intended Use
Portfolio/demonstration project targeting fintech risk, data, and RegTech hiring teams.
Not intended for live trading or investment decisions. Demonstrates an end-to-end
event-study pipeline: SEC EDGAR ingestion → event verification → price labeling →
feature engineering → modeling, with an emphasis on methodological honesty over
inflated performance claims.

## Data
- **Source**: SEC EDGAR 8-K filings (Item 5.02) for S&P 500 companies, cross-referenced
  with Yahoo Finance adjusted daily closes (event ticker + SPY as market benchmark).
- **Event definition**: CFO departure announcements, confirmed via a two-stage filter —
  (1) SEC full-text search for departure-related phrases co-occurring with "Chief
  Financial Officer" mentions, (2) a proximity check requiring the matched phrase and
  CFO language to appear within 200 characters of each other, restricted to the primary
  8-K body and EX-99.x press-release exhibits (excluding boilerplate bylaws/contract
  exhibits, which were a major source of false positives in early filtering — see
  Known Limitations).
- **Final dataset**: 496 labeled events (of 506 verified true positives, less 3 events
  with untradeable/delisted tickers, less 3 events with insufficient price history for
  feature computation), spanning 2001–2026.
- **Label**: 3-day cumulative abnormal return vs. SPY, thresholded at ±0.5% (fixed
  threshold, not a tertile split — chosen to reflect real economic significance rather
  than force an artificial balanced split).
- **Label distribution**: Negative 47.4%, Positive 33.3%, Neutral 19.3% (consistent
  across train/val/test splits, see below).

## Train/Val/Test Split
- **Chronological, not random** — split by filing date to prevent any future-information
  leakage into training, matching realistic deployment (predicting genuinely unseen
  future events).
- Train: 346 events, 2001-01-18 to 2019-12-23
- Val: 74 events, 2020-02-18 to 2023-08-10
- Test: 76 events, 2023-08-17 to 2026-08-25
- **Note**: the three splits span materially different market regimes (train ends
  pre-COVID; val opens near the COVID crash; test covers the post-COVID/rate-hike
  era). This is a deliberate, honest consequence of chronological splitting, not an
  artifact to correct — but it does mean val and test performance are not directly
  comparable to each other, since they represent different market conditions.

## Baseline Model
- **Algorithm**: Random Forest (n_estimators=300, max_depth=6, class_weight=balanced)
- **Features (8)**: 30d/90d volatility and momentum for the event ticker, 30d
  volatility/momentum for SPY (market context), filing word count, negative-word count
  from the filing text.
- **Feature selection**: started from 13 candidate features (the above 8, plus 5
  binary keyword flags — has_interim, has_immediate, has_named_successor,
  has_retirement, has_search_committee); the 5 flags were dropped after showing
  near-zero feature importance (<0.02 each) in an initial run, and validation
  macro F1 improved after removing them.
- **Model selection**: chosen via grid search over {Logistic Regression, Random Forest}
  × {13-feature, 8-feature} × {class_weight balanced/none}, selecting on **validation**
  macro F1 only. Test set was not touched during model selection.

## Results
- **Majority-class baseline** (always predict "Negative"): macro F1 = 0.226 (test)
- **Selected baseline model**: macro F1 = 0.311 (val, selection metric) / **0.334 (test)**
- Improvement over majority baseline: **+0.108 macro F1** on test.

| Class    | Precision | Recall | F1   | Support (test) |
|----------|-----------|--------|------|-----------------|
| Negative | 0.54      | 0.51   | 0.53 | 39              |
| Neutral  | 0.12      | 0.17   | 0.14 | 12              |
| Positive | 0.35      | 0.32   | 0.33 | 25              |

### Feature Importance (Random Forest)
Pre-event price/volatility features dominate; filing-text features contribute
comparatively little:

1. volatility_30d — 0.149
2. momentum_30d — 0.148
3. momentum_90d — 0.143
4. volatility_90d — 0.133
5. filing_word_count — 0.122
6. mkt_momentum_30d — 0.118
7. mkt_volatility_30d — 0.115
8. negative_word_count — 0.073

## Known Limitations
1. **Neutral class is poorly predicted** (F1 = 0.14) across every configuration
   tested. With only ~95-100 Neutral examples total across all splits, the model has
   limited ability to distinguish "no meaningful reaction" from noise at the class
   boundaries. This is the weakest part of the baseline and the main target for
   improvement in later modeling stages.
2. **Val/test model-selection variance**: the configuration that scored best on
   validation (0.311 macro F1) was *not* the best-scoring configuration on test — an
   untuned 13-feature Random Forest variant scored 0.377 on this same test set. This
   is a direct consequence of small val/test sizes (74/76 events) and illustrates
   that single-run macro F1 on a dataset this size carries meaningful variance.
   Reported results follow proper validation discipline (test touched exactly once,
   after model selection was finalized on val), which is procedurally correct even
   though it does not yield the highest possible test score.
3. **Confound checking was not performed at scale.** `is_confounded` was manually
   verified only for the single VFC pilot event (Step 4/5); for the remaining 495
   events in the full dataset, it is defaulted to unchecked. This means some labeled
   events may have concurrent, unrelated news (earnings releases, M&A activity,
   litigation) within the same 3-day window, which would contaminate the abnormal-
   return label independent of the CFO departure itself. This is a real limitation on
   label quality that has not yet been addressed.
4. **Filing-text features are shallow.** The 5 keyword-flag features tested
   (has_interim, has_retirement, etc.) showed almost no predictive value, suggesting
   simple keyword matching does not capture meaningful sentiment/severity signal in
   the filing language. This motivates moving to transformer-based text embeddings
   (planned next step) rather than concluding that filing text is uninformative.
5. **Regime shift across splits.** Train, val, and test each cover different market
   conditions (pre-COVID, COVID-adjacent, post-COVID/rate-hike), which is realistic
   for a deployment scenario but means this single chronological split may not fully
   characterize model stability across market regimes.

## FinBERT Fusion Model (Update)

Replaced the shallow keyword-flag text features with FinBERT (`ProsusAI/finbert`)
embeddings of the filing text (mean-pooled over tokens, 768-dim), reduced via PCA
and fused with the same 8 price/market features from the baseline.

- **Model selection**: grid search over {Logistic Regression, Random Forest} ×
  {5, 10, 20, 50 PCA components} × {class_weight balanced/none}, selected on
  **validation** macro F1 only, same discipline as the baseline. PCA was fit on
  train only, to avoid leaking val/test information into the dimensionality
  reduction itself.
- **Selected config**: Logistic Regression, 8 price features + 20 PCA components
  (92.8% explained variance retained), class_weight=balanced. Val macro F1 = 0.364.
- **Final test result (touched once)**: macro F1 = **0.375**, vs. 0.334 for the
  price-only baseline (+0.041) and 0.226 for the majority-class baseline.

| Class    | Precision | Recall | F1   | (baseline F1) |
|----------|-----------|--------|------|----------------|
| Negative | 0.57      | 0.74   | 0.64 | 0.53           |
| Neutral  | 0.12      | 0.08   | 0.10 | 0.14           |
| Positive | 0.47      | 0.32   | 0.38 | 0.33           |

**Honest interpretation**: the aggregate improvement is real, but it is not evenly
distributed. FinBERT embeddings sharpened the Negative/Positive distinction
(Negative recall +0.23) but made the Neutral-class problem slightly *worse*
(F1 0.14 → 0.10; only 1 of 12 true Neutral test events was correctly identified,
with 10 misclassified as Negative). This suggests the added text signal increases
the model's confidence toward directional outcomes without helping it recognize
"no meaningful reaction" — the dataset's smallest and already weakest class.
Limitation #1 from the baseline (Neutral-class weakness) is therefore **not
resolved** by this model and remains the primary target for future work, rather
than something transformer embeddings alone fixed.

## Next Steps
- Address the Neutral-class weakness directly — e.g. class-specific threshold
  tuning, oversampling (SMOTE or similar) restricted to train only, or reframing
  as two binary problems (directional vs. non-event) before combining.
- Investigate confound-checking at scale (limitation 3) before treating labels as
  ground truth for any published results.
- Consider repeated/rolling-window validation to better characterize variance
  (limitation 2), if time permits within the project timeline.
- MLOps/cloud deployment phase (per original roadmap Phase 4) once modeling work
  is considered sufficiently mature.