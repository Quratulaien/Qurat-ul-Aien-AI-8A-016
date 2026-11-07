#!/usr/bin/env python3
"""
partD_interactive.py — Task D1 (bonus): the Task B1 trend, rebuilt in Plotly.

Same computation as partB_charts.py B1 (energy spread over each reading's span,
mean MWh per day per zone, summed to the network). Interactive additions:
hover for the exact value, click a zone in the legend to filter it, and a range
slider plus 12-month / all buttons to change the date window.

    python3 partD_interactive.py     (after partA_process.py)
    -> partD_interactive.html (offline, self-contained)
"""
from __future__ import annotations

import os

import numpy as np
import pandas as pd
import plotly.graph_objects as go

HERE = os.path.dirname(os.path.abspath(__file__))
CLEAN = os.path.join(HERE, "clean")

g = pd.read_csv(os.path.join(CLEAN, "grid_daily_clean.csv"), parse_dates=["date"])
rep = g[g.reported & g.energy_mwh.notna()].copy()
rep["span"] = rep.span_days.astype(int)
rep["rate"] = rep.energy_mwh / rep.span

offs = np.concatenate([np.arange(s) for s in rep.span])
rep_x = rep.loc[rep.index.repeat(rep.span)].reset_index(drop=True)
rep_x["day"] = rep_x.date - pd.to_timedelta(rep_x.span - 1 - offs, unit="D")
rep_x["month"] = rep_x.day.dt.to_period("M")

zone_month = rep_x.groupby(["zone", "month"]).rate.mean().unstack("zone")
network = zone_month.sum(axis=1)
last_day = g.date.max()
partial = [m for m in network.index if m.end_time.normalize() > last_day]
complete = network.drop(index=partial)
zone_month = zone_month.drop(index=partial)

x = [m.start_time for m in complete.index]
fig = go.Figure()
fig.add_trace(go.Scatter(
    x=x, y=complete.values, mode="lines+markers", name="Network (sum of zones)",
    line=dict(color="#222222", width=3), marker=dict(size=5),
    hovertemplate="%{x|%b %Y}<br>Network: %{y:,.0f} MWh/day<extra></extra>"))
for z in zone_month.columns:
    fig.add_trace(go.Scatter(
        x=x, y=zone_month.loc[complete.index, z].values, mode="lines", name=str(z),
        line=dict(width=1.4), visible="legendonly",
        hovertemplate=f"%{{x|%b %Y}}<br>{z}: %{{y:,.0f}} MWh/day<extra></extra>"))

fig.update_layout(
    title=dict(text="Network energy delivered per day rose over the period (mean of days with a reading)",
               x=0.0, font=dict(size=15)),
    yaxis=dict(title="Energy delivered, MWh per day", rangemode="tozero", tickformat=",.0f"),
    xaxis=dict(rangeslider=dict(visible=True),
               rangeselector=dict(buttons=[
                   dict(count=12, label="12 months", step="month", stepmode="backward"),
                   dict(step="all", label="all")])),
    legend=dict(title="Click to show or hide a zone", orientation="h", y=-0.25),
    hovermode="x unified", template="simple_white", height=640, width=1100,
    margin=dict(l=70, r=30, t=80, b=130),
)
out = os.path.join(HERE, "partD_interactive.html")
fig.write_html(out, include_plotlyjs=True, full_html=True)
print(f"wrote {out}  ({len(complete)} complete months; partial months excluded: {len(partial)})")
