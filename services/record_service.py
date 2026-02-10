# services/record_service.py
from datetime import date
import unicodedata
import re

from sqlalchemy import func
from db.models import HoSo, DonThuoc
from db.session import get_session


# -------------------------
# Fetch
# -------------------------
def fetch_records():
    session = get_session()

    # 1️⃣ Subquery: latest NgayLap per HoSo
    latest_donthuoc = (
        session.query(
            DonThuoc.HoSoID.label("hoso_id"),
            func.max(DonThuoc.NgayLap).label("latest_ngaylap"),
        )
        .group_by(DonThuoc.HoSoID)
        .subquery()
    )

    # 2️⃣ Main query: LEFT JOIN subquery
    rows = (
        session.query(
            HoSo.HoSoID,
            HoSo.Ten,
            HoSo.NamSinh,
            HoSo.DiaChi,
            HoSo.DienThoai,
            HoSo.TienCan,
            func.coalesce(
                latest_donthuoc.c.latest_ngaylap,
                HoSo.NgayMoHoSo
            ).label("last_modified"),
        )
        .outerjoin(
            latest_donthuoc,
            latest_donthuoc.c.hoso_id == HoSo.HoSoID
        )
        .order_by(
            func.coalesce(
                latest_donthuoc.c.latest_ngaylap,
                HoSo.NgayMoHoSo
            ).desc()
        )
        .all()
    )

    session.close()

    return [
        (
            int(hoso_id),
            ten,
            int(namsinh) if namsinh is not None else None,
            diachi,
            dienthoai,
            tiencan,
            last_modified,
        )
        for (
            hoso_id,
            ten,
            namsinh,
            diachi,
            dienthoai,
            tiencan,
            last_modified,
        ) in rows
    ]


# -------------------------
# Create
# -------------------------
def create_record(name, year, address, phone, tiencan):
    session = get_session()
    hoso = HoSo(
        Ten=name,
        NamSinh=int(year) if year else None,
        DiaChi=address,
        DienThoai=phone,
        TienCan=tiencan,
        NgayMoHoSo=date.today(),
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
def remove_accents(s):
    return "".join(
        c for c in unicodedata.normalize("NFD", s)
        if unicodedata.category(c) != "Mn"
    )


def parse_search_query(query: str):
    query_norm = remove_accents(query.strip().lower())
    if not query_norm:
        return "", None
    nums = re.findall(r"\d+", query_norm)
    year = int(nums[0]) if nums else None
    letters = re.findall(r"[a-z]+", query_norm)
    name = " ".join(letters).strip()
    return name, year


def name_matches(full_name: str, name_query: str):
    if not name_query:
        return True
    full_norm = remove_accents(full_name.strip().lower())
    return full_norm.endswith(name_query)


def fetch_patient_suggestions(query: str):
    name_query, year_query = parse_search_query(query)
