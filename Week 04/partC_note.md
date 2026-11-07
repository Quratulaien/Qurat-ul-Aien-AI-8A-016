# Part C — Part-to-whole legality, and the ranking test

## 1. Legality (slide 32), computed by `partC_shares.py`

| Table | Exclusive | Whole meaningful | Share is the question | Verdict |
|---|---|---|---|---|
| Four `touch_*` columns, case 8 | No: sum 130.98%; 1,105 customers (27.6%) touched by two or more channels | Customers, yes; but the parts overlap | Reach, not share | **Neither.** Draw reach bars with a 100% reference. |
| `shares_eight.csv`, eight sub-categories | Yes: each SKU appears once after the dedupe | Net revenue of the catalogue | Yes: the claim is a ranking | **Pie legal**, bars preferred for ranking (position beats angle, Week 2). |
| Premium vs other, 2025Q4 | Yes: 38.0% + 62.0% = 100% | Total revenue, yes | No: the claim is about change over time, which one quarter's split cannot show | **Neither.** Show premium in absolute terms, indexed to total (Part A case 9). |

## 2. Stimuli (no numbers on either)

- `partC_stim_pie.png`: the eight shares as a pie in file order (A–H), `startangle=90, counterclock=False`.
- `partC_stim_bars.png`: the same eight, sorted, zero-based, letters only.

True rank order, largest first: **A B C H G D E F** (24.6, 18.4, 15.0, 13.1, 11.2, 9.2, 6.1, 2.4).

## 3. The reader trial: NOT RUN

`pie_ranking_results.csv` is an empty template. No reader has been run, so no times, errors or scores are reported here. The brief forbids inventing these, and this file does not contain any.

To run it, a person runs `python3 partC_reader_trial.py --reader R1 --first pie` (alternate `--first bars` between readers so learning does not favour one stimulus). The script times each answer with `time.perf_counter()` and scores the order against the true rank.

What the result needs to support: the deck predicts that readers get A and B right and disagree about the middle three (C, H, G are 15.0, 13.1 and 11.2%, about two points apart). One reader is one reader; a result from one person can suggest a pattern, not establish one.

## 4. Rule (provisional until the trial is run)

Draw a pie only when the parts are exclusive, sum to a meaningful whole, the question is about each part's share of that whole, and there are no more than about three slices with values readable from labels. For ranking eight parts, draw sorted bars.
