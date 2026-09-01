from __future__ import annotations

from datetime import datetime
from typing import Any, Optional, Union

from sqlalchemy.orm import Session, selectinload, joinedload

from db.models import DonThuoc, ChiDinh, Thuoc, HoSo
from db.session import get_session
from utils.formatter import safe_float


RowData = Union[dict[str, Any], list[Any]]


def calculate_total_from_donthuoc(donthuoc_obj: Optional[DonThuoc]) -> float:
    if not donthuoc_obj:
        return 0.0

    total = 0.0
    for chi in donthuoc_obj.chidinh_list:
        days = getattr(chi, "SoNgay", 1)
        if days <= 0:
            continue
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
        total += dose * price * days
    return total


def fetch_prescription_summaries_by_hoso(
    hoso_id: int,
) -> list[tuple[int, Optional[datetime]]]:
    session = get_session()
    try:
        return (
            session.query(DonThuoc.DonThuocID, DonThuoc.NgayLap)
            .filter(DonThuoc.HoSoID == hoso_id)
            .order_by(DonThuoc.NgayLap)
            .all()
        )
    finally:
        session.close()


def fetch_prescription_detail_by_id(prescription_id: int) -> Optional[DonThuoc]:
    session = get_session()
    try:
        return (
            session.query(DonThuoc)
            .options(
                joinedload(DonThuoc.chidinh_list)
                .joinedload(ChiDinh.thuoc)
            )
            .filter(DonThuoc.DonThuocID == prescription_id)
            .first()
        )
    finally:
        session.close()


def fetch_prescriptions_by_hoso(hoso_id: int) -> list[DonThuoc]:
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


def delete_prescription_by_id(donthuoc_id: int) -> None:
    session = get_session()
    try:
        don = session.get(DonThuoc, donthuoc_id)
        if not don:
            return
        session.query(ChiDinh).filter(ChiDinh.DonThuocID == donthuoc_id).delete()
        session.delete(don)
        session.commit()
    finally:
        session.close()


def normalize_cells(row: RowData) -> list[str]:
    if isinstance(row, dict):
        row = row.get("entries", row)

    if row and hasattr(row[0], "get"):
        return [e.get().strip() for e in row]

    return [str(v).strip() for v in row]


def is_row_excluded(row: RowData) -> bool:
    if isinstance(row, dict):
        return row.get("days", 1) <= 0
    return False


def get_row_days(row: RowData) -> int:
    if isinstance(row, dict):
        return row.get("days", 1)
    return 1


def save_prescription(
    hoso_id: int,
    donthuoc_obj: Optional[DonThuoc],
    chandoan_text: str,
    entry_rows: list[RowData],
) -> tuple[DonThuoc, float]:
    session = get_session()
    try:
        if donthuoc_obj is None:
            donthuoc_obj = DonThuoc(HoSoID=hoso_id)
        donthuoc_obj.NgayLap = datetime.now()
        donthuoc_obj.MoTa = chandoan_text

        donthuoc_obj = session.merge(donthuoc_obj)
        session.flush()

        session.query(ChiDinh)\
            .filter(ChiDinh.DonThuocID == donthuoc_obj.DonThuocID)\
            .delete()

        valid_rows: list[list[str]] = []
        medicine_names: list[str] = []

        for row in entry_rows:
            values = normalize_cells(row)
            if not any(values):
                continue

            name = values[0]
            valid_rows.append(values)
            medicine_names.append(name)

        thuoc_list = (
            session.query(Thuoc)
            .filter(Thuoc.Ten.in_(medicine_names))
            .all()
        )

        thuoc_map: dict[str, Thuoc] = {t.Ten: t for t in thuoc_list}

        total_cost = 0.0

        for row in entry_rows:
            values = normalize_cells(row)
            if not any(values):
                continue

            name = values[0]
            thuoc_obj = thuoc_map.get(name)

            if not thuoc_obj:
                raise ValueError(f"Thuốc '{name}' không tồn tại")

            price = float(thuoc_obj.Gia or 0)
            doses = [safe_float(v) for v in values[1:8]]
            days = get_row_days(row)

            total_cost += sum(doses) * price * days

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
                SoNgay=days,
            )

            session.add(chi)

        donthuoc_obj.TienToa = total_cost
        session.commit()

        donthuoc_obj = session.get(
            DonThuoc,
            donthuoc_obj.DonThuocID,
            options=[
                selectinload(DonThuoc.chidinh_list)
                .selectinload(ChiDinh.thuoc)
            ],
        )

        return donthuoc_obj, total_cost

    finally:
        session.close()


_medicine_names_cache: dict[str, Optional[list[str]]] = {"names": None}


def fetch_thuoc_suggestions(prefix: str) -> list[str]:
    if not prefix:
        return []
    if _medicine_names_cache["names"] is None:
        session = get_session()
        try:
            _medicine_names_cache["names"] = [
                t.Ten for t in session.query(Thuoc.Ten).order_by(Thuoc.Ten).all()
            ]
        finally:
            session.close()
    prefix_lower = prefix.lower()
    return [
        name
        for name in _medicine_names_cache["names"]
        if name.lower().startswith(prefix_lower)
    ][:20]


def fetch_thuoc_price_map(names: list[str]) -> dict[str, float]:
    names = [name for name in names if name]
    if not names:
        return {}

    session = get_session()
    try:
        rows = session.query(Thuoc).filter(Thuoc.Ten.in_(names)).all()
        return {row.Ten: float(row.Gia or 0) for row in rows}
    finally:
        session.close()


_price_cache: dict[str, Optional[dict[str, float]]] = {"map": None}


def get_thuoc_price_map(names: list[str]) -> dict[str, float]:
    if _price_cache["map"] is None:
        session = get_session()
        try:
            rows = session.query(Thuoc.Ten, Thuoc.Gia).all()
            _price_cache["map"] = {t: float(g or 0) for t, g in rows}
        finally:
            session.close()
    return {n: _price_cache["map"].get(n, 0.0) for n in names if n}


def invalidate_price_cache() -> None:
    _price_cache["map"] = None
    _medicine_names_cache["names"] = None
