"""
Shared helpers for the Week 5 scripts (CDB601220). Synthetic course data.

geolib.py and vizlib.py are the course toolkits and are used UNCHANGED.
One finding: geolib.corr_chain() crashes on pandas >= 3.0, because
`DataFrame.values` is now a read-only view and np.fill_diagonal() writes into
it ("ValueError: underlying array is read-only"). `corr_chain()` below is the
same greedy rule from slide 24, computed on a writable NumPy copy; on pandas 2
it returns exactly what geolib.corr_chain() returns (checked in __main__).
"""
from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

import geolib

HERE = Path(__file__).resolve().parent
D = HERE / "data"
SYNTH = "CDB601220 Week 5 synthetic course data — fictional places, not real ones"
BOUNDARIES = ("Boundaries: districts.geojson (24 districts, CDB601220 Week 5, fictional "
              "federation 66–74°E, 24–36°N), course release 2026")
NUM_COLS = ["gdp_pc", "healthcare_access", "urban_pct", "median_age", "cases_per_100k"]
PER = 100_000


def corr_chain(df: pd.DataFrame, cols) -> list:
    """Slide 24's greedy axis order by |r| — geolib.corr_chain(), pandas-3 safe."""
    cols = list(cols)
    r = np.abs(df[cols].corr().to_numpy(copy=True))
    np.fill_diagonal(r, 0.0)
    i, j = np.unravel_index(np.argmax(r), r.shape)
    order = [i, j]
    while len(order) < len(cols):
        rest = [k for k in range(len(cols)) if k not in order]
        order.append(max(rest, key=lambda k: r[order[-1], k]))
    return [cols[k] for k in order]


def health():
    return pd.read_csv(D / "health_indicators.csv")


def districts():
    """Features + district table, joined on code, with the join audited."""
    feats = geolib.read_geojson(D / "districts.geojson")
    df = pd.read_csv(D / "district_health.csv")
    geo_codes = {f["code"] for f in feats}
    tab_codes = set(df.code)
    audit = {
        "features": len(feats),
        "rows": len(df),
        "rows_unmatched": sorted(tab_codes - geo_codes),
        "features_unmatched": sorted(geo_codes - tab_codes),
        "dup_codes_table": int(df.code.duplicated().sum()),
    }
    df["rate"] = df.cases / df.population * PER
    return feats, df, audit


def pooled_rate(cases, pop):
    return float(np.sum(cases) / np.sum(pop) * PER)


if __name__ == "__main__":
    h = health()
    print("corr_chain:", " -> ".join(corr_chain(h, NUM_COLS)))
    try:
        print("geolib.corr_chain:", " -> ".join(geolib.corr_chain(h, NUM_COLS)))
    except ValueError as e:
        print(f"geolib.corr_chain fails on pandas {pd.__version__}: {e}")
