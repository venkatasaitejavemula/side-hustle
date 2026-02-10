"""
Module 2: The Performance Analyzer (Post-Mortem)

Compares yesterday's predictions against actual market data, classifies each
outcome (NO ENTRY / TARGET HIT / STOP LOSS HIT / STAGNANT), generates
human-readable technical reasons, and feeds metrics back for retraining decisions.
"""

import logging
from datetime import date

from data_fetcher import get_day_summary
from database import (
    get_predictions_for_date,
    get_recent_win_rate,
    insert_model_metrics,
    update_prediction_outcome,
)
from why_generator import generate_reason
from config import RETRAIN_ACCURACY_THRESHOLD

logger = logging.getLogger(__name__)


def _classify_outcome(
    predicted_entry: float,
    predicted_target: float,
    predicted_sl: float,
    actuals: dict,
) -> str:
    """
    Determines the outcome category based on actual vs predicted levels.

    Priority order when multiple conditions are true on the same day:
      1. NO ENTRY  — price never reached entry, so everything else is moot
      2. STOP LOSS HIT — counted as a loss regardless of intraday recovery
      3. TARGET HIT — full reward captured
      4. STAGNANT  — entry triggered but price stuck between SL and target
    """
    actual_high = actuals["high"]
    actual_low = actuals["low"]

    if actual_high < predicted_entry:
        return "NO ENTRY"

    if actual_low <= predicted_sl:
        return "STOP LOSS HIT"

    if actual_high >= predicted_target:
        return "TARGET HIT"

    return "STAGNANT"


def analyze_predictions(analysis_date: date) -> list[dict]:
    """
    Runs the post-mortem for a given trading day.

    Args:
        analysis_date: The date whose predictions we are validating
                       (i.e., the target_date stored in the DB).

    Returns:
        List of result dicts ready for the analysis email.
    """
    predictions = get_predictions_for_date(analysis_date)
    if not predictions:
        logger.info(f"No predictions found for {analysis_date}")
        return []

    results: list[dict] = []
    counters = {"TARGET HIT": 0, "STOP LOSS HIT": 0, "NO ENTRY": 0, "STAGNANT": 0}

    for pred in predictions:
        ticker = pred["stock"]
        logger.info(f"Analyzing {ticker} for {analysis_date}")

        actuals = get_day_summary(ticker, analysis_date)
        if actuals is None:
            logger.warning(f"Could not fetch actuals for {ticker} on {analysis_date}")
            continue

        outcome = _classify_outcome(
            pred["predicted_entry"],
            pred["predicted_target"],
            pred["predicted_sl"],
            actuals,
        )

        reason = generate_reason(
            outcome=outcome,
            ticker=ticker,
            predicted_entry=pred["predicted_entry"],
            predicted_target=pred["predicted_target"],
            predicted_sl=pred["predicted_sl"],
            actuals=actuals,
            target_date=analysis_date,
        )

        update_prediction_outcome(pred["id"], actuals, outcome, reason)
        counters[outcome] += 1

        results.append(
            {
                "stock": ticker,
                "predicted_entry": pred["predicted_entry"],
                "predicted_target": pred["predicted_target"],
                "predicted_sl": pred["predicted_sl"],
                "actual_open": actuals["open"],
                "actual_high": actuals["high"],
                "actual_low": actuals["low"],
                "actual_close": actuals["close"],
                "actual_volume": actuals["volume"],
                "outcome": outcome,
                "reason": reason,
            }
        )

    total = len(results)
    if total == 0:
        return results

    win_rate = round(counters["TARGET HIT"] / total, 4)
    retrained = _check_and_retrain(win_rate)

    insert_model_metrics(
        {
            "eval_date": analysis_date.isoformat(),
            "total_predictions": total,
            "target_hit": counters["TARGET HIT"],
            "sl_hit": counters["STOP LOSS HIT"],
            "no_entry": counters["NO ENTRY"],
            "stagnant": counters["STAGNANT"],
            "win_rate": win_rate,
            "retrained": int(retrained),
        }
    )

    logger.info(
        f"Analysis complete for {analysis_date}: "
        f"{counters} | Win rate: {win_rate:.1%} | Retrained: {retrained}"
    )
    return results


def _check_and_retrain(current_win_rate: float) -> bool:
    """Trigger retraining when accuracy degrades below threshold."""
    avg_win_rate = get_recent_win_rate(lookback=5)

    should_retrain = (
        avg_win_rate is not None and avg_win_rate < RETRAIN_ACCURACY_THRESHOLD
    ) or current_win_rate < RETRAIN_ACCURACY_THRESHOLD

    if should_retrain:
        logger.warning(
            f"Win rate ({current_win_rate:.1%}) below threshold "
            f"({RETRAIN_ACCURACY_THRESHOLD:.0%}). Triggering retrain."
        )
        _retrain_model()
        return True

    return False


def _retrain_model():
    """
    Placeholder for model retraining logic.

    In a production system this would:
      - Pull the last N days of labeled predictions from the DB
      - Re-optimize technical indicator weights / thresholds
      - Persist the updated model parameters
    """
    logger.info(
        "RETRAIN: Adjusting model parameters based on recent prediction failures. "
        "This is a placeholder — plug in your ML pipeline here."
    )
