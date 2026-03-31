"""Signal generation: per-strategy scoring and composite signal computation."""

from __future__ import annotations

import pandas as pd

from config import STRATEGY_NAMES, STRATEGY_WEIGHTS


def _safe_float(val) -> float:
    """Extract a scalar float from a value that might be a Series or array."""
    if isinstance(val, pd.Series):
        return float(val.iloc[-1]) if len(val) > 0 else 0.0
    try:
        return float(val)
    except (TypeError, ValueError):
        return 0.0


def ma_signal(df: pd.DataFrame) -> float:
    """Moving average crossover signal."""
    if len(df) < 3:
        return 0.0
    row = df.iloc[-1]
    close = _safe_float(row["Close"])
    ema9 = _safe_float(row["EMA_9"])
    ema21 = _safe_float(row["EMA_21"])
    sma50 = _safe_float(row.get("SMA_50", 0))
    sma200 = _safe_float(row.get("SMA_200", 0))

    has_sma50 = sma50 > 0 and not pd.isna(sma50)
    has_sma200 = sma200 > 0 and not pd.isna(sma200)

    score = 0.0
    if ema9 > ema21:
        if has_sma50 and close > sma50:
            score = 0.5
            if has_sma200 and sma50 > sma200:
                score = 1.0
        else:
            score = 0.25
    elif ema9 < ema21:
        if has_sma50 and close < sma50:
            score = -0.5
            if has_sma200 and sma50 < sma200:
                score = -1.0
        else:
            score = -0.25

    # Detect fresh crossover (within last 3 bars)
    for i in range(-3, -1):
        if abs(i) > len(df):
            continue
        prev_ema9 = _safe_float(df.iloc[i]["EMA_9"])
        prev_ema21 = _safe_float(df.iloc[i]["EMA_21"])
        if prev_ema9 < prev_ema21 and ema9 > ema21:
            score = min(score + 0.25, 1.0)
            break
        if prev_ema9 > prev_ema21 and ema9 < ema21:
            score = max(score - 0.25, -1.0)
            break

    return score


def rsi_signal(df: pd.DataFrame) -> float:
    """RSI mean-reversion signal."""
    rsi = _safe_float(df.iloc[-1].get("RSI", 50))
    if pd.isna(rsi):
        return 0.0

    if rsi < 25:
        return 0.75
    if rsi < 30:
        return 0.5
    if rsi < 40:
        return 0.25
    if rsi <= 60:
        return 0.0
    if rsi <= 70:
        return -0.25
    if rsi <= 75:
        return -0.5
    return -0.75


def macd_signal(df: pd.DataFrame) -> float:
    """MACD momentum signal."""
    if len(df) < 3:
        return 0.0
    row = df.iloc[-1]
    macd_line = _safe_float(row.get("MACD_Line", 0))
    signal_line = _safe_float(row.get("MACD_Signal", 0))
    hist = _safe_float(row.get("MACD_Hist", 0))
    prev_hist = _safe_float(df.iloc[-2].get("MACD_Hist", 0))

    # Check for fresh crossover
    for i in range(-3, -1):
        if abs(i) > len(df):
            continue
        prev_ml = _safe_float(df.iloc[i].get("MACD_Line", 0))
        prev_sl = _safe_float(df.iloc[i].get("MACD_Signal", 0))
        if prev_ml < prev_sl and macd_line > signal_line:
            return 0.75
        if prev_ml > prev_sl and macd_line < signal_line:
            return -0.75

    if macd_line > signal_line and hist > 0:
        if hist > prev_hist:
            return 1.0
        return 0.5
    if macd_line < signal_line and hist < 0:
        if hist < prev_hist:
            return -1.0
        return -0.5

    return 0.0


def bb_signal(df: pd.DataFrame) -> float:
    """Bollinger Bands mean-reversion signal."""
    pct_b = _safe_float(df.iloc[-1].get("BB_PctB", 0.5))
    if pd.isna(pct_b):
        return 0.0

    if pct_b < 0.0:
        return 0.75
    if pct_b < 0.2:
        return 0.5
    if pct_b < 0.4:
        return 0.25
    if pct_b <= 0.6:
        return 0.0
    if pct_b <= 0.8:
        return -0.25
    if pct_b <= 1.0:
        return -0.5
    return -0.75


def volume_signal(df: pd.DataFrame) -> float:
    """Volume confirmation signal."""
    row = df.iloc[-1]
    vol_ratio = _safe_float(row.get("Vol_Ratio", 1.0))
    close = _safe_float(row["Close"])
    open_price = _safe_float(row["Open"])
    price_up = close > open_price

    if vol_ratio > 2.0:
        return 0.5 if price_up else -0.5
    if vol_ratio > 1.0:
        return 0.25 if price_up else -0.25
    return 0.0


def adx_signal(df: pd.DataFrame) -> float:
    """ADX trend strength + direction signal."""
    row = df.iloc[-1]
    adx = _safe_float(row.get("ADX", 0))
    plus_di = _safe_float(row.get("Plus_DI", 0))
    minus_di = _safe_float(row.get("Minus_DI", 0))

    if pd.isna(adx) or adx < 20:
        return 0.0

    bullish = plus_di > minus_di
    if adx > 30:
        return 0.75 if bullish else -0.75
    # ADX 20-30
    return 0.4 if bullish else -0.4


SIGNAL_FUNCTIONS = {
    "ma_crossover": ma_signal,
    "rsi": rsi_signal,
    "macd": macd_signal,
    "bollinger": bb_signal,
    "volume": volume_signal,
    "adx": adx_signal,
}


def compute_composite(df: pd.DataFrame) -> dict:
    """Compute all sub-signals and the weighted composite score."""
    sub_signals = {}
    for name, func in SIGNAL_FUNCTIONS.items():
        sub_signals[name] = func(df)

    composite = sum(sub_signals[k] * STRATEGY_WEIGHTS[k] for k in sub_signals)

    if composite >= 0.4:
        label = "STRONG BUY"
    elif composite >= 0.15:
        label = "BUY"
    elif composite > -0.15:
        label = "HOLD"
    elif composite > -0.4:
        label = "SELL"
    else:
        label = "STRONG SELL"

    return {
        "sub_signals": sub_signals,
        "composite_score": round(composite, 3),
        "signal_label": label,
    }


def generate_all_signals(all_data: dict) -> list[dict]:
    """Generate signal summaries for all assets."""
    from config import ASSET_MAP

    results = []
    for ticker, df in all_data.items():
        if df is None or df.empty or len(df) < 30:
            continue
        from indicators import compute_all_indicators

        df_ind = compute_all_indicators(df)
        sig = compute_composite(df_ind)
        row = df_ind.iloc[-1]
        prev_close = _safe_float(df_ind.iloc[-2]["Close"]) if len(df_ind) > 1 else 0

        current_close = _safe_float(row["Close"])
        change_pct = ((current_close - prev_close) / prev_close * 100) if prev_close > 0 else 0

        asset_info = ASSET_MAP.get(ticker, {})
        results.append({
            "ticker": ticker,
            "label": asset_info.get("label", ticker),
            "category": asset_info.get("category", ""),
            "price": round(current_close, 2),
            "change_pct": round(change_pct, 2),
            "rsi": round(_safe_float(row.get("RSI", 0)), 1),
            "macd_hist": round(_safe_float(row.get("MACD_Hist", 0)), 4),
            "adx": round(_safe_float(row.get("ADX", 0)), 1),
            "vol_ratio": round(_safe_float(row.get("Vol_Ratio", 1)), 2),
            "bb_pctb": round(_safe_float(row.get("BB_PctB", 0.5)), 2),
            **sig,
        })

    return results


def get_signal_for_strategy(df: pd.DataFrame, strategy: str) -> float:
    """Get signal score for a single strategy."""
    func = SIGNAL_FUNCTIONS.get(strategy)
    if func is None:
        return 0.0
    return func(df)


def get_strategy_display_name(strategy: str) -> str:
    """Get human-readable strategy name."""
    return STRATEGY_NAMES.get(strategy, strategy)
