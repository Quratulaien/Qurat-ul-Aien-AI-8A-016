"""
Bonus - Week 1 pre-attentive experiment, rebuilt in code.

    python3 popout_experiment.py

Step 1 (always)   builds the four panels -> popout_panels.png
                  and writes popout_results_template.csv
Step 2 (you)      show each panel to FIVE classmates, one at a time, in a
                  different random order per person (see ORDER below), time them
                  with a stopwatch, and fill in popout_results.csv
                  (columns: participant, panel, seconds, count)
Step 3 (always)   if popout_results.csv exists, charts it -> popout_results.png
                  and prints the three-sentence summary numbers.

No timings are invented: without popout_results.csv this script only builds
the panels. Synthetic stimulus grid, seed 1947. Week 1 activity.
"""
from __future__ import annotations

import os

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from vizlib import PALETTE, save_fig, style_defaults

ROOT = os.path.dirname(os.path.abspath(__file__))
style_defaults()
C = PALETTE["series"]

ROWS, COLS, TARGET, N_TARGETS, SEED = 12, 18, "3", 9, 1947
PANELS = {1: "none", 2: "colour", 3: "size", 4: "colour+shape"}


def make_grid(seed=SEED):
    rng = np.random.default_rng(seed)
    others = [d for d in "0123456789" if d != TARGET]
    grid = np.array([[rng.choice(others) for _ in range(COLS)] for _ in range(ROWS)], dtype=object)
    for k in rng.choice(ROWS * COLS, size=N_TARGETS, replace=False):
        grid[k // COLS, k % COLS] = TARGET
    return grid


def draw(ax, grid, title, colour=False, size=False, shape=False):
    ax.set_xlim(-0.5, COLS - 0.5); ax.set_ylim(-0.5, ROWS - 0.5)
    ax.invert_yaxis(); ax.axis("off"); ax.set_title(title, fontsize=10.5, loc="left")
    for r in range(ROWS):
        for c in range(COLS):
            d = grid[r, c]; hit = d == TARGET
            if shape and hit:
                ax.add_patch(plt.Circle((c, r), 0.40, fill=False, edgecolor=PALETTE["ink"], lw=1.6))
            ax.text(c, r, d, ha="center", va="center",
                    fontsize=15 if (size and hit) else 11,
                    fontweight="bold" if (size and hit) else "normal",
                    color=PALETTE["highlight"] if (colour and hit) else PALETTE["ink"])


def build_panels():
    grid = make_grid()
    fig, ax = plt.subplots(2, 2, figsize=(13.0, 8.0))
    draw(ax[0, 0], grid, "1. No channel - you have to read every cell")
    draw(ax[0, 1], grid, "2. Colour - the targets appear before you look", colour=True)
    draw(ax[1, 0], grid, "3. Size only, no colour", size=True)                      # TODO 1
    draw(ax[1, 1], grid, "4. Colour AND shape together (redundant coding)", colour=True, shape=True)   # TODO 2
    fig.suptitle(f"Count the {TARGET}s. Same {N_TARGETS} targets in all four panels, same positions.",
                 x=0.006, ha="left", fontsize=13.5, fontweight="bold", color=PALETTE["ink"])
    fig.tight_layout(rect=[0, 0, 1, 0.94])
    out = save_fig(fig, os.path.join(ROOT, "popout_panels.png"),
                   f"{ROWS}x{COLS} grid, {N_TARGETS} targets, seed {SEED}. Week 1 activity, rebuilt in Matplotlib.")
    plt.close(fig); print("wrote", out)


def write_template(path):
    rng = np.random.default_rng(2026)          # a reproducible random ORDER per person (not results)
    rows = []
    for p in range(1, 6):
        for order, panel in enumerate(rng.permutation([1, 2, 3, 4]), start=1):
            rows.append(dict(participant=f"P{p}", order_shown=order, panel=int(panel), seconds="", count=""))
    pd.DataFrame(rows).to_csv(path, index=False)
    print("wrote", os.path.basename(path), "- panel ORDER per person is randomised (seed 2026); fill in seconds and count")


def chart_results(path):
    d = pd.read_csv(path)
    need = {"participant", "panel", "seconds"}
    assert need <= set(d.columns), f"need columns {need}"
    d = d.dropna(subset=["seconds"]); d["seconds"] = d.seconds.astype(float)
    n = d.participant.nunique()
    m = d.groupby("panel").seconds.mean().reindex([1, 2, 3, 4])
    labels = ["1 none", "2 colour", "3 size", "4 colour\n+ shape"]
    fig, ax = plt.subplots(figsize=(7.4, 4.4))
    ax.bar(range(4), m.values, color=[PALETTE["muted"], C[1], C[0], C[2]], alpha=0.35, width=0.6)     # faded bar
    rng = np.random.default_rng(1)
    for i, p in enumerate([1, 2, 3, 4]):
        s = d[d.panel == p].seconds.values
        ax.scatter(i + rng.uniform(-0.12, 0.12, len(s)), s, color=PALETTE["ink"], s=22, zorder=3)       # strip plot
        ax.text(i, m[p] + 0.03 * m.max(), f"{m[p]:.1f}s", ha="center", fontsize=9)
    ax.set_xticks(range(4), labels); ax.set_ylim(0, d.seconds.max() * 1.15)                           # zero baseline
    fastest, slowest = m.idxmin(), m.idxmax()
    ax.set_title(f"Panel {fastest} was found fastest ({m[fastest]:.1f}s); panel {slowest} slowest ({m[slowest]:.1f}s)")
    ax.set_ylabel("Mean seconds to count the 3s"); ax.grid(axis="x", visible=False)
    out = save_fig(fig, os.path.join(ROOT, "popout_results.png"),
                   f"n = {n}; panel order randomised per participant (random permutation, seed 2026). Dots = individual times.")
    plt.close(fig); print("wrote", out)
    print(f"fastest: panel {fastest} ({PANELS[fastest]}) {m[fastest]:.1f}s | slowest: panel {slowest} ({PANELS[slowest]}) {m[slowest]:.1f}s")
    print(f"redundant coding (4) vs colour alone (2): {m[4] - m[2]:+.1f}s")


if __name__ == "__main__":
    build_panels()
    tpl, res = os.path.join(ROOT, "popout_results_template.csv"), os.path.join(ROOT, "popout_results.csv")
    write_template(tpl)
    if os.path.exists(res):
        chart_results(res)
    else:
        print("popout_results.csv not found: run the timing, save it, and rerun to chart it.")
