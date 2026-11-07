# Task D1 — bonus note

**What the interaction lets a reader do:** hover any month for its exact MWh per day, and click a zone in the legend to show that zone's line alone against the network total, so the reader can see which zones drive the rise.

**What I would rather they did not do:** use the 12-month button or the range slider to pick a short window and read the slope inside it as the trend. On this series the window decides the sign: the six 12-month windows starting April to September 2025 give four falling slopes (April to July starts, about −2,700 to −10,700 MWh/day per month) and two rising ones (August and September starts, about +3,700 and +9,700). That is the window problem from Week 4 Part B.

Build: `python3 partD_interactive.py` → `partD_interactive.html` (offline, self-contained, 4.8 MB).
