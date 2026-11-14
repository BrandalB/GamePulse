from __future__ import annotations

import pandas as pd
from .market import genre_year_trends, genre_growth


def summarize_findings(games: pd.DataFrame, genres: pd.DataFrame,
                       start_year: int | None = None, end_year: int | None = None) -> list[dict]:
    if games.empty:
        return []
    n = int(games['appid'].nunique())
    findings = [{
        'title': 'Games in the imported catalog', 'value': f'{n:,}',
        'explanation': f'There are {n:,} distinct Steam AppIDs in the database.',
        'limitation': 'The imported snapshot is not a live or necessarily complete Steam catalog.'
    }]
    prices = pd.to_numeric(games['price'], errors='coerce').dropna()
    if len(prices):
        free = int(prices.eq(0).sum())
        findings.append({
            'title': 'Free-to-play footprint', 'value': f'{free / len(prices):.1%}',
            'explanation': f'{free:,} of {len(prices):,} games with a known listed price are priced at $0.',
            'limitation': 'List price is from a historical snapshot; it does not establish past pricing or revenue.'
        })
    if not genres.empty:
        genre_counts = genres[genres['appid'].isin(games['appid'])].drop_duplicates(['appid', 'genre']).groupby('genre')['appid'].nunique()
        if not genre_counts.empty:
            name, count = genre_counts.sort_values(ascending=False).index[0], int(genre_counts.max())
            findings.append({
                'title': 'Most frequent genre label', 'value': str(name),
                'explanation': f'{count:,} distinct games carry the {name} genre label.',
                'limitation': 'Genres overlap; a game can appear under multiple genre labels.'
            })
    reviews = pd.to_numeric(games['review_count'], errors='coerce').fillna(0)
    active = int(reviews.ge(100).sum())
    findings.append({
        'title': 'Games with 100+ reviews', 'value': f'{active:,}',
        'explanation': f'{active:,} of {n:,} games have at least 100 recorded reviews ({active / n:.1%}).',
        'limitation': 'Review activity is not sales and is not measured at each game’s launch date.'
    })
    if start_year is not None and end_year is not None and start_year < end_year:
        trend = genre_year_trends(games, genres, start_year, end_year)
        growth = genre_growth(trend, start_year, end_year, min_base=5)
        if not growth.empty:
            top = growth.iloc[0]
            findings.append({
                'title': 'Largest increase in genre-tagged releases', 'value': str(top['genre']),
                'explanation': f"Titles tagged {top['genre']}: {int(top['start_titles']):,} releases in {start_year} compared with {int(top['end_titles']):,} in {end_year} ({int(top['change']):+} change).",
                'limitation': 'These are release counts from the snapshot, not game revenue or historical popularity. The last observed year was excluded as potentially incomplete.'
            })
    return findings


def make_case_study(games: pd.DataFrame, genres: pd.DataFrame,
                    start_year: int | None = None, end_year: int | None = None) -> str:
    findings = summarize_findings(games, genres, start_year, end_year)
    lines = [
        '# GamePulse — Steam Market Intelligence: Case Study', '',
        '## Purpose',
        'Explore historical Steam catalog data to compare genre mix, pricing and review activity.', '',
        '## Tools', 'Python, Pandas, SQL, Streamlit, Plotly and SQLite (optional PostgreSQL).', '',
        '## Process',
        '1. Load and validate a public Steam catalog CSV.',
        '2. Store unique games and their genre labels in related database tables.',
        '3. Calculate summary metrics and build interactive charts.',
        '4. Audit missing values, discuss limitations and test key calculations.', '',
        '## Findings (generated from the imported database)',
    ]
    for item in findings:
        lines += [f"### {item['title']} — {item['value']}", item['explanation'],
                  f"**Limitation:** {item['limitation']}", '']
    lines += [
        '## Lessons learned',
        '_Write 2–3 sentences in your own words about one data-cleaning problem and how you fixed it._', '',
        '## Screenshots', '_Add screenshots of the dashboard before publishing._', '',
        '## Responsible interpretation',
        'This project does not contain verified units sold, revenue or profit. Estimated owners are not transactions. Reviews and snapshot prices cannot establish causal relationships.', '',
        '## Data source',
        '[Steam Games Dataset 2025](https://www.kaggle.com/datasets/artermiloff/steam-games-dataset). Verify the exact file and snapshot version used before publishing.', ''
    ]
    return '\n'.join(lines)
