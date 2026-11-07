#!/usr/bin/env python3
"""
partB_windows.py — Part B: smoothing, windows and panel shape, computed.

Five questions, each answered with a number printed below. Run:

    python3 partB_windows.py | tee partB_output.txt

Works on the cleaned daily session series from sessions_clean.analysis_daily():
complete days only (>= 21 of 24 hours filed), September 2025 excluded as partial.
"""
from __future__ import annotations

import os
import sys
import warnings

import numpy as np
import pandas as pd
from statsmodels.tsa.seasonal import seasonal_decompose

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import sessions_clean as sc  # noqa: E402
import tslib  # noqa: E402

warnings.filterwarnings("ignore", category=FutureWarning)
pd.set_option("display.width", 120)

h, decisions, gap_days, last_day = sc.load_sessions(os.path.join(HERE, "data", "sessions_hourly.csv"))
daily_full = sc.daily_series(h)
daily = sc.analysis_daily(h)  # complete days, Sep 2025 excluded
print(f"ANALYSIS SERIES  {daily.index.min().date()} .. {daily.index.max().date()}  "
      f"({len(daily)} calendar days; {int(daily.notna().sum())} usable; "
      f"{int(daily.isna().sum())} unusable/missing)")
print(f"scaled days in analysis (21-23 hours filed): "
      f"{int(daily_full.loc[daily.index, 'scaled'].sum())}")
print()

# ---------------------------------------------------------------- 1. windows
print("=" * 78)
print("Q1  The window is a hypothesis: tslib.window_report() for 7, 28, 91")
print("=" * 78)
rep = tslib.window_report(daily, windows=(7, 28, 91), center=True)
cycles = {7: "weekly (day-of-week)", 28: "roughly monthly", 91: "roughly quarterly"}
rep["cycle_removed"] = rep.window.map(cycles)
print(rep.to_string(index=False))
print()
print("Reading: a rolling mean over exactly one cycle removes that cycle. A 7-day")
print("mean removes the day-of-week pattern completely; 28 and 91 remove it too, but")
print("also average across several weeks of real movement. The three windows remove")
print("32-39% of the raw variation: most of what they remove is the weekly cycle,")
print("which the 7-day window cancels and the others only partly cancel.")
print("The window for Part D is 7, chosen because the weekly cycle is the one Q3 finds")
print("large. The cost is 3 days at each end; 28 and 91 would cost 14 and 45.")
print()

# ---------------------------------------------------------------- 2. spike
print("=" * 78)
print("Q2  Three smoothers against one spike: 29 Nov 2024 (Black Friday)")
print("=" * 78)
bf = pd.Timestamp("2024-11-29")
raw_bf = h.sessions.groupby(h.index.normalize()).sum().get(bf)
print(f"raw day total on {bf.date()}: {raw_bf:,.0f} sessions (all 24 hours filed: "
      f"{int(daily_full.loc[bf, 'filed_hours'])})")
cen = daily.rolling(14, center=True, min_periods=10)
c_mean = cen.mean().loc[bf]
c_med = cen.median().loc[bf]
ewm = daily.ewm(span=14, adjust=False).mean().loc[bf]
window_days = daily.loc[bf - pd.Timedelta(days=7): bf + pd.Timedelta(days=6)]
print(f"14-day centred window {window_days.index.min().date()} .. {window_days.index.max().date()}, "
      f"{int(window_days.notna().sum())} usable days")
print(f"  centred MEAN   : {c_mean:,.0f}   (the spike is inside the mean: it is pulled up)")
print(f"  centred MEDIAN : {c_med:,.0f}   (the spike cannot move the median)")
print(f"  EWMA span=14   : {ewm:,.0f}   (trailing by construction: it cannot be centred without a shift)")
print(f"  fortnight median of the window, spike included: {window_days.median():,.0f}")
print("Dashboard: the median, because a monitoring view must not be moved by one event.")
print("Quarterly report: the mean, because totals must add up across the quarter.")
print()

# ---------------------------------------------------------------- 3. decompose
print("=" * 78)
print("Q3  seasonal_decompose(additive): weekly, then the yearly test")
print("=" * 78)
# seasonal_decompose needs a complete series. Interpolate INSIDE the record only,
# for decomposition alone, and report how many days were filled.
inside = daily.copy()
n_fill = int(inside.loc[inside.first_valid_index():inside.last_valid_index()].isna().sum())
filled = inside.interpolate(limit_area="inside")
dec7 = seasonal_decompose(filled, model="additive", period=7)
season7 = dec7.seasonal.iloc[:7]
amp7 = season7.max() - season7.min()
resid = dec7.resid.dropna()
big = resid.abs().idxmax()
print(f"days filled by interpolation for decomposition only: {n_fill} (of {len(daily)})")
print(f"weekly seasonal component: one cycle, peak-to-trough amplitude = {amp7:,.0f} sessions/day")
print("  by weekday:", {d.strftime('%a'): round(v) for d, v in zip(season7.index, season7.values)})
print(f"largest residual: {big.date()} = {resid.loc[big]:,.0f} sessions "
      f"({big.day_name()}; the spike the decomposition cannot explain by weekday)")

# yearly test: the file covers well under two full years, so period=365 cannot run.
days_covered = len(filled.dropna())
span_days = (filled.index.max() - filled.index.min()).days + 1
print(f"period=365 needs at least 730 days (two full cycles). The analysis series spans "
      f"{span_days} days, so period=365 is NOT computable here.")
dec91 = seasonal_decompose(filled, model="additive", period=91)
s91 = dec91.seasonal.iloc[:91]
print(f"comparison that IS computable: period=91 (two cycles need 182 days). "
      f"Quarterly seasonal amplitude = {s91.max() - s91.min():,.0f} sessions/day.")
sd_r7 = dec7.resid.dropna().std()
sd_r91 = dec91.resid.dropna().std()
sd_s7 = dec7.seasonal.std()
sd_s91 = dec91.seasonal.std()
print(f"  residual sd: period 7 = {sd_r7:,.0f}, period 91 = {sd_r91:,.0f}")
print(f"  seasonal sd: period 7 = {sd_s7:,.0f}, period 91 = {sd_s91:,.0f}")
print("  the 91-day model does NOT remove the weekly cycle, so the residual sd rises:")
print("  the day-of-week pattern goes back into 'resid'. The period has to match the")
print("  cycle you mean to cancel; a longer period is not a smoother residual.")
print()

# ---------------------------------------------------------------- 4. lag
print("=" * 78)
print("Q4  Trailing or centred: tslib.lag_at_turn() with a 31-day window")
print("=" * 78)
lag = tslib.lag_at_turn(filled, window=31, how="min")
print(f"  trailing turn : {lag['trailing_turn'].date()}")
print(f"  centred turn  : {lag['centred_turn'].date()}")
print(f"  lag           : {lag['lag_periods']} days   half-window = {lag['half_window']} days")
print("Dashboard refreshes every morning: it must show the TRAILING 31-day mean,")
print("because the centred value needs days that have not happened yet. Its caption:")
print("'Trailing 31-day mean. A turn appears about 15 days after it happened. The")
print("centred value, computed after the window fills, is what the report uses.'")
print()

# ---------------------------------------------------------------- 5. loop
print("=" * 78)
print("Q5  The window is a claim: 12 start months x 5 window lengths, slope sign")
print("=" * 78)
starts = pd.date_range("2024-05-01", periods=12, freq="MS")
windows = [7, 14, 28, 56, 91]
rows = []
for st in starts:
    for w in windows:
        seg = daily.loc[st: st + pd.Timedelta(days=w - 1)].dropna()
        if len(seg) < max(3, w // 2):
            rows.append(dict(start=st.date(), window=w, slope=np.nan, n=len(seg), sign="insufficient"))
            continue
        x = (seg.index - seg.index[0]).days.values
        slope = np.polyfit(x, seg.values, 1)[0]
        rows.append(dict(start=st.date(), window=w, slope=slope, n=len(seg),
                         sign="rising" if slope > 0 else "falling"))
res = pd.DataFrame(rows)
ok = res[res.sign != "insufficient"]
print(f"combinations computed: {len(ok)} of {len(res)}")
print(f"  rising : {int((ok.sign == 'rising').sum())}")
print(f"  falling: {int((ok.sign == 'falling').sum())}")
print()
print(ok.groupby("window").sign.value_counts().unstack(fill_value=0).to_string())
print()
print("Lie Factor = (effect shown) / (effect in the data). It needs ONE effect in the")
print("data, measured between two fixed points that were chosen before looking. The")
print("cherry-picked window has no single effect: each start and length gives a")
print("different one, and which one is 'the data' depends on the choice being")
print("judged. The formula assumes the comparison was declared first; with a")
print("selected window that assumption is false, so the ratio has no value to take.")
print("Honest substitute: fix the window before plotting, and report the whole")
print("distribution of outcomes (every start, every length) rather than the one that")
print("was selected. Here the distribution is the result.")
