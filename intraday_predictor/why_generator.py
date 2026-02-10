"""
Generates technical explanations for trade outcomes by inspecting
volume, trend, and volatility conditions from intraday data.
"""

import logging

import pandas as pd

from data_fetcher import fetch_daily_ohlcv, fetch_intraday_ohlcv

logger = logging.getLogger(__name__)


def _volume_context(ticker: str, actual_volume: int) -> str:
    """Compare today's volume to the 20-day average."""
    df = fetch_daily_ohlcv(ticker, days=25)
    if df.empty or len(df) < 20:
        return "average volume"

    avg_vol = df["Volume"].tail(20).mean()
    if avg_vol == 0:
        return "average volume"

    ratio = actual_volume / avg_vol
    if ratio >= 2.0:
        return "very high volume (2x+ average)"
    if ratio >= 1.3:
        return "above-average volume"
    if ratio <= 0.5:
        return "very low volume (below 50% of average)"
    if ratio <= 0.8:
        return "below-average volume"
    return "average volume"


def _trend_context(ticker: str) -> str:
    """Determine short-term trend from the 9-EMA vs 21-EMA relationship."""
    df = fetch_daily_ohlcv(ticker, days=30)
    if df.empty or len(df) < 21:
        return "indeterminate trend"

    ema9 = df["Close"].ewm(span=9, adjust=False).mean()
    ema21 = df["Close"].ewm(span=21, adjust=False).mean()

    latest_gap = ema9.iloc[-1] - ema21.iloc[-1]
    prev_gap = ema9.iloc[-2] - ema21.iloc[-2]

    if latest_gap > 0 and prev_gap > 0 and latest_gap > prev_gap:
        return "strong uptrend (EMA9 widening above EMA21)"
    if latest_gap > 0:
        return "mild uptrend (EMA9 above EMA21)"
    if latest_gap < 0 and prev_gap < 0 and latest_gap < prev_gap:
        return "strong downtrend (EMA9 widening below EMA21)"
    if latest_gap < 0:
        return "mild downtrend (EMA9 below EMA21)"
    return "flat/ranging market"


def _intraday_pattern(ticker: str, target_date) -> str:
    """Check intraday candle pattern for reversal/gap clues."""
    df = fetch_intraday_ohlcv(ticker, target_date)
    if df.empty or len(df) < 4:
        return ""

    open_price = df["Open"].iloc[0]
    first_hour_high = df["High"].iloc[:4].max()
    close_price = df["Close"].iloc[-1]

    if first_hour_high == df["High"].max() and close_price < open_price:
        return " Opening spike followed by sustained selling."
    if close_price > first_hour_high:
        return " Late-session breakout confirmed strength."
    return ""


def generate_reason(
    outcome: str,
    ticker: str,
    predicted_entry: float,
    predicted_target: float,
    predicted_sl: float,
    actuals: dict,
    target_date,
) -> str:
    vol_ctx = _volume_context(ticker, actuals.get("volume", 0))
    trend_ctx = _trend_context(ticker)
    intraday_note = _intraday_pattern(ticker, target_date)

    if outcome == "NO ENTRY":
        gap = round(predicted_entry - actuals["high"], 2)
        base = (
            f"Buying pressure was insufficient. The stock never crossed the "
            f"trigger price (₹{predicted_entry}), missing by ₹{gap}. "
            f"Trend: {trend_ctx}; Volume: {vol_ctx}."
        )
        if "low volume" in vol_ctx:
            base += " Lack of participation kept the price range-bound."
        if "flat" in trend_ctx or "ranging" in trend_ctx:
            base += " Market ranged with no directional conviction."
        return base + intraday_note

    if outcome == "TARGET HIT":
        base = (
            f"Strong momentum carried the stock past the target (₹{predicted_target}). "
            f"Volume: {vol_ctx}; Trend: {trend_ctx}."
        )
        if "high volume" in vol_ctx:
            base += " Volume confirmed the breakout direction."
        return base + intraday_note

    if outcome == "STOP LOSS HIT":
        breach = round(predicted_sl - actuals["low"], 2)
        base = (
            f"Trend reversal detected. The stock broke key support at "
            f"₹{predicted_sl} (breached by ₹{breach}). "
            f"Trend: {trend_ctx}; Volume: {vol_ctx}."
        )
        if "low volume" in vol_ctx:
            base += " Likely a fakeout on low volume — thin order book amplified the move."
        if "downtrend" in trend_ctx:
            base += " Broader selling pressure overrode the breakout thesis."
        base += " The model will retrain to recognize this false signal."
        return base + intraday_note

    if outcome == "STAGNANT":
        close = actuals["close"]
        entry = predicted_entry
        pct_move = round(((close - entry) / entry) * 100, 2)
        base = (
            f"Low volatility. Entry was triggered at ₹{entry} but the stock "
            f"closed at ₹{close} ({pct_move:+.2f}%), failing to reach either "
            f"target (₹{predicted_target}) or stop-loss (₹{predicted_sl}). "
            f"Volume: {vol_ctx}; Trend: {trend_ctx}."
        )
        if "low volume" in vol_ctx or "average volume" in vol_ctx:
            base += " Insufficient participation to sustain momentum."
        base += " Market lacked the power to push the stock to the target before closing."
        return base + intraday_note

    return "Outcome could not be classified."
