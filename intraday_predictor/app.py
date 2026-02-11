"""
HTTP API for testing: trigger next-day predictions (same as 4 PM batch)
and optionally send results by email.
"""
import logging
from datetime import date

from flask import Flask, jsonify, request

from database import init_db
from email_notifier import send_analysis_email, send_prediction_email
from performance_analyzer import analyze_predictions
from prediction_engine import generate_predictions
from trading_days import next_trading_day

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)

app = Flask(__name__)


def _run_full_job():
    """Same logic as the 4 PM batch: analyze today + predict tomorrow."""
    today = date.today()
    # Module 2: Analyze today's predictions vs actuals
    analysis_results = analyze_predictions(today)
    # Module 1: Generate predictions for next trading day
    target_date = next_trading_day(today)
    predictions = generate_predictions(target_date, prediction_date=today)
    return today, analysis_results, target_date, predictions


@app.route("/predict", methods=["GET", "POST"])
def predict():
    """
    Generate stock predictions for the next trading day (same as scheduled job).
    Optionally send the result by email.

    Query or JSON body:
      send_email: "true" | "false" (default false)
    """
    send_email = False
    if request.method == "POST" and request.is_json:
        send_email = request.json.get("send_email", False)
    else:
        send_email = request.args.get("send_email", "false").lower() in ("true", "1", "yes")

    try:
        analysis_date, analysis_results, target_date, predictions = _run_full_job()
    except Exception as e:
        logger.exception("Job failed")
        return jsonify({"error": str(e)}), 500

    # Serializable payload (date and floats)
    payload = {
        "analysis_date": analysis_date.isoformat(),
        "target_date": target_date.isoformat(),
        "prediction_count": len(predictions),
        "analysis_count": len(analysis_results),
        "predictions": [
            {
                "stock": p["stock"],
                "predicted_entry": p["predicted_entry"],
                "predicted_target": p["predicted_target"],
                "predicted_sl": p["predicted_sl"],
                "score": p.get("score"),
                "atr": p.get("atr"),
            }
            for p in predictions
        ],
    }

    if send_email:
        send_analysis_email(analysis_results, analysis_date)
        send_prediction_email(predictions, target_date)
        payload["emails_sent"] = {"analysis": True, "prediction": True}
    else:
        payload["emails_sent"] = {"analysis": False, "prediction": False}

    return jsonify(payload)


@app.route("/analyze", methods=["GET", "POST"])
def analyze():
    """
    Analyze today's predictions vs actual outcomes and optionally send the report by email.

    Query or JSON body:
      send_email: "true" | "false" (default false)
    """
    send_email = False
    if request.method == "POST" and request.is_json:
        send_email = request.json.get("send_email", False)
    else:
        send_email = request.args.get("send_email", "false").lower() in ("true", "1", "yes")

    try:
        today = date.today()
        results = analyze_predictions(today)
    except Exception as e:
        logger.exception("Analyze job failed")
        return jsonify({"error": str(e)}), 500

    if send_email:
        send_analysis_email(results, today)

    payload = {
        "analysis_date": today.isoformat(),
        "count": len(results),
        "results": [
            {
                "stock": r["stock"],
                "predicted_entry": r["predicted_entry"],
                "actual_high": r["actual_high"],
                "actual_low": r["actual_low"],
                "outcome": r["outcome"],
                "reason": r["reason"],
            }
            for r in results
        ],
        "email_sent": send_email,
    }
    return jsonify(payload)


@app.route("/health", methods=["GET"])
def health():
    """Health check for the API."""
    return jsonify({"status": "ok"})


def main():
    init_db()
    logger.info("Database initialized.")
    # Use config for host/port so it can be overridden by env if needed
    import os
    host = os.getenv("API_HOST", "0.0.0.0")
    port = int(os.getenv("API_PORT", "5000"))
    logger.info("Starting API — GET/POST /predict, GET/POST /analyze, GET /health")
    app.run(host=host, port=port, debug=False)


if __name__ == "__main__":
    main()
