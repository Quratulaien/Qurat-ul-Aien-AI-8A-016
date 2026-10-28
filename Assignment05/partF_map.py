"""
Part F (bonus) — a normalized choropleth on real data (CDB601220, Week 5).

Map: reported COVID-19 deaths per 100,000 residents, cumulative to early
August 2024, for the countries of Asia.

DATA  Our World in Data, COVID-19 dataset, `owid-covid-latest.csv`
      (columns total_deaths, population; deaths from the WHO COVID-19 dashboard,
      population from UN World Population Prospects), from
      https://raw.githubusercontent.com/owid/covid-19-data/master/public/data/latest/owid-covid-latest.csv
      Downloaded 28 Oct 2026; last_updated_date in the file: 2024-08-04 (India 2024-08-12).
BOUNDARIES  Natural Earth 1:50m Admin 0 – Countries (de facto boundaries),
      ne_50m_admin_0_countries.geojson, repository version 5.2.0-pre, from
      https://raw.githubusercontent.com/nvkelso/natural-earth-vector/master/geojson/ne_50m_admin_0_countries.geojson
      Downloaded 28 Oct 2026. Natural Earth shows de facto control lines; disputed
      areas (e.g. Kashmir) are drawn as NE draws them — that is a political choice
      by the boundary source, stated here rather than hidden.

    python3 partF_map.py   -> partF_map.png (300 dpi) + printed log (partF_output.txt)
"""
import json
import math
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.collections import PatchCollection
from matplotlib.patches import Patch, Polygon as MplPolygon
import numpy as np
import pandas as pd

import geolib
from geolib import PALETTE, style_defaults, save_fig

HERE = Path(__file__).resolve().parent
DF = HERE / "data_partF"
PER = 100_000
K, SCHEME = 5, "natural"
# Albers equal-area conic for Asia (sphere). Standard parallels chosen to
# bracket the continent's land: 15°N and 55°N; centre 95°E, origin 30°N.
LAT1, LAT2, LAT0, LON0 = 15.0, 55.0, 30.0, 95.0
R = geolib.R_EARTH_KM


def albers(lon, lat):
    p1, p2, p0 = map(math.radians, (LAT1, LAT2, LAT0))
    n = (math.sin(p1) + math.sin(p2)) / 2
    C = math.cos(p1) ** 2 + 2 * n * math.sin(p1)
    rho0 = R * math.sqrt(C - 2 * n * math.sin(p0)) / n
    lon, lat = np.radians(np.asarray(lon, float)), np.radians(np.asarray(lat, float))
    rho = R * np.sqrt(C - 2 * n * np.sin(lat)) / n
    th = n * (lon - math.radians(LON0))
    return rho * np.sin(th), rho0 - rho * np.cos(th)


def rings_of(geom):
    if geom["type"] == "Polygon":
        return [geom["coordinates"][0]]
    return [poly[0] for poly in geom["coordinates"]]


def shoelace(x, y):
    return 0.5 * abs(np.dot(x, np.roll(y, -1)) - np.dot(y, np.roll(x, -1)))


def main():
    style_defaults()
    gj = json.load(open(DF / "ne_50m_admin_0_countries.geojson"))
    asia = [f for f in gj["features"] if f["properties"]["CONTINENT"] == "Asia"]
    o = pd.read_csv(DF / "owid_latest.csv")
    o = o[o.iso_code.str.len() == 3]                      # drop OWID aggregates (OWID_*)
    by_iso = o.set_index("iso_code")

    # ---- join, with failures counted
    rows, unmatched = [], []
    for f in asia:
        p = f["properties"]
        iso = p["ISO_A3"] if p["ISO_A3"] != "-99" else p["ADM0_A3"]
        if iso in by_iso.index:
            r = by_iso.loc[iso]
            rows.append({"iso": iso, "name": p["NAME"], "deaths": r.total_deaths,
                         "population": r.population, "updated": r.last_updated_date, "feat": f})
        else:
            unmatched.append(p["NAME"])
    d = pd.DataFrame(rows)
    print(f"[join] Natural Earth Asia features {len(asia)}; matched to OWID {len(d)}; "
          f"unmatched {len(unmatched)}: {unmatched} -> drawn as 'no data'")

    # ---- normalize; flag non-credible reports instead of colouring them 'low'
    d["rate"] = d.deaths / d.population * PER
    no_rep = d[(d.deaths.isna()) | (d.deaths == 0)]
    print(f"[suppress] reported deaths missing or exactly 0 -> 'no usable report' (not a low rate): "
          f"{no_rep.name.tolist()}")
    ok = d.drop(no_rep.index).copy()
    print(f"[normalize] {len(ok)} countries; {ok.deaths.sum():,.0f} reported deaths / "
          f"{ok.population.sum()/1e9:.2f} bn residents = {ok.deaths.sum()/ok.population.sum()*PER:.1f} "
          f"per 100,000 (pooled)")
    print(f"           r(deaths, population) {np.corrcoef(ok.deaths, ok.population)[0,1]:+.3f}; "
          f"r(rate, population) {np.corrcoef(ok.rate, ok.population)[0,1]:+.3f}")
    print("top 5 by COUNT:", ", ".join(f"{r.name} {r.deaths:,.0f}" for r in ok.nlargest(5, "deaths").itertuples()))
    print("top 5 by RATE: ", ", ".join(f"{r.name} {r.rate:.0f}" for r in ok.nlargest(5, "rate").itertuples()))
    # ---- classify
    scores = {s: geolib.gvf(ok.rate, geolib.breaks(ok.rate, s, K)) for s in ("equal", "quantile", "natural")}
    edges = geolib.breaks(ok.rate, SCHEME, K)
    ok["cls"] = geolib.class_of(ok.rate, edges)
    print(f"[classify] Jenks k=5 edges {[round(e) for e in edges]}; per class "
          f"{np.bincount(ok.cls, minlength=K).tolist()}; GVF " +
          ", ".join(f"{k} {v:.3f}" for k, v in scores.items()))
    small = ok[ok.population < 1_000_000]
    for r in small.itertuples():
        hw = 1.96 / np.sqrt(r.deaths)
        lo_, hi_ = r.rate * (1 - hw), r.rate * (1 + hw)
        same = geolib.class_of([lo_], edges)[0] == geolib.class_of([hi_], edges)[0]
        print(f"small population: {r.name} {r.population/1e6:.2f} M, {r.deaths:.0f} deaths, rate "
              f"{r.rate:.1f} (95% ≈ {lo_:.1f}–{hi_:.1f}) -> "
              f"{'same class across its interval, shown' if same else 'interval crosses a break — flagged'}")


    # ---- projection check: Albers is equal-area
    errs = []
    for r in ok.itertuples():
        for ring in rings_of(r.feat["geometry"]):
            if len(ring) > 50:
                x, y = albers(*np.array(ring).T)
                sph = geolib.polygon_area_km2(ring)
                if sph > 50_000:
                    errs.append(abs(shoelace(x, y) / sph - 1))
    print(f"[project] Albers equal-area conic ({LAT1}°N/{LAT2}°N, {LON0}°E); planar ÷ spherical "
          f"area on {len(errs)} large rings: max error {max(errs)*100:.2f}% (vertex sampling only)")

    # ---- draw
    cm = plt.get_cmap(PALETTE["sequential"])
    shades = [cm(0.18 + 0.78 * c / (K - 1)) for c in range(K)]
    fig, ax = plt.subplots(figsize=(13, 9))
    patches, colours, hatch_p = [], [], []
    for r in d.itertuples():
        for ring in rings_of(r.feat["geometry"]):
            x, y = albers(*np.array(ring).T)
            poly = MplPolygon(np.column_stack([x, y]), closed=True)
            if r.Index in no_rep.index:
                hatch_p.append(poly)
            else:
                patches.append(poly)
                colours.append(shades[int(ok.loc[r.Index, "cls"])])
    for f in asia:
        if f["properties"]["NAME"] in unmatched:
            for ring in rings_of(f["geometry"]):
                hatch_p.append(MplPolygon(np.column_stack(albers(*np.array(ring).T)), closed=True))
    ax.add_collection(PatchCollection(patches, facecolors=colours, edgecolors="white", linewidths=0.35))
    ax.add_collection(PatchCollection(hatch_p, facecolors="#F2F2F2", edgecolors=PALETTE["muted"],
                                      linewidths=0.35, hatch="////"))
    ax.autoscale_view()
    ax.set_aspect("equal")
    ax.set_axis_off()
    for r in ok.nlargest(6, "rate").itertuples():
        lon, lat = r.feat["properties"].get("LABEL_X"), r.feat["properties"].get("LABEL_Y")
        x, y = albers(lon, lat)
        ax.annotate(f"{r.name} {r.rate:.0f}", (x, y), xytext=(x - 900, y + 650), fontsize=8,
                    arrowprops=dict(arrowstyle="-", lw=0.5, color=PALETTE["ink_soft"]))
    for nm in ("India", "China", "Pakistan"):
        r = ok[ok.name == nm].iloc[0]
        x, y = albers(r.feat["properties"]["LABEL_X"], r.feat["properties"]["LABEL_Y"])
        ax.text(x, y, f"{nm}\n{r.rate:.0f}", ha="center", fontsize=8,
                color="white" if r.cls >= 3 else PALETTE["ink"])
    handles = [Patch(facecolor=shades[c], edgecolor="white",
                     label=f"{edges[c]:,.0f} – {edges[c+1]:,.0f}   ({(ok.cls==c).sum()} "
                           f"countr{'y' if (ok.cls==c).sum()==1 else 'ies'})")
               for c in range(K)]
    handles.append(Patch(facecolor="#F2F2F2", edgecolor=PALETTE["muted"], hatch="////",
                         label="no usable report (0 or missing, or no OWID row)"))
    ax.legend(handles=handles, title="Reported COVID-19 deaths per 100,000 residents\n"
              "(cumulative to Aug 2024; Jenks natural breaks, 5 classes)", loc="lower left",
              fontsize=8, title_fontsize=8.5, frameon=False)
    top = ok.nlargest(1, "rate").iloc[0]
    cnt = ok.nlargest(1, "deaths").iloc[0]
    ax.set_title(f"Per resident, the Caucasus and Levant were hit hardest — {top['name']} reported "
                 f"{top.rate:,.0f} deaths per 100,000;\na raw-count map would instead point at "
                 f"{cnt['name']} ({cnt.deaths:,.0f} deaths, {cnt.rate:.0f} per 100,000)",
                 fontsize=12.5, loc="left")
    note = ("Data: Our World in Data COVID-19 dataset (owid-covid-latest.csv; deaths from the WHO COVID-19 "
            "dashboard, population UN WPP), data to 4 Aug 2024 (India 12 Aug), downloaded 28 Oct 2026. "
            "Boundaries: Natural Earth 1:50m Admin 0 Countries, v5.2.0-pre, de facto lines, downloaded 28 Oct 2026.\n"
            f"Projection: Albers equal-area conic, standard parallels {LAT1:.0f}°N and {LAT2:.0f}°N, central "
            f"meridian {LON0:.0f}°E. Rate = reported deaths ÷ residents × 100,000. Jenks GVF {scores['natural']:.3f} "
            f"(quantile {scores['quantile']:.3f}). Breaks: {', '.join(f'{e:,.0f}' for e in edges)}.\n"
            f"Not coloured: {', '.join(no_rep.name)} (reported 0 or missing — a reporting gap, not a low rate) and "
            f"{', '.join(unmatched)} (no OWID row). Reported deaths depend on testing and registration, "
            "which differ between countries; excess mortality is not shown.")
    save_fig(fig, HERE / "partF_map.png", note=note)
    plt.close(fig)
    print("saved partF_map.png")
    ce = geolib.breaks(ok.deaths, SCHEME, K)
    ccls = geolib.class_of(ok.deaths, ce)
    print(f"count map check (Jenks on deaths): darkest class {ok.name[ccls == K-1].tolist()}; "
          f"{top['name']} in count class {int(ccls[ok.name.tolist().index(top['name'])]) + 1} of {K}")
    second = ok.name[ccls == K - 2].tolist()
    print(f"\nRAW-COUNT COUNTERFACTUAL: a count map (same Jenks scheme) would put {cnt['name']} "
          f"({cnt.deaths:,.0f}) alone in the darkest class and {', '.join(second)} next — large-population "
          f"countries — while {top['name']}, with {top.population/1e6:.1f} M people and the "
          f"highest rate, would sit in the palest class.")


if __name__ == "__main__":
    main()
