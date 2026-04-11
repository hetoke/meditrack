import ttkbootstrap as tb
import tkinter as tk
from tkinter import messagebox

from services.prescription_service import (
    delete_prescription_by_id,
    fetch_prescription_detail_by_id,
    fetch_prescription_summaries_by_hoso,
    fetch_thuoc_price_map,
    save_prescription,
)
from ui.prescription.table import PrescriptionTable
from utils.formatter import format_currency, format_ngaylap
from utils.tk_helpers import clear_parents


def collect_prescription_rows(entries):
    rows = []
    for row in entries:
        values = []
        for entry in row["entries"]:
            if hasattr(entry, "get"):
                values.append(entry.get().strip())
            else:
                values.append(str(entry).strip())

        if any(values):
            rows.append({
                "entries": values,
                "excluded": row.get("exclude_from_total", False),
            })
    return rows


def append_to_newest_prescription(prescriptions, current_index):
    if not prescriptions:
        return

    current_prescription = prescriptions[current_index["value"]]
    newest_prescription = prescriptions[-1]

    existing_meds = set()
    for row in newest_prescription.entries:
        med_name = row["entries"][0].get().strip()
        if med_name:
            existing_meds.add(med_name)

    rows_to_add = []
    for row in current_prescription.entries:
        med_name = row["entries"][0].get().strip()
        if med_name and med_name not in existing_meds:
            rows_to_add.append({
                "entries": [e.get().strip() for e in row["entries"]],
                "excluded": row.get("exclude_from_total", False),
            })
            existing_meds.add(med_name)

    if not rows_to_add:
        messagebox.showinfo(
            "Thông báo",
            "Không có thuốc mới để thêm (có thể đã tồn tại trong đơn mới nhất)!",
        )
        return

    for values in rows_to_add:
        newest_prescription.add_row(values)

    newest_prescription._mark_dirty()
    canvas = newest_prescription.grid_frame.master
    canvas.update_idletasks()
    canvas.yview_moveto(1.0)
    newest_prescription.entries[-1]["entries"][0].focus_set()

    messagebox.showinfo("Thông báo", f"Đã thêm {len(rows_to_add)} thuốc vào đơn mới nhất.")


def show_ho_so_detail_window(root, container, record, show_ho_so_window, show_primary_window):
    container = clear_parents(container, stop_at=root, levels=2)

    hoso_id, name, year, address, phone, tiencan, _ = record

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

    content = tb.Frame(container, padding=20)
    content.pack(side="left", fill="both", expand=True)

    tiencan_box = tb.Labelframe(sidebar, text="Tiền căn", padding=10)
    tiencan_box.pack(fill="x", pady=(2, 4), expand=False)

    tiencan_text = tk.Text(tiencan_box, height=3, width=28, wrap="word")
    tiencan_text.pack(fill="x")
    if tiencan:
        tiencan_text.insert("1.0", tiencan)
    tiencan_text.config(state="disabled")

    current_index = {"value": 0}
    summary_rows = fetch_prescription_summaries_by_hoso(hoso_id)
    prescription_ids = [row.DonThuocID for row in summary_rows]
    prescriptions = [None] * len(prescription_ids)

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

    def update_sidebar_total(table):
        if not table:
            sidebar_total_label.config(text=f"T: {format_currency(0)}")
            return

        medicine_names = [row["entries"][0].get().strip() for row in table.entries]
        total_value = table.get_total(fetch_thuoc_price_map(medicine_names))
        sidebar_total_label.config(text=f"T: {format_currency(total_value)}")

    def show_prescription(index):
        for table in prescriptions:
            if table:
                table.pack_forget()

        if prescriptions[index] is None:
            don = fetch_prescription_detail_by_id(prescription_ids[index])
            prescriptions[index] = PrescriptionTable(content, don)
            prescriptions[index].on_change = lambda idx=index: update_sidebar_total(prescriptions[idx])

        table = prescriptions[index]
        table.pack(fill="both", expand=True)

        current_index["value"] = index
        nav_label.config(text=f"Đơn {index + 1}/{len(prescriptions)}")

        if table.donthuoc and table.donthuoc.NgayLap:
            date_label.config(text=f"Ngày lập đơn thuốc: {format_ngaylap(table.donthuoc.NgayLap)}")
        else:
            date_label.config(text="")

        update_sidebar_total(table)

        prev_btn.config(state=("disabled" if index == 0 else "normal"))
        next_btn.config(state=("disabled" if index == len(prescriptions) - 1 else "normal"))

    def next_prescription():
        if current_index["value"] < len(prescriptions) - 1:
            show_prescription(current_index["value"] + 1)

    def prev_prescription():
        if current_index["value"] > 0:
            show_prescription(current_index["value"] - 1)

    def add_prescription():
        table = PrescriptionTable(content)
        table.on_change = lambda: update_sidebar_total(table)
        prescriptions.append(table)
        show_prescription(len(prescriptions) - 1)

    def duplicate_prescription():
        if not prescriptions:
            return

        source = prescriptions[current_index["value"]]
        rows = collect_prescription_rows(source.entries)
        chandoan = source.chandoan_text.get("1.0", "end").strip()

        table = PrescriptionTable(content, seed_rows=rows, seed_chandoan=chandoan)
        table.on_change = lambda: update_sidebar_total(table)
        table.dirty = True
        prescriptions.append(table)
        show_prescription(len(prescriptions) - 1)

    def delete_prescription(index):
        table = prescriptions[index]

        if table.dirty and not messagebox.askyesno("Chưa lưu", "Đơn thuốc này có thay đổi chưa lưu. Xoá vẫn tiếp tục?"):
            return

        if table.donthuoc:
            delete_prescription_by_id(table.donthuoc.DonThuocID)

        table.frame.destroy()
        prescriptions.pop(index)

        if prescriptions:
            show_prescription(min(index, len(prescriptions) - 1))
        else:
            new_table = PrescriptionTable(content)
            new_table.on_change = lambda: update_sidebar_total(new_table)
            prescriptions.append(new_table)
            show_prescription(0)

    def save_current_prescription():
        if not prescriptions:
            return

        try:
            table = prescriptions[current_index["value"]]
            rows = collect_prescription_rows(table.entries)
            don_obj, _total_cost = save_prescription(
                hoso_id,
                table.donthuoc,
                table.chandoan_text.get("1.0", "end").strip(),
                entry_rows=rows,
            )
            table.donthuoc = don_obj
            table.dirty = False
        except ValueError as e:
            messagebox.showerror("Lỗi", str(e))
            return

        if don_obj and don_obj.NgayLap:
            date_label.config(text=f"Ngày lập đơn thuốc: {format_ngaylap(don_obj.NgayLap)}")

        update_sidebar_total(table)
        messagebox.showinfo("Thông báo", "Đã lưu đơn thuốc thành công!")

    if not prescription_ids:
        initial_table = PrescriptionTable(content)
        initial_table.on_change = lambda: update_sidebar_total(initial_table)
        prescriptions = [initial_table]
    else:
        prescriptions = [None] * len(prescription_ids)

    show_prescription(len(prescriptions) - 1)

    prev_btn.config(command=prev_prescription)
    next_btn.config(command=next_prescription)

    tb.Button(sidebar_actions, text="+ Thêm đơn thuốc", bootstyle="success", command=add_prescription).pack(fill="x", pady=2)
    tb.Button(
        sidebar_actions,
        text="⤓ Ghép thuốc vào đơn mới nhất",
        bootstyle="info",
        command=lambda: append_to_newest_prescription(prescriptions, current_index),
    ).pack(fill="x", pady=2)
    tb.Button(sidebar_actions, text="⎘ Nhân bản đơn hiện tại", bootstyle="secondary", command=duplicate_prescription).pack(fill="x", pady=2)
    tb.Button(sidebar_actions, text="💾 Lưu đơn thuốc hiện tại", bootstyle="primary", command=save_current_prescription).pack(fill="x", pady=2)
    tb.Button(
        sidebar_actions,
        text="🗑 Xoá đơn thuốc hiện tại",
        bootstyle="danger",
        command=lambda: delete_prescription(current_index["value"]),
    ).pack(fill="x", pady=2)

    def confirm_back():
        if prescriptions:
            current_prescription = prescriptions[current_index["value"]]
            if current_prescription.dirty and not messagebox.askyesno(
                "Chưa lưu",
                "Đơn thuốc hiện tại có thay đổi chưa lưu. Quay lại mà không lưu?",
            ):
                return
        show_ho_so_window(root, container, show_primary_window)

    tb.Button(container, text="⬅ Quay lại", bootstyle="secondary", command=confirm_back).pack(pady=20)
