"""
sessions_clean.py — the Part D cleaning, shared by partB_windows.py and partD_figure.py.

    load_sessions(path)  -> (hourly DataFrame with a real DatetimeIndex, decisions list)

Each decision is a dict: what, detected, rule, rows. The rules, in the order they
must run:

  1. timestamps: two formats; slash rows are day-first (proof: 2,151 rows have a
     first field above 12). Parsed format by format, never format="mixed".
  2. sessions = -1 is the logger's not-available code (290 rows; the same rows
     have orders above sessions). Set to NaN; orders and revenue kept.
  3. device labels: 'mobile', 'MOBILE', 'Mobile' are one class. Normalised first,
     because the case variants hide duplicates from a check that runs before it.
  4. exact duplicate hours: removed, one copy kept (286 hours).
  5. missing hours: left absent, NOT filled. 312 hours = 13 whole days.
  6. the extract ends part-way through September 2025: the last month is partial
     and is flagged, never drawn at full weight.
"""
from __future__ import annotations

import numpy as np
import pandas as pd


def load_sessions(path: str):
    raw = pd.read_csv(path, dtype={"ts": str})
    raw["row"] = np.arange(len(raw))
    decisions = []

    sl = raw.ts.str.contains("/")
    iso = ~sl
    a = raw.loc[sl, "ts"].str.extract(r"(\d+)/(\d+)/(\d+)").astype(int)
    first_gt12 = int((a[0] > 12).sum())
    both_le12 = int(((a[0] <= 12) & (a[1] <= 12)).sum())
    month_first_wrong = int(((a[0] <= 12) & (a[1] <= 12) & (a[0] != a[1])).sum())
    decisions.append(dict(
        what="timestamps written two ways: ISO and DD/MM/YYYY HH:MM",
        detected=f"{int(sl.sum())} slash rows; {first_gt12} have a first field above 12 "
                 f"(cannot be a month); {both_le12} are ambiguous, {month_first_wrong} of which "
                 f"a month-first parse would put on a different day",
        rule="parse each format with its own explicit format string; slash rows day-first. "
             "format='mixed' is never used: it parses every row and silently moves the series",
        rows=int(sl.sum())))

    ts = pd.Series(pd.NaT, index=raw.index, dtype="datetime64[ns]")
    ts[iso] = pd.to_datetime(raw.loc[iso, "ts"], format="%Y-%m-%d %H:%M:%S")
    ts[sl] = pd.to_datetime(raw.loc[sl, "ts"], format="%d/%m/%Y %H:%M")
    assert ts.notna().all(), "unparsed timestamps"
    raw["t"] = ts

    sent = raw.sessions == -1
    decisions.append(dict(
        what="sessions = -1 (logger not-available code)",
        detected=f"{int(sent.sum())} rows; the same rows have orders above sessions "
                 f"({int((raw.orders > raw.sessions).sum())} rows)",
        rule="NaN, not zero. orders and revenue on the row are real and kept",
        rows=int(sent.sum())))
    raw["sessions"] = raw.sessions.where(~sent)

    raw["device"] = raw.device.str.strip().str.lower()
    dev_before = raw.device.nunique()  # distinct labels before normalising
    decisions.append(dict(
        what="device label in three casings (Mobile / mobile / MOBILE)",
        detected="value_counts() shows case variants of the same class",
        rule="lower-case then title-case. Done before the duplicate check, which otherwise "
             "fails to see identical hours",
        rows=int(dev_before)))  # label variants collapsed to 3 classes
    raw["device"] = raw.device.str.title()

    key = ["t", "sessions", "orders", "revenue_pkr", "device"]
    dup = raw.duplicated("t", keep=False)
    n_dup_hours = int(raw.loc[raw.duplicated("t"), "t"].nunique())
    exact_hours = raw[dup].groupby("t").apply(
        lambda g: g[["sessions", "orders", "revenue_pkr", "device"]].nunique(dropna=False).max() <= 1,
        include_groups=False)
    decisions.append(dict(
        what="the same hour filed twice",
        detected=f"{n_dup_hours} hours appear twice; {int(exact_hours.sum())} of them are identical in every "
                 f"field once the device label is normalised",
        rule="keep the first copy. Only exact copies are dropped; a conflicting pair would have stopped the run",
        rows=int(raw.duplicated("t").sum())))
    assert exact_hours.all(), "conflicting duplicate hours found: decide before continuing"
    h = raw.drop_duplicates("t", keep="first").set_index("t").sort_index()

    full = pd.date_range(h.index.min(), h.index.max(), freq="h")
    gaps = full.difference(h.index)
    gap_days = sorted(set(gaps.normalize()))
    decisions.append(dict(
        what="hours nobody filed",
        detected=f"{len(gaps)} hours on {len(gap_days)} whole days out of "
                 f"{(h.index.max() - h.index.min()).days + 1} days",
        rule="left absent (NaN in any resample), never filled. Whole missing days are reported, "
             "not averaged over",
        rows=int(len(gaps))))
    h = h.reindex(full)
    h.index.name = "t"

    last_day = h.index.max()
    partial = h.index[h.index.to_period("M") == last_day.to_period("M")]
    decisions.append(dict(
        what="the extract ends part-way through a month",
        detected=f"last filed hour {last_day}; {last_day.to_period('M')} has "
                 f"{h.loc[h.index.to_period('M') == last_day.to_period('M')].sessions.notna().sum()} filed hours",
        rule="the final month is labelled partial and never drawn at full weight",
        rows=int(len(partial))))
    return h, decisions, gap_days, last_day


# ------------------------------------------------------------------ daily
ANALYSIS_END = pd.Timestamp("2025-08-31")  # Sep 2025 is partial: excluded from analysis


def daily_series(h: pd.DataFrame, min_hours: int = 21):
    """
    Resample the cleaned hourly flow to a regular daily series.

    Rule (declared, applied once, here):
      - sessions is a FLOW, so the day total is a SUM of its filed hours;
      - a day needs at least `min_hours` of its 24 hours filed. Days with fewer,
        and the 13 whole missing days, are NaN and break the line;
      - a day with 21-23 filed hours is scaled by 24 / filed_hours, because the
        missing hours are not spread evenly across the day. The scaling is
        recorded in the `scaled` column and its effect is reported in partB.

    Returns a DataFrame indexed by a complete daily calendar with columns
    sessions (day total, NaN if not usable), filed_hours, scaled.
    """
    g = h.sessions.groupby(h.index.normalize())
    filed = g.count()
    total = g.sum()
    cal = pd.date_range(h.index.min().normalize(), h.index.max().normalize(), freq="D")
    filed = filed.reindex(cal, fill_value=0)
    total = total.reindex(cal)
    ok = filed >= min_hours
    scaled_total = total * 24 / filed.where(filed > 0)
    out = pd.DataFrame({
        "sessions": scaled_total.where(ok),
        "filed_hours": filed,
        "scaled": (filed < 24) & ok,
    }, index=cal)
    out.index.name = "day"
    return out


def analysis_daily(h: pd.DataFrame, min_hours: int = 21) -> pd.Series:
    """The daily series used for analysis: complete days only, Sep 2025 excluded."""
    d = daily_series(h, min_hours)
    return d.loc[:ANALYSIS_END, "sessions"]


# ------------------------------------------------------------------ catalogue
def load_catalogue(path: str):
    """
    The hierarchy, cleaned for the treemap and the shares check.

    Rules:
      - SKU-0127 is filed twice, under Audio and under Wearables, with identical
        values. Its sku_name is AUDI-04, so the Audio row is kept and the
        Wearables row dropped (keep='first' after sorting by the name prefix).
      - Negative net-revenue rows (returns above sales) are kept inside their
        sub-category total so the totals reconcile with shares_eight.csv, and are
        reported separately; no leaf in the treemap is negative.
    Returns (catalogue, decisions).
    """
    c = pd.read_csv(path)
    decisions = []
    dup = c.sku.duplicated(keep=False)
    dup_rows = c[dup]
    # keep the Audio copy: the name prefix AUDI matches the Audio sub-category
    keep_mask = ~(dup & (c.subcategory != "Audio") & c.sku_name.str.startswith("AUDI"))
    dropped = c[~keep_mask]
    decisions.append(dict(
        what="SKU filed under two sub-categories",
        detected=f"{len(dup_rows)//2} SKU ({', '.join(sorted(set(dup_rows.sku)))}) appears twice "
                 f"with identical values; sku_name {', '.join(sorted(set(dup_rows.sku_name)))}",
        rule="keep the Audio row (name prefix AUDI matches Audio); drop the Wearables copy",
        rows=int(len(dropped))))
    c = c[keep_mask].copy()
    neg = c[c.net_revenue_pkr_m < 0]
    decisions.append(dict(
        what="negative net revenue (returns exceed sales)",
        detected=f"{len(neg)} SKU rows, total {neg.net_revenue_pkr_m.sum():.4f} PKR m",
        rule="kept inside sub-category totals so they reconcile with shares_eight.csv; "
             "no negative leaf is drawn; each row listed in partD note",
        rows=int(len(neg))))
    return c, decisions, neg
