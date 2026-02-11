# Intraday Predictor

A Python app that generates daily intraday stock predictions for Nifty 200 (NSE) and emails performance reports. It uses technical indicators (RSI, MACD, ATR) to pick breakout setups and retrains parameters when win rate drops.

## Prerequisites

- **Python 3.10+**
- **Docker Desktop** (for running PostgreSQL)
- (Optional) Gmail account with app password for email reports

## 1. Clone and enter the project

```bash
cd path/to/Side-Hustle/intraday_predictor
```

## 2. Create a virtual environment (recommended)

```bash
python -m venv venv
# Windows (PowerShell)
.\venv\Scripts\Activate.ps1
# Windows (CMD)
venv\Scripts\activate.bat
# macOS / Linux
source venv/bin/activate
```

## 3. Install Python dependencies

```bash
pip install -r requirements.txt
```

This installs: `yfinance`, `pandas`, `numpy`, `APScheduler`, `pytz`, `python-dotenv`, `psycopg2-binary`.

## 4. Start PostgreSQL with Docker

From the `intraday_predictor` directory (where `docker-compose.yml` lives):

```bash
docker compose up -d
```

This starts a PostgreSQL 16 container. The DB is exposed on `localhost:5432` by default. To stop:

```bash
docker compose down
```

## 5. Configure environment variables

Copy the example env file and edit it with your values:

```bash
copy .env.example .env   # Windows
# or
cp .env.example .env     # macOS / Linux
```

Edit `.env` and set at least:

| Variable | Description |
|----------|-------------|
| `POSTGRES_HOST` | `localhost` when using Docker |
| `POSTGRES_PASSWORD` | Same value you use in Docker (see below) |
| `POSTGRES_USER` | Default: `predictor` |
| `POSTGRES_DB` | Default: `predictions` |

To use the same credentials as the default in `docker-compose.yml`, you can set:

```env
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
POSTGRES_USER=predictor
POSTGRES_PASSWORD=predictor_secret
POSTGRES_DB=predictions
```

For email reports, set `EMAIL_SENDER`, `EMAIL_PASSWORD`, and `EMAIL_RECIPIENT`. If these are empty, the app prints reports to the console.

## 6. Run the app on localhost

**One-off run (no scheduler):**

```bash
python main.py --now
```

This initializes the database, runs the daily job once (analyze today’s predictions, generate tomorrow’s, send emails or print to console), then exits.

**Scheduled run (Mon–Fri at 4:00 PM IST):**

```bash
python main.py
```

The app stays running and runs the daily job at the configured time. Stop with `Ctrl+C`.

**Test API (predict next day + optional email):**

```bash
python app.py
```

Then:

- **GET** `http://localhost:5000/predict` — run prediction for the next trading day, return JSON (no email).
- **GET** `http://localhost:5000/predict?send_email=true` — same and send the result to the configured `EMAIL_RECIPIENT`.
- **POST** `http://localhost:5000/predict` with body `{"send_email": true}` — same as above.
- **GET** `http://localhost:5000/health` — health check.

The prediction logic is the same as the 4 PM batch job (next trading day, same model and config). Use `API_HOST` / `API_PORT` in `.env` to change host/port (default `0.0.0.0:5000`).

---

## Database behaviour

- **With PostgreSQL:** Set `POSTGRES_HOST` and `POSTGRES_PASSWORD` in `.env` and start the DB with `docker compose up -d`. The app will create tables on first run.
- **Without PostgreSQL:** If `POSTGRES_HOST` is not set, the app uses a local **SQLite** file at `data/predictions.db` (no Docker required).

## Project layout

```
intraday_predictor/
├── main.py              # Entry point, scheduler
├── app.py               # API server: /predict, /health
├── trading_days.py      # Next/prev trading day helpers
├── config.py            # Settings, Nifty 200 list
├── database.py          # PostgreSQL / SQLite
├── data_fetcher.py      # Yahoo Finance OHLCV
├── prediction_engine.py # Scoring and levels
├── performance_analyzer.py # Post-mortem and retrain
├── why_generator.py     # Outcome explanations
├── email_notifier.py    # Email reports
├── docker-compose.yml   # PostgreSQL service
├── .env.example         # Env template
├── requirements.txt
└── README.md
```

## Disclaimer

This is an algorithmic system for educational use. It is not financial advice. Use at your own risk.
