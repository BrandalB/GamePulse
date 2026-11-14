import argparse
from pathlib import Path
from .db import engine_from_env,read_games,read_genres
from .analytics import overview,genre_summary,year_summary,quality_metrics

def generate(out):
    engine=engine_from_env()
    games=read_games(engine);genres=read_genres(engine)
    if games.empty: raise ValueError('Database is empty. Load data first.')
    o=overview(games);q=quality_metrics(games,genres)
    g=genre_summary(games,genres).head(10)
    yr=year_summary(games).tail(10)
    table='\n'.join(f'| {r.genre} | {r.games:,} | {r.review_volume:,} |' for r in g.itertuples())
    ytable='\n'.join(f'| {int(r.year)} | {r.releases:,} |' for r in yr.itertuples())
    src='**Synthetic sample — not Steam market evidence**' if len(games)<=220 and games['name'].astype(str).str.startswith('Demo Game ').all() else '**Imported Steam snapshot — verify provenance/version in README**'
    md=f'''# GamePulse — reproducible analysis summary

{src}

This report is generated from the local database, not typed estimates. Metrics apply to the **currently imported snapshot** and may be affected by missingness and selection bias.

## Overview

- Unique games: **{o['games']:,}**
- Median price among paid games: **${o['paid_median']:,.2f}**
- Free-to-play share among catalog entries with known price (approx.): **{o['free_share']:.1%}**
- Positive share of all counted reviews: **{o['positive_share']:.1%}**
- Total counted reviews: **{o['review_volume']:,}**

## Top 10 genres by game count

| Genre | Games | Reviews |
|---|---:|---:|
{table}

**Genres are multi-label:** totals overlap and should not be summed to get unique games.

## Release cohort sizes (recent 10 in snapshot)

| Release year | Games |
|---|---:|
{ytable}

## Quality audit

- Missing price: **{q['no_price']:,}**
- Missing release date: **{q['no_release_date']:,}**
- Missing ownership range: **{q['no_owners']:,}**
- Missing reviews (zero counted): **{q['no_reviews']:,}**
- Games without genre: **{q['without_genres']:,}**

## Important interpretation limits

The dataset does **not** contain independently verified sales or revenue. Owner-range midpoints are rough estimates, not copies sold. Review counts are not purchases; catalog prices are not historic prices. These release-year comparisons do not reconstruct historical yearly sales.

## Next research questions

1. Compare review distributions within large genre cohorts while controlling for review count.
2. Investigate how paid-game median prices differ across recent release cohorts.
3. Examine which genres have the highest missing ownership and price fields, and whether this affects comparisons.
'''
    p=Path(out);p.parent.mkdir(parents=True,exist_ok=True);p.write_text(md,encoding='utf-8')
    return p

if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--out',default='docs/ANALYSIS_RESULTS.md')
    args=parser.parse_args()
    print(generate(args.out))
