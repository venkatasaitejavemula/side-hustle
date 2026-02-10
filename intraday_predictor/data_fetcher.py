import logging
from datetime import date, timedelta

import pandas as pd
import yfinance as yf

from config import LOOKBACK_DAYS

logger = logging.getLogger(__name__)


def fetch_daily_ohlcv(ticker: str, days: int = LOOKBACK_DAYS) -> pd.DataFrame:
    end = date.today()
    start = end - timedelta(days=int(days * 1.6))
    df = yf.download(ticker, start=str(start), end=str(end), interval="1d", progress=False)
    if df.empty:
        logger.warning(f"No daily data for {ticker}")
        return df
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = df.columns.get_level_values(0)
    df.index = pd.to_datetime(df.index)
    return df.tail(days)


def fetch_intraday_ohlcv(ticker: str, target_date: date) -> pd.DataFrame:
    start = target_date
    end = target_date + timedelta(days=1)
    df = yf.download(ticker, start=str(start), end=str(end), interval="15m", progress=False)
    if df.empty:
        logger.warning(f"No 15m data for {ticker} on {target_date}")
        return df
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = df.columns.get_level_values(0)
    return df


def get_day_summary(ticker: str, target_date: date) -> dict | None:
    df = fetch_daily_ohlcv(ticker, days=5)
    if df.empty:
        return None

    df.index = pd.to_datetime(df.index).date
    if target_date in df.index:
        row = df.loc[target_date]
        if isinstance(row, pd.DataFrame):
            row = row.iloc[-1]
        return {
            "open": float(row["Open"]),
            "high": float(row["High"]),
            "low": float(row["Low"]),
            "close": float(row["Close"]),
            "volume": int(row["Volume"]),
        }

    df_intra = fetch_intraday_ohlcv(ticker, target_date)
    if df_intra.empty:
        return None
    return {
        "open": float(df_intra["Open"].iloc[0]),
        "high": float(df_intra["High"].max()),
        "low": float(df_intra["Low"].min()),
        "close": float(df_intra["Close"].iloc[-1]),
        "volume": int(df_intra["Volume"].sum()),
    }
