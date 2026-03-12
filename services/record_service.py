# services/record_service.py
from datetime import date, datetime
import unicodedata
import re

from sqlalchemy import func, or_, case
from db.models import HoSo, DonThuoc
from db.session import get_session


# -------------------------
# Fetch
# -------------------------

def _apply_search_filters(query, search_query: str, exact_given_name=False):
    name_query, year_query = parse_search_query(search_query)
    if name_query:
        pattern = f"%{name_query}%"
        query = query.filter(
            or_(
                HoSo.GivenName.ilike(pattern),
                HoSo.Ten.ilike(pattern),
            )
        )
        query = query.order_by(
            case(
                (HoSo.GivenName == name_query.lower(), 1),
                (HoSo.GivenName.ilike(pattern), 2),
                (HoSo.Ten.ilike(pattern), 3),
                else_=4
            )
        )
    if year_query is not None:
        query = query.filter(HoSo.NamSinh == year_query)
    return query


def fetch_records_page(page, page_size, search_query=None, count=True):
    session = get_session()
    try:
        query = session.query(HoSo)
        if search_query:
            query = _apply_search_filters(query, search_query)
        
        total = query.count() if count else None
        rows = (
            query
            .order_by(HoSo.NgayMoHoSo.desc())
            .limit(page_size)
            .offset((page - 1) * page_size)
            .all()
        )
        result = [(r.HoSoID, r.Ten, r.NamSinh, r.DiaChi,
                   r.DienThoai, r.TienCan, r.NgayMoHoSo) for r in rows]
        return result, total
    finally:
        session.close()


def fetch_patient_suggestions(query: str):
    session = get_session()
    try:
        q = _apply_search_filters(session.query(HoSo), query)
        rows = q.limit(10).all()
        return [f"{r.Ten} - {r.NamSinh}" for r in rows]
    finally:
        session.close()

# -------------------------
# Create
# -------------------------
def create_record(name, year, address, phone, tiencan):
    session = get_session()
    hoso = HoSo(
        Ten=name,
        GivenName=name.strip().split()[-1].lower(),
        NamSinh=int(year) if year else None,
        DiaChi=address,
        DienThoai=phone,
        TienCan=tiencan,
        NgayMoHoSo=datetime.now(),
    )
    session.add(hoso)
    session.commit()
    session.close()


# -------------------------
# Update
# -------------------------
def update_record(hoso_id, name, year, address, phone, tiencan):
    session = get_session()
    h = session.get(HoSo, hoso_id)
    if h:
        h.Ten = name
        h.NamSinh = int(year) if year else None
        h.DiaChi = address
        h.DienThoai = phone
        h.TienCan = tiencan
        session.commit()
    session.close()


# -------------------------
# Delete
# -------------------------
def delete_record(hoso_id):
    session = get_session()
    h = session.get(HoSo, hoso_id)
    if h:
        session.delete(h)
        session.commit()
    session.close()


# -------------------------
# Search helpers
# -------------------------



def parse_search_query(query: str):
    query_norm = query.strip()
    if not query_norm:
        return None, None

    nums = re.findall(r"\d+", query_norm)
    year = int(nums[0]) if nums else None

    letters = re.findall(r"[^\W\d_]+", query_norm, re.UNICODE)
    name = " ".join(letters).strip() or None

    return name, year




