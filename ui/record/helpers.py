from __future__ import annotations

from datetime import date, datetime
from typing import Any, Callable, Optional

import ttkbootstrap as tb

from ui.prescription.screen import show_ho_so_detail_window


def format_last_modified(dt: Optional[datetime | date]) -> str:
    if not dt:
        return "Chưa cập nhật"

    if isinstance(dt, datetime):
        return f"Cập nhật: {dt.strftime('%d/%m/%Y %H:%M')}"

    if isinstance(dt, date):
        return f"Cập nhật: {dt.strftime('%d/%m/%Y')}"

    return "Chưa cập nhật"


def open_detail(
    event: Any,
    root: tb.Window,
    container: tb.Frame,
    record: Any,
    show_ho_so_window: Callable[..., None],
    show_primary_window: Callable[..., None],
) -> None:
    show_ho_so_detail_window(root, container, record, show_ho_so_window, show_primary_window)


def bind_card_click(
    widget: tb.Misc,
    callback: Callable[..., None],
    exclude_widget: Optional[tb.Misc] = None,
) -> None:
    widget.bind("<Button-1>", callback)
    for child in widget.winfo_children():
        if child is exclude_widget or isinstance(child, tb.Button):
            continue
        bind_card_click(child, callback, exclude_widget)
