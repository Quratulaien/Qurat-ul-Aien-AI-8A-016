"""
Builds partA_diagnosis.pdf (nine cases) and partE_justification.pdf (one page)
from the figures and printed numbers of the part scripts. Re-run it AFTER you
have collected Part C readers: it reads partC_reader_results.csv and writes
your real mean overlap into Part E.
"""
from pathlib import Path

import pandas as pd
from PIL import Image as PILImage
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import cm
from reportlab.platypus import (Image, KeepTogether, PageBreak, Paragraph,
                                SimpleDocTemplate, Spacer)

HERE = Path(__file__).resolve().parent

# DejaVu Sans ships with matplotlib and has Δ, ρ, χ², √ and superscripts that
# reportlab's built-in Helvetica lacks.
import matplotlib
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.fonts import addMapping
_FD = Path(matplotlib.get_data_path()) / "fonts" / "ttf"
for _n, _f in (("DV", "DejaVuSans.ttf"), ("DV-B", "DejaVuSans-Bold.ttf"),
               ("DV-I", "DejaVuSans-Oblique.ttf"), ("DV-BI", "DejaVuSans-BoldOblique.ttf")):
    pdfmetrics.registerFont(TTFont(_n, str(_FD / _f)))
addMapping("DV", 0, 0, "DV"); addMapping("DV", 1, 0, "DV-B")
addMapping("DV", 0, 1, "DV-I"); addMapping("DV", 1, 1, "DV-BI")
STUDENT = "Qurat ul Aien · Roll No. AI-016 · CDB601220 Data Visualization · Week 5"
ss = getSampleStyleSheet()
H1 = ParagraphStyle("h1", parent=ss["Heading1"], fontName="DV-B", fontSize=15, spaceAfter=4,
                    textColor=colors.HexColor("#16202E"))
H2 = ParagraphStyle("h2", parent=ss["Heading2"], fontName="DV-B", fontSize=12, spaceBefore=4, spaceAfter=3,
                    textColor=colors.HexColor("#0072B2"))
B = ParagraphStyle("b", parent=ss["BodyText"], fontName="DV", fontSize=9, leading=12, spaceAfter=3)
SM = ParagraphStyle("sm", parent=B, fontSize=7.5, leading=9.5, textColor=colors.HexColor("#5B6573"))

CASES = [
    ("Population and healthcare access are unrelated — the large countries are spread right across the range",
     "Conclusion invited: a country's size tells you nothing about its access. <b>Decoy:</b> 'the log x-axis "
     "distorts the picture'. Ruled out: GDP spans $283–$120,219 (425×), a multiplicative spread, so log is the "
     "correct axis — the x and y positions are fine.",
     "<b>A value driving the mark's radius instead of its area.</b> <i>s</i> is area in points², so "
     "<i>s = pop_m**2</i> makes the <b>diameter</b> proportional to population: 589× across (area 346,921×). "
     "Wessant's mark is 353 pt = <b>4.9 in</b> wide on a 6.4 in figure and buries the others, while the 9 "
     "countries under 2.0 M are under 2 pt across (3 under 1 pt). <i>Finding: the brief's '589× the area' "
     "reproduces as 589× the diameter.</i> With the size channel repaired the relation is weak but positive: "
     "r(log pop, access) = +0.27; countries ≥ 50 M average 53.4 vs 47.7.",
     "Area ∝ population with sizes=(16, 1600) pt² (10× across), size legend with real values (1, 50, 350 M), "
     "region hue plus letter."),
    ("The outbreak is concentrated in the three districts around the capital",
     "Conclusion invited: D17, D13 and D09 are where the risk is. <b>Decoy:</b> 'the class scheme put them "
     "there'. Ruled out: equal-interval and Jenks put D17 alone in the top count class and quantile puts "
     "D09/D11/D13/D17/D24 there — every scheme ranks the same big districts, because the ranking is by count.",
     "<b>A raw-count choropleth is a population map.</b> r(cases, population) = <b>+0.986</b>, r(rate, "
     "population) = <b>−0.000</b>. The count top three hold 6.3–11.0 M people each (41.8% of residents, 42.8% "
     "of cases) and their rates are 49.9, 64.0 and 51.0 against a national 52.8. Top three by rate: "
     "<b>D19, D20, D21</b> — overlap with the count list: <b>zero</b>.",
     "The same map, normalised: cases per 100,000 residents, legend titled with the denominator."),
    ("GDP per capita barely varies across the sample",
     "Conclusion invited: income is roughly equal everywhere. <b>Decoy:</b> 'GDP genuinely varies little'. "
     "Ruled out: GDP has the highest coefficient of variation of the five columns (<b>2.65</b> vs 0.19–0.40), "
     "and even without its largest value it spans $283–$13,009 (<b>46×</b>).",
     "<b>Min–max scaling flattened by one outlier.</b> Aldonia's $120,219 is <b>9.2×</b> the next country, so "
     "the min–max denominator is set by one row: <b>58 of 60</b> countries land under 0.10 and the median at "
     "<b>0.017</b>; the other 59 share 10.6% of the axis. z-scoring has the same problem (Aldonia +7.5 sd).",
     "Same parallel coordinates chart, one decision changed: percentile-rank scaling (median 0.508; the 59 "
     "use 98% of the axis). <i>Not fixed by changing the chart type.</i>"),
    ("Healthcare access and case rate are unrelated — there is no crossing pattern between them",
     "Conclusion invited: no link between access and cases. <b>Decoy:</b> 'n = 60 is too small to show a "
     "pattern'. Ruled out: r = −0.80 with n = 60 has p = 1.9 × 10⁻¹⁴.",
     "<b>An axis order that separates the related pair.</b> Crossings are only readable between ADJACENT "
     "axes; in file order access and cases are <b>three apart</b>. Placed side by side, <b>81%</b> of line "
     "pairs cross (an X, r = <b>−0.799</b>); the four file-order gaps show only 15%, 21%, 28% and 71%.",
     "Same chart, same min–max scaling, order decision changed: greedy |r| chain access → cases → urban → "
     "median age → GDP. <i>Not fixed by changing the chart type.</i>"),
    ("There is a clear five-level gradient in incidence across the federation",
     "Conclusion invited: risk rises steadily across the map. <b>Decoy:</b> 'just use Jenks or equal "
     "interval instead'. Ruled out: all three schemes still paint five confident colours (breaks within "
     "31.07–33.40) — no scheme can say whether a pattern exists.",
     "<b>Five quantile classes painted over a 7.2% spread.</b> Rates run 31.07–33.40 per 100,000, a spread "
     "of <b>7.2%</b> of the mean (2.33 per 100,000), while each district's 95% Poisson interval is "
     "±3.7 to ±5.2 and <b>all 24</b> contain the pooled 32.2. A χ² homogeneity test gives <b>2.3 on 23 df "
     "(p = 1.00)</b> — less variation than chance alone would produce.",
     "A dot plot of the 24 rates with 95% intervals and the pooled line: no detectable gradient, so no map."),
    ("Unit U32 is a hotspot — it is running at nearly five times the national rate",
     "Conclusion invited: U32 needs intervention. <b>Decoy:</b> 'U32 really has an outbreak'. The file "
     "states all 40 units share one true rate; and every other 'high' unit (15.4, 12.3, 12.2…) is a small unit "
     "inside the funnel.",
     "<b>A small-denominator rate read as a hotspot.</b> U32's 40.9 (<b>4.7×</b> the pooled 8.72) comes from "
     "<b>9 cases in 22,000 people</b>; its exact 95% interval is 18.7–77.7 (a 4.2-fold range). The 10 units "
     "over 100,000 people all sit at 5.5–12.0; the 10 units under 25,000 span 0–40.9. U32 is outside the 99.8% "
     "funnel (P = 0.0002), which with 40 units happens on about 1 map in 143 — a rare extreme, not a measured rate.",
     "A funnel plot (rate vs population, 95% and 99.8% Poisson limits). Rule: flag U32 for follow-up, merge "
     "units under ~43,000 people before mapping."),
    ("District income and case rate are only weakly related — r is about −0.31",
     "Conclusion invited: income barely matters. <b>Decoy:</b> 'n = 24 is too small for a reliable r'. "
     "Ruled out as the cause: the SAME people give very different r at different scales, which n cannot explain.",
     "<b>A correlation quoted at the wrong areal scale (MAUP).</b> Across 24 districts r = <b>−0.308</b> "
     "(p = 0.14); aggregated to the 6 zones of districts_coarse, r = <b>−0.889</b> (−0.746 with "
     "population-weighted income). Within zones it ranges from −0.69 to +0.77. The coefficient is a property "
     "of the units, not only of income and disease; and a zone-level r says nothing about individuals "
     "(ecological fallacy).",
     "Both scales side by side, each r labelled with its unit; state the scale the decision is made at."),
    ("This is a rural outbreak — look how much of the map is dark",
     "Conclusion invited: risk lives in the big, empty districts. <b>Decoy:</b> 'the projection inflates the "
     "north'. Ruled out: the map is Lambert equal-area (error &lt; 10⁻¹⁰ %); even Mercator would inflate north "
     "vs south by only 1.21× (Part B4).",
     "<b>Area read as people.</b> The five most populous districts are <b>12.6% of the land and 59.9% of the "
     "people</b>; the top two rate classes cover 31.2% of land but 26.5% of people. The middle class holds "
     "<b>49.5% of residents on 25.3% of land</b>. And the rate has no link to density at all: r(rate, density) "
     "= <b>+0.001</b> (+0.14 on log density) — nothing here is 'rural'.",
     "A sorted bar chart of rate with each district's population, beside land-share vs people-share for every "
     "rate class."),
    ("Region A is the stronger of the two — its profile encloses visibly more area",
     "Conclusion invited: A outperforms B. <b>Decoy:</b> 'the six axes are on different scales'. Ruled out: "
     "all six indicators are 0–100.",
     "<b>A radar chart whose enclosed area depends on axis order.</b> The means are <b>62.3 vs 62.0</b> "
     "(difference 0.33), but area multiplies NEIGHBOURING values: file order gives 9,933 vs 9,433, and across "
     "the 60 distinct orders A − B ranges from −1,131 to +1,659 — B encloses more in <b>21 of 60</b>. B "
     "leads on 3 of 6 indicators (coverage by 42.7, funding favours A by 35.5).",
     "A dot plot (dumbbell) on one position axis, sorted by the difference, with the six gaps printed."),
]


def img(path, width):
    w, h = PILImage.open(path).size
    return Image(str(path), width=width, height=width * h / w)


def diagnosis():
    doc = SimpleDocTemplate(str(HERE / "partA_diagnosis.pdf"), pagesize=A4,
                            leftMargin=1.6 * cm, rightMargin=1.6 * cm, topMargin=1.4 * cm,
                            bottomMargin=1.4 * cm, title="Part A diagnosis — Week 5",
                            author="Qurat ul Aien (AI-016)")
    W = A4[0] - 3.2 * cm
    st = [Paragraph("Week 5 · Part A — nine charts, taken apart", H1), Paragraph(STUDENT, SM),
          Spacer(1, 6),
          Paragraph("Each case: the faithful rebuild (left) and the redesign (right), then the conclusion "
                    "and decoy, the lying channel or boundary with the number that proves it, and the "
                    "redesign. Self-checks are asserted in <i>partA_charts.py</i>; every number is printed in "
                    "<i>partA_output.txt</i>. All data is synthetic course data generated for CDB601220.", B),
          Spacer(1, 4)]
    for i, (claim, decoy, mech, red) in enumerate(CASES, 1):
        st.append(KeepTogether([
            Paragraph(f"Case {i} · “{claim}”", H2),
            img(HERE / f"partA_case{i:02d}.png", W), Spacer(1, 4),
            Paragraph("<b>1 · Rebuild.</b> Recipe followed exactly; self-check reproduced and asserted.", B),
            Paragraph("<b>2 · Conclusion and decoy.</b> " + decoy, B),
            Paragraph("<b>3 · Mechanism.</b> " + mech, B),
            Paragraph("<b>4 · Redesign.</b> " + red, B)]))
        if i < 9:
            st.append(PageBreak())
    doc.build(st)


E = ParagraphStyle("e", parent=B, fontSize=7.9, leading=10.2, spaceAfter=2)
EH = ParagraphStyle("eh", parent=E, fontSize=9.2, leading=11, spaceBefore=4, spaceAfter=1,
                    textColor=colors.HexColor("#0072B2"), fontName="DV-B")


def part_c_sentence():
    p = HERE / "partC_reader_results.csv"
    if not p.exists():
        return ("<b>[Part C readers not yet run — after `python partC_maps.py --record` for each of "
                "at least five real readers, re-run build_reports.py and this sentence is replaced by "
                "the measured mean overlap.]</b>")
    df = pd.read_csv(p)
    a_hits = sum(len({r.mapA_1, r.mapA_2, r.mapA_3} & {"Dunmere", "Pellbrook", "Grimsby"})
                 for r in df.itertuples())
    return (f"In Part C, <b>{len(df)} real readers</b> chose police counties from each map; their Map A "
            f"and Map B choices overlapped by a mean of <b>{df.overlap.mean():.2f} of 3</b>, and "
            f"{a_hits} of their {3*len(df)} Map A picks were the three most populous counties.")


def justification():
    doc = SimpleDocTemplate(str(HERE / "partE_justification.pdf"), pagesize=A4,
                            leftMargin=1.3 * cm, rightMargin=1.3 * cm, topMargin=1.0 * cm,
                            bottomMargin=0.9 * cm, title="Part E justification — Week 5",
                            author="Qurat ul Aien (AI-016)")
    P = lambda t: Paragraph(t, E)
    st = [Paragraph("Week 5 · Part E — justification of the three health figures",
                    ParagraphStyle("t", parent=H1, fontSize=12.5, spaceAfter=1)),
          Paragraph(STUDENT + " · synthetic course data; geolib/vizlib used unchanged, no geopandas", SM),

          Paragraph("1 · Which variable got which channel, and why (slide 8's budget)", EH),
          P("D1 spends the channels in the order the reader must compare: the two quantities to read "
            "precisely get the two <b>positions</b> — x = GDP per capita on a <b>log</b> axis (a multiplicative "
            "spread, $283–$120,219) and y = healthcare access (a bounded 0–100 index). Population gets "
            "<b>area</b>, which is read only roughly, so it carries the 'how many people' context and a size "
            "legend with real values (1, 50, 350 M) lets readers convert it back; the radius goes as √, never "
            "linearly (sizes = 16–1,600 pt², 10× across — Part B1). Region is identity, not amount, so it gets "
            "<b>hue</b> (six Okabe–Ito colours) plus the region letter on each mark, because the green/pink "
            "pair falls to ΔE 7.5 under deuteranopia. The GDP outlier (Aldonia, 9.2× the next) is kept and "
            "labelled; the log axis holds it."),

          Paragraph("2 · Parallel coordinates decisions", EH),
          P("<b>Scaling: percentile rank</b>, chosen before drawing, because min–max puts 58/60 countries "
            "under 0.10 on GDP and z-scoring puts Aldonia at +7.5 sd (Part B3); rank keeps each country's order, "
            "which is what crossings are read from, and I printed the real min and max at each axis end. "
            "<b>Order: the greedy |r| chain</b> (access → cases → urban → median age → GDP), computed with a "
            "pandas-3-safe copy of geolib.corr_chain (the original crashes on pandas 3 — reported as a finding). "
            "<b>Clutter:</b> all 60 grey, Borealis brushed. It showed an X between access and cases (81% of "
            "lines cross, r = −0.80) and — the relationship a Pearson scatter-matrix would have hidden — median "
            "age and GDP running almost parallel: <b>ρ = +0.87 but Pearson r = +0.28</b>, because one outlier "
            "drags r down; only 16% of lines cross in that gap. PCA confirms two axes miss 16.3% of the variation."),

          Paragraph("3 · Spatial decisions", EH),
          P("<b>Denominator:</b> resident population, so the map shows cases per 100,000 residents (written in "
            "the legend title) — the question is risk, and counts track population (r = +0.986). "
            "<b>Classification:</b> Jenks natural breaks, 5 classes (GVF 0.969 vs 0.908 for quantile), breaks "
            "printed in the legend with the number of districts in each. <b>Projection:</b> Lambert cylindrical "
            "equal-area at 30.5°N, because colour over area makes area the channel; Mercator would have inflated "
            "the north 1.49× and the south 1.24× (Part B4 — geolib's self-check figure uses the linear, not the "
            "area, scale). The join was checked: 24/24 matched, 0 failed. <b>Suppression:</b> rule set at "
            "< 20 cases per district; none qualified (smallest 186 cases), so nothing was merged. For the "
            "small-area file the same rule would merge every unit under ~43,000 people, the population below "
            "which 9 and 18 per 100,000 cannot be told apart (Part B5) — at the price of losing U32's signal."),

          Paragraph("4 · The counterfactual", EH),
          P("A raw-count map of this outbreak would have coloured <b>D17 Qilabad, D13 Mehrabad and D09 "
            "Ilyaspur</b> darkest — the three biggest urban districts, 6.3–11.0 M people each — and told a "
            "health ministry to send its teams to the cities. Two of the three run at or below the national rate "
            "(51.0 and 49.9 vs 52.8). The districts actually at highest risk, <b>D19, D20 and D21</b> in the "
            "north (69–76 per 100,000, 1.1–1.8 M people), would have been pale. The cost lands on two groups: "
            "the city residents whose districts are labelled 'outbreak areas' every week, and the northern "
            "residents whose real risk is never shown. " + part_c_sentence() + " Week 4's lesson applies "
            "unchanged: the denominator is a modelling decision, and a map is never neutral because it points "
            "at a place where people live."),
          ]
    doc.build(st)


if __name__ == "__main__":
    diagnosis()
    justification()
    print("built partA_diagnosis.pdf and partE_justification.pdf")
