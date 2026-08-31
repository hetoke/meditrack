from __future__ import annotations

from datetime import date, datetime
from typing import Union


def safe_float(value: object) -> float:
    try:
        return float(value)
    except Exception:
        return 0.0


def format_currency(value: float) -> str:
    return f"{value:,.0f}"


def format_ngaylap(value: Union[datetime, date, None]) -> str:
    if isinstance(value, datetime):
        return value.strftime("%d/%m/%Y %H:%M:%S")
    if isinstance(value, date):
        return value.strftime("%d/%m/%Y 00:00:00")
    return datetime.now().strftime("%d/%m/%Y %H:%M:%S")
