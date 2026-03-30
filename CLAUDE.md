# F1 Fantasy Prediction Model

## Project Overview

Mathematical model for optimizing F1 Fantasy team selections. Converts bookmaker odds into expected value projections, then solves for the optimal team using linear programming.

## Key Files

| File | Purpose |
|------|---------|
| `f1-2026.ipynb` | Main notebook — full pipeline from odds to optimal team |
| `run_notebook.py` | Papermill wrapper to execute notebook programmatically |
| `update_f1db.py` | Fetches F1 race data from Jolpica API into `f1db_csv/` |
| `odds_2026.csv` | Current race odds (scraped from Oddschecker or manual) |
| `_prices.csv` | Driver/constructor fantasy prices (scraped from fantasy.formula1.com) |
| `f1db_csv/` | Historical F1 database (2021-2026) |

## Running the Notebook

```bash
# Full run (scrapes odds + prices)
python run_notebook.py

# Skip Oddschecker scraper (use existing odds_2026.csv)
python run_notebook.py --skip-scraper
```

Always use `run_notebook.py` (papermill) — never `jupyter execute` (stale cache issues).

## Notebook Cell Map

| Cell Index | Content |
|------------|---------|
| 2 | Race config: `RACE_CALENDAR`, streak lists (`q_streak_drivers`, `race_streak_drivers`, etc.) |
| 3 (code idx 7) | Oddschecker scraper — `SCRAPER_CELL_INDEX = 7` in run_notebook.py |
| 25 (code) | Race result hrefs + `season_length` for teammate comparisons |
| 34 (code) | Fantasy price scraper (`fetch_f1_fantasy_prices()`) |
| 38 (code) | `TEAMS_PORTFOLIO` — user's 3 fantasy teams with rosters, transfers, budgets |
| Final cells | EV rankings, team optimization output, budget range table, stacked bar chart |

## Editing the Notebook Programmatically

Use `nbformat` — never `json.dump`:
```python
import nbformat
nb = nbformat.read("f1-2026.ipynb", as_version=4)
nb.cells[idx]["source"] = new_source
nbformat.write(nb, open("f1-2026.ipynb", "w"))
```

## Known Gotchas

- F1 Fantasy API uses `FUllName` (not a typo — actual API key spelling)
- F1.com results columns: `Pos.` not `Pos`, `Team` not `Car`, `Time / Retired` not `Time/Retired`
- F1.com driver names: `"George\xa0RussellRUS"` — strip 3-letter country code with regex
- Race result URL: `.../race-result.html` (NOT `.../{circuit}.html`)
- Oddschecker fastest-lap market often blocked by Cloudflare; notebook has fallback logic
- Oddschecker scraper can miss heavy favorites (e.g. showing 501.0 for actual favorites) — always verify scraped odds
- DNF odds are not scraped; they're hardcoded estimates by team reliability tier

## Race Update Workflow

Before each race:
1. Run `update_f1db.py` (set year list to `[2026]`) if new race results available
2. Update cell 2 streak lists based on latest results
3. Update cell 25 `hrefs` list + `season_length` after races complete
4. Update cell 38 `TEAMS_PORTFOLIO` with current team compositions
5. Run notebook via `python run_notebook.py`
6. Verify odds and EV output for anomalies

## Dependencies

Gurobi (QP solver), PuLP (ILP solver), scipy/sklearn (regression), pandas/numpy, matplotlib/seaborn, playwright (scraping), papermill (notebook execution). All in `.venv/`.
