import ttkbootstrap as tb
from tkinter import messagebox


from ui.record.controller import RecordController
from datetime import datetime, date


from services.record_service import (
    fetch_patient_suggestions,
    create_record,
    update_record,
    delete_record,
)

from prescription import show_ho_so_detail_window
from intellisense import AutocompleteEntry

ITEMS_PER_PAGE = 15


# -------------------------
# show_ho_so_window (small fixes)
# -------------------------
def show_ho_so_window(root, container, show_primary_window, controller=None):
    for w in container.winfo_children():
        w.destroy()

    current_search_query = {"value": None}
    if controller is None:
        controller = RecordController()

    

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
        command=lambda: show_add_ho_so_window(root, container, controller, show_primary_window)
    ).pack(side="right", padx=5)

    record_frame = tb.Frame(container, bootstyle="light", padding=10)
    record_frame.pack(fill="both", expand=True, padx=20, pady=10)

    pagination_frame = tb.Frame(container)
    pagination_frame.pack(pady=10)

    prev_btn = tb.Button(
        pagination_frame,
        text="← Trước",
        command=lambda: change_page(
            controller, -1,
            record_frame, page_label,
            root, show_primary_window,
            current_search_query["value"]
        )
    )
    prev_btn.pack(side="left", padx=10)

    page_label = tb.Label(pagination_frame, text="")
    page_label.pack(side="left")

    next_btn = tb.Button(
        pagination_frame,
        text="→ Sau",
        command=lambda: change_page(
            controller, 1,
            record_frame, page_label,
            root, show_primary_window,
            current_search_query["value"]
        )
    )
    next_btn.pack(side="left", padx=10)

    tb.Button(container, text="⬅ Quay lại", bootstyle="secondary",
              command=lambda: show_primary_window(root, container)).pack(pady=20)
    

    def on_search_change(*args):
        controller.current_page = 1
        current_search_query["value"] = search_entry.get().strip()

        render_record_list(
            root,
            record_frame,
            page_label,
            show_primary_window,
            controller,
            current_search_query["value"]
        )
    search_entry.var.trace_add("write", on_search_change)

    # Initial render
    render_record_list(
        root,
        record_frame,
        page_label,
        show_primary_window,
        controller
    )



# -------------------------
# render_record_list (accept show_primary_window)
# -------------------------

def format_last_modified(dt):
    if not dt:
        return "Chưa cập nhật"

    if isinstance(dt, datetime):
        return f"Cập nhật: {dt.strftime('%d/%m/%Y %H:%M')}"

    if isinstance(dt, date):
        return f"Cập nhật: {dt.strftime('%d/%m/%Y')}"

    return "Chưa cập nhật"

def stop_event(event):
    return "break"

def open_detail(event, root, container, record, show_ho_so_window, show_primary_window):
    show_ho_so_detail_window(
        root, container, record, show_ho_so_window, show_primary_window
    )

def bind_card_click(widget, callback, exclude_widget=None):
    """Recursively bind click event to widget and all its children"""
    widget.bind("<Button-1>", callback)
    for child in widget.winfo_children():
        # Skip the excluded widget and buttons
        if child is exclude_widget or isinstance(child, tb.Button):
            continue
        bind_card_click(child, callback, exclude_widget)

def render_record_list(root, container, page_label, show_primary_window, controller, search_query=None):
    
    record_list = controller.get_page(
        controller.current_page,
        ITEMS_PER_PAGE,
        search_query
    )

    for w in container.winfo_children():
        w.destroy()

    for record in record_list:
        hoso_id, name, year, address, phone, tiencan, last_modified = record

        card = tb.Frame(container, padding=(8, 3))
        card.pack(fill="x", pady=2)

        row = tb.Frame(card)
        row.pack(fill="x")

        left = tb.Frame(row)
        left.pack(side="left", fill="x", expand=True)

        tb.Label(
            left,
            text=f"{name} ({year})",
            font=("Quicksand", 12)
        ).pack(anchor="w")

        btn_frame = tb.Frame(row, width=300, height=28)
        btn_frame.pack(side="right")
        btn_frame.pack_propagate(False)

        btn_inner = tb.Frame(btn_frame)
        btn_inner.pack(expand=True)

        tb.Button(
            btn_inner,
            text="✏ Sửa hồ sơ",
            style="CompactInfo.TButton",
            command=lambda rid=hoso_id, r=record: show_edit_ho_so_window(
                root, container.master, show_primary_window, controller, rid, r
            )
        ).pack(side="left", padx=2)

        tb.Button(
            btn_inner,
            text="🗑 Xoá hồ sơ",
            style="CompactDanger.TButton",
            command=lambda rid=hoso_id: delete_ho_so(
                root, container, show_primary_window,
                controller, page_label, rid, search_query
            )
        ).pack(side="left", padx=2)

        right = tb.Frame(row)
        right.pack(side="right", padx=10)

        tb.Label(
            right,
            text=format_last_modified(last_modified),
            font=("Quicksand", 10),
            foreground="#6c757d"
        ).pack(anchor="e")

        click_handler = lambda e, r=record: open_detail(
            e, root, container, r, show_ho_so_window, show_primary_window
        )
        bind_card_click(card, click_handler, exclude_widget=btn_frame)

    max_page = max(
        1,
        (controller.total_records + ITEMS_PER_PAGE - 1) // ITEMS_PER_PAGE
    )

    page_label.config(text=f"Page {controller.current_page} / {max_page}")

# -------------------------
# show_edit_ho_so_window (persist edits to DB)
# -------------------------
def show_edit_ho_so_window(root, container, show_primary_window, controller, hoso_id, record):
    """Edit a HoSo record by HoSoID (persists to DB)."""
    # record may be outdated; we still use it for initial fill
    _, name, year, address, phone, tiencan, _ = record
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
        update_record(
            hoso_id,
            name_entry.get().strip(),
            year_value,
            address_entry.get().strip(),
            phone_entry.get().strip(),
            tiencan_entry.get("1.0", "end").strip()
        )

        show_ho_so_window(root, container, show_primary_window, controller)
    

    tb.Button(container, text="💾 Lưu", bootstyle="success-outline", command=save_changes).pack(pady=10)
    tb.Button(container, text="↩ Quay lại", bootstyle="secondary-outline",
              command=lambda: show_ho_so_window(root, container, show_primary_window, controller)).pack()


# -------------------------
# delete_ho_so (persist delete to DB)
# -------------------------
def delete_ho_so(root, container, show_primary_window,
                 controller, page_label, hoso_id, search_query=None):

    if not messagebox.askyesno("Xác nhận", "Bạn có chắc chắn muốn xoá hồ sơ này?"):
        return

    delete_record(hoso_id)

    max_page = max(
        1,
        (controller.total_records - 1 + ITEMS_PER_PAGE - 1) // ITEMS_PER_PAGE
    )

    if controller.current_page > max_page:
        controller.current_page = max_page

    render_record_list(
        root,
        container,
        page_label,
        show_primary_window,
        controller,
        search_query
    )



# -------------------------
# show_add_ho_so_window (refresh records after commit)
# -------------------------
def show_add_ho_so_window(root, page_container, controller, show_primary_window):
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
            create_record(name, year, address, phone, tiencan)
            show_ho_so_window(root, page_container, show_primary_window)

    tb.Button(form, text="Thêm hồ sơ", bootstyle="success", command=add_ho_so).pack(pady=10)

    tb.Button(page_container, text="⬅ Quay lại", bootstyle="secondary",
              command=lambda: show_ho_so_window(root, page_container, show_primary_window)).pack(pady=20)





def change_page(controller, direction, container, page_label, root, show_primary_window, search_query=None):
    max_page = max(
        1,
        (controller.total_records + ITEMS_PER_PAGE - 1) // ITEMS_PER_PAGE
    )

    controller.current_page = max(
        1,
        min(max_page, controller.current_page + direction)
    )

    render_record_list(
        root,
        container,
        page_label,
        show_primary_window,
        controller,
        search_query
    )


