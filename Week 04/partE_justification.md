# Part E — Justification for the e-commerce review figure

Figure: `partD_figure.png`. Script: `partD_figure.py`. Source data: `sessions_hourly.csv` (12,670 rows, Apr 2024 to 11 Sep 2025) and `revenue_catalogue.csv`. All data is synthetic (CDB601220).

## 1. Each panel, its question, its chart and its channel rule

- **Panel 1, daily sessions.** Question: is daily traffic rising, and how big are the spikes? Line chart, raw in grey with a centred 7-day mean. Channel rule (Week 2): position on a common scale is the most accurate channel for trend, so a line on a zero baseline.
- **Panel 2, weekday by hour heatmap.** Question: when in the week and day are sessions highest? Heatmap with a sequential colormap, because mean sessions has no midpoint (Week 3). Colour carries magnitude only, so the peak is named in the title.
- **Panel 3, treemap of net revenue.** Question: where does the revenue mass sit? Area encodes the value, which is read only to about ±20% (slide 45), so each block prints its value. One hue per category keeps the parent visible.
- **Panel 4, sorted bars.** Question: by how much does each sub-category differ? Position on a shared baseline (Week 2: position beats length beats area), with values printed. It answers the same question as panel 3 in the channel that reads accurately.

## 2. Time and aggregation decisions

- **Parse.** Two formats, parsed separately with explicit formats. Slash dates are day-first: 2,151 slash rows have a first field above 12, which cannot be a month. The 1,500 ambiguous rows are resolved by format, not guessed. `format="mixed"` was not used.
- **Aggregation.** `sessions` is a flow, so a day is the sum of its filed hours. A day needs at least 21 of 24 hours; 215 days with 21–23 hours are scaled by 24 over the filed hours (a 23-hour day moves by +4.3%). The 13 wholly unfiled days stay NaN and break the line. The day total is never averaged over missing hours.
- **Window: 7 days, centred.** Chosen on the weekly cycle. The 7-day mean removes the day-of-week pattern exactly; the weekly seasonal component has a peak-to-trough of 7,569 sessions per day (partB Q3). It costs 3 days at each end. Centred, because this is a report; the morning dashboard must use a trailing mean, which runs about 15 days late (partB Q4).
- **Partial month.** September 2025 is partial (last filed hour 11 Sep). It is excluded from the analysis, not drawn at full weight.

## 3. The window declaration

The window (7 days, centred) was fixed before plotting, on the weekly cycle. The series is shown from its first recorded day, 1 April 2024; no start date was selected. Part B Q5 reports every start and length (12 × 5): 33 combinations rise and 27 fall, because short windows on this series depend on where they start. The 28-day version gives the same direction over the full series (slope +21.0 sessions per day against +21.0 for the 7-day). I did not choose the window to strengthen a conclusion; the 7-day choice was made from the cycle.

## 4. Removed and changed rows

| Rule | Count | Effect |
|---|---|---|
| Sessions = −1 (not-available code) set to NaN; orders and revenue kept | 290 | sessions NaN on those hours, not zero |
| Exact duplicate hours, one copy kept | 286 | 12,670 → 12,384 hours |
| Hours nobody filed, left absent | 312 | 13 whole days, not filled |
| Partial September 2025, excluded from analysis | 255 filed hours | the series ends 31 Aug 2025 |
| Duplicate SKU-0127 under Wearables, dropped (Audio copy kept) | 1 | Wearables 174.79 → 159.96 PKR m; share 10.13% → 9.35% |
| Negative net-revenue rows: kept, not drawn as area | 7 | sum −1.07 PKR m, netted in sub-category totals |

Checks: sub-category shares match `shares_eight.csv` within 0.24 points (tolerance 0.3).

## 5. Levels rolled up

- **Categories:** 4 (Mobile, Computing, Audio & Imaging, Lifestyle), each drawn as a hue.
- **Sub-categories:** 8, each drawn as a block and a bar. The treemap depth stops here because the eight shares are the object of the comparison, and it sits within the 4 ± 1 chunking limit.
- **Other:** none. Every sub-category is above the 1% threshold (smallest, Drones, 2.4%), so no bucket is hidden. The script prints this as "no categories below 1.0%".
- **SKU level:** 344 SKUs, not drawn; a treemap of 344 blocks is unreadable.
