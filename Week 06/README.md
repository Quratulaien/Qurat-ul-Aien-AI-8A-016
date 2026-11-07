# Week 6 — integration checkpoint (Parts A–C)

Run from this folder, in this order:
1. `python3 partA_process.py` — audits the raw CSVs and GeoJSON, applies the rules, writes `clean/` and `partA_audit.txt` and `partA_decisions.md`.
2. `python3 partB_charts.py` — writes `partB_1.png`, `partB_2.png`, `partB_3.png` from `clean/`.
3. `python3 partC_figure.py` — writes `partC_figure.png` (300 dpi) and prints the reliability anchors.

`partC_note.md` is the half-page note for the board. Raw files in `data/` are never written to.
Toolkits `vizlib.py`, `tslib.py`, `geolib.py` are the course versions, unchanged.
