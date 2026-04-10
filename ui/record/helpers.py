from datetime import date, datetime

import ttkbootstrap as tb

from ui.prescription.screen import show_ho_so_detail_window


def format_last_modified(dt):
    if not dt:
        return "Chưa cập nhật"

    if isinstance(dt, datetime):
        return f"Cập nhật: {dt.strftime('%d/%m/%Y %H:%M')}"

    if isinstance(dt, date):
        return f"Cập nhật: {dt.strftime('%d/%m/%Y')}"

    return "Chưa cập nhật"


def open_detail(event, root, container, record, show_ho_so_window, show_primary_window):
    show_ho_so_detail_window(root, container, record, show_ho_so_window, show_primary_window)


def bind_card_click(widget, callback, exclude_widget=None):
    widget.bind("<Button-1>", callback)
    for child in widget.winfo_children():
        if child is exclude_widget or isinstance(child, tb.Button):
            continue
        bind_card_click(child, callback, exclude_widget)
