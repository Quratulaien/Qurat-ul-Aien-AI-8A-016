#!/usr/bin/env python3
"""
partD_figure.py — Part D: the e-commerce review figure, one 2x2 panel.

    python3 partD_figure.py

Writes partD_figure.png (300 dpi), partD_decisions.md (every cleaning rule with its
count), partD_audit.txt (the index audit output), and prints every number the titles use.

Panels
  1  daily sessions: raw grey, centred 7-day mean on top (window named)
  2  day-of-week x hour-of-day heatmap of mean sessions, sequential colormap
  3  treemap of category -> sub-category net revenue (one hue per category)
  4  the same eight sub-categories as sorted horizontal bars, values printed
"""
from __future__ import annotations

import os
import sys

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import sessions_clean as sc  # noqa: E402
import tslib  # noqa: E402
from vizlib import PALETTE, style_defaults, save_fig  # noqa: E402

D = os.path.join(HERE, "data")
style_defaults()
C = PALETTE
WINDOW = 7  # from partB Q1: the weekly cycle

# ------------------------------------------------------------- load and clean
h, decisions, gap_days, last_day = sc.load_sessions(os.path.join(D, "sessions_hourly.csv"))
daily_full = sc.daily_series(h)
daily = sc.analysis_daily(h)  # complete days only, Sep 2025 excluded
hourly = h.loc[:sc.ANALYSIS_END]
cat, cat_dec, neg = sc.load_catalogue(os.path.join(D, "revenue_catalogue.csv"))

# ------------------------------------------------------------- numbers for titles
roll = daily.rolling(WINDOW, center=True, min_periods=5).mean()
monthly = daily.dropna().resample("MS").mean()
m_first, m_last = monthly.iloc[0], monthly.iloc[-1]

hs = hourly.sessions.dropna()
dow = hs.groupby(hs.index.dayofweek).mean()
wk = dow.loc[:4].mean()
we = dow.loc[5:].mean()
weekend_pct = (we / wk - 1) * 100
grid = hs.groupby([hs.index.dayofweek, hs.index.hour]).mean().unstack()
pk = grid.stack().idxmax()
pk_day = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"][pk[0]]
pk_hour = pk[1]

sub = cat.groupby(["category", "subcategory"]).net_revenue_pkr_m.sum().reset_index()
total_net = sub.net_revenue_pkr_m.sum()
sub["share"] = sub.net_revenue_pkr_m / total_net * 100
sub = sub.sort_values("net_revenue_pkr_m", ascending=False).reset_index(drop=True)
assert (sub.net_revenue_pkr_m > 0).all(), "a sub-category total is negative: cannot be drawn as area"
ref = pd.read_csv(os.path.join(D, "shares_eight.csv")).set_index("subcategory").share_pct
chk = sub.set_index("subcategory").share.reindex(ref.index)
max_dev = float((chk - ref).abs().max())
assert max_dev <= 0.3, f"shares differ from shares_eight.csv by {max_dev:.2f} points"

# hierarchy must be a tree: each sub-category one parent, children sum to parent
assert cat.groupby("subcategory").category.nunique().max() == 1
cat_tot = cat.groupby("category").net_revenue_pkr_m.sum()
assert abs(cat_tot.sum() - sub.net_revenue_pkr_m.sum()) < 1e-6

# "Other": how many sub-categories fall under 1%? (declared, not hidden)
other_series, other_note = tslib.rollup_other(sub.set_index("subcategory").net_revenue_pkr_m, min_share_pct=1.0)

# ------------------------------------------------------------- figure
fig, axs = plt.subplots(2, 2, figsize=(15, 11))
ax1, ax2, ax3, ax4 = axs.ravel()

# Panel 1 — raw grey, window named
ax1.plot(daily.index, daily.values, color="#b8bec6", linewidth=0.8, label="raw day")
ax1.plot(roll.index, roll.values, color=C["series"][0], linewidth=2.2, label=f"centred {WINDOW}-day mean")
ax1.set_ylim(0, daily.max() * 1.1)
ax1.set_ylabel("Sessions per day (sum of filed hours)")
ax1.set_xlabel("Day")
ax1.yaxis.set_major_formatter(matplotlib.ticker.StrMethodFormatter("{x:,.0f}"))
ax1.legend(fontsize=8, loc="upper left", frameon=False)
ax1.set_title(f"Sessions per day rose from {m_first:,.0f} (Apr 2024) to {m_last:,.0f} (Aug 2025)",
              loc="left", fontsize=10)

# Panel 2 — heatmap, sequential
im = ax2.imshow(grid.values, aspect="auto", cmap="Blues", origin="upper")
ax2.set_yticks(range(7))
ax2.set_yticklabels(["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"])
ax2.set_xticks(range(0, 24, 3))
ax2.set_xticklabels([f"{x:02d}:00" for x in range(0, 24, 3)], fontsize=8)
ax2.set_xlabel("Hour of day (start of hour)")
for s in ["top", "right", "left", "bottom"]:
    ax2.spines[s].set_visible(False)
cb = fig.colorbar(im, ax=ax2, fraction=0.035, pad=0.02)
cb.set_label("Mean sessions per hour", fontsize=8)
ax2.set_title(f"Weekend hours carry {weekend_pct:.0f}% more sessions than weekday hours; "
              f"the peak is {pk_day} {pk_hour:02d}:00", loc="left", fontsize=10)

# Panel 3 — treemap, one hue per category, children are shades of the parent hue
hues = {"Mobile": C["series"][0], "Computing": C["series"][1],
        "Audio & Imaging": C["series"][2], "Lifestyle": C["series_4th"]}
def shade(hexcol, k, n):
    """Children of one parent: the parent hue, from full strength down to lighter, so
    the hue still says which category a block belongs to."""
    import matplotlib.colors as mc
    r, g, b = mc.to_rgb(hexcol)
    t = 1.0 - 0.35 * (k / max(n - 1, 1))  # 1.0 for the largest child, 0.65 for the smallest
    return (r * t, g * t, b * t)
colors, labels, vals = [], [], []
for _, row in sub.iterrows():
    siblings = sub[sub.category == row.category].index.tolist()
    k = siblings.index(_)
    colors.append(shade(hues[row.category], k, len(siblings)))
    labels.append(row.subcategory)
    vals.append(row.net_revenue_pkr_m)
tslib.treemap(ax3, sub.net_revenue_pkr_m.values, labels=labels, values=vals,
              colors=colors, fontsize=8, value_fmt="{:,.1f} PKR m")
import matplotlib.patches as mpatches  # noqa: E402
ax3.legend(handles=[mpatches.Patch(color=col, label=name) for name, col in hues.items()],
           loc="lower left", bbox_to_anchor=(0.0, -0.09), ncol=4, fontsize=8, frameon=False,
           title="Category (hue)", title_fontsize=8)
share_of = sub.set_index("subcategory").share
ax3.set_title(f"Phones and Laptops hold {share_of['Phones'] + share_of['Laptops']:.0f}% of net revenue "
              f"(area = net revenue, PKR m)", loc="left", fontsize=10)

# Panel 4 — sorted bars, values printed
bars = sub.sort_values("net_revenue_pkr_m", ascending=True)
ypos = np.arange(len(bars))
ax4.barh(ypos, bars.net_revenue_pkr_m.values, color=[hues[c] for c in bars.category], height=0.62)
ax4.set_yticks(ypos)
ax4.set_yticklabels(bars.subcategory.values, fontsize=9)
ax4.set_xlabel("Net revenue, PKR m over the catalogue period (sum, zero-based)")
for y, v, s_ in zip(ypos, bars.net_revenue_pkr_m.values, bars.share.values):
    ax4.text(v + total_net * 0.003, y, f"{v:,.1f}  ({s_:.1f}%)", va="center", fontsize=8)
ax4.set_xlim(0, bars.net_revenue_pkr_m.max() * 1.22)
for s in ["top", "right"]:
    ax4.spines[s].set_visible(False)
ax4.set_title(f"Phones leads Laptops by {share_of['Phones'] - share_of['Laptops']:.1f} points; "
              f"Drones is the smallest at {share_of['Drones']:.1f}%", loc="left", fontsize=10)

neg_txt = "; ".join(f"{r.sku} {r.subcategory} {r.net_revenue_pkr_m:.4f}" for r in neg.itertuples())
note = (
    "Source: sessions_hourly.csv (12,670 rows, Apr 2024 to 11 Sep 2025) and revenue_catalogue.csv; all data synthetic (CDB601220). "
    f"Daily totals use complete days only (>=21 of 24 hours filed); {int(daily_full.loc[daily.index, 'scaled'].sum())} days "
    "with 21-23 hours are scaled by 24/filed. Sep 2025 is partial and excluded. "
    f"Panel 1 window: centred {WINDOW} days (weekly cycle). "
    f"Catalogue: SKU-0127 counted once (Audio). Other: {other_note}. "
    f"Negative rows (returns > sales), kept inside sub-category totals and not drawn as area: {neg_txt}."
)
import textwrap  # noqa: E402
fig.text(0.01, -0.012, "\n".join(textwrap.wrap(note, 210)), fontsize=7,
         color=C["ink_soft"], va="top")
fig.savefig(os.path.join(HERE, "partD_figure.png"), dpi=300, bbox_inches="tight", facecolor="white")
plt.close(fig)

# ------------------------------------------------------------- written outputs
dec_all = decisions + cat_dec
md = ["# partD decisions (generated by partD_figure.py)", "",
      "| # | what | detected | rule | rows |", "|---|---|---|---|---|"]
for i, d in enumerate(dec_all, 1):
    md.append(f"| {i} | {d['what']} | {d['detected']} | {d['rule']} | {d['rows']} |")
md += ["", "Daily rule: a day needs >= 21 of 24 filed hours; 21-23 scaled by 24/filed. "
       f"Scaled days in analysis: {int(daily_full.loc[daily.index, 'scaled'].sum())}; "
       "scaling changes a 23-hour day by +4.3%."]
md += ["", f"Shares vs shares_eight.csv: max deviation {max_dev:.2f} points (tolerance 0.3).", ""]
md += ["Negative rows (kept inside sub-category totals):", ""]
md += [f"- {r.sku} {r.category} / {r.subcategory} ({r.sku_name}): {r.net_revenue_pkr_m:.4f} PKR m"
       for r in neg.itertuples()]
with open(os.path.join(HERE, "partD_decisions.md"), "w") as f:
    f.write("\n".join(md) + "\n")

audit_daily = tslib.audit_index(daily_full.sessions.dropna(), "D")
present = h.index[h.orders.notna()]
audit_hour = tslib.audit_index(pd.Series(1, index=present), "h")
with open(os.path.join(HERE, "partD_audit.txt"), "w") as f:
    f.write("index audit, hourly (rows present; missing = hours nobody filed)\n")
    f.write(f"{audit_hour}\n\n")
    f.write("index audit, daily (complete days with a value)\n")
    f.write(f"{audit_daily}\n\n")
    f.write(f"catalogue sub-category shares max deviation vs shares_eight: {max_dev:.3f}\n")
    f.write(f"other bucket: {other_note}\n")

print("TITLES AND NUMBERS")
print(f"  monthly mean/day first {m_first:,.0f}, last {m_last:,.0f}")
print(f"  weekday mean/hr {wk:,.0f}, weekend {we:,.0f}, +{weekend_pct:.1f}%; peak {pk_day} {pk_hour:02d}:00")
print("  sub-category net shares:", {r.subcategory: round(r.share, 2) for r in sub.itertuples()})
print(f"  max deviation vs shares_eight: {max_dev:.3f}")
print(f"  other: {other_note}")
print(f"  negatives: {len(neg)} rows, sum {neg.net_revenue_pkr_m.sum():.4f}")
print("wrote partD_figure.png, partD_decisions.md, partD_audit.txt")
