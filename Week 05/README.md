# Week 5 — Multivariate Data & Geospatial Visualization (CDB601220)

Qurat ul Aien · AI-016. Course data is synthetic (CDB601220 Week 5, fictional places).
`geolib.py` and `vizlib.py` are the course toolkits, **unchanged**. No geopandas needed.

## Run (Windows, VS Code terminal)

```
pip install -r requirements.txt
python run_all.py
```

| Script | Produces |
|---|---|
| `partD_bubble.py` | `partD_bubble.png` — D1, four channels, size legend |
| `partD_pcp.py` | `partD_pcp.png` — D2, rank scaling, greedy order, Borealis brushed |
| `partD_choropleth.py` | `partD_choropleth.png` — D3, rate map + counts beside it |
| `partA_charts.py` | `partA_case01..09.png` (rebuild + redesign), `partA_output.txt` |
| `partB_decisions.py` | `partB_output.txt`, `partB_overplotting.png`, `partB_funnel.png` |
| `partC_maps.py` | `partC_mapA_count.png`, `partC_mapB_rate.png` |
| `partF_map.py` | `partF_map.png` (bonus, real data — sources in `data_partF/SOURCE.txt`) |
| `build_reports.py` | `partA_diagnosis.pdf`, `partE_justification.pdf` |
| `w5common.py` | shared helpers, incl. a pandas-3-safe `corr_chain` |

## Part C — YOU must run this on at least 5 real people

Invented results score zero, so no results are included.

1. Open `partC_mapA_count.png` full screen. Run `python partC_maps.py --record`.
2. Ask: *"Which three counties would you send extra police to, and why?"* Type their three.
3. Then show `partC_mapB_rate.png`, same question, type their three. Don't let them change answer 1.
4. Repeat for each reader (5 minimum). Results go to `partC_reader_results.csv`.
5. `python partC_maps.py --score > partC_score.txt` — mean overlap.
6. `python build_reports.py` — Part E's counterfactual now quotes your real readers.

## Findings reported (numbers that did not reproduce as worded)

- Case 1: with `s=pop_m**2`, **589× is the mark's diameter** (area 346,921×); the 9 countries under 2.0 M are < 2 pt across (3 under 1 pt).
- `geolib.corr_chain()` crashes on pandas ≥ 3 (`DataFrame.values` is read-only); `w5common.corr_chain()` is the same rule on a NumPy copy and gives the brief's order.
- geolib's self-check Mercator inflation (1.14–1.17×) uses sec φ (linear scale); measured on the projected polygons the area inflation is 1.24× (south) to 1.49× (north).
