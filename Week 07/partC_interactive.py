#!/usr/bin/env python3
"""
partC_interactive.py — Task C: one chart made interactive, plus its static default state.

Rebuilds Task B's trend chart (boardings per filed day, by mode, by month) in
Plotly: hover for values, click a legend entry to hide a mode, drag the range
slider to zoom to a window. Writes:

    partC_interactive.html   the live view (Plotly, offline; open in any browser)
    partC_default.png        the static default state, for a marker with no mouse

The default state is what most readers will see. The contract that goes with
it is in partC_contract.md.   python3 partC_interactive.py
"""
from __future__ import annotations

import os
import sys

import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from vizlib import PALETTE  # noqa: E402

import plotly.graph_objects as go  # noqa: E402

CLEAN = os.path.join(HERE, "clean")
MODES = ["Metro", "BRT", "Bus", "Ferry"]
COLOUR = {"Metro": PALETTE["series"][0], "BRT": PALETTE["highlight"],
          "Bus": PALETTE["series"][2], "Ferry": PALETTE["series_4th"]}

rd = pd.read_csv(os.path.join(CLEAN, "ridership_daily_clean.csv"), parse_dates=["date"])
f = rd[rd.filed].copy()
f["month"] = f.date.dt.to_period("M").dt.to_timestamp()
m = f.groupby(["month", "mode"]).boardings.mean().unstack("mode")[MODES]
days = f.groupby(["month", "mode"]).boardings.size().unstack("mode")[MODES]
# the complete months only, as Task B: 2026-09 is partial and is left out
m = m[m.index < pd.Timestamp("2026-09-01")]
days = days.loc[m.index]

fig = go.Figure()
for mo in MODES:
    fig.add_trace(go.Scatter(
        x=m.index, y=m[mo], name=mo, mode="lines+markers",
        line=dict(color=COLOUR[mo], width=2.2), marker=dict(size=5, symbol="circle"),
        customdata=days[mo],
        hovertemplate=(f"<b>{mo}</b><br>%{{x|%b %Y}}<br>mean boardings/day: "
                       "%{y:,.0f}<br>days filed: %{customdata}<extra></extra>")))

fig.update_layout(
    title=dict(text="Boardings per filed day by mode, Apr 2025 – Aug 2026",
               x=0.0, font=dict(size=15)),
    yaxis=dict(title="Boardings per filed day (mean, zero baseline)", rangemode="tozero",
               tickformat=","),
    xaxis=dict(title="Month", rangeslider=dict(visible=True, thickness=0.08),
               rangeselector=dict(buttons=[
                   dict(count=6, label="6m", step="month", stepmode="backward"),
                   dict(count=12, label="12m", step="month", stepmode="backward"),
                   dict(step="all", label="all")])),
    legend=dict(title="Mode (click to hide)", orientation="h", y=-0.25),
    template="simple_white", height=560, margin=dict(t=70, b=120),
    annotations=[dict(
        text="Source: synthetic CDB601220 Week 7 data, cleaned by partA_process.py. "
             "Monthly means over filed days; 2026-09 partial and excluded; gaps not interpolated.",
        xref="paper", yref="paper", x=0, y=-0.36, showarrow=False, font=dict(size=10))])

out_html = os.path.join(HERE, "partC_interactive.html")
fig.write_html(out_html, include_plotlyjs=True, full_html=True)
print(f"wrote {os.path.basename(out_html)}")

# ---- the static default state, drawn with matplotlib so it is a PNG ----------
import matplotlib  # noqa: E402
matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import matplotlib.ticker  # noqa: E402
from vizlib import style_defaults, save_fig  # noqa: E402

style_defaults()
fig2, ax = plt.subplots(figsize=(9.5, 4.9))
for mo in MODES:
    ax.plot(m.index, m[mo], color=COLOUR[mo], marker="o", markersize=3.5, linewidth=2.0, label=mo)
ax.set_ylim(0, m.max().max() * 1.12)
ax.yaxis.set_major_formatter(matplotlib.ticker.StrMethodFormatter("{x:,.0f}"))
ax.set_ylabel("Boardings per filed day (mean, zero baseline)")
ax.set_xlabel("Month")
ax.legend(ncol=4, loc="upper center", bbox_to_anchor=(0.5, -0.12), fontsize=8)
ax.set_title("Default view: Metro carries the growth; Bus and Ferry fall. Hover in the live view for values.",
             loc="left", fontsize=10.5)
save_fig(fig2, os.path.join(HERE, "partC_default.png"),
         note="Static default state of partC_interactive.html. Source: synthetic CDB601220 Week 7 data. "
              "Monthly means over filed days, Apr 2025 – Aug 2026 (2026-09 partial, excluded).")
plt.close(fig2)
print("wrote partC_default.png")
