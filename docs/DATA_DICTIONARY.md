# Data dictionary / metric definitions

## games (one record per AppID)

- `appid`: Steam application identifier (primary key)
- `name`: title of game; required
- `release_date`, `release_year`: parsed release date; absent when missing/invalid
- `price`: observed catalog price (USD per dataset documentation); snapshot, not historic release price
- `positive`, `negative`: observed cumulative counts of Steam positive and negative reviews
- `review_count`: positive + negative; does not imply purchase volume
- `positive_rate`: positive / review_count; NULL when no reviews
- `owners_low`, `owners_high`: ends of third-party estimated ownership interval
- `owners_mid`: arithmetic midpoint, *not actual owners, units sold, or revenue*
- `peak_ccu`: captured concurrent player metric; not live
- `average_playtime_forever`: minutes, sourced estimate
- `metacritic_score`: review aggregate, when available
- `windows`, `mac`, `linux`: boolean declared platform support
- `developers`, `publishers`: JSON-encoded credit lists on newer imports; older imports may contain comma-separated strings
- `is_free`: price equals zero; NULL/unknown prices are not free

## game_genres (many-to-many)

`(appid, genre)` composite key; games may have several genres; genre counts overlap.

## import_runs

Importer audit log: timestamp, source, input, valid, rejected and duplicate counts per chunk.

## Quality policy

Records missing AppID/name are rejected. Duplicate AppIDs within a chunk keep the last occurrence. Across chunks, the newer row replaces the previous record. Negative prices, invalid review counts and unreasonable prices are set to missing. Missing counts remain missing in storage, but dashboard total review volume treats undefined counts as 0 with caveats. If a game has one missing review component, review_count is provisional. Historic trends refer to a **snapshot's release cohorts**, not historic year-by-year sales or concurrent player measurements.
