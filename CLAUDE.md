# Market Signals Dashboard

Daily market signals dashboard with technical analysis for swing trading.

See [.claude/skills.md](.claude/skills.md) for coding standards and conventions.

## How to run

```bash
cd /Users/aya/market-dash
uv sync
uv run python app.py
# Open http://127.0.0.1:8050
```

## Project structure

- `app.py` - FastAPI application, routes, Plotly chart generation, entry point
- `config.py` - Asset list, strategy weights, indicator parameters
- `data_fetcher.py` - yfinance data download with pickle file caching
- `indicators.py` - Technical indicator calculations (RSI, MACD, MA, BB, Volume, ADX)
- `signals.py` - Per-strategy scoring (-1 to +1) and weighted composite signal
- `backtester.py` - Historical strategy simulation for comparison tab
- `templates/` - Jinja2 HTML templates (dark theme)
- `static/` - CSS and JS (table sorting, auto-refresh)
- `cache/` - Pickle cache files (auto-created, gitignored)

## Key conventions

- All indicator math uses pandas/numpy directly (no ta-lib)
- Data cached as pickle with TTL (15 min market hours, 6 hours after close)
- Signal scores range from -1.0 (strong sell) to +1.0 (strong buy)
- Composite thresholds: STRONG BUY >= 0.4, BUY >= 0.15, HOLD > -0.15, SELL > -0.4, STRONG SELL <= -0.4

## Adding a new asset

Add entry to `ASSETS` list in `config.py`:
```python
{"ticker": "TICKER", "label": "Display Name", "category": "Category"}
```

## Adding a new strategy

1. Add indicator calculation in `indicators.py`
2. Add signal function in `signals.py` and register in `SIGNAL_FUNCTIONS`
3. Add weight in `config.py` `STRATEGY_WEIGHTS` (must sum to 1.0)
4. Add display name in `config.py` `STRATEGY_NAMES`
