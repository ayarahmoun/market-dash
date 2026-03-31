"""Market Signals Dashboard - FastAPI application."""

from __future__ import annotations

import json
import os

import pandas as pd
import plotly.graph_objects as go
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from plotly.subplots import make_subplots

from backtester import backtest_all_strategies
from config import ASSET_MAP, ASSET_TICKERS, STRATEGY_NAMES
from data_fetcher import fetch_all_assets, get_last_fetch_time, get_ohlcv
from indicators import compute_all_indicators
from signals import (
    SIGNAL_FUNCTIONS,
    _safe_float,
    compute_composite,
    generate_all_signals,
    get_signal_for_strategy,
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    os.makedirs("cache", exist_ok=True)
    fetch_all_assets()
    yield


app = FastAPI(title="Market Signals Dashboard", lifespan=lifespan)
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")


@app.get("/")
async def dashboard(request: Request):
    all_data = fetch_all_assets()
    signals = generate_all_signals(all_data)
    last_updated = get_last_fetch_time()
    return templates.TemplateResponse("dashboard.html", {
        "request": request,
        "signals": signals,
        "last_updated": last_updated,
        "active_tab": "overview",
        "strategies": STRATEGY_NAMES,
    })


@app.get("/strategy/{strategy_name}")
async def strategy_view(request: Request, strategy_name: str):
    if strategy_name not in SIGNAL_FUNCTIONS:
        return RedirectResponse("/")

    all_data = fetch_all_assets()
    last_updated = get_last_fetch_time()

    strategy_signals = []
    for ticker in ASSET_TICKERS:
        df = all_data.get(ticker)
        if df is None or df.empty or len(df) < 30:
            continue
        df_ind = compute_all_indicators(df)
        sig_score = get_signal_for_strategy(df_ind, strategy_name)
        row = df_ind.iloc[-1]
        prev_close = _safe_float(df_ind.iloc[-2]["Close"]) if len(df_ind) > 1 else 0
        current_close = _safe_float(row["Close"])
        change_pct = ((current_close - prev_close) / prev_close * 100) if prev_close > 0 else 0

        if sig_score >= 0.4:
            label = "STRONG BUY"
        elif sig_score >= 0.15:
            label = "BUY"
        elif sig_score > -0.15:
            label = "HOLD"
        elif sig_score > -0.4:
            label = "SELL"
        else:
            label = "STRONG SELL"

        asset_info = ASSET_MAP.get(ticker, {})

        # Get relevant indicator value for this strategy
        indicator_val = _get_strategy_indicator(df_ind, strategy_name)

        strategy_signals.append({
            "ticker": ticker,
            "label": asset_info.get("label", ticker),
            "category": asset_info.get("category", ""),
            "price": round(current_close, 2),
            "change_pct": round(change_pct, 2),
            "score": round(sig_score, 3),
            "signal_label": label,
            "indicator_val": indicator_val,
        })

    return templates.TemplateResponse("strategy.html", {
        "request": request,
        "strategy_name": strategy_name,
        "display_name": STRATEGY_NAMES.get(strategy_name, strategy_name),
        "signals": strategy_signals,
        "last_updated": last_updated,
        "active_tab": strategy_name,
        "strategies": STRATEGY_NAMES,
    })


@app.get("/compare")
async def compare_view(request: Request):
    all_data = fetch_all_assets()
    last_updated = get_last_fetch_time()

    # Build comparison data for each asset
    comparison_charts = {}
    summary_data = {}

    for ticker in ASSET_TICKERS:
        df = all_data.get(ticker)
        if df is None or df.empty or len(df) < 50:
            continue
        bt = backtest_all_strategies(df)
        summary_data[ticker] = {}
        for strat, result in bt.items():
            if "error" in result:
                continue
            summary_data[ticker][strat] = {
                "total_return": result["total_return"],
                "win_rate": result["win_rate"],
                "sharpe": result["sharpe"],
                "num_trades": result["num_trades"],
            }

        # Build plotly chart for this asset
        fig = go.Figure()
        for strat, result in bt.items():
            if "error" in result:
                continue
            fig.add_trace(go.Scatter(
                x=result["dates"],
                y=[round(c * 100 - 100, 2) for c in result["cumulative"]],
                name=STRATEGY_NAMES.get(strat, strat),
                mode="lines",
            ))
        fig.update_layout(
            template="plotly_dark",
            height=300,
            margin={"l": 40, "r": 20, "t": 30, "b": 30},
            yaxis_title="Return (%)",
            showlegend=True,
            legend={"orientation": "h", "y": -0.2},
            paper_bgcolor="#16213e",
            plot_bgcolor="#1a1a2e",
        )
        comparison_charts[ticker] = json.loads(fig.to_json())

    return templates.TemplateResponse("compare.html", {
        "request": request,
        "comparison_charts": comparison_charts,
        "summary_data": summary_data,
        "asset_map": ASSET_MAP,
        "last_updated": last_updated,
        "active_tab": "compare",
        "strategies": STRATEGY_NAMES,
    })


@app.get("/asset/{ticker}")
async def asset_detail(request: Request, ticker: str):
    if ticker not in ASSET_MAP:
        return RedirectResponse("/")

    df = get_ohlcv(ticker)
    if df is None or df.empty:
        return RedirectResponse("/")

    df_ind = compute_all_indicators(df)
    sig = compute_composite(df_ind)
    chart_json = _build_detail_charts(df_ind, ticker)
    last_updated = get_last_fetch_time()

    row = df_ind.iloc[-1]
    prev_close = _safe_float(df_ind.iloc[-2]["Close"]) if len(df_ind) > 1 else 0
    current_close = _safe_float(row["Close"])
    change_pct = ((current_close - prev_close) / prev_close * 100) if prev_close > 0 else 0

    asset_info = ASSET_MAP.get(ticker, {})

    return templates.TemplateResponse("detail.html", {
        "request": request,
        "ticker": ticker,
        "asset_label": asset_info.get("label", ticker),
        "category": asset_info.get("category", ""),
        "price": round(current_close, 2),
        "change_pct": round(change_pct, 2),
        "signal": sig,
        "chart_json": chart_json,
        "last_updated": last_updated,
        "active_tab": "",
        "strategies": STRATEGY_NAMES,
        "strategy_names": STRATEGY_NAMES,
    })


@app.get("/api/signals")
async def api_signals():
    all_data = fetch_all_assets()
    signals = generate_all_signals(all_data)
    return JSONResponse({"signals": signals, "last_updated": get_last_fetch_time()})


@app.post("/api/refresh")
async def api_refresh():
    # Clear cache and re-fetch
    import glob

    for f in glob.glob("cache/*.pkl"):
        os.remove(f)
    fetch_all_assets()
    return JSONResponse({"status": "ok", "last_updated": get_last_fetch_time()})


def _get_strategy_indicator(df_ind, strategy_name: str) -> str:
    """Get the key indicator value string for display in strategy view."""
    row = df_ind.iloc[-1]
    if strategy_name == "ma_crossover":
        ema9 = _safe_float(row.get("EMA_9", 0))
        ema21 = _safe_float(row.get("EMA_21", 0))
        trend = "Bullish" if ema9 > ema21 else "Bearish"
        return f"EMA9/21: {trend}"
    if strategy_name == "rsi":
        return f"RSI: {_safe_float(row.get('RSI', 0)):.1f}"
    if strategy_name == "macd":
        return f"Hist: {_safe_float(row.get('MACD_Hist', 0)):.4f}"
    if strategy_name == "bollinger":
        return f"%B: {_safe_float(row.get('BB_PctB', 0.5)):.2f}"
    if strategy_name == "volume":
        return f"Vol Ratio: {_safe_float(row.get('Vol_Ratio', 1)):.2f}x"
    if strategy_name == "adx":
        adx = _safe_float(row.get("ADX", 0))
        strength = "Trending" if adx > 25 else "Range-bound"
        return f"ADX: {adx:.1f} ({strength})"
    return ""


def _build_detail_charts(df: pd.DataFrame, ticker: str) -> dict:
    """Build Plotly figure with 5 subplots for asset detail page."""
    # Use last 6 months of data for cleaner charts
    df_plot = df.tail(130).copy()

    fig = make_subplots(
        rows=5,
        cols=1,
        shared_xaxes=True,
        row_heights=[0.40, 0.15, 0.15, 0.15, 0.15],
        vertical_spacing=0.03,
        subplot_titles=["Price", "Volume", "RSI (14)", "MACD (12/26/9)", "ADX (14)"],
    )

    dates = df_plot.index

    # 1. Candlestick + overlays
    fig.add_trace(
        go.Candlestick(
            x=dates,
            open=df_plot["Open"],
            high=df_plot["High"],
            low=df_plot["Low"],
            close=df_plot["Close"],
            name="Price",
            showlegend=False,
        ),
        row=1,
        col=1,
    )

    for col_name, color, dash in [
        ("EMA_9", "#00bcd4", None),
        ("EMA_21", "#ff9800", None),
        ("SMA_50", "#9c27b0", "dash"),
        ("SMA_200", "#f44336", "dash"),
        ("BB_Upper", "#616161", "dot"),
        ("BB_Lower", "#616161", "dot"),
    ]:
        if col_name in df_plot.columns:
            series = df_plot[col_name].dropna()
            if not series.empty:
                fig.add_trace(
                    go.Scatter(
                        x=series.index,
                        y=series,
                        name=col_name.replace("_", " "),
                        line={"color": color, "width": 1, "dash": dash},
                    ),
                    row=1,
                    col=1,
                )

    # 2. Volume bars
    colors = [
        "#00c853" if c >= o else "#ff1744"
        for c, o in zip(df_plot["Close"], df_plot["Open"])
    ]
    fig.add_trace(
        go.Bar(x=dates, y=df_plot["Volume"], marker_color=colors, name="Volume", showlegend=False),
        row=2,
        col=1,
    )
    if "Vol_SMA" in df_plot.columns:
        fig.add_trace(
            go.Scatter(
                x=dates,
                y=df_plot["Vol_SMA"],
                name="Vol Avg",
                line={"color": "#ffd600", "width": 1},
            ),
            row=2,
            col=1,
        )

    # 3. RSI
    if "RSI" in df_plot.columns:
        fig.add_trace(
            go.Scatter(
                x=dates, y=df_plot["RSI"], name="RSI", line={"color": "#7c4dff", "width": 1.5}
            ),
            row=3,
            col=1,
        )
        fig.add_hline(y=70, line_dash="dash", line_color="#ff1744", row=3, col=1)
        fig.add_hline(y=30, line_dash="dash", line_color="#00c853", row=3, col=1)
        fig.add_hrect(y0=30, y1=70, fillcolor="gray", opacity=0.1, row=3, col=1)

    # 4. MACD
    if "MACD_Line" in df_plot.columns:
        fig.add_trace(
            go.Scatter(
                x=dates,
                y=df_plot["MACD_Line"],
                name="MACD",
                line={"color": "#00bcd4", "width": 1.5},
            ),
            row=4,
            col=1,
        )
        fig.add_trace(
            go.Scatter(
                x=dates,
                y=df_plot["MACD_Signal"],
                name="Signal",
                line={"color": "#ff9800", "width": 1},
            ),
            row=4,
            col=1,
        )
        hist_colors = ["#00c853" if v >= 0 else "#ff1744" for v in df_plot["MACD_Hist"]]
        fig.add_trace(
            go.Bar(
                x=dates,
                y=df_plot["MACD_Hist"],
                name="Histogram",
                marker_color=hist_colors,
                showlegend=False,
            ),
            row=4,
            col=1,
        )

    # 5. ADX
    if "ADX" in df_plot.columns:
        fig.add_trace(
            go.Scatter(
                x=dates, y=df_plot["ADX"], name="ADX", line={"color": "#ffd600", "width": 1.5}
            ),
            row=5,
            col=1,
        )
        fig.add_trace(
            go.Scatter(
                x=dates,
                y=df_plot["Plus_DI"],
                name="+DI",
                line={"color": "#00c853", "width": 1},
            ),
            row=5,
            col=1,
        )
        fig.add_trace(
            go.Scatter(
                x=dates,
                y=df_plot["Minus_DI"],
                name="-DI",
                line={"color": "#ff1744", "width": 1},
            ),
            row=5,
            col=1,
        )
        fig.add_hline(y=25, line_dash="dash", line_color="#616161", row=5, col=1)

    fig.update_layout(
        template="plotly_dark",
        height=1100,
        showlegend=True,
        legend={"orientation": "h", "y": -0.05, "font": {"size": 10}},
        xaxis_rangeslider_visible=False,
        paper_bgcolor="#16213e",
        plot_bgcolor="#1a1a2e",
        margin={"l": 50, "r": 20, "t": 40, "b": 40},
        font={"family": "monospace"},
    )

    return json.loads(fig.to_json())


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("app:app", host="127.0.0.1", port=8050, reload=True)
