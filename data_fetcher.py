"""Data fetching and caching layer for market data via yfinance."""

from __future__ import annotations

import os
import pickle
import time
from datetime import datetime, timezone
from typing import Dict, Optional

import pandas as pd
import yfinance as yf

from config import ASSET_TICKERS, CACHE_DIR, CACHE_TTL_CLOSED_MINUTES, CACHE_TTL_MARKET_MINUTES


def _cache_path(ticker: str) -> str:
    return os.path.join(CACHE_DIR, f"{ticker}_1d.pkl")


def _is_market_hours() -> bool:
    """Check if US stock market is likely open (rough check, no holiday calendar)."""
    now = datetime.now(timezone.utc)
    weekday = now.weekday()
    if weekday >= 5:
        return False
    hour_et = (now.hour - 4) % 24
    return 9 <= hour_et < 16


def _cache_ttl_seconds() -> int:
    if _is_market_hours():
        return CACHE_TTL_MARKET_MINUTES * 60
    return CACHE_TTL_CLOSED_MINUTES * 60


def _is_cache_fresh(ticker: str) -> bool:
    path = _cache_path(ticker)
    if not os.path.exists(path):
        return False
    age = time.time() - os.path.getmtime(path)
    return age < _cache_ttl_seconds()


def _load_from_cache(ticker: str) -> Optional[pd.DataFrame]:
    path = _cache_path(ticker)
    if not os.path.exists(path):
        return None
    with open(path, "rb") as f:
        return pickle.load(f)


def _save_to_cache(ticker: str, df: pd.DataFrame) -> None:
    os.makedirs(CACHE_DIR, exist_ok=True)
    path = _cache_path(ticker)
    with open(path, "wb") as f:
        pickle.dump(df, f)


def get_ohlcv(ticker: str) -> Optional[pd.DataFrame]:
    """Get OHLCV data for a single ticker, using cache when fresh."""
    if _is_cache_fresh(ticker):
        return _load_from_cache(ticker)

    try:
        df = yf.download(ticker, period="1y", interval="1d", progress=False)
        if df is None or df.empty:
            return _load_from_cache(ticker)
        # Flatten multi-level columns if present
        if isinstance(df.columns, pd.MultiIndex):
            df.columns = df.columns.get_level_values(0)
        _save_to_cache(ticker, df)
        return df
    except Exception:
        return _load_from_cache(ticker)


def fetch_all_assets() -> Dict[str, pd.DataFrame]:
    """Fetch data for all configured assets. Returns dict keyed by ticker."""
    # Check if all caches are fresh
    all_fresh = all(_is_cache_fresh(t) for t in ASSET_TICKERS)
    if all_fresh:
        return {t: _load_from_cache(t) for t in ASSET_TICKERS}

    # Batch download for efficiency
    try:
        raw = yf.download(ASSET_TICKERS, period="1y", interval="1d", progress=False, group_by="ticker")
    except Exception:
        raw = None

    result = {}
    for ticker in ASSET_TICKERS:
        if raw is not None and not raw.empty:
            try:
                if len(ASSET_TICKERS) == 1:
                    df = raw.copy()
                else:
                    df = raw[ticker].copy()
                df = df.dropna(how="all")
                if not df.empty:
                    if isinstance(df.columns, pd.MultiIndex):
                        df.columns = df.columns.get_level_values(0)
                    _save_to_cache(ticker, df)
                    result[ticker] = df
                    continue
            except (KeyError, TypeError):
                pass

        # Fallback: individual fetch or stale cache
        cached = _load_from_cache(ticker)
        if cached is not None:
            result[ticker] = cached
        else:
            df = get_ohlcv(ticker)
            if df is not None:
                result[ticker] = df

    return result


def get_last_fetch_time() -> Optional[str]:
    """Return the most recent cache file modification time as a string."""
    times = []
    for ticker in ASSET_TICKERS:
        path = _cache_path(ticker)
        if os.path.exists(path):
            times.append(os.path.getmtime(path))
    if not times:
        return None
    latest = max(times)
    return datetime.fromtimestamp(latest).strftime("%Y-%m-%d %H:%M:%S")
