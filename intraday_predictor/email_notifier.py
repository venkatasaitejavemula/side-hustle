import logging
import smtplib
from datetime import date
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from config import EMAIL_PASSWORD, EMAIL_RECIPIENT, EMAIL_SENDER, SMTP_PORT, SMTP_SERVER

logger = logging.getLogger(__name__)


def _send_email(subject: str, html_body: str):
    if not all([EMAIL_SENDER, EMAIL_PASSWORD, EMAIL_RECIPIENT]):
        logger.warning("Email credentials not configured — printing to console instead.")
        print(f"\n{'='*80}\nSUBJECT: {subject}\n{'='*80}\n")
        print(html_body)
        return

    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = EMAIL_SENDER
    msg["To"] = EMAIL_RECIPIENT
    msg.attach(MIMEText(html_body, "html"))

    with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
        server.starttls()
        server.login(EMAIL_SENDER, EMAIL_PASSWORD)
        server.sendmail(EMAIL_SENDER, EMAIL_RECIPIENT, msg.as_string())

    logger.info(f"Email sent: {subject}")


def send_prediction_email(predictions: list[dict], target_date: date):
    if not predictions:
        logger.info("No predictions to email.")
        return

    rows_html = ""
    for p in predictions:
        rows_html += f"""
        <tr>
            <td style="padding:8px;border:1px solid #ddd;">{p['stock'].replace('.NS','')}</td>
            <td style="padding:8px;border:1px solid #ddd;text-align:right;">₹{p['predicted_entry']:.2f}</td>
            <td style="padding:8px;border:1px solid #ddd;text-align:right;color:#27ae60;">₹{p['predicted_target']:.2f}</td>
            <td style="padding:8px;border:1px solid #ddd;text-align:right;color:#e74c3c;">₹{p['predicted_sl']:.2f}</td>
            <td style="padding:8px;border:1px solid #ddd;text-align:right;">{p.get('score', '-')}</td>
        </tr>"""

    html = f"""
    <html><body style="font-family:Arial,sans-serif;max-width:700px;margin:auto;">
    <h2 style="color:#2c3e50;">📈 Intraday Predictions for {target_date.strftime('%A, %d %b %Y')}</h2>
    <p>The following stocks show strong breakout setups for tomorrow's session.
    Entry is valid only if price crosses the trigger level.</p>
    <table style="border-collapse:collapse;width:100%;">
        <thead>
            <tr style="background:#2c3e50;color:white;">
                <th style="padding:10px;border:1px solid #ddd;">Stock</th>
                <th style="padding:10px;border:1px solid #ddd;">Entry (Trigger)</th>
                <th style="padding:10px;border:1px solid #ddd;">Target</th>
                <th style="padding:10px;border:1px solid #ddd;">Stop Loss</th>
                <th style="padding:10px;border:1px solid #ddd;">Score</th>
            </tr>
        </thead>
        <tbody>{rows_html}</tbody>
    </table>
    <p style="color:#7f8c8d;font-size:12px;margin-top:20px;">
        Risk/Reward: 1:2 | SL: ATR-based | Generated at 4:00 PM IST<br>
        <em>This is an algorithmic system — not financial advice.</em>
    </p>
    </body></html>
    """
    _send_email(f"🔮 Stock Predictions — {target_date.strftime('%d %b %Y')}", html)


def send_analysis_email(results: list[dict], analysis_date: date):
    if not results:
        logger.info("No analysis results to email.")
        return

    outcome_colors = {
        "TARGET HIT": "#27ae60",
        "STOP LOSS HIT": "#e74c3c",
        "NO ENTRY": "#95a5a6",
        "STAGNANT": "#f39c12",
    }

    rows_html = ""
    for r in results:
        color = outcome_colors.get(r["outcome"], "#333")
        rows_html += f"""
        <tr>
            <td style="padding:8px;border:1px solid #ddd;">{r['stock'].replace('.NS','')}</td>
            <td style="padding:8px;border:1px solid #ddd;text-align:right;">₹{r['predicted_entry']:.2f}</td>
            <td style="padding:8px;border:1px solid #ddd;text-align:right;">₹{r['actual_high']:.2f}</td>
            <td style="padding:8px;border:1px solid #ddd;text-align:right;">₹{r['actual_low']:.2f}</td>
            <td style="padding:8px;border:1px solid #ddd;text-align:center;">
                <span style="color:{color};font-weight:bold;">{r['outcome']}</span>
            </td>
            <td style="padding:8px;border:1px solid #ddd;font-size:12px;">{r['reason']}</td>
        </tr>"""

    total = len(results)
    wins = sum(1 for r in results if r["outcome"] == "TARGET HIT")
    win_rate = f"{(wins/total)*100:.0f}%" if total else "N/A"

    html = f"""
    <html><body style="font-family:Arial,sans-serif;max-width:900px;margin:auto;">
    <h2 style="color:#2c3e50;">📊 Performance Report — {analysis_date.strftime('%A, %d %b %Y')}</h2>
    <p><strong>Results:</strong> {wins}/{total} targets hit ({win_rate} accuracy)</p>
    <table style="border-collapse:collapse;width:100%;">
        <thead>
            <tr style="background:#2c3e50;color:white;">
                <th style="padding:10px;border:1px solid #ddd;">Stock</th>
                <th style="padding:10px;border:1px solid #ddd;">Predicted Entry</th>
                <th style="padding:10px;border:1px solid #ddd;">Actual High</th>
                <th style="padding:10px;border:1px solid #ddd;">Actual Low</th>
                <th style="padding:10px;border:1px solid #ddd;">Outcome</th>
                <th style="padding:10px;border:1px solid #ddd;">Why?</th>
            </tr>
        </thead>
        <tbody>{rows_html}</tbody>
    </table>
    <p style="color:#7f8c8d;font-size:12px;margin-top:20px;">
        Auto-generated post-mortem. Model retrains automatically when win rate drops below 40%.<br>
        <em>This is an algorithmic system — not financial advice.</em>
    </p>
    </body></html>
    """
    _send_email(f"📊 Performance Report — {analysis_date.strftime('%d %b %Y')}", html)
