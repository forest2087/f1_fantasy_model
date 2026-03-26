# F1 Fantasy Prediction Model

A mathematical model for optimizing Formula 1 Fantasy team selections by converting bookmaker odds into expected value projections and solving for the optimal team using linear programming.

## How It Works

The model follows a pipeline:

1. **Odds Ingestion** - Automatically scrape shortest decimal odds from Oddschecker across 5 markets (winner, top3, top6, top10, fastest lap) via Playwright, with DNF estimates by team reliability tier. Falls back to `odds_2026.csv` if scraping fails
2. **Position Distributions** - Solve a quadratic program (Gurobi) per driver to produce smooth finishing position probability distributions (P1-P22) anchored to odds brackets
3. **Race EV** - Calculate expected fantasy points from race positions, fastest lap, DNF penalty, and sprint races
4. **Regression Models** - Fit historical data (2021-2025) to predict qualifying EV, Q2/Q3 appearance probability, and position gains using polynomial, logistic, and linear regression
5. **Teammate Comparisons** - Estimate beat-teammate probabilities from season data with Bayesian shrinkage, adjusted for DNF scenarios
6. **Streak Modelling** - Calculate expected value of qualifying and race streak bonuses
7. **Team Optimization** - Solve an integer linear program (PuLP) to select the optimal 5 drivers + 2 constructors within the budget cap

## Models

| Notebook | Season | Grid |
|----------|--------|------|
| `f1-2026.ipynb` | 2026 | 22 drivers / 11 teams (new regulation era) |
| `f1-2024.ipynb` | 2024 | 20 drivers / 10 teams |

### 2026 Key Updates

- 22-driver grid (Cadillac enters as 11th team, Sauber becomes Audi)
- New power unit regulations (50/50 ICE/electric split)
- Active aerodynamics replacing DRS
- Updated Fantasy scoring (sprint DNF reduced to -10)
- Pre-season teammate estimates from odds-derived position distributions

## Data

| File | Description |
|------|-------------|
| `odds_2026.csv` | Bookmaker odds for 2026 season (auto-updated by notebook scraper, or manual fallback) |
| `odds.csv` | Bookmaker odds (2024 format) |
| `_prices.csv` | Fantasy driver/constructor prices (auto-updated by notebook scraper, or manual fallback) |
| `f1db_csv/` | Historical F1 database (results, qualifying, races, drivers, etc.) |

## Usage

```bash
# Setup
python3 -m venv .venv
source .venv/bin/activate
pip install gurobipy pulp scipy scikit-learn pandas numpy matplotlib seaborn unidecode
pip install playwright && playwright install chromium

# Run
jupyter notebook f1-2026.ipynb
```

### Before Each Race

1. Update `RACE_SLUG` in the odds scraper cell (e.g. `australian-grand-prix`, `chinese-grand-prix`) — odds and prices are scraped automatically when you run the notebook
2. Update race URLs in the teammate comparison section as races complete
3. Update streak driver lists based on current streak status
4. Run all cells to get optimal team selection

> **Note:** If Playwright is not installed or scraping fails, the notebook falls back to the existing `odds_2026.csv` and `_prices.csv` files. You can also update these CSVs manually.

## Dependencies

- **gurobipy** - Quadratic programming (position distributions)
- **pulp** - Integer linear programming (team optimization)
- **scipy** - Nonlinear optimization and curve fitting
- **scikit-learn** - Linear regression
- **pandas/numpy** - Data manipulation
- **matplotlib/seaborn** - Visualization
- **playwright** - Browser automation for scraping odds from Oddschecker and prices from F1 Fantasy

## Current Top Picks (Japanese GP, Round 3)

**Top EV Drivers:**

| Driver | EV | Price | EV/$M |
|--------|---:|------:|------:|
| Russell | 55.7 | $28.0M | 1.99 |
| Antonelli | 50.8 | $23.8M | 2.13 |
| Hamilton | 44.1 | $22.9M | 1.92 |
| Leclerc | 43.9 | $23.4M | 1.88 |
| Bearman | 18.4 | $8.6M | 2.14 |
| Gasly | 18.4 | $12.8M | 1.44 |
| Hadjar | 17.9 | $13.9M | 1.29 |

**Top EV Constructors:**

| Constructor | EV | Price | EV/$M |
|-------------|---:|------:|------:|
| Mercedes | 86.5 | $29.9M | 2.89 |
| Ferrari | 68.0 | $23.9M | 2.85 |
| Haas | 14.6 | $8.6M | 1.70 |
| Racing Bulls | 9.4 | $7.5M | 1.25 |

**Best value picks:** Bearman (2.14 EV/$M), Antonelli (2.13), Mercedes (2.89), Ferrari (2.85). Budget fillers: Hulkenberg ($5.6M), Bottas ($4.7M), Perez ($6.4M).

**Optimal unconstrained team (budget ~$103M):** Antonelli, Bearman, Hulkenberg, Perez, Bottas + Mercedes, Ferrari = **287 EV**. Turbo: Antonelli.

## Performance

The 2024 model achieved **top 2.5% of global F1 Fantasy players** in its first season. Formal backtesting is not possible due to the high variance nature of F1 Fantasy and lack of historical fantasy data.
