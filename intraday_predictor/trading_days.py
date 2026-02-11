"""Trading-day helpers: next/previous weekday (Mon–Fri)."""
from datetime import date, timedelta


def next_trading_day(from_date: date) -> date:
    """Return the next weekday (Mon–Fri) after from_date."""
    nxt = from_date + timedelta(days=1)
    while nxt.weekday() >= 5:  # Sat=5, Sun=6
        nxt += timedelta(days=1)
    return nxt


def prev_trading_day(from_date: date) -> date:
    """Return the most recent weekday (Mon–Fri) before from_date."""
    prev = from_date - timedelta(days=1)
    while prev.weekday() >= 5:
        prev -= timedelta(days=1)
    return prev
