# GamePulse — Steam Market Intelligence

A data analytics dashboard for exploring historical Steam catalog trends using **Python, Pandas, SQL, Streamlit, and Plotly**.

GamePulse lets users investigate game releases, genres, prices, player reviews, estimated ownership, and studio/publisher catalogs. It uses the imported snapshot; it is **not a live Steam sales tracker**.

## Dashboard features

- **Overview:** Catalog size, price statistics, release trends and review activity.
- **Genres & Pricing:** Genre distribution and pricing comparisons.
- **Reception & Reach:** Review sentiment, activity and estimated ownership.
- **Game Explorer:** Search, filter, export, inspect game details and find similar genres.
- **Compare Games:** Compare selected games side-by-side.
- **Market Insights:** Calculated indicators and high-rated, less-reviewed titles.
- **Genre Trends:** Compare release cohorts by genre.
- **Studios & Publishers:** Catalog footprint, review volume and reception for credited organizations.
- **SQL Lab:** Run and inspect parameterized analytical SQL reports.
- **Findings & Case Study:** Generate a summary from your imported catalog.
- **Data Quality & Methods:** Data coverage, import history and metric definitions.

The interface uses clickable top navigation tabs and sidebar filters.

## Quick start — Windows / VS Code

1. Clone the repository, then open its folder in VS Code.
2. Create and activate a Python environment:

   ```powershell
   python -m venv .venv
   .\.venv\Scripts\Activate.ps1
   ```

3. Install dependencies:

   ```powershell
   python -m pip install -r requirements.txt
   ```

4. For a quick feature preview, load the included **synthetic sample**:

   ```powershell
   python -m gamepulse.load data/sample_games.csv
   python -m streamlit run app.py
   ```

   The sample is fabricated for tests and exploration; **do not use it as evidence about the real Steam market**.

## Use real Steam data

Download the historical cleaned Steam dataset from [Kaggle — Steam Games Dataset 2025](https://www.kaggle.com/datasets/artermiloff/steam-games-dataset). Place `games_march2025_cleaned.csv` in `data/raw/`, then run:

```powershell
python -m gamepulse.load data/raw/games_march2025_cleaned.csv
python -m streamlit run app.py
```

**Important:** If you first loaded the synthetic sample into SQLite, stop Streamlit and remove the local `data/gamepulse.db` before the first real import. This avoids combining sample games with real games. Do **not** remove an existing database that already holds your real imported dataset.

The raw CSV, local database and `.env` are excluded from version control. Other supported local formats may require additional packages; the CSV workflow is the documented path.

## Architecture

```text
Steam CSV → Pandas validation / normalization → SQLite (or PostgreSQL)
                                               ↓
                               SQL and Pandas analytics
                                               ↓
                                Streamlit + Plotly dashboard
```

Code lives in `gamepulse/` (loading, transformations, queries and analytics); `app.py` renders the UI. `sql/analytics.sql` contains example analysis queries. The `tests/` folder verifies data-processing logic, and GitHub Actions runs tests on pushes and pull requests.

## Run tests

```powershell
python -m pytest -q
```

## Generate findings from your imported catalog

```powershell
python -m gamepulse.report --out docs/ANALYSIS_RESULTS.md
```

Only publish that generated report after importing the **real dataset** and reviewing its outputs. This repository does not include an example report with fabricated numbers. Use `screenshots/` for screenshots from the real application.

## Limitations and interpretation

- This is an historical snapshot, not current Steam activity.
- Estimated ownership is **not** verified sales, purchases or revenue.
- List price does not establish historical selling price or profit.
- Review sentiment represents recorded reviews, not every player.
- Games may have multiple genres and credited developers/publishers. Historical comma-delimited names are normalized on a best-effort basis.
- Missing fields and incomplete release years can affect comparisons.

See [`docs/DATA_DICTIONARY.md`](docs/DATA_DICTIONARY.md) and [`docs/ADVANCED_ANALYTICS_METHODS.md`](docs/ADVANCED_ANALYTICS_METHODS.md) for metric definitions.

## Technologies

Python · Pandas · SQLAlchemy · SQLite / optional PostgreSQL · Streamlit · Plotly · pytest · GitHub Actions

## Dataset credit

Steam Games Dataset 2025 (historical snapshot) from Kaggle: https://www.kaggle.com/datasets/artermiloff/steam-games-dataset. The dataset is not distributed with this repository. The included sample CSV is synthetic.

## License

See [LICENSE](LICENSE) for project source licensing. Dataset rights remain with their respective owners.
