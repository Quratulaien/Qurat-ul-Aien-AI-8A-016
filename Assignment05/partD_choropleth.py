"""
Part D3 — the normalized choropleth, with the count put back beside it
(CDB601220, Week 5). Slide 50's six steps, each printed as it is done.

    python3 partD_choropleth.py   -> partD_choropleth.png (300 dpi) + printed log
Synthetic course data — a fictional federation.
"""
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Polygon as MplPolygon, Patch
import numpy as np

import geolib
from geolib import PALETTE, style_defaults, save_fig
from w5common import BOUNDARIES, HERE, PER, SYNTH, districts, pooled_rate

SCHEME, K = "natural", 5            # Jenks, exact (geolib.breaks)
SUPPRESS_BELOW = 20                 # cases; a district under this would be merged/suppressed
LEGEND_TITLE = "Cases per 100,000 residents\n(this period; Jenks, 5 classes)"


def main():
    style_defaults()
    # 1-2 · read + JOIN, counting failures
    feats, d, audit = districts()
    print(f"[join] features {audit['features']}, table rows {audit['rows']}, "
          f"rows unmatched {len(audit['rows_unmatched'])}, features unmatched "
          f"{len(audit['features_unmatched'])}, duplicate codes {audit['dup_codes_table']}")
    assert not audit["rows_unmatched"] and not audit["features_unmatched"]
    # 1 · PROJECT: geolib's Lambert cylindrical equal-area, one lat_ts for all
    lat_ts = float(np.mean([p[1] for f in feats for p in f["ring"]]))
    print(f"[project] Lambert cylindrical equal-area, true scale at {lat_ts:.2f}°N (collection mean)")
    # 3 · NORMALIZE
    pr = pooled_rate(d.cases, d.population)
    print(f"[normalize] {d.cases.sum():,} cases / {d.population.sum():,} residents = "
          f"{pr:.1f} per 100,000 (pooled)")
    r_cp = np.corrcoef(d.cases, d.population)[0, 1]
    r_rp = np.corrcoef(d.rate, d.population)[0, 1]
    print(f"           r(cases, population) {r_cp:+.3f}  ->  r(rate, population) {r_rp:+.3f}")
    # stability / suppression
    half = 1.96 / np.sqrt(d.cases) * 100
    print(f"[suppress] rule: merge or suppress any district under {SUPPRESS_BELOW} cases; smallest "
          f"count {d.cases.min()} -> none suppressed (widest 95% CI ±{half.max():.0f}% of the rate)")
    # 4 · CLASSIFY
    scores = {s: geolib.gvf(d.rate, geolib.breaks(d.rate, s, K))
              for s in ("equal", "quantile", "natural")}
    edges = geolib.breaks(d.rate, SCHEME, K)
    cls = geolib.class_of(d.rate, edges)
    print(f"[classify] {SCHEME} k={K}; edges {[round(e, 1) for e in edges]}; per class "
          f"{np.bincount(cls, minlength=K).tolist()}; GVF " +
          ", ".join(f"{k} {v:.3f}" for k, v in scores.items()))
    top_rate = d.nlargest(3, "rate").code.tolist()
    top_count = d.nlargest(3, "cases").code.tolist()
    print(f"top 3 by rate {top_rate}; by count {top_count}; overlap "
          f"{len(set(top_rate) & set(top_count))}")
    assert top_rate == ["D19", "D20", "D21"] and top_count == ["D17", "D13", "D09"]

    # ------------------------------------------------------------------ draw
    fig = plt.figure(figsize=(14, 7.6))
    gs = fig.add_gridspec(1, 2, width_ratios=[1.25, 1], wspace=0.55)
    ax = fig.add_subplot(gs[0, 0])
    axb = fig.add_subplot(gs[0, 1])
    # 5 · COLOUR: one sequential hue, dark = more (geolib default 'Blues')
    geolib.choropleth(ax, feats, dict(zip(d.code, d.rate)), SCHEME, K,
                      legend_title=LEGEND_TITLE, fmt="{:.1f}",
                      legend_loc="upper left", legend_anchor=(1.03, 1.0))
    leg = ax.get_legend()
    for t, c in zip(leg.get_texts(), np.bincount(cls, minlength=K)):
        t.set_text(f"{t.get_text()}   ({c} districts)")
    # codes on the map; top-3-by-count outlined
    cm = plt.get_cmap(PALETTE["sequential"])
    shades = [cm(0.18 + 0.78 * c / (K - 1)) for c in range(K)]
    by = d.set_index("code")
    for f in feats:
        x, y = geolib.equal_area_xy(*geolib.representative_point(f["ring"]), lat_ts=lat_ts)
        c = int(cls[d.index[d.code == f["code"]][0]])
        ax.text(x, y, f"{f['code']}\n{by.loc[f['code'], 'rate']:.0f}", ha="center",
                va="center", fontsize=6.6, color="white" if c >= 3 else PALETTE["ink"])
        if f["code"] in top_count:
            xs, ys = geolib.equal_area_xy([p[0] for p in f["ring"]], [p[1] for p in f["ring"]],
                                          lat_ts=lat_ts)
            ax.add_patch(MplPolygon(np.column_stack([xs, ys]), closed=True, fill=False,
                                    edgecolor=PALETTE["highlight"], lw=2.0, ls="--", zorder=6))
    ax.legend_.set_visible(True)
    from matplotlib.lines import Line2D
    ax.add_artist(leg)
    ax.legend(handles=[Line2D([], [], color=PALETTE["highlight"], lw=2, ls="--",
                              label="Top 3 by raw COUNT\n(D17, D13, D09) — none is\nin the top rate class")],
              loc="upper left", bbox_to_anchor=(1.03, 0.62), frameon=False, fontsize=7.5)
    ax.set_title(f"RATE: the highest risk is in the north — D19, D20, D21 ({d.nlargest(3,'rate').rate.min():.0f}–"
                 f"{d.rate.max():.0f} per 100k),\nnot in the big-city districts that top the case "
                 f"count", fontsize=11, loc="left")

    # count put back: sorted bars, coloured by the district's RATE class
    s = d.sort_values("cases")
    yy = np.arange(len(s))
    axb.barh(yy, s.cases, color=[shades[int(cls[i])] for i in s.index],
             edgecolor=PALETTE["ink_soft"], linewidth=0.3, height=0.72)
    for y_, r in zip(yy, s.itertuples()):
        axb.text(r.cases + 70, y_, f"{r.cases:,}  ({r.population/1e6:.1f} M people)",
                 va="center", fontsize=6.8, color=PALETTE["ink"])
    axb.set_yticks(yy, [f"{c} {n}" for c, n in zip(s.code, s.district)], fontsize=7)
    axb.set_xlim(0, s.cases.max() * 1.45)
    axb.set_xlabel("Confirmed cases this period (count, from zero)")
    axb.grid(axis="y", visible=False)
    axb.tick_params(axis="y", length=0)
    axb.set_title(f"COUNT: cases follow people (r = {r_cp:+.3f} with population).\nBar colour = "
                  f"the district's rate class on the map", fontsize=11, loc="left")

    fig.suptitle(f"Outbreak risk by district: national rate {pr:.1f} per 100,000; the rate map and "
                 f"the count ranking share none of their top three", x=0.01, ha="left",
                 fontsize=13.5, fontweight="bold", y=1.0)
    note = (f"Source: {SYNTH} — district_health.csv (cases this period, resident population), course release "
            f"dated 24 Oct 2026 (repository commit), downloaded 28 Oct 2026. {BOUNDARIES}; joined on "
            f"`code`: 24/24 matched, 0 failed.\n"
            f"Map: Lambert cylindrical equal-area projection, true scale {lat_ts:.1f}°N (area is the "
            f"encoding channel). Rate = cases ÷ residents × 100,000. Classes: Jenks natural breaks, 5 "
            f"classes, GVF {scores['natural']:.3f} (quantile {scores['quantile']:.3f}); breaks "
            f"{', '.join(f'{e:.1f}' for e in edges)}.\n"
            f"Suppression rule: districts under {SUPPRESS_BELOW} cases would be merged with a neighbour; "
            f"none qualified (smallest count {d.cases.min()}). Numbers on the map: code and rate.")
    out = save_fig(fig, HERE / "partD_choropleth.png", note=note)
    plt.close(fig)
    print("saved", out)


if __name__ == "__main__":
    main()
