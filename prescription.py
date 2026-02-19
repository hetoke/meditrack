import ttkbootstrap as tb
import tkinter as tk
import tkinter.font as tkfont
from tkinter import messagebox
from datetime import date, datetime


from services.prescription_service import (
    safe_float,
    format_currency,
    format_ngaylap,
    calculate_total_from_donthuoc,
    fetch_prescription_summaries_by_hoso,
    fetch_prescription_detail_by_id,
    save_prescription,
    delete_prescription_by_id,
    fetch_thuoc_suggestions
)

from utils.tk_helpers import clear_parents
from intellisense import AutocompleteEntry
from ui.prescription.table import PrescriptionTable






def show_ho_so_detail_window(root, container, record, show_ho_so_window, show_primary_window):
    container = clear_parents(container, stop_at=root, levels=2)

    # record is (HoSoID, Ten, NamSinh, DiaChi, DienThoai, TienCan)
    hoso_id, name, year, address, phone, tiencan, _ = record

    # --- Sidebar ---
    sidebar = tb.Frame(container, padding=20)
    sidebar.pack(side="left", fill="y")

    tb.Label(sidebar, text=name, font=("Quicksand", 14, "bold")).pack(anchor="center", pady=(0, 5))
    tb.Label(sidebar, text=f"Năm sinh: {year}", anchor="w", justify="left").pack(fill="x", pady=2)
    tb.Label(sidebar, text=f"SĐT: {phone}", anchor="w", justify="left").pack(fill="x", pady=2)
    tb.Label(sidebar, text=f"Địa chỉ: {address}", wraplength=200, anchor="w", justify="left").pack(fill="x", pady=(5, 20))

    sidebar_total_label = tb.Label(
        sidebar,
        text=f"T: {format_currency(0)}",
        anchor="w",
        justify="left",
        font=("Quicksand", 14, "bold"),
    )
    sidebar_total_label.pack(fill="x", pady=5)

    sidebar_actions = tb.Frame(sidebar)
    sidebar_actions.pack(fill="x", pady=(10, 5))

    # --- Content ---
    content = tb.Frame(container, padding=20)
    content.pack(side="left", fill="both", expand=True)

    # ---- Tiền căn ----
    tiencan_box = tb.Labelframe(sidebar, text="Tiền căn", padding=10)
    tiencan_box.pack(fill="x", pady=(2, 4), expand=False)

    tiencan_text = tk.Text(tiencan_box, height=3, width=28, wrap="word")
    tiencan_text.pack(fill="x")
    if tiencan:
        tiencan_text.insert("1.0", tiencan)

    tiencan_text.config(state="disabled")

    # ============= PRESCRIPTIONS =============
    current_index = {"value": 0}
    summary_rows = fetch_prescription_summaries_by_hoso(hoso_id)
    prescription_ids = [row.DonThuocID for row in summary_rows]
    prescriptions = [None] * len(prescription_ids)

    # --- Navigation in sidebar ---
    sidebar_nav = tb.Frame(sidebar)
    sidebar_nav.pack(fill="x", pady=(10, 5))

    nav_row = tb.Frame(sidebar_nav)
    nav_row.pack(fill="x", pady=2)

    prev_btn = tb.Button(nav_row, text="Trước")
    prev_btn.pack(side="left", expand=True, fill="x", padx=(0, 2))

    nav_label = tb.Label(nav_row, text="")
    nav_label.pack(side="left", expand=True, fill="x")

    next_btn = tb.Button(nav_row, text="Sau")
    next_btn.pack(side="left", expand=True, fill="x", padx=(2, 0))

    date_label = tb.Label(sidebar_nav, text="")
    date_label.pack(fill="x", pady=2)

    base_font_size = tkfont.nametofont("TkDefaultFont").cget("size") + 2
    zoom_min = 0.5
    zoom_max = 1.5
    zoom_step = 0.1
    base_pad = 1
    base_row = base_font_size + 2

    table_font_family = "Quicksand"
    if table_font_family not in tkfont.families():
        table_font_family = tkfont.nametofont("TkDefaultFont").cget("family")
    font_cache = {}

    def build_font(size):
        f = font_cache.get(size)
        if f is None:
            f = tkfont.Font(family=table_font_family, size=size)
            font_cache[size] = f
        return f

    

    

    delete_btn = None

    # --- Navigation / CRUD functions ---
    def show_prescription(index):
        # Hide existing tables
        for t in prescriptions:
            if t:
                t.pack_forget()

        # Lazy build if not created yet
        if prescriptions[index] is None:
            prescription_id = prescription_ids[index]
            don = fetch_prescription_detail_by_id(prescription_id)
            prescriptions[index] = PrescriptionTable(content, don)

        t = prescriptions[index]
        t.pack(fill="both", expand=True)

        current_index["value"] = index
        nav_label.config(text=f"Đơn {index+1}/{len(prescriptions)}")

        if t.donthuoc and t.donthuoc.NgayLap:
            date_label.config(
                text=f"Ngày lập đơn thuốc: {format_ngaylap(t.donthuoc.NgayLap)}"
            )
        else:
            date_label.config(text="")

        total_value = calculate_total_from_donthuoc(t.donthuoc)
        sidebar_total_label.config(
            text=f"T: {format_currency(total_value)}"
        )

        prev_btn.config(state=("disabled" if index == 0 else "normal"))
        next_btn.config(state=("disabled" if index == len(prescriptions)-1 else "normal"))

    def next_prescription():
        if current_index["value"] < len(prescriptions) - 1:
            show_prescription(current_index["value"] + 1)

    def prev_prescription():
        if current_index["value"] > 0:
            show_prescription(current_index["value"] - 1)

    def collect_prescription_rows(entries):
        rows = []

        for row in entries:
            # row is a dict with key "entries"
            cells = row["entries"]

            values = []
            for e in cells:
                if hasattr(e, "get"):
                    values.append(e.get().strip())
                else:
                    values.append(str(e).strip())

            #print(values)
            if any(values):
                rows.append(values)

        return rows

    def add_prescription():
        t = PrescriptionTable(content)
        prescriptions.append(t)
        show_prescription(len(prescriptions) - 1)

    def duplicate_prescription():
        if not prescriptions:
            return

        src = prescriptions[current_index["value"]]
        rows = collect_prescription_rows(src.entries)

        chandoan = src.chandoan_text.get("1.0", "end").strip()
        rows = [[e for e in row] for row in rows]

        t = PrescriptionTable(
            content,
            seed_rows=rows,
            seed_chandoan=chandoan
        )
        t.dirty = True
        prescriptions.append(t)

        show_prescription(len(prescriptions) - 1)

    def delete_prescription(index):
        t = prescriptions[index]

        if t.dirty:
            if not messagebox.askyesno("Chưa lưu", "Đơn thuốc này có thay đổi chưa lưu. Xoá vẫn tiếp tục?"):
                return

        if t.donthuoc:
            delete_prescription_by_id(t.donthuoc.DonThuocID)

        t.frame.destroy()
        prescriptions.pop(index)

        if prescriptions:
            show_prescription(min(index, len(prescriptions) - 1))
        else:
            new_t = PrescriptionTable(content)
            prescriptions.append(new_t)
            show_prescription(0)

    

    def save_current_prescription():
        if not prescriptions:
            return

        try:
            t = prescriptions[current_index["value"]]
            rows = collect_prescription_rows(t.entries)


            don_obj, total_cost = save_prescription(
                hoso_id,
                t.donthuoc,
                t.chandoan_text.get("1.0", "end").strip(),
                entry_rows=rows,
            )
            t.donthuoc = don_obj
            t.dirty = False
        except ValueError as e:
            messagebox.showerror("Lỗi", str(e))
            return

        t.donthuoc = don_obj
        t.dirty = False

        if don_obj and don_obj.NgayLap:
            date_label.config(
                text=f"Ngày lập đơn thuốc: {format_ngaylap(don_obj.NgayLap)}"
            )

        sidebar_total_label.config(
            text=f"T: {format_currency(total_cost)}"
        )

        messagebox.showinfo("Thông báo", "Đã lưu đơn thuốc thành công!")

    if not prescription_ids:
        prescriptions = [PrescriptionTable(content)]
    else:
        prescriptions = [None] * len(prescription_ids)

    show_prescription(len(prescriptions) - 1)

    # --- Connect navigation buttons ---
    prev_btn.config(command=prev_prescription)
    next_btn.config(command=next_prescription)
    tb.Button(sidebar_actions, text="+ Thêm đơn thuốc", bootstyle="success",
              command=add_prescription).pack(fill="x", pady=2)
    tb.Button(sidebar_actions, text="⎘ Nhân bản đơn hiện tại", bootstyle="secondary",
              command=duplicate_prescription).pack(fill="x", pady=2)
    tb.Button(sidebar_actions, text="💾 Lưu đơn thuốc hiện tại", bootstyle="primary",
              command=save_current_prescription).pack(fill="x", pady=2)
    delete_btn = tb.Button(
        sidebar_actions,
        text="🗑 Xoá đơn thuốc hiện tại",
        bootstyle="danger",
        command=lambda: delete_prescription(current_index["value"]),
    )
    delete_btn.pack(fill="x", pady=2)

    # --- Back button ---
    def confirm_back():
        if prescriptions:
            current_prescription = prescriptions[current_index["value"]]
            if current_prescription.dirty:
                if not messagebox.askyesno("Chưa lưu", "Đơn thuốc hiện tại có thay đổi chưa lưu. Quay lại mà không lưu?"):
                    return
        show_ho_so_window(root, container, show_primary_window)

    tb.Button(
        container,
        text="⬅ Quay lại",
        bootstyle="secondary",
        command=confirm_back,
    ).pack(pady=20)
