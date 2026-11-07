# Part F (bonus) — the seasonal swing, on real data

**Source:** Our World in Data, COVID-19 dataset, `owid-covid-data.csv`, github.com/owid/covid-19-data; downloaded 2026-11-07 (`bonus_F_data/download_stamp.txt`). Location used: Pakistan, daily `new_cases`, summed to months for 2020-03 to 2023-12.

**Defects found in the file (audit, `partF_audit.txt`):**
- The file's last month is partial: it ends 4 Aug 2024 (`partial_tail` = True, 4 days in August 2024). It is outside the analysis window, so it is excluded rather than summed.
- The series starts on 5 Jan 2020, so January 2020 is partial too; the analysis begins March 2020.
- No duplicate dates, no gaps, and no negative values for this location.

**Answer to Week 1's question:** neither reading holds cleanly. The within-year range falls by about 40,810 cases a year while the level falls by about 18,469 a year, so the absolute swing is shrinking with the level, not growing. The swing relative to the level grows (range divided by mean: 2.79 in 2020, 5.33 in 2023) because the level collapses faster than the swing does, so a rising ratio here is a denominator effect, not growing seasonality.

**What the figure cannot settle:** this series is driven by pandemic waves, not an annual cycle, so the period-12 decomposition is an assumption rather than a finding; its additive residual sd is 25,480 cases and its multiplicative residual sd is 0.69 (ratio).
