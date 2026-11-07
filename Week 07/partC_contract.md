# Part C — interaction contract: boardings per filed day, by mode

Files: `partC_interactive.html` (the live view, offline) and `partC_default.png` (the default state, static). Both come from `partC_interactive.py`.

**Default state.** Metro's boardings per filed day rose through the period while Bus fell, Apr 2025 to Aug 2026, complete months only; most readers will read the chart as it opens and never touch it.

**Controls.**
- **Legend click:** hides one mode and rescales nothing. It does not change any value that remains visible, so it cannot make a mode look bigger by removing another. Click the entry again to restore it; there is no trap, because a hidden mode is shown as a grey legend entry and the default is one click away from every view.
- **Range slider and the 6m / 12m / all buttons:** zoom the time axis. They change the window shown, not the aggregation: every point is still a monthly mean per filed day. The slider stops at 2026-08, so the partial September cannot be drawn at full weight. "All" returns to the default.
- **Hover:** shows the mean boardings per day and the number of filed days behind each point. The day count is the control that tells a reader how many of the month's days the mean rests on.

**What the controls must not invite, and what was done.** A reader who switches on all four modes and adds their lines together gets "boardings", and may then read it as riders or journeys. A boarding is one vehicle entry; a journey is one passenger trip. Across the file there are about 1.3 boardings per journey (1.305 in this run), so boardings and journeys cannot be added or put on one axis. The chart's title and the hover text both say "boardings", the y-axis says "per filed day", and the legend carries no total. No stacked total is drawn. The journey figures live in the Task B fare charts, which carry their own unit label.
