import ttkbootstrap as tb
import tkinter as tk
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from db.models import Thuoc  
from db.session import get_session 
from intellisense import AutocompleteEntry




# -------------------------
# Helpers
# -------------------------
def fetch_medicines():
    session = get_session()
    medicines = session.query(Thuoc).order_by(Thuoc.Ten).all()
    session.close()


    return [(t.Ten, float(t.Gia)) for t in medicines]


medicines = fetch_medicines()
ITEMS_PER_PAGE = 4
current_page = {"value": 1}


# -------------------------
# Page functions
# -------------------------
def render_medicine_list(root, page_container, page_label, show_primary_window, medicine_list=None):
    for w in page_container.winfo_children():
        w.destroy()

    if medicine_list is None:
        medicine_list = medicines

    start = (current_page["value"] - 1) * ITEMS_PER_PAGE
    end = start + ITEMS_PER_PAGE
    page_items = medicine_list[start:end]

    for name, price in page_items:
        card = tb.Frame(page_container, padding=10)
        card.pack(fill="x", pady=5)

        tb.Label(card, text=f"💊 {name}", font=("Quicksand", 12, "bold")).pack(anchor="w")
        tb.Label(card, text=f"{price}đ").pack(anchor="w")

        btn_frame = tb.Frame(card)
        btn_frame.pack(anchor="e")

        tb.Button(
            btn_frame, text="✏ Sửa", bootstyle="info-outline",
            command=lambda n=name, p=price: show_edit_thuoc_window(root, page_container, show_primary_window, n, p)
        ).pack(side="left", padx=5)

        tb.Button(
            btn_frame, text="🗑 Xoá", bootstyle="danger-outline",
            command=lambda n=name: delete_medicine(root, page_container, show_primary_window, page_label, n)
        ).pack(side="left")

    max_page = max(1, (len(medicine_list) + ITEMS_PER_PAGE - 1) // ITEMS_PER_PAGE)
    page_label.config(text=f"Page {current_page['value']} / {max_page}")


def change_page(direction, page_container, page_label, root, show_primary_window, medicine_list=None):
    if medicine_list is None:
        medicine_list = medicines
    max_page = max(1, (len(medicine_list) + ITEMS_PER_PAGE - 1) // ITEMS_PER_PAGE)
    current_page["value"] = max(1, min(max_page, current_page["value"] + direction))
    render_medicine_list(root, page_container, page_label, show_primary_window, medicine_list=medicine_list)


def show_thuoc_window(root, page_container, show_primary_window):
    page_container = clear_parents(page_container, stop_at=root, levels=2)

    tb.Label(page_container, text="💊 Quản lý thuốc", font=("Quicksand", 16, "bold")).pack(pady=10)

    search_frame = tb.Frame(page_container)
    search_frame.pack(fill="x", padx=20, pady=10)

    tb.Label(search_frame, text="🔍").pack(side="left")
    def fetch_suggestions(query):
        return [name for name, _ in medicines]

    search_entry = AutocompleteEntry(search_frame, width=100, fetch_suggestions=fetch_suggestions)
    search_entry.pack(side="left", padx=5)
    tb.Button(
        search_frame,
        text="×",
        command=lambda: (search_entry.delete(0, "end"), on_search_change()),
    ).pack(side="left", padx=5)

    filtered_medicines = {"data": medicines.copy()}

    def on_search_change(*args):
        query = search_entry.get().strip().lower()
        if query:
            filtered_medicines["data"] = [m for m in medicines if query in m[0].lower()]
        else:
            filtered_medicines["data"] = medicines.copy()
        current_page["value"] = 1
        render_medicine_list(root, medicine_frame, page_label, show_primary_window, medicine_list=filtered_medicines["data"])

    search_entry.var.trace_add("write", lambda *args: on_search_change())
    search_entry.bind("<<AutocompleteSelected>>", lambda e: on_search_change())


    tb.Button(
        search_frame, text="+ Thêm thuốc", bootstyle="success",
        command=lambda: show_add_thuoc_window(root, page_container, show_primary_window)
    ).pack(side="left")

    medicine_frame = tb.Frame(page_container, bootstyle="light", padding=10)
    medicine_frame.pack(fill="both", expand=True, padx=20, pady=10)

    pagination_frame = tb.Frame(page_container)
    pagination_frame.pack(pady=10)

    page_label = tb.Label(pagination_frame, text="")
    page_label.pack(side="left")

    tb.Button(
        pagination_frame, text="← Trước",
        command=lambda: change_page(-1, medicine_frame, page_label, root, show_primary_window, filtered_medicines["data"])
    ).pack(side="left", padx=10)

    tb.Button(
        pagination_frame, text="Sau →",
        command=lambda: change_page(1, medicine_frame, page_label, root, show_primary_window, filtered_medicines["data"])
    ).pack(side="left", padx=10)

    tb.Button(page_container, text="⬅ Quay lại", bootstyle="secondary",
              command=lambda: show_primary_window(root, page_container)).pack(pady=20)

    render_medicine_list(root, medicine_frame, page_label, show_primary_window, medicine_list=filtered_medicines["data"])


def show_add_thuoc_window(root, page_container, show_primary_window):
    for w in page_container.winfo_children():
        w.destroy()

    form = tb.Frame(page_container, padding=20)
    form.pack(pady=100)

    tb.Label(form, text="Tên thuốc").pack(anchor="w")
    name_entry = tb.Entry(form, width=40)
    name_entry.pack(pady=5)

    tb.Label(form, text="Giá tiền").pack(anchor="w")
    price_entry = tb.Entry(form, width=40)
    price_entry.pack(pady=5)

    def add_medicine():
        name = name_entry.get().strip()
        price = price_entry.get().strip()

        if name and price.isdigit():
            session = get_session()
            new_medicine = Thuoc(Ten=name, Gia=int(price))
            session.add(new_medicine)
            session.commit()
            session.close()

            global medicines
            medicines = fetch_medicines()
            current_page["value"] = 1
            show_thuoc_window(root, page_container, show_primary_window)

    tb.Button(form, text="Thêm vào kho thuốc", bootstyle="success", command=add_medicine).pack(pady=10)

    tb.Button(page_container, text="⬅ Quay lại", bootstyle="secondary",
              command=lambda: show_thuoc_window(root, page_container, show_primary_window)).pack(pady=20)


def show_edit_thuoc_window(root, page_container, show_primary_window, old_name, old_price):
    for w in page_container.winfo_children():
        w.destroy()

    form = tb.Frame(page_container, padding=20)
    form.pack(pady=100)

    tb.Label(form, text="Tên thuốc").pack(anchor="w")
    name_entry = tb.Entry(form, width=40)
    name_entry.insert(0, old_name)
    name_entry.pack(pady=5)

    tb.Label(form, text="Giá tiền").pack(anchor="w")
    price_entry = tb.Entry(form, width=40)
    price_entry.insert(0, str(int(old_price)))
    price_entry.pack(pady=5)

    def update_medicine():
        session = get_session()
        medicine = session.query(Thuoc).filter_by(Ten=old_name).first()
        if medicine:
            medicine.Ten = name_entry.get().strip()
            medicine.Gia = int(price_entry.get().strip())
            session.commit()
        session.close()

        global medicines
        medicines = fetch_medicines()
        current_page["value"] = 1
        show_thuoc_window(root, page_container, show_primary_window)

    button_frame = tb.Frame(form)
    button_frame.pack(pady=20)

    tb.Button(button_frame, text="💾 Lưu", bootstyle="success", command=update_medicine).pack(side="left", padx=10)
    tb.Button(button_frame, text="⬅ Quay lại", bootstyle="secondary",
              command=lambda: show_thuoc_window(root, page_container, show_primary_window)).pack(side="left", padx=10)


def delete_medicine(root, page_container, show_primary_window, page_label, name):
    session = get_session()
    medicine = session.query(Thuoc).filter_by(Ten=name).first()
    if medicine:
        session.delete(medicine)
        session.commit()
    session.close()

    global medicines
    medicines = fetch_medicines()
    current_page["value"] = 1
    render_medicine_list(root, page_container, page_label, show_primary_window)

def clear_parents(widget, stop_at=None, levels=2):
    parent = widget
    for _ in range(levels - 1):
        if parent.master == stop_at or parent.master is None:
            break
        parent = parent.master
    for w in parent.winfo_children():
        w.destroy()
    return parent
