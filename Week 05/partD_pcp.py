"""
Part D2 — the parallel coordinates plot (CDB601220, Week 5).

    python3 partD_pcp.py   -> partD_pcp.png (300 dpi) + printed checks

Three decisions, fixed before drawing and printed on the figure:
  1. SCALING   percentile rank, because one gdp_pc value is 9.2× the next and
               min–max would crush 58 of 60 countries under 0.10 (Part A case 3,
               Part B3). Rank keeps every country's ORDER on each axis, which is
               what crossings between adjacent axes are read from.
  2. ORDER     slide 24's greedy chain by |r| (corr_chain), computed, not eyeballed.
  3. CLUTTER   everything grey, one region (Borealis — highest mean case rate)
               brushed in colour, drawn on top.
Synthetic course data.
"""
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

import geolib
from geolib import PALETTE, style_defaults, save_fig
from w5common import HERE, NUM_COLS, SYNTH, corr_chain, health

SCALING = "rank"
BRUSH = "Borealis"
NICE = {"gdp_pc": "GDP per capita\n(USD)", "healthcare_access": "Healthcare\naccess (0–100)",
        "urban_pct": "Urban\npopulation (%)", "median_age": "Median age\n(years)",
        "cases_per_100k": "Cases per\n100,000"}


def discordant_share(a, b):
    """Share of country pairs whose order flips between two axes = the share
    of line pairs that CROSS in the gap. ~1 is an X (negative), ~0 parallel."""
    a, b = np.asarray(a), np.asarray(b)
    i, j = np.triu_indices(len(a), 1)
    return float(((a[i] - a[j]) * (b[i] - b[j]) < 0).mean())


def main():
    style_defaults()
    h = health()
    order = corr_chain(h, NUM_COLS)
    r = h[NUM_COLS].corr()
    rho = h[NUM_COLS].corr(method="spearman")
    print("axis order (greedy |r| chain):", " -> ".join(order))
    assert order == ["healthcare_access", "cases_per_100k", "urban_pct", "median_age", "gdp_pc"]
    print(f"r(healthcare_access, cases_per_100k) = {r.loc['healthcare_access','cases_per_100k']:+.3f}")
    S = geolib.scale_frame(h, NUM_COLS, SCALING)
    gaps = []
    for a, b in zip(order[:-1], order[1:]):
        d = discordant_share(h[a], h[b])
        gaps.append((a, b, r.loc[a, b], rho.loc[a, b], d))
        print(f"  {a:18s} | {b:16s} r {r.loc[a,b]:+.3f}  rho {rho.loc[a,b]:+.3f}  "
              f"lines crossing in this gap {d*100:4.1f}%")
    br = h[h.region == BRUSH]
    print(f"brushed: {BRUSH}, n = {len(br)}; mean access {br.healthcare_access.mean():.1f} vs "
          f"{h.healthcare_access.mean():.1f}, mean cases {br.cases_per_100k.mean():.1f} vs "
          f"{h.cases_per_100k.mean():.1f}")

    fig, ax = plt.subplots(figsize=(11, 6))
    geolib.pcp(ax, h, order, how=SCALING, highlight=(h.region == BRUSH).to_numpy(),
               hl_color=PALETTE["series"][1], lw_hl=1.9, alpha_bg=0.5)
    ax.set_xticklabels([NICE[c] for c in order], fontsize=9)
    ax.tick_params(axis="x", pad=16, length=0)
    # what each gap shows, printed in the gap
    for k, (a, b, rv, rh, d) in enumerate(gaps):
        ax.text(k + 0.5, 1.13, f"r = {rv:+.2f} · ρ = {rh:+.2f}\n{d*100:.0f}% of lines cross",
                ha="center", va="bottom", fontsize=7.5, color=PALETTE["ink_soft"])
    ax.text(0.5, -0.24, "X-shaped waist:\nmore access, fewer cases", ha="center",
            fontsize=8.5, color=PALETTE["ink"], fontweight="bold", transform=ax.transData)
    ax.text(3.5, -0.24, f"near-parallel: older ↔ richer\n(ρ = {gaps[3][3]:+.2f}; Pearson r = "
            f"{gaps[3][2]:+.2f} hidden by one outlier)", ha="center", fontsize=8.5,
            color=PALETTE["ink"], fontweight="bold", transform=ax.transData)
    ax.set_ylim(-0.32, 1.32)
    for sp in ("bottom",):
        ax.spines[sp].set_visible(False)
    ax.grid(False)
    ax.set_title(f"Where healthcare access is high, case rates are low: the lines cross in an X "
                 f"(r = {gaps[0][2]:+.2f}).\n{BRUSH} (orange) sits low on access and high on cases; "
                 f"older countries are richer almost in rank order",
                 fontsize=12)
    decl = (f"DECLARED BEFORE DRAWING · scaling: percentile rank on every axis (min–max would "
            f"crush 58/60 countries under 0.10 on GDP) · axis order: greedy chain by |r| "
            f"(slide 24), computed · clutter: all 60 grey, {BRUSH} brushed.\n"
            "Axis ends show the real minimum and maximum of each variable; position between "
            "them is rank, not distance.")
    fig.text(0.01, 0.005, decl, fontsize=7.8, color=PALETTE["ink"], va="bottom")
    note = (f"Source: {SYNTH} (health_indicators.csv, n = 60 countries; cases_per_100k is already "
            "a rate). No rows removed.")
    fig.subplots_adjust(bottom=0.16)
    out = save_fig(fig, HERE / "partD_pcp.png", note=note)
    plt.close(fig)
    print("saved", out)


if __name__ == "__main__":
    main()
