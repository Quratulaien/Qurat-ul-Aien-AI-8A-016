#!/usr/bin/env python3
"""
partB_charts.py — three charts from the cleaned data, three different questions.

    partB_1.png  TREND        network energy per day, by month     (grid_daily)
    partB_2.png  COMPOSITION  generation mix, 100% by month        (generation_mix)
    partB_3.png  DISTRIBUTION outage minutes per zone-day, by zone (grid_daily)

Every parameter that changes the picture is printed on the figure: the
aggregation, the window, the period, anything excluded. Run:

    python3 partB_charts.py          (after partA_process.py)
"""
from __future__ import annotations

import os
import sys

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import matplotlib.ticker  # noqa: E402
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import tslib  # noqa: E402
from vizlib import PALETTE, style_defaults, save_fig  # noqa: E402

CLEAN = os.path.join(HERE, "clean")
SOURCE = ("Source: synthetic CDB601220 Week 6 data, cleaned by partA_process.py "
          "(see partA_decisions.md).")
style_defaults()

# =========================================================================
# B1 — TREND: network energy delivered per day, by month
# =========================================================================
g = pd.read_csv(os.path.join(CLEAN, "grid_daily_clean.csv"), parse_dates=["date"])
rep = g[g.reported & g.energy_mwh.notna()].copy()
rep["span"] = rep.span_days.astype(int)
rep["rate"] = rep.energy_mwh / rep.span           # MWh per day over the span

# Spread each reading's rate over every day its span covers. This is how a
# gap is handled without interpolation: the energy is counted once, over the
# days it actually spans.
offs = np.concatenate([np.arange(s) for s in rep.span])
rep_x = rep.loc[rep.index.repeat(rep.span)].reset_index(drop=True)
rep_x["day"] = rep_x.date - pd.to_timedelta(rep_x.span - 1 - offs, unit="D")
rep_x["month"] = rep_x.day.dt.to_period("M")

zone_month = rep_x.groupby(["zone", "month"]).rate.mean().unstack("zone")
network = zone_month.sum(axis=1)          # sum of the six zones' mean MWh/day
days_per_month = rep_x.groupby("month").day.nunique()

last_day = g.date.max()
partial = [m for m in network.index if m.end_time.normalize() > last_day]
complete = network.drop(index=partial)
b1_first, b1_last = complete.iloc[0], complete.iloc[-1]
b1_growth = (b1_last / b1_first - 1) * 100

fig, ax = plt.subplots(figsize=(9, 4.6))
x = np.arange(len(complete))
ax.plot(x, complete.values, color=PALETTE["series"][0], marker="o", markersize=4)
ax.set_ylim(0, complete.max() * 1.15)
ax.set_xticks(x[::2])
ax.set_xticklabels([m.strftime("%b %y") for m in complete.index[::2]], rotation=0)
ax.set_ylabel("Energy delivered, MWh per day\n(mean of days with a reading)")
ax.yaxis.set_major_formatter(matplotlib.ticker.StrMethodFormatter("{x:,.0f}"))
ax.set_xlabel("Month")
ax.annotate(f"{b1_first/1e3:,.0f}k", (x[0], b1_first), textcoords="offset points",
            xytext=(6, -14), fontsize=8, color=PALETTE["ink_soft"])
ax.annotate(f"{b1_last/1e3:,.0f}k", (x[-1], b1_last), textcoords="offset points",
            xytext=(-6, 8), ha="right", fontsize=8, color=PALETTE["ink"])
ax.set_title(f"Network energy per day rose {b1_growth:.0f}% from {complete.index[0].strftime('%b %Y')} "
             f"to {complete.index[-1].strftime('%b %Y')}", loc="left")
fig.text(0.01, 0.885,
         "Decision supported: sizing next year's reliability budget against a base that is growing, not flat.",
         fontsize=8.5, color=PALETTE["ink_soft"])
pct_note = (f"Aggregation: mean MWh per day per zone over the days each reading covers, "
            f"summed over six zones. Period: {complete.index[0]} to {complete.index[-1]} "
            f"(complete months). Excluded: {', '.join(str(m) for m in partial)} "
            f"(partial, data ends 11 Sep 2026). Gaps: not interpolated; a gap's energy is "
            f"counted once over the days it spans. 1 Apr 2025 has no baseline and is not counted.")
ax.text(0, -0.26, "\n".join(__import__("textwrap").wrap(pct_note, 150)), transform=ax.transAxes,
        fontsize=6.8, color=PALETTE["ink_soft"], va="top")
save_fig(fig, os.path.join(HERE, "partB_1.png"), note=SOURCE)
plt.close(fig)
print(f"B1 network MWh/day: {complete.index[0]} {b1_first:,.0f} -> {complete.index[-1]} "
      f"{b1_last:,.0f}  ({b1_growth:+.1f}%); partial excluded: {partial}")
print(f"   zone-days covered per month (min/max): {days_per_month.min()}/{days_per_month.max()}")

# =========================================================================
# B2 — COMPOSITION: generation mix, 100% by month
# =========================================================================
p = pd.read_csv(os.path.join(CLEAN, "generation_mix_parts.csv"))
CAT = {"Gas": "Fossil", "Coal": "Fossil", "Furnace oil": "Fossil",
       "Dam": "Hydro", "Run-of-river": "Hydro",
       "Wind": "Wind", "Solar": "Solar", "Imported": "Imported"}
ORDER = ["Fossil", "Hydro", "Wind", "Solar", "Imported"]
COLOUR = {"Fossil": PALETTE["muted"], "Hydro": PALETTE["series"][0],
          "Wind": PALETTE["series"][2], "Solar": PALETTE["highlight"],
          "Imported": PALETTE["series_4th"]}
p["cat"] = p.subsource.map(CAT)
assert p.cat.notna().all(), "unmapped subsource"
t = p.groupby(["month", "cat"]).mwh.sum().unstack("cat")[ORDER]
totals = t.sum(axis=1)
shares = t.div(totals, axis=0) * 100
assert np.allclose(shares.sum(axis=1), 100), "parts do not sum to the whole"

tot_first, tot_last = totals.iloc[0], totals.iloc[-1]
solar = shares["Solar"]
solar_mwh = t["Solar"]
fig, ax = plt.subplots(figsize=(9, 4.8))
x = np.arange(len(shares))
bottom = np.zeros(len(shares))
for cat in ORDER:
    ax.bar(x, shares[cat].values, bottom=bottom, width=0.78, color=COLOUR[cat],
           edgecolor=PALETTE["surface"], linewidth=0.5, label=cat)
    bottom += shares[cat].values
ax.set_ylim(0, 100)
ax.set_xticks(x)
ax.set_xticklabels([m[2:] for m in shares.index], rotation=0, fontsize=7)
ax.set_ylabel("Share of the month's generation (%)")
ax.set_xlabel("Month (YYYY-MM shown as YY-MM)")
ax.legend(ncol=5, loc="upper center", bbox_to_anchor=(0.5, -0.12), fontsize=8)
for i in (0, len(x) - 1):
    ax.text(x[i], solar.iloc[i] / 2 + (shares[ORDER[:3]].iloc[i].sum()),
            f"{solar.iloc[i]:.1f}%", ha="center", va="center",
            fontsize=7.5, color="white", fontweight="bold")
solar_change = (solar_mwh.iloc[-1] / solar_mwh.iloc[0] - 1) * 100
total_change = (tot_last / tot_first - 1) * 100
ax.set_title(f"Solar rose from {solar.iloc[0]:.1f}% to {solar.iloc[-1]:.1f}% of generation; total fell {abs(total_change):.1f}%", loc="left")
fig.text(0.01, 0.885,
         "Decision supported: whether the renewables claim for the board is a real shift or an effect of a shrinking total.",
         fontsize=8.5, color=PALETTE["ink_soft"])
ax.text(0, -0.22, "\n".join(__import__("textwrap").wrap(
    f"Denominator: all generation in the month (the five categories sum to the published total, "
    f"100% every month). Parts: Fossil = gas + coal + furnace oil; Hydro = dam + run-of-river; "
    f"Imported shown separately. Solar MWh moved {solar_change:+.1f}% over the period, total MWh "
    f"{total_change:+.1f}%. Published 'All sources / Total' rows excluded from the sums.", 150)),
    transform=ax.transAxes, fontsize=6.8, color=PALETTE["ink_soft"], va="top")
save_fig(fig, os.path.join(HERE, "partB_2.png"), note=SOURCE)
plt.close(fig)
print(f"B2 solar share {solar.iloc[0]:.2f}% -> {solar.iloc[-1]:.2f}%; solar MWh {solar_change:+.1f}%; "
      f"total MWh {total_change:+.1f}%; months {shares.index[0]}..{shares.index[-1]} ({len(shares)})")

# =========================================================================
# B3 — DISTRIBUTION: outage minutes per zone-day, by zone
# =========================================================================
o = g[g.reported & g.outage_minutes.notna()]
zones = sorted(o.zone.unique())
data = [o.loc[o.zone == z, "outage_minutes"].values for z in zones]
medians = [np.median(d) for d in data]
fig, ax = plt.subplots(figsize=(9, 4.8))
bp = ax.boxplot(data, tick_labels=zones, patch_artist=True, widths=0.55,
                medianprops=dict(color=PALETTE["ink"], linewidth=1.6),
                whiskerprops=dict(color=PALETTE["ink_soft"]),
                capprops=dict(color=PALETTE["ink_soft"]),
                flierprops=dict(marker="o", markersize=2.5, markerfacecolor=PALETTE["muted"],
                                markeredgecolor="none"))
for patch in bp["boxes"]:
    patch.set_facecolor(PALETTE["series"][0])
    patch.set_alpha(0.35)
    patch.set_edgecolor(PALETTE["series"][0])
ax.set_ylim(0, max(o.outage_minutes.max() * 1.05, 10))
ax.set_ylabel("Interruption minutes filed per zone-day")
ax.set_xlabel("Supply zone")
ax.set_xticklabels([f"{z}\nn={len(d)}" for z, d in zip(zones, data)], fontsize=8)
ax.set_title(f"Zones differ little in typical outage length: medians "
             f"{min(medians):.0f}–{max(medians):.0f} minutes per zone-day", loc="left")
fig.text(0.01, 0.885,
         "Decision supported: whether crew standby should be split by zone on duration (it should not, on this evidence).",
         fontsize=8.5, color=PALETTE["ink_soft"])
ax.text(0, -0.17, "\n".join(__import__("textwrap").wrap(
    "Aggregation: one value per zone-day as filed (not summed across zones). Box = inter-quartile "
    "range, line = median, whiskers = 1.5 IQR, dots = beyond. Excluded: the 128 zone-days nobody "
    "filed (not zero). Kept: zero-minute days, which are real days with no interruption.", 150)),
    transform=ax.transAxes, fontsize=6.8, color=PALETTE["ink_soft"], va="top")
save_fig(fig, os.path.join(HERE, "partB_3.png"), note=SOURCE)
plt.close(fig)
print("B3 median minutes per zone-day: " + ", ".join(f"{z} {m:.0f}" for z, m in zip(zones, medians)))
