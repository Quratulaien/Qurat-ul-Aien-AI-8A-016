"""
Part B — the five channel and spatial decisions, computed (CDB601220, Week 5).

    python3 partB_decisions.py  -> printed answers (partB_output.txt)
                                   + partB_overplotting.png, partB_funnel.png (300 dpi)
Every answer below is a number this script prints. Synthetic course data.
"""
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from scipy import stats
from sklearn.decomposition import PCA

import geolib
from geolib import PALETTE, style_defaults, save_fig
from w5common import D, HERE, NUM_COLS, PER, SYNTH, districts, health, pooled_rate
import partD_bubble as bub

style_defaults()
BLUE, ORANGE = PALETTE["series"][0], PALETTE["series"][1]


def hdr(t):
    print("\n" + "=" * 78 + f"\n{t}\n" + "=" * 78)


# ======================================================================= B1
hdr("B1 · The size range for D1")
h = health()
vmin, vmax = h.pop_m.min(), h.pop_m.max()
print(f"pop_m {vmin}–{vmax} M (×{vmax/vmin:.0f}). matplotlib's s is AREA in points²; diameter = √s.")


def hidden_and_cover(sizes):
    """Render D1 with these sizes; count marks whose CENTRE lies inside a
    bigger mark (hidden), and the share of the plot the biggest mark covers."""
    fig, ax = plt.subplots(figsize=(10, 6.4))
    s = bub.draw(ax, h, sizes=sizes, labels=False)
    fig.canvas.draw()
    xy = ax.transData.transform(np.column_stack([h.gdp_pc, h.healthcare_access]))
    rad = np.sqrt(s) / 2 * fig.dpi / 72                # radius in pixels
    hidden = 0
    for i in range(len(h)):
        dist = np.hypot(*(xy - xy[i]).T)
        if np.any((dist < rad) & (rad > rad[i]) & (np.arange(len(h)) != i)):
            hidden += 1
    bb = ax.get_window_extent()
    cover = np.pi * rad.max() ** 2 / (bb.width * bb.height) * 100
    plt.close(fig)
    return hidden, cover


rows = []
for lo, hi in [(2, 1600), (6, 1600), (16, 1600), (36, 1600), (16, 400), (16, 900),
               (16, 2500), (16, 4900)]:
    hid, cov = hidden_and_cover((lo, hi))
    rows.append({"lo_pt2": lo, "hi_pt2": hi, "smallest_diam_pt": round(np.sqrt(lo), 1),
                 "largest_diam_pt": round(np.sqrt(hi), 1), "diam_ratio": round(np.sqrt(hi / lo), 1),
                 "centres_hidden": hid, "largest_covers_plot_%": round(cov, 1)})
print(pd.DataFrame(rows).to_string(index=False))
lo, hi = bub.SIZES
print(f"""CHOSEN sizes=({lo}, {hi}) pt²:
  low end  {lo} pt² = {np.sqrt(lo):.0f} pt ≈ {np.sqrt(lo)/72*25.4:.1f} mm across: the smallest mark that still
           reads as a filled disc carrying its region letter; 2–6 pt² (1.4–2.4 pt) shrink to a speck.
  high end {hi} pt² = {np.sqrt(hi):.0f} pt across: covers {[r for r in rows if r['lo_pt2']==lo and r['hi_pt2']==hi][0]['largest_covers_plot_%']}% of the plot; at 4900 pt² the biggest
           mark hides more centres (see table) — the knee of the trade-off.
  implied DIAMETER ratio √({hi}/{lo}) = {np.sqrt(hi/lo):.0f}× (area ratio {hi/lo:.0f}×). A radius encoding of
           the same 589× range would be 589× across.""")
s_ref = bub.size_area(np.array([1, 50, 350]), vmin, vmax)
print("proof it is AREA: s − lo is proportional to (value − min): " + ", ".join(
    f"{v} M -> s {sv:.0f} pt²" for v, sv in zip([1, 50, 350], s_ref)) +
      f"; (s(350)−lo)/(s(50)−lo) = {(s_ref[2]-lo)/(s_ref[1]-lo):.2f} = (350−{vmin})/(50−{vmin}) = "
      f"{(350-vmin)/(50-vmin):.2f}")
print("note: linear-in-area with a floor (seaborn's sizes=(lo, hi) rule) keeps tiny countries "
      "visible; a strictly proportional s = k·pop would make the 0.6 M country "
      f"{np.sqrt(hi*vmin/vmax):.1f} pt across. The size legend uses the same function, so "
      "readers convert area back to people.")

# ======================================================================= B2
hdr("B2 · Overplotting — scatter_dense.csv")
sd = pd.read_csv(D / "scatter_dense.csv")
CX, CY, R = 3.1, 3.0, 0.3
ALPHA, GRIDSIZE = 0.04, 60
inner = np.hypot(sd.x - CX, sd.y - CY) < R
ring = (np.hypot(sd.x - CX, sd.y - CY) >= R) & (np.hypot(sd.x - CX, sd.y - CY) < 2 * R)
true_contrast = (inner.sum() / (np.pi * R**2)) / (ring.sum() / (3 * np.pi * R**2))
print(f"n = {len(sd):,}; points within {R} of ({CX}, {CY}): {inner.sum()}; true density there is "
      f"{true_contrast:.1f}× the surrounding ring")

fig, axs = plt.subplots(1, 4, figsize=(16, 4.3))
methods = ["opaque", f"alpha={ALPHA}", f"hexbin gridsize={GRIDSIZE}", "2-D KDE"]
axs[0].scatter(sd.x, sd.y, s=6, color=BLUE, linewidths=0)
axs[1].scatter(sd.x, sd.y, s=6, color=BLUE, alpha=ALPHA, linewidths=0)
axs[2].hexbin(sd.x, sd.y, gridsize=GRIDSIZE, cmap="Blues", mincnt=1, linewidths=0)
kde = stats.gaussian_kde(np.vstack([sd.x, sd.y]))
gx, gy = np.meshgrid(np.linspace(-4, 4.5, 220), np.linspace(-4, 4.5, 220))
gz = kde(np.vstack([gx.ravel(), gy.ravel()])).reshape(gx.shape)
axs[3].contourf(gx, gy, gz, levels=14, cmap="Blues")
for a, m in zip(axs, methods):
    a.set_xlim(-4, 4.5)
    a.set_ylim(-4, 4.5)
    a.set_aspect("equal")
    a.set_title(m, fontsize=10)
    a.grid(False)
fig.canvas.draw()


def measured_contrast(ax):
    """ink darkness inside the cluster disc vs the ring around it, measured on
    the rendered pixels (1 = invisible, higher = visible)"""
    img = np.asarray(fig.canvas.buffer_rgba())[..., :3].astype(float) / 255
    dark = 1 - img.mean(axis=2)
    H = dark.shape[0]
    cx, cy = ax.transData.transform((CX, CY))
    rpx = abs(ax.transData.transform((CX + R, CY))[0] - cx)
    yy, xx = np.mgrid[0:H, 0:dark.shape[1]]
    dd = np.hypot(xx - cx, (H - yy) - cy)
    i_, r_ = dark[dd < rpx].mean(), dark[(dd >= rpx) & (dd < 2 * rpx)].mean()
    return i_ / max(r_, 1e-6), i_


res = []
for a, m in zip(axs, methods):
    c, ink = measured_contrast(a)
    res.append((m, c, ink))
for (m, c, ink), a in zip(res, axs):
    a.set_title(f"{m}\ncluster/ring ink {c:.2f}×", fontsize=10)
    a.add_patch(plt.Circle((CX, CY), 2 * R, fill=False, ec=ORANGE, lw=0.8, ls="--"))
for m, c, ink in res:
    verdict = ("visible, with its density" if c > 1.6 else "barely visible" if c > 1.2 else
               "a blob is seen but its DENSITY is not: inside and ring both saturate, so 800 "
               "points look like 80")
    print(f"  {m:20s} ink inside / ring = {c:5.2f}×  (inside ink {ink:.2f}) -> {verdict}")
print(f"""Declared parameters: marker s=6 pt², alpha={ALPHA}, hexbin gridsize={GRIDSIZE} (mincnt=1),
KDE Scott bandwidth (scipy default), 14 contour levels. The orange dashed circle is the 2R ring.
PUBLISH: hexbin — it keeps every point as a COUNT with a readable colour bar, shows the cluster,
and does not depend on a bandwidth the reader cannot see (the KDE's smoothing is a hidden
parameter that can spread or erase an 800-point cluster); alpha is fine for exploring but the
darkness of a pixel is not a number a reader can decode.""")
fig.suptitle("Part B2 · the same 9,000 points four ways — the 800-point cluster at (3.1, 3.0)",
             x=0.01, ha="left", fontweight="bold")
save_fig(fig, HERE / "partB_overplotting.png", note=f"Source: {SYNTH} (scatter_dense.csv).")
plt.close(fig)

# ======================================================================= B3
hdr("B3 · Scaling and dimension reduction")
for how in ("minmax", "zscore", "rank"):
    g = geolib.scale_frame(h, NUM_COLS, how).gdp_pc
    rest = g[h.country != "Aldonia"]
    print(f"  {how:7s} gdp_pc: Aldonia {g.max():6.3f}; other 59 span {rest.min():6.3f}–{rest.max():6.3f} "
          f"(width {rest.max()-rest.min():.3f} of total {g.max()-g.min():.3f} = "
          f"{(rest.max()-rest.min())/(g.max()-g.min())*100:4.1f}%); median {g.median():6.3f}")
print("  -> min–max: 59 countries share 11% of the axis; z-score: same crush, Aldonia at +7.5 sd; "
      "rank: even spread, but the 9.2× gap becomes one rank step.")
Z = geolib.scale_frame(h, NUM_COLS, "zscore")
pca = PCA().fit(Z)
evr = pca.explained_variance_ratio_
print("PCA on z-scored columns, explained variance ratio: " +
      ", ".join(f"PC{i+1} {v*100:.1f}%" for i, v in enumerate(evr)))
print(f"first two components: {evr[:2].sum()*100:.1f}% -> a two-axis picture misses "
      f"{(1-evr[:2].sum())*100:.1f}% of the (standardised) variation")
print("PC1 loadings: " + ", ".join(f"{c} {l:+.2f}" for c, l in zip(NUM_COLS, pca.components_[0])))
Zr = geolib.scale_frame(h, NUM_COLS, "rank")
evr_r = PCA().fit(Zr - Zr.mean()).explained_variance_ratio_
print(f"(sensitivity: on rank-scaled columns the first two explain {evr_r[:2].sum()*100:.1f}%)")

# ======================================================================= B4
hdr("B4 · Project before you measure")
feats, d, _ = districts()


def shoelace(x, y):
    x, y = np.asarray(x), np.asarray(y)
    return 0.5 * abs(np.dot(x, np.roll(y, -1)) - np.dot(y, np.roll(x, -1)))


codes = [f["code"] for f in feats]
sph = np.array([geolib.polygon_area_km2(f["ring"]) for f in feats])
deg = np.array([shoelace(*np.array(f["ring"]).T) for f in feats])
mer = np.array([shoelace(*geolib.mercator_xy(*np.array(f["ring"]).T)) for f in feats])
lat_ts = float(np.mean([p[1] for f in feats for p in f["ring"]]))
ea = np.array([shoelace(*geolib.equal_area_xy(*np.array(f["ring"]).T, lat_ts=lat_ts)) for f in feats])
lat = np.array([geolib.representative_point(f["ring"])[1] for f in feats])
north = np.argsort(-lat)[:4]
print(f"total area: spherical {sph.sum():,.0f} km²; shoelace on degrees {deg.sum():.2f} 'square degrees'")
print(f"four northernmost ({', '.join(codes[i] for i in north)}): share of total area "
      f"{sph[north].sum()/sph.sum()*100:.2f}% (spherical) vs {deg[north].sum()/deg.sum()*100:.2f}% "
      f"(degrees) -> over-weighted by {(deg[north].sum()/deg.sum())/(sph[north].sum()/sph.sum())*100-100:+.1f}%")
s_s, s_d = sph / sph.sum(), deg / deg.sum()
k = int(np.argmax(np.abs(s_d / s_s - 1)))
j = int(np.argmin(s_d / s_s))
print(f"most distorted district: {codes[k]} ({lat[k]:.1f}°N) share {s_s[k]*100:.2f}% -> "
      f"{s_d[k]*100:.2f}% ({(s_d[k]/s_s[k]-1)*100:+.1f}%); most UNDER-weighted: {codes[j]} "
      f"({lat[j]:.1f}°N, {(s_d[j]/s_s[j]-1)*100:+.1f}%)")
infl = mer / sph
print(f"Mercator area inflation (projected planar area ÷ true area): {infl.min():.3f}× in the "
      f"south to {infl.max():.3f}× in the north ({infl.max()/infl.min():.3f}× relative); "
      f"Lambert equal-area error {np.abs(ea/sph-1).max()*100:.1e}%")
print("  [finding] geolib's self-check prints 1.144–1.168× because it scales by sec(lat), "
      "Mercator's LINEAR scale; the AREA scale is sec²(lat), which the projected polygons confirm.")
print("Why it matters: on a choropleth, AREA is the encoding channel, so a projection that makes "
      f"northern districts {infl.max()/infl.min():.2f}× bigger than equal southern ones adds ink "
      "the data never asked for — slide 34's reason for equal-area.")

# ======================================================================= B5
hdr("B5 · Small-area stability — funnel plot")
sa = pd.read_csv(D / "smallarea_cases.csv")
sa["rate"] = sa.cases / sa.population * PER
pr = pooled_rate(sa.cases, sa.population)
out = {}
for z, lab in ((1.96, "95%"), (3.09, "99.8%")):
    lam = pr / PER * sa.population
    lo_ = np.maximum((lam - z * np.sqrt(lam)) / sa.population * PER, 0)
    hi_ = (lam + z * np.sqrt(lam)) / sa.population * PER
    o = sa[(sa.rate < lo_) | (sa.rate > hi_)]
    out[lab] = o
    print(f"outside {lab} limits: {len(o)} of 40 -> {o.unit.tolist()} "
          f"(expected by chance if all share one rate ≈ {40*2*(1-stats.norm.cdf(z)):.2f})")
u = sa[sa.unit == "U32"].iloc[0]
lam32 = pr / PER * u.population
p32 = stats.poisson.sf(u.cases - 1, lam32)
print(f"U32 exactly: expected {lam32:.2f} cases, observed {u.cases}; P(≥{u.cases}) = {p32:.5f}; chance "
      f"that SOME unit of 40 does this = {1-(1-p32)**40:.4f} (about 1 map in {1/(1-(1-p32)**40):.0f}).")
print("Meaning for case 6: the other 39 units — including every 'high' bar after U32 (15.4, 12.3, "
      "12.2…) — sit inside the funnel, so the ranking below U32 is pure noise. U32 itself is "
      "surprising, but the file states all 40 share one true rate, so it is the rare extreme that "
      "a 40-unit map throws up about once in 140 maps; and its 9 cases give a 95% interval of "
      "18.7–77.7 per 100k, so '4.7×' is not a measured number. Publishable action: flag U32 for "
      "follow-up, do not map it as a hotspot; merge units below ~43,000 people (see next line).")
# minimum population to tell 9 from 18 per 100k
P = np.arange(1000, 1_000_000, 100)
lam9, lam18 = 9e-5 * P, 18e-5 * P
one = P[np.argmax(lam9 + 1.96 * np.sqrt(lam9) < lam18)]
both = P[np.argmax(lam9 + 1.96 * np.sqrt(lam9) < lam18 - 1.96 * np.sqrt(lam18))]
exact = None
for p_ in range(5000, 400_000, 100):
    if stats.poisson.ppf(0.975, 9e-5 * p_) < stats.poisson.ppf(0.025, 18e-5 * p_):
        exact = p_
        break
print(f"9 vs 18 per 100,000: the 95% funnel at 9 first excludes 18 at a population of about "
      f"{one:,} (λ ≈ {9e-5*one:.1f} cases); for the two 95% intervals not to overlap at all needs "
      f"~{both:,} (normal approx.) / {exact:,} (exact Poisson). Below ~43,000 people the two rates "
      "cannot be told apart at all.")

fig, ax = plt.subplots(figsize=(8, 5))
pop = np.linspace(sa.population.min() * 0.9, sa.population.max() * 1.05, 400)
for z, ls, lab in ((1.96, "-", "95% limits"), (3.09, ":", "99.8% limits")):
    fl = geolib.funnel_limits(pop, pr, z=z)
    ax.plot(fl.population, fl.hi, color=PALETTE["ink"], lw=0.9, ls=ls, label=lab)
    ax.plot(fl.population, fl.lo, color=PALETTE["ink"], lw=0.9, ls=ls)
ax.axhline(pr, color=PALETTE["muted"], lw=1, label=f"pooled {pr:.2f}")
ax.scatter(sa.population, sa.rate, s=20, color=[ORANGE if u in out["95%"].unit.tolist() else BLUE
                                                for u in sa.unit], zorder=3)
ax.set_xscale("log")
ax.set_xlabel("Population of the unit (log)")
ax.set_ylabel("Cases per 100,000 residents")
ax.legend(fontsize=8)
ax.set_title(f"{len(out['95%'])} of 40 units outside the 95% funnel and {len(out['99.8%'])} outside 99.8% —\n"
             "what one shared rate plus Poisson noise looks like", fontsize=11)
save_fig(fig, HERE / "partB_funnel.png", note=f"Source: {SYNTH} (smallarea_cases.csv). "
         "Limits: normal approximation to Poisson, geolib.funnel_limits().")
plt.close(fig)
print("\nsaved partB_overplotting.png, partB_funnel.png")
