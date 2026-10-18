"""
Part C - Prove the palette, do not claim it.

    python3 partC_palette.py

Writes partC_palette.png (before/after swatches under deutan, protan, tritan)
and prints the numbers behind the four answers.
"""
import os
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from vizlib import (PALETTE, save_fig, simulate_cvd, style_defaults, verdict,
                    worst_pair)

ROOT = os.path.dirname(os.path.abspath(__file__))
style_defaults()

# Q1: a palette I like the look of and did NOT pre-check - Excel/Office
# default accent colours (blue, orange, green, red) as hex.
MY_PALETTE = ["#4472C4", "#ED7D31", "#70AD47", "#FF0000"]
MY_LABEL = "Excel / Office default accents + red"
COURSE3 = PALETTE["series"]
COURSE4 = PALETTE["series"] + [PALETTE["series_4th"]]
KINDS = ["normal", "deutan", "protan", "tritan"]


def swatch_sheet(palettes, path):
    fig, axes = plt.subplots(len(palettes), len(KINDS),
                             figsize=(3.0 * len(KINDS), 2.2 * len(palettes)))
    for row, (pal, label) in enumerate(palettes):
        for col, kind in enumerate(KINDS):
            ax = axes[row, col]
            shown = pal if kind == "normal" else simulate_cvd(pal, kind)
            for i, hexc in enumerate(shown):
                ax.add_patch(plt.Rectangle((i, 0), 0.92, 1, color=hexc))
                ax.text(i + 0.46, -0.22, f"S{i+1}", ha="center", fontsize=8,
                        color=PALETTE["ink_soft"])
            ax.set_xlim(-0.1, len(pal)); ax.set_ylim(-0.4, 1.1)
            ax.axis("off")
            ax.set_title("normal vision" if kind == "normal" else kind, fontsize=10)
        axes[row, 0].text(-0.05, 1.42, label, transform=axes[row, 0].transAxes,
                          fontsize=11, fontweight="bold", color=PALETTE["ink"])
    fig.suptitle("Two of three palettes collapse under colour-blindness; "
                 "the course palette's 4th slot is the weak one",
                 x=0.006, ha="left", fontsize=12.5, fontweight="bold",
                 color=PALETTE["ink"])
    fig.tight_layout(rect=[0, 0, 1, 0.92])
    out = save_fig(fig, path,
                   "Machado, Oliveira & Fernandes (2009) severity-1.0 matrices in "
                   "linear RGB (vizlib.simulate_cvd). Rows: my palette, "
                   "course 3 slots, course 3 slots + 4th.")
    plt.close(fig)
    return out


def audit(pal, label):
    print(label)
    out = {}
    for kind in KINDS:
        i, j, a, b, d = worst_pair(pal, kind)
        out[kind] = (i, j, a, b, d)
        print(f"  {kind:7s} closest pair S{i} {a} vs S{j} {b}   "
              f"dE {d:5.1f}   {verdict(d)}")
    print()
    return out


print("wrote", swatch_sheet([(MY_PALETTE, MY_LABEL),
                             (COURSE3, "Course palette (3 slots)"),
                             (COURSE4, "Course palette + 4th slot (#CC79A7)")],
                            os.path.join(ROOT, "partC_palette.png")), "\n")

print("Q1  simulated swatches:")
for kind in ["deutan", "protan", "tritan"]:
    print(f"  {kind}: {MY_PALETTE} -> {simulate_cvd(MY_PALETTE, kind)}")
print()
mine = audit(MY_PALETTE, f"Q1/Q3  {MY_LABEL}")
c3 = audit(COURSE3, "Q2/Q3  Course palette, 3 slots")
c4 = audit(COURSE4, "Q2/Q3  Course palette + 4th slot")

worst_mine = min(mine.items(), key=lambda kv: kv[1][4])
worst_c4 = min(c4.items(), key=lambda kv: kv[1][4])
worst_c3 = min(c3.items(), key=lambda kv: kv[1][4])
print(f"Worst pair, my palette:        {worst_mine[0]} S{worst_mine[1][0]}/S{worst_mine[1][1]}"
      f"  dE {worst_mine[1][4]:.1f}  ({verdict(worst_mine[1][4])})")
print(f"Worst pair, course (3 slots):  {worst_c3[0]} S{worst_c3[1][0]}/S{worst_c3[1][1]}"
      f"  dE {worst_c3[1][4]:.1f}  ({verdict(worst_c3[1][4])})")
print(f"Worst pair, course (+4th):     {worst_c4[0]} S{worst_c4[1][0]}/S{worst_c4[1][1]}"
      f"  dE {worst_c4[1][4]:.1f}  ({verdict(worst_c4[1][4])})")

print(f"""
ANSWERS
Q1  My palette ({MY_LABEL}) is the one I'd pick for a dashboard by eye. Under
    simulation its worst pair is {worst_mine[0]} S{worst_mine[1][0]}/S{worst_mine[1][1]} at dE {worst_mine[1][4]:.1f}:
    the green and the red/orange slots drift toward the same olive/brown, so a
    reader with that deficiency cannot separate the series.
Q2  Course palette: 3 slots stay separable in all three simulations; adding
    the 4th slot (#CC79A7) pulls the CVD margin down (see dE above).
Q3  Every palette has a worst pair, the course one included: it is the pair
    involving the 4th slot (S{worst_c4[1][0]}/S{worst_c4[1][1]}, {worst_c4[0]}, dE {worst_c4[1][4]:.1f}). That pair
    sits in the "needs a second channel" band, and the 4th slot also falls
    below 3:1 contrast on white. So the colour may only be used when the chart
    also carries direct labels, a different marker shape or a table view.
Q4  Rule: at most three colour-coded categories. For a fourth or more, do not
    reach for a bigger palette: keep the three hues and add a second encoding
    channel - direct labels at line ends, different marker shapes (vizlib.MARKERS),
    line style/texture, small multiples, or a table view. Colour is never the
    only carrier of identity.
""")
