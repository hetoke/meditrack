import ttkbootstrap as tb
from tkinter import messagebox

from services.record_service import create_record, update_record


def show_edit_ho_so_window(root, container, show_primary_window, controller, hoso_id, record, show_ho_so_window):
    _, name, year, address, phone, tiencan, _ = record

    for w in container.winfo_children():
        w.destroy()

    tb.Label(container, text="Sửa hồ sơ", font=("Quicksand", 16, "bold")).pack(pady=10)

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
            tiencan_entry.get("1.0", "end").strip(),
        )

        show_ho_so_window(root, container, show_primary_window, controller)

    tb.Button(container, text="💾 Lưu", bootstyle="success-outline", command=save_changes).pack(pady=10)
    tb.Button(
        container,
        text="↩ Quay lại",
        bootstyle="secondary-outline",
        command=lambda: show_ho_so_window(root, container, show_primary_window, controller),
    ).pack()


def show_add_ho_so_window(root, page_container, controller, show_primary_window, show_ho_so_window):
    for w in page_container.winfo_children():
        w.destroy()

    form = tb.Frame(page_container, padding=20)
    form.pack(pady=50)

    tb.Label(form, text="Họ và tên bệnh nhân").pack(anchor="w")
    name_entry = tb.Entry(form, width=40)
    name_entry.pack(pady=5)

    tb.Label(form, text="Năm sinh").pack(anchor="w")
    year_entry = tb.Entry(form, width=40)
    year_entry.pack(pady=5)

    tb.Label(form, text="Địa chỉ").pack(anchor="w")
    address_entry = tb.Entry(form, width=40)
    address_entry.pack(pady=5)

    tb.Label(form, text="Số điện thoại").pack(anchor="w")
    phone_entry = tb.Entry(form, width=40)
    phone_entry.pack(pady=5)

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

        create_record(name, year, address, phone, tiencan)
        show_ho_so_window(root, page_container, show_primary_window)

    tb.Button(form, text="Thêm hồ sơ", bootstyle="success", command=add_ho_so).pack(pady=10)
    tb.Button(
        page_container,
        text="⬅ Quay lại",
        bootstyle="secondary",
        command=lambda: show_ho_so_window(root, page_container, show_primary_window),
    ).pack(pady=20)
