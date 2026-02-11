import logging
from datetime import date

import pytz
from apscheduler.schedulers.blocking import BlockingScheduler

from config import SCHEDULE_HOUR, SCHEDULE_MINUTE, TIMEZONE
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

IST = pytz.timezone(TIMEZONE)


def daily_job():
    today = date.today()

    if today.weekday() >= 5:
        logger.info(f"Weekend ({today.strftime('%A')}) — skipping.")
        return

    logger.info(f"=== Running daily job for {today} ===")

    # --- Module 2: Analyze today's completed session against yesterday's predictions ---
    analysis_date = today
    logger.info(f"Analyzing predictions for {analysis_date}")
    results = analyze_predictions(analysis_date)
    send_analysis_email(results, analysis_date)

    # --- Module 1: Generate predictions for tomorrow ---
    target_date = next_trading_day(today)
    logger.info(f"Generating predictions for {target_date}")
    predictions = generate_predictions(target_date, prediction_date=today)
    send_prediction_email(predictions, target_date)

    logger.info("=== Daily job complete ===")


def main():
    init_db()
    logger.info("Database initialized.")

    import sys
    if "--now" in sys.argv:
        logger.info("Running immediately (--now flag).")
        daily_job()
        return

    scheduler = BlockingScheduler(timezone=IST)
    scheduler.add_job(
        daily_job,
        "cron",
        hour=SCHEDULE_HOUR,
        minute=SCHEDULE_MINUTE,
        day_of_week="mon-fri",
        id="daily_prediction_cycle",
    )
    logger.info(
        f"Scheduler started — job runs Mon-Fri at "
        f"{SCHEDULE_HOUR:02d}:{SCHEDULE_MINUTE:02d} IST."
    )

    try:
        scheduler.start()
    except (KeyboardInterrupt, SystemExit):
        logger.info("Scheduler stopped.")


if __name__ == "__main__":
    main()
