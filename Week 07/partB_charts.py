#!/usr/bin/env python3
"""
partB_charts.py — the static spine: four charts, four questions (Week 7, Task B).

    partB_1.png  TREND        boardings per filed day, by mode, by month  (ridership_daily)
    partB_2.png  COMPOSITION  share of journeys vs share of revenue, one month  (fare_revenue)
    partB_3.png  MAP          boardings per 1,000 residents, by district  (district_transit)
    partB_4.png  COMPARISON   change in journeys by mode, complete months  (fare_revenue)

Run after partA_process.py:  python3 partB_charts.py
"""
from __future__ import annotations

import os
import sys
import textwrap

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import matplotlib.ticker  # noqa: E402
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import geolib  # noqa: E402
from vizlib import PALETTE, style_defaults, save_fig  # noqa: E402

CLEAN = os.path.join(HERE, "clean")
SOURCE = "Source: synthetic CDB601220 Week 7 data, cleaned by partA_process.py (see partA_decisions.md)."
MODES = ["Metro", "BRT", "Bus", "Ferry"]
MODE_COLOUR = {"Metro": PALETTE["series"][0], "BRT": PALETTE["highlight"],
               "Bus": PALETTE["series"][2], "Ferry": PALETTE["series_4th"]}
style_defaults()


def wrap(text, width=150):
    return "\n".join(textwrap.wrap(text, width))


# =========================================================================
# B1 — TREND: boardings per filed day, by mode, by month
# =========================================================================
rd = pd.read_csv(os.path.join(CLEAN, "ridership_daily_clean.csv"), parse_dates=["date"])
f = rd[rd.filed].copy()
f["month"] = f.date.dt.to_period("M")
m = f.groupby(["month", "mode"]).agg(b=("boardings", "mean"), days=("boardings", "size")).reset_index()
piv = m.pivot(index="month", columns="mode", values="b")[MODES]
days = m.pivot(index="month", columns="mode", values="days")[MODES]
last_filed = {mo: f[f["mode"] == mo].date.max() for mo in MODES}
partial_months = [pd.Period("2026-09", "M")]
complete = piv.drop(index=partial_months)
c_first, c_last = complete.index[0], complete.index[-1]

fig, ax = plt.subplots(figsize=(9.5, 4.9))
x = np.arange(len(complete))
for mo in MODES:
    ax.plot(x, complete[mo].values / 1e3, color=MODE_COLOUR[mo], marker="o", markersize=3.5,
            linewidth=2.0)
    ax.text(x[-1] + 0.3, complete[mo].values[-1] / 1e3, mo, va="center", fontsize=8,
            color=MODE_COLOUR[mo])
ax.set_ylim(0, complete.max().max() / 1e3 * 1.12)
ax.set_xlim(-0.3, len(x) + 0.6)
ax.set_xticks(x[::2])
ax.set_xticklabels([p.strftime("%b %y") for p in complete.index[::2]])
ax.yaxis.set_major_formatter(matplotlib.ticker.StrMethodFormatter("{x:,.0f}"))
ax.set_ylabel("Boardings per filed day (thousands, mean)")
ax.set_xlabel("Month")
metro_b = complete["Metro"]
bus_b = complete["Bus"]
ax.set_title(f"Metro boardings per day rose {(metro_b.iloc[-1] / metro_b.iloc[0] - 1) * 100:.0f}% while "
             f"Bus fell {abs(bus_b.iloc[-1] / bus_b.iloc[0] - 1) * 100:.0f}%", loc="left")
fig.text(0.01, 0.885, "Decision supported: where the next corridor's demand is growing, and which modes to "
         "protect in the budget.", fontsize=8.5, color=PALETTE["ink_soft"])
ax.text(0, -0.13, wrap(
    f"Aggregation: mean boardings per day over the days each mode filed, per month (a level of "
    f"flow; not summed, so gaps do not pull the mean down). Period: {c_first} to {c_last} "
    f"(complete months). Excluded: 2026-09 (partial: Bus and Ferry stop filing after 21 Sep). "
    f"Gaps: 63 unfiled mode-days, not interpolated. 30 re-submitted Bus rows (May 2026) removed."),
    transform=ax.transAxes, fontsize=6.8,
    color=PALETTE["ink_soft"], va="top")
save_fig(fig, os.path.join(HERE, "partB_1.png"), note=SOURCE)
plt.close(fig)
print(f"B1 Metro mean/day {metro_b.iloc[0]:,.0f} -> {metro_b.iloc[-1]:,.0f} "
      f"({(metro_b.iloc[-1] / metro_b.iloc[0] - 1) * 100:+.1f}%)")
for mo in MODES:
    print(f"   {mo:6s} {complete[mo].iloc[0]:>10,.0f} -> {complete[mo].iloc[-1]:>10,.0f}")

# =========================================================================
# B2 — COMPOSITION: share of journeys vs share of revenue, one month
# =========================================================================
fp = pd.read_csv(os.path.join(CLEAN, "fare_revenue_parts.csv"))
MONTH = "2026-08"
mm = fp[fp.month == MONTH].groupby("mode")[["trips", "revenue_pkr"]].sum().loc[MODES]
sh_j = mm.trips / mm.trips.sum() * 100
sh_r = mm.revenue_pkr / mm.revenue_pkr.sum() * 100
assert abs(sh_j.sum() - 100) < 1e-9 and abs(sh_r.sum() - 100) < 1e-9
fare_per = mm.revenue_pkr / mm.trips

fig, ax = plt.subplots(figsize=(8.4, 5.0))
bars = ["Journeys", "Revenue"]
x = np.arange(2)
bottom = np.zeros(2)
for mo in MODES:
    vals = np.array([sh_j[mo], sh_r[mo]])
    ax.bar(x, vals, bottom=bottom, width=0.5, color=MODE_COLOUR[mo], edgecolor=PALETTE["surface"],
           linewidth=0.6, label=mo)
    for xi, v, b in zip(x, vals, bottom):
        ax.text(xi, b + v / 2, f"{mo} {v:.1f}%", ha="center", va="center", fontsize=8,
                color="white" if mo != "Ferry" else PALETTE["ink"], fontweight="bold")
    bottom += vals
ax.set_ylim(0, 100)
ax.set_xticks(x)
ax.set_xticklabels(bars, fontsize=10)
ax.set_ylabel(f"Share of the month's total (%), {MONTH}")
ax.legend(ncol=4, loc="upper center", bbox_to_anchor=(0.5, -0.1), fontsize=8)
ax.set_title(f"Metro carries {sh_j['Metro']:.0f}% of journeys but {sh_r['Metro']:.0f}% of revenue, "
             f"because a metro journey earns more", loc="left")
fig.text(0.01, 0.885, "Decision supported: whether the fare-box recovery is ridership or fares. It is "
         "the mix of mode, not only volume.", fontsize=8.5, color=PALETTE["ink_soft"])
ax.text(0, -0.13, wrap(
    f"Denominator: all journeys (and all revenue) in {MONTH}, summed over the four modes' product "
    f"rows. The published 'All tickets' subtotal is excluded and reconciles exactly. Revenue per "
    f"journey: " + ", ".join(f"{mo} {fare_per[mo]:.1f} PKR" for mo in MODES) +
    ". Journeys are fare events, not boardings: they are not comparable with ridership."),
    transform=ax.transAxes, fontsize=6.8, color=PALETTE["ink_soft"], va="top")
save_fig(fig, os.path.join(HERE, "partB_2.png"), note=SOURCE)
plt.close(fig)
print(f"B2 {MONTH} journeys share {dict(sh_j.round(1))}; revenue share {dict(sh_r.round(1))}; "
      f"PKR/journey {dict(fare_per.round(1))}")

# =========================================================================
# B3 — MAP: boardings per 1,000 residents, by district
# =========================================================================
reg = pd.read_csv(os.path.join(CLEAN, "district_transit_clean.csv"))
reg["per1000"] = reg.boardings_annual / reg.population * 1000
feats = geolib.read_geojson(os.path.join(CLEAN, "regions.geojson"))
vals = dict(zip(reg.code, reg.per1000))
fig = plt.figure(figsize=(7.4, 6.4))
ax = fig.add_axes([0.02, 0.10, 0.62, 0.80])
edges = geolib.choropleth(ax, feats, vals, scheme="natural", k=5,
                          legend_title="Boardings per 1,000 residents\n(12 months to 31 Aug 2026)",
                          fmt="{:,.0f}", legend_loc="lower left", legend_anchor=(1.02, 0.0))
top = reg.nlargest(3, "per1000")[["code", "district", "per1000"]]
ax.set_title(f"Boardings per resident are highest in {', '.join(top.code)}", loc="left", fontsize=11)
fig.text(0.01, 0.94, "Decision supported: where the Authority's rate of use is highest per head, "
         "for the next corridor. Normalised by population.", fontsize=8.5, color=PALETTE["ink_soft"])
save_fig(fig, os.path.join(HERE, "partB_3.png"), note=SOURCE + " Denominator: population of the "
         "district (register). Numerator: boardings_annual, district-attributed.")
plt.close(fig)
print("B3 top per 1,000 residents: " + ", ".join(f"{r.code} {r.per1000:,.0f}" for r in top.itertuples()))
print(f"   classes {[round(e) for e in edges]}")

# =========================================================================
# B4 — COMPARISON: change in journeys by mode over complete months
# =========================================================================
cm = fp[(fp.month >= "2025-04") & (fp.month <= "2026-08")]
first_m, last_m = "2025-04", "2026-08"
jm = cm.groupby(["month", "mode"]).trips.sum().unstack("mode")[MODES]
chg_j = (jm.loc[last_m] / jm.loc[first_m] - 1) * 100
rm = cm.groupby(["month", "mode"]).revenue_pkr.sum().unstack("mode")[MODES]
chg_r = (rm.loc[last_m] / rm.loc[first_m] - 1) * 100
tot_j = (jm.loc[last_m].sum() / jm.loc[first_m].sum() - 1) * 100
tot_r = (rm.loc[last_m].sum() / rm.loc[first_m].sum() - 1) * 100

order = chg_j.sort_values()
fig, ax = plt.subplots(figsize=(8.6, 4.6))
y = np.arange(len(order))
ax.barh(y - 0.2, order.values, height=0.36, color=[MODE_COLOUR[mo] for mo in order.index],
        label="journeys")
ax.barh(y + 0.2, chg_r[order.index].values, height=0.36, color=PALETTE["muted"], label="revenue")
ax.axvline(0, color=PALETTE["ink_soft"], linewidth=0.9)
ax.set_yticks(y)
ax.set_yticklabels(order.index)
ax.set_xlabel(f"Change, {first_m} to {last_m} (%), zero baseline")
for yi, v in zip(y - 0.2, order.values):
    ax.text(v + (2 if v >= 0 else -2), yi, f"{v:+.1f}%", va="center",
            ha="left" if v >= 0 else "right", fontsize=8)
for yi, mo in zip(y + 0.2, order.index):
    v = chg_r[mo]
    ax.text(v + (2 if v >= 0 else -2), yi, f"{v:+.1f}%", va="center",
            ha="left" if v >= 0 else "right", fontsize=8, color=PALETTE["ink_soft"])
ax.set_xlim(min(order.min(), chg_r.min()) - 15, max(order.max(), chg_r.max()) + 20)
ax.legend(loc="lower right", fontsize=8)
ax.set_title(f"Revenue grew {tot_r:.0f}%, journeys {tot_j:.0f}%: the mix moved to metro", loc="left")
fig.text(0.01, 0.92, "Decision supported: whether the finance director's fare-box recovery is volume or price "
         "and mix.", fontsize=8.5, color=PALETTE["ink_soft"])
ax.text(0, -0.13, wrap(
    f"Period: {first_m} to {last_m}, complete months only (2026-09 is partial and excluded). "
    f"Aggregation: summed journeys and revenue per month, first month against last. Journeys and "
    f"revenue are both published counts; no mean of percentages is used. Mode changes: "
    f"Metro journeys {chg_j['Metro']:+.1f}%, Bus {chg_j['Bus']:+.1f}%, BRT {chg_j['BRT']:+.1f}%, "
    f"Ferry {chg_j['Ferry']:+.1f}%."), transform=ax.transAxes, fontsize=6.8,
    color=PALETTE["ink_soft"], va="top")
save_fig(fig, os.path.join(HERE, "partB_4.png"), note=SOURCE)
plt.close(fig)
print("B4 journeys change: " + ", ".join(f"{mo} {chg_j[mo]:+.1f}%" for mo in MODES) +
      f"; total {tot_j:+.1f}%; revenue total {tot_r:+.1f}%")
