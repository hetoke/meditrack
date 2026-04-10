import ttkbootstrap as tb
from tkinter import messagebox

from intellisense import AutocompleteEntry
from services.record_service import delete_record, fetch_patient_suggestions
from ui.record.controller import RecordController
from ui.record.forms import show_add_ho_so_window, show_edit_ho_so_window
from ui.record.helpers import bind_card_click, format_last_modified, open_detail


ITEMS_PER_PAGE = 15


def show_ho_so_window(root, container, show_primary_window, controller=None):
    for w in container.winfo_children():
        w.destroy()

    current_search_query = {"value": None}
    if controller is None:
        controller = RecordController()

    tb.Label(container, text="Hồ sơ bệnh nhân", font=("Quicksand", 16, "bold")).pack(pady=10)

    search_frame = tb.Frame(container)
    search_frame.pack(fill="x", padx=20, pady=10)

    tb.Label(search_frame, text="🔍").pack(side="left", padx=(0, 5))

    search_entry = AutocompleteEntry(search_frame, fetch_suggestions=fetch_patient_suggestions)
    search_entry.pack(side="left", fill="x", expand=True)

    tb.Button(search_frame, text="×", command=lambda: search_entry.delete(0, "end")).pack(side="left", padx=5)
    tb.Button(
        search_frame,
        text="+ Thêm hồ sơ",
        bootstyle="success",
        command=lambda: show_add_ho_so_window(root, container, controller, show_primary_window, show_ho_so_window),
    ).pack(side="right", padx=5)

    record_frame = tb.Frame(container, bootstyle="light", padding=10)
    record_frame.pack(fill="both", expand=True, padx=20, pady=10)

    pagination_frame = tb.Frame(container)
    pagination_frame.pack(pady=10)

    tb.Button(
        pagination_frame,
        text="← Trước",
        command=lambda: change_page(
            controller,
            -1,
            record_frame,
            page_label,
            root,
            show_primary_window,
            current_search_query["value"],
        ),
    ).pack(side="left", padx=10)

    page_label = tb.Label(pagination_frame, text="")
    page_label.pack(side="left")

    tb.Button(
        pagination_frame,
        text="→ Sau",
        command=lambda: change_page(
            controller,
            1,
            record_frame,
            page_label,
            root,
            show_primary_window,
            current_search_query["value"],
        ),
    ).pack(side="left", padx=10)

    tb.Button(
        container,
        text="⬅ Quay lại",
        bootstyle="secondary",
        command=lambda: show_primary_window(root, container),
    ).pack(pady=20)

    search_after_id = {"id": None}

    def on_search_change(*args):
        controller.current_page = 1
        current_search_query["value"] = search_entry.get().strip()

        if search_after_id["id"]:
            search_entry.after_cancel(search_after_id["id"])

        search_after_id["id"] = search_entry.after(
            100,
            lambda: render_record_list(
                root,
                record_frame,
                page_label,
                show_primary_window,
                controller,
                current_search_query["value"],
            ),
        )

    def on_suggestion_selected(*args):
        if search_after_id["id"]:
            search_entry.after_cancel(search_after_id["id"])
            search_after_id["id"] = None

        current_search_query["value"] = search_entry.get().strip()
        controller.current_page = 1
        render_record_list(
            root,
            record_frame,
            page_label,
            show_primary_window,
            controller,
            current_search_query["value"],
        )

    search_entry.var.trace_add("write", on_search_change)
    search_entry.bind("<<AutocompleteSelected>>", lambda e: on_suggestion_selected())

    render_record_list(root, record_frame, page_label, show_primary_window, controller)


def render_record_list(root, container, page_label, show_primary_window, controller, search_query=None):
    record_list = controller.get_page(controller.current_page, ITEMS_PER_PAGE, search_query)

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

        tb.Label(left, text=f"{name} - {year}", font=("Quicksand", 12)).pack(anchor="w")

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
                root,
                container.master,
                show_primary_window,
                controller,
                rid,
                r,
                show_ho_so_window,
            ),
        ).pack(side="left", padx=2)

        tb.Button(
            btn_inner,
            text="🗑 Xoá hồ sơ",
            style="CompactDanger.TButton",
            command=lambda rid=hoso_id: delete_ho_so(
                root,
                container,
                show_primary_window,
                controller,
                page_label,
                rid,
                search_query,
            ),
        ).pack(side="left", padx=2)

        right = tb.Frame(row)
        right.pack(side="right", padx=10)

        tb.Label(
            right,
            text=format_last_modified(last_modified),
            font=("Quicksand", 10),
            foreground="#6c757d",
        ).pack(anchor="e")

        click_handler = lambda e, r=record: open_detail(
            e, root, container, r, show_ho_so_window, show_primary_window
        )
        bind_card_click(card, click_handler, exclude_widget=btn_frame)

    max_page = max(1, (controller.total_records + ITEMS_PER_PAGE - 1) // ITEMS_PER_PAGE)
    page_label.config(text=f"Page {controller.current_page} / {max_page}")


def delete_ho_so(root, container, show_primary_window, controller, page_label, hoso_id, search_query=None):
    if not messagebox.askyesno("Xác nhận", "Bạn có chắc chắn muốn xoá hồ sơ này?"):
        return

    delete_record(hoso_id)

    max_page = max(1, (controller.total_records - 1 + ITEMS_PER_PAGE - 1) // ITEMS_PER_PAGE)
    if controller.current_page > max_page:
        controller.current_page = max_page

    render_record_list(root, container, page_label, show_primary_window, controller, search_query)


def change_page(controller, direction, container, page_label, root, show_primary_window, search_query=None):
    max_page = max(1, (controller.total_records + ITEMS_PER_PAGE - 1) // ITEMS_PER_PAGE)
    controller.current_page = max(1, min(max_page, controller.current_page + direction))
    render_record_list(root, container, page_label, show_primary_window, controller, search_query)
