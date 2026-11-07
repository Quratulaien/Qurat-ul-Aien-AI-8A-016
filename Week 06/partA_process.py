#!/usr/bin/env python3
"""
partA_process.py — raw -> audit -> clean/

Reads the three raw CSVs and the GeoJSON from data/, prints an audit, applies
the decision rules listed in partA_decisions.md, and writes cleaned copies to
clean/. The raw files are never written to. Run from anywhere:

    python3 partA_process.py

Writes:
    partA_audit.txt       the printed audit, verbatim
    partA_decisions.md    one row per decision: what, how detected, rule, rows
    clean/district_grid_clean.csv
    clean/grid_daily_clean.csv        full calendar, one row per zone-day
    clean/generation_mix_parts.csv    the 144 part rows
    clean/generation_mix_totals.csv   the 18 published total rows (not summed)
    clean/regions.geojson             unchanged copy, checked for joins
"""
from __future__ import annotations

import os
import sys

import numpy as np
import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import geolib  # noqa: E402  (exact spherical area, for the join audit)

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


# =========================================================================
# FILE 1 — district_grid.csv
# =========================================================================
say("=" * 74)
say("FILE 1  district_grid.csv  (district register, one row per district)")
say("=" * 74)

raw_r = pd.read_csv(os.path.join(D, "district_grid.csv"), dtype=str)
raw_r["_row"] = np.arange(len(raw_r))
say(f"rows read {len(raw_r)}, columns {len(raw_r.columns) - 1}, "
    f"all read as text so nothing is coerced silently")

say("\nkey uniqueness (code)")
say(f"  distinct codes {raw_r.code.nunique()} in {len(raw_r)} rows")
dupe_codes = raw_r.code[raw_r.code.duplicated(keep=False)].unique()
for c in dupe_codes:
    sub = raw_r[raw_r.code == c]
    say(f"  DUPLICATE {c}: rows " + ", ".join(
        f"line {r + 2} '{n}'" for r, n in zip(sub._row, sub.district)))

say("\nnon-numeric and blank values, per numeric column")
num_cols_r = ["population", "households", "area_km2", "lon", "lat",
              "income_pc_usd", "electrification_pct", "solar_kw_installed",
              "outages", "outage_minutes"]
for c in num_cols_r:
    as_num = pd.to_numeric(raw_r[c], errors="coerce")
    bad = raw_r.loc[as_num.isna() & raw_r[c].notna(), c].tolist()
    blank = int(raw_r[c].isna().sum())
    say(f"  {c:20s} blank={blank}  not-a-number={bad}")

say("\njoin audit against regions.geojson")
feats = geolib.read_geojson(os.path.join(D, "regions.geojson"))
gname = {f["code"]: f["name"] for f in feats}
gcodes = set(gname)
say(f"  GeoJSON features {len(feats)}, distinct codes {len(gcodes)}")
say(f"  register rows whose code is in GeoJSON (as filed): "
    f"{int(raw_r.code.isin(gcodes).sum())} of {len(raw_r)} rows, "
    f"{len(set(raw_r.code) & gcodes)} of {len(gcodes)} distinct codes")
say(f"  register codes missing from GeoJSON: {sorted(set(raw_r.code) - gcodes)}")

# ---- cleaning ----------------------------------------------------------
reg = raw_r.copy()

# R1 duplicate key -------------------------------------------------------
# Keep the row whose name matches the boundary file; then first in file order.
reg["_name_ok"] = reg.district == reg.code.map(gname)
reg = reg.sort_values(["code", "_name_ok", "_row"], ascending=[True, False, True])
kept_r1 = reg.drop_duplicates("code", keep="first")
dropped_r1 = reg[~reg._row.isin(kept_r1._row)]
for _, d in dropped_r1.iterrows():
    keep = kept_r1[kept_r1.code == d.code].iloc[0]
    diffs = {c: (keep[c], d[c]) for c in ["district", "population", "households",
             "outages", "outage_minutes", "solar_kw_installed"]
             if keep[c] != d[c]}
    say(f"\nR1 dropping line {d._row + 2} '{d.district}' — duplicate of "
        f"'{keep.district}' (kept). Fields that differ (kept, dropped): {diffs}")
    decide("district_grid", "drop",
           f"duplicate register row {d.code} '{d.district}'",
           f"same code as '{keep.district}' on the line above; GeoJSON names "
           f"the district '{gname[d.code]}'",
           f"duplicate key: keep the row whose name matches the boundary file; "
           f"the other is dropped. Its {', '.join(diffs)} disagree with the kept row "
           f"— reported, not averaged",
           len(dropped_r1))
reg = kept_r1.sort_values("_row").copy()
say(f"  after R1: {len(reg)} rows, {reg.code.nunique()} distinct codes")

# R2 percent sign inside a numeric field ---------------------------------
pct_mask = reg.electrification_pct.fillna("").str.endswith("%")
say(f"\nR2 electrification_pct carries a literal '%': "
    f"{reg.loc[pct_mask, 'code'].tolist()} ({int(pct_mask.sum())} rows)")
reg["electrification_pct"] = pd.to_numeric(
    reg.electrification_pct.str.replace("%", "", regex=False), errors="coerce")
for c in ["area_km2", "lon", "lat", "income_pc_usd", "solar_kw_installed", "outages"]:
    reg[c] = pd.to_numeric(reg[c])
decide("district_grid", "repair",
       "electrification_pct written as text with a '%' sign",
       "to_numeric() failed on these fields; the number is intact",
       "strip the '%' and keep the value", int(pct_mask.sum()))

# R3 genuinely blank electrification -------------------------------------
blank_elec = reg.electrification_pct.isna()
say(f"R3 electrification_pct blank (missing, not zero): "
    f"{reg.loc[blank_elec, 'code'].tolist()}")
decide("district_grid", "flag as missing",
       "electrification_pct blank",
       "field is empty in the file",
       "left as NaN. A blank is not a 0% connection rate; the chart has to say so",
       int(blank_elec.sum()))

# R4 sentinel -1 in outage_minutes ---------------------------------------
om = pd.to_numeric(reg.outage_minutes)
sent = om < 0
say(f"R4 outage_minutes negative (sentinel): {reg.loc[sent, 'code'].tolist()} "
    f"values {om[sent].tolist()}")
reg["outage_minutes"] = om.where(~sent)
decide("district_grid", "set to missing",
       "outage_minutes = -1 (not a duration)",
       "negative minutes cannot happen; -1 is the operator's not-available code",
       "NaN, not 0 and not a mean. The same district's outages count is kept, "
       "because it is a separate measurement",
       int(sent.sum()))

# R5 households typed without its thousands --------------------------------
reg["households"] = pd.to_numeric(reg.households)
reg["population"] = pd.to_numeric(reg.population)
reg["pph"] = reg.population / reg.households
median_pph = reg.pph.median()
flag_pph = reg.pph > 3 * median_pph
say(f"R5 persons per household (register median {median_pph:.2f}); "
    f"flagged above 3x median: {reg.loc[flag_pph, 'code'].tolist()} "
    f"at {reg.loc[flag_pph, 'pph'].round(0).tolist()} people per household")
ok_band = (reg.pph[~flag_pph].min(), reg.pph[~flag_pph].max())
for i in reg.index[flag_pph]:
    trial = reg.at[i, "households"] * 1000
    trial_pph = reg.at[i, "population"] / trial
    accept = ok_band[0] <= trial_pph <= ok_band[1]
    say(f"  {reg.at[i, 'code']} households {int(reg.at[i, 'households'])} x 1000 = "
        f"{int(trial):,} -> {trial_pph:.2f} persons per household; "
        f"band of the other 23 is {ok_band[0]:.2f}-{ok_band[1]:.2f}; "
        f"{'repaired' if accept else 'NOT repaired'}")
    if accept:
        reg.at[i, "households"] = trial
        decide("district_grid", "repair",
               f"households {reg.at[i, 'code']} '{reg.at[i, 'district']}' = "
               f"{int(trial / 1000)} (should be {int(trial):,})",
               f"as filed, {int(trial / 1000)} households gives "
               f"{reg.at[i, 'pph']:,.0f} people per household; the other 23 are "
               f"{ok_band[0]:.2f}–{ok_band[1]:.2f}",
               f"the three leading digits were filed without the thousands; "
               f"repaired to {int(trial):,}, which lands inside the band",
               1)
reg["pph"] = reg.population / reg.households
say(f"  persons per household after repair: min {reg.pph.min():.2f}, "
    f"max {reg.pph.max():.2f}")

# derived ranges for the audit ---------------------------------------------
reg["interruption_min"] = reg.outage_minutes / reg.outages
say("\nranges of anything we divide by (after cleaning)")
for c in ["population", "households", "outages"]:
    say(f"  {c:12s} min {reg[c].min():>12,.0f}  max {reg[c].max():>12,.0f}")
say(f"  electrification_pct: min {reg.electrification_pct.min():.1f}, "
    f"max {reg.electrification_pct.max():.1f}, usable {int(reg.electrification_pct.notna().sum())}")
say(f"  outage_minutes usable rows {int(reg.outage_minutes.notna().sum())} of {len(reg)}; "
    f"mean interruption {reg.interruption_min.min():.0f}–{reg.interruption_min.max():.0f} min")
say(f"  totals: population {int(reg.population.sum()):,}; households "
    f"{int(reg.households.sum()):,}; interruptions {int(reg.outages.sum()):,}")
say(f"  population with the duplicate row also summed: "
    f"{int(raw_r.assign(p=pd.to_numeric(raw_r.population)).p.sum()):,} "
    f"(the extra row adds {int(dropped_r1.population.astype(float).sum()):,}, "
    f"so this is the figure to hold, not a surprise)")

# area check against geometry ------------------------------------------------
area_geo = {f["code"]: geolib.polygon_area_km2(f["ring"]) for f in feats}
dev = max(abs(area_geo[c] - float(reg.loc[reg.code == c, "area_km2"].iloc[0]))
          / area_geo[c] for c in reg.code)
say(f"  area_km2 vs polygon area from geometry: max relative deviation {dev:.2%}")

reg_out = reg.drop(columns=["_row", "_name_ok", "pph", "interruption_min"])
reg_out.to_csv(os.path.join(CLEAN, "district_grid_clean.csv"), index=False)
say(f"  wrote clean/district_grid_clean.csv  ({len(reg_out)} rows)")
joined = reg_out.code.isin(gcodes).sum()
say(f"  join after cleaning: {joined} of {len(reg_out)} register rows matched, "
    f"{len(gcodes - set(reg_out.code))} GeoJSON features unmatched")

# =========================================================================
# FILE 2 — grid_daily.csv
# =========================================================================
say("\n" + "=" * 74)
say("FILE 2  grid_daily.csv  (daily meter readings, one row per zone per day)")
say("=" * 74)

raw_g = pd.read_csv(os.path.join(D, "grid_daily.csv"), dtype=str)
raw_g["_row"] = np.arange(len(raw_g))
say(f"rows read {len(raw_g)}, zones {sorted(raw_g.zone.unique())}")

is_iso = raw_g.date.str.fullmatch(r"\d{4}-\d{2}-\d{2}").fillna(False).astype(bool)
is_slash = raw_g.date.str.fullmatch(r"\d{2}/\d{2}/\d{4}").fillna(False).astype(bool)
say(f"\ndate formats: ISO YYYY-MM-DD {int(is_iso.sum())} rows, "
    f"DD/MM/YYYY {int(is_slash.sum())} rows, other {int((~is_iso & ~is_slash).sum())}")
sp = raw_g.loc[is_slash, "date"].str.split("/", expand=True).astype(int)
first_gt12 = int((sp[0] > 12).sum())
second_gt12 = int((sp[1] > 12).sum())
both_le12 = (sp[0] <= 12) & (sp[1] <= 12)
silent = int((both_le12 & (sp[0] != sp[1])).sum())
say(f"  slash rows whose FIRST field exceeds 12 (cannot be a month): {first_gt12}")
say(f"  slash rows whose SECOND field exceeds 12 (cannot be a day): {second_gt12}")
say(f"  slash rows where both fields are <= 12 (ambiguous): {int(both_le12.sum())}")
say(f"  of those, month-first would silently give a different real day: {silent}")
say(f"  => the file's slash convention is day-first (evidence: {first_gt12} rows, "
    f"zero contrary)")
d_parsed = pd.Series(pd.NaT, index=raw_g.index, dtype="datetime64[ns]")
d_parsed[is_iso] = pd.to_datetime(raw_g.loc[is_iso, "date"], format="%Y-%m-%d")
d_parsed[is_slash] = pd.to_datetime(raw_g.loc[is_slash, "date"], format="%d/%m/%Y")
assert d_parsed.notna().all(), "unparsed dates remain"
say(f"  parsed range {d_parsed.min().date()} -> {d_parsed.max().date()}, "
    f"unparsed {int(d_parsed.isna().sum())}")
decide("grid_daily", "repair",
       "dates written DD/MM/YYYY alongside the ISO majority",
       f"{first_gt12} rows have a first field above 12; a month-first parse "
       f"fails on them and silently misdates {silent} more",
       "parse the slash rows day-first, the ISO rows as ISO; no row dropped",
       int(is_slash.sum()))

cum = pd.to_numeric(raw_g.cumulative_mwh, errors="coerce")
peak = pd.to_numeric(raw_g.peak_load_mw, errors="coerce")
outg = pd.to_numeric(raw_g.outage_minutes, errors="coerce")
say(f"\nnumeric check: cumulative_mwh not-a-number {int(cum.isna().sum())}, "
    f"peak_load_mw {int(peak.isna().sum())}, outage_minutes {int(outg.isna().sum())}")

sent_peak = peak <= 0
say(f"peak_load_mw sentinel (<= 0): {int(sent_peak.sum())} rows, values "
    f"{sorted(set(peak[sent_peak].tolist()))}")
peak = peak.where(~sent_peak)
decide("grid_daily", "set to missing",
       "peak_load_mw = -1, the SCADA not-available code",
       "negative megawatts cannot happen; every value is -1",
       "NaN. Peak is a maximum, so there is no mean or sum to fall back on",
       int(sent_peak.sum()))

df = pd.DataFrame({"_row": raw_g._row, "date": d_parsed, "zone": raw_g.zone,
                   "cum": cum, "peak": peak, "outage": outg})
key_dup = df.duplicated(["date", "zone"], keep=False)
grp = df[key_dup].groupby(["date", "zone"])
n_keys = grp.ngroups
exact_groups = grp.apply(lambda g: g[["cum", "peak", "outage"]].nunique(dropna=False).max() == 1,
                         include_groups=False)
n_exact_keys = int(exact_groups.sum())
n_conflict_keys = int((~exact_groups).sum())
say(f"\nduplicate (date, zone) keys: {n_keys}  "
    f"(identical on every field: {n_exact_keys}; disagreeing: {n_conflict_keys})")
cum_disagree = int((grp.cum.nunique(dropna=False) > 1).sum())
say(f"  of which the MWh meter reading disagrees: {cum_disagree}")
for (dt, z), g in grp:
    if g[["cum", "peak", "outage"]].nunique(dropna=False).max() > 1:
        say(f"  conflict {dt.date()} {z}: " + "; ".join(
            f"line {int(r) + 2}: peak {p}, outage {o}"
            for r, p, o in zip(g._row, g.peak, g.outage)))

# keep rule: highest peak wins (peak is a maximum, so the filing that saw more
# of the day holds the larger value), exact duplicates collapse to one, and
# the whole record is kept from one filing, never a mix of two.
df["_pk"] = df.peak.fillna(-np.inf)
df = df.sort_values(["date", "zone", "_pk", "_row"], ascending=[True, True, False, True])
kept_g = df.drop_duplicates(["date", "zone"], keep="first").copy()
n_dropped_g = len(df) - len(kept_g)
decide("grid_daily", "drop",
       "duplicate zone-day filings",
       f"{n_keys} (date, zone) keys appear twice",
       "keep one filing per key. Identical filings: keep either. Disagreeing "
       "filings (peak and outage differ, meter reading does not): keep the "
       "filing with the higher peak, because a maximum seen over more of the "
       "day is the better estimate, and never mix fields across the two",
       n_dropped_g)
say(f"  kept {len(kept_g)} rows after de-duplication, dropped {n_dropped_g}")

# meter rules ----------------------------------------------------------------
kept_g = kept_g.sort_values(["zone", "date"]).reset_index(drop=True)
kept_g["prev_date"] = kept_g.groupby("zone").date.shift()
kept_g["prev_cum"] = kept_g.groupby("zone").cum.shift()
kept_g["span_days"] = (kept_g.date - kept_g.prev_date).dt.days
kept_g["energy_mwh"] = kept_g.cum - kept_g.prev_cum
no_base = kept_g.prev_cum.isna()
reset = kept_g.energy_mwh < 0
say(f"\nmeter: first reading of each zone, no baseline -> no energy: "
    f"{int(no_base.sum())} rows")
say(f"meter: readings that go DOWN: {int(reset.sum())} row(s):")
for _, r in kept_g[reset].iterrows():
    say(f"  {r.zone} {r.date.date()}: reading {r.cum:,.1f} after {r.prev_cum:,.1f} "
        f"on {r.prev_date.date()} (a new meter, or a reset)")
kept_g.loc[reset, "energy_mwh"] = np.nan
decide("grid_daily", "set to missing",
       "meter reading falls: " + ", ".join(
           f"{z} {d.date()}" for z, d in zip(kept_g[reset].zone, kept_g[reset].date)),
       f"cumulative reading {kept_g.loc[reset, 'cum'].iloc[0]:,.0f} MWh is below the "
       f"previous day's {kept_g.loc[reset, 'prev_cum'].iloc[0]:,.0f} MWh; an energy meter "
       f"cannot run backwards",
       "energy for that day is undefined: NaN. The new reading is kept as the baseline "
       "for the next day, so the following day's energy is valid",
       int(reset.sum()))
no_base_n = int(no_base.sum())

# calendar -----------------------------------------------------------------
start, end = kept_g.date.min(), kept_g.date.max()
days = pd.date_range(start, end, freq="D")
zones = sorted(kept_g.zone.unique())
full = pd.MultiIndex.from_product([days, zones], names=["date", "zone"])
rep_idx = pd.MultiIndex.from_arrays([kept_g.date, kept_g.zone])
calendar = pd.DataFrame(index=full).reset_index()
calendar["reported"] = pd.Series(list(zip(calendar.date, calendar.zone))).isin(
    list(zip(kept_g.date, kept_g.zone))).values
merged = calendar.merge(kept_g[["date", "zone", "cum", "energy_mwh", "span_days", "peak", "outage"]],
                        on=["date", "zone"], how="left")
merged = merged.rename(columns={"cum": "cumulative_mwh", "peak": "peak_load_mw",
                                "outage": "outage_minutes"})
merged["meter_reset"] = merged.set_index(["date", "zone"]).index.isin(
    list(zip(kept_g.loc[reset, "date"], kept_g.loc[reset, "zone"])))
n_slots = len(days) * len(zones)
n_missing = int((~merged.reported).sum())
say(f"\ncalendar: {start.date()} -> {end.date()} = {len(days)} days x {len(zones)} zones "
    f"= {n_slots} slots")
say(f"  reported zone-days {int(merged.reported.sum())}, never reported {n_missing}")
gaps = kept_g.assign(gap=kept_g.span_days - 1).query("gap>0")
say(f"  zone-day gaps: {len(gaps)} breaks, longest {int(gaps.gap.max())} days")
miss_by_zone = merged[~merged.reported].zone.value_counts().sort_index().to_dict()
say(f"  missing by zone: {miss_by_zone}")
decide("grid_daily", "flag as missing",
       "zone-days nobody filed",
       f"the calendar {start.date()}–{end.date()} has {n_slots} slots; "
       f"{int(merged.reported.sum())} are filed",
       "left absent (NaN), not zero and not interpolated. Energy across a gap is "
       "the difference of two readings, so the energy is still counted once; "
       "span_days records how many days it covers",
       n_missing)
decide("grid_daily", "derive",
       "cumulative meter reading converted to energy",
       "the file says the reading is a running total from installation",
       "energy = today's reading minus the last filed reading; never sum() the "
       "reading, which overstates energy by the number of days in the window",
       int(merged.energy_mwh.notna().sum()))

# index audit, slide 10, run per zone on the filed days ----------------------
import tslib  # noqa: E402
say("\ntslib.audit_index() per zone, on the filed days (freq D):")
for z in zones:
    s = (kept_g[kept_g.zone == z].set_index("date").cum)
    a = tslib.audit_index(s, "D")
    say(f"  {z}: dtype_ok={a['dtype_ok']} monotonic={a['monotonic']} "
        f"duplicated={a['n_duplicated']} missing_days={a['n_missing']} "
        f"partial_tail={a['partial_tail']} span={a['span'][0][:10]}..{a['span'][1][:10]}")
s_all = kept_g.groupby("date").size()
a_all = tslib.audit_index(s_all, "D")
say(f"  any zone filed on the day: {len(s_all)} of {len(days)} days; "
    f"days with no filing from any zone: {a_all['n_missing']}; "
    f"days where fewer than 6 zones filed: {int((s_all < 6).sum())}")

# the June 2026 anchor, computed both ways ---------------------------------
def energy_between(zone, start_day, end_day):
    z = kept_g[kept_g.zone == zone]
    hi = z[z.date <= end_day].iloc[-1]
    lo = z[z.date <= start_day].iloc[-1]
    return hi.cum - lo.cum, hi.date.date(), lo.date.date()

e_jun, hi_d, lo_d = energy_between("P1", pd.Timestamp("2026-05-31"), pd.Timestamp("2026-06-30"))
say(f"\nenergy delivered in P1, June 2026 = reading {hi_d} minus reading {lo_d}: "
    f"{e_jun:,.0f} MWh")
say(f"  the same month if you sum() the cumulative column: "
    f"{kept_g[(kept_g.zone == 'P1') & (kept_g.date.dt.month == 6) & (kept_g.date.dt.year == 2026)].cum.sum():,.0f} MWh"
    f"  (the wrong answer, shown for the record)")

# peak summary -----------------------------------------------------------
say(f"\npeak_load_mw usable {int(merged.peak_load_mw.notna().sum())} of {len(merged)} "
    f"filed slots (missing from sentinel: {int(sent_peak.sum())})")
say(f"outage_minutes usable {int(merged.outage_minutes.notna().sum())}; "
    f"zero-minute days {int((merged.outage_minutes == 0).sum())} (kept: a day with "
    f"no interruption is a real zero, not a code)")

merged_out = merged.copy()
merged_out["date"] = merged_out.date.dt.strftime("%Y-%m-%d")
merged_out["reported"] = merged_out.reported.astype(bool)
merged_out["meter_reset"] = merged_out.meter_reset.astype(bool)
merged_out.to_csv(os.path.join(CLEAN, "grid_daily_clean.csv"), index=False)
say(f"  wrote clean/grid_daily_clean.csv  ({len(merged_out)} rows, full calendar)")

# =========================================================================
# FILE 3 — generation_mix.csv
# =========================================================================
say("\n" + "=" * 74)
say("FILE 3  generation_mix.csv  (monthly generation, published hierarchy)")
say("=" * 74)
gm = pd.read_csv(os.path.join(D, "generation_mix.csv"))
say(f"rows {len(gm)}, months {gm.month.nunique()}, rows per month "
    f"{sorted(gm.groupby('month').size().unique().tolist())}")
is_total = (gm.source == "All sources") & (gm.subsource == "Total")
totals = gm[is_total].set_index("month").mwh
parts = gm[~is_total].copy()
say(f"published 'All sources / Total' rows: {int(is_total.sum())}; part rows: {len(parts)}")
dup_parts = parts.duplicated(["month", "subsource"]).sum()
say(f"each unit in exactly one part per month: duplicate (month, subsource) = {dup_parts}")
ps = parts.groupby("month").mwh.sum()
diff = (ps - totals)
say(f"parts summed vs published total: max |difference| {diff.abs().max():,.0f} MWh "
    f"(rounding; tolerance 2 MWh)")
say(f"every row summed (what the file says if you sum it all): "
    f"{gm.mwh.sum() / totals.sum() * 100:.1f}% of the true generation")
say(f"ranges: monthly total min {totals.min():,.0f}, max {totals.max():,.0f} MWh")
assert dup_parts == 0 and diff.abs().max() <= 2

decide("generation_mix", "exclude from sums",
       "published 'All sources / Total' rows sit in the same column as the parts",
       f"summing every row gives {gm.mwh.sum() / totals.sum() * 100:.1f}% of the generation",
       "a row that is itself the sum of other rows is kept for reconciliation only "
       "(clean/generation_mix_totals.csv) and never added to a part-to-whole",
       int(is_total.sum()))
decide("generation_mix", "check",
       "parts reconcile to the published total",
       "parts summed vs published total, every month",
       f"accept if within 2 MWh of rounding; observed max {diff.abs().max():,.0f} MWh, "
       f"so the eight categories are exhaustive and mutually exclusive",
       len(totals))

parts["share_of_total_pct"] = parts.mwh / parts.month.map(totals) * 100
parts.to_csv(os.path.join(CLEAN, "generation_mix_parts.csv"), index=False)
gm[is_total].to_csv(os.path.join(CLEAN, "generation_mix_totals.csv"), index=False)
say(f"  wrote clean/generation_mix_parts.csv ({len(parts)} rows) and "
    f"clean/generation_mix_totals.csv ({int(is_total.sum())} rows)")

# =========================================================================
# GeoJSON copy, decisions table, audit file
# =========================================================================
import shutil  # noqa: E402
shutil.copy(os.path.join(D, "regions.geojson"), os.path.join(CLEAN, "regions.geojson"))
say("  copied regions.geojson unchanged to clean/ (no geometry defect found)")

# =========================================================================
# write the decisions table and the audit
# =========================================================================
md = ["# Part A — decisions table", "",
      "One row per decision. **Repair** = a value we can state the true value of, and why. "
      "**Drop** = a row we cannot repair. **Set to missing** = carried as NaN, not zero. "
      "**Exclude** = kept in the file, kept out of sums. Generated by `partA_process.py`; "
      "the counts are the ones the script printed.", "",
      "| # | File | Action | What | How detected | Rule applied | Rows affected |",
      "|---|---|---|---|---|---|---|"]
for d in DECISIONS:
    md.append(f"| {d['id']} | {d['file']} | {d['action']} | {d['what']} | {d['detected']} | "
              f"{d['rule']} | {d['n']} |")
with open(os.path.join(HERE, "partA_decisions.md"), "w") as fh:
    fh.write("\n".join(md) + "\n")
say(f"\nwrote partA_decisions.md with {len(DECISIONS)} decisions")

with open(os.path.join(HERE, "partA_audit.txt"), "w") as fh:
    fh.write("\n".join(_audit) + "\n")
print("wrote partA_audit.txt")
