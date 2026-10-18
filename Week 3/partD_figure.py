"""
Part D - the clinical review figure (2x2, 300 dpi).

    python3 partD_figure.py

Inputs : data/vitals_10k.csv           (synthetic, CDB601220 Week 3)
         data/ward_los_wide.csv        (used only to show the melt() step)
Outputs: partD_figure.png              the figure
         partD_appendix_heart_rate.png heart rate WITH and WITHOUT the exclusion
         partD_cleaning_log.txt        every rule and count (feeds Part E)

Every figure starts with fig, ax = plt.subplots(). Save happens before show.
"""
from __future__ import annotations

import os

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns
from scipy import stats

from vizlib import MARKERS, PALETTE, save_fig, style_defaults

ROOT = os.path.dirname(os.path.abspath(__file__))
style_defaults()
C = PALETTE["series"]                 # blue, vermillion, green (Okabe-Ito subset)
LOG: dict[str, str] = {}              # the audit trail, printed at the end

BIN_WIDTH = 3        # mmHg, panel 1 (declared on the figure)
HR_LO, HR_HI = 30, 250      # bpm, physiological plausibility window
LOS_MAX = 30         # days; the data has a clean gap between 14.6 d and 139.8 d
SCATTER_ALPHA = 0.18


# ============================================================================
# STEP 0 - inspect (kept so the output can be read; it is cheap)
# ============================================================================
def inspect(df: pd.DataFrame) -> None:
    print("=== df.info() ===");  df.info()
    print("\n=== df.describe().T ===");  print(df.describe().T.round(2))
    print("\n=== ward values ===");  print(df.ward.value_counts())
    print("\n=== admit_date head ===");  print(df.admit_date.head(20).tolist())


# ============================================================================
# STEP 1 - clean, with a rule and a count for every change
# ============================================================================
WARD_MAP = {
    "general medicine": "General Medicine", "gen medicine": "General Medicine",
    "cardiology": "Cardiology", "cardio": "Cardiology",
    "day surgery": "Day Surgery", "day-surgery": "Day Surgery",
    "intensive care": "ICU", "icu": "ICU", "i.c.u": "ICU",
}


def parse_dates(s: pd.Series) -> pd.Series:
    """Three source systems -> three explicit formats. Never guess row by row."""
    iso = s.str.match(r"^\d{4}-\d{2}-\d{2}$")
    mon = s.str.match(r"^\d{2}-[A-Za-z]{3}-\d{4}$")
    sla = s.str.match(r"^\d{2}/\d{2}/\d{4}$")
    out = pd.Series(pd.NaT, index=s.index, dtype="datetime64[ns]")
    out[iso] = pd.to_datetime(s[iso], format="%Y-%m-%d")
    out[mon] = pd.to_datetime(s[mon], format="%d-%b-%Y")
    out[sla] = pd.to_datetime(s[sla], format="%d/%m/%Y")   # day first: see LOG
    LOG["admit_date formats"] = (
        f"3 formats parsed explicitly: ISO n={iso.sum():,}, dd-Mon-yyyy "
        f"n={mon.sum():,}, dd/mm/yyyy n={sla.sum():,}; unparsed = "
        f"{out.isna().sum()}")
    as_mm_dd = pd.to_datetime(s[sla], format="%m/%d/%Y", errors="coerce")
    LOG["dd/mm vs mm/dd"] = (
        f"slash dates are day-first: read as mm/dd/yyyy {as_mm_dd.isna().sum():,} "
        f"of {sla.sum():,} would be impossible (month > 12); range "
        f"{out.min():%d %b %Y} - {out.max():%d %b %Y}")
    return out


def clean(raw: pd.DataFrame) -> pd.DataFrame:
    df = raw.copy()
    LOG["rows loaded"] = f"{len(df):,} (patient_id unique: {df.patient_id.is_unique}, " \
                         f"duplicate rows: {df.duplicated().sum()})"

    # 1. ward spellings -> 4 wards
    n_raw = df.ward.nunique()
    df["ward_clean"] = df.ward.str.strip().str.lower().map(WARD_MAP)
    assert df.ward_clean.isna().sum() == 0 and df.ward_clean.nunique() == 4
    LOG["ward spellings"] = (f"{n_raw} spellings conformed to 4 wards "
                             f"(strip, lower-case, dictionary map); 0 unmapped")

    # 2. dates
    df["admit_dt"] = parse_dates(df.admit_date)

    # 3. bmi sentinels: 999 (not recorded) and 0 (impossible)
    m0 = df.bmi.mean()
    s999, s0 = (df.bmi == 999).sum(), (df.bmi == 0).sum()
    df.loc[df.bmi.isin([999, 0]), "bmi"] = np.nan
    LOG["bmi sentinels"] = (f"999 (n={s999}) and 0 (n={s0}) are 'missing' codes, set to "
                            f"NaN, rows kept. Mean bmi {m0:.1f} -> {df.bmi.mean():.1f} kg/m2")

    # 4. heart_rate device faults (the ethics clause)
    hm0 = df.heart_rate.mean()
    hi, lo = (df.heart_rate > HR_HI).sum(), (df.heart_rate < HR_LO).sum()
    df["heart_rate_raw"] = df.heart_rate
    df.loc[(df.heart_rate > HR_HI) | (df.heart_rate < HR_LO), "heart_rate"] = np.nan
    LOG["heart_rate device faults"] = (
        f"Readings above {HR_HI} bpm were removed as device faults (n = {hi}); "
        f"readings below {HR_LO} bpm (all 0 bpm, flat-line) also removed (n = {lo}). "
        f"Mean heart rate moves from {hm0:.1f} to {df.heart_rate.mean():.1f} bpm. "
        f"The figure was also produced without the exclusion: "
        f"partD_appendix_heart_rate.png")

    # 5. los_days entry errors
    lm0, lmed0 = df.los_days.mean(), df.los_days.median()
    bad = df.los_days > LOS_MAX
    gap = (df.los_days[~bad].max(), df.los_days[bad].min())
    df.loc[bad, "los_days"] = np.nan
    LOG["los_days entry errors"] = (
        f"> {LOS_MAX} days set to NaN (n = {bad.sum()}); no value lies between "
        f"{gap[0]:.1f} and {gap[1]:.1f} days. Mean LOS {lm0:.2f} -> "
        f"{df.los_days.mean():.2f} d (median {lmed0:.2f} -> {df.los_days.median():.2f})")

    # 6. derived column
    LOG["derived column"] = ("map_mmhg = (systolic + 2*diastolic)/3 is arithmetic, "
                             "excluded from the heatmap (corr with systolic "
                             f"{raw.map_mmhg.corr(raw.systolic):.2f})")
    # 7. ratio column
    LOG["risk_score"] = ("a ratio (events/day): never averaged across wards here; "
                         "not plotted")
    return df


# ============================================================================
# STEP 2 - the figure
# ============================================================================
def two_populations(x: np.ndarray):
    """Peaks of a KDE and the valley between them (used to split panel 1)."""
    grid = np.linspace(x.min(), x.max(), 600)
    dens = stats.gaussian_kde(x)(grid)
    # first and second highest local maxima
    peaks = [i for i in range(1, len(grid) - 1)
             if dens[i] > dens[i - 1] and dens[i] > dens[i + 1]]
    peaks = sorted(peaks, key=lambda i: dens[i], reverse=True)[:2]
    p1, p2 = sorted(peaks)
    valley = grid[p1:p2][np.argmin(dens[p1:p2])]
    return grid[p1], grid[p2], valley


def build_figure(df: pd.DataFrame):
    fig, ax = plt.subplots(2, 2, figsize=(12.6, 8.4))

    # -------------------------------------------------- panel 1: distribution
    a = ax[0, 0]
    sys_ = df.systolic.to_numpy()
    p_lo, p_hi, split = two_populations(sys_)
    edges = np.arange(sys_.min() // BIN_WIDTH * BIN_WIDTH,
                      sys_.max() + BIN_WIDTH + 1, BIN_WIDTH)
    lo, hi = sys_[sys_ < split], sys_[sys_ >= split]
    a.hist(lo, bins=edges, color=C[0], label=f"lower mode (n = {len(lo):,})")
    a.hist(hi, bins=edges, color=C[1], label=f"upper mode (n = {len(hi):,})")
    a.axvline(split, color=PALETTE["ink_soft"], ls="--", lw=1)
    a.text(0.98, 0.95, f"bin width = {BIN_WIDTH} mmHg\nsplit at the valley, "
           f"{split:.0f} mmHg", transform=a.transAxes, ha="right", va="top",
           fontsize=8.5, color=PALETTE["ink_soft"])
    a.set_ylim(0, a.get_ylim()[1] * 1.2)
    a.set_title(f"Systolic pressure is bimodal:\ntwo groups peak near "
                f"{p_lo:.0f} and {p_hi:.0f} mmHg", fontsize=11)
    a.set_xlabel("Systolic blood pressure (mmHg)")
    a.set_ylabel("Patients per 3-mmHg bin")
    a.legend(loc="upper left")
    LOG["panel 1 parameters"] = (f"hist bin width {BIN_WIDTH} mmHg, KDE-valley split at "
                                 f"{split:.1f} mmHg (peaks {p_lo:.0f}, {p_hi:.0f})")

    # ------------------------------------------------------ panel 2: box plot
    b = ax[0, 1]
    d2 = df[["ward_clean", "los_days"]].dropna()
    d2 = d2[d2.los_days > 0]                      # 0 cannot be drawn on a log axis
    n_zero = int((df.los_days == 0).sum())
    order = (d2.groupby("ward_clean").los_days.median()
             .sort_values().index.tolist())       # sorted by median, not A-Z
    meds = d2.groupby("ward_clean").los_days.median()
    sns.boxplot(data=d2, x="ward_clean", y="los_days", order=order, ax=b,
                color=C[0], width=0.55, showfliers=True, linewidth=1.1,
                flierprops=dict(marker="o", markersize=2.5, alpha=0.35,
                                markerfacecolor=PALETTE["muted"],
                                markeredgecolor="none"))
    b.set_yscale("log")
    b.set_title(f"ICU stays run longest:\nmedian {meds['ICU']:.1f} days "
                f"vs {meds['Day Surgery']:.2f} in Day Surgery", fontsize=11)
    b.set_xlabel("Ward (sorted by median length of stay)")
    b.set_ylabel("Length of stay (days, log scale)")
    b.yaxis.set_major_formatter(matplotlib.ticker.FuncFormatter(
        lambda v, _: f"{v:g}"))
    b.set_ylim(0.004, 40)
    b.set_xticks(range(len(order)))
    b.set_xticklabels([f"{w}\n(n = {int((d2.ward_clean == w).sum()):,})"
                       for w in order])
    LOG["panel 2 parameters"] = (f"log-10 y axis; showfliers=True (outliers visible); "
                                 f"wards ordered by median; {n_zero} zero-day stays "
                                 f"cannot be drawn on a log axis")

    # ------------------------------------------------------- panel 4 FIRST
    cols = ["age", "systolic", "diastolic", "heart_rate", "spo2", "bmi",
            "chol_mmol_l", "glucose_mmol_l", "los_days"]
    short = {"age": "age", "systolic": "systolic", "diastolic": "diastolic",
             "heart_rate": "heart rate", "spo2": "SpO2", "bmi": "BMI",
             "chol_mmol_l": "cholesterol", "glucose_mmol_l": "glucose",
             "los_days": "LOS"}
    corr = df[cols].corr().rename(index=short, columns=short)   # pairwise-complete
    mask = np.triu(np.ones_like(corr, dtype=bool), k=1)
    d = ax[1, 1]
    sns.heatmap(corr, ax=d, mask=mask, cmap=PALETTE["diverging"], vmin=-1, vmax=1,
                center=0, annot=True, fmt=".2f", annot_kws={"size": 7},
                linewidths=0.5, linecolor="white",
                cbar_kws={"shrink": 0.8, "label": "Pearson r"})
    d.grid(False)
    d.set_title("Only one non-arithmetic pair stands out:\nage and cholesterol "
                f"(r = {corr.loc['cholesterol', 'age']:.2f})", fontsize=11)
    d.tick_params(axis="x", rotation=40, labelsize=8)
    d.tick_params(axis="y", labelsize=8)

    # --------------------------------------------------- panel 3: the scatter
    c = ax[1, 0]
    d3 = df[["age", "chol_mmol_l", "sex"]].dropna()
    for k, (sex, mk) in enumerate([("F", MARKERS[0]), ("M", MARKERS[1])]):
        g = d3[d3.sex == sex]
        c.scatter(g.age, g.chol_mmol_l, s=9, alpha=SCATTER_ALPHA, marker=mk,
                  color=C[k], edgecolors="none", label=f"{'Female' if sex == 'F' else 'Male'} (n = {len(g):,})")
    slope, intercept, r, _, _ = stats.linregress(d3.age, d3.chol_mmol_l)
    xs = np.array([d3.age.min(), d3.age.max()])
    c.plot(xs, intercept + slope * xs, color=PALETTE["ink"], lw=1.8)
    c.text(0.03, 0.95, f"r = {r:.2f}\n+{slope * 10:.2f} mmol/L per decade",
           transform=c.transAxes, va="top", fontsize=9, color=PALETTE["ink"])
    c.set_title("Cholesterol rises about "
                f"{slope * 10:.2f} mmol/L\nwith every decade of age", fontsize=11)
    c.set_xlabel("Age (years)")
    c.set_ylabel("Total cholesterol (mmol/L)")
    leg = c.legend(loc="lower right", markerscale=2)
    for h in leg.legend_handles:
        h.set_alpha(1)
    LOG["panel 3 parameters"] = (f"all {len(d3):,} points, alpha {SCATTER_ALPHA}, "
                                 f"s=9, OLS line, shape + colour for sex")

    # ------------------------------------------------------------- finishing
    for p in ax.flat:
        for sp in ("top", "right", "left", "bottom"):
            p.spines[sp].set_visible(False)
    fig.suptitle("Clinical safety review: two blood-pressure populations, "
                 "one real risk correlation, and ICU stays that run longest",
                 x=0.006, ha="left", fontsize=14, fontweight="bold",
                 color=PALETTE["ink"])
    fig.tight_layout(rect=[0, 0, 1, 0.95])
    return fig, corr


def appendix_heart_rate(raw: pd.DataFrame, df: pd.DataFrame) -> str:
    """The ethics clause: show heart rate with AND without the exclusion."""
    fig, ax = plt.subplots(1, 2, figsize=(11, 4.2))
    a, b = ax
    a.boxplot([raw.heart_rate], vert=False, widths=0.5, patch_artist=True,
              boxprops=dict(facecolor=C[0], alpha=0.6),
              flierprops=dict(marker="o", markersize=3, markerfacecolor=C[1],
                              markeredgecolor="none"))
    a.set_title(f"Without exclusion: {int(((raw.heart_rate > HR_HI) | (raw.heart_rate < HR_LO)).sum())} "
                f"impossible readings dominate the scale")
    a.set_xlabel("Heart rate (bpm)"); a.set_yticks([])
    b.boxplot([df.heart_rate.dropna()], vert=False, widths=0.5, patch_artist=True,
              boxprops=dict(facecolor=C[0], alpha=0.6),
              flierprops=dict(marker="o", markersize=3, markerfacecolor=C[1],
                              markeredgecolor="none"))
    b.set_title(f"With exclusion ({HR_LO}-{HR_HI} bpm): mean "
                f"{df.heart_rate.mean():.1f} vs {raw.heart_rate.mean():.1f} bpm")
    b.set_xlabel("Heart rate (bpm)"); b.set_yticks([])
    for p in ax:
        p.spines[["left", "top", "right"]].set_visible(False)
    fig.suptitle("Appendix: heart rate before and after the device-fault rule",
                 x=0.006, ha="left", fontsize=12.5, fontweight="bold")
    fig.tight_layout(rect=[0, 0, 1, 0.92])
    out = save_fig(fig, os.path.join(ROOT, "partD_appendix_heart_rate.png"),
                   "Same data, same boxplot, exclusion rule applied on the right. "
                   "Synthetic data, CDB601220 Week 3.")
    plt.close(fig)
    return out


def main():
    raw = pd.read_csv(os.path.join(ROOT, "data", "vitals_10k.csv"))
    # inspect(raw)            # <- run once, read, comment out
    df = clean(raw)

    # The wide file exists to demonstrate melt(): seaborn wants long data.
    wide = pd.read_csv(os.path.join(ROOT, "data", "ward_los_wide.csv"))
    long_ = wide.melt(var_name="ward", value_name="los_days").dropna()
    LOG["ward_los_wide.csv"] = (f"melt(): {wide.shape} wide -> {long_.shape} long "
                                f"(not used for the figure; vitals_10k is)")

    fig, corr = build_figure(df)

    n_los = int(df.los_days.notna().sum())
    note = (f"n = {len(df):,} patients (synthetic data, CDB601220 Week 3). "
            f"Removed: heart rate outside {HR_LO}-{HR_HI} bpm as device faults "
            f"(n = {int(raw.heart_rate.gt(HR_HI).sum())} + "
            f"{int(raw.heart_rate.lt(HR_LO).sum())}); BMI codes 999/0 as missing "
            f"(n = {int(raw.bmi.isin([999, 0]).sum())}); LOS > {LOS_MAX} d as entry errors "
            f"(n = {int((raw.los_days > LOS_MAX).sum())}).\n"
            f"Wards: 12 spellings -> 4; dates parsed in 3 formats. map_mmhg excluded "
            f"from heatmap (derived). Panel 1 bin width {BIN_WIDTH} mmHg; panel 2 log "
            f"y-axis, outliers shown; panel 3 alpha {SCATTER_ALPHA}; "
            f"correlations pairwise-complete, n = {n_los:,}+.")
    out = save_fig(fig, os.path.join(ROOT, "partD_figure.png"), note)   # SAVE first
    plt.close(fig)
    print("wrote", out)
    print("wrote", appendix_heart_rate(raw, df))

    text = "\n".join(f"{k:<28} {v}" for k, v in LOG.items())
    with open(os.path.join(ROOT, "partD_cleaning_log.txt"), "w") as f:
        f.write(text + "\n")
    print("\nCleaning log (Part E item 3):\n")
    print(text)
    print("\nCorrelation matrix (rounded):")
    print(corr.round(2).to_string())


if __name__ == "__main__":
    main()
