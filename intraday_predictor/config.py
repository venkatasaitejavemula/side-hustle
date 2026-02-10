import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

BASE_DIR = Path(__file__).resolve().parent
DB_PATH = BASE_DIR / "data" / "predictions.db"

NIFTY_200_TICKERS = [
    "RELIANCE.NS", "TCS.NS", "HDFCBANK.NS", "INFY.NS", "ICICIBANK.NS",
    "HINDUNILVR.NS", "SBIN.NS", "BHARTIARTL.NS", "KOTAKBANK.NS", "ITC.NS",
    "LT.NS", "AXISBANK.NS", "BAJFINANCE.NS", "ASIANPAINT.NS", "MARUTI.NS",
    "SUNPHARMA.NS", "TITAN.NS", "ULTRACEMCO.NS", "NESTLEIND.NS", "WIPRO.NS",
    "HCLTECH.NS", "POWERGRID.NS", "NTPC.NS", "TATAMOTORS.NS", "ADANIENT.NS",
    "ADANIPORTS.NS", "JSWSTEEL.NS", "TATASTEEL.NS", "BAJAJFINSV.NS", "TECHM.NS",
    "ONGC.NS", "COALINDIA.NS", "HDFCLIFE.NS", "SBILIFE.NS", "DIVISLAB.NS",
    "DRREDDY.NS", "GRASIM.NS", "CIPLA.NS", "APOLLOHOSP.NS", "EICHERMOT.NS",
    "HEROMOTOCO.NS", "BPCL.NS", "INDUSINDBK.NS", "TATACONSUM.NS", "BRITANNIA.NS",
    "M&M.NS", "BAJAJ-AUTO.NS", "DABUR.NS", "VEDL.NS", "HINDALCO.NS",
]

PREDICTION_COUNT = 5

# Risk/Reward ratio for target calculation
RISK_REWARD_RATIO = 2.0

# ATR multiplier for stop-loss
ATR_MULTIPLIER = 1.5

# Lookback period for technical analysis (trading days)
LOOKBACK_DAYS = 60

# Retraining threshold — retrain if win rate drops below this
RETRAIN_ACCURACY_THRESHOLD = 0.40

EMAIL_SENDER = os.getenv("EMAIL_SENDER", "")
EMAIL_PASSWORD = os.getenv("EMAIL_PASSWORD", "")
EMAIL_RECIPIENT = os.getenv("EMAIL_RECIPIENT", "")
SMTP_SERVER = os.getenv("SMTP_SERVER", "smtp.gmail.com")
SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))

SCHEDULE_HOUR = 16  # 4:00 PM IST
SCHEDULE_MINUTE = 0
TIMEZONE = "Asia/Kolkata"
