#!/usr/bin/env python3
"""
partC_shares.py — Part C: part-to-whole legality, and the stimuli for the ranking test.

  1. the three share tables, tested against slide 32's conditions — printed verdicts
  2. the two stimuli, PNGs with NO numbers on them:
       partC_stim_pie.png    the eight shares as a pie, file order, startangle=90, counterclock=False
       partC_stim_bars.png   the same eight as sorted horizontal bars
  3. pie_ranking_results.csv — an EMPTY template. No reader has been run by this script.

The reader trial itself is run by a person: see partC_reader_trial.py.
"""
from __future__ import annotations

import os
import sys

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import tslib  # noqa: E402
from vizlib import PALETTE, style_defaults, save_fig  # noqa: E402
import sessions_clean as sc  # noqa: E402

D = os.path.join(HERE, "data")
style_defaults()
C = PALETTE

# ============================================================ 1. legality
print("=" * 78)
print("1. Part-to-whole legality (slide 32): exclusive parts, meaningful whole, share is the question")
print("=" * 78)

case8 = pd.read_csv(os.path.join(D, "case08_channel_attrib.csv"))
touch = [c for c in case8.columns if c.startswith("touch_")]
ex = tslib.exclusivity_check(case8, touch)
print("\n(a) four touch_* columns, case08 (4,000 customers)")
print(f"    shares: {ex['shares_pct']}")
print(f"    sum = {ex['sum_pct']}%   exclusive = {ex['exclusive']}   "
      f"customers touched by 2+ channels = {ex['n_multi']} ({ex['pct_multi']}%)   zero-touch = {ex['n_zero']}")
print("    VERDICT: neither a pie nor a bar of shares. The four rates are reach (who was touched),")
print("             and they overlap. Draw reach bars with a 100% reference, not a share.")

shares = pd.read_csv(os.path.join(D, "shares_eight.csv"))
assert abs(shares.share_pct.sum() - 100) < 1e-6, "shares_eight does not sum to 100"
c_cat, _, _ = sc.load_catalogue(os.path.join(D, "revenue_catalogue.csv"))
sub = c_cat.groupby("subcategory").net_revenue_pkr_m.sum()
dup_free = not c_cat.sku.duplicated().any()
print("\n(b) shares_eight.csv: eight sub-categories")
print(f"    sum = {shares.share_pct.sum():.1f}%  (assertion passed)")
print(f"    exclusive: each SKU appears once after the dedupe = {dup_free}")
print("    meaningful whole: net revenue of the eight sub-categories, negatives netted inside")
print("    share is the question: the claim is about ranking, so yes")
print("    VERDICT: a pie is LEGAL here. The ranking is still read better as bars")
print("             (position beats angle, Week 2), which is what the Part C test measures.")

prem = pd.read_csv(os.path.join(D, "case09_premium_share.csv")).set_index("quarter")
q4 = prem.loc["2025Q4"]
other = q4.total_revenue_pkr_m - q4.premium_revenue_pkr_m
two = pd.Series({"premium": q4.premium_revenue_pkr_m, "other": other})
tshares = two / two.sum() * 100
print("\n(c) premium vs other revenue, 2025Q4")
print(f"    premium {q4.premium_revenue_pkr_m} / other {other:.1f} of total {q4.total_revenue_pkr_m}")
print(f"    shares: {tshares.round(2).to_dict()}   sum = {tshares.sum():.1f}%")
print("    exclusive: yes (two parts, one revenue each). whole: total revenue, yes.")
print("    share is the question: NO. The claim is that premium's SHARE rose; this is one quarter's")
print("    composition, and the change lives in the denominator (Part A case 9).")
print("    VERDICT: neither. A single-quarter 2-slice pie can be drawn, but it cannot show the claim.")
print("             Show premium in absolute terms, indexed, against total.")

# ============================================================ 2. stimuli
print("\n" + "=" * 78)
print("2. Stimuli (no numbers, no percentages, file order for the pie)")
print("=" * 78)

letters = shares.slice.tolist()
vals = shares.share_pct.values
true_rank = shares.sort_values("share_pct", ascending=False).slice.tolist()
print("true rank order (largest first):", " ".join(true_rank))
assert true_rank == ["A", "B", "C", "H", "G", "D", "E", "F"], true_rank

# pie: file order, startangle=90, counterclock=False, letters only
fig, ax = plt.subplots(figsize=(6.4, 6.4))
ax.pie(vals, labels=letters, startangle=90, counterclock=False,
       colors=[C["series"][i % len(C["series"])] for i in range(8)],
       wedgeprops=dict(edgecolor="white"), textprops=dict(fontsize=14))
ax.set_aspect("equal")
ax.set_title("Which sub-category is largest? Write A–H in order, largest first", fontsize=11, loc="left")
save_fig(fig, os.path.join(HERE, "partC_stim_pie.png"))
plt.close(fig)

# bars: sorted, letters only, no values
srt = shares.sort_values("share_pct", ascending=False).reset_index(drop=True)
fig, ax = plt.subplots(figsize=(6.4, 5.2))
ypos = np.arange(len(srt))[::-1]
ax.barh(ypos, srt.share_pct.values, color=C["series"][0], height=0.6)  # zero-based, no values printed
ax.set_xlim(0, srt.share_pct.max() * 1.05)
ax.set_yticks(ypos)
ax.set_yticklabels(srt.slice.tolist(), fontsize=13)
ax.set_xticks([])
for s in ["top", "right", "bottom"]:
    ax.spines[s].set_visible(False)
ax.set_title("Which sub-category is largest? Write A–H in order, largest first", fontsize=11, loc="left")
save_fig(fig, os.path.join(HERE, "partC_stim_bars.png"))
plt.close(fig)
print("wrote partC_stim_pie.png and partC_stim_bars.png (both 300 dpi, letters only)")

# ============================================================ 3. template
tmpl = pd.DataFrame(columns=["stimulus", "reader_id", "trial_no", "order_given",
                             "seconds", "n_wrong_positions", "wrong_positions_note"])
out = os.path.join(HERE, "pie_ranking_results.csv")
if not os.path.exists(out):
    tmpl.to_csv(out, index=False)
print(f"template written: pie_ranking_results.csv (no rows: no reader has been run)")
print("true order for scoring: " + " ".join(true_rank))
print("\nPrediction in the brief, to test: C (15.0%), H (13.1%), G (11.2%) are about 2 points apart;")
print("readers should get A, B right and disagree about the middle three.")
