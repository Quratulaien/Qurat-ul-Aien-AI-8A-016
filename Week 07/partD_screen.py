#!/usr/bin/env python3
"""
partD_screen.py — the one screen (Week 7, Task D).

Headline, from the Authority's own published data: network punctuality rose
1.7 points between 2025 Q2 and 2026 Q2, and every mode got worse. The screen
shows both, and says why, on the same page.

Panels
  kpi_net    network on-time share, 2026 Q2, with the change — said once
  kpi_bus    Bus on-time share, 2026 Q2, with the change
  trend      on-time share by mode, five complete quarters (same colour = same mode)
  mix        share of departures operated by mode, the two quarters compared
  decomp     the headline change split into within-mode and mix (ink and grey, not hue)

Writes partD_screen.png (300 dpi) and partD_audit.txt (channel_conflicts and cvd_report).
    python3 partD_screen.py
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
import dashlib  # noqa: E402
import vizlib  # noqa: E402
from vizlib import PALETTE, style_defaults, save_fig  # noqa: E402

CLEAN = os.path.join(HERE, "clean")
MODES = ["Metro", "BRT", "Bus", "Ferry"]
COLOUR = {"Metro": PALETTE["series"][0], "BRT": PALETTE["highlight"],
          "Bus": PALETTE["series"][2], "Ferry": PALETTE["series_4th"]}
MARK = {"Metro": "o", "BRT": "s", "Bus": "^", "Ferry": "D"}
QUARTERS = ["2025Q2", "2025Q3", "2025Q4", "2026Q1", "2026Q2"]
BEFORE, AFTER = "2025Q2", "2026Q2"

style_defaults()
audit = []


def say(s=""):
    print(s)
    audit.append(s)


# ---------------------------------------------------------------- the numbers
rd = pd.read_csv(os.path.join(CLEAN, "ridership_daily_clean.csv"), parse_dates=["date"])
f = rd[rd.filed & rd.trips_on_time.notna()].copy()           # on-time-known days only
f["q"] = f.date.dt.to_period("Q").astype(str)
qm = f[f.q.isin(QUARTERS)].groupby(["q", "mode"])[["trips_on_time", "trips_operated"]].sum()
ontime = (qm.trips_on_time / qm.trips_operated * 100).unstack("mode")[MODES]
net_q = qm.groupby("q").sum()
net = net_q.trips_on_time / net_q.trips_operated * 100
dep = qm.trips_operated.unstack("mode")[MODES]
mix = dep.div(dep.sum(axis=1), axis=0) * 100

A = f[f.q == BEFORE].groupby("mode")[["trips_on_time", "trips_operated"]].sum().loc[MODES]
B = f[f.q == AFTER].groupby("mode")[["trips_on_time", "trips_operated"]].sum().loc[MODES]
dec = dashlib.rate_decomposition(A.reset_index(), B.reset_index(), "mode",
                                 "trips_on_time", "trips_operated", per=100)
net_change = net[AFTER] - net[BEFORE]
bus_change = ontime.loc[AFTER, "Bus"] - ontime.loc[BEFORE, "Bus"]

say("NUMBERS USED ON THE SCREEN")
say(f"  network on-time {BEFORE} {net[BEFORE]:.2f}%  {AFTER} {net[AFTER]:.2f}%  change {net_change:+.2f} pts")
for mo in MODES:
    say(f"  {mo:6s} {ontime.loc[BEFORE, mo]:6.2f}% -> {ontime.loc[AFTER, mo]:6.2f}%  "
        f"change {ontime.loc[AFTER, mo] - ontime.loc[BEFORE, mo]:+.2f}")
say(f"  departures share {BEFORE}: " + ", ".join(f"{mo} {mix.loc[BEFORE, mo]:.1f}%" for mo in MODES))
say(f"  departures share {AFTER}: " + ", ".join(f"{mo} {mix.loc[AFTER, mo]:.1f}%" for mo in MODES))
say(f"  rate_decomposition: change {dec['change']:+.2f}  within {dec['within']:+.2f}  "
    f"mix {dec['mix']:+.2f}  reversal={dec['reversal']}")
assert abs(dec["within"] + dec["mix"] - dec["change"]) < 1e-9, "decomposition is not exact"
say(f"  every mode fell: {bool((ontime.loc[AFTER] < ontime.loc[BEFORE]).all())}")

# ------------------------------------------------------- the screen-wide checks
conflicts = dashlib.channel_conflicts([
    {"panel": "kpi_net"},
    {"panel": "kpi_bus"},
    {"panel": "trend", "x": "quarter", "y": "on_time_pct", "hue": "mode", "shape": "mode"},
    {"panel": "mix", "x": "quarter", "y": "departures_pct", "hue": "mode"},
    {"panel": "decomp", "x": "pts", "y": "component", "lightness": "component"},
])
say("\nchannel_conflicts()")
for k, v in conflicts.items():
    say(f"  {k}: {v}")
palette_used = [COLOUR[m] for m in MODES]
say("\ncvd_report() on the palette the screen uses (mode hues)")
vizlib.cvd_report(palette_used, "deutan")
wp = vizlib.worst_pair(palette_used, "deutan")
say(f"  worst deutan pair: {MODES[wp[0]-1]}/{MODES[wp[1]-1]} dE {wp[-1]:.1f} ({vizlib.verdict(wp[-1])})")
say("  the trend panel separates modes by marker shape as well as hue; the mix panel labels "
    "every share above 4% in place, and Ferry (2%) is identified by its legend entry only")

# ---------------------------------------------------------------- the screen
fig = plt.figure(figsize=(13.5, 10.4))
axd = dashlib.dashboard_grid(
    fig,
    [["kpi_net", "kpi_bus", "kpi_metro"],
     ["trend", "trend", "mix"],
     ["decomp", "decomp", "decomp"]],
    headline=f"Punctuality rose {net_change:.1f} points network-wide, but every mode got worse",
    standfirst=(f"On-time share of departures operated, {BEFORE} to {AFTER} (complete quarters). "
                f"Denominator: trips operated. Mix: share of departures operated. Synthetic CDB601220 Week 7 data."),
    height_ratios=[1.0, 2.2, 1.9], hspace=0.62, wspace=0.28, top=0.86)

dashlib.kpi_tile(axd["kpi_net"], "Network on-time, 2026 Q2", net[AFTER],
                 delta=net_change, note=f"vs {net[BEFORE]:.1f}% in 2025 Q2",
                 good="up", fmt="{:.1f}%", delta_fmt="{:+.2f} pts",
                 series=net.values)
dashlib.kpi_tile(axd["kpi_bus"], "Bus on-time, 2026 Q2", ontime.loc[AFTER, "Bus"],
                 delta=bus_change, note=f"vs {ontime.loc[BEFORE, 'Bus']:.1f}% in 2025 Q2",
                 good="up", fmt="{:.1f}%", delta_fmt="{:+.2f} pts",
                 series=ontime["Bus"].values)

dashlib.kpi_tile(axd["kpi_metro"], "Metro on-time, 2026 Q2", ontime.loc[AFTER, "Metro"],
                 delta=ontime.loc[AFTER, "Metro"] - ontime.loc[BEFORE, "Metro"],
                 note=f"vs {ontime.loc[BEFORE, 'Metro']:.1f}% in 2025 Q2", good="up",
                 fmt="{:.1f}%", delta_fmt="{:+.2f} pts", series=ontime["Metro"].values)

ax = axd["trend"]
xq = np.arange(len(QUARTERS))
for mo in MODES:
    ax.plot(xq, ontime[mo].values, color=COLOUR[mo], marker=MARK[mo], markersize=5, linewidth=2,
            label=mo)
    dy = {"Ferry": -1.6}.get(mo, 0.0)
    ax.text(xq[-1] + 0.08, ontime[mo].values[-1] + dy, f"{mo} {ontime[mo].values[-1]:.1f}%",
            va="center", fontsize=8, color=COLOUR[mo])
ax.plot(xq, net.values, color=PALETTE["ink"], linewidth=1.4, linestyle="--", label="network")
ax.text(xq[-1] + 0.08, net.values[-1] + 1.6, f"network {net.values[-1]:.1f}%", va="center", fontsize=8,
        color=PALETTE["ink"])
ax.set_xticks(xq)
ax.set_xticklabels(QUARTERS)
ax.set_ylim(60, 100)
ax.set_xlim(-0.2, len(xq) + 0.5)
ax.set_ylabel("On-time share of departures (%)")
ax.set_title("Each mode is lower in 2026 Q2 than in 2025 Q2; the network line is higher", loc="left", fontsize=9.5)
ax.legend(ncol=5, loc="upper center", bbox_to_anchor=(0.5, -0.13), fontsize=7.5)

ax = axd["mix"]
bottom = np.zeros(2)
xm = np.arange(2)
for mo in MODES:
    vals = np.array([mix.loc[BEFORE, mo], mix.loc[AFTER, mo]])
    ax.bar(xm, vals, bottom=bottom, width=0.55, color=COLOUR[mo], edgecolor=PALETTE["surface"],
           linewidth=0.6, label=mo)
    for xi, v, b in zip(xm, vals, bottom):
        if v > 4:
            ax.text(xi, b + v / 2, f"{v:.0f}%", ha="center", va="center", fontsize=7.5,
                    color="white" if mo != "Ferry" else PALETTE["ink"], fontweight="bold")
    bottom += vals
ax.set_ylim(0, 100)
ax.set_xticks(xm)
ax.set_xticklabels([BEFORE, AFTER])
ax.set_ylabel("Share of departures operated (%)")
ax.set_title(f"Metro: {mix.loc[BEFORE, 'Metro']:.0f}% to {mix.loc[AFTER, 'Metro']:.0f}% of departures; "
             f"Bus: {mix.loc[BEFORE, 'Bus']:.0f}% to {mix.loc[AFTER, 'Bus']:.0f}%", loc="left", fontsize=9.5)
ax.legend(ncol=4, loc="upper center", bbox_to_anchor=(0.5, -0.13), fontsize=7.5)

ax = axd["decomp"]
labels = ["Within-mode change\n(each mode's own rate)", "Mix change\n(which modes ran)", "Network change\n(headline)"]
vals = [dec["within"], dec["mix"], dec["change"]]
cols = [PALETTE["ink_soft"], PALETTE["muted"], PALETTE["ink"]]
yd = np.arange(3)[::-1]
ax.barh(yd, vals, color=cols, height=0.55)
ax.axvline(0, color=PALETTE["ink"], linewidth=0.9)
ax.set_yticks(yd)
ax.set_yticklabels(labels, fontsize=8)
span = max(abs(v) for v in vals) * 1.35
ax.set_xlim(-span, span)
ax.set_xlabel("Percentage points, zero baseline")
for yi, v in zip(yd, vals):
    ax.text(v + (0.08 if v >= 0 else -0.08), yi, f"{v:+.2f} pts", va="center",
            ha="left" if v >= 0 else "right", fontsize=8.5, fontweight="bold")
ax.set_title("Reading the headline: the mix moved riders to Metro, and each mode got worse. "
             "The change is a mix effect, not better running", loc="left", fontsize=9.5)

fig.text(0.01, 0.01,
         "Source: synthetic CDB601220 Week 7 data, cleaned by partA_process.py. Five complete quarters; "
         "rows where on-time was impossible excluded from both numerator and denominator. "
         "Decomposition: Kitagawa two-term, exact.", fontsize=7, color=PALETTE["ink_soft"])
save_fig(fig, os.path.join(HERE, "partD_screen.png"))
plt.close(fig)
print("wrote partD_screen.png")

with open(os.path.join(HERE, "partD_audit.txt"), "w") as fh:
    fh.write("\n".join(audit) + "\n")
print("wrote partD_audit.txt")
