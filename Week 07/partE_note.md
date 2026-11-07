# Part E — note for the board: the screen, its parameters, and the counterfactual

**Message, one sentence:** The published headline says punctuality is improving, and it is: the network rose 1.73 points from 2025 Q2 to 2026 Q2. But every mode got worse, and the rise is a shift of departures toward Metro, which is punctual, not a better service. **Readers:** the Secretary (the headline tile), the finance director (a filtered mode view), and a journalist (the link on its own).

## Parameters, each with a reason

- **Window: 2025 Q2 to 2026 Q2, five complete quarters.** The first and last quarter that are both complete. The partial 2025 Q1 (April only) and partial 2026 Q3 are left out. Comparing the first three complete months (Apr–Jun 2025) with the last three (Jun–Aug 2026) gives +2.02 points, and the first six with the last six (Mar–Aug 2026) gives +1.52. Every window shows a positive headline with every mode lower, so the sign does not depend on this choice. The first-to-last quarter window is the one the screen shows.
- **Unit: on-time departures as a share of departures operated.** A ratio of two counts, summed over the window before dividing. A mean of daily percentages would weight a 300-departure Sunday the same as a 3,000-departure Tuesday, so it is not used.
- **Denominator, stated on the screen: trips operated.** Mix panel: share of departures operated, the same denominator.
- **Aggregation: Kitagawa two-term decomposition** (`dashlib.rate_decomposition`). Exact: within-mode −1.10 plus mix +2.82 equals the change of +1.73.
- **Excluded from punctuality:** the 7 days where on-time exceeded departures operated. Both their on-time and operated counts left the ratio; their boardings and delays are kept.
- **Excluded from the window:** 63 unfiled mode-days, not interpolated, and 30 re-submitted rows removed before any sum.
- **Palette: the course three-slot Okabe-Ito set plus one fourth hue for Ferry.** `vizlib.cvd_report()` gives Bus and Ferry a worst deuteranopia separation of ΔE 7.5. The trend panel separates the modes by marker shape as well as hue. The mix panel labels shares above 4% in place, so Ferry (2%) is named only in its legend. This is a stated limit, not a solved one.

## The counterfactual and the ethics clause

The board is siting its next corridor using a count of boardings, which would be the default reading of a raw map. The count and the rate point to different districts.

| | Top three |
|---|---|
| By **count** of boardings | **D17 Qilabad** (rate rank 7), **D09 Ilyaspur** (rate rank 3), **D13 Mehrabad** (rate rank 8) |
| By **rate** per 1,000 residents | **D12 Lashkar** (count rank 6), **D21 Ushkan** (count rank 7), **D09 Ilyaspur** (count rank 2) |

**One district is on both lists: D09.** The reason it is on both is the finding: it is large and well-used, so it is second on count and still places in the top three per head.

The raw-count version would have sent the corridor to **D17, D09 and D13**, the three largest districts by people using the network. It would have taken the corridor away from **D12 and D21**, the two highest-rate districts (1st and 2nd per 1,000 residents), which are each ranked only 6th and 7th on count. The count is a population measure: r(boardings, population) = **+0.945** across the 24 districts; the per-resident rate correlates with population at only **+0.249**. The five most populous districts hold **12.6%** of the land and **59.9%** of the people.

## Ethics clause

No district was suppressed or merged. The smallest district has 76,721 households and the rate figures rest on large counts, so the funnel question is not the issue; the population effect is. Recommend the corridor is sited on the rate, with the count version shown beside it and labelled as a population measure.

## The filter, and what it invites

Filtering the route table by district and adding the filtered totals double-counts: a route serving several districts is credited to each one. `dashlib.overlap_factor()` gives **3.096×** the network's boardings (28 of 36 routes serve more than one district, up to four). Any by-district boardings figure on the screen must say this, or split the route's boardings across its districts. The screen uses district figures only as rates, not sums.
