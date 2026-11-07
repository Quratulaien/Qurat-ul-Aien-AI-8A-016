# Week 4 — time series, proportions and hierarchies

Run in this order, from this folder:

1. `python3 partA_charts.py` — rebuilds the nine published charts beside their redesigns (`partA_case01..09.png`); self-check numbers print to the terminal.
2. `python3 partB_windows.py > partB_output.txt` — window report, smoothers at Black Friday, decomposition, lag and the 12 × 5 window loop.
3. `python3 partC_shares.py` — legality verdicts and the two ranking stimuli; `pie_ranking_results.csv` is an empty template (the reader trial is run by a person with `partC_reader_trial.py`).
4. `python3 partD_figure.py` — the 2×2 e-commerce figure (`partD_figure.png`), plus `partD_decisions.md` and `partD_audit.txt`.

Requirements: `pip install -r requirements.txt`. The cleaning shared by Parts B and D is in `sessions_clean.py`; `tslib.py` and `vizlib.py` are the Week 4 and Week 3 toolkits.

Written work: `partA_diagnosis.md` / `.pdf` (Part A), `partC_note.md` (Part C), `partE_justification.md` / `.pdf` (Part E, one page). The data is synthetic (CDB601220).

Bonus (Part F, optional): `python3 partF_cycle.py` on the Our World in Data file in `bonus_F_data/` (source and download date in `download_stamp.txt`; the 98 MB CSV is excluded from the zip and re-downloaded from the URL in `partF_note.md`). Writes `partF_cycle.png`, `partF_audit.txt`; the answer is in `partF_note.md`.

Status: Parts A–E complete. Part C's reader trial still needs a person to run it (`pie_ranking_results.csv` is empty on purpose).
