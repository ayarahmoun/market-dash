# Market Signals Dashboard

Daily market signals dashboard for swing trading. Tracks 12 assets across commodities, indices, sectors, and crypto. Combines six technical analysis strategies into a weighted composite signal, with interactive charts and historical backtesting.

## What it does

The dashboard fetches live market data and runs six independent technical analysis strategies on each asset. Each strategy scores between -1.0 (strong sell) and +1.0 (strong buy). The scores are combined into a single **composite signal** using configurable weights:

| Strategy | Weight | What it measures |
|----------|--------|------------------|
| MA Crossover | 20% | EMA 9/21 and SMA 50/200 crosses -- trend direction |
| MACD | 20% | MACD line vs signal line -- momentum shifts |
| ADX | 20% | Average Directional Index -- trend strength |
| RSI | 15% | Relative Strength Index -- overbought/oversold |
| Bollinger Bands | 15% | Price vs 2-sigma bands -- mean reversion |
| Volume | 10% | Volume spikes vs 20-day average -- conviction |

### Signal thresholds

| Composite score | Label |
|-----------------|-------|
| >= 0.40 | STRONG BUY |
| >= 0.15 | BUY |
| > -0.15 | HOLD |
| > -0.40 | SELL |
| <= -0.40 | STRONG SELL |

### Assets tracked

Commodities (Natural Gas, Crude Oil, Gold, Silver), Indices (S&P 500, Nasdaq 100), Sectors (Semiconductors), Crypto (Bitcoin ETF), Bonds (20+ Year Treasury), Stocks (Tesla), Thematic (Uranium), Energy (Cheniere Energy).

## How to run locally

### Prerequisites

- Python 3.9+
- [uv](https://docs.astral.sh/uv/) (Python package manager)

### Setup

```bash
git clone https://github.com/ayarahmoun/market-dash.git
cd market-dash

# Install dependencies
uv sync

# Run the dashboard
uv run python app.py
```

Open http://127.0.0.1:8050 in your browser.

No API keys are needed -- market data is fetched from Yahoo Finance (free, no registration).

### Data caching

Market data is cached as pickle files in `cache/` (gitignored). Cache TTL is 15 minutes during US market hours (9:30-16:00 ET) and 6 hours outside market hours, so you won't hit Yahoo Finance rate limits.

## Pages

- **Dashboard** (`/`) -- Overview table with all assets, their signals, and composite scores
- **Strategy** (`/strategy/{name}`) -- Single strategy view across all assets
- **Compare** (`/compare`) -- Multi-strategy comparison with 120-day backtest results (total return, win rate, Sharpe ratio)
- **Detail** (`/asset/{ticker}`) -- Individual asset deep-dive with candlestick chart and indicator overlays

## Project structure

```
market-dash/
  app.py              -- FastAPI application, routes, Plotly charts, entry point
  config.py           -- Asset list, strategy weights, indicator parameters
  data_fetcher.py     -- Yahoo Finance data download with pickle caching
  indicators.py       -- Technical indicator calculations (RSI, MACD, MA, BB, Volume, ADX)
  signals.py          -- Per-strategy scoring (-1 to +1) and weighted composite
  backtester.py       -- Historical strategy simulation over 120-day windows
  templates/          -- Jinja2 HTML templates (dark theme)
    base.html         -- Base layout with navigation
    dashboard.html    -- Overview page
    strategy.html     -- Single strategy view
    compare.html      -- Strategy comparison with backtest
    detail.html       -- Asset detail with charts
  static/
    style.css         -- Dark theme CSS
    app.js            -- Table sorting and auto-refresh
  cache/              -- Pickle cache files (auto-created, gitignored)
```

## Technical stack

- **Backend**: FastAPI + Uvicorn
- **Frontend**: Jinja2 templates with Plotly charts
- **Data**: yfinance (Yahoo Finance)
- **Indicators**: pandas + numpy (no ta-lib dependency)

## Limitations

- **Daily data only.** All indicators use daily OHLCV candles from Yahoo Finance. No intraday granularity.
- **No live execution.** Signals are informational -- there is no broker integration or order execution.
- **Backtest is simplified.** Uses daily close-to-close returns with no transaction costs, slippage, or position sizing.
- **US-centric market hours.** Cache TTL logic uses NYSE hours. Commodity and crypto assets trade on different schedules.
