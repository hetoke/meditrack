import ttkbootstrap as tb
import tkinter as tk
from tkinter import messagebox
from ttkbootstrap.tableview import Tableview
from db import HoSo, DonThuoc, ChiDinh, Thuoc
from db_connect import get_session 
from datetime import date
from intellisense import AutocompleteEntry

def fetch_records():
    session = get_session()
    records = session.query(HoSo).all()
    session.close()
    return [(int(t.HoSoID), t.Ten, int(t.NamSinh), t.DiaChi, t.DienThoai, t.TienCan) for t in records]

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

import unicodedata

def remove_accents(s):
    return ''.join(
        c for c in unicodedata.normalize('NFD', s)
        if unicodedata.category(c) != 'Mn'
    )

import re

def safe_float(value):
    try:
        return float(value)
    except Exception:
        return 0.0

def format_currency(value):
    return f"{value:,.0f} đ"

def fetch_patient_suggestions(query: str):
    query_norm = remove_accents(query.strip().lower())
    if not query_norm:
        return []

    session = get_session()
    results = session.query(HoSo.Ten).all()
    session.close()

    suggestions = []
    pattern = re.compile(rf"^{re.escape(query_norm)}")  # matches start of string
    for (name,) in results:
        name_norm = remove_accents(name.strip().lower())
        if pattern.match(name_norm):
            suggestions.append(name)
    return suggestions

records = fetch_records()

ITEMS_PER_PAGE = 3
current_page = {"value": 1}

# -------------------------
# show_ho_so_window (small fixes)
# -------------------------
def show_ho_so_window(root, container, show_primary_window):
    container = clear_parents(container, stop_at=root, levels=2)

    tb.Label(container, text="Hồ sơ bệnh nhân", font=("Quicksand", 16, "bold")).pack(pady=10)

    search_frame = tb.Frame(container)
    search_frame.pack(fill="x", padx=20, pady=10)

    tb.Label(search_frame, text="🔍").pack(side="left", padx=(0,5))


    search_entry = AutocompleteEntry(search_frame, fetch_suggestions=fetch_patient_suggestions)
    search_entry.pack(side="left", fill="x", expand=True)

    tb.Button(search_frame, text="×", command=lambda: search_entry.delete(0, "end")).pack(side="left", padx=5)
    tb.Button(
        search_frame,
        text="+ Thêm hồ sơ",
        bootstyle="success",
        command=lambda: show_add_ho_so_window(root, container, show_primary_window)
    ).pack(side="right", padx=5)

    record_frame = tb.Frame(container, bootstyle="light", padding=10)
    record_frame.pack(fill="both", expand=True, padx=20, pady=10)

    pagination_frame = tb.Frame(container)
    pagination_frame.pack(pady=10)

    prev_btn = tb.Button(
        pagination_frame, text="← Previous",
        command=lambda: change_page(root, -1, record_frame, page_label, show_primary_window, filtered_records["data"])
    )
    prev_btn.pack(side="left", padx=10)

    page_label = tb.Label(pagination_frame, text="")
    page_label.pack(side="left")

    next_btn = tb.Button(
        pagination_frame, text="Next →",
        command=lambda: change_page(root, 1, record_frame, page_label, show_primary_window, filtered_records["data"])
    )
    next_btn.pack(side="left", padx=10)

    tb.Button(container, text="⬅ Quay lại", bootstyle="secondary",
              command=lambda: show_primary_window(root, container)).pack(pady=20)

    # Live search filter
    filtered_records = {"data": records.copy()}

    def on_search_change(*args):
        query = search_entry.get().strip()
        if query:
            filtered_records["data"] = [r for r in records if query.lower() in r[1].lower()]
        else:
            filtered_records["data"] = records.copy()
        current_page["value"] = 1
        render_record_list(
            root, record_frame, page_label, show_primary_window,
            record_list=filtered_records["data"]
        )

    search_entry.var.trace_add("write", on_search_change)

    # Initial render
    render_record_list(root, record_frame, page_label, show_primary_window, record_list=filtered_records["data"])



# -------------------------
# render_record_list (accept show_primary_window)
# -------------------------
def render_record_list(root, container, page_label, show_primary_window, record_list=None):
    record_list = record_list or records
    for w in container.winfo_children():
        w.destroy()

    start = (current_page["value"] - 1) * ITEMS_PER_PAGE
    end = start + ITEMS_PER_PAGE
    page_items = record_list[start:end]

    for record in page_items:
        hoso_id, name, year, address, phone, _ = record

        card = tb.Frame(container, padding=10)
        card.pack(fill="x", pady=5)

        tb.Label(card, text=f"{name} - {year}", font=("Quicksand", 12, "bold")).pack(anchor="w")
        tb.Label(card, text=f"{address}").pack(anchor="w")
        tb.Label(card, text=f"{phone}").pack(anchor="w")

        # Make card clickable
        card.bind("<Button-1>", lambda e, r=record: show_ho_so_detail_window(
            root, container, r, show_ho_so_window, show_primary_window
        ))
        for child in card.winfo_children():
            child.bind("<Button-1>", lambda e, r=record: show_ho_so_detail_window(
                root, container, r, show_ho_so_window, show_primary_window
            ))

        btn_frame = tb.Frame(card)
        btn_frame.pack(anchor="e")

        tb.Button(
            btn_frame, text="✏ Sửa", bootstyle="info-outline",
            command=lambda rid=hoso_id, r=record: show_edit_ho_so_window(root, container, show_primary_window, rid, r)
        ).pack(side="left", padx=5)

        tb.Button(
            btn_frame, text="🗑 Xoá", bootstyle="danger-outline",
            command=lambda rid=hoso_id: delete_ho_so(root, container, show_primary_window, page_label, rid)
        ).pack(side="left")

    max_page = max(1, (len(record_list) + ITEMS_PER_PAGE - 1) // ITEMS_PER_PAGE)
    page_label.config(text=f"Page {current_page['value']} / {max_page}")

# -------------------------
# show_edit_ho_so_window (persist edits to DB)
# -------------------------
def show_edit_ho_so_window(root, container, show_primary_window, hoso_id, record):
    """Edit a HoSo record by HoSoID (persists to DB)."""
    # record may be outdated; we still use it for initial fill
    _, name, year, address, phone, tiencan = record

    for w in container.winfo_children():
        w.destroy()

    tb.Label(container, text="Sửa hồ sơ", font=("Quicksand", 16, "bold")).pack(pady=10)

    # Entries
    tb.Label(container, text="Tên:").pack(anchor="w", padx=10)
    name_entry = tb.Entry(container)
    name_entry.insert(0, name)
    name_entry.pack(fill="x", padx=10, pady=5)

    tb.Label(container, text="Năm sinh:").pack(anchor="w", padx=10)
    year_entry = tb.Entry(container)
    year_entry.insert(0, year)
    year_entry.pack(fill="x", padx=10, pady=5)

    tb.Label(container, text="Địa chỉ:").pack(anchor="w", padx=10)
    address_entry = tb.Entry(container)
    address_entry.insert(0, address)
    address_entry.pack(fill="x", padx=10, pady=5)

    tb.Label(container, text="SĐT:").pack(anchor="w", padx=10)
    phone_entry = tb.Entry(container)
    phone_entry.insert(0, phone)
    phone_entry.pack(fill="x", padx=10, pady=5)

    tb.Label(container, text="Tiền căn").pack(anchor="w", padx=10) 
    tiencan_entry = tb.Text(container, width=40, height=5) 
    tiencan_entry.insert("1.0", tiencan)
    tiencan_entry.pack(fill="x", padx=10, pady=5)

    def save_changes():
        session = get_session()
        # use session.get to load the row by primary key
        h = session.get(HoSo, hoso_id)
        if h:
            h.Ten = name_entry.get().strip()
            h.NamSinh = int(year_entry.get()) if year_entry.get().strip().isdigit() else None
            h.DiaChi = address_entry.get().strip()
            h.DienThoai = phone_entry.get().strip()
            h.TienCan = tiencan_entry.get("1.0", "end").strip()
            session.commit()
        session.close()

        # refresh in-memory list from DB and go back to list view
        global records
        records = fetch_records()
        show_ho_so_window(root, container, show_primary_window)

    tb.Button(container, text="💾 Lưu", bootstyle="success-outline", command=save_changes).pack(pady=10)
    tb.Button(container, text="↩ Quay lại", bootstyle="secondary-outline",
              command=lambda: show_ho_so_window(root, container, show_primary_window)).pack()


# -------------------------
# delete_ho_so (persist delete to DB)
# -------------------------
def delete_ho_so(root, container, show_primary_window, page_label, hoso_id):
    if not messagebox.askyesno("Xác nhận", "Bạn có chắc chắn muốn xoá hồ sơ này?"):
        return
    session = get_session()
    h = session.get(HoSo, hoso_id)
    if h:
        session.delete(h)
        session.commit()
    session.close()

    # refresh records from DB and re-render list
    global records
    records = fetch_records()
    show_ho_so_window(root, container, show_primary_window)


# -------------------------
# show_add_ho_so_window (refresh records after commit)
# -------------------------
def show_add_ho_so_window(root, page_container, show_primary_window):
    for w in page_container.winfo_children():
        w.destroy()

    form = tb.Frame(page_container, padding=20)
    form.pack(pady=50)

    # ... (fields same as you already have)
    tb.Label(form, text="Họ và tên bệnh nhân").pack(anchor="w")
    name_entry = tb.Entry(form, width=40)
    name_entry.pack(pady=5)
    # (year, address, phone, tiencan as in your code...)
    # Năm sinh 
    tb.Label(form, text="Năm sinh").pack(anchor="w") 
    year_entry = tb.Entry(form, width=40) 
    year_entry.pack(pady=5) 

    # Địa chỉ 
    tb.Label(form, text="Địa chỉ").pack(anchor="w") 
    address_entry = tb.Entry(form, width=40) 
    address_entry.pack(pady=5) 

    # Số điện thoại 
    tb.Label(form, text="Số điện thoại").pack(anchor="w") 
    phone_entry = tb.Entry(form, width=40) 
    phone_entry.pack(pady=5) 

    # Tiền căn (multiline) 
    tb.Label(form, text="Tiền căn").pack(anchor="w") 
    tiencan_entry = tb.Text(form, width=40, height=5) 
    tiencan_entry.pack(pady=5)

    def add_ho_so():
        name = name_entry.get().strip()
        year = year_entry.get().strip()
        address = address_entry.get().strip()
        phone = phone_entry.get().strip()
        tiencan = tiencan_entry.get("1.0", "end").strip()

        if name:
            session = get_session()
            new_hoso = HoSo(
                Ten=name,
                NamSinh=int(year) if year.isdigit() else None,
                DiaChi=address,
                DienThoai=phone,
                TienCan=tiencan,
                NgayMoHoSo=date.today()
            )
            session.add(new_hoso)
            session.commit()
            session.close()

            # refresh in-memory list and go back to list view
            global records
            records = fetch_records()
            show_ho_so_window(root, page_container, show_primary_window)

    tb.Button(form, text="Thêm hồ sơ", bootstyle="success", command=add_ho_so).pack(pady=10)

    tb.Button(page_container, text="⬅ Quay lại", bootstyle="secondary",
              command=lambda: show_ho_so_window(root, page_container, show_primary_window)).pack(pady=20)





def change_page(root, direction, container, page_label, show_primary_window, record_list):
    max_page = max(1, (len(record_list) + ITEMS_PER_PAGE - 1) // ITEMS_PER_PAGE)
    current_page["value"] = max(1, min(max_page, current_page["value"] + direction))
    render_record_list(root, container, page_label, show_primary_window, record_list=record_list)


def show_ho_so_detail_window(root, container, record, show_ho_so_window, show_primary_window):
    container = clear_parents(container, stop_at=root, levels=2)


    # <-- FIX: record is (HoSoID, Ten, NamSinh, DiaChi, DienThoai, TienCan)
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
        font=("Quicksand", 14, "bold")  # font family, size, style
    )
    sidebar_total_label.pack(fill="x", pady=5)

    # --- Content ---
    content = tb.Frame(container, padding=20)
    content.pack(side="left", fill="both", expand=True)

    # ---- Tiền căn ----
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
    donthuoc_list = session.query(DonThuoc).filter(DonThuoc.HoSoID == hoso_id).order_by(DonThuoc.NgayLap).all()

    # --- Navigation bar first so functions can access it ---
    nav_frame = tb.Frame(content)
    nav_frame.pack(fill="x", pady=5)

    prev_btn = tb.Button(nav_frame, text="⬅️ Trước")
    prev_btn.pack(side="left")

    nav_label = tb.Label(nav_frame, text="")
    nav_label.pack(side="left", padx=10)

    next_btn = tb.Button(nav_frame, text="➡️ Sau")
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
            "total_label": None,
        })

        # ---- Chuẩn đoán ----
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
        for c, text in enumerate(columns + ["Xóa"]):
            tb.Label(grid_frame, text=text, anchor="center",
                     bootstyle="secondary", width=(col_widths[c] if c < len(columns) else 6)
                     ).grid(row=0, column=c, sticky="nsew", padx=1, pady=1)

        entries = []

        def add_row(row_values=None):
            row_index = len(entries) + 1
            row_entries = []
            vals = row_values if row_values else ("",) * len(columns)

            for c in range(len(columns)):
                v = vals[c] if c < len(vals) else ""
                if c == 0:
                    # This works but would be lethal if there is too much thuoc
                    all_meds = lambda query: [t.Ten for t in session.query(Thuoc).filter(Thuoc.Ten.ilike(f"{query}%")).all()]
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

            btn = tb.Button(grid_frame, text="❌", bootstyle="danger", command=delete_row)
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

        tb.Button(frame, text="➕ Thêm dòng", bootstyle="success",
                  command=lambda: add_row()).pack(anchor="e", pady=5)

        total_value = calculate_total_from_donthuoc(donthuoc_obj)
        total_label = tb.Label(frame, text=f"Tổng tiền: {format_currency(total_value)}", font=("Quicksand", 12, "bold"))
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
            don_obj = DonThuoc(HoSoID=hoso_id, NgayLap=date.today())
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
                    messagebox.showerror("Lỗi", f"Thuốc '{name}' không tồn tại!")
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
        p["donthuoc"] = don_obj
        sidebar_total_label.config(text=f"Tổng tiền: {format_currency(total_cost)}")
        if p["total_label"]:
            p["total_label"].config(text=f"Tổng tiền: {format_currency(total_cost)}")
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
    tb.Button(nav_frame, text="➕ Thêm đơn thuốc", bootstyle="success", command=add_prescription).pack(side="right", padx=5)
    tb.Button(nav_frame, text="💾 Lưu đơn thuốc hiện tại", bootstyle="primary", command=save_current_prescription).pack(side="right", padx=5)
    if len(prescriptions) > 1:
        tb.Button(nav_frame, text="🗑 Xóa đơn thuốc hiện tại", bootstyle="danger",
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
