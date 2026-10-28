"""
Part D1 — the four-variable bubble chart (CDB601220, Week 5).

    python3 partD_bubble.py      -> partD_bubble.png (300 dpi) + printed checks

Channel budget (slide 8), spent in the order the reader must compare:
    x  position  gdp_pc, log scale       (multiplicative spread, $283–$120,219)
    y  position  healthcare_access 0–100 (bounded index, real axis limits)
    area         pop_m                   (AREA, not radius: s is points², so
                                          diameter goes as sqrt)
    hue          region (6, identity)    + region letter A–F on every mark as a
                                          second channel (worst deutan pair ΔE 7.5)
Synthetic course data — not real countries.
"""
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

import vizlib
from geolib import PALETTE, style_defaults, save_fig
from w5common import HERE, SYNTH, health

# ------------------------------------------------------------ declared params
SIZES = (16, 1600)        # points² for the smallest / largest population (Part B1)
REGION_COLOURS = {        # Okabe–Ito, identity only
    "Andara": "#0072B2", "Borealis": "#D55E00", "Caldera": "#009E73",
    "Dravira": "#CC79A7", "Esperia": "#E69F00", "Fenwick": "#56B4E9",
}
LABEL = ["Aldonia", "Wessant", "Vornath", "Tarrowin"]   # the four the title talks about


def size_area(v, vmin, vmax, sizes=SIZES):
    """Value -> marker AREA in points² (linear in area, like seaborn's
    `sizes=(lo, hi)`). Diameter is sqrt(area), so it is NOT linear in value."""
    lo, hi = sizes
    return lo + (hi - lo) * (np.asarray(v, float) - vmin) / (vmax - vmin)


def draw(ax, h, sizes=SIZES, labels=True):
    vmin, vmax = h.pop_m.min(), h.pop_m.max()
    s = size_area(h.pop_m.to_numpy(), vmin, vmax, sizes)
    order = np.argsort(-s)               # big first, small on top
    hs = h.iloc[order]
    ax.scatter(hs.gdp_pc, hs.healthcare_access, s=s[order],
               c=[REGION_COLOURS[r] for r in hs.region], alpha=0.72,
               edgecolor="white", linewidth=0.7, zorder=3)
    for r in hs.itertuples():
        ax.text(r.gdp_pc, r.healthcare_access, r.region[0], ha="center", va="center",
                fontsize=5.2, color=PALETTE["ink"], zorder=4, fontweight="bold")
    ax.set_xscale("log")
    ax.set_xlim(180, 200_000)
    ax.set_ylim(0, 100)
    if labels:
        for name in LABEL:
            r = h[h.country == name].iloc[0]
            pos = {"Aldonia": (0.84, 6, "right"), "Wessant": (1.9, 6, "left"),
                   "Vornath": (1.9, 6, "left"), "Tarrowin": (1.0, -14, "center")}
            dx, dy, ha = pos[name]
            ax.annotate(f"{name}\n{r.pop_m:,.1f} M people", (r.gdp_pc, r.healthcare_access),
                        xytext=(r.gdp_pc * dx, r.healthcare_access + dy),
                        ha=ha, fontsize=7.5, color=PALETTE["ink"],
                        arrowprops=dict(arrowstyle="-", lw=0.6, color=PALETTE["ink_soft"]))
    return s


def size_legend(ax, h, sizes=SIZES):
    """Three reference circles with REAL populations, drawn with the same
    size_area() as the marks, so area converts back into people."""
    vmin, vmax = h.pop_m.min(), h.pop_m.max()
    refs = [1, 50, 350]
    handles = [ax.scatter([], [], s=size_area(v, vmin, vmax, sizes), color=PALETTE["muted"],
                          alpha=0.6, edgecolor="white", label=f"{v:,} M")
               for v in refs]
    return ax.legend(handles=handles, title="Population\n(area ∝ people)", loc="upper left",
                     bbox_to_anchor=(1.01, 1.0), labelspacing=2.2, borderpad=1.2,
                     frameon=False, fontsize=8, title_fontsize=8, handletextpad=1.6)


def main():
    style_defaults()
    h = health()
    n = len(h)
    vmin, vmax = h.pop_m.min(), h.pop_m.max()
    s = size_area(h.pop_m.to_numpy(), vmin, vmax)
    r_log = np.corrcoef(np.log10(h.gdp_pc), h.healthcare_access)[0, 1]
    w_acc = np.average(h.healthcare_access, weights=h.pop_m)
    top2 = h.gdp_pc.nlargest(2)
    print(f"D1 rows {n}, regions {h.region.nunique()}; pop {vmin}–{vmax} M (×{vmax/vmin:.0f})")
    print(f"sizes={SIZES} pt² -> area ratio {s.max()/s.min():.0f}×, diameter ratio "
          f"{np.sqrt(s.max()/s.min()):.1f}× (radius-encoding the same range would be ×{vmax/vmin:.0f})")
    print(f"gdp outlier: {h.loc[h.gdp_pc.idxmax(), 'country']} ${top2.iloc[0]:,} = "
          f"{top2.iloc[0]/top2.iloc[1]:.1f}× next; on log10 x it sits "
          f"{np.log10(top2.iloc[0]/top2.iloc[1]):.2f} decades right -> KEPT, labelled")
    print(f"r(log10 gdp, access) = {r_log:.3f}; access mean per country {h.healthcare_access.mean():.1f}, "
          f"population-weighted {w_acc:.1f}")
    for k in ("deutan", "protan", "tritan"):
        i, j, a, b, d = vizlib.worst_pair(list(REGION_COLOURS.values()), k)
        print(f"palette worst {k} pair {a}/{b} ΔE {d:.1f} ({vizlib.verdict(d)})")
    print("second channel: region letter A–F printed on every mark")

    fig, ax = plt.subplots(figsize=(10, 6.4))
    draw(ax, h)
    ax.set_xlabel("GDP per capita, USD per person per year (log scale)")
    ax.set_ylabel("Healthcare access index (0–100, higher is better)")
    ax.set_xticks([300, 1000, 3000, 10000, 30000, 100000],
                  ["$300", "$1k", "$3k", "$10k", "$30k", "$100k"])
    ax.set_title(f"Healthcare access rises with income (r = {r_log:.2f} against log GDP), and most "
                 f"people live\nabove the per-country average: population-weighted access "
                 f"{w_acc:.1f} vs {h.healthcare_access.mean():.1f} per country", fontsize=11.5)
    leg1 = size_legend(ax, h)
    ax.add_artist(leg1)
    from matplotlib.lines import Line2D
    handles = [Line2D([], [], marker="o", ls="", ms=9, color=c, alpha=0.8,
                      label=f"{r[0]} · {r}") for r, c in REGION_COLOURS.items()]
    ax.legend(handles=handles, title="Region (hue + letter)", loc="upper left",
              bbox_to_anchor=(1.01, 0.48), frameon=False, fontsize=8, title_fontsize=8)
    note = (f"Source: {SYNTH} (health_indicators.csv, n = {n} countries, 6 regions). "
            f"x: GDP per capita on log10 axis. Area ∝ population: sizes = {SIZES} pt², linear in AREA "
            f"(diameter ratio {np.sqrt(s.max()/s.min()):.0f}×, not {vmax/vmin:.0f}×).\n"
            f"Outlier: Aldonia's GDP per capita (${top2.iloc[0]:,}) is {top2.iloc[0]/top2.iloc[1]:.1f}× the next — "
            f"kept and labelled; the log axis holds it without compressing the other 59. "
            f"No countries removed. Letters A–F repeat the region hue for colour-blind readers.")
    out = save_fig(fig, HERE / "partD_bubble.png", note=note)
    plt.close(fig)
    print("saved", out)


if __name__ == "__main__":
    main()
