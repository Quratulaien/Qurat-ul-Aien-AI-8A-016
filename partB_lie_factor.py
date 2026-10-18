"""
Part B - Lie Factor, computed in code.

    python3 partB_lie_factor.py

Reads data/case07_lie_factor.csv, calls vizlib.lie_factor() for graphics A-E,
prints the audit table and answers questions 1-5. All data is synthetic,
generated for CDB601220 Week 3.
"""
import os
import pandas as pd
from vizlib import lie_factor, lie_verdict

ROOT = os.path.dirname(os.path.abspath(__file__))
df = pd.read_csv(os.path.join(ROOT, "data", "case07_lie_factor.csv"))

# ------------------------------------------------------------------ Q1: table
rows = []
for _, r in df.iterrows():
    lf, de, ge = lie_factor(r.value_start, r.value_end, r.ink_start, r.ink_end,
                            int(r.ink_dimension))
    rows.append(dict(chart=r.chart_id, subject=r.subject,
                     ink_dim=int(r.ink_dimension),
                     data_effect=de, graphic_effect=ge,
                     lie_factor=lf, verdict=lie_verdict(lf)))
tbl = pd.DataFrame(rows)

print("=" * 92)
print("Q1  Lie Factor audit  (effect = (final - initial) / initial)")
print("=" * 92)
print(f"{'':2}{'Subject':32}{'dim':>4}{'data effect':>13}{'graphic effect':>16}"
      f"{'LF':>8}   verdict")
for _, r in tbl.iterrows():
    print(f"{r.chart:2}{r.subject:32}{r.ink_dim:>4}{r.data_effect:>+13.1%}"
          f"{r.graphic_effect:>+16.1%}{r.lie_factor:>8.2f}   {r.verdict}")

honest = tbl[(tbl.lie_factor >= 0.95) & (tbl.lie_factor <= 1.05)]
under = tbl[tbl.lie_factor < 0.95]
assert len(honest) == 1, "exactly one graphic should be honest"

# Q3 - what happens if ink_dimension is left at 1 for the area-encoded ones
print("\n" + "=" * 92)
print("Q3  Same two charts with ink_dimension left at 1 (the mistake)")
print("=" * 92)
for _, r in df[df.ink_dimension == 2].iterrows():
    wrong, _, ge_wrong = lie_factor(r.value_start, r.value_end,
                                    r.ink_start, r.ink_end, 1)
    right = tbl.loc[tbl.chart == r.chart_id, "lie_factor"].item()
    print(f"  {r.chart_id}: LF with dim=1 -> {wrong:5.2f}   LF with dim=2 -> {right:5.2f}")

# ------------------------------------------------------------------ Q5: dual axis
rev = pd.read_csv(os.path.join(ROOT, "data", "case07_dual_axis_series.csv"))
print("\n" + "=" * 92)
print("Q5  Chart F (dual axis): can a Lie Factor be computed?")
print("=" * 92)
print("  Lie Factor compares ONE data effect with ONE ink effect, measured on a")
print("  single shared scale. A twin-axis chart has two scales; the 'ink' for")
print("  revenue and for cost are not comparable, so there is no single ink ratio")
print("  to put on top of the fraction. The formula is undefined for this chart.")
rev["margin"] = rev.revenue_pkr_m - rev.cost_pkr_m
rev["revenue_cost_ratio"] = rev.revenue_pkr_m / rev.cost_pkr_m
print("\n  What the data says (same unit, PKR millions):")
print(rev.to_string(index=False, float_format=lambda x: f"{x:.2f}"))
print(f"\n  Revenue exceeded cost in all {len(rev)} months "
      f"(smallest margin {rev.margin.min()} in {rev.month[rev.margin.idxmin()]}).")
print(f"  Revenue grew {rev.revenue_pkr_m.iloc[-1] / rev.revenue_pkr_m.iloc[0] - 1:+.0%} "
      f"Jan->Jun, cost {rev.cost_pkr_m.iloc[-1] / rev.cost_pkr_m.iloc[0] - 1:+.0%}; "
      f"margin widened {rev.margin.iloc[0]} -> {rev.margin.iloc[-1]} PKR m.")
print("  ShaheenGo never ran at a loss. The 'loss until May' story is produced by")
print("  the two independently chosen axis windows (50-80 vs 40-56), nothing else.")

# --------------------------------------------------------------- written answers
a = tbl.set_index("chart")
print("\n" + "=" * 92)
print("WRITTEN ANSWERS")
print("=" * 92)
print(f"""
Q2  Which is honest, and what do the other four do wrong?
    Honest: {honest.chart.iloc[0]} (LF {honest.lie_factor.iloc[0]:.2f}). Bars start at zero, ink is a
    length, and the ink ratio (6/5 = +20%) equals the data ratio (30/25 = +20%).
    A  Bars drawn from a 29.6% baseline: the ink encodes (value - 29.6), not the
       value. A 6.7% rise becomes a 500% rise in ink (LF {a.lie_factor['A']:.1f}).
    B  A coin icon scaled 1.5x in height AND width. The reader sees area, which
       grows 2.25x, while the data grew 1.5x (LF {a.lie_factor['B']:.2f}).
    D  Bars start at zero but the second bar is only 12.5% taller while the data
       rose 50%: the ink encodes a smaller change than the data (LF {a.lie_factor['D']:.2f}),
       so the graphic understates.
    E  A bubble whose RADIUS is proportional to the value: area grows with the
       square of the radius, so a 4x value looks like a 16x bubble (LF {a.lie_factor['E']:.2f}).

Q3  Charts needing ink_dimension=2: B and E (icon scaled in both directions;
    bubble sized by radius). If left at 1 the ink ratio is read as a length
    ratio, so the 2.25x (B) and 16x (E) area growth is reported as only 1.5x and
    4x, and the Lie Factor is badly under-reported, hiding the very distortion
    being audited.

Q4  Graphic D has LF {a.lie_factor['D']:.2f} (< 1). An understated chart is still a distortion
    because the reader takes away the wrong size of effect - a 50% rise in air
    pollution looks like a 12.5% rise. Whoever is responsible for the pollution
    (the polluting industry or the authority being judged on air quality)
    benefits, since the problem looks minor and pressure to act is reduced.
    Honesty means LF close to 1.0 in BOTH directions.

Q5  See the printed output above: the Lie Factor is undefined for the dual-axis
    chart because it has no single ink scale, and the data show revenue above
    cost in every month.
""")
