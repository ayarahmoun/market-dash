"""Technical indicator calculations using pandas/numpy."""

import numpy as np
import pandas as pd

from config import (
    ADX_PERIOD,
    BB_PERIOD,
    BB_STD,
    MA_LONG_FAST,
    MA_LONG_SLOW,
    MA_SHORT_FAST,
    MA_SHORT_SLOW,
    MACD_FAST,
    MACD_SIGNAL,
    MACD_SLOW,
    RSI_PERIOD,
    VOLUME_AVG_PERIOD,
)


def add_moving_averages(df: pd.DataFrame) -> pd.DataFrame:
    """Add EMA 9/21 and SMA 50/200."""
    close = df["Close"]
    df["EMA_9"] = close.ewm(span=MA_SHORT_FAST, adjust=False).mean()
    df["EMA_21"] = close.ewm(span=MA_SHORT_SLOW, adjust=False).mean()
    df["SMA_50"] = close.rolling(window=MA_LONG_FAST, min_periods=MA_LONG_FAST).mean()
    df["SMA_200"] = close.rolling(window=MA_LONG_SLOW, min_periods=MA_LONG_SLOW).mean()
    return df


def add_rsi(df: pd.DataFrame) -> pd.DataFrame:
    """Add RSI using Wilder's smoothing method."""
    delta = df["Close"].diff()
    gain = delta.where(delta > 0, 0.0)
    loss = -delta.where(delta < 0, 0.0)
    avg_gain = gain.ewm(alpha=1 / RSI_PERIOD, min_periods=RSI_PERIOD, adjust=False).mean()
    avg_loss = loss.ewm(alpha=1 / RSI_PERIOD, min_periods=RSI_PERIOD, adjust=False).mean()
    rs = avg_gain / avg_loss
    df["RSI"] = 100 - (100 / (1 + rs))
    return df


def add_macd(df: pd.DataFrame) -> pd.DataFrame:
    """Add MACD line, signal line, and histogram."""
    close = df["Close"]
    ema_fast = close.ewm(span=MACD_FAST, adjust=False).mean()
    ema_slow = close.ewm(span=MACD_SLOW, adjust=False).mean()
    df["MACD_Line"] = ema_fast - ema_slow
    df["MACD_Signal"] = df["MACD_Line"].ewm(span=MACD_SIGNAL, adjust=False).mean()
    df["MACD_Hist"] = df["MACD_Line"] - df["MACD_Signal"]
    return df


def add_bollinger_bands(df: pd.DataFrame) -> pd.DataFrame:
    """Add Bollinger Bands and %B position."""
    close = df["Close"]
    df["BB_Middle"] = close.rolling(window=BB_PERIOD, min_periods=BB_PERIOD).mean()
    bb_std = close.rolling(window=BB_PERIOD, min_periods=BB_PERIOD).std()
    df["BB_Upper"] = df["BB_Middle"] + BB_STD * bb_std
    df["BB_Lower"] = df["BB_Middle"] - BB_STD * bb_std
    band_width = df["BB_Upper"] - df["BB_Lower"]
    df["BB_PctB"] = np.where(band_width > 0, (close - df["BB_Lower"]) / band_width, 0.5)
    return df


def add_volume_analysis(df: pd.DataFrame) -> pd.DataFrame:
    """Add volume moving average and ratio."""
    df["Vol_SMA"] = df["Volume"].rolling(window=VOLUME_AVG_PERIOD, min_periods=1).mean()
    df["Vol_Ratio"] = np.where(df["Vol_SMA"] > 0, df["Volume"] / df["Vol_SMA"], 1.0)
    return df


def add_adx(df: pd.DataFrame) -> pd.DataFrame:
    """Add ADX, +DI, and -DI using Wilder's smoothing."""
    high = df["High"]
    low = df["Low"]
    close = df["Close"]
    period = ADX_PERIOD

    plus_dm = high.diff()
    minus_dm = -low.diff()

    plus_dm = np.where((plus_dm > minus_dm) & (plus_dm > 0), plus_dm, 0.0)
    minus_dm_vals = np.where((minus_dm > plus_dm) & (minus_dm > 0), minus_dm, 0.0)

    plus_dm = pd.Series(plus_dm, index=df.index)
    minus_dm = pd.Series(minus_dm_vals, index=df.index)

    tr1 = high - low
    tr2 = (high - close.shift(1)).abs()
    tr3 = (low - close.shift(1)).abs()
    tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)

    # Wilder's smoothing
    atr = tr.ewm(alpha=1 / period, min_periods=period, adjust=False).mean()
    smooth_plus_dm = plus_dm.ewm(alpha=1 / period, min_periods=period, adjust=False).mean()
    smooth_minus_dm = minus_dm.ewm(alpha=1 / period, min_periods=period, adjust=False).mean()

    df["Plus_DI"] = np.where(atr > 0, 100 * smooth_plus_dm / atr, 0.0)
    df["Minus_DI"] = np.where(atr > 0, 100 * smooth_minus_dm / atr, 0.0)

    di_sum = df["Plus_DI"] + df["Minus_DI"]
    di_diff = (df["Plus_DI"] - df["Minus_DI"]).abs()
    dx = np.where(di_sum > 0, 100 * di_diff / di_sum, 0.0)
    dx = pd.Series(dx, index=df.index)

    df["ADX"] = dx.ewm(alpha=1 / period, min_periods=period, adjust=False).mean()
    return df


def compute_all_indicators(df: pd.DataFrame) -> pd.DataFrame:
    """Compute all technical indicators on a copy of the dataframe."""
    df = df.copy()
    df = add_moving_averages(df)
    df = add_rsi(df)
    df = add_macd(df)
    df = add_bollinger_bands(df)
    df = add_volume_analysis(df)
    df = add_adx(df)
    return df
