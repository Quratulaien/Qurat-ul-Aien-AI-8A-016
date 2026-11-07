# Part C — note for the board: where is supply least reliable?

**Message, one sentence:** Measured per household, the worst-served districts are D12 (Lashkar), D11 (Kotla) and D13 (Mehrabad), not the largest ones. **Reader:** the Grid Authority board, splitting a reliability budget across 24 districts.

## The quantity and its denominator

The map shows **supply interruptions filed per 1,000 households, over 12 months**. The numerator is the count of interruptions on district feeders (`outages`). The denominator is households, the billed domestic connections in the cleaned register. The legend says so in words. National pooled rate: **43.7 per 1,000 households**.

## Parameters, each with a reason

- **Denominator: households, not population.** Reliability is experienced by connections, and households is the billed unit. Population would also work but would count people without connections.
- **Classes: Jenks natural breaks, 5 classes.** Jenks minimises within-class spread, so the breaks follow the data rather than a rule. Equal intervals would empty most classes, since one district's rate sits far from the rest.
- **Projection: equal-area.** The map colours an area, so an area-distorting projection would change what the eye sees.
- **Scaling: none needed.** The rate is already a ratio; the raw count is shown only in the right-hand panel, as a rank.
- **Window: the 12 months the register covers.** No window was chosen, so none could be cherry-picked.
- **Suppression: none.** The smallest base is 76,721 households. A Poisson funnel test over the 24 districts places 22 outside the limits, so the spread between districts is larger than chance would produce. Small-area noise does not explain the ranking.

## The counterfactual

A raw-count map of interruptions would have pointed at **D17 (Qilabad), D13 (Mehrabad) and D24 (Zhobara)**. Those three hold the most interruptions because they hold the most households. Qilabad ranks **19th** on the rate, and Zhobara **12th**: the count map would send money to districts with a middling rate. It would also have taken money away from **D12** (rate rank 1, count rank 8) and **D11** (rate rank 2, count rank 5), the two highest-rate districts.

Only one district is on both lists. **D13** is second on count and third on rate, so it is the one place both maps agree. The correlation of the count with households is **+0.991**; for the rate it is **+0.175**. The count is almost entirely a population measure, which is the finding.

## Ethics

The count map is a population map: it would route the reliability budget toward the biggest districts (the five most populous hold 12.6% of the land and 59.9% of the people) and away from the districts whose households are most often cut off per head. The rate map is the one that answers "where is service worst". The board should see both, with the count version labelled as a population measure.
