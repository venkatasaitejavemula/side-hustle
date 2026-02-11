import logging
from datetime import date

import numpy as np
import pandas as pd

from config import NIFTY_200_TICKERS
from data_fetcher import fetch_daily_ohlcv
from database import get_all_model_params, insert_predictions

logger = logging.getLogger(__name__)


def _compute_atr(df: pd.DataFrame, period: int = 14) -> pd.Series:
    high = df["High"]
    low = df["Low"]
    close = df["Close"].shift(1)
    tr = pd.concat(
        [high - low, (high - close).abs(), (low - close).abs()], axis=1
    ).max(axis=1)
    return tr.rolling(window=period).mean()


def _compute_rsi(series: pd.Series, period: int = 14) -> pd.Series:
    delta = series.diff()
    gain = delta.clip(lower=0).rolling(window=period).mean()
    loss = (-delta.clip(upper=0)).rolling(window=period).mean()
    rs = gain / loss
    return 100 - (100 / (1 + rs))


def _compute_ema(series: pd.Series, span: int) -> pd.Series:
    return series.ewm(span=span, adjust=False).mean()


def _compute_macd(series: pd.Series) -> tuple[pd.Series, pd.Series]:
    ema12 = _compute_ema(series, 12)
    ema26 = _compute_ema(series, 26)
    macd_line = ema12 - ema26
    signal_line = _compute_ema(macd_line, 9)
    return macd_line, signal_line


def _compute_volume_sma(df: pd.DataFrame, period: int = 20) -> pd.Series:
    return df["Volume"].rolling(window=period).mean()


def _score_stock(df: pd.DataFrame) -> float | None:
    if len(df) < 30:
        return None

    close = df["Close"]
    atr = _compute_atr(df)
    rsi = _compute_rsi(close)
    macd_line, signal_line = _compute_macd(close)
    vol_sma = _compute_volume_sma(df)

    latest = df.iloc[-1]
    latest_rsi = rsi.iloc[-1]
    latest_macd = macd_line.iloc[-1]
    latest_signal = signal_line.iloc[-1]
    latest_vol = latest["Volume"]
    latest_vol_sma = vol_sma.iloc[-1]
    latest_atr = atr.iloc[-1]

    if pd.isna(latest_rsi) or pd.isna(latest_atr) or latest_atr == 0:
        return None

    score = 0.0

    # RSI sweet spot (40-60 = momentum building, not overbought)
    if 40 <= latest_rsi <= 60:
        score += 2.0
    elif 60 < latest_rsi <= 70:
        score += 1.0

    # MACD bullish crossover
    if latest_macd > latest_signal:
        score += 2.0
    if latest_macd > 0:
        score += 1.0

    # Volume surge
    if latest_vol_sma and latest_vol_sma > 0:
        vol_ratio = latest_vol / latest_vol_sma
        if vol_ratio > 1.5:
            score += 2.0
        elif vol_ratio > 1.2:
            score += 1.0

    # Price above 20-EMA (trend confirmation)
    ema20 = _compute_ema(close, 20).iloc[-1]
    if latest["Close"] > ema20:
        score += 1.5

    # Breakout proximity: price within 1 ATR of 20-day high
    high_20 = df["High"].tail(20).max()
    if (high_20 - latest["Close"]) <= latest_atr:
        score += 2.0

    return score


def _calculate_levels(df: pd.DataFrame, atr_multiplier: float, risk_reward_ratio: float) -> dict:
    atr_series = _compute_atr(df)
    atr = float(atr_series.iloc[-1])
    latest_close = float(df["Close"].iloc[-1])
    high_20 = float(df["High"].tail(20).max())

    entry = round(max(high_20, latest_close + atr * 0.3), 2)
    sl = round(entry - (atr_multiplier * atr), 2)
    risk = entry - sl
    target = round(entry + (risk_reward_ratio * risk), 2)

    return {"entry": entry, "target": target, "sl": sl, "atr": round(atr, 2)}


def generate_predictions(target_date: date, prediction_date: date) -> list[dict]:
    params = get_all_model_params()
    atr_mult = params["atr_multiplier"]
    rr_ratio = params["risk_reward_ratio"]
    score_threshold = params["score_threshold"]
    prediction_count = int(params["prediction_count"])

    scored: list[tuple[str, float, pd.DataFrame]] = []

    for ticker in NIFTY_200_TICKERS:
        try:
            df = fetch_daily_ohlcv(ticker)
            if df.empty:
                continue
            s = _score_stock(df)
            if s is not None and s > score_threshold:
                scored.append((ticker, s, df))
        except Exception as e:
            logger.warning(f"Skipping {ticker}: {e}")

    scored.sort(key=lambda x: x[1], reverse=True)
    top = scored[:prediction_count]

    predictions = []
    for ticker, score, df in top:
        levels = _calculate_levels(df, atr_mult, rr_ratio)
        predictions.append(
            {
                "prediction_date": prediction_date.isoformat(),
                "target_date": target_date.isoformat(),
                "stock": ticker,
                "predicted_entry": levels["entry"],
                "predicted_target": levels["target"],
                "predicted_sl": levels["sl"],
                "score": round(score, 2),
                "atr": levels["atr"],
            }
        )

    if predictions:
        insert_predictions(predictions)
        logger.info(f"Stored {len(predictions)} predictions for {target_date}")

    return predictions
