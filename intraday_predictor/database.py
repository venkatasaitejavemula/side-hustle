from contextlib import contextmanager
from datetime import date, datetime
from typing import Any, Optional

from config import (
    ATR_MULTIPLIER,
    DB_PATH,
    PREDICTION_COUNT,
    RISK_REWARD_RATIO,
    USE_POSTGRES,
    POSTGRES_HOST,
    POSTGRES_PORT,
    POSTGRES_USER,
    POSTGRES_PASSWORD,
    POSTGRES_DB,
)

# Default model param keys (stored in model_params table)
DEFAULT_MODEL_PARAMS = {
    "atr_multiplier": ATR_MULTIPLIER,
    "risk_reward_ratio": RISK_REWARD_RATIO,
    "score_threshold": 4.0,
    "prediction_count": PREDICTION_COUNT,
}


def _get_postgres_conn():
    import psycopg2
    from psycopg2.extras import RealDictCursor
    return psycopg2.connect(
        host=POSTGRES_HOST,
        port=POSTGRES_PORT,
        user=POSTGRES_USER,
        password=POSTGRES_PASSWORD,
        dbname=POSTGRES_DB,
        cursor_factory=RealDictCursor,
    )


def init_db():
    if USE_POSTGRES:
        _init_postgres()
    else:
        _init_sqlite()


def _init_postgres():
    with _connect() as conn:
        conn.cursor().execute("""
            CREATE TABLE IF NOT EXISTS predictions (
                id SERIAL PRIMARY KEY,
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
        conn.cursor().execute("""
            CREATE TABLE IF NOT EXISTS model_metrics (
                id SERIAL PRIMARY KEY,
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
        conn.cursor().execute("""
            CREATE TABLE IF NOT EXISTS model_params (
                param_name TEXT PRIMARY KEY,
                param_value REAL NOT NULL,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        cur = conn.cursor()
        cur.execute("SELECT COUNT(*) AS n FROM model_params")
        if cur.fetchone()["n"] == 0:
            for name, value in DEFAULT_MODEL_PARAMS.items():
                cur.execute(
                    "INSERT INTO model_params (param_name, param_value) VALUES (%s, %s)",
                    (name, value),
                )
        conn.commit()


def _init_sqlite():
    import sqlite3
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    try:
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
        conn.execute("""
            CREATE TABLE IF NOT EXISTS model_params (
                param_name TEXT PRIMARY KEY,
                param_value REAL NOT NULL,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        cur = conn.execute("SELECT COUNT(*) FROM model_params")
        if cur.fetchone()[0] == 0:
            for name, value in DEFAULT_MODEL_PARAMS.items():
                conn.execute(
                    "INSERT INTO model_params (param_name, param_value) VALUES (?, ?)",
                    (name, value),
                )
        conn.commit()
    finally:
        conn.close()


@contextmanager
def _connect():
    if USE_POSTGRES:
        conn = _get_postgres_conn()
        try:
            yield conn
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()
    else:
        import sqlite3
        conn = sqlite3.connect(str(DB_PATH))
        conn.row_factory = sqlite3.Row
        try:
            yield conn
            conn.commit()
        finally:
            conn.close()


def _row_to_dict(row: Any) -> dict:
    if hasattr(row, "keys"):
        return dict(row)
    return dict(zip([c[0] for c in row.cursor.description], row)) if row else {}


def insert_predictions(rows: list[dict]):
    with _connect() as conn:
        cur = conn.cursor()
        if USE_POSTGRES:
            for r in rows:
                cur.execute(
                    """INSERT INTO predictions
                       (prediction_date, target_date, stock, predicted_entry, predicted_target, predicted_sl)
                       VALUES (%s, %s, %s, %s, %s, %s)
                       ON CONFLICT (target_date, stock) DO UPDATE SET
                         prediction_date = EXCLUDED.prediction_date,
                         predicted_entry = EXCLUDED.predicted_entry,
                         predicted_target = EXCLUDED.predicted_target,
                         predicted_sl = EXCLUDED.predicted_sl
                    """,
                    (
                        r["prediction_date"],
                        r["target_date"],
                        r["stock"],
                        r["predicted_entry"],
                        r["predicted_target"],
                        r["predicted_sl"],
                    ),
                )
        else:
            cur.executemany(
                """INSERT OR REPLACE INTO predictions
                   (prediction_date, target_date, stock, predicted_entry, predicted_target, predicted_sl)
                   VALUES (?, ?, ?, ?, ?, ?)
                """,
                [
                    (
                        r["prediction_date"],
                        r["target_date"],
                        r["stock"],
                        r["predicted_entry"],
                        r["predicted_target"],
                        r["predicted_sl"],
                    )
                    for r in rows
                ],
            )


def get_predictions_for_date(target_date: date) -> list[dict]:
    with _connect() as conn:
        cur = conn.cursor()
        if USE_POSTGRES:
            cur.execute(
                "SELECT * FROM predictions WHERE target_date = %s",
                (target_date.isoformat(),),
            )
            rows = cur.fetchall()
        else:
            rows = cur.execute(
                "SELECT * FROM predictions WHERE target_date = ?",
                (target_date.isoformat(),),
            ).fetchall()
    return [dict(r) for r in rows]


def update_prediction_outcome(prediction_id: int, actuals: dict, outcome: str, reason: str):
    with _connect() as conn:
        cur = conn.cursor()
        args = (
            actuals["open"],
            actuals["high"],
            actuals["low"],
            actuals["close"],
            actuals.get("volume", 0),
            outcome,
            reason,
            prediction_id,
        )
        if USE_POSTGRES:
            cur.execute(
                """UPDATE predictions
                   SET actual_open = %s, actual_high = %s, actual_low = %s, actual_close = %s,
                       actual_volume = %s, outcome = %s, reason = %s
                   WHERE id = %s
                """,
                args,
            )
        else:
            cur.execute(
                """UPDATE predictions
                   SET actual_open = ?, actual_high = ?, actual_low = ?, actual_close = ?,
                       actual_volume = ?, outcome = ?, reason = ?
                   WHERE id = ?
                """,
                args,
            )


def insert_model_metrics(metrics: dict):
    with _connect() as conn:
        cur = conn.cursor()
        if USE_POSTGRES:
            cur.execute(
                """INSERT INTO model_metrics
                   (eval_date, total_predictions, target_hit, sl_hit, no_entry, stagnant, win_rate, retrained)
                   VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                """,
                (
                    metrics["eval_date"],
                    metrics["total_predictions"],
                    metrics["target_hit"],
                    metrics["sl_hit"],
                    metrics["no_entry"],
                    metrics["stagnant"],
                    metrics["win_rate"],
                    metrics["retrained"],
                ),
            )
        else:
            cur.execute(
                """INSERT INTO model_metrics
                   (eval_date, total_predictions, target_hit, sl_hit, no_entry, stagnant, win_rate, retrained)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    metrics["eval_date"],
                    metrics["total_predictions"],
                    metrics["target_hit"],
                    metrics["sl_hit"],
                    metrics["no_entry"],
                    metrics["stagnant"],
                    metrics["win_rate"],
                    metrics["retrained"],
                ),
            )


def get_recent_win_rate(lookback: int = 5) -> Optional[float]:
    with _connect() as conn:
        cur = conn.cursor()
        if USE_POSTGRES:
            cur.execute(
                "SELECT AVG(win_rate) AS avg_wr FROM (SELECT win_rate FROM model_metrics ORDER BY eval_date DESC LIMIT %s) t",
                (lookback,),
            )
        else:
            cur.execute(
                "SELECT AVG(win_rate) AS avg_wr FROM (SELECT win_rate FROM model_metrics ORDER BY eval_date DESC LIMIT ?) t",
                (lookback,),
            )
        row = cur.fetchone()
    return float(row["avg_wr"]) if row and row["avg_wr"] is not None else None


def get_model_param(param_name: str) -> Optional[float]:
    with _connect() as conn:
        cur = conn.cursor()
        if USE_POSTGRES:
            cur.execute("SELECT param_value FROM model_params WHERE param_name = %s", (param_name,))
        else:
            cur.execute("SELECT param_value FROM model_params WHERE param_name = ?", (param_name,))
        row = cur.fetchone()
    return float(row["param_value"]) if row else None


def set_model_param(param_name: str, value: float):
    with _connect() as conn:
        cur = conn.cursor()
        now = datetime.utcnow().isoformat()
        if USE_POSTGRES:
            cur.execute(
                """INSERT INTO model_params (param_name, param_value, updated_at)
                   VALUES (%s, %s, %s)
                   ON CONFLICT (param_name) DO UPDATE SET
                     param_value = EXCLUDED.param_value,
                     updated_at = EXCLUDED.updated_at
                """,
                (param_name, value, now),
            )
        else:
            cur.execute(
                """INSERT INTO model_params (param_name, param_value, updated_at)
                   VALUES (?, ?, ?)
                   ON CONFLICT(param_name) DO UPDATE SET
                     param_value = excluded.param_value,
                     updated_at = excluded.updated_at
                """,
                (param_name, value, now),
            )


def get_all_model_params() -> dict[str, float]:
    with _connect() as conn:
        cur = conn.cursor()
        cur.execute("SELECT param_name, param_value FROM model_params")
        rows = cur.fetchall()
    out = dict(DEFAULT_MODEL_PARAMS)
    for r in rows:
        out[r["param_name"]] = float(r["param_value"])
    return out


def get_predictions_with_outcomes(limit: int = 60) -> list[dict]:
    with _connect() as conn:
        cur = conn.cursor()
        if USE_POSTGRES:
            cur.execute(
                """SELECT id, target_date, stock, predicted_entry, predicted_target, predicted_sl,
                          actual_high, actual_low, outcome
                   FROM predictions
                   WHERE outcome IS NOT NULL AND actual_high IS NOT NULL AND actual_low IS NOT NULL
                   ORDER BY target_date DESC
                   LIMIT %s
                """,
                (limit,),
            )
        else:
            cur.execute(
                """SELECT id, target_date, stock, predicted_entry, predicted_target, predicted_sl,
                          actual_high, actual_low, outcome
                   FROM predictions
                   WHERE outcome IS NOT NULL AND actual_high IS NOT NULL AND actual_low IS NOT NULL
                   ORDER BY target_date DESC
                   LIMIT ?
                """,
                (limit,),
            )
        rows = cur.fetchall()
    return [dict(r) for r in rows]
