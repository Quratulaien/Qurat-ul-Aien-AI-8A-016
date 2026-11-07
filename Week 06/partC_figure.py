#!/usr/bin/env python3
"""
partC_figure.py — the figure the board will see: where is supply least reliable?

One figure, two panels:
  left   a normalised choropleth: interruptions per 1,000 households (12 months)
  right  the same 24 districts as sorted bars of that rate, with the raw-count
         rank beside each name, so the counterfactual is on the page

Writes partC_figure.png (300 dpi). Run after partA_process.py:

    python3 partC_figure.py
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
import geolib  # noqa: E402
from vizlib import PALETTE, style_defaults, save_fig  # noqa: E402

CLEAN = os.path.join(HERE, "clean")
style_defaults()

reg = pd.read_csv(os.path.join(CLEAN, "district_grid_clean.csv"))
reg["rate"] = reg.outages / reg.households * 1000          # per 1,000 households
pooled = reg.outages.sum() / reg.households.sum() * 1000   # national pooled rate
reg["rank_rate"] = reg.rate.rank(ascending=False, method="first").astype(int)
reg["rank_count"] = reg.outages.rank(ascending=False, method="first").astype(int)

top_rate = reg.nlargest(3, "rate").code.tolist()
top_count = reg.nlargest(3, "outages").code.tolist()
both = sorted(set(top_rate) & set(top_count))
r_count = np.corrcoef(reg.outages, reg.households)[0, 1]
r_rate = np.corrcoef(reg.rate, reg.households)[0, 1]

# Poisson funnel: is the spread in the rate more than chance, given the base?
fl = geolib.funnel_limits(reg.households, pooled, per=1000)
fl_sorted = reg.sort_values("households").reset_index(drop=True)
outside = int(((fl_sorted.rate < fl.lo) | (fl_sorted.rate > fl.hi)).sum())

print(f"r(interruptions, households) = {r_count:+.3f}")
print(f"r(rate, households)          = {r_rate:+.3f}")
print(f"national pooled rate         = {pooled:.1f} per 1,000 households")
print(f"top 3 by count: {top_count}   top 3 by rate: {top_rate}   on both: {both}")
print(f"funnel: {outside} of {len(reg)} districts outside Poisson limits "
      f"(smallest base {int(reg.households.min()):,} households)")
for code in top_rate:
    r = reg.loc[reg.code == code].iloc[0]
    print(f"  {code} {r.district:14s} rate rank {r.rank_rate:2d}  count rank {r.rank_count:2d}  "
          f"rate {r.rate:.1f}")
for code in top_count:
    r = reg.loc[reg.code == code].iloc[0]
    print(f"  count-top {code} {r.district:14s} rate rank {r.rank_rate:2d}")

# ---------------------------------------------------------------- the figure
feats = geolib.read_geojson(os.path.join(CLEAN, "regions.geojson"))
rate_by_code = dict(zip(reg.code, reg.rate))

fig = plt.figure(figsize=(12.5, 6.4))
ax_map = fig.add_axes([0.0, 0.06, 0.40, 0.82])
ax_bar = fig.add_axes([0.60, 0.10, 0.36, 0.74])

edges = geolib.choropleth(
    ax_map, feats, rate_by_code, scheme="natural", k=5,
    legend_title="Interruptions per 1,000 households\n(12 months; Jenks classes)",
    fmt="{:.1f}", legend_loc="lower left", legend_anchor=(1.0, 0.0))
ax_map.set_title(f"Rate, not count, points at {', '.join(top_rate)}",
                 loc="left", fontsize=11)

# label the top three by rate on the map (a point inside each district)
lat_ts = geolib._collection_lat_ts(feats)
for f in feats:
    if f["code"] in top_rate:
        pt = geolib.representative_point(f["ring"])
        x, y = geolib.equal_area_xy([pt[0]], [pt[1]], lat_ts=lat_ts)
        ax_map.scatter(x, y, s=38, facecolor="white", edgecolor=PALETTE["ink"],
                       linewidth=1.0, zorder=6)
        off = {"D12": (6, -12), "D11": (-30, 6)}.get(f["code"], (6, 4))
        ax_map.annotate(f["code"], (x[0], y[0]), xytext=off, textcoords="offset points",
                        fontsize=8, color=PALETTE["ink"], zorder=7)

order = reg.sort_values("rate").reset_index(drop=True)
y = np.arange(len(order))
colours = [PALETTE["highlight"] if c in top_rate else PALETTE["muted"] for c in order.code]
ax_bar.barh(y, order.rate, color=colours, height=0.7)
ax_bar.set_yticks(y)
ax_bar.set_yticklabels([f"{c}  (count #{rk})" for c, rk in zip(order.code, order.rank_count)],
                       fontsize=7)
ax_bar.set_xlim(0, order.rate.max() * 1.12)
ax_bar.set_xlabel("Interruptions per 1,000 households (zero baseline)")
ax_bar.axvline(pooled, color=PALETTE["ink_soft"], linestyle="--", linewidth=0.9)
ax_bar.text(pooled, len(order) - 0.2, f" national {pooled:.1f}", fontsize=7,
            color=PALETTE["ink_soft"], va="bottom")
for i, (rate, c) in enumerate(zip(order.rate, order.code)):
    ax_bar.text(rate + 0.4, i, f"{rate:.1f}", va="center", fontsize=6.5,
                color=PALETTE["ink_soft"])
ax_bar.set_title("Ranked by rate; grey number = rank by raw count",
                 loc="left", fontsize=9)

fig.text(0.01, 0.955,
         f"Decision: where the reliability budget goes. Ranked by count, the budget goes to "
         f"{', '.join(top_count)}; ranked by rate it goes to {', '.join(top_rate)} — "
         f"{both[0]} is on both lists.",
         fontsize=8.5, color=PALETTE["ink_soft"])
note = ("Denominator: households in the district (register, cleaned by partA_process.py). "
        "Numerator: supply interruptions filed on district feeders over the same 12 months. "
        "Classes: Jenks natural breaks, 5 classes, equal-area projection. Districts suppressed: none; "
        "smallest base 76,721 households. Synthetic CDB601220 Week 6 data.")
save_fig(fig, os.path.join(HERE, "partC_figure.png"), note=note)
plt.close(fig)
print("wrote partC_figure.png")
