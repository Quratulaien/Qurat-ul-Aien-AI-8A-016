"""
Part A — rebuild nine published charts, then plot the nine redesigns
(CDB601220, Week 5). Synthetic course data — fictional places.

    python3 partA_charts.py   -> partA_case01.png … partA_case09.png (300 dpi)
                                 + the evidence printed to stdout (partA_output.txt)

Each rebuild follows the analyst's recipe and ASSERTS its self-check number
before anything is diagnosed.
"""
import itertools

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Patch
import numpy as np
import pandas as pd
from scipy import stats

import geolib
from geolib import PALETTE, style_defaults
from w5common import D, HERE, NUM_COLS, PER, SYNTH, corr_chain, districts, health, pooled_rate
import partD_bubble as bub

BLUE, ORANGE, GREEN = PALETTE["series"]
PINK, GREY, INK = PALETTE["series_4th"], PALETTE["muted"], PALETTE["ink"]


def new_fig(case, claim, w=13, h=5.0, right_cols=1, polar_left=False, headline=None):
    fig = plt.figure(figsize=(w, h))
    gs = fig.add_gridspec(1, 2, wspace=0.28)
    ax_l = fig.add_subplot(gs[0, 0], projection="polar" if polar_left else None)
    sub = gs[0, 1].subgridspec(1, right_cols, wspace=0.45)
    ax_r = [fig.add_subplot(sub[0, j]) for j in range(right_cols)]
    top = 1.03
    if headline:
        fig.text(0.53, 0.985, headline, fontsize=10, fontweight="bold", ha="left", va="bottom")
        top = 1.03 + 0.42 / h
    fig.suptitle(f"Case {case} — the published claim: “{claim}”", x=0.01, ha="left",
                 fontsize=12.5, fontweight="bold", y=top)
    return fig, ax_l, ax_r


def rebuilt(ax, title):
    ax.set_title("REBUILT AS PUBLISHED\n" + title, fontsize=10, color=PALETTE["ink_soft"],
                 loc="left")


def finish(fig, case, src):
    fig.text(0.01, -0.07, f"Source: {SYNTH} ({src}).", fontsize=7,
             color=PALETTE["ink_soft"], ha="left", va="top")
    out = HERE / f"partA_case{case:02d}.png"
    fig.savefig(out, dpi=300, bbox_inches="tight", facecolor=PALETTE["surface"])
    plt.close(fig)
    print(f"   saved {out.name}")


def head(n, text):
    print("\n" + "=" * 78 + f"\nCASE {n}: {text}\n" + "=" * 78)


def disc(a, b):
    """share of pairs whose order flips between two axes = lines crossing in the gap"""
    a, b = np.asarray(a), np.asarray(b)
    i, j = np.triu_indices(len(a), 1)
    return float(((a[i] - a[j]) * (b[i] - b[j]) < 0).mean())


# ========================================================================= 1
def case1():
    head(1, "Population and healthcare access are unrelated")
    h = health()
    s = h.pop_m ** 2
    diam = np.sqrt(s)                      # marker diameter in points = sqrt(area)
    print(f"marks {len(h)}; s=pop_m**2 -> area ratio {s.max()/s.min():,.0f}×, DIAMETER ratio "
          f"{diam.max()/diam.min():.0f}× (radius ∝ value)")
    print(f"countries < 2.0 M people: {(h.pop_m < 2).sum()} -> drawn {diam[h.pop_m < 2].max():.1f} pt "
          f"across or less; under 1 pt across: {(diam < 1).sum()}")
    print("  [finding] the brief's '589× the area' is 589× the DIAMETER; area is 589² = "
          f"{589**2:,}×. The 9 sub-2 M countries are < 2 pt wide (3 are < 1 pt).")
    assert len(h) == 60 and round(diam.max() / diam.min()) == 589 and (h.pop_m < 2).sum() == 9
    print(f"largest mark (Wessant, 353.4 M): {diam.max():.0f} pt = {diam.max()/72:.1f} in across "
          f"on a 6.4 in figure; Vornath {np.sqrt(238**2)/72:.1f} in")
    r_lin = np.corrcoef(h.pop_m, h.healthcare_access)[0, 1]
    r_log = np.corrcoef(np.log10(h.pop_m), h.healthcare_access)[0, 1]
    print(f"actual relation: r(pop, access) {r_lin:+.2f}, r(log pop, access) {r_log:+.2f}; "
          f"countries ≥50 M mean access {h[h.pop_m>=50].healthcare_access.mean():.1f} vs "
          f"{h[h.pop_m<50].healthcare_access.mean():.1f}")
    print("decoy 'the log x-axis distorts it': GDP spans $283–$120,219 (425×); log is the right "
          "axis — the x positions are fine, the SIZE channel is what is broken")
    fig, ax, (ax2,) = new_fig(1, "Population and healthcare access are unrelated — the large "
                                 "countries are spread right across the range", h=5.6)
    ax.scatter(h.gdp_pc, h.healthcare_access, s=s, c=GREY, alpha=0.5, edgecolor="white")
    ax.set_xscale("log")
    ax.set_xlabel("GDP per capita, USD (log)")
    ax.set_ylabel("Healthcare access (0–100)")
    ax.set_ylim(0, 100)
    rebuilt(ax, "s = pop_m**2: the value drives the RADIUS;\nWessant's mark is 4.9 in across")
    bub.draw(ax2, h, labels=False)
    bub.size_legend(ax2, h)
    ax2.set_xlabel("GDP per capita, USD (log)")
    ax2.set_ylabel("Healthcare access (0–100)")
    ax2.set_title(f"REDESIGN: area ∝ people, sizes={bub.SIZES} pt² (10× across, not 589×).\n"
                  f"Weakly related at most: r(log pop, access) = {r_log:+.2f}", fontsize=10,
                  loc="left")
    finish(fig, 1, "health_indicators.csv, 60 countries")


# ========================================================================= 2
def case2():
    head(2, "The outbreak is concentrated in the three districts around the capital")
    feats, d, audit = districts()
    print(f"join: {audit['features']} features, {audit['rows']} rows, unmatched "
          f"{len(audit['rows_unmatched'])}+{len(audit['features_unmatched'])}")
    assert d.cases.sum() == 30564 and d.population.sum() == 57_857_000
    tc = d.nlargest(3, "cases").code.tolist()
    tr = d.nlargest(3, "rate").code.tolist()
    assert tc == ["D17", "D13", "D09"]
    r_cp = np.corrcoef(d.cases, d.population)[0, 1]
    r_rp = np.corrcoef(d.rate, d.population)[0, 1]
    print(f"top 3 by count {tc}; by rate {tr}; overlap {len(set(tc) & set(tr))}")
    print(f"r(cases, population) {r_cp:+.3f}; r(rate, population) {r_rp:+.3f}")
    big = d[d.code.isin(tc)]
    print(f"count top-3 hold {big.population.min()/1e6:.1f}–{big.population.max()/1e6:.1f} M people "
          f"each, {big.population.sum()/d.population.sum()*100:.1f}% of all residents, "
          f"{big.cases.sum()/d.cases.sum()*100:.1f}% of cases; their rates "
          f"{', '.join(f'{v:.1f}' for v in big.rate)} vs national {pooled_rate(d.cases,d.population):.1f}")
    for s in ("equal", "quantile", "natural"):
        e = geolib.breaks(d.cases, s, 5)
        top_cls = d.code[geolib.class_of(d.cases, e) == 4].tolist()
        print(f"decoy 'it's the class scheme': {s:8s} top count class = {top_cls}")
    fig, ax, (ax2,) = new_fig(2, "The outbreak is concentrated in the three districts around "
                                 "the capital", h=6.2)
    geolib.choropleth(ax, feats, dict(zip(d.code, d.cases)), "natural", 5,
                      legend_title="Cases (count)", legend_anchor=(1.0, 1.0))
    rebuilt(ax, "cases (COUNT), Jenks 5 classes — a population map")
    geolib.choropleth(ax2, feats, dict(zip(d.code, d.rate)), "natural", 5,
                      legend_title="Cases per 100,000\nresidents", fmt="{:.1f}",
                      legend_anchor=(1.0, 1.0))
    ax2.set_title(f"REDESIGN: normalised by residents — the top three\nare {', '.join(tr)}; "
                  f"r(count, population) = {r_cp:+.3f}", fontsize=10, loc="left")
    lat_ts = float(np.mean([p[1] for f in feats for p in f["ring"]]))
    for a_, codes in ((ax, tc), (ax2, tr)):
        for f in feats:
            if f["code"] in codes:
                x, y = geolib.equal_area_xy(*geolib.representative_point(f["ring"]), lat_ts=lat_ts)
                a_.text(x, y, f["code"], ha="center", va="center", fontsize=8, color="white",
                        fontweight="bold")
    finish(fig, 2, "district_health.csv + districts.geojson; Lambert cylindrical equal-area")


# ========================================================================= 3
def case3():
    head(3, "GDP per capita barely varies across the sample")
    h = health()
    mm = geolib.scale_frame(h, NUM_COLS, "minmax")
    below = int((mm.gdp_pc < 0.10).sum())
    print(f"min–max gdp_pc: {below}/60 below 0.10, median {mm.gdp_pc.median():.3f}")
    assert below == 58 and round(mm.gdp_pc.median(), 3) == 0.017
    g = h.gdp_pc.sort_values()
    print(f"one value: Aldonia ${g.iloc[-1]:,} = {g.iloc[-1]/g.iloc[-2]:.1f}× the next (${g.iloc[-2]:,})")
    cv = h[NUM_COLS].std() / h[NUM_COLS].mean()
    print("decoy 'GDP genuinely varies little': coefficient of variation by column " +
          ", ".join(f"{c} {v:.2f}" for c, v in cv.items()) + " -> GDP varies MOST")
    print(f"without Aldonia GDP still spans ${g.iloc[0]:,}–${g.iloc[-2]:,} ({g.iloc[-2]/g.iloc[0]:.0f}×)")
    rk = geolib.scale_frame(h, NUM_COLS, "rank")
    print(f"rank scaling: gdp_pc median {rk.gdp_pc.median():.3f}, below 0.10: {(rk.gdp_pc<0.10).sum()}")
    fig, ax, (ax2,) = new_fig(3, "GDP per capita barely varies across the sample")
    geolib.pcp(ax, h, NUM_COLS, "minmax")
    rebuilt(ax, f"min–max scaled, file order: {below}/60 countries\nunder 0.10 on gdp_pc")
    geolib.pcp(ax2, h, NUM_COLS, "rank")
    ax2.set_title(f"REDESIGN (same chart, scaling decision changed): percentile\nrank — GDP spans "
                  f"{g.iloc[-2]/g.iloc[0]:.0f}× even without its one outlier", fontsize=10, loc="left")
    for a_ in (ax, ax2):
        a_.tick_params(axis="x", pad=12, length=0)
    finish(fig, 3, "health_indicators.csv, 60 countries; axis ends = real min/max")


# ========================================================================= 4
def case4():
    head(4, "Healthcare access and case rate are unrelated — no crossing pattern")
    h = health()
    pos = {c: NUM_COLS.index(c) for c in NUM_COLS}
    gap = abs(pos["healthcare_access"] - pos["cases_per_100k"])
    print(f"file order {NUM_COLS}; access and cases are {gap} axes apart")
    assert gap == 3
    r = h.healthcare_access.corr(h.cases_per_100k)
    print(f"r(healthcare_access, cases_per_100k) = {r:+.3f}; lines that would cross if adjacent: "
          f"{disc(h.healthcare_access, h.cases_per_100k)*100:.0f}%")
    for a, b in zip(NUM_COLS[:-1], NUM_COLS[1:]):
        print(f"   file-order gap {a} | {b}: r {h[a].corr(h[b]):+.3f}, crossing {disc(h[a], h[b])*100:.0f}%")
    order = corr_chain(h, NUM_COLS)
    print("greedy order:", " -> ".join(order))
    print("decoy 'n = 60 is too few to see a pattern': r = -0.80 with n = 60 has p = "
          f"{stats.pearsonr(h.healthcare_access, h.cases_per_100k)[1]:.1e}")
    fig, ax, (ax2,) = new_fig(4, "Healthcare access and case rate are unrelated — there is no "
                                 "crossing pattern between them")
    geolib.pcp(ax, h, NUM_COLS, "minmax")
    rebuilt(ax, "file order, min–max: access and cases are 3 axes apart\n(urban_pct, median_age between)")
    geolib.pcp(ax2, h, order, "minmax")
    ax2.set_title(f"REDESIGN (same chart, order decision changed): greedy\n|r| chain puts them "
                  f"side by side — an X, r = {r:+.2f}", fontsize=10, loc="left")
    for a_ in (ax, ax2):
        a_.tick_params(axis="x", pad=12, length=0)
    finish(fig, 4, "health_indicators.csv; both panels min–max so only the ORDER differs")


# ========================================================================= 5
def case5():
    head(5, "There is a clear five-level gradient in incidence")
    feats = geolib.read_geojson(D / "districts.geojson")
    c = pd.read_csv(D / "case05_flat_rates.csv")
    c["rate"] = c.cases / c.population * PER
    spread = (c.rate.max() - c.rate.min()) / c.rate.mean() * 100
    print(f"rates {c.rate.min():.2f}–{c.rate.max():.2f}, spread {spread:.1f}% of mean")
    assert round(c.rate.min(), 2) == 31.07 and round(c.rate.max(), 2) == 33.40 and round(spread, 1) == 7.2
    pr = pooled_rate(c.cases, c.population)
    exp = c.population * c.cases.sum() / c.population.sum()
    chi = float(((c.cases - exp) ** 2 / exp).sum())
    p = stats.chi2.sf(chi, len(c) - 1)
    hw = 1.96 * np.sqrt(c.cases) / c.population * PER
    print(f"pooled {pr:.2f}; chi-square homogeneity {chi:.2f} on {len(c)-1} df, p = {p:.3f} "
          f"(expected ≈ {len(c)-1} if only Poisson noise) -> LESS spread than noise alone")
    print(f"each rate's 95% CI is ±{hw.min():.1f} to ±{hw.max():.1f}; all {((c.rate-hw<=pr)&(c.rate+hw>=pr)).sum()}/24 "
          f"contain the pooled rate; total spread is {c.rate.max()-c.rate.min():.2f}")
    for s in ("quantile", "equal", "natural"):
        e = geolib.breaks(c.rate, s, 5)
        print(f"decoy 'just use another scheme': {s:8s} breaks {[round(float(x), 2) for x in e]} — still 5 "
              f"confident colours")
    fig, ax, (ax2,) = new_fig(5, "There is a clear five-level gradient in incidence across the "
                                 "federation", h=6.0)
    e = geolib.choropleth(ax, feats, dict(zip(c.code, c.rate)), "quantile", 5,
                          legend_title="Cases per 100,000\n(quantile, 5)", fmt="{:.2f}")
    rebuilt(ax, f"5 quantile classes painted over a {spread:.1f}% spread")
    s = c.sort_values("rate")
    y = np.arange(len(s))
    ax2.errorbar(s.rate, y, xerr=hw.loc[s.index], fmt="o", color=BLUE, ecolor=GREY, ms=4,
                 capsize=0, lw=1)
    ax2.axvline(pr, color=ORANGE, lw=1.2)
    ax2.text(pr, len(s) + 0.3, f" pooled {pr:.1f}", color=ORANGE, fontsize=8)
    ax2.set_yticks(y, s.code, fontsize=6.5)
    ax2.set_xlim(20, 45)
    ax2.set_xlabel("Cases per 100,000 residents, with 95% Poisson interval")
    ax2.set_title(f"REDESIGN: every interval contains the pooled rate;\nχ² = {chi:.1f} on 23 df "
                  f"(p = {p:.2f}) — no detectable gradient, so no map", fontsize=10, loc="left")
    finish(fig, 5, "case05_flat_rates.csv + districts.geojson")


# ========================================================================= 6
def case6():
    head(6, "Unit U32 is a hotspot at nearly five times the national rate")
    sa = pd.read_csv(D / "smallarea_cases.csv")
    sa["rate"] = sa.cases / sa.population * PER
    pr = pooled_rate(sa.cases, sa.population)
    u = sa[sa.unit == "U32"].iloc[0]
    big = sa[sa.population > 100_000]
    print(f"pooled {pr:.2f}; U32 {u.rate:.1f} = {u.rate/pr:.1f}× from {u.cases} cases in {u.population:,}")
    print(f"units > 100k: {len(big)}, rates {big.rate.min():.1f}–{big.rate.max():.1f}")
    assert round(pr, 2) == 8.72 and round(u.rate, 1) == 40.9 and len(big) == 10
    lam = pr / PER * u.population
    pval = stats.poisson.sf(u.cases - 1, lam)
    print(f"expected cases in U32 at the common rate: {lam:.2f}; P(≥{u.cases}) = {pval:.5f}; "
          f"chance that at least one of 40 units does this: {1-(1-pval)**40:.4f}")
    lo95, hi95 = (stats.chi2.ppf(.025, 2*u.cases)/2/u.population*PER,
                  stats.chi2.ppf(.975, 2*u.cases+2)/2/u.population*PER)
    print(f"U32 exact 95% CI {lo95:.1f}–{hi95:.1f} per 100k: the data cannot pin the rate to "
          f"within a factor of {hi95/lo95:.1f}")
    small = sa[sa.population < 25_000]
    print(f"units under 25,000 people: {len(small)}; their rates span {small.rate.min():.1f}–"
          f"{small.rate.max():.1f} (zero-case units: {(sa.cases==0).sum()})")
    print("decoy 'U32 really has an outbreak': the file states every unit has the SAME true rate; "
          "the funnel (Part B5) shows the extremes are all small units")
    fig, ax, (ax2,) = new_fig(6, "Unit U32 is a hotspot — it is running at nearly five times the "
                                 "national rate", h=6.2)
    s = sa.sort_values("rate")
    y = np.arange(len(s))
    ax.barh(y, s.rate, color=[ORANGE if u_ == "U32" else GREY for u_ in s.unit], height=0.7)
    ax.axvline(pr, color=INK, lw=1, ls="--")
    ax.text(pr + 0.5, 1, f"national {pr:.2f}", fontsize=8)
    ax.set_yticks(y, s.unit, fontsize=6)
    ax.set_xlabel("Cases per 100,000 residents")
    rebuilt(ax, "40 units ranked by rate; U32 = 40.9, 4.7× national")
    pop = np.linspace(sa.population.min() * 0.9, sa.population.max() * 1.05, 400)
    for z, ls, lab in ((1.96, "-", "95%"), (3.09, ":", "99.8%")):
        fl = geolib.funnel_limits(pop, pr, z=z)
        ax2.plot(fl.population, fl.hi, color=INK, lw=0.9, ls=ls, label=f"{lab} limits")
        ax2.plot(fl.population, fl.lo, color=INK, lw=0.9, ls=ls)
    ax2.axhline(pr, color=GREY, lw=1)
    ax2.scatter(sa.population, sa.rate, s=18, color=[ORANGE if u_ == "U32" else BLUE for u_ in sa.unit],
                zorder=3)
    ax2.annotate(f"U32: {u.cases} cases in {u.population:,}", (u.population, u.rate),
                 xytext=(u.population + 30000, u.rate - 2), fontsize=8)
    ax2.set_xscale("log")
    ax2.set_xlabel("Population of the unit (log)")
    ax2.set_ylabel("Cases per 100,000 residents")
    ax2.legend(fontsize=8, loc="upper right")
    ax2.set_title("REDESIGN: funnel plot — the extremes are all small units;\n"
                  "big units sit near the line because they have enough cases", fontsize=10, loc="left")
    finish(fig, 6, "smallarea_cases.csv, 40 units sharing one true rate")


# ========================================================================= 7
def zone_table(d):
    z = d.groupby("zone").agg(cases=("cases", "sum"), population=("population", "sum"),
                              income=("income_pc_usd", "mean"))
    z["rate"] = z.cases / z.population * PER
    z["income_popw"] = (d.assign(w=d.income_pc_usd * d.population).groupby("zone").w.sum()
                        / z.population)
    return z


def case7():
    head(7, "District income and case rate are only weakly related, r ≈ −0.31")
    _, d, _ = districts()
    r24 = np.corrcoef(d.income_pc_usd, d.rate)[0, 1]
    print(f"r across 24 districts {r24:+.3f}")
    assert round(r24, 3) == -0.308
    z = zone_table(d)
    r6 = np.corrcoef(z.income, z.rate)[0, 1]
    r6w = np.corrcoef(z.income_popw, z.rate)[0, 1]
    print(f"same data, 6 zones (districts_coarse members): r {r6:+.3f} (mean district income), "
          f"{r6w:+.3f} (population-weighted income)")
    wz = d.groupby("zone").apply(lambda x: np.corrcoef(x.income_pc_usd, x.rate)[0, 1],
                                 include_groups=False)
    print("within-zone r (4 districts each): " + ", ".join(f"{k} {v:+.2f}" for k, v in wz.items()))
    print(f"p-values: districts {stats.pearsonr(d.income_pc_usd, d.rate)[1]:.3f} (n=24), zones "
          f"{stats.pearsonr(z.income, z.rate)[1]:.3f} (n=6)")
    print("decoy 'n = 24 is too small for r': the problem is not n — the SAME people give "
          "r from -0.31 to -0.89 depending only on where the lines are drawn (MAUP, scale effect)")
    fig, ax, (r1, r2) = new_fig(7, "District income and case rate are only weakly related — r is "
                                   "about −0.31", right_cols=2,
                                headline="REDESIGN: report the coefficient WITH its unit — the same "
                                         "data at both scales,\nand say which unit the decision is "
                                         "made at (MAUP scale effect)")
    for a_ in (ax, r1):
        a_.scatter(d.income_pc_usd, d.rate, s=24, color=GREY if a_ is ax else BLUE)
        a_.set_xlabel("Income per head, USD (district)")
        a_.set_ylabel("Cases per 100,000")
        a_.set_ylim(0, 85)
    rebuilt(ax, f"24 districts: r = {r24:+.3f}")
    r1.set_title(f"24 districts\nr = {r24:+.2f}", fontsize=9.5)
    r2.scatter(z.income, z.rate, s=50, color=ORANGE)
    for k, row in z.iterrows():
        r2.annotate(k, (row.income, row.rate), xytext=(4, 3), textcoords="offset points", fontsize=7.5)
    r2.set_ylim(0, 85)
    r2.set_xlabel("Mean district income, USD (zone)")
    r2.set_title(f"6 zones, same data\nr = {r6:+.2f} ({r6w:+.2f} if pop-weighted)", fontsize=9.5)
    finish(fig, 7, "district_health.csv; zones = districts_coarse.geojson `members`")


# ========================================================================= 8
def case8():
    head(8, "This is a rural outbreak — look how much of the map is dark")
    feats, d, _ = districts()
    t5 = d.nlargest(5, "population")
    a5 = t5.area_km2.sum() / d.area_km2.sum() * 100
    p5 = t5.population.sum() / d.population.sum() * 100
    print(f"five most populous districts: {a5:.1f}% of land, {p5:.1f}% of people")
    assert round(a5, 1) == 12.6 and round(p5, 1) == 59.9
    e = geolib.breaks(d.rate, "natural", 5)
    cls = geolib.class_of(d.rate, e)
    top = cls >= 3
    print(f"top two classes (rate > {e[3]:.1f}): {top.sum()} districts, "
          f"{d.area_km2[top].sum()/d.area_km2.sum()*100:.1f}% of land, "
          f"{d.population[top].sum()/d.population.sum()*100:.1f}% of people, "
          f"{d.cases[top].sum()/d.cases.sum()*100:.1f}% of cases")
    d["dens"] = d.population / d.area_km2
    print(f"density {d.dens.min():.0f}–{d.dens.max():.0f} people/km²; r(rate, density) "
          f"{np.corrcoef(d.rate, d.dens)[0,1]:+.3f}, r(rate, log density) "
          f"{np.corrcoef(d.rate, np.log(d.dens))[0,1]:+.3f} -> no rural/urban gradient in the RATE")
    print("decoy 'the projection inflates the north': the map is Lambert equal-area (area error "
          "< 1e-10 %); even Mercator would only inflate north vs south by 1.21× (Part B4) — the "
          "issue is km² vs people, not the projection")
    by = pd.DataFrame({"cls": cls, "land": d.area_km2, "people": d.population}).groupby("cls").sum()
    by = by / by.sum() * 100
    print("share by rate class (land % / people %): " +
          "; ".join(f"class {k+1} {r.land:.1f}/{r.people:.1f}" for k, r in by.iterrows()))
    fig, ax, (r1, r2) = new_fig(8, "This is a rural outbreak — look how much of the map is dark",
                                h=6.0, right_cols=2,
                                headline="REDESIGN: count people, not km² — and the rate has no "
                                         f"link to density (r = {np.corrcoef(d.rate, d.dens)[0,1]:+.2f})")
    geolib.choropleth(ax, feats, dict(zip(d.code, d.rate)), "natural", 5,
                      legend_title="Cases per 100,000", fmt="{:.1f}")
    rebuilt(ax, "rate, Jenks 5 — large, empty districts own the ink")
    cm = plt.get_cmap(PALETTE["sequential"])
    shades = [cm(0.18 + 0.78 * c / 4) for c in range(5)]
    s = d.assign(cls=cls).sort_values("rate")
    yy = np.arange(len(s))
    r1.barh(yy, s.rate, color=[shades[c] for c in s.cls], edgecolor=PALETTE["ink_soft"], lw=0.3)
    r1.set_yticks(yy, [f"{c} · {p/1e6:.1f}M" for c, p in zip(s.code, s.population)], fontsize=6)
    r1.set_xlabel("Cases per 100,000 (sorted)")
    r1.set_title("Rate by district,\nwith its population", fontsize=9.5)
    x = np.arange(5)
    r2.bar(x - 0.2, by.land, width=0.4, color=GREY, label="% of land")
    r2.bar(x + 0.2, by.people, width=0.4, color=BLUE, label="% of people")
    r2.set_xticks(x, [f"{e[k]:.0f}–\n{e[k+1]:.0f}" for k in range(5)], fontsize=7)
    r2.set_xlabel("Rate class (per 100,000)")
    r2.set_ylabel("% of federation")
    r2.legend(fontsize=7.5)
    r2.set_title(f"Top 5 districts by population:\n{a5:.1f}% of land, {p5:.1f}% of people",
                 fontsize=9.5)
    finish(fig, 8, "district_health.csv + districts.geojson, equal-area")


# ========================================================================= 9
def radar_area(v):
    v = np.asarray(v, float)
    return 0.5 * np.sin(2 * np.pi / len(v)) * float(np.sum(v * np.roll(v, -1)))


def case9():
    head(9, "Region A is the stronger of the two — its profile encloses visibly more area")
    rp = pd.read_csv(D / "region_profiles.csv")
    ma, mb = rp.region_a.mean(), rp.region_b.mean()
    aa, ab = radar_area(rp.region_a), radar_area(rp.region_b)
    print(f"means A {ma:.1f}, B {mb:.1f} (diff {ma-mb:.2f}); file-order areas A {aa:,.0f}, B {ab:,.0f}")
    assert round(ma, 1) == 62.3 and round(mb, 1) == 62.0 and round(aa) == 9933 and round(ab) == 9433
    diffs = []
    for perm in itertools.permutations(range(1, 6)):
        o = [0, *perm]
        diffs.append(radar_area(rp.region_a.values[o]) - radar_area(rp.region_b.values[o]))
    diffs = np.array(diffs)   # 120 = first axis fixed; each cycle appears twice (mirror image)
    nb = int((diffs < 0).sum()) // 2
    print(f"axis orders: 120 with the first axis fixed = 60 distinct (a mirror image encloses the "
          f"same area). A − B area ranges {diffs.min():+,.0f} to {diffs.max():+,.0f}; B encloses "
          f"MORE in {nb} of 60 distinct orders")
    print("indicator differences A − B: " + ", ".join(
        f"{r.indicator} {r.region_a-r.region_b:+.1f}" for r in rp.itertuples()))
    print("decoy 'the axes have different scales': all six are 0–100 (same scale) — the area "
          "depends on which values sit NEXT to each other, i.e. on the order")
    fig, ax, (ax2,) = new_fig(9, "Region A is the stronger of the two — its profile encloses "
                                 "visibly more area", polar_left=True, h=5.4)
    ang = np.linspace(0, 2 * np.pi, len(rp), endpoint=False)
    for col, c, lab in (("region_a", BLUE, "Region A"), ("region_b", ORANGE, "Region B")):
        v = np.r_[rp[col].values, rp[col].values[0]]
        ax.plot(np.r_[ang, ang[0]], v, color=c, lw=1.6, label=lab)
        ax.fill(np.r_[ang, ang[0]], v, color=c, alpha=0.18)
    ax.set_xticks(ang, rp.indicator, fontsize=8)
    ax.set_ylim(0, 100)
    ax.legend(loc="lower left", bbox_to_anchor=(-0.15, -0.12), fontsize=8)
    ax.set_title(f"REBUILT AS PUBLISHED\nradar, file order: areas A {aa:,.0f} vs B {ab:,.0f}",
                 fontsize=10, color=PALETTE["ink_soft"], pad=18)
    s = rp.assign(diff=rp.region_a - rp.region_b).sort_values("diff")
    y = np.arange(len(s))
    ax2.hlines(y, s[["region_a", "region_b"]].min(axis=1), s[["region_a", "region_b"]].max(axis=1),
               color=GREY, lw=2)
    ax2.scatter(s.region_a, y, color=BLUE, s=45, label="Region A", zorder=3)
    ax2.scatter(s.region_b, y, color=ORANGE, s=45, marker="s", label="Region B", zorder=3)
    for yi, r in zip(y, s.itertuples()):
        ax2.text(101, yi, f"{r.diff:+.1f}", va="center", fontsize=8)
    ax2.set_yticks(y, s.indicator)
    ax2.set_xlim(0, 108)
    ax2.set_xlabel("Rating (0–100, same scale on every indicator)")
    ax2.legend(fontsize=8, loc="lower left")
    ax2.set_title(f"REDESIGN: dot plot on one position axis — means {ma:.1f} vs {mb:.1f}.\n"
                  f"Neither is 'stronger': B leads on 3 of 6; radar area favours B in {nb} of 60 orders",
                  fontsize=10, loc="left")
    finish(fig, 9, "region_profiles.csv, six 0–100 ratings")


if __name__ == "__main__":
    style_defaults()
    for fn in (case1, case2, case3, case4, case5, case6, case7, case8, case9):
        fn()
    print("\nall nine self-checks passed")
