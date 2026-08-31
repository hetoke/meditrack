import unicodedata

from db.models import Thuoc
from db.session import get_session
from services.prescription_service import invalidate_price_cache


VI_BASE_ORDER = {
    "ă": "a1",
    "â": "a2",
    "đ": "dz",
    "ê": "e1",
    "ô": "o1",
    "ơ": "o2",
    "ư": "u1",
}


def remove_tone_marks(text):
    normalized = unicodedata.normalize("NFD", text)
    return "".join(c for c in normalized if unicodedata.category(c) != "Mn")


def vietnamese_sort_key(text):
    text = remove_tone_marks(text.lower())
    return "".join(VI_BASE_ORDER.get(char, char) for char in text)


def fetch_medicines():
    session = get_session()
    try:
        rows = session.query(Thuoc.Ten, Thuoc.Gia).all()
        medicines_sorted = sorted(rows, key=lambda t: vietnamese_sort_key(t[0]))
        return [(t[0], float(t[1])) for t in medicines_sorted]
    finally:
        session.close()


def add_medicine(name, price):
    session = get_session()
    try:
        session.add(Thuoc(Ten=name, Gia=int(price)))
        session.commit()
        invalidate_price_cache()
    finally:
        session.close()


def update_medicine(old_name, new_name, new_price):
    session = get_session()
    try:
        medicine = session.query(Thuoc).filter_by(Ten=old_name).first()
        if medicine:
            medicine.Ten = new_name
            medicine.Gia = int(new_price)
            session.commit()
            invalidate_price_cache()
    finally:
        session.close()


def delete_medicine_by_name(name):
    session = get_session()
    try:
        medicine = session.query(Thuoc).filter_by(Ten=name).first()
        if medicine:
            session.delete(medicine)
            session.commit()
            invalidate_price_cache()
    finally:
        session.close()
