#!/usr/bin/env python3
"""
partA_charts.py — Part A: rebuild the nine published charts, then take them apart.

For each case: a LEFT panel that reproduces the published recipe (and hits its
self-check number), and a RIGHT panel that is the honest redesign, actually
plotted from the data. Writes partA_case01.png ... partA_case09.png and prints
every self-check number the diagnoses rely on, so the write-up can cite them.

    python3 partA_charts.py
"""
from __future__ import annotations

import os
import sys
import textwrap

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import matplotlib.ticker  # noqa: E402
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from vizlib import PALETTE, style_defaults, save_fig  # noqa: E402

D = os.path.join(HERE, "data")
style_defaults()
C = PALETTE
out = {}


def fmt_k(ax, axis="y"):
    f = matplotlib.ticker.StrMethodFormatter("{x:,.0f}")
    (ax.yaxis if axis == "y" else ax.xaxis).set_major_formatter(f)


_NOTE = {"text": ""}


def note(fig, text):
    """Record the footnote; finish() stamps it once through save_fig."""
    _NOTE["text"] = "\n".join(textwrap.wrap(text, 175))


def panel_titles(ax_l, ax_r, left, right):
    ax_l.set_title(left, loc="left", fontsize=9.5)
    ax_r.set_title(right, loc="left", fontsize=9.5)


def two_panel(name, figsize=(12, 4.8)):
    fig, (al, ar) = plt.subplots(1, 2, figsize=figsize)
    return fig, al, ar


def finish(fig, name, src):
    save_fig(fig, os.path.join(HERE, f"partA_{name}.png"), note=_NOTE["text"] or src)
    plt.close(fig)


SRC = "Source: Week 4 Part A case file (synthetic, CDB601220). Left: the published recipe. Right: the redesign."

# ------------------------------------------------------------------ case 1
c1 = pd.read_csv(os.path.join(D, "case01_orders_stringdate.csv"))
text_sorted = c1.sort_values("month")
c1["d"] = pd.to_datetime(c1.month, format="%Y-%m")
chron = c1.sort_values("d")
steps = np.diff(text_sorted.orders.values)
drops = steps[steps < 0]
out["c1_drops"] = drops.tolist()
out["c1_growth"] = (chron.orders.iloc[-1] / chron.orders.iloc[0] - 1) * 100
fig, al, ar = two_panel("c1")
al.plot(range(len(text_sorted)), text_sorted.orders, color=C["muted"], marker="o", markersize=4)
al.set_ylim(0, text_sorted.orders.max() * 1.1)
al.set_xlabel("position after sorting the text 'month' column")
al.set_ylabel("Orders")
al.set_title(f"Published: sorted as text, drops of {abs(drops[0]):,} and {abs(drops[1]):,}", loc="left", fontsize=9.5)
ar.plot(chron.d, chron.orders, color=C["series"][0], marker="o", markersize=4)
ar.set_ylim(0, chron.orders.max() * 1.1)
ar.set_ylabel("Orders")
ar.set_xlabel("Month (parsed as a date)")
ar.set_title(f"Redesign: a steady {out['c1_growth']:.0f}% rise, no annual collapse", loc="left", fontsize=9.5)
note(fig, SRC + " Mechanism: '2024-1' sorts before '2024-2' as text, so sorting by the string puts Jan 2025 after Dec 2024 for the wrong reason. Pick the date, not the label.")
finish(fig, "case01", SRC)

# ------------------------------------------------------------------ case 2
c2 = pd.read_csv(os.path.join(D, "case02_shop_closed.csv"), parse_dates=["date"])
full = pd.date_range(c2.date.min(), c2.date.max(), freq="D")
closed = full.difference(c2.date)
xi = np.arange(len(c2))
b_row = np.polyfit(xi, c2.sales_pkr_k, 1)[0]
xd = (c2.date - c2.date.min()).dt.days.values
b_day = np.polyfit(xd, c2.sales_pkr_k, 1)[0]
out.update(c2_first=int(c2.sales_pkr_k.iloc[0]), c2_last=int(c2.sales_pkr_k.iloc[-1]),
           c2_pct=(c2.sales_pkr_k.iloc[-1] / c2.sales_pkr_k.iloc[0] - 1) * 100,
           c2_slope_row=b_row, c2_slope_day=b_day, c2_closed=len(closed),
           c2_closed_wd=pd.Series(closed.day_name()).value_counts().to_dict())
fig, al, ar = two_panel("c2")
al.scatter(xi, c2.sales_pkr_k, s=14, color=C["muted"])
pf = np.polyfit(xi, c2.sales_pkr_k, 1)
al.plot(xi, np.polyval(pf, xi), color=C["highlight"], linewidth=1.8)
al.set_xlabel("row number (not a date)")
al.set_ylabel("Sales, PKR thousands")
al.set_ylim(0, c2.sales_pkr_k.max() * 1.15)
al.set_title(f"Published: trend on row number, slope {b_row:.2f} per row", loc="left", fontsize=9.5)
ar.plot(c2.date, c2.sales_pkr_k, color=C["muted"], linewidth=1, marker="o", markersize=2.5)
for d in closed:
    ar.axvline(d, color=C["grid"], linewidth=0.6, zorder=0)
pf2 = np.polyfit(xd, c2.sales_pkr_k, 1)
ar.plot(c2.date, np.polyval(pf2, xd), color=C["series"][0], linewidth=2)
ar.set_ylim(0, c2.sales_pkr_k.max() * 1.15)
ar.set_ylabel("Sales, PKR thousands")
ar.set_xlabel("Date. Grey verticals: the 21 days the shop was closed")
ar.set_title(f"Redesign: {b_day:.2f} per calendar day; the closures are visible", loc="left", fontsize=9.5)
src2 = SRC + " Mechanism: the x axis counts recorded rows, so each closed day is silently removed and the 21 closures pull the days together. The row slope is inflated by {:.0f}%.".format((b_row / b_day - 1) * 100)
note(fig, src2)
finish(fig, "case02", src2)

# ------------------------------------------------------------------ case 3
c3 = pd.read_csv(os.path.join(D, "case03_bandwidth_levels.csv"), parse_dates=["ts"]).set_index("ts")
dsum = c3.concurrent_users.resample("D").sum()
dmean = c3.concurrent_users.resample("D").mean()
per_day = c3.concurrent_users.resample("D").count()
jun = dsum["2025-06"].mean()
jul = dsum["2025-07"].mean()
out.update(c3_sum_jun=jun, c3_sum_jul=jul, c3_sum_step=(jul / jun - 1) * 100,
           c3_mean_jun=dmean["2025-06"].mean(), c3_mean_jul=dmean["2025-07"].mean(),
           c3_mean_step=(dmean["2025-07"].mean() / dmean["2025-06"].mean() - 1) * 100,
           c3_read_jun=(per_day["2025-06"].min(), per_day["2025-06"].max()),
           c3_read_jul=(per_day["2025-07"].min(), per_day["2025-07"].max()))
fig, axs = plt.subplots(2, 2, figsize=(12, 6.4), sharex="col",
                        gridspec_kw={"height_ratios": [4, 1.1]})
al, ar = axs[0]
al.plot(dsum.index, dsum, color=C["muted"], linewidth=1.8)
al.set_ylim(0, dsum.max() * 1.12)
fmt_k(al)
al.set_ylabel("Daily 'peak load' (sum of hourly readings)")
al.set_title(f"Published: a +{out['c3_sum_step']:.0f}% jump on 1 July", loc="left", fontsize=9.5)
axs[1][0].axis("off")
al.tick_params(labelbottom=True, labelsize=7)
ar.plot(dmean.index, dmean, color=C["series"][0], linewidth=1.8, label="daily MEAN of readings")
ar.set_ylim(0, dmean.max() * 1.25)
ar.set_ylabel("Mean concurrent users")
ax_n = axs[1][1]
ax_n.bar(per_day.index, per_day.values, width=0.9, color=C["muted"])
ax_n.set_ylabel("readings\nper day", fontsize=8)
ax_n.set_ylim(0, 26)
ax_n.tick_params(labelsize=7)
ar.set_title(f"Redesign: the mean is flat ({out['c3_mean_step']:+.1f}%); June had fewer readings", loc="left", fontsize=9.5)
src3 = SRC + " Mechanism: concurrent_users is a level. June logs 12-20 readings a day and July 24, so the daily SUM rises with the number of readings, not with users."
note(fig, src3)
finish(fig, "case03", src3)

# ------------------------------------------------------------------ case 4
c4 = pd.read_csv(os.path.join(D, "case04_intervention_lag.csv"), parse_dates=["date"]).set_index("date").conversion_pct
tr = c4.rolling(31).mean()
ce = c4.rolling(31, center=True).mean()
t_trail, t_cent = tr.idxmin(), ce.idxmin()
lag = (t_trail - t_cent).days
out.update(c4_trail=str(t_trail.date()), c4_cent=str(t_cent.date()), c4_lag=lag)
fig, al, ar = two_panel("c4")
al.plot(c4.index, c4, color=C["muted"], linewidth=0.8, label="raw")
al.plot(c4.index, tr, color=C["series"][0], linewidth=2, label="31-day trailing mean")
al.axvline(t_trail, color=C["highlight"], linestyle="--")
al.text(t_trail, al.get_ylim()[0] + 0.05, f" published turn {t_trail.date()}", fontsize=8, color=C["highlight"])
al.set_ylabel("Conversion, %")
al.set_title("Published: the turn is read off a trailing mean", loc="left", fontsize=9.5)
al.legend(fontsize=8)
ar.plot(c4.index, c4, color=C["muted"], linewidth=0.8, label="raw")
ar.plot(c4.index, tr, color=C["series"][0], linewidth=1.6, label="31-day TRAILING")
ar.plot(c4.index, ce, color=C["series"][2], linewidth=1.8, label="31-day CENTRED")
ar.axvline(t_cent, color=C["series"][2], linestyle="--")
ar.axvline(t_trail, color=C["series"][0], linestyle=":")
ar.set_ylabel("Conversion, %")
ar.set_title(f"Redesign: centred turn {t_cent.date()}; trailing finds it {lag} days late", loc="left", fontsize=9.5)
ar.legend(fontsize=8, loc="upper left")
src4 = SRC + " Mechanism: a trailing window cannot see a turn until it has filled, so its minimum sits half a window (15 days) after the true turn."
note(fig, src4)
finish(fig, "case04", src4)

# ------------------------------------------------------------------ case 5
c5 = pd.read_csv(os.path.join(D, "case05_revenue_window.csv"))
c5["y"] = c5.month.str[:4].astype(int)
c5["m"] = c5.month.str[5:].astype(int)
win = c5[(c5.month >= "2025-05") & (c5.month <= "2025-11")].reset_index(drop=True)
pct5 = (win.revenue_pkr_m.iloc[-1] / win.revenue_pkr_m.iloc[0] - 1) * 100
piv = c5.pivot(index="m", columns="y", values="revenue_pkr_m")
fall = {y: (piv.loc[11, y] / piv.loc[5, y] - 1) * 100 for y in [2023, 2024, 2025]}
out.update(c5_pct=pct5, c5_fall=fall, c5_start=win.revenue_pkr_m.iloc[0], c5_end=win.revenue_pkr_m.iloc[-1])
fig, al, ar = two_panel("c5")
al.plot(range(len(win)), win.revenue_pkr_m, color=C["series"][1], marker="o", linewidth=2)
al.set_xticks(range(len(win)))
al.set_xticklabels(win.month, rotation=0, fontsize=8)
al.set_ylim(0, win.revenue_pkr_m.max() * 1.12)
al.set_ylabel("Revenue, PKR m per month")
al.set_title(f"Published: May–Nov 2025 only, {pct5:.1f}%", loc="left", fontsize=9.5)
cols = {2023: C["muted"], 2024: C["series"][0], 2025: C["highlight"]}
for y in [2023, 2024, 2025]:
    ar.plot(piv.index, piv[y], color=cols[y], linewidth=2, marker="o", markersize=3, label=str(y))
ar.axvspan(4.5, 11.5, color=C["grid"], alpha=0.35, zorder=0)
ar.set_xticks(range(1, 13))
ar.set_xticklabels(["J", "F", "M", "A", "M", "J", "J", "A", "S", "O", "N", "D"])
ar.set_ylim(0, piv.max().max() * 1.12)
ar.set_ylabel("Revenue, PKR m per month")
ar.set_xlabel("Month of the year (shaded: May to Nov)")
ar.legend(fontsize=8)
ar.set_title(f"Redesign: every year falls May→Nov ({fall[2023]:.0f}%, {fall[2024]:.0f}%, {fall[2025]:.0f}%)", loc="left", fontsize=9.5)
src5 = SRC + " Mechanism: a seasonal peak in May or June followed by a fall to November is the pattern of every year in the file. The window starts at the peak."
note(fig, src5)
finish(fig, "case05", src5)

# ------------------------------------------------------------------ case 6
c6 = pd.read_csv(os.path.join(D, "case06_monthly_partial.csv"), parse_dates=["date"]).set_index("date").orders
mo = c6.resample("MS").agg(["sum", "count", "mean"])
sep, octo = mo.loc["2025-09-01"], mo.loc["2025-10-01"]
out.update(c6_sep=sep["sum"], c6_oct=octo["sum"], c6_oct_share=octo["sum"] / sep["sum"] * 100,
           c6_sep_pd=sep["mean"], c6_oct_pd=octo["mean"], c6_oct_days=int(octo["count"]),
           c6_pd_step=(octo["mean"] / sep["mean"] - 1) * 100)
fig, al, ar = two_panel("c6")
mm = mo.loc[:"2025-10-01"]
al.bar(range(len(mm)), mm["sum"], color=C["muted"])
al.set_xticks(range(len(mm)))
al.set_xticklabels([p.strftime("%b") for p in mm.index], fontsize=8)
al.set_ylim(0, mm["sum"].max() * 1.12)
fmt_k(al)
al.set_ylabel("Orders per month (sum)")
al.set_title(f"Published: October is {out['c6_oct_share']:.0f}% of September", loc="left", fontsize=9.5)
ar.bar(range(len(mm)), mm["mean"], color=[C["muted"]] * (len(mm) - 1) + [C["surface"]],
       edgecolor=[C["muted"]] * (len(mm) - 1) + [C["highlight"]], hatch=None)
ar.bar(len(mm) - 1, mm["mean"].iloc[-1], color="none", edgecolor=C["highlight"], linestyle="--")
ar.set_xticks(range(len(mm)))
ar.set_xticklabels([p.strftime("%b") for p in mm.index], fontsize=8)
ar.set_ylim(0, mm["mean"].max() * 1.2)
ar.set_ylabel("Orders per day (mean)")
ar.set_title(f"Redesign: per day, October is {out['c6_pd_step']:+.1f}% vs September (11 days, outlined)", loc="left", fontsize=9.5)
src6 = SRC + " Mechanism: the file stops on 11 October. A month summed over 11 days is compared with a month summed over 30."
note(fig, src6)
finish(fig, "case06", src6)

# ------------------------------------------------------------------ case 7
c7 = pd.read_csv(os.path.join(D, "case07_stacked_products.csv")).set_index("month")
tot = c7.sum(axis=1)
out.update(c7_env=(tot.min(), tot.max()), c7_std={p: c7[p].std() for p in c7.columns},
           c7_rng={p: (c7[p].min(), c7[p].max()) for p in c7.columns})
fig, al, ar = two_panel("c7")
x = np.arange(len(c7))
cols4 = [C["series"][0], C["highlight"], C["series"][2], C["series_4th"]]
al.stackplot(x, c7.T.values, labels=c7.columns, colors=cols4, alpha=0.85)
al.set_xticks(x[::6])
al.set_xticklabels(c7.index[::6], fontsize=8)
al.set_ylim(0, tot.max() * 1.05)
al.set_ylabel("Revenue, PKR m")
al.legend(loc="upper left", fontsize=7.5, ncol=4)
al.set_title("Published: stacked area; product D looks like it moves", loc="left", fontsize=9.5)
for p, col in zip(c7.columns, cols4):
    ar.plot(x, c7[p].values, color=col, linewidth=2 if p == "product_b" else 1.4, label=p)
ar.set_xticks(x[::6])
ar.set_xticklabels(c7.index[::6], fontsize=8)
ar.set_ylim(0, c7.max().max() * 1.1)
ar.set_ylabel("Revenue, PKR m (own line each, zero baseline)")
ar.legend(fontsize=7.5, ncol=4, loc="upper left")
ar.set_title(f"Redesign: product B is the erratic line (range {c7.product_b.min():.0f}–{c7.product_b.max():.0f}); D is steady", loc="left", fontsize=9.5)
src7 = SRC + " Mechanism: in a stack, every band's edges move with everything beneath it, so product B's swings are read as D's."
note(fig, src7)
finish(fig, "case07", src7)

# ------------------------------------------------------------------ case 8
c8 = pd.read_csv(os.path.join(D, "case08_channel_attrib.csv"))
touch = [c for c in c8.columns if c.startswith("touch_")]
rates = (c8[touch].mean() * 100)
per_cust = c8[touch].sum(axis=1)
out.update(c8_rates=rates.round(1).to_dict(), c8_sum=rates.sum(), c8_single=(per_cust == 1).mean() * 100,
           c8_multi=(per_cust >= 2).mean() * 100)
fig, al, ar = two_panel("c8")
labels = [t.replace("touch_", "").capitalize() for t in touch]
al.pie(rates.values, labels=[f"{l}\n{v:.1f}%" for l, v in zip(labels, rates.values)],
       startangle=90, counterclock=False, colors=[C["series"][0], C["series"][1], C["series"][2], C["muted"]],
       wedgeprops=dict(edgecolor="white"))
al.set_title(f"Published: pie of 'touch' rates; they sum to {rates.sum():.0f}%", loc="left", fontsize=9.5)
al.set_aspect("equal")
order = rates.sort_values().index
y = np.arange(len(order))
ar.barh(y, rates[order].values, color=C["series"][0], height=0.55)
ar.axvline(100, color=C["ink_soft"], linestyle=":", linewidth=1)
ar.set_yticks(y)
ar.set_yticklabels([o.replace("touch_", "").capitalize() for o in order])
ar.set_xlim(0, 110)
ar.set_xlabel("Share of all 4,000 customers touched by the channel at least once (%)")
for yi, v in zip(y, rates[order].values):
    ar.text(v + 1, yi, f"{v:.1f}%", va="center", fontsize=8)
ar.set_title(f"Redesign: reach, not share. {out['c8_single']:.0f}% touched once; {out['c8_multi']:.0f}% by two or more", loc="left", fontsize=9.5)
src8 = SRC + " Mechanism: a customer can be touched by several channels, so the four rates are reach and overlap. A pie assumes one channel per customer."
note(fig, src8)
finish(fig, "case08", src8)

# ------------------------------------------------------------------ case 9
c9 = pd.read_csv(os.path.join(D, "case09_premium_share.csv"))
c9["share"] = c9.premium_revenue_pkr_m / c9.total_revenue_pkr_m * 100
out.update(c9_share0=c9.share.iloc[0], c9_share1=c9.share.iloc[-1],
           c9_prem=(c9.premium_revenue_pkr_m.iloc[0], c9.premium_revenue_pkr_m.iloc[-1]),
           c9_tot=(c9.total_revenue_pkr_m.iloc[0], c9.total_revenue_pkr_m.iloc[-1]))
fig, al, ar = two_panel("c9")
al.plot(c9.quarter, c9.share, color=C["series"][0], marker="o", linewidth=2)
al.set_ylim(0, 45)
al.set_ylabel("Premium share of revenue (%)")
al.annotate(f"{c9.share.iloc[-1]:.1f}%", (len(c9) - 1, c9.share.iloc[-1]), textcoords="offset points",
            xytext=(-8, 10), fontsize=9, ha="right")
al.tick_params(axis="x", rotation=45, labelsize=8)
al.set_title(f"Published: share rises {c9.share.iloc[0]:.0f}% → {c9.share.iloc[-1]:.0f}%", loc="left", fontsize=9.5)
idx = pd.DataFrame({"premium": c9.premium_revenue_pkr_m / c9.premium_revenue_pkr_m.iloc[0] * 100,
                    "total": c9.total_revenue_pkr_m / c9.total_revenue_pkr_m.iloc[0] * 100}, index=c9.quarter)
ar.plot(idx.index, idx.total, color=C["muted"], marker="o", linewidth=2, label="total revenue")
ar.plot(idx.index, idx.premium, color=C["series"][0], marker="o", linewidth=2, label="premium revenue")
ar.set_ylim(0, 110)
ar.set_ylabel("Index, 2024Q1 = 100 (zero baseline)")
ar.tick_params(axis="x", rotation=45, labelsize=8)
ar.legend(fontsize=8)
ar.set_title(f"Redesign: premium fell {abs(out['c9_prem'][1] / out['c9_prem'][0] - 1) * 100:.0f}%; total fell "
             f"{abs(out['c9_tot'][1] / out['c9_tot'][0] - 1) * 100:.0f}%", loc="left", fontsize=9.5)
src9 = SRC + " Mechanism: the share's denominator shrank faster than the numerator. Premium revenue barely moved; the rest of the business fell."
note(fig, src9)
finish(fig, "case09", src9)

print("SELF-CHECK NUMBERS")
for k in sorted(out):
    print(f"  {k}: {out[k]}")
