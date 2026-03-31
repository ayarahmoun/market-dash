"""Historical strategy backtesting and comparison."""

from __future__ import annotations

import pandas as pd

from indicators import compute_all_indicators
from signals import SIGNAL_FUNCTIONS, _safe_float


def backtest_strategy(df: pd.DataFrame, strategy: str, lookback: int = 120) -> dict:
    """Simulate a single strategy over the last `lookback` trading days.

    Returns daily signals, cumulative returns, and performance metrics.
    The simulation goes long when signal > 0.15, flat when signal < -0.15,
    and holds previous position otherwise.
    """
    df_ind = compute_all_indicators(df)
    if len(df_ind) < lookback + 30:
        lookback = max(len(df_ind) - 30, 10)

    signal_func = SIGNAL_FUNCTIONS.get(strategy)
    if signal_func is None:
        return {"error": f"Unknown strategy: {strategy}"}

    start_idx = len(df_ind) - lookback
    dates = []
    signals = []
    daily_returns = []
    positions = []
    position = 0  # 0=flat, 1=long

    for i in range(start_idx, len(df_ind)):
        window = df_ind.iloc[:i + 1]
        sig = signal_func(window)
        signals.append(sig)
        dates.append(df_ind.index[i])

        if sig >= 0.15:
            position = 1
        elif sig <= -0.15:
            position = 0

        positions.append(position)

        if i > start_idx:
            prev_close = _safe_float(df_ind.iloc[i - 1]["Close"])
            curr_close = _safe_float(df_ind.iloc[i]["Close"])
            if prev_close > 0:
                ret = (curr_close - prev_close) / prev_close
            else:
                ret = 0.0
            daily_returns.append(ret * positions[-2])  # Previous position determines today's return
        else:
            daily_returns.append(0.0)

    cumulative = []
    cum = 1.0
    for r in daily_returns:
        cum *= (1 + r)
        cumulative.append(cum)

    total_return = (cumulative[-1] - 1) * 100 if cumulative else 0
    win_days = sum(1 for r in daily_returns if r > 0)
    loss_days = sum(1 for r in daily_returns if r < 0)
    total_trading_days = win_days + loss_days
    win_rate = (win_days / total_trading_days * 100) if total_trading_days > 0 else 0

    avg_daily = sum(daily_returns) / len(daily_returns) if daily_returns else 0
    std_daily = (
        (sum((r - avg_daily) ** 2 for r in daily_returns) / len(daily_returns)) ** 0.5
        if daily_returns
        else 0
    )
    sharpe = (avg_daily / std_daily * (252 ** 0.5)) if std_daily > 0 else 0

    return {
        "dates": [d.strftime("%Y-%m-%d") if hasattr(d, "strftime") else str(d) for d in dates],
        "signals": signals,
        "cumulative": cumulative,
        "total_return": round(total_return, 2),
        "win_rate": round(win_rate, 1),
        "sharpe": round(sharpe, 2),
        "num_trades": sum(
            1 for i in range(1, len(positions)) if positions[i] != positions[i - 1]
        ),
    }


def backtest_all_strategies(df: pd.DataFrame, lookback: int = 120) -> dict:
    """Run backtests for all strategies on a single asset."""
    results = {}
    for strategy_name in SIGNAL_FUNCTIONS:
        results[strategy_name] = backtest_strategy(df, strategy_name, lookback)
    return results


def compare_strategies_all_assets(
    all_data: dict[str, pd.DataFrame], lookback: int = 120
) -> dict:
    """Run backtests across all assets and strategies. Returns nested dict."""
    comparison = {}
    for ticker, df in all_data.items():
        if df is None or df.empty or len(df) < 50:
            continue
        comparison[ticker] = backtest_all_strategies(df, lookback)
    return comparison
