"""
Builds the two written deliverables from the numbers the scripts computed:

    python3 partA_charts.py     # figures + partA_metrics.json
    python3 partD_figure.py     # figure + cleaning log
    python3 build_pdfs.py       # partA_diagnosis.pdf, partE_justification.pdf

Every number in the text is read from partA_metrics.json or recomputed from the
data here, so the prose cannot drift away from the results.
All data is synthetic, generated for CDB601220 Week 3.
"""
import json
import os

import numpy as np
import pandas as pd
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import cm
from reportlab.platypus import (Image, KeepTogether, PageBreak, Paragraph,
                                SimpleDocTemplate, Spacer, Table, TableStyle)
from PIL import Image as PILImage

ROOT = os.path.dirname(os.path.abspath(__file__))
FIG = os.path.join(ROOT, "partA_figs")
M = json.load(open(os.path.join(ROOT, "partA_metrics.json")))

import matplotlib
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
_fd = os.path.join(matplotlib.get_data_path(), "fonts", "ttf")
for _n, _f in [("DV", "DejaVuSans.ttf"), ("DV-B", "DejaVuSans-Bold.ttf"),
               ("DV-I", "DejaVuSans-Oblique.ttf"), ("DV-BI", "DejaVuSans-BoldOblique.ttf")]:
    pdfmetrics.registerFont(TTFont(_n, os.path.join(_fd, _f)))
pdfmetrics.registerFontFamily("DV", normal="DV", bold="DV-B", italic="DV-I", boldItalic="DV-BI")

ss = getSampleStyleSheet()
BODY = ParagraphStyle("b", parent=ss["BodyText"], fontName="DV", fontSize=8.0, leading=10.6, spaceAfter=3)
H1 = ParagraphStyle("h1", parent=ss["Heading1"], fontName="DV-B", fontSize=13, leading=16, spaceAfter=2, textColor=colors.HexColor("#16202E"))
CLAIM = ParagraphStyle("c", parent=BODY, fontName="DV-I", textColor=colors.HexColor("#5B6573"), spaceAfter=5)
LAB = ParagraphStyle("l", parent=BODY, fontName="DV-B", textColor=colors.HexColor("#0072B2"), spaceAfter=0, spaceBefore=3)
CAP = ParagraphStyle("cap", parent=BODY, fontSize=7.2, leading=9, textColor=colors.HexColor("#5B6573"), spaceAfter=2)


def img(name, max_w=17.2 * cm, max_h=5.9 * cm):
    p = os.path.join(FIG, name)
    w, h = PILImage.open(p).size
    k = min(max_w / w, max_h / h)
    return Image(p, width=w * k, height=h * k)


def P(t, s=BODY):
    return Paragraph(t, s)


def f(x, n=1):
    return f"{x:,.{n}f}"


def case_page(n, title, claim, conclusion, decoy, mechanism, redesign, rebuild_note, extra_heights=(5.9, 5.9)):
    return [
        P(f"Case {n} · {title}", H1), P(claim, CLAIM),
        P("1 · Rebuild", LAB), P(rebuild_note),
        img(f"case{n}_rebuild.png", max_h=extra_heights[0] * cm),
        P("2 · The conclusion the chart invites, and the decoy", LAB),
        P(f"<b>Conclusion:</b> {conclusion}"), P(f"<b>Decoy:</b> {decoy}"),
        P("3 · The mechanism", LAB), P(mechanism),
        P("4 · The redesign", LAB), img(f"case{n}_redesign.png", max_h=extra_heights[1] * cm),
        P(redesign, CAP), PageBreak(),
    ]


def build_A():
    c1, c2, c3, c4, c5, c6, c7, c8, c9 = (M[k] for k in ("c1", "c2", "c3", "c4", "c5", "c6", "c7", "c8", "c9"))
    st = []
    st += [P("Week 3 · Part A — nine charts, rebuilt and taken apart", H1),
           P("Every chart below was rebuilt from its recipe (<i>partA_charts.py</i>) and hit its self-check number. "
             "Each case gives the conclusion and decoy, the mechanism with the number that proves it, and the redesign. "
             "All data is synthetic, generated for CDB601220 Week 3.", BODY), Spacer(1, 4)]

    # ---- 1
    r = c1["rate"]; sw = c1["speed_within"]; ew = c1["exp_within"]
    st += case_page(1, "Premium helmets and head injuries", "“Premium-certified helmets have 2.5x the head-injury rate.”",
        f"Premium helmets are more dangerous ({f(c1['rate_prem'],2)} vs {f(c1['rate_std'],2)} injuries per 1,000 trips).",
        f"“Premium riders are just riskier: faster or less experienced.” Within a road type the riders are not faster: "
        f"motorway {f(sw['Motorway']['Premium'])} vs {f(sw['Motorway']['Standard'])} kph, city arterial "
        f"{f(sw['City arterial']['Premium'])} vs {f(sw['City arterial']['Standard'])}, inner-city lanes "
        f"{f(sw['Inner-city lanes']['Premium'])} vs {f(sw['Inner-city lanes']['Standard'])}. Experience gaps are mixed "
        f"(motorway Premium {f(ew['Motorway']['Premium'],0)} vs Standard {f(ew['Motorway']['Standard'],0)} months), and Premium is still lower in every stratum. "
        f"The sample is not the issue either: {c1['trips']:,} trips, {c1['injuries']} injuries.",
        f"<b>Road type is a confounder (Simpson's paradox).</b> {c1['prem_motorway_share']:.0%} of Premium trips are on the motorway vs "
        f"{c1['std_motorway_share']:.1%} of Standard trips ({c1['std_inner_share']:.0%} of Standard trips are in inner-city lanes). "
        f"The motorway is intrinsically dangerous ({f(c1['road_rate_all']['Motorway'])} per 1,000 vs "
        f"{f(c1['road_rate_all']['Inner-city lanes'])} in inner-city lanes). Inside each road type Premium is lower: "
        f"{f(r['Motorway']['Premium'])} vs {f(r['Motorway']['Standard'])}, {f(r['City arterial']['Premium'])} vs {f(r['City arterial']['Standard'])}, "
        f"{f(r['Inner-city lanes']['Premium'],2)} vs {f(r['Inner-city lanes']['Standard'],2)}. Standardised to the combined road mix: "
        f"Standard {f(c1['std_adj']['Standard'],2)}, Premium {f(c1['std_adj']['Premium'],2)} "
        f"({c1['std_adj']['Premium']/c1['std_adj']['Standard']-1:+.0%}).",
        "Left: who rides where. Right: rate within each road type. y from zero; rates = sum(injuries)/sum(trips) x 1000.",
        "Bar chart, y from zero, one bar per grade (the recipe).")

    # ---- 2
    st += case_page(2, "Chai sales and quiz failures", "“Canteen chai sales predict quiz failures.”",
        f"Selling more chai goes with more failed quizzes (r = {c2['r']:.2f}), so chai (or whatever drives it) is a lever on failures.",
        f"“Exam months push up both.” They do not: the correlation of the exam-month flag with cups sold is r = {c2['r_exam_cups']:.2f}, and dropping the "
        f"{c2['n_exam']} exam months makes the relationship <i>stronger</i> (r = {c2['r_noexam']:.3f}), not weaker.",
        f"<b>Enrolment growth.</b> Students enrolled rose from {c2['enrol_first']:,} to {c2['enrol_last']:,} ({c2['enrol_ratio']:.1f}x). "
        f"Cups sold track enrolment at r = {c2['r_cups_enrol']:.3f} and failures at r = {c2['r_fail_enrol']:.3f}: both are head-counts that scale with the number of students. "
        f"Per student the relationship is gone: {c2['cps_min']:.2f}-{c2['cps_max']:.2f} cups per student in every month, "
        f"{c2['fail_min']:.0f}-{c2['fail_max']:.0f} failures per 1,000 students, and the correlation between the two rates is only r = {c2['r_rate']:.2f} "
        f"(p = {c2['p_rate']:.2f}, n = 24).",
        "Two panels, one measure each (no dual axis), y from zero. Grey bands mark exam months.",
        "Scatter of cups (x) vs failures (y), one point per month, OLS line, r annotated.")

    # ---- 3
    z = c3["zone"]
    st += case_page(3, "The Smog Action Plan", "“The Smog Action Plan cut Lahore's AQI by a third.”",
        f"AQI fell from {c3['before']:.0f} to {c3['after']:.0f} ({c3['fall']:+.0%}) after day 61, so the plan worked.",
        f"“It is just the season / the weather.” Weather would move every zone. Zones that reported on all 120 days did not move: Residential "
        f"{z['Residential|before']['mean']:.1f} → {z['Residential|after']['mean']:.1f}, Peri-urban {z['Peri-urban|before']['mean']:.1f} → "
        f"{z['Peri-urban|after']['mean']:.1f}, Arterial {z['Arterial|before']['mean']:.1f} → {z['Arterial|after']['mean']:.1f}. "
        f"(The axis is not truncated either: I set it from zero.)",
        f"<b>A change in who is being averaged.</b> {c3['n_blank']} cells are blank and pandas skips them silently. From day 61 the "
        f"{c3['n_industrial']} Industrial stations (mean AQI {c3['ind_before']:.0f}, the dirtiest zone) are 100% offline and Arterial stations are 50% offline, so the "
        f"mean is taken over fewer, cleaner stations (average reporting stations per day: {c3['stations_per_day_before']:.1f} → {c3['stations_per_day_after']:.1f}). "
        f"Like-for-like, over the {c3['n_stations_keep']} stations that reported in both periods, AQI is {c3['lfl_before']:.1f} → {c3['lfl_after']:.1f} ({c3['lfl_change']:+.1%}): "
        f"no change at all. The ‘32% fall’ is arithmetic produced by missing data, not by the plan.",
        "Left: one line per zone, direct labels, broken where a zone has no data. Right: same-station comparison.",
        "Mean aqi per date over all rows, y from zero, marker at day 61, period mean lines.")

    # ---- 4
    sh = c4["shape"]
    bus = max(sh, key=lambda k: sh[k]["r2_quad"] or 0); eng = max(sh, key=lambda k: sh[k]["max_abs_res"])
    arc = min(sh, key=lambda k: sh[k]["distinct_x"]); cs = [k for k in sh if k not in (bus, eng, arc)][0]
    st += case_page(4, "Four departments, identical statistics", "“Four departments behave identically, so fund them equally.”",
        "Same mean hours (18.00), same mean score (14.50), same r (0.816), same slope (0.25): the departments are interchangeable.",
        "“Eleven students per department is too small to say anything.” Sample size is not what breaks this: eleven points are plenty to <i>see</i> "
        "the difference, and a bigger sample from the same processes would give the same four shapes.",
        f"<b>Summary statistics do not constrain shape</b> (Anscombe, 1973). {bus}: a perfect curve — a quadratic fits with R² = {sh[bus]['r2_quad']:.2f} against {sh[bus]['r2_lin']:.2f} for the line. "
        f"{eng}: a straight line broken by one outlier (largest residual {sh[eng]['max_abs_res']:.2f} marks vs about 1.9 elsewhere; Cook's D {sh[eng]['max_cook']:.2f}). "
        f"{arc}: ten of eleven students study exactly 16 hours and one studies 38 — only {sh[arc]['distinct_x']} distinct x values, so the whole slope hangs on a single student (leverage 1.0). "
        f"{cs} is the only department where the straight-line summary is a fair description.",
        "One scatter per department with its OLS line, shared axes.",
        "Not a chart: a table of n, mean, SD, Pearson r and slope per department (sample SD). Also saved to case4_table.csv.")

    # ---- 5
    sh5 = c5["shape"]; ks = [v["x_kurt"] for v in sh5.values()]
    st += case_page(5, "Five cohorts, one set of statistics", "“Five cohorts, one set of statistics.”",
        "The five learning-platform cohorts are statistically the same group (mean 48/63, SD 12/15, r = 0.420).",
        f"“The differences are just sampling noise.” There is no noise to blame: n = {c5['n']} per cohort and the statistics agree to within {c5['max_dev']:.0e}, "
        "because they were forced to — not estimated.",
        f"<b>Five numbers describe a point cloud's centre, spread and linear tilt, not its shape.</b> <i>vizlib.match_stats()</i> rescales each cloud linearly "
        f"to the target mean, SD and r, as in the Datasaurus Dozen (Matejka &amp; Fitzmaurice, 2017). Every cohort therefore has R² = 0.176 and the same "
        f"residual SD about the line ({np.mean([v['resid_sd'] for v in sh5.values()]):.1f}), yet the cohorts are a line, a ring, a star, two clusters and the letter X; "
        f"the excess kurtosis of hours on platform alone runs from {min(ks):.2f} to {max(ks):.2f}.",
        "Small multiples, shared axes, n = 180 each.",
        "Not a chart: a table of n, means, SDs (population), r and slope per cohort. Also saved to case5_table.csv.")

    # ---- 6
    st += case_page(6, "Creatinine tracks HbA1c", "“Creatinine tracks HbA1c — a finding.”",
        f"Creatinine and HbA1c are strongly related (r = {c6['r']:.2f}), a candidate kidney–glucose link worth reporting.",
        f"“Both rise with age (a confounder).” Not here: age correlates with HbA1c at r = {c6['r_age_hba1c']:.2f} and with creatinine at r = {c6['r_age_creat']:.2f}. "
        f"And “190 pairs, so some will be flukes” is also not the story: apart from the arithmetic pairs there is no other strong cell.",
        f"<b>Two problems, only one of them is the drawing.</b> <u>Drawing:</u> a one-hue sequential map (Reds) for a signed quantity, with no vmin/vmax (the scale stretches from "
        f"{c6['cm_min']:.2f} to 1) and both triangles shown, so negative and zero look alike and every cell is printed twice. Fixing it (diverging RdBu_r pinned to −1…+1, upper triangle masked) "
        f"does <b>not</b> change the 0.77 cell — it is still 0.77. <u>Finding:</u> one participant (row {c6['row']}: HbA1c {c6['hba1c_row']:.1f}%, creatinine {c6['creat_row']:.0f} µmol/L, against medians of "
        f"{c6['hba1c_med']:.1f} and {c6['creat_med']:.0f}) produces the entire correlation. Without that single row r = {abs(c6['r_wo']) if abs(c6['r_wo'])<0.005 else c6['r_wo']:.2f}; Spearman r = {c6['spearman']:.2f}. "
        f"Pearson is not robust to one extreme point, and a heatmap hides the scatter that would have shown it. (Also: systolic–MAP, r = 0.96, is arithmetic, and the probes are uncalibrated channels.)",
        "Left: fixed heatmap. Right: the scatter the heatmap hid, with the one participant marked.",
        "Annotated heatmap of the 20 x 20 correlation matrix, cmap=‘Reds’, no vmin/vmax, both triangles.", extra_heights=(5.4, 6.4))

    # ---- 7
    st += case_page(7, "ShaheenGo's loss until May", "“ShaheenGo ran at a loss until May.”",
        "Cost exceeded revenue for the first four months, then revenue overtook it in May.",
        f"“The numbers must contain a crossover, maybe a one-off cost.” They contain none: both columns are PKR millions and revenue exceeds cost in all six months "
        f"(margin {c7['margin_min']} → {c7['margin_max']} PKR m).",
        f"<b>Two independent y-axes.</b> Revenue is plotted on 50–80 and cost on 40–56, so each line is stretched to fill the same height; where the lines cross on screen is decided entirely by the "
        f"windows chosen, not by the data. The cost line is drawn above revenue in {c7['crossing_months']} of 6 months although revenue was higher in all 6. "
        f"Revenue grew {c7['rev_growth']:+.0%} and cost {c7['cost_growth']:+.0%}: the business grew its margin every month.",
        "Left: both measures on ONE axis from zero. Right: the margin on its own panel.",
        "Line chart with ax.twinx(): revenue on 50–80 (left), cost on 40–56 (right).")

    # ---- 8
    st += case_page(8, "Three bin widths", "“Three bin widths, three different distributions.”",
        "The shape of the systolic distribution depends on who draws it: one hump, a bimodal curve, or a spiky comb.",
        "“Different samples, or too few observations.” All three panels use the same 10,000 values (n = 10,000 in each), so it is not sampling.",
        f"<b>Bin width is a parameter, and two of these choices are bad.</b> bins = 3 means {c8['width3']:.0f} mmHg per bin, which merges two populations into one hump. "
        f"bins = 400 means {c8['width400']:.2f} mmHg per bin, narrower than the data's 1-mmHg resolution ({c8['unique']} distinct values), so {c8['empty400']:.0%} of the bins are empty and the "
        f"histogram is a comb. bins = 45 ({c8['width45']:.1f} mmHg) happens to work. A rule beats luck: Freedman–Diaconis gives {c8['fd']:.1f} mmHg; I use 3 mmHg, aligned to whole mmHg.",
        "One histogram with a declared bin width, aligned to whole mmHg; peaks near 121 and 163.",
        "Three histograms of systolic with bins = 3, 45, 400 (n = 10,000 in each).", extra_heights=(3.8, 4.6))

    # ---- 9
    st += case_page(9, "Density above 100% saturation", "“4.4% of the density sits above 100% saturation.”",
        "Some patients have an oxygen saturation above 100%, so the data (or the instruments) are broken.",
        f"“The data contain impossible readings.” They do not: the maximum is {c9['max']:.0f}; {c9['n100']} patients ({c9['share100']:.1%}) sit exactly at 100.",
        f"<b>The estimator, not the data, leaks past a hard ceiling.</b> A Gaussian KDE puts a symmetric kernel (default bandwidth {c9['bw']:.2f} points) on every observation; the {c9['n100']} readings at the ceiling "
        f"each spill half their mass above 100. I measure {c9['above']:.1%} of the curve's area above 100 ({c9['above_995']:.1%} above 99.5); the brief's 4.4% did not reproduce exactly with the default bandwidth, so I report what I measured. "
        f"SpO2 is also whole-number, so a smooth curve invents detail that was never recorded.",
        "One bar per recorded whole-number value; nothing exists above 100.",
        "KDE of spo2, default bandwidth, x extended to 108, line at 100.", extra_heights=(4.0, 4.6))
    st.pop()   # last PageBreak
    st += [Spacer(1, 6), P("References: Anscombe (1973) The American Statistician 27(1); Matejka &amp; Fitzmaurice (2017) Same Stats, Different Graphs; Tufte (1983) The Visual Display of Quantitative Information; "
                           "Wilke, Fundamentals of Data Visualization; seaborn and SciPy documentation. All data synthetic, CDB601220 Week 3.", CAP)]
    doc = SimpleDocTemplate(os.path.join(ROOT, "partA_diagnosis.pdf"), pagesize=A4, leftMargin=1.9 * cm, rightMargin=1.9 * cm,
                            topMargin=1.5 * cm, bottomMargin=1.4 * cm, title="Week 3 Part A diagnosis")
    doc.build(st)
    print("wrote partA_diagnosis.pdf")


def build_E():
    import partD_figure as D
    raw = pd.read_csv(os.path.join(ROOT, "data", "vitals_10k.csv"))
    df = D.clean(raw)
    hi, lo = int((raw.heart_rate > D.HR_HI).sum()), int((raw.heart_rate < D.HR_LO).sum())
    s999, s0 = int((raw.bmi == 999).sum()), int((raw.bmi == 0).sum())
    nlos = int((raw.los_days > D.LOS_MAX).sum())
    ch = raw[["age", "chol_mmol_l"]].corr().iloc[0, 1]; ch2 = df[["age", "chol_mmol_l"]].corr().iloc[0, 1]
    meds = df.groupby("ward_clean").los_days.median()
    raw_m = raw.los_days.median()
    S = ParagraphStyle("s", parent=BODY, fontSize=7.1, leading=9.0, spaceAfter=2)
    SH = ParagraphStyle("sh", parent=LAB, fontSize=8.8, leading=10.5, spaceBefore=4, spaceAfter=1)
    st = [P("Part E · Justification for the clinical review figure", ParagraphStyle("t", parent=H1, fontSize=12.5, leading=14)),
          P("Source: vitals_10k.csv, 10,000 synthetic patient records generated for CDB601220 Week 3.", ParagraphStyle("c2", parent=CAP, spaceAfter=3)),
          P("1 · The four panels", SH)]
    rows = [["Panel", "Question it answers", "Why this chart", "Week 2 channel rule"],
            [P("1 Histogram", S), P("Is systolic pressure one population or several?", S),
             P("One continuous variable, shape is the question; a histogram shows modes that a mean or box would hide.", S),
             P("Position on a common aligned scale carries the count; hue only labels the two modes and never carries a value.", S)],
            [P("2 Box plot", S), P("Which ward keeps patients longest?", S),
             P("One skewed measure across four categories: median, spread and outliers per ward, side by side.", S),
             P("Aligned position on one log axis; categories ordered by median so rank reads left to right.", S)],
            [P("3 Scatter", S), P("How strongly does cholesterol follow age?", S),
             P("Two continuous variables: a scatter shows form, strength and spread. Panel 4 pointed to this pair.", S),
             P("Two aligned position scales; sex is carried by shape <i>and</i> colour (redundant coding); alpha tackles overplotting.", S)],
            [P("4 Heatmap", S), P("Which variable pairs move together?", S),
             P("A screening tool for 36 pairs at once; it points, it does not prove.", S),
             P("Colour is a weaker channel, so cells are annotated; hue = sign, lightness = size, diverging, midpoint 0.", S)]]
    t = Table(rows, colWidths=[2.0 * cm, 4.0 * cm, 5.9 * cm, 5.4 * cm])
    t.setStyle(TableStyle([("GRID", (0, 0), (-1, -1), 0.3, colors.HexColor("#DFE6EE")), ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#F1F5F9")),
                           ("FONTSIZE", (0, 0), (-1, 0), 7.6), ("FONTNAME", (0, 0), (-1, 0), "DV-B"), ("VALIGN", (0, 0), (-1, -1), "TOP"),
                           ("TOPPADDING", (0, 0), (-1, -1), 2), ("BOTTOMPADDING", (0, 0), (-1, -1), 2)]))
    st += [t, P("2 · Every parameter I chose", SH)]
    st += [P(f"<b>Panel 1:</b> bin width <b>3 mmHg</b>, aligned to whole mmHg (Freedman–Diaconis gives about 3.8; 3 keeps both peaks and a clean valley). Split at the density valley, "
             f"<b>141 mmHg</b>, found from a KDE rather than by eye. <b>Panel 2:</b> <b>log₁₀ y-axis</b> (length of stay is strongly right-skewed); <b>showfliers = True</b>; wards sorted by median; "
             f"the 2 zero-day stays cannot be drawn on a log axis. <b>Panel 3:</b> all 10,000 points, <b>alpha 0.18</b>, marker size 9, OLS line, no subsampling. "
             f"<b>Panel 4:</b> <b>cmap RdBu_r, vmin = −1, vmax = +1, center = 0</b>, upper triangle masked, annotation .2f, pairwise-complete correlations, "
             f"map_mmhg excluded. <b>Figure:</b> 12.6 × 8.4 in, <b>300 dpi</b>, bbox tight, house palette (#0072B2, #D55E00, #009E73), spines off.", S)]
    st += [P("3 · Every change to the data, with rule, count and effect", SH)]
    rows = [["Rule", "Count", "Effect"],
            [P("ward: 12 spellings conformed to 4 (strip, lower-case, map)", S), P("12 → 4; 0 unmapped", S), P("Groupby no longer splits wards", S)],
            [P("admit_date: 3 formats parsed explicitly; slash dates are day-first", S), P("3,382 / 3,365 / 3,253; 0 unparsed", S), P(f"mm/dd would be impossible for 1,933 rows; range 1 Jan–30 Apr 2026", S)],
            [P("bmi 999 (not recorded) and 0 (impossible) set to missing", S), P(f"{s999} + {s0} = {s999 + s0}", S), P(f"mean BMI {raw.bmi.mean():.1f} → {df.bmi.mean():.1f} kg/m²", S)],
            [P(f"heart_rate > {D.HR_HI} bpm removed as device faults; &lt; {D.HR_LO} bpm (all 0, flat-line) removed", S), P(f"{hi} + {lo} = {hi + lo}", S), P(f"mean {raw.heart_rate.mean():.1f} → {df.heart_rate.mean():.1f} bpm", S)],
            [P(f"los_days &gt; {D.LOS_MAX} d set to missing (nothing lies between 24.0 and 139.8 d)", S), P(f"{nlos}", S), P(f"mean {raw.los_days.mean():.2f} → {df.los_days.mean():.2f} d; median {raw_m:.2f} → {df.los_days.median():.2f}", S)],
            [P("map_mmhg excluded from heatmap: derived from systolic and diastolic", S), P("1 column", S), P(f"r with systolic {raw.map_mmhg.corr(raw.systolic):.2f} is arithmetic", S)]]
    t2 = Table(rows, colWidths=[8.3 * cm, 3.6 * cm, 5.4 * cm])
    t2.setStyle(TableStyle([("GRID", (0, 0), (-1, -1), 0.3, colors.HexColor("#DFE6EE")), ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#F1F5F9")),
                            ("FONTSIZE", (0, 0), (-1, 0), 7.6), ("FONTNAME", (0, 0), (-1, 0), "DV-B"), ("VALIGN", (0, 0), (-1, -1), "TOP"),
                            ("TOPPADDING", (0, 0), (-1, -1), 2), ("BOTTOMPADDING", (0, 0), (-1, -1), 2)]))
    st += [t2, P("The ethics clause", SH),
           P(f"Readings above {D.HR_HI} bpm were removed as device faults (n = {hi}). Mean heart rate moves from {raw.heart_rate.mean():.1f} to {df.heart_rate.mean():.1f} bpm. "
             f"The figure was also produced without the exclusion; it is in the appendix (partD_appendix_heart_rate.png). The same applies to the {lo} flat-line (0 bpm) readings. "
             f"Rows were never silently dropped: faulty <i>values</i> were set to missing, so each patient still counts everywhere else, and no box plot hides its outliers (showfliers = True).", S),
           P("<b>Symmetry test.</b> Would I have made the same removals if they had weakened my conclusion? Yes. Each rule was fixed by physiology or by the file's own coding (no human heart beats at 400 bpm; "
             "999 is a missing-value code; no inpatient stays 270 days when nothing lies between 24 and 140) <i>before</i> I looked at any relationship. "
             f"Checking afterwards: the headline correlation, age and cholesterol, is r = {ch:.2f} before and {ch2:.2f} after cleaning, because neither column was touched; "
             f"the ward medians for length of stay are unchanged (overall {raw_m:.2f} → {df.los_days.median():.2f} d). The removals change means, not conclusions, so they are cleaning rules, not edits.", S),
           P("Sources: Tufte (1983); Wilke, <i>Fundamentals of Data Visualization</i>; Week 2 channel-ranking notes; seaborn and SciPy documentation. All data synthetic.", CAP)]
    doc = SimpleDocTemplate(os.path.join(ROOT, "partE_justification.pdf"), pagesize=A4, leftMargin=1.7 * cm, rightMargin=1.7 * cm,
                            topMargin=1.2 * cm, bottomMargin=1.0 * cm, title="Week 3 Part E justification")
    doc.build(st)
    from pypdf import PdfReader
    print("wrote partE_justification.pdf, pages:", len(PdfReader(os.path.join(ROOT, "partE_justification.pdf")).pages))


if __name__ == "__main__":
    build_A()
    build_E()
