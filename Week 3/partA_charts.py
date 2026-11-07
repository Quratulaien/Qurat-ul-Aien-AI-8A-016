"""
Part A - rebuild nine charts, then plot the nine honest redesigns.

    python3 partA_charts.py

For every case N it writes
    partA_figs/caseN_rebuild.png    the analyst's chart, from the recipe
    partA_figs/caseN_redesign.png   the honest chart
and asserts the self-check number from the brief. All the numbers the
diagnosis needs are collected in partA_metrics.json (read by build_pdfs.py).

All data is synthetic, generated for CDB601220 Week 3.
Every figure starts with fig, ax = plt.subplots(); no plt.plot().
"""
from __future__ import annotations

import json
import os

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns
from scipy import stats

from vizlib import MARKERS, PALETTE, style_defaults

ROOT = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(ROOT, "data")
OUT = os.path.join(ROOT, "partA_figs")
os.makedirs(OUT, exist_ok=True)
style_defaults()
C = PALETTE["series"]
M: dict = {}          # metrics for the diagnosis PDF


def save(fig, name, note):
    """Save BEFORE any show; note goes under the figure (source + parameters)."""
    fig.text(0.01, -0.02, note, fontsize=7, color=PALETTE["ink_soft"],
             ha="left", va="top")
    path = os.path.join(OUT, name)
    fig.savefig(path, dpi=200, bbox_inches="tight", facecolor="white")
    plt.close(fig)
    print("  wrote", os.path.relpath(path, ROOT))


def check(label, got, want, tol=0.006):
    ok = abs(got - want) <= tol
    print(f"  self-check {label}: got {got:.3f}, expected {want}  ->  "
          f"{'OK' if ok else 'MISMATCH'}")
    assert ok, label


SRC = "Synthetic data generated for CDB601220 Week 3."


# =============================================================================
# CASE 1  helmets
# =============================================================================
def case1():
    print("\nCASE 1  helmets")
    d = pd.read_csv(os.path.join(DATA, "case01_helmet_rickshaw.csv"))
    g = d.groupby("helmet_grade")[["trips", "head_injuries"]].sum()
    g["per_1000"] = g.head_injuries / g.trips * 1000
    check("Standard", g.per_1000["Standard"], 2.15)
    check("Premium", g.per_1000["Premium"], 5.40)

    fig, ax = plt.subplots(figsize=(5.2, 3.8))
    order = ["Standard", "Premium"]
    bars = ax.bar(order, g.per_1000[order], color=[C[0], C[1]], width=0.55)
    ax.bar_label(bars, fmt="%.2f", padding=3)
    ax.set_ylim(0, 6.5)
    ax.set_ylabel("Head injuries per 1,000 trips")
    ax.set_title("Premium helmets: 2.5x the head-injury rate?")
    ax.grid(axis="x", visible=False)
    save(fig, "case1_rebuild.png", f"y-axis from zero; 100,000 trips. {SRC}")

    # ---- diagnosis numbers
    t = d.groupby(["road_type", "helmet_grade"]).agg(
        trips=("trips", "sum"), inj=("head_injuries", "sum"),
        speed=("avg_speed_kph", "mean"), exp=("months_experience", "mean"),
        riders=("rider_id", "count")).reset_index()
    t["rate"] = t.inj / t.trips * 1000
    roads = ["Motorway", "City arterial", "Inner-city lanes"]
    share = (t.pivot(index="road_type", columns="helmet_grade", values="trips")
             .loc[roads]); share = share / share.sum()
    rate = t.pivot(index="road_type", columns="helmet_grade", values="rate").loc[roads]
    # direct standardisation to the combined road mix
    w = t.groupby("road_type").trips.sum().loc[roads]; w = w / w.sum()
    std = {gr: float((rate[gr] * w).sum()) for gr in order}
    overall_speed = d.groupby("helmet_grade").avg_speed_kph.mean()
    overall_exp = d.groupby("helmet_grade").months_experience.mean()
    sp = t.pivot(index="road_type", columns="helmet_grade", values="speed").loc[roads]
    ex = t.pivot(index="road_type", columns="helmet_grade", values="exp").loc[roads]
    M["c1"] = dict(
        rate_std=g.per_1000["Standard"], rate_prem=g.per_1000["Premium"],
        prem_motorway_share=share.loc["Motorway", "Premium"],
        std_motorway_share=share.loc["Motorway", "Standard"],
        std_inner_share=share.loc["Inner-city lanes", "Standard"],
        road_rate_all={r: float(t[t.road_type == r].inj.sum() / t[t.road_type == r].trips.sum() * 1000) for r in roads},
        rate={r: {gr: float(rate.loc[r, gr]) for gr in order} for r in roads},
        std_adj=std, speed_overall={k: float(v) for k, v in overall_speed.items()},
        exp_overall={k: float(v) for k, v in overall_exp.items()},
        speed_within={r: {gr: float(sp.loc[r, gr]) for gr in order} for r in roads},
        exp_within={r: {gr: float(ex.loc[r, gr]) for gr in order} for r in roads},
        injuries=int(g.head_injuries.sum()), trips=int(g.trips.sum()))
    print("  share of trips by road:\n", share.round(3).to_string())
    print("  rate per 1000 by road x grade:\n", rate.round(2).to_string())
    print("  standardised:", {k: round(v, 2) for k, v in std.items()})

    # ---- redesign: where they ride | rate within road type
    fig, ax = plt.subplots(1, 2, figsize=(10.5, 4.0), gridspec_kw=dict(width_ratios=[1, 1.25]))
    a, b = ax
    y = np.arange(2)
    left = np.zeros(2)
    cols = {"Motorway": C[1], "City arterial": C[0], "Inner-city lanes": C[2]}
    for r in roads:
        vals = np.array([share.loc[r, "Standard"], share.loc[r, "Premium"]]) * 100
        a.barh(y, vals, left=left, color=cols[r], label=r, height=0.55)
        for yi, v, l in zip(y, vals, left):
            if v > 6:
                a.text(l + v / 2, yi, f"{v:.0f}%", ha="center", va="center",
                       color="white", fontsize=9, fontweight="bold")
        left += vals
    a.set_yticks(y, ["Standard", "Premium"]); a.set_xlim(0, 100)
    a.set_xlabel("Share of the grade's trips (%)")
    a.set_title("Premium riders ride the motorway;\nStandard riders ride the inner city")
    a.legend(loc="upper center", bbox_to_anchor=(0.5, -0.2), ncol=3, fontsize=8)
    a.grid(axis="y", visible=False)
    x = np.arange(len(roads)); wd = 0.36
    b1 = b.bar(x - wd / 2, [rate.loc[r, "Standard"] for r in roads], wd, color=C[0], label="Standard")
    b2 = b.bar(x + wd / 2, [rate.loc[r, "Premium"] for r in roads], wd, color=C[1],
               hatch="//", edgecolor="white", label="Premium")
    b.bar_label(b1, fmt="%.1f", padding=2, fontsize=8); b.bar_label(b2, fmt="%.1f", padding=2, fontsize=8)
    b.set_xticks(x, roads); b.set_ylim(0, 9)
    b.set_ylabel("Head injuries per 1,000 trips")
    b.set_title("Within every road type, Premium is the safer helmet")
    b.legend(loc="upper right"); b.grid(axis="x", visible=False)
    fig.tight_layout()
    save(fig, "case1_redesign.png",
         f"Rates computed as sum(injuries)/sum(trips)*1000 per cell. y from zero. {SRC}")


# =============================================================================
# CASE 2  chai
# =============================================================================
def case2():
    print("\nCASE 2  chai and quizzes")
    d = pd.read_csv(os.path.join(DATA, "case02_chai_quizzes.csv"))
    r = d.cups_doodh_patti_sold.corr(d.quiz_failures)
    check("r", r, 0.98, 0.006)
    fig, ax = plt.subplots(figsize=(5.8, 4.2))
    ax.scatter(d.cups_doodh_patti_sold, d.quiz_failures, color=C[0], s=28)
    s, i, *_ = stats.linregress(d.cups_doodh_patti_sold, d.quiz_failures)
    xs = np.array([d.cups_doodh_patti_sold.min(), d.cups_doodh_patti_sold.max()])
    ax.plot(xs, i + s * xs, color=PALETTE["ink"], lw=1.8)
    ax.text(0.05, 0.93, f"Pearson r = {r:.2f}", transform=ax.transAxes, fontsize=10)
    ax.set_xlabel("Cups of doodh patti sold per month"); ax.set_ylabel("Quiz failures per month")
    ax.set_title("Chai sales predict quiz failures")
    save(fig, "case2_rebuild.png", f"One point per month, n = 24, OLS line. {SRC}")

    d["cups_ps"] = d.cups_doodh_patti_sold / d.students_enrolled
    d["fail_per1000"] = d.quiz_failures / d.students_enrolled * 1000
    ex = d[d.is_exam_month == 0]
    r_noexam = ex.cups_doodh_patti_sold.corr(ex.quiz_failures)
    r_rate = d.cups_ps.corr(d.fail_per1000)
    # partial correlation controlling for enrolment
    def resid(y, x):
        s, i, *_ = stats.linregress(x, y); return y - (i + s * x)
    r_partial = np.corrcoef(resid(d.cups_doodh_patti_sold, d.students_enrolled),
                            resid(d.quiz_failures, d.students_enrolled))[0, 1]
    M["c2"] = dict(r=r, r_noexam=r_noexam, n_exam=int(d.is_exam_month.sum()),
                   r_cups_enrol=d.cups_doodh_patti_sold.corr(d.students_enrolled),
                   r_fail_enrol=d.quiz_failures.corr(d.students_enrolled),
                   r_exam_cups=d.is_exam_month.corr(d.cups_doodh_patti_sold),
                   enrol_first=int(d.students_enrolled.iloc[0]), enrol_last=int(d.students_enrolled.iloc[-1]),
                   enrol_ratio=d.students_enrolled.iloc[-1] / d.students_enrolled.iloc[0],
                   cps_min=d.cups_ps.min(), cps_max=d.cups_ps.max(),
                   fail_min=d.fail_per1000.min(), fail_max=d.fail_per1000.max(),
                   r_rate=r_rate, r_partial=r_partial,
                   p_rate=float(stats.pearsonr(d.cups_ps, d.fail_per1000).pvalue),
                   fail_exam=float(d[d.is_exam_month == 1].fail_per1000.mean()),
                   fail_nonexam=float(d[d.is_exam_month == 0].fail_per1000.mean()))
    print("  ", {k: round(v, 3) if isinstance(v, float) else v for k, v in M["c2"].items()})

    fig, ax = plt.subplots(1, 2, figsize=(10.8, 4.0))
    a, b = ax
    mid = pd.to_datetime(d.month)
    a.plot(mid, d.cups_ps, color=C[0], marker=MARKERS[0], ms=3.5)
    a.set_ylim(0, 3); a.set_ylabel("Cups sold per enrolled student")
    a.set_title("Per student, chai sales are flat\n(2.0-2.2 cups all along)")
    b.plot(mid, d.fail_per1000, color=C[1], marker=MARKERS[1], ms=3.5)
    b.set_ylim(0, 60); b.set_ylabel("Quiz failures per 1,000 students")
    b.set_title("Per student, failures are nearly flat too\n(exam months run a little higher)")
    exm = mid[d.is_exam_month == 1]
    for p in (a, b):
        for t in exm:
            p.axvspan(t - pd.Timedelta(days=15), t + pd.Timedelta(days=15), color=PALETTE["grid"], alpha=0.7, lw=0)
        p.tick_params(axis="x", rotation=35)
    fig.tight_layout()
    save(fig, "case2_redesign.png",
         "Two panels, one measure each, both y-axes from zero. Grey bands = exam months. "
         f"Rates divided by students_enrolled. {SRC}")


# =============================================================================
# CASE 3  AQI
# =============================================================================
def case3():
    print("\nCASE 3  AQI")
    d = pd.read_csv(os.path.join(DATA, "case03_aqi_monitors.csv"), parse_dates=["date"])
    d["day"] = (d.date - d.date.min()).dt.days + 1
    daily = d.groupby("day").aqi.mean()
    before, after = daily[daily.index <= 60].mean(), daily[daily.index > 60].mean()
    # the brief's self-check uses the mean over all rows in each period
    b_rows, a_rows = d[d.day <= 60].aqi.mean(), d[d.day > 60].aqi.mean()
    fall = a_rows / b_rows - 1
    check("before", b_rows, 202, 0.6); check("after", a_rows, 137, 0.6)
    check("fall", fall * -100, 32, 0.6)

    fig, ax = plt.subplots(figsize=(8.4, 4.0))
    ax.plot(daily.index, daily.values, color=C[0], lw=1.4)
    ax.axvline(61, color=PALETTE["ink_soft"], ls="--"); ax.text(61.5, 15, "Plan starts (day 61)", fontsize=8.5)
    ax.hlines(b_rows, 1, 60, color=C[1], lw=2); ax.hlines(a_rows, 61, 120, color=C[2], lw=2)
    ax.text(2, b_rows + 8, f"mean {b_rows:.0f}", color=C[1], fontsize=9)
    ax.text(62, a_rows + 8, f"mean {a_rows:.0f}", color=C[2], fontsize=9)
    ax.set_ylim(0, 260); ax.set_xlabel("Day (1 = 1 Jan 2026)"); ax.set_ylabel("Mean AQI across reporting stations")
    ax.set_title(f"The Smog Action Plan cut Lahore's AQI by {-fall:.0%}")
    save(fig, "case3_rebuild.png", f"Mean aqi per date over all rows (blanks skipped); y from zero. {SRC}")

    # ---- diagnosis: who stopped reporting?
    d["reporting"] = d.aqi.notna()
    zone = d.groupby([d.day > 60, "zone"]).agg(mean=("aqi", "mean"), rows=("aqi", "size"),
                                                reporting=("reporting", "sum")).reset_index()
    zone["period"] = np.where(zone["day"], "after", "before")
    stat = {f"{r.zone}|{r.period}": dict(mean=None if np.isnan(r["mean"]) else float(r["mean"]),
                                         rows=int(r.rows), reporting=int(r.reporting))
            for _, r in zone.iterrows()}
    # like-for-like: stations that reported in BOTH periods
    both = d.groupby("station_id").apply(
        lambda g: g[g.day <= 60].aqi.notna().any() and g[g.day > 60].aqi.notna().any(),
        include_groups=False)
    keep = both[both].index
    lfl = d[d.station_id.isin(keep)]
    lfl_b, lfl_a = lfl[lfl.day <= 60].aqi.mean(), lfl[lfl.day > 60].aqi.mean()
    ind_before = d[(d.zone == "Industrial") & (d.day <= 60)].aqi.mean()
    off_after = d[(d.day > 60)].groupby("zone").reporting.mean()
    stations_b = d[(d.day <= 60)].groupby("day").aqi.count().mean()
    stations_a = d[(d.day > 60)].groupby("day").aqi.count().mean()
    M["c3"] = dict(before=b_rows, after=a_rows, fall=fall, zone=stat,
                   n_stations_keep=int(len(keep)), n_stations=int(d.station_id.nunique()),
                   lfl_before=float(lfl_b), lfl_after=float(lfl_a), lfl_change=float(lfl_a / lfl_b - 1),
                   ind_before=float(ind_before), reporting_after={k: float(v) for k, v in off_after.items()},
                   stations_per_day_before=float(stations_b), stations_per_day_after=float(stations_a),
                   n_blank=int(d.aqi.isna().sum()),
                   n_industrial=int(d[d.zone == "Industrial"].station_id.nunique()))
    print("  zone means:", {k: (None if v["mean"] is None else round(v["mean"], 1)) for k, v in stat.items()})
    print("  like-for-like:", round(lfl_b, 1), "->", round(lfl_a, 1), f"({lfl_a / lfl_b - 1:+.1%})")

    fig, ax = plt.subplots(1, 2, figsize=(11, 4.2), gridspec_kw=dict(width_ratios=[1.4, 1]))
    a, b = ax
    zcol = {"Industrial": C[1], "Arterial": C[0], "Residential": C[2], "Peri-urban": PALETTE["series_4th"]}
    for z, col in zcol.items():
        s = d[d.zone == z].groupby("day").aqi.mean().reindex(range(1, 121))
        a.plot(s.index, s.values, color=col, lw=1.5)
        last = s.dropna().index[-1]
        a.text(min(last, 120) + 1, s.dropna().iloc[-1], z, color=col, fontsize=8.5, va="center")
    a.axvline(61, color=PALETTE["ink_soft"], ls="--")
    a.set_xlim(0, 135); a.set_ylim(0, 380)
    a.set_xlabel("Day (1 = 1 Jan 2026)"); a.set_ylabel("Mean AQI of reporting stations")
    a.set_title("By zone, nothing changed on day 61:\nthe Industrial stations simply stopped reporting")
    # like-for-like bars
    b.bar(["Before\n(days 1-60)", "After\n(days 61-120)"], [lfl_b, lfl_a], color=[C[1], C[2]], width=0.5)
    b.bar_label(b.containers[0], fmt="%.0f", padding=3)
    b.set_ylim(0, 260); b.set_ylabel("Mean AQI, same stations only")
    b.set_title(f"Like-for-like ({len(keep)} stations that reported\nin both periods): {lfl_a / lfl_b - 1:+.0%}")
    b.grid(axis="x", visible=False)
    fig.tight_layout()
    save(fig, "case3_redesign.png",
         "Lines are broken where a zone has no reporting station. Direct labels, no legend. "
         f"Like-for-like = stations with data in both periods. {SRC}")


# =============================================================================
# CASE 4 / 5  summary-statistics tables and the shapes behind them
# =============================================================================
def stats_table(df, grp, xcol, ycol, ddof):
    rows = {}
    for k, g in df.groupby(grp, sort=False):
        s = stats.linregress(g[xcol], g[ycol])
        rows[k] = {"n": len(g), "mean x": g[xcol].mean(), "mean y": g[ycol].mean(),
                   "SD x": g[xcol].std(ddof=ddof), "SD y": g[ycol].std(ddof=ddof),
                   "Pearson r": g[xcol].corr(g[ycol]), "slope": s.slope}
    return pd.DataFrame(rows)


def table_figure(tbl, title, name, note, fmt):
    fig, ax = plt.subplots(figsize=(1.9 + 1.55 * tbl.shape[1], 0.5 + 0.34 * (len(tbl) + 1)))
    ax.axis("off")
    cell = [[fmt(i, v) for v in tbl.loc[i]] for i in tbl.index]
    t = ax.table(cellText=cell, rowLabels=list(tbl.index), colLabels=[c.replace(" ", "\n", 1) if len(c) > 12 else c for c in tbl.columns],
                 loc="center", cellLoc="center")
    t.auto_set_font_size(False); t.set_fontsize(9); t.scale(1, 1.4)
    for (r, c), ce in t.get_celld().items():
        ce.set_edgecolor(PALETTE["grid"])
        if r == 0:
            ce.set_text_props(fontweight="bold"); ce.set_facecolor("#F1F5F9")
    ax.set_title(title, pad=2)
    save(fig, name, note)


def case4():
    print("\nCASE 4  four departments")
    d = pd.read_csv(os.path.join(DATA, "case04_quartet_depts.csv"))
    t = stats_table(d, "department", "study_hours_per_week", "final_score_out_of_20", ddof=1)
    for dep in t.columns:
        check(f"{dep} mean x", t.loc["mean x", dep], 18.0, 0.005)
        check(f"{dep} mean y", t.loc["mean y", dep], 14.5, 0.005)
        check(f"{dep} r", t.loc["Pearson r", dep], 0.816, 0.001)
    t.T.round(3).to_csv(os.path.join(OUT, "case4_table.csv"))
    fmt = lambda i, v: f"{int(v)}" if i == "n" else f"{v:.3f}" if i in ("Pearson r", "slope") else f"{v:.2f}"
    table_figure(t.T, "Four departments, identical summary statistics (the analyst's table)",
                 "case4_rebuild.png", f"Sample SD (ddof = 1). {SRC}", lambda i, v: fmt("x", v) if False else
                 (f"{int(v)}" if float(v).is_integer() and v > 5 and v < 12 else f"{v:.3f}"))
    # diagnosis numbers: which dept is which shape
    deps = list(t.columns); info = {}
    for dep in deps:
        g = d[d.department == dep]; x, y = g.study_hours_per_week.values, g.final_score_out_of_20.values
        lin = stats.linregress(x, y); res = y - (lin.intercept + lin.slope * x)
        r2l = lin.rvalue ** 2
        if len(set(x)) >= 3:
            q = np.polyfit(x, y, 2); resq = y - np.polyval(q, x); r2q = 1 - resq.var() / y.var()
        else:
            r2q = None                                     # a quadratic is not identifiable
        h = 1 / len(x) + (x - x.mean()) ** 2 / ((x - x.mean()) ** 2).sum()
        s2 = (res ** 2).sum() / (len(x) - 2)
        with np.errstate(divide="ignore", invalid="ignore"):
            cook = res ** 2 / (2 * s2) * h / (1 - h) ** 2
        cmax = float(np.nanmax(cook)) if np.isfinite(cook).any() else None
        info[dep] = dict(r2_lin=r2l, r2_quad=(None if r2q is None else float(r2q)), max_cook=cmax, max_lev=float(h.max()),
                         distinct_x=int(len(set(x))), max_abs_res=float(np.abs(res).max()))
    M["c4"] = dict(stats={dep: {k: float(v) for k, v in t[dep].items()} for dep in deps}, shape=info)
    print("  shape metrics:", {k: {kk: (round(vv, 2) if vv is not None else None) for kk, vv in v.items()} for k, v in info.items()})

    fig, ax = plt.subplots(1, 4, figsize=(13, 3.5), sharex=True, sharey=True)
    for a, dep in zip(ax, deps):
        g = d[d.department == dep]
        a.scatter(g.study_hours_per_week, g.final_score_out_of_20, color=C[0], s=30)
        lin = stats.linregress(g.study_hours_per_week, g.final_score_out_of_20)
        xs = np.array([g.study_hours_per_week.min(), g.study_hours_per_week.max()]); a.plot(xs, lin.intercept + lin.slope * xs, color=PALETTE["ink"], lw=1.3)
        a.set_title(dep, fontsize=10.5); a.set_xlabel("Study hours / week")
    ax[0].set_ylabel("Final score (/20)")
    fig.suptitle("Same line, four different stories: a curve, an outlier, one lever point, and a clean fit",
                 x=0.005, ha="left", fontsize=11.5, fontweight="bold")
    fig.tight_layout(rect=[0, 0, 1, 0.9])
    save(fig, "case4_redesign.png", f"OLS line in each panel; shared axes. {SRC}")


def case5():
    print("\nCASE 5  five cohorts")
    d = pd.read_csv(os.path.join(DATA, "case05_same_stats_shapes.csv"))
    t = stats_table(d, "shape_name", "hours_on_platform", "assessment_score", ddof=0)
    for s in t.columns:
        check(f"{s} mean", t.loc["mean x", s], 48.0, 0.01); check(f"{s} SD y", t.loc["SD y", s], 15.0, 0.01)
        check(f"{s} r", t.loc["Pearson r", s], 0.420, 0.001)
    t.T.round(3).to_csv(os.path.join(OUT, "case5_table.csv"))
    table_figure(t.T, "Five cohorts, one set of statistics (the analyst's table)", "case5_rebuild.png",
                 f"Population SD (ddof = 0). {SRC}",
                 lambda i, v: f"{int(v)}" if float(v).is_integer() and v >= 100 else f"{v:.3f}")
    maxdev = max(abs(t.loc["mean x"] - 48).max(), abs(t.loc["mean y"] - 63).max(),
                 abs(t.loc["SD x"] - 12).max(), abs(t.loc["SD y"] - 15).max(), abs(t.loc["Pearson r"] - 0.42).max())
    # shape metrics: residual scatter about the common regression line, and bimodality of x
    shp = {}
    for s in t.columns:
        g = d[d.shape_name == s]; sl = stats.linregress(g.hours_on_platform, g.assessment_score)
        res = g.assessment_score - (sl.intercept + sl.slope * g.hours_on_platform)
        shp[s] = dict(r2=sl.rvalue ** 2, resid_sd=float(res.std()), x_min=float(g.hours_on_platform.min()),
                      x_max=float(g.hours_on_platform.max()), y_min=float(g.assessment_score.min()),
                      y_max=float(g.assessment_score.max()), x_kurt=float(stats.kurtosis(g.hours_on_platform)))
    M["c5"] = dict(max_dev=float(maxdev), shape=shp, n=int(len(d) // 5))
    print("  max deviation from targets:", f"{maxdev:.1e}")

    fig, ax = plt.subplots(1, 5, figsize=(15, 3.3), sharex=True, sharey=True)
    for a, s in zip(ax, t.columns):
        g = d[d.shape_name == s]
        a.scatter(g.hours_on_platform, g.assessment_score, s=7, alpha=0.7, color=C[0], edgecolors="none")
        a.set_title(s, fontsize=10.5); a.set_xlabel("Hours on platform")
    ax[0].set_ylabel("Assessment score")
    fig.suptitle("Same mean, SD and r = 0.420 in all five: a line, a ring, a star, two clusters and the letter X",
                 x=0.005, ha="left", fontsize=11.5, fontweight="bold")
    fig.tight_layout(rect=[0, 0, 1, 0.88])
    save(fig, "case5_redesign.png", f"n = 180 per cohort, shared axes. {SRC}")


# =============================================================================
# CASE 6  correlation matrix
# =============================================================================
def case6():
    print("\nCASE 6  correlation heatmap")
    d = pd.read_csv(os.path.join(DATA, "case06_sensor_matrix.csv"))
    num = d.drop(columns=["age_band", "study_site", "hr_device_model"])
    cm = num.corr()
    assert cm.shape == (20, 20)
    check("creatinine-hba1c", cm.loc["creatinine", "hba1c"], 0.77, 0.006)
    check("systolic-map", cm.loc["systolic", "map_mmhg"], 0.96, 0.006)

    fig, ax = plt.subplots(figsize=(9.2, 7.6))
    sns.heatmap(cm, ax=ax, cmap="Reds", annot=True, fmt=".2f", annot_kws={"size": 5.5}, cbar_kws={"label": "r"})
    ax.set_title("Creatinine tracks HbA1c: a finding"); ax.grid(False)
    ax.tick_params(labelsize=7)
    save(fig, "case6_rebuild.png", "cmap='Reds', no vmin/vmax, both triangles shown (as published). " + SRC)

    # ---- diagnosis numbers
    worst = num.creatinine.idxmax()
    keep = num.index != worst
    r_wo = num.loc[keep, "hba1c"].corr(num.loc[keep, "creatinine"])
    sp = stats.spearmanr(num.hba1c, num.creatinine).statistic
    iu = np.triu_indices(20, 1)
    pairs = [(num.columns[i], num.columns[j], cm.iloc[i, j]) for i, j in zip(*iu)]
    strong = [p for p in pairs if abs(p[2]) >= 0.5]
    off = np.array([p[2] for p in pairs])
    M["c6"] = dict(r=float(cm.loc["creatinine", "hba1c"]), r_wo=float(r_wo), spearman=float(sp),
                   row=int(worst), hba1c_row=float(num.loc[worst, "hba1c"]), creat_row=float(num.loc[worst, "creatinine"]),
                   hba1c_med=float(num.hba1c.median()), creat_med=float(num.creatinine.median()),
                   hba1c_max_wo=float(num.loc[keep, "hba1c"].max()), creat_max_wo=float(num.loc[keep, "creatinine"].max()),
                   r_age_hba1c=float(num.age_years.corr(num.hba1c)), r_age_creat=float(num.age_years.corr(num.creatinine)),
                   n_pairs=len(pairs), strong=[(a, b, float(r)) for a, b, r in strong],
                   cm_min=float(off.min()), n_neg=int((off < 0).sum()),
                   probe_max=float(cm.loc[[f"probe_{c}" for c in "abcdef"], [c for c in cm.columns if not c.startswith("probe")]].abs().max().max()))
    print("  r", round(M["c6"]["r"], 3), "-> without row", worst, round(r_wo, 3), "| spearman", round(sp, 3))

    fig, ax = plt.subplots(1, 2, figsize=(14, 6.2), gridspec_kw=dict(width_ratios=[1.3, 1]))
    a, b = ax
    mask = np.triu(np.ones_like(cm, dtype=bool), k=1)
    sns.heatmap(cm, ax=a, mask=mask, cmap=PALETTE["diverging"], vmin=-1, vmax=1, center=0, annot=True, fmt=".2f",
                annot_kws={"size": 5.5}, linewidths=0.4, linecolor="white", cbar_kws={"label": "Pearson r", "shrink": 0.8})
    a.grid(False); a.tick_params(labelsize=7)
    a.set_title("Fixed drawing: diverging map pinned to -1...+1, upper triangle masked\n"
                "(the 0.77 cell is still 0.77 - drawing was never the main problem)", fontsize=10)
    keepdf = num[keep]
    b.scatter(keepdf.hba1c, keepdf.creatinine, color=C[0], s=18, alpha=0.8, label=f"179 participants (r = {abs(r_wo) if abs(r_wo) < 0.005 else r_wo:.2f})")
    b.scatter([num.loc[worst, "hba1c"]], [num.loc[worst, "creatinine"]], color=C[1], s=70, marker="D",
              label=f"one participant (row {worst}): HbA1c {num.loc[worst, 'hba1c']:.1f}%, creatinine {num.loc[worst, 'creatinine']:.0f}")
    b.set_xlabel("HbA1c (%)"); b.set_ylabel("Creatinine (umol/L)")
    b.set_title(f"One participant manufactures r = {M['c6']['r']:.2f};\nwithout them r = {abs(r_wo) if abs(r_wo) < 0.005 else r_wo:.2f} (Spearman {sp:.2f})", fontsize=10.5)
    b.legend(loc="center right", fontsize=8)
    fig.tight_layout()
    save(fig, "case6_redesign.png", f"n = 180, pairwise Pearson; Spearman computed with scipy. {SRC}")


# =============================================================================
# CASE 7  dual axis
# =============================================================================
def case7():
    print("\nCASE 7  dual axis")
    d = pd.read_csv(os.path.join(DATA, "case07_dual_axis_series.csv"))
    fig, ax = plt.subplots(figsize=(7.4, 4.0))
    ax2 = ax.twinx()
    ax.plot(d.month, d.revenue_pkr_m, color=C[0], marker="o"); ax.set_ylim(50, 80)
    ax2.plot(d.month, d.cost_pkr_m, color=C[1], marker="s"); ax2.set_ylim(40, 56)
    ax.set_ylabel("Revenue (PKR m)", color=C[0]); ax2.set_ylabel("Cost (PKR m)", color=C[1])
    ax2.grid(False); ax2.spines["right"].set_visible(True)
    ax.set_title("ShaheenGo ran at a loss until May")
    # visual crossing: in pixel space cost line above revenue line?
    disp = lambda a, v: a.transData.transform((0, v))[1]
    fig.canvas.draw()
    above = [disp(ax2, c) > disp(ax, r) for r, c in zip(d.revenue_pkr_m, d.cost_pkr_m)]
    print("  cost line drawn above revenue line, by month:", above)
    assert above[:4] == [True] * 4, "self-check: first four months"
    M["c7_drawn_above"] = int(sum(above))
    save(fig, "case7_rebuild.png", f"Two y-axes via ax.twinx(): 50-80 and 40-56 (as published). {SRC}")

    d["margin"] = d.revenue_pkr_m - d.cost_pkr_m
    M["c7"] = dict(margin_min=int(d.margin.min()), margin_max=int(d.margin.max()),
                   rev_growth=float(d.revenue_pkr_m.iloc[-1] / d.revenue_pkr_m.iloc[0] - 1),
                   cost_growth=float(d.cost_pkr_m.iloc[-1] / d.cost_pkr_m.iloc[0] - 1),
                   crossing_months=int(M["c7_drawn_above"]))
    fig, ax = plt.subplots(1, 2, figsize=(10.6, 3.9))
    a, b = ax
    a.plot(d.month, d.revenue_pkr_m, color=C[0], marker="o"); a.plot(d.month, d.cost_pkr_m, color=C[1], marker="s")
    a.text(5.1, d.revenue_pkr_m.iloc[-1], "Revenue", color=C[0], va="center", fontsize=9)
    a.text(5.1, d.cost_pkr_m.iloc[-1], "Cost", color=C[1], va="center", fontsize=9)
    a.set_ylim(0, 90); a.set_xlim(-0.3, 5.9); a.set_ylabel("PKR millions (one shared axis)")
    a.set_title("Revenue is above cost in every month")
    bars = b.bar(d.month, d.margin, color=C[2], width=0.55); b.bar_label(bars, padding=2, fontsize=9)
    b.set_ylim(0, 30); b.set_ylabel("Revenue minus cost (PKR millions)")
    b.set_title(f"Margin never below {d.margin.min()}: it widens from {d.margin.iloc[0]} to {d.margin.iloc[-1]}")
    b.grid(axis="x", visible=False)
    fig.tight_layout()
    save(fig, "case7_redesign.png", f"Two panels, no twin axes, both y-axes from zero. {SRC}")


# =============================================================================
# CASE 8  bin width       CASE 9  KDE ceiling
# =============================================================================
def case8():
    print("\nCASE 8  bin widths")
    v = pd.read_csv(os.path.join(DATA, "vitals_10k.csv"))
    x = v.systolic.to_numpy()
    fig, ax = plt.subplots(1, 3, figsize=(13, 3.6))
    ns = []
    for a, b in zip(ax, [3, 45, 400]):
        h, _, _ = a.hist(x, bins=b, color=C[0], edgecolor="white", linewidth=0.3)
        ns.append(int(h.sum())); a.set_title(f"bins = {b}", fontsize=10.5); a.set_xlabel("Systolic (mmHg)")
        if b == 3:
            a.set_ylabel("Patients")
    assert ns == [10000] * 3; print("  n per panel:", ns)
    fig.suptitle("Three bin widths, three different distributions", x=0.005, ha="left", fontsize=12, fontweight="bold")
    fig.tight_layout(rect=[0, 0, 1, 0.9])
    save(fig, "case8_rebuild.png", f"Each panel n = 10,000; sharing nothing but the data. {SRC}")

    h400, e400 = np.histogram(x, bins=400)
    iqr = np.subtract(*np.percentile(x, [75, 25])); fd = 2 * iqr * len(x) ** (-1 / 3)
    sturges = int(np.ceil(np.log2(len(x)) + 1))
    M["c8"] = dict(n=ns, unique=int(len(np.unique(x))), width400=float((x.max() - x.min()) / 400),
                   empty400=float((h400 == 0).mean()), fd=float(fd), sturges=sturges,
                   range=(int(x.min()), int(x.max())), width3=float((x.max() - x.min()) / 3),
                   width45=float((x.max() - x.min()) / 45))
    print("  unique values", M["c8"]["unique"], "empty bins at 400:", round(M["c8"]["empty400"], 2), "FD width", round(fd, 2))

    fig, ax = plt.subplots(figsize=(7.4, 4.0))
    bw = 3
    edges = np.arange(x.min() - 0.5, x.max() + bw, bw)
    ax.hist(x, bins=edges, color=C[0], edgecolor="white", linewidth=0.4)
    ax.text(0.98, 0.95, f"bin width = {bw} mmHg (Freedman-Diaconis: {fd:.1f})\nn = {len(x):,}\nbins aligned to whole mmHg",
            transform=ax.transAxes, ha="right", va="top", fontsize=8.5, color=PALETTE["ink_soft"])
    ax.set_xlabel("Systolic blood pressure (mmHg)"); ax.set_ylabel("Patients per bin")
    ax.set_title("Two populations, peaking near 121 and 163 mmHg")
    save(fig, "case8_redesign.png", f"One declared bin width, chosen by rule (FD = 2*IQR*n^(-1/3)) and rounded to whole mmHg. {SRC}")


def case9():
    print("\nCASE 9  KDE above 100%")
    v = pd.read_csv(os.path.join(DATA, "vitals_10k.csv")); x = v.spo2.to_numpy().astype(float)
    assert x.max() == 100
    kde = stats.gaussian_kde(x)           # default bandwidth: Scott's rule, the same default seaborn uses
    grid = np.linspace(80, 108, 1200); dens = kde(grid)
    above = float(kde.integrate_box_1d(100, np.inf))
    fig, ax = plt.subplots(figsize=(7.2, 4.0))
    ax.plot(grid, dens, color=C[0]); ax.fill_between(grid, dens, where=grid > 100, color=C[1], alpha=0.6)
    ax.axvline(100, color=PALETTE["ink"], ls="--"); ax.set_xlim(80, 108)
    ax.text(100.4, dens.max() * 0.55, f"{above:.1%} of the\ndensity is above\n100% SpO2", color=C[1], fontsize=9)
    ax.set_xlabel("SpO2 (%)"); ax.set_ylabel("Density")
    ax.set_title(f"The curve puts {above:.1%} of its density above 100% saturation")
    save(fig, "case9_rebuild.png", f"gaussian_kde, default (Scott) bandwidth {kde.factor * x.std(ddof=1):.2f}; x extended to 108. {SRC}")

    cnt = pd.Series(x.astype(int)).value_counts().sort_index()
    M["c9"] = dict(max=float(x.max()), above=above, bw=float(kde.factor * x.std(ddof=1)),
                   n100=int(cnt.get(100, 0)), share100=float(cnt.get(100, 0) / len(x)),
                   n_values=int(len(cnt)), min=float(x.min()))
    print("  max", x.max(), "| density above 100:", f"{above:.3%}")
    above995 = float(kde.integrate_box_1d(99.5, np.inf))
    M["c9"]["above_995"] = above995
    print(f"  NOTE: the brief quotes 4.4%; default-bandwidth KDE gives {above:.2%} above 100 "
          f"({above995:.2%} above 99.5). Reported as measured. Self-check that matters: "
          f"max = {x.max():.0f}, curve extends past it.")

    fig, ax = plt.subplots(figsize=(7.2, 4.0))
    cnt = cnt[cnt.index >= 85]
    col = [C[1] if i == 100 else C[0] for i in cnt.index]
    bars = ax.bar(cnt.index, cnt.values / len(x) * 100, color=col, width=0.8)
    ax.set_xlim(84, 102); ax.set_xticks(range(86, 101, 2))
    ax.text(100, cnt[100] / len(x) * 100 + 1.2, f"{cnt[100] / len(x):.1%}\nat the 100% ceiling", ha="center", fontsize=8.5, color=C[1])
    ax.set_xlabel("SpO2 (%, whole numbers as recorded)"); ax.set_ylabel("Share of patients (%)")
    ax.set_title("SpO2 is whole-number and capped: nothing is recorded above 100%")
    ax.grid(axis="x", visible=False)
    save(fig, "case9_redesign.png", f"One bar per recorded integer value, n = 10,000, no smoothing, x cut at 85 for legibility. {SRC}")


def main():
    for f in (case1, case2, case3, case4, case5, case6, case7, case8, case9):
        f()
    def clean(o):
        if isinstance(o, dict): return {str(k): clean(v) for k, v in o.items()}
        if isinstance(o, (list, tuple)): return [clean(i) for i in o]
        if isinstance(o, (np.floating, np.integer)): return o.item()
        return o
    with open(os.path.join(ROOT, "partA_metrics.json"), "w") as fh:
        json.dump(clean(M), fh, indent=1)
    print("\nall nine cases rebuilt and redesigned; metrics -> partA_metrics.json")


if __name__ == "__main__":
    main()
