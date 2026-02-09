from datetime import date, datetime

def safe_float(value):
    try:
        return float(value)
    except Exception:
        return 0.0

def format_currency(value):
    return f"{value:,.0f} đ"

def format_ngaylap(value):
    if isinstance(value, datetime):
        return value.strftime("%d/%m/%Y %H:%M:%S")
    if isinstance(value, date):
        return value.strftime("%d/%m/%Y 00:00:00")
    return datetime.now().strftime("%d/%m/%Y %H:%M:%S")
