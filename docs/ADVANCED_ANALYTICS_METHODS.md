# GamePulse advanced analytics: metric definitions and design choices

## Release counts and genre growth

`genre_year_trends` counts distinct Steam AppIDs in each genre–release-year combination. It does not sum across genres; a game with multiple genre tags belongs to more than one group. The comparison table calculates `end_releases - start_releases`, and relative change = `(end - start) / start` when the starting count exceeds a user-chosen threshold. The latest observed cohort is omitted by default as a safeguard against incomplete years, although **the supplied dataset's coverage should still be checked manually**.

These results show **catalog composition by original release year** as observed in a later snapshot. They do not show how much a genre earned in a particular year, the number of new players that year, or historic positive ratings at the time of launch.

## Developers and publishers

Each source list is stored as a comma-delimited text field. For group analyses, GamePulse splits that field on commas, trims names, and associates a title with every credited contributor. The same title can appear in multiple organizations' totals. Source rows may use aliases, company rebrands, misspellings, or company names containing commas; no entity resolution is performed. Studio/publisher statistics therefore describe **credited catalog footprint**, not verified legal organization market share.

The weighted review-positive share is `SUM(positive) / SUM(positive+negative)` over a group's games with observed review activity. It is not the mean of the individual title scores. Review totals reflect a single later snapshot and can be higher for older titles.

## Price versus reception

Use snapshot **USD list prices**, not transaction prices. Records are divided into Free, $0.01–5, $5–15, $15–30, $30–60, and $60+ tiers. Games need at least 100 total reviews. The chart reports the share of positive review votes within each tier, weighted by the review counts of titles in that tier. A difference is an association, **not proof that pricing causes reviews to improve or worsen**. Missing prices and missing review activity are excluded.

## Lesser-known highly rated games

A title qualifies when it has a user-selected minimum/maximum review count and at least the user-selected positive review fraction. This is a discovery heuristic, not a claim about low sales, financial performance, or commercial opportunity.

## SQL Lab

Four parameterized **read-only** SELECT queries are provided in `gamepulse/market.py`. All SQL filters use bound parameters rather than string interpolation. The raw `publishers` grouping SQL intentionally does not split contributor lists; use the Python entity summary for multi-credit organization counts.

## Portfolio interpretation

Always label findings with the data source, snapshot, filter scope, cohort window, sample sizes, and relevant uncertainty. Do not report profit, sales revenue, unit sales, or real-time active player estimates from this dataset.
