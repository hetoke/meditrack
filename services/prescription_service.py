# services/prescription_service.py
from datetime import date, datetime
from sqlalchemy.orm import selectinload, joinedload

from db.models import DonThuoc, ChiDinh, Thuoc
from db.session import get_session


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




def calculate_total_from_donthuoc(donthuoc_obj):
    if not donthuoc_obj:
        return 0.0

    total = 0.0
    for chi in donthuoc_obj.chidinh_list:
        price = float(chi.thuoc.Gia or 0) if chi.thuoc else 0.0
        dose = (
            safe_float(chi.SangTruocAn)
            + safe_float(chi.SangSauAn)
            + safe_float(chi.TruaTruocAn)
            + safe_float(chi.TruaSauAn)
            + safe_float(chi.ChieuTruocAn)
            + safe_float(chi.ChieuSauAn)
            + safe_float(chi.Toi)
        )
        total += dose * price
    return total

def fetch_prescriptions_by_hoso(hoso_id):
    session = get_session()
    try:
        prescriptions = (
            session.query(DonThuoc)
            .options(joinedload(DonThuoc.chidinh_list).joinedload(ChiDinh.thuoc))
            .filter(DonThuoc.HoSoID == hoso_id)
            .order_by(DonThuoc.NgayLap)
            .all()
        )
        return prescriptions
    finally:
        session.close()


def delete_prescription_by_id(donthuoc_id):
    session = get_session()
    try:
        don = session.get(DonThuoc, donthuoc_id)
        if not don:
            return
        for chi in list(don.chidinh_list):
            session.delete(chi)
        session.delete(don)
        session.commit()
    finally:
        session.close()

def normalize_cells(row):
    # dict row from new UI
    if isinstance(row, dict):
        row = row.get("entries", row)

    # list of Entry widgets
    if row and hasattr(row[0], "get"):
        return [e.get().strip() for e in row]

    # already list of strings
    return [str(v).strip() for v in row]

def save_prescription(
    hoso_id,
    donthuoc_obj,
    chandoan_text,
    entry_rows,
):
    """
    entry_rows: list[list[tk.Entry]]  (UI owns widgets, service reads values)
    """
    session = get_session()
    try:
        if donthuoc_obj is None:
            donthuoc_obj = DonThuoc(
                HoSoID=hoso_id,
            )

        donthuoc_obj.NgayLap = datetime.now()
        donthuoc_obj.MoTa = chandoan_text
        donthuoc_obj = session.merge(donthuoc_obj)
        session.commit()

        # clear old ChiDinh
        for chi in list(donthuoc_obj.chidinh_list):
            session.delete(chi)
        session.commit()

        total_cost = 0.0

        for row in entry_rows:
            values = normalize_cells(row)

            if not any(values):
                continue

            name = values[0]
            thuoc_obj = session.query(Thuoc).filter(Thuoc.Ten == name).first()
            if not thuoc_obj:
                raise ValueError(f"Thuốc '{name}' không tồn tại")

            price = float(thuoc_obj.Gia or 0)

            doses = [safe_float(v) for v in values[1:8]]
            total_cost += sum(doses) * price

            chi = ChiDinh(
                DonThuocID=donthuoc_obj.DonThuocID,
                ThuocID=thuoc_obj.ThuocID,
                SangTruocAn=doses[0],
                SangSauAn=doses[1],
                TruaTruocAn=doses[2],
                TruaSauAn=doses[3],
                ChieuTruocAn=doses[4],
                ChieuSauAn=doses[5],
                Toi=doses[6],
            )
            session.add(chi)

        donthuoc_obj.TienToa = total_cost
        session.commit()

        donthuoc_obj = session.get(
            DonThuoc,
            donthuoc_obj.DonThuocID,
            options=[selectinload(DonThuoc.chidinh_list).selectinload(ChiDinh.thuoc)],
        )

        return donthuoc_obj, total_cost

    finally:
        session.close()

def fetch_thuoc_suggestions(prefix: str):
    if not prefix:
        return []

    session = get_session()
    try:
        return [
            t.Ten
            for t in session.query(Thuoc)
            .filter(Thuoc.Ten.ilike(f"{prefix}%"))
            .order_by(Thuoc.Ten)
            .limit(20)
            .all()
        ]
    finally:
        session.close()
