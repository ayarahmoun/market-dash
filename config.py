"""Configuration for the Market Signals Dashboard."""

ASSETS = [
    {"ticker": "UNG", "label": "Natural Gas", "category": "Commodity"},
    {"ticker": "LNG", "label": "Cheniere Energy", "category": "Energy"},
    {"ticker": "USO", "label": "Crude Oil", "category": "Commodity"},
    {"ticker": "GLD", "label": "Gold", "category": "Commodity"},
    {"ticker": "SPY", "label": "S&P 500", "category": "Index"},
    {"ticker": "QQQ", "label": "Nasdaq 100", "category": "Index"},
    {"ticker": "SOXX", "label": "Semiconductors", "category": "Sector"},
    {"ticker": "IBIT", "label": "Bitcoin ETF", "category": "Crypto"},
    {"ticker": "TLT", "label": "20+ Year Treasury", "category": "Bond"},
    {"ticker": "SLV", "label": "Silver", "category": "Commodity"},
    {"ticker": "TSLA", "label": "Tesla", "category": "Stock"},
    {"ticker": "URA", "label": "Uranium", "category": "Thematic"},
]

ASSET_TICKERS = [a["ticker"] for a in ASSETS]
ASSET_MAP = {a["ticker"]: a for a in ASSETS}

# Strategy weights for composite signal (must sum to 1.0)
STRATEGY_WEIGHTS = {
    "ma_crossover": 0.20,
    "rsi": 0.15,
    "macd": 0.20,
    "bollinger": 0.15,
    "volume": 0.10,
    "adx": 0.20,
}

STRATEGY_NAMES = {
    "ma_crossover": "MA Crossover",
    "rsi": "RSI",
    "macd": "MACD",
    "bollinger": "Bollinger Bands",
    "volume": "Volume",
    "adx": "ADX",
}

# Moving average periods
MA_SHORT_FAST = 9
MA_SHORT_SLOW = 21
MA_LONG_FAST = 50
MA_LONG_SLOW = 200

# RSI
RSI_PERIOD = 14
RSI_OVERBOUGHT = 70
RSI_OVERSOLD = 30

# MACD
MACD_FAST = 12
MACD_SLOW = 26
MACD_SIGNAL = 9

# Bollinger Bands
BB_PERIOD = 20
BB_STD = 2

# Volume
VOLUME_AVG_PERIOD = 20

# ADX
ADX_PERIOD = 14

# Cache
CACHE_DIR = "cache"
CACHE_TTL_MARKET_MINUTES = 15
CACHE_TTL_CLOSED_MINUTES = 360
DATA_LOOKBACK_DAYS = 365
