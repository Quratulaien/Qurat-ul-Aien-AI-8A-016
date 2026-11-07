#!/usr/bin/env python3
"""
partF_cycle.py — Part F (bonus): Week 1's open question, settled on a real file.

Week 1 asked: the seasonal swing gets bigger every year — is the seasonality growing, or just
the level? Here the same question on real data: Our World in Data, COVID-19 dataset, daily new
cases by location. Source: https://github.com/owid/covid-19-data (owid-covid-data.csv),
downloaded 2026-11-07 (see bonus_F_data/download_stamp.txt).

    python3 partF_cycle.py   -> partF_cycle.png, partF_audit.txt
"""
from __future__ import annotations

import os
import sys

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402
from statsmodels.tsa.seasonal import seasonal_decompose  # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import tslib  # noqa: E402
from vizlib import PALETTE, style_defaults, save_fig  # noqa: E402

style_defaults()
C = PALETTE
SRC = os.path.join(HERE, "bonus_F_data", "owid-covid-data.csv")
LOC = "Pakistan"
START, END = "2020-03-01", "2023-12-31"  # the span of the file's complete months used here

raw = pd.read_csv(SRC, usecols=["location", "date", "new_cases"])
raw["date"] = pd.to_datetime(raw.date, format="%Y-%m-%d")
p = raw[raw.location == LOC].set_index("date").sort_index()

audit_lines = []
audit_lines.append(f"location = {LOC}; rows {len(p)}; span {p.index.min().date()} .. {p.index.max().date()}")
audit_lines.append(f"index audit (daily): {tslib.audit_index(p.new_cases, 'D')}")
neg = int((p.new_cases < 0).sum())
nan = int(p.new_cases.isna().sum())
audit_lines.append(f"negative new_cases rows: {neg}")
audit_lines.append(f"missing new_cases values: {nan}")

d = p.new_cases.loc[START:END]
m = d.resample("MS").sum()  # a FLOW: monthly total is a sum (slide 12)
audit_lines.append(f"monthly series: {len(m)} months {m.index.min().date()} .. {m.index.max().date()}")
audit_lines.append(f"monthly audit: {tslib.audit_index(m, 'MS')}")

# banked aspect ratio (Cleveland 45 degrees) — computed, printed
figsize = tslib.banked_figsize(m.values, width=9.0)
audit_lines.append(f"banked figsize for the time-series panel: {figsize}")

# additive vs multiplicative residuals (both need the same complete series)
add = seasonal_decompose(m, model="additive", period=12)
mul = seasonal_decompose(m.clip(lower=1), model="multiplicative", period=12)
r_add = add.resid.dropna()
r_mul = mul.resid.dropna()
audit_lines.append(f"residual sd additive = {r_add.std():,.0f} cases; multiplicative ratio sd = {r_mul.std():.3f}")

# THE QUESTION: does the within-year swing grow with the level, or independently?
by_year = m.groupby(m.index.year)
rng = by_year.max() - by_year.min()
lvl = by_year.mean()
rel = rng / lvl
audit_lines.append("year | mean per month | within-year range (max-min) | range / mean")
for y in lvl.index:
    audit_lines.append(f"{y} | {lvl[y]:,.0f} | {rng[y]:,.0f} | {rel[y]:.2f}")
slope_rng = np.polyfit(np.arange(len(rng)), rng.values, 1)[0]
slope_lvl = np.polyfit(np.arange(len(lvl)), lvl.values, 1)[0]
audit_lines.append(f"trend in range per year: {slope_rng:,.0f}; trend in level per year: {slope_lvl:,.0f}")

with open(os.path.join(HERE, "partF_audit.txt"), "w") as f:
    f.write("\n".join(audit_lines) + "\n")
print("\n".join(audit_lines))

# ----------------------------------------------------------------- figure
fig, axs = plt.subplots(1, 3, figsize=(16, 5.2))
a0, a1, a2 = axs

a0.plot(m.index, m.values, color=C["muted"], linewidth=0.9, marker="o", markersize=2.5, label="monthly total")
a0.plot(m.index, m.rolling(3, center=True, min_periods=2).mean(), color=C["series"][0], linewidth=2,
        label="3-month centred mean")
a0.set_ylabel("New cases per month (sum)")
a0.set_title(f"{LOC}: a level that moves in waves, 2020–2023", loc="left", fontsize=10)
a0.legend(fontsize=8)
a0.yaxis.set_major_formatter(matplotlib.ticker.StrMethodFormatter("{x:,.0f}"))

cyc = m.to_frame("v")
cyc["year"] = cyc.index.year
cyc["month"] = cyc.index.month
for i, y in enumerate(sorted(cyc.year.unique())):
    s = cyc[cyc.year == y]
    a1.plot(s.month, s.v, color=[C["series"][0], C["highlight"], C["series"][2], C["muted"]][i % 4],
            marker="o", markersize=3, linewidth=1.6, label=str(y))
a1.set_xticks(range(1, 13))
a1.set_xticklabels(list("JFMAMJJASOND"))
a1.set_ylabel("New cases per month (sum)")
a1.set_title("Cycle plot: each year on its own line, by month", loc="left", fontsize=10)
a1.legend(fontsize=8)
a1.yaxis.set_major_formatter(matplotlib.ticker.StrMethodFormatter("{x:,.0f}"))

a2.plot(r_add.index, r_add.values, color=C["series"][0], linewidth=1.4, label="additive residual (cases)")
a2.axhline(0, color=C["ink_soft"], linewidth=0.6)
a2.set_ylabel("Additive residual, cases")
a2b = a2.twinx()
a2b.plot(r_mul.index, r_mul.values, color=C["highlight"], linewidth=1.4, label="multiplicative residual (ratio)")
a2b.axhline(1, color=C["highlight"], linewidth=0.5, linestyle=":")
a2b.set_ylabel("Multiplicative residual (ratio, 1 = fit)")
a2.set_title(f"Residuals: additive sd {r_add.std():,.0f}; multiplicative sd {r_mul.std():.2f}", loc="left", fontsize=10)
a2.legend(loc="lower left", fontsize=8, frameon=False)
a2b.legend(loc="lower right", fontsize=8, frameon=False)

note = (f"Source: Our World in Data, owid-covid-data.csv (github.com/owid/covid-19-data), downloaded 2026-11-07. "
        f"Location {LOC}; monthly sums of new_cases over {START[:7]} to {END[:7]}. "
        f"Audit and index checks in partF_audit.txt. No negative values in this location.")
import textwrap  # noqa: E402
fig.text(0.01, -0.03, "\n".join(textwrap.wrap(note, 200)), fontsize=7, color=C["ink_soft"], va="top")
fig.savefig(os.path.join(HERE, "partF_cycle.png"), dpi=300, bbox_inches="tight", facecolor="white")
plt.close(fig)
print("wrote partF_cycle.png")
