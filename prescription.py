import ttkbootstrap as tb
import tkinter as tk
from tkinter import messagebox
from datetime import date, datetime

from sqlalchemy.orm import selectinload

from db import DonThuoc, ChiDinh, Thuoc
from db_connect import get_session
from intellisense import AutocompleteEntry


def fetch_prescriptions(hoso_id):
    session = get_session()
    donthuocs = (
        session.query(DonThuoc)
        .filter(DonThuoc.HoSoID == hoso_id)
        .order_by(DonThuoc.NgayLap)
        .all()
    )
    session.close()

    # Return list of tuples (DonThuocID, NgayLap, MoTa, TienToa)
    return [
        (
            int(d.DonThuocID),
            d.NgayLap,
            d.MoTa,
            float(d.TienToa) if d.TienToa else 0.0,
            [
                (
                    chi.TenThuoc,
                    chi.SangTruocAn,
                    chi.SangSauAn,
                    chi.TruaTruocAn,
                    chi.TruaSauAn,
                    chi.ChieuTruocAn,
                    chi.ChieuSauAn,
                    chi.Toi,
                )
                for chi in d.chidinh_list
            ],
        )
        for d in donthuocs
    ]


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


def show_ho_so_detail_window(root, container, record, show_ho_so_window, show_primary_window):
    container = clear_parents(container, stop_at=root, levels=2)

    # record is (HoSoID, Ten, NamSinh, DiaChi, DienThoai, TienCan)
    hoso_id, name, year, address, phone, tiencan = record

    # --- Sidebar ---
    sidebar = tb.Frame(container, padding=20)
    sidebar.pack(side="left", fill="y")

    tb.Label(sidebar, text=name, font=("Quicksand", 14, "bold")).pack(anchor="center", pady=(0, 5))
    tb.Label(sidebar, text=f"Năm sinh: {year}", anchor="w", justify="left").pack(fill="x", pady=2)
    tb.Label(sidebar, text=f"SĐT: {phone}", anchor="w", justify="left").pack(fill="x", pady=2)
    tb.Label(sidebar, text=f"Địa chỉ: {address}", wraplength=200, anchor="w", justify="left").pack(fill="x", pady=(5, 20))

    sidebar_total_label = tb.Label(
        sidebar,
        text=f"Tổng tiền: {format_currency(0)}",
        anchor="w",
        justify="left",
        font=("Quicksand", 14, "bold"),
    )
    sidebar_total_label.pack(fill="x", pady=5)

    # --- Content ---
    content = tb.Frame(container, padding=20)
    content.pack(side="left", fill="both", expand=True)

    # ---- Tiá»n cÄƒn ----
    tiencan_box = tb.Labelframe(content, text="Tiền căn", padding=10)
    tiencan_box.pack(fill="x", pady=5)

    tiencan_text = tk.Text(tiencan_box, height=3, wrap="word")
    tiencan_text.pack(fill="x")
    if tiencan:
        tiencan_text.insert("1.0", tiencan)

    tiencan_text.config(state="disabled")

    # ============= PRESCRIPTIONS =============
    prescriptions = []
    current_index = {"value": 0}
    session = get_session()
    donthuoc_list = (
        session.query(DonThuoc)
        .options(selectinload(DonThuoc.chidinh_list).selectinload(ChiDinh.thuoc))
        .filter(DonThuoc.HoSoID == hoso_id)
        .order_by(DonThuoc.NgayLap)
        .all()
    )
    session.expunge_all()
    session.close()

    # --- Navigation bar first so functions can access it ---
    nav_frame = tb.Frame(content)
    nav_frame.pack(fill="x", pady=5)

    prev_btn = tb.Button(nav_frame, text="Trước")
    prev_btn.pack(side="left")

    nav_label = tb.Label(nav_frame, text="")
    nav_label.pack(side="left", padx=10)

    date_label = tb.Label(nav_frame, text="")
    date_label.pack(side="left", padx=10)

    next_btn = tb.Button(nav_frame, text="Sau")
    next_btn.pack(side="left")

    # --- Helper: Build single prescription UI ---
    def calculate_total_from_donthuoc(donthuoc_obj):
        total = 0.0
        if not donthuoc_obj:
            return total
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

    def build_prescription(donthuoc_obj=None):
        frame = tb.Frame(content, padding=10)
        prescriptions.append({
            "frame": frame,
            "donthuoc": donthuoc_obj,
            "entries": [],
            "chandoan_text": None,
        })

        # ---- Chuáº©n Ä‘oÃ¡n ----
        chandoan_box = tb.Labelframe(frame, text="Chuẩn đoán", padding=10)
        chandoan_box.pack(fill="x", pady=5)
        chandoan_text = tk.Text(chandoan_box, height=3, wrap="word")
        chandoan_text.pack(fill="x")
        if donthuoc_obj:
            chandoan_text.insert("1.0", donthuoc_obj.MoTa)

        # ---- Prescription Table ----
        columns = ["Thuốc", "Sáng trước ăn", "Sáng sau ăn", "Trưa trước ăn",
                    "Trưa sau ăn", "Chiều trước ăn", "Chiều sau ăn", "Tối"]
        sau_an_indices = {2, 4, 6}
        col_widths = [22, 12, 12, 12, 12, 12, 12, 12]

        table_outer = tb.Frame(frame)
        table_outer.pack(fill="both", expand=True, padx=20, pady=10)

        canvas = tk.Canvas(table_outer)
        vsb = tb.Scrollbar(table_outer, orient="vertical", command=canvas.yview)
        canvas.configure(yscrollcommand=vsb.set)
        vsb.pack(side="right", fill="y")
        canvas.pack(side="left", fill="both", expand=True)

        grid_frame = tb.Frame(canvas)
        canvas.create_window((0, 0), window=grid_frame, anchor="nw")

        # Header row
        # for c, text in enumerate(columns + ["Xoá"]):
        #     tb.Label(
        #         grid_frame,
        #         text=text,
        #         anchor="center",
        #         bootstyle="secondary",
        #         width=(col_widths[c] if c < len(columns) else 6),
        #     ).grid(row=0, column=c, sticky="nsew", padx=1, pady=1)

        entries = []

        def add_row(row_values=None):
            row_index = len(entries) + 1
            row_entries = []
            vals = row_values if row_values else ("",) * len(columns)

            for c in range(len(columns)):
                v = vals[c] if c < len(vals) else ""
                if c == 0:
                    # This works but would be lethal if there is too much thuoc
                    all_meds = lambda query: [
                        t.Ten for t in session.query(Thuoc).filter(Thuoc.Ten.ilike(f"{query}%")).all()
                    ]
                    e = AutocompleteEntry(grid_frame, fetch_suggestions=all_meds, width=col_widths[c])
                else:
                    e = tk.Entry(grid_frame, width=col_widths[c])
                e.insert(0, v)
                if c in sau_an_indices:
                    e.config(bg="#FFC107")
                e.grid(row=row_index, column=c, sticky="nsew", padx=1, pady=1)
                row_entries.append(e)

            entries.append(row_entries)

            def delete_row():
                for e in row_entries + [btn]:
                    e.destroy()
                if row_entries in entries:
                    entries.remove(row_entries)
                grid_frame.update_idletasks()
                canvas.config(scrollregion=canvas.bbox("all"))

            btn = tb.Button(grid_frame, text="X", bootstyle="danger", command=delete_row)
            btn.grid(row=row_index, column=len(columns), sticky="nsew", padx=1, pady=1)

            grid_frame.update_idletasks()
            canvas.config(scrollregion=canvas.bbox("all"))

        # Populate rows from DB
        if donthuoc_obj and donthuoc_obj.chidinh_list:
            for chi in donthuoc_obj.chidinh_list:
                name = chi.thuoc.Ten if chi.thuoc else "(Thuốc không tồn tại)"
                add_row([
                    name,
                    chi.SangTruocAn or "",
                    chi.SangSauAn or "",
                    chi.TruaTruocAn or "",
                    chi.TruaSauAn or "",
                    chi.ChieuTruocAn or "",
                    chi.ChieuSauAn or "",
                    chi.Toi or "",
                ])
        else:
            add_row()

        tb.Button(frame, text="Thêm dòng", bootstyle="success",
                  command=lambda: add_row()).pack(anchor="e", pady=5)

        prescriptions[-1]["chandoan_text"] = chandoan_text
        prescriptions[-1]["entries"] = entries

        return frame

    # --- Navigation / CRUD functions ---
    def show_prescription(index):
        for p in prescriptions:
            p["frame"].pack_forget()
        prescriptions[index]["frame"].pack(fill="both", expand=True)
        current_index["value"] = index
        nav_label.config(text=f"Đơn {index+1}/{len(prescriptions)}")
        don_obj = prescriptions[index]["donthuoc"]
        if don_obj and don_obj.NgayLap:
            date_text = format_ngaylap(don_obj.NgayLap)
            date_label.config(text=f"Ngày lập đơn thuốc: {date_text}")
        else:
            date_label.config(text="")
        total_value = calculate_total_from_donthuoc(prescriptions[index]["donthuoc"])
        sidebar_total_label.config(text=f"Tổng tiền: {format_currency(total_value)}")
        prev_btn.config(state=("disabled" if index == 0 else "normal"))
        next_btn.config(state=("disabled" if index == len(prescriptions)-1 else "normal"))

    def next_prescription():
        if current_index["value"] < len(prescriptions) - 1:
            show_prescription(current_index["value"] + 1)

    def prev_prescription():
        if current_index["value"] > 0:
            show_prescription(current_index["value"] - 1)

    def add_prescription():
        build_prescription()
        show_prescription(len(prescriptions) - 1)

    def delete_prescription(index):
        if not prescriptions or index < 0 or index >= len(prescriptions):
            return
        p = prescriptions[index]
        don_obj = p.get("donthuoc")
        if don_obj:
            session_local = get_session()
            don_obj = session_local.get(DonThuoc, don_obj.DonThuocID)
            if don_obj:
                for chi in list(don_obj.chidinh_list):
                    session_local.delete(chi)
                session_local.delete(don_obj)
                session_local.commit()
            session_local.close()
        p["frame"].destroy()
        prescriptions.pop(index)
        if prescriptions:
            show_prescription(min(index, len(prescriptions)-1))
        else:
            build_prescription()
            show_prescription(0)

    def save_current_prescription():
        session_local = get_session()
        p = prescriptions[current_index["value"]]
        don_obj = p["donthuoc"]
        if don_obj is None:
            don_obj = DonThuoc(HoSoID=hoso_id, NgayLap=datetime.now())
        don_obj.MoTa = p["chandoan_text"].get("1.0", "end").strip()
        don_obj = session_local.merge(don_obj)
        session_local.commit()

        # Clear old ChiDinh
        for chi in list(don_obj.chidinh_list):
            session_local.delete(chi)
        session_local.commit()

        total_cost = 0.0
        # Save new ChiDinh
        for row in p["entries"]:
            if any(e.get() for e in row):
                name = row[0].get().strip()
                thuoc_obj = session_local.query(Thuoc).filter(Thuoc.Ten == name).first()
                if not thuoc_obj:
                    messagebox.showerror("Lỗi", f"Thuốc '{name}' không tồn tại")
                    return
                price = float(thuoc_obj.Gia or 0)
                dose = (
                    safe_float(row[1].get() or 0)
                    + safe_float(row[2].get() or 0)
                    + safe_float(row[3].get() or 0)
                    + safe_float(row[4].get() or 0)
                    + safe_float(row[5].get() or 0)
                    + safe_float(row[6].get() or 0)
                    + safe_float(row[7].get() or 0)
                )
                total_cost += dose * price
                chi = ChiDinh(
                    DonThuocID=don_obj.DonThuocID,
                    ThuocID=thuoc_obj.ThuocID,
                    SangTruocAn=float(row[1].get() or 0),
                    SangSauAn=float(row[2].get() or 0),
                    TruaTruocAn=float(row[3].get() or 0),
                    TruaSauAn=float(row[4].get() or 0),
                    ChieuTruocAn=float(row[5].get() or 0),
                    ChieuSauAn=float(row[6].get() or 0),
                    Toi=float(row[7].get() or 0),
                )
                session_local.add(chi)
        don_obj.TienToa = total_cost
        session_local.commit()
        don_obj = session_local.get(
            DonThuoc,
            don_obj.DonThuocID,
            options=[selectinload(DonThuoc.chidinh_list).selectinload(ChiDinh.thuoc)],
        )
        p["donthuoc"] = don_obj
        if don_obj and don_obj.NgayLap:
            date_text = format_ngaylap(don_obj.NgayLap)
            date_label.config(text=f"Ngày lập đơn thuốc: {date_text}")
        else:
            date_label.config(text="")
        sidebar_total_label.config(text=f"Tổng tiền: {format_currency(total_cost)}")
        session_local.close()
        messagebox.showinfo("Thông báo", "Đã lưu đơn thuốc thành công!")

    # --- Build prescriptions from DB ---
    for don in donthuoc_list:
        build_prescription(don)
    if not prescriptions:
        build_prescription()
    show_prescription(0)

    # --- Connect navigation buttons ---
    prev_btn.config(command=prev_prescription)
    next_btn.config(command=next_prescription)
    tb.Button(nav_frame, text="+ Thêm đơn thuốc", bootstyle="success", command=add_prescription).pack(side="right", padx=5)
    tb.Button(nav_frame, text="💾 Lưu đơn thuốc hiện tại", bootstyle="primary", command=save_current_prescription).pack(side="right", padx=5)
    if len(prescriptions) > 1:
        tb.Button(nav_frame, text="🗑 Xoá đơn thuốc hiện tại", bootstyle="danger",
                  command=lambda idx=current_index["value"]: delete_prescription(idx)).pack(side="right", padx=5)

    # --- Back button ---
    tb.Button(
        container,
        text="⬅ Quay lại",
        bootstyle="secondary",
        command=lambda: show_ho_so_window(root, container, show_primary_window),
    ).pack(pady=20)


def clear_parents(widget, stop_at=None, levels=2):
    parent = widget
    for _ in range(levels - 1):
        if parent.master == stop_at or parent.master is None:
            break
        parent = parent.master
    for w in parent.winfo_children():
        w.destroy()
    return parent
