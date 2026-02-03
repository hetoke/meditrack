import ttkbootstrap as tb
from tkinter import messagebox
from datetime import date

from db import HoSo
from db_connect import get_session
from intellisense import AutocompleteEntry
from prescription import show_ho_so_detail_window

def fetch_records():
    session = get_session()
    records = session.query(HoSo).all()
    session.close()
    return [
        (
            int(t.HoSoID),
            t.Ten,
            int(t.NamSinh) if t.NamSinh is not None else None,
            t.DiaChi,
            t.DienThoai,
            t.TienCan,
        )
        for t in records
    ]

import unicodedata

def remove_accents(s):
    return ''.join(
        c for c in unicodedata.normalize('NFD', s)
        if unicodedata.category(c) != 'Mn'
    )

import re


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
    if not name_query and year_query is None:
        return []

    session = get_session()
    results = session.query(HoSo.Ten, HoSo.NamSinh).all()
    session.close()

    suggestions = []
    for name, year in results:
        if year_query is not None:
            if year is None or int(year) != year_query:
                continue
        if name_matches(name, name_query):
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
            name_query, year_query = parse_search_query(query)
            filtered_records["data"] = [
                r for r in records
                if (year_query is None or (r[2] is not None and int(r[2]) == year_query))
                and name_matches(r[1], name_query)
            ]
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
        year_value = year_entry.get().strip()
        if year_value and not year_value.isdigit():
            messagebox.showerror("Lỗi", "Năm sinh chỉ được nhập số.")
            return
        session = get_session()
        # use session.get to load the row by primary key
        h = session.get(HoSo, hoso_id)
        if h:
            h.Ten = name_entry.get().strip()
            h.NamSinh = int(year_value) if year_value.isdigit() else None
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

        if not name:
            messagebox.showerror("Lỗi", "Vui lòng nhập họ và tên.")
            return
        if not year or not year.isdigit():
            messagebox.showerror("Lỗi", "Vui lòng nhập năm sinh hợp lệ (chỉ số).")
            return

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


def clear_parents(widget, stop_at=None, levels=2):
    parent = widget
    for _ in range(levels - 1):
        if parent.master == stop_at or parent.master is None:
            break
        parent = parent.master
    for w in parent.winfo_children():
        w.destroy()
    return parent
