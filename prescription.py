import ttkbootstrap as tb
import tkinter as tk
import tkinter.font as tkfont
from tkinter import messagebox
from datetime import date, datetime

from sqlalchemy.orm import object_session, selectinload

from db import DonThuoc, ChiDinh, Thuoc
from db_connect import get_session
from intellisense import AutocompleteEntry


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


def safe_float(value):
    try:
        return float(value)
    except Exception:
        return 0.0


def format_currency(value):
    return f"{value:,.0f} đ"

def ensure_donthuoc_loaded(donthuoc_obj):
    if not donthuoc_obj:
        return None
    if "chidinh_list" in donthuoc_obj.__dict__:
        return donthuoc_obj
    if object_session(donthuoc_obj) is None:
        don_id = getattr(donthuoc_obj, "DonThuocID", None)
        if not don_id:
            return donthuoc_obj
        session = get_session()
        try:
            donthuoc_obj = session.get(
                DonThuoc,
                don_id,
                options=[selectinload(DonThuoc.chidinh_list).selectinload(ChiDinh.thuoc)],
            )
            session.expunge_all()
        finally:
            session.close()
    return donthuoc_obj

def format_ngaylap(value):
    if isinstance(value, datetime):
        return value.strftime("%d/%m/%Y %H:%M:%S")
    if isinstance(value, date):
        return value.strftime("%d/%m/%Y 00:00:00")
    return datetime.now().strftime("%d/%m/%Y %H:%M:%S")


def show_ho_so_detail_window(root, container, record, show_ho_so_window, show_primary_window):
    container = clear_parents(container, stop_at=root, levels=2)

    # record is (HoSoID, Ten, NamSinh, DiaChi, DienThoai, TienCan)
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
        font=("Quicksand", 14, "bold"),
    )
    sidebar_total_label.pack(fill="x", pady=5)

    sidebar_actions = tb.Frame(sidebar)
    sidebar_actions.pack(fill="x", pady=(10, 5))

    # --- Content ---
    content = tb.Frame(container, padding=20)
    content.pack(side="left", fill="both", expand=True)

    # ---- Tiá»n cÄƒn ----
    tiencan_box = tb.Labelframe(content, text="Tiền căn", padding=10)
    tiencan_box.pack(fill="x", pady=(2, 4))

    tiencan_text = tk.Text(tiencan_box, height=3, wrap="word")
    tiencan_text.pack(fill="x")
    if tiencan:
        tiencan_text.insert("1.0", tiencan)

    tiencan_text.config(state="disabled")

    # ============= PRESCRIPTIONS =============
    prescriptions = []
    current_index = {"value": 0}
    session = get_session()
    donthuoc_list = (
        session.query(DonThuoc)
        .options(selectinload(DonThuoc.chidinh_list).selectinload(ChiDinh.thuoc))
        .filter(DonThuoc.HoSoID == hoso_id)
        .order_by(DonThuoc.NgayLap)
        .all()
    )
    session.expunge_all()
    session.close()

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

    def apply_table_zoom(prescription):
        zoom = prescription.get("zoom", 1.0)
        size = max(8, min(24, int(round(base_font_size * zoom))))
        pad = max(0, int(round(base_pad * zoom)))
        ipad = max(0, int(round(2 * zoom)))
        row_height = max(10, int(round(base_row * zoom)))
        grid = prescription.get("grid_frame")
        if not grid:
            return
        row_count = prescription.get("row_count", 0)
        if row_count:
            for r in range(row_count):
                grid.grid_rowconfigure(r, minsize=row_height)
        col_widths = prescription.get("col_widths", [])
        width_scale = zoom * 0.75 if zoom < 1.0 else zoom
        for w in grid.winfo_children():
            try:
                w.configure(font=build_font(size))
            except Exception:
                pass
            try:
                info = w.grid_info()
                col = int(info.get("column", 0))
                if col_widths:
                    if col < len(col_widths):
                        w.configure(width=max(5, int(round(col_widths[col] * width_scale))))
                    else:
                        w.configure(width=max(3, int(round(6 * zoom))))
                w.grid_configure(padx=pad, pady=pad, ipady=ipad)
            except Exception:
                pass

    def zoom_table(delta):
        if not prescriptions:
            return
        p = prescriptions[current_index["value"]]
        new_zoom = p.get("zoom", 1.0) + delta
        new_zoom = max(zoom_min, min(zoom_max, new_zoom))
        p["zoom"] = new_zoom
        apply_table_zoom(p)

    zoom_row = tb.Frame(sidebar_actions)
    zoom_row.pack(fill="x", pady=2)
    tb.Button(zoom_row, text="Thu nhỏ", command=lambda: zoom_table(-zoom_step)).pack(side="left", expand=True, fill="x", padx=(0, 2))
    tb.Button(zoom_row, text="Phóng to", command=lambda: zoom_table(zoom_step)).pack(side="left", expand=True, fill="x", padx=(2, 0))

    # --- Helper: Build single prescription UI ---
    def calculate_total_from_donthuoc(donthuoc_obj):
        total = 0.0
        donthuoc_obj = ensure_donthuoc_loaded(donthuoc_obj)
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

    def build_prescription(donthuoc_obj=None, seed_rows=None, seed_chandoan=None):
        frame = tb.Frame(content, padding=10)
        prescriptions.append({
            "frame": frame,
            "donthuoc": donthuoc_obj,
            "entries": [],
            "chandoan_text": None,
            "grid_frame": None,
            "zoom": 1.0,
            "row_count": 0,
            "dirty": False,
        })
        p = prescriptions[-1]

        # ---- Chuáº©n Ä‘oÃ¡n ----
        chandoan_box = tb.Labelframe(frame, text="Chuẩn đoán", padding=10)
        chandoan_box.pack(fill="x", pady=(2, 4))
        chandoan_text = tk.Text(chandoan_box, height=3, wrap="word")
        chandoan_text.pack(fill="x")
        if donthuoc_obj:
            chandoan_text.insert("1.0", donthuoc_obj.MoTa)
        elif seed_chandoan:
            chandoan_text.insert("1.0", seed_chandoan)
            p["dirty"] = True

        def mark_dirty(*_):
            p["dirty"] = True

        def on_text_modified(event):
            w = event.widget
            if w.edit_modified():
                mark_dirty()
                w.edit_modified(False)

        # ---- Prescription Table ----
        columns = ["Thuốc", "Sáng trước ăn", "Sáng sau ăn", "Trưa trước ăn",
                    "Trưa sau ăn", "Chiều trước ăn", "Chiều sau ăn", "Tối"]
        sau_an_indices = {2, 4, 6}
        col_widths = [22, 12, 12, 12, 12, 12, 12, 12]
        p["col_widths"] = col_widths

        table_outer = tb.Frame(frame)
        table_outer.pack(fill="both", expand=True, padx=20, pady=(2, 6))

        canvas = tk.Canvas(table_outer)
        vsb = tb.Scrollbar(table_outer, orient="vertical", command=canvas.yview)
        canvas.configure(yscrollcommand=vsb.set)
        vsb.pack(side="right", fill="y")
        canvas.pack(side="left", fill="both", expand=True)

        grid_frame = tb.Frame(canvas)
        canvas.create_window((0, 0), window=grid_frame, anchor="nw")
        p["grid_frame"] = grid_frame

        resize_state = {"col": None, "start_x": 0, "start_w": 0}

        def cell_motion(event, col):
            w = event.widget
            if w.winfo_width() - event.x <= 6:
                w.configure(cursor="sb_h_double_arrow")
            else:
                w.configure(cursor="")

        def start_resize(event, col):
            w = event.widget
            if w.winfo_width() - event.x <= 6:
                resize_state["col"] = col
                resize_state["start_x"] = event.x_root
                resize_state["start_w"] = w.winfo_width()
                w.configure(cursor="sb_h_double_arrow")
            else:
                resize_state["col"] = None

        def do_resize(event, col):
            if resize_state["col"] != col:
                return
            dx = event.x_root - resize_state["start_x"]
            new_px = max(40, resize_state["start_w"] + dx)
            font = tkfont.nametofont("TkDefaultFont")
            char_w = max(1, font.measure("0"))
            col_widths[col] = max(5, int(round(new_px / char_w)))
            p["col_widths"] = col_widths
            apply_table_zoom(p)

        def stop_resize(event, col):
            if resize_state["col"] == col:
                resize_state["col"] = None
            event.widget.configure(cursor="")

        entries = []
        p["row_count"] = 0
        apply_table_zoom(p)

        def add_row(row_values=None):
            row_index = len(entries) + 1
            row_entries = []
            vals = row_values if row_values else ("",) * len(columns)

            for c in range(len(columns)):
                v = vals[c] if c < len(vals) else ""
                if c == 0:
                    # This works but would be lethal if there is too much thuoc
                    all_meds = lambda query: [
                        t.Ten for t in session.query(Thuoc).filter(Thuoc.Ten.ilike(f"{query}%")).all()
                    ]
                    e = AutocompleteEntry(grid_frame, fetch_suggestions=all_meds, width=col_widths[c])
                else:
                    e = tk.Entry(grid_frame, width=col_widths[c])
                e.insert(0, v)
                if v:
                    p["dirty"] = True
                if c in sau_an_indices:
                    e.config(bg="#FFC107")
                e.grid(row=row_index, column=c, sticky="nsew", padx=1, pady=1)
                e.bind("<KeyRelease>", mark_dirty)
                e.bind("<FocusOut>", mark_dirty)
                e.bind("<Motion>", lambda ev, col=c: cell_motion(ev, col))
                e.bind("<Button-1>", lambda ev, col=c: start_resize(ev, col))
                e.bind("<B1-Motion>", lambda ev, col=c: do_resize(ev, col))
                e.bind("<ButtonRelease-1>", lambda ev, col=c: stop_resize(ev, col))
                row_entries.append(e)

            entries.append(row_entries)
            p["row_count"] = len(entries)

            def delete_row():
                for e in row_entries + [btn]:
                    e.destroy()
                if row_entries in entries:
                    entries.remove(row_entries)
                p["row_count"] = len(entries)
                p["dirty"] = True
                grid_frame.update_idletasks()
                canvas.config(scrollregion=canvas.bbox("all"))

            btn = tb.Button(grid_frame, text="X", bootstyle="danger", command=delete_row)
            btn.grid(row=row_index, column=len(columns), sticky="nsew", padx=1, pady=1)

            apply_table_zoom(prescriptions[-1])

            grid_frame.update_idletasks()
            canvas.config(scrollregion=canvas.bbox("all"))

        # Populate rows from DB / seed data
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
        elif seed_rows:
            for row in seed_rows:
                add_row(row)
        else:
            add_row()

        tb.Button(frame, text="Thêm dòng", bootstyle="success",
                  command=lambda: add_row()).pack(anchor="e", pady=5)

        chandoan_text.bind("<<Modified>>", on_text_modified)
        prescriptions[-1]["chandoan_text"] = chandoan_text
        prescriptions[-1]["entries"] = entries
        prescriptions[-1]["add_row"] = add_row

        return frame

    delete_btn = None

    # --- Navigation / CRUD functions ---
    def show_prescription(index):
        for p in prescriptions:
            p["frame"].pack_forget()
        prescriptions[index]["frame"].pack(fill="both", expand=True)
        current_index["value"] = index
        nav_label.config(text=f"Đơn {index+1}/{len(prescriptions)}")
        don_obj = prescriptions[index]["donthuoc"]
        if don_obj and don_obj.NgayLap:
            date_text = format_ngaylap(don_obj.NgayLap)
            date_label.config(text=f"Ngày lập đơn thuốc: {date_text}")
        else:
            date_label.config(text="")
        total_value = calculate_total_from_donthuoc(prescriptions[index]["donthuoc"])
        sidebar_total_label.config(text=f"Tổng tiền: {format_currency(total_value)}")
        prev_btn.config(state=("disabled" if index == 0 else "normal"))
        next_btn.config(state=("disabled" if index == len(prescriptions)-1 else "normal"))
        if delete_btn:
            delete_btn.config(state=("disabled" if len(prescriptions) <= 1 else "normal"))
        apply_table_zoom(prescriptions[index])

    def next_prescription():
        if current_index["value"] < len(prescriptions) - 1:
            show_prescription(current_index["value"] + 1)

    def prev_prescription():
        if current_index["value"] > 0:
            show_prescription(current_index["value"] - 1)

    def add_prescription():
        build_prescription()
        show_prescription(len(prescriptions) - 1)

    def duplicate_prescription():
        if not prescriptions:
            return
        src = prescriptions[current_index["value"]]
        chandoan = src["chandoan_text"].get("1.0", "end").strip() if src.get("chandoan_text") else ""
        rows = []
        for row in src.get("entries", []):
            vals = [e.get() for e in row]
            if any(v.strip() for v in vals):
                rows.append(vals)
        build_prescription(seed_rows=rows if rows else None, seed_chandoan=chandoan)
        prescriptions[-1]["dirty"] = True
        show_prescription(len(prescriptions) - 1)

    def delete_prescription(index):
        if not prescriptions or index < 0 or index >= len(prescriptions):
            return
        p = prescriptions[index]
        if p.get("dirty"):
            if not messagebox.askyesno("Chưa lưu", "Đơn thuốc này có thay đổi chưa lưu. Xoá vẫn tiếp tục?"):
                return
        if not messagebox.askyesno("Xác nhận", "Bạn có chắc chắn muốn xoá đơn thuốc này?"):
            return
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
            don_obj = DonThuoc(HoSoID=hoso_id, NgayLap=datetime.now())
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
                    messagebox.showerror("Lỗi", f"Thuốc '{name}' không tồn tại")
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
        don_obj = session_local.get(
            DonThuoc,
            don_obj.DonThuocID,
            options=[selectinload(DonThuoc.chidinh_list).selectinload(ChiDinh.thuoc)],
        )
        p["donthuoc"] = don_obj
        if don_obj and don_obj.NgayLap:
            date_text = format_ngaylap(don_obj.NgayLap)
            date_label.config(text=f"Ngày lập đơn thuốc: {date_text}")
        else:
            date_label.config(text="")
        sidebar_total_label.config(text=f"Tổng tiền: {format_currency(total_cost)}")
        session_local.close()
        messagebox.showinfo("Thông báo", "Đã lưu đơn thuốc thành công!")
        p["dirty"] = False

    # --- Build prescriptions from DB ---
    for don in donthuoc_list:
        build_prescription(don)
    if not prescriptions:
        build_prescription()
        show_prescription(0)
    else:
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
        if any(p.get("dirty") for p in prescriptions):
            if not messagebox.askyesno("Chưa lưu", "Bạn có thay đổi chưa lưu. Quay lại mà không lưu?"):
                return
        show_ho_so_window(root, container, show_primary_window)

    tb.Button(
        container,
        text="⬅ Quay lại",
        bootstyle="secondary",
        command=confirm_back,
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
