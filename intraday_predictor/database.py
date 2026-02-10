import sqlite3
from contextlib import contextmanager
from datetime import date
from typing import Optional

from config import DB_PATH


def init_db():
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    with _connect() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS predictions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                prediction_date DATE NOT NULL,
                target_date DATE NOT NULL,
                stock TEXT NOT NULL,
                predicted_entry REAL NOT NULL,
                predicted_target REAL NOT NULL,
                predicted_sl REAL NOT NULL,
                actual_open REAL,
                actual_high REAL,
                actual_low REAL,
                actual_close REAL,
                actual_volume INTEGER,
                outcome TEXT,
                reason TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(target_date, stock)
            )
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS model_metrics (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                eval_date DATE NOT NULL,
                total_predictions INTEGER,
                target_hit INTEGER,
                sl_hit INTEGER,
                no_entry INTEGER,
                stagnant INTEGER,
                win_rate REAL,
                retrained INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)


@contextmanager
def _connect():
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    try:
        yield conn
        conn.commit()
    finally:
        conn.close()


def insert_predictions(rows: list[dict]):
    with _connect() as conn:
        conn.executemany(
            """INSERT OR REPLACE INTO predictions
               (prediction_date, target_date, stock, predicted_entry, predicted_target, predicted_sl)
               VALUES (:prediction_date, :target_date, :stock, :predicted_entry, :predicted_target, :predicted_sl)
            """,
            rows,
        )


def get_predictions_for_date(target_date: date) -> list[dict]:
    with _connect() as conn:
        rows = conn.execute(
            "SELECT * FROM predictions WHERE target_date = ?",
            (target_date.isoformat(),),
        ).fetchall()
    return [dict(r) for r in rows]


def update_prediction_outcome(prediction_id: int, actuals: dict, outcome: str, reason: str):
    with _connect() as conn:
        conn.execute(
            """UPDATE predictions
               SET actual_open = ?, actual_high = ?, actual_low = ?, actual_close = ?,
                   actual_volume = ?, outcome = ?, reason = ?
               WHERE id = ?
            """,
            (
                actuals["open"],
                actuals["high"],
                actuals["low"],
                actuals["close"],
                actuals.get("volume", 0),
                outcome,
                reason,
                prediction_id,
            ),
        )


def insert_model_metrics(metrics: dict):
    with _connect() as conn:
        conn.execute(
            """INSERT INTO model_metrics
               (eval_date, total_predictions, target_hit, sl_hit, no_entry, stagnant, win_rate, retrained)
               VALUES (:eval_date, :total_predictions, :target_hit, :sl_hit, :no_entry, :stagnant, :win_rate, :retrained)
            """,
            metrics,
        )


def get_recent_win_rate(lookback: int = 5) -> Optional[float]:
    with _connect() as conn:
        row = conn.execute(
            "SELECT AVG(win_rate) as avg_wr FROM model_metrics ORDER BY eval_date DESC LIMIT ?",
            (lookback,),
        ).fetchone()
    return row["avg_wr"] if row and row["avg_wr"] is not None else None
