#!/usr/bin/env python3
"""
partC_reader_trial.py — run ONE reader through the pie-vs-bars ranking test.

A real person must do this. Run it, open the stimulus image when prompted,
and type the letters A–H in order, largest first. Each trial is timed with
time.perf_counter() from the moment the stimulus is shown until Enter.

    python3 partC_reader_trial.py --reader R1

Appends one row per trial to pie_ranking_results.csv and prints how many
positions were wrong against the true order. Nothing here fabricates a
result: if you do not run it with a person, the CSV stays empty.
"""
from __future__ import annotations

import argparse
import csv
import os
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
RESULTS = os.path.join(HERE, "pie_ranking_results.csv")
TRUE = ["A", "B", "C", "H", "G", "D", "E", "F"]  # shares_eight.csv, largest first
STIMULI = {
    "pie": os.path.join(HERE, "partC_stim_pie.png"),
    "bars": os.path.join(HERE, "partC_stim_bars.png"),
}
FIELDS = ["stimulus", "reader_id", "trial_no", "order_given", "seconds",
          "n_wrong_positions", "wrong_positions_note"]


def score(given: list[str]) -> tuple[int, str]:
    """Count positions that differ from the true order, and say where they fell."""
    wrong = [i + 1 for i, (g, t) in enumerate(zip(given, TRUE)) if g != t]
    if len(given) != len(TRUE) or len(set(given)) != len(given) or set(given) != set(TRUE):
        return -1, "invalid answer: must be each of A–H exactly once"
    note = "positions " + ", ".join(map(str, wrong)) if wrong else "all positions correct"
    return len(wrong), note


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--reader", required=True, help="an anonymous reader id, e.g. R1")
    ap.add_argument("--out", default=RESULTS,
                    help="results CSV path (default: the submission file). Use a scratch path for tests.")
    ap.add_argument("--first", choices=["pie", "bars"], default="pie",
                    help="which stimulus this reader sees first; alternate between readers")
    args = ap.parse_args()
    order = [args.first, "bars" if args.first == "pie" else "pie"]
    results_path = args.out
    new = not os.path.exists(results_path) or os.path.getsize(results_path) == 0
    with open(results_path, "a", newline="") as f:
        w = csv.DictWriter(f, fieldnames=FIELDS)
        if new:
            w.writeheader()
        trial = 0
        for stim in order:
            trial += 1
            print(f"\nTrial {trial}: stimulus = {stim}")
            print(f"Open: {STIMULI[stim]}")
            print("Type the letters A–H, largest first, separated by spaces, then Enter.")
            input("Press Enter when you are ready to start the timer... ")
            t0 = time.perf_counter()
            answer = input("> ").replace(",", " ").split()
            seconds = round(time.perf_counter() - t0, 2)
            n_wrong, note = score([a.upper() for a in answer])
            if n_wrong < 0:
                print(note, "- this trial will be recorded as invalid and not scored.")
            w.writerow(dict(stimulus=stim, reader_id=args.reader, trial_no=trial,
                            order_given=" ".join(a.upper() for a in answer),
                            seconds=seconds, n_wrong_positions=n_wrong,
                            wrong_positions_note=note))
            print(f"time {seconds} s; {note}")
    print(f"\nSaved to {results_path}")


if __name__ == "__main__":
    sys.exit(main())
