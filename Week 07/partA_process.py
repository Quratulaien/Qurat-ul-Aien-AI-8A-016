#!/usr/bin/env python3
"""
partA_process.py — raw -> audit -> clean/   (Week 7, Task A)

Reads the three raw CSVs and the GeoJSON from data/, prints an audit, applies
the rules in partA_decisions.md, writes cleaned copies to clean/. Raw files are
never written to. Run from anywhere:

    python3 partA_process.py

Writes: partA_audit.txt, partA_decisions.md, clean/*.csv, clean/regions.geojson
"""
from __future__ import annotations

import os
import shutil
import sys

import numpy as np
import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import geolib  # noqa: E402
import tslib   # noqa: E402

D = os.path.join(HERE, "data")
CLEAN = os.path.join(HERE, "clean")
os.makedirs(CLEAN, exist_ok=True)

_audit: list[str] = []


def say(*parts) -> None:
    line = " ".join(str(p) for p in parts)
    print(line)
    _audit.append(line)


DECISIONS: list[dict] = []


def decide(file, action, what, detected, rule, n) -> None:
    DECISIONS.append(dict(id=f"A{len(DECISIONS) + 1}", file=file, action=action,
                          what=what, detected=detected, rule=rule, n=n))


feats = geolib.read_geojson(os.path.join(D, "regions.geojson"))
gname = {f["code"]: f["name"] for f in feats}
GCODES = set(gname)

# =========================================================================
# 1  district_transit.csv
# =========================================================================
say("=" * 74)
say("FILE 1  district_transit.csv  (district register)")
say("=" * 74)
raw = pd.read_csv(os.path.join(D, "district_transit.csv"), dtype=str)
raw["_row"] = np.arange(len(raw))
say(f"rows {len(raw)}; distinct code strings {raw.code.nunique()}")
bad_key = raw[~raw.code.isin(GCODES)]
say("codes not in the boundary file (as filed):")
for _, r in bad_key.iterrows():
    say(f"  line {r._row + 2}: '{r.code}' ({r.district}), population {int(r.population):,}")
say(f"register rows matched to boundaries as filed: {int(raw.code.isin(GCODES).sum())} of {len(raw)}")

num = ["population", "households", "area_km2", "lon", "lat", "income_pc_usd", "stops",
       "road_km", "boardings_annual", "fare_concession_pct", "vehicles_registered"]
say("\nnon-numeric per numeric column:")
for c in num:
    as_n = pd.to_numeric(raw[c], errors="coerce")
    say(f"  {c:20s} blank={int(raw[c].isna().sum())} not-a-number="
        f"{raw.loc[as_n.isna() & raw[c].notna(), c].tolist()}")

reg = raw.copy()

# R1 key typed wrong -----------------------------------------------------
fix = reg.code.str.replace(" ", "", regex=False).str.upper()
changed = reg.code != fix
say(f"\nR1 code typed wrong: {reg.loc[changed, 'code'].tolist()} -> {fix[changed].tolist()}")
reg["code"] = fix
decide("district_transit", "repair",
       "register codes typed as " + ", ".join(f"'{c}'" for c in raw.loc[changed, 'code']),
       "they do not match any boundary feature as filed",
       "remove spaces, upper-case: 'd13' -> D13, 'D 20' -> D20. The district is unambiguous",
       int(changed.sum()))

# R2 a row that is not one of the 24 districts ------------------------------
extra = ~reg.code.isin(GCODES)
say(f"R2 rows whose code is not one of the 24 boundary districts: "
    f"{reg.loc[extra, 'code'].tolist()}")
for _, r in reg[extra].iterrows():
    say(f"  '{r.district}' population {int(r.population):,}, households {int(r.households):,}")
pop_all = pd.to_numeric(raw.population).sum()
say(f"  population of all {len(raw)} rows: {pop_all:,}; of the 24 districts: "
    f"{pop_all - pd.to_numeric(raw.loc[raw.code == 'D00', 'population']).sum():,}")
decide("district_transit", "drop",
       "extra register row 'D00' 'Qilabad Capital Territory'",
       "its code is not among the 24 boundary features; adding it gives 60,747,000 people, "
       "which is not the federation's population",
       "not a district of the federation. Dropped with the count. Its boardings are not "
       "added to any district",
       int(extra.sum()))
reg = reg[~extra].copy()
say(f"  after R2: {len(reg)} rows, distinct codes {reg.code.nunique()}")

# convert numerics -----------------------------------------------------------
for c in num:
    reg[c] = pd.to_numeric(reg[c])

# R3 boardings typed in thousands ------------------------------------------
reg["bpr"] = reg.boardings_annual / reg.population            # per resident per year
low = reg.bpr < 1
say(f"\nR3 boardings per resident per year (<1 flagged): "
    f"{[(c, round(v, 4)) for c, v in zip(reg.loc[low, 'code'], reg.loc[low, 'bpr'])]}")
band = (reg.bpr[~low].min() * 1000, reg.bpr[~low].max() * 1000)
for i in reg.index[low]:
    trial = reg.at[i, "boardings_annual"] * 1000
    tpr = trial / reg.at[i, "population"]
    lo_, hi_ = reg.bpr[~low].min(), reg.bpr[~low].max()
    accept = lo_ <= tpr <= hi_
    say(f"  {reg.at[i, 'code']} boardings {int(reg.at[i, 'boardings_annual'])} x 1000 = "
        f"{int(trial):,} -> {tpr:.2f} per resident; band of the others {lo_:.2f}-{hi_:.2f}; "
        f"{'repaired' if accept else 'NOT repaired'}")
    if accept:
        reg.at[i, "boardings_annual"] = trial
        decide("district_transit", "repair",
               f"boardings_annual {reg.at[i, 'code']} '{reg.at[i, 'district']}' filed as "
               f"{int(trial / 1000)}; should be {int(trial):,}",
               f"{reg.at[i, 'bpr']:.4f} boardings per resident as filed "
               f"vs band {lo_:.2f}–{hi_:.2f} for the other districts",
               "the value was filed in thousands. Repaired x1000 only because the repaired "
               "value lands inside the band of the other districts",
               1)
reg["bpr"] = reg.boardings_annual / reg.population
reg["bp1000"] = reg.bpr * 1000
say(f"  boardings per 1,000 residents after repair: min {reg.bp1000.min():,.0f}, "
    f"max {reg.bp1000.max():,.0f}")

# R4 fraction typed as percent ------------------------------------------------
frac = reg.fare_concession_pct <= 1
say(f"R4 fare_concession_pct filed as a fraction: {reg.loc[frac, 'code'].tolist()}")
reg.loc[frac, "fare_concession_pct"] = reg.loc[frac, "fare_concession_pct"] * 100
decide("district_transit", "repair",
       "fare_concession_pct filed as a fraction (0.33) not a percent (33)",
       "value is below 1 while every other district is between 20 and 43",
       "multiply by 100; the repaired values land inside the others' range",
       int(frac.sum()))

# R5 sentinel in road_km ------------------------------------------------------
roadsent = reg.road_km < 0
say(f"R5 road_km negative (sentinel): {reg.loc[roadsent, 'code'].tolist()}")
reg["road_km"] = reg.road_km.where(~roadsent)
decide("district_transit", "set to missing",
       "road_km = -1 (not a length)",
       "a negative length cannot occur; -1 is the not-available code",
       "NaN, not 0", int(roadsent.sum()))

say(f"\ndistricts after cleaning {len(reg)}; population {int(reg.population.sum()):,}; "
    f"households {int(reg.households.sum()):,}")
say(f"  boardings_annual total {int(reg.boardings_annual.sum()):,}; "
    f"per 1,000 residents, pooled {reg.boardings_annual.sum() / reg.population.sum() * 1000:,.0f}")
say(f"  road_km usable {int(reg.road_km.notna().sum())} of {len(reg)}; "
    f"fare_concession_pct {reg.fare_concession_pct.min():.1f}–{reg.fare_concession_pct.max():.1f}")
area_geo = {f["code"]: geolib.polygon_area_km2(f["ring"]) for f in feats}
dev = max(abs(area_geo[c] - reg.loc[reg.code == c, "area_km2"].iloc[0]) / area_geo[c] for c in reg.code)
say(f"  area_km2 vs geometry, max relative deviation {dev:.2%}")
joined = reg.code.isin(GCODES).sum()
say(f"  join after cleaning: {joined} of {len(reg)} matched; "
    f"{len(GCODES - set(reg.code))} boundary features unmatched")

reg_out = reg.drop(columns=["_row", "bpr", "bp1000"])
reg_out.to_csv(os.path.join(CLEAN, "district_transit_clean.csv"), index=False)
say("  wrote clean/district_transit_clean.csv")

# =========================================================================
# 2  routes.csv
# =========================================================================
say("\n" + "=" * 74)
say("FILE 2  routes.csv  (route table, 36 routes)")
say("=" * 74)
rt = pd.read_csv(os.path.join(D, "routes.csv"), dtype=str)
rt["_row"] = np.arange(len(rt))
say(f"rows {len(rt)}; distinct mode labels as filed: {sorted(rt['mode'].unique())}")
MODE = {"metro": "Metro", "brt": "BRT", "bus rapid transit": "BRT",
        "bus": "Bus", "ferry": "Ferry"}
canon = rt["mode"].str.strip().str.lower().map(MODE)
assert canon.notna().all(), "unmapped mode label"
changed_m = rt["mode"] != canon
say(f"distinct mode labels after mapping: {sorted(canon.unique())}; "
    f"rows relabelled: {int(changed_m.sum())}")
rt["mode"] = canon
decide("routes", "repair",
       "mode label inconsistent: " + ", ".join(sorted(rt.loc[changed_m, 'mode'].unique())) +
       " for four modes",
       "value_counts() shows six labels for four modes",
       "map to the four canonical modes: brt and Bus Rapid Transit -> BRT, case-folded",
       int(changed_m.sum()))
for c in ["length_km", "stops", "fleet", "boardings_annual", "punctuality_pct",
          "crowding_index", "cost_recovery_pct", "subsidy_pkr_per_trip"]:
    rt[c] = pd.to_numeric(rt[c])

sent = rt.punctuality_pct > 100
say(f"punctuality_pct above 100 (sentinel): {rt.loc[sent, 'route_id'].tolist()}")
rt["punctuality_pct"] = rt.punctuality_pct.where(~sent)
decide("routes", "set to missing", "punctuality_pct = 999 (not a percentage)",
       "above 100 is impossible for a share", "NaN, not 100", int(sent.sum()))

zero_cr = rt.cost_recovery_pct == 0
say(f"cost_recovery_pct exactly 0: {rt.loc[zero_cr, 'route_id'].tolist()} "
    f"({rt.loc[zero_cr, 'mode'].tolist()}): read as a code, not a measurement")
rt["cost_recovery_pct"] = rt.cost_recovery_pct.where(~zero_cr)
decide("routes", "set to missing",
       "cost_recovery_pct = 0 on " + ", ".join(rt.loc[zero_cr, 'route_id']),
       "a route that recovers nothing of its cost is not what the ministry means; 0 "
       "is the not-available code here, consistent with the data dictionary",
       "NaN, not 0", int(zero_cr.sum()))

say(f"routes per mode after mapping: {rt['mode'].value_counts().sort_index().to_dict()}")
say(f"punctuality usable {int(rt.punctuality_pct.notna().sum())} of {len(rt)}, range "
    f"{rt.punctuality_pct.min():.1f}–{rt.punctuality_pct.max():.1f}")
rb = int(rt.boardings_annual.sum())
say(f"boardings_annual summed over routes: {rb:,}")
say(f"register boardings (cleaned): {int(reg.boardings_annual.sum()):,}; difference "
    f"{abs(rb - int(reg.boardings_annual.sum())):,}")
served = rt.districts_served.str.split(";")
say(f"routes serving more than one district: {int((served.str.len() > 1).sum())} of {len(rt)}; "
    f"mean {served.str.len().mean():.2f}, max {served.str.len().max()}")
attributed = int((rt.boardings_annual * served.str.len()).sum())
say(f"attributed to every district served: {attributed:,} = {attributed / rb:.3f}x the network total")
decide("routes", "exclude from sums",
       "a route is listed under every district it serves",
       f"attributed to each district it serves, boardings add to {attributed / rb:.2f}x the network",
       "a route's boardings are counted once in the network total; any by-district figure "
       "must split them, or say that the district figures overlap",
       int((served.str.len() > 1).sum()))
rt_out = rt.drop(columns=["_row"])
rt_out.to_csv(os.path.join(CLEAN, "routes_clean.csv"), index=False)
say("  wrote clean/routes_clean.csv")

# =========================================================================
# 3  ridership_daily.csv
# =========================================================================
say("\n" + "=" * 74)
say("FILE 3  ridership_daily.csv  (daily returns, four modes)")
say("=" * 74)
rd = pd.read_csv(os.path.join(D, "ridership_daily.csv"), dtype=str)
rd["_row"] = np.arange(len(rd))
is_iso = rd.date.str.fullmatch(r"\d{4}-\d{2}-\d{2}").fillna(False).astype(bool)
is_sl = rd.date.str.fullmatch(r"\d{2}/\d{2}/\d{4}").fillna(False).astype(bool)
say(f"rows {len(rd)}; ISO {int(is_iso.sum())}, DD/MM/YYYY {int(is_sl.sum())}, "
    f"other {int((~is_iso & ~is_sl).sum())}")
sp = rd.loc[is_sl, "date"].str.split("/", expand=True).astype(int)
first12 = int((sp[0] > 12).sum())
second12 = int((sp[1] > 12).sum())
amb = (sp[0] <= 12) & (sp[1] <= 12)
silent = int((amb & (sp[0] != sp[1])).sum())
say(f"  first field > 12: {first12} (cannot be a month); second > 12: {second12}; "
    f"ambiguous (month-first accepts them): {int(amb.sum())}; of those, month-first gives a "
    f"different real day for {silent}")
say(f"  => day-first, the convention the slash rows follow ({first12} rows prove it)")
d = pd.Series(pd.NaT, index=rd.index, dtype="datetime64[ns]")
d[is_iso] = pd.to_datetime(rd.loc[is_iso, "date"], format="%Y-%m-%d")
d[is_sl] = pd.to_datetime(rd.loc[is_sl, "date"], format="%d/%m/%Y")
assert d.notna().all()
decide("ridership_daily", "repair",
       "dates written DD/MM/YYYY alongside ISO",
       f"{first12} slash rows fail a month-first parse; the {int(amb.sum())} ambiguous rows "
       f"parse without error, and {silent} of them become a different real day",
       "parse slash rows day-first, ISO as ISO; no row dropped", int(is_sl.sum()))
rd["date"] = d
for c in ["trips_scheduled", "trips_operated", "trips_on_time", "boardings", "delay_minutes"]:
    rd[c] = pd.to_numeric(rd[c])

keycols = ["date", "mode", "trips_scheduled", "trips_operated", "trips_on_time",
           "boardings", "delay_minutes"]
exact_dup = rd.duplicated(keycols, keep="first")
say(f"\nexact re-submissions (same key and every field): {int(exact_dup.sum())}")
say(f"  by mode: {rd.loc[exact_dup, 'mode'].value_counts().to_dict()}; "
    f"months: {rd.loc[exact_dup, 'date'].dt.to_period('M').value_counts().sort_index().to_dict()}")
key_dup = rd.duplicated(["date", "mode"], keep=False).sum()
say(f"  rows sharing a (date, mode) key: {int(key_dup)}; all exact: "
    f"{bool(rd.duplicated(['date', 'mode'], keep=False).sum() == rd.duplicated(keycols, keep=False).sum())}")
rd_nodup = rd[~exact_dup].copy()
decide("ridership_daily", "drop",
       "exact re-submission of a day's return",
       f"{int(exact_dup.sum())} rows identical to another row in every field, same mode",
       "keep the first filing, drop the re-submission; all months and modes counted once",
       int(exact_dup.sum()))

imp = rd_nodup.trips_on_time > rd_nodup.trips_operated
say(f"\nimpossible: trips_on_time > trips_operated: {int(imp.sum())} rows")
for _, r in rd_nodup[imp].iterrows():
    say(f"  {r.date.date()} {r['mode']}: on time {int(r.trips_on_time)} > operated {int(r.trips_operated)}")
rd_nodup.loc[imp, "trips_on_time"] = np.nan
decide("ridership_daily", "set to missing",
       "trips_on_time greater than trips_operated, on " + str(int(imp.sum())) + " rows",
       "more trains arrived on time than ran; the on-time count is the field that cannot be right",
       "on-time set to NaN, so these days leave the punctuality ratio (both numerator and "
       "denominator). Boardings and delay are kept: the day's ridership did happen",
       int(imp.sum()))

full = pd.date_range(rd_nodup.date.min(), rd_nodup.date.max(), freq="D")
modes = ["Bus", "BRT", "Metro", "Ferry"]
slots = len(full) * len(modes)
filed = len(rd_nodup)
say(f"\nreporting span {full[0].date()} -> {full[-1].date()} = {len(full)} days x "
    f"{len(modes)} modes = {slots} slots; filed {filed}; never filed {slots - filed}")
missing_by_mode = {m: int(len(full) - rd_nodup[rd_nodup['mode'] == m].date.nunique()) for m in modes}
say(f"  never filed by mode: {missing_by_mode}")
rd_nodup = rd_nodup.sort_values(["mode", "date"])
gaps = rd_nodup.groupby("mode").date.diff().dt.days.fillna(1)
say(f"  longest single gap: {int(gaps.max() - 1)} missing days in a row, "
    f"{rd_nodup.loc[gaps.idxmax(), 'mode']} ending {rd_nodup.loc[gaps.idxmax(), 'date'].date()}")
decide("ridership_daily", "flag as missing",
       "days no control room filed",
       f"{slots} slots over the span; {filed} filed",
       "left absent: not zero boardings, not interpolated. Counts are summed only over days "
       "that were filed, and the day count is declared wherever a total is quoted",
       slots - filed)

last = rd_nodup.groupby("mode").date.max()
stopped = last[last < full[-1]]
late = rd_nodup[rd_nodup.date >= "2026-09-22"]
say(f"\nlast filing by mode: {{{', '.join(f'{m}: {v.date()}' for m, v in last.items())}}}")
say(f"  slots filed from 2026-09-22 onward: {len(late)} of {len(full[full >= '2026-09-22']) * 4} "
    f"(two modes stopped filing: {stopped.index.tolist()})")
decide("ridership_daily", "flag",
       "two modes stopped filing on 2026-09-21; the span runs to 2026-09-30",
       f"{late.shape[0]} filings from 2026-09-22 vs {len(full[full >= '2026-09-22']) * 4} slots",
       "the last nine days of September are a partial period for those modes. Drawn and "
       "labelled as partial, never at full weight",
       int(sum(len(full[full > v]) for v in stopped)))

y12 = rd_nodup[(rd_nodup.date >= "2025-09-01") & (rd_nodup.date <= "2026-08-31")]
b12 = int(y12.boardings.sum())
b12_raw = int(rd[(rd.date >= "2025-09-01") & (rd.date <= "2026-08-31")].boardings.sum())
say(f"\nboardings, 12 months to 2026-08-31, duplicates removed: {b12:,}; with them: "
    f"{b12_raw:,} ({(b12_raw / b12 - 1) * 100:+.2f}%)")
say(f"  the register annual total {int(reg.boardings_annual.sum()):,} covers "
    f"{b12 / reg.boardings_annual.sum() * 100:.1f}% of that register figure")
rd_nodup.drop(columns=["_row"]).to_csv(os.path.join(CLEAN, "ridership_daily_filed.csv"), index=False)

cal = pd.MultiIndex.from_product([full, modes], names=["date", "mode"]).to_frame(index=False)
cal = cal.merge(rd_nodup.drop(columns=["_row"]), on=["date", "mode"], how="left")
cal["filed"] = cal.boardings.notna()
cal["date"] = cal.date.dt.strftime("%Y-%m-%d")
cal.to_csv(os.path.join(CLEAN, "ridership_daily_clean.csv"), index=False)
say(f"  wrote clean/ridership_daily_clean.csv  (full calendar, {len(cal)} rows)")

# index audit (slide 10), per mode
say("\ntslib.audit_index() per mode, freq D:")
for m in modes:
    s = rd_nodup[rd_nodup["mode"] == m].set_index("date").boardings.sort_index()
    a = tslib.audit_index(s, "D")
    say(f"  {m:6s} dtype_ok={a['dtype_ok']} monotonic={a['monotonic']} dup={a['n_duplicated']} "
        f"missing={a['n_missing']} partial_tail={a['partial_tail']} "
        f"span {a['span'][0][:10]}..{a['span'][1][:10]}")

# =========================================================================
# 4  fare_revenue.csv
# =========================================================================
say("\n" + "=" * 74)
say("FILE 4  fare_revenue.csv  (published fare table)")
say("=" * 74)
fr = pd.read_csv(os.path.join(D, "fare_revenue.csv"))
is_all = fr.ticket_type == "All tickets"
parts = fr[~is_all].copy()
tot = fr[is_all].copy()
say(f"rows {len(fr)}: part rows {len(parts)}, published 'All tickets' rows {len(tot)}")
ps = parts.groupby(["month", "mode"])[["trips", "revenue_pkr"]].sum()
tt = tot.set_index(["month", "mode"])[["trips", "revenue_pkr"]]
diff_t = (ps.trips - tt.trips).abs().max()
diff_r = (ps.revenue_pkr - tt.revenue_pkr).abs().max()
say(f"parts summed vs published 'All tickets': max |diff| journeys {diff_t}, revenue {diff_r}")
say(f"every row summed = {fr.trips.sum() / tt.trips.sum() * 100:.1f}% of journeys; "
    f"{fr.revenue_pkr.sum() / tt.revenue_pkr.sum() * 100:.1f}% of revenue")
say(f"journeys {parts.trips.sum():,}; revenue {parts.revenue_pkr.sum():,} PKR; "
    f"mean fare {parts.revenue_pkr.sum() / parts.trips.sum():.1f} PKR per journey")
decide("fare_revenue", "exclude from sums",
       "published 'All tickets' rows sit beside the Daily, Monthly and Single rows",
       f"summing every row gives {fr.trips.sum() / tt.trips.sum() * 100:.1f}% of journeys",
       "the subtotal is kept for reconciliation only and never added to a part",
       int(is_all.sum()))
parts.to_csv(os.path.join(CLEAN, "fare_revenue_parts.csv"), index=False)
tot.to_csv(os.path.join(CLEAN, "fare_revenue_totals.csv"), index=False)
say("  wrote clean/fare_revenue_parts.csv, clean/fare_revenue_totals.csv")
say(f"  journeys / boardings (12 months to 2026-08) ratio: "
    f"{parts.trips.sum() / max(b12, 1):.3f} over the whole table, "
    f"{parts[(parts.month >= '2025-09') & (parts.month <= '2026-08')].trips.sum() / b12:.3f} for the 12 months")

shutil.copy(os.path.join(D, "regions.geojson"), os.path.join(CLEAN, "regions.geojson"))
say("  copied regions.geojson unchanged")

# =========================================================================
# outputs
# =========================================================================
md = ["# Part A — decisions table (Week 7)", "",
      "One row per decision. **Repair** = a value we can state the true value of, and why. "
      "**Drop** = a row we cannot repair or that does not belong. **Set to missing** = carried "
      "as NaN, not zero. **Exclude** = kept in the file, kept out of sums. **Flag** = kept, "
      "marked. Generated by `partA_process.py`.", "",
      "| # | File | Action | What | How detected | Rule applied | Rows affected |",
      "|---|---|---|---|---|---|---|"]
for x in DECISIONS:
    md.append(f"| {x['id']} | {x['file']} | {x['action']} | {x['what']} | {x['detected']} | "
              f"{x['rule']} | {x['n']} |")
with open(os.path.join(HERE, "partA_decisions.md"), "w") as fh:
    fh.write("\n".join(md) + "\n")
say(f"\nwrote partA_decisions.md with {len(DECISIONS)} decisions")
with open(os.path.join(HERE, "partA_audit.txt"), "w") as fh:
    fh.write("\n".join(_audit) + "\n")
print("wrote partA_audit.txt")
