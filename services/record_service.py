from __future__ import annotations

from datetime import date, datetime
import re
from typing import Optional

from sqlalchemy import func, or_, case
from sqlalchemy.orm import Query
from db.models import HoSo, DonThuoc
from db.session import get_session

Record = tuple[int, str, Optional[int], Optional[str], Optional[str], Optional[str], Optional[datetime]]


def _apply_search_filters(
    query: Query,
    search_query: str,
    exact_given_name: bool = False,
) -> Query:
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
                else_=4,
            )
        )
    if year_query is not None:
        query = query.filter(HoSo.NamSinh == year_query)
    return query


def fetch_records_page(
    page: int,
    page_size: int,
    search_query: Optional[str] = None,
    count: bool = True,
) -> tuple[list[Record], Optional[int]]:
    session = get_session()
    try:
        query = session.query(HoSo)
        if search_query:
            query = _apply_search_filters(query, search_query)

        total: Optional[int] = query.count() if count else None
        rows = (
            query
            .order_by(HoSo.NgayMoHoSo.desc())
            .limit(page_size)
            .offset((page - 1) * page_size)
            .all()
        )
        result: list[Record] = [
            (r.HoSoID, r.Ten, r.NamSinh, r.DiaChi, r.DienThoai, r.TienCan, r.NgayMoHoSo)
            for r in rows
        ]
        return result, total
    finally:
        session.close()


def fetch_patient_suggestions(query: str) -> list[str]:
    session = get_session()
    try:
        q = _apply_search_filters(session.query(HoSo), query)
        rows = q.limit(10).all()
        return [f"{r.Ten} - {r.NamSinh}" for r in rows]
    finally:
        session.close()


def create_record(
    name: str,
    year: str,
    address: str,
    phone: str,
    tiencan: str,
) -> None:
    session = get_session()
    now = datetime.now()
    hoso = HoSo(
        Ten=name,
        GivenName=name.strip().split()[-1].lower(),
        NamSinh=int(year) if year else None,
        DiaChi=address,
        DienThoai=phone,
        TienCan=tiencan,
        NgayMoHoSo=now,
    )
    session.add(hoso)
    session.commit()
    session.close()


def update_record(
    hoso_id: int,
    name: str,
    year: str,
    address: str,
    phone: str,
    tiencan: str,
) -> None:
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


def delete_record(hoso_id: int) -> None:
    session = get_session()
    h = session.get(HoSo, hoso_id)
    if h:
        session.delete(h)
        session.commit()
    session.close()


def parse_search_query(query: str) -> tuple[Optional[str], Optional[int]]:
    query_norm = query.strip()
    if not query_norm:
        return None, None

    nums = re.findall(r"\d+", query_norm)
    year: Optional[int] = int(nums[0]) if nums else None

    letters = re.findall(r"[^\W\d_]+", query_norm, re.UNICODE)
    name: Optional[str] = " ".join(letters).strip() or None

    return name, year
