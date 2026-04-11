import ttkbootstrap as tb
import tkinter as tk
import tkinter.font as tkfont

from intellisense import AutocompleteEntry
from services.prescription_service import fetch_thuoc_suggestions
from utils.formatter import safe_float


def format_dose_value(value):
    if value in (None, ""):
        return ""
    try:
        number = float(value)
    except (TypeError, ValueError):
        return str(value)

    if number.is_integer():
        return str(int(number))
    return f"{number:.10f}".rstrip("0").rstrip(".")


class TableRowFactory:
    def __init__(self, parent_frame, columns, col_widths, bold_font, sau_an_indices, on_dirty_callback):
        self.parent_frame = parent_frame
        self.columns = columns
        self.col_widths = col_widths
        self.bold_font = bold_font
        self.sau_an_indices = sau_an_indices
        self.on_dirty_callback = on_dirty_callback

    def create_row_structure(self, values=None):
        """Creates the basic structure of a row - returns entries and buttons"""
        excluded = False
        if isinstance(values, dict):
            excluded = values.get("excluded", False)
            values = values.get("entries", [])

        values = values or [""] * len(self.columns)
        row_entries = []

        # Create entries
        for c in range(len(self.columns)):
            if c == 0:
                entry = AutocompleteEntry(
                    self.parent_frame,
                    fetch_suggestions=fetch_thuoc_suggestions,
                    width=self.col_widths[c],
                    font=self.bold_font,
                )
            else:
                entry = tk.Entry(
                    self.parent_frame,
                    width=self.col_widths[c],
                    font=self.bold_font
                )

            entry.config(
                relief="solid",
                bd=1,
                highlightthickness=1,
                highlightbackground="black",
                highlightcolor="black",
            )

            if c < len(values):
                entry.insert(0, format_dose_value(values[c]) if c > 0 else values[c])

            if c in self.sau_an_indices:
                entry.config(bg="#FFC107")

            row_entries.append(entry)

        # Create buttons structure (commands will be set by caller)
        btn_del = tb.Button(
            self.parent_frame,
            text="X",
            bootstyle="danger",
        )

        btn_insert_above = tb.Button(
            self.parent_frame,
            text="↑+",
            width=2,
        )

        btn_insert_below = tb.Button(
            self.parent_frame,
            text="↓+",
            width=2,
        )

        btn_toggle_money = tb.Button(
            self.parent_frame,
            text="T$",
            width=3,
        )

        return {
            "entries": row_entries,
            "btn_del": btn_del,
            "btn_insert_above": btn_insert_above,
            "btn_insert_below": btn_insert_below,
            "btn_toggle_money": btn_toggle_money,
            "exclude_from_total": excluded,
        }

    def setup_entry_events(self, entry, col, on_cell_motion, on_cell_press, on_cell_drag, on_cell_release):
        """Setup all the event bindings for an entry"""
        entry.bind("<KeyRelease>", lambda *_: self.on_dirty_callback())
        entry.bind("<Motion>", lambda ev, col=col: on_cell_motion(ev, col))
        entry.bind("<Button-1>", lambda ev, col=col: on_cell_press(ev, col))
        entry.bind("<B1-Motion>", on_cell_drag)
        entry.bind("<ButtonRelease-1>", on_cell_release)

    def create_enter_handler(self, row_obj, col, get_row_index_func, focus_cell_callback):
        """Create the enter key handler for a specific entry"""
        def on_enter(event):
            row_idx = get_row_index_func(row_obj)

            # Medicine column (autocomplete handling)
            if col == 0:
                widget = event.widget
                
                # If autocomplete is showing
                if hasattr(widget, 'listbox_visible') and widget.listbox_visible and widget.listbox:
                    # Select from listbox and close it
                    widget.select_suggestion()
                    # Move to next cell after brief delay
                    widget.after(50, lambda: focus_cell_callback(row_idx, 1))
                    return "break"
                
                # No autocomplete visible, move to next cell immediately
                focus_cell_callback(row_idx, 1)
                return "break"

            # Normal columns (not medicine)
            next_col = col + 1
            if next_col < len(self.columns):
                # Move to next column in same row
                focus_cell_callback(row_idx, next_col)
            else:
                # Last column → create new row and focus on medicine cell
                focus_cell_callback(row_idx + 1, 0)

            return "break"
        
        return on_enter


class PrescriptionTable:
    def __init__(self, parent, donthuoc=None, seed_rows=None, seed_chandoan=None, on_change=None):
        self.frame = tb.Frame(parent, padding=10)

        self.donthuoc = donthuoc
        self.entries = []
        self.dirty = False
        self.zoom = 1.0
        self.on_change = on_change

        self._resize_col = None
        self._resize_start_x = 0
        self._resize_start_width = 0

        self.grid_frame = None
        self.col_widths = [18, 4, 4, 4, 4, 4, 4, 4]
        self.columns = ["Thuốc", "Sáng trước ăn", "Sáng sau ăn", "Trưa trước ăn", "Trưa sau ăn", "Chiều trước ăn", "Chiều sau ăn", "Tối"]
        self.sau_an_indices = {2, 4, 6}

        default_font = tkfont.nametofont("TkDefaultFont")
        self.bold_font = default_font.copy()
        self.bold_font.configure(weight="bold")

        self._build_chandoan(seed_chandoan)
        self._build_table(seed_rows)
        

    # -------------------------------------------------
    # Public helpers (for screen.py compatibility)
    # -------------------------------------------------

    def pack(self, **kwargs):
        self.frame.pack(**kwargs)

    def pack_forget(self):
        self.frame.pack_forget()

    # -------------------------------------------------
    # Diagnosis
    # -------------------------------------------------

    def _build_chandoan(self, seed_text=None):
        box = tb.Labelframe(self.frame, text="Chuẩn đoán", padding=10)
        box.pack(fill="x", pady=(2, 4))

        self.chandoan_text = tk.Text(box, height=3, wrap="word")
        self.chandoan_text.pack(fill="x")

        if self.donthuoc and getattr(self.donthuoc, "MoTa", None):
            self.chandoan_text.insert("1.0", self.donthuoc.MoTa)
        elif seed_text:
            self.chandoan_text.insert("1.0", seed_text)
            self.dirty = True

        def on_modified(event):
            if self.chandoan_text.edit_modified():
                self.dirty = True
                self.chandoan_text.edit_modified(False)

        self.chandoan_text.bind("<<Modified>>", on_modified)

    # -------------------------------------------------
    # Table
    # -------------------------------------------------

    def _build_table(self, seed_rows=None):
        table_outer = tb.Frame(self.frame)
        table_outer.pack(fill="both", expand=True, padx=20, pady=(2, 6))

        canvas = tk.Canvas(table_outer)
        vsb = tb.Scrollbar(table_outer, orient="vertical", command=canvas.yview)
        canvas.configure(yscrollcommand=vsb.set)

        vsb.pack(side="right", fill="y")
        canvas.pack(side="left", fill="both", expand=True)

        self.grid_frame = tb.Frame(canvas)
        window_id = canvas.create_window((0, 0), window=self.grid_frame, anchor="nw")

        for c in range(len(self.columns)):
            self.grid_frame.columnconfigure(c * 2, minsize=40)

        # Create factory instance
        factory = TableRowFactory(
            parent_frame=self.grid_frame,
            columns=self.columns,
            col_widths=self.col_widths,
            bold_font=self.bold_font,
            sau_an_indices=self.sau_an_indices,
            on_dirty_callback=self._mark_dirty
        )

        EDGE_THRESHOLD = 6  # pixels

        def on_cell_motion(event, col):
            widget = event.widget
            x = event.x

            if widget.winfo_width() - x <= EDGE_THRESHOLD:
                widget.config(cursor="sb_h_double_arrow")
            else:
                widget.config(cursor="")

        def on_cell_press(event, col):
            widget = event.widget
            if widget.winfo_width() - event.x <= EDGE_THRESHOLD:
                self._resize_col = col
                self._resize_start_x = event.x_root
                self._resize_start_width = self.col_widths[col]

        def on_cell_drag(event):
            if self._resize_col is None:
                return

            dx = event.x_root - self._resize_start_x
            char_delta = dx // 6
            new_width = max(4, self._resize_start_width + char_delta)

            self.col_widths[self._resize_col] = new_width
            apply_column_width(self._resize_col)

        def on_cell_release(event):
            self._resize_col = None

        def apply_column_width(col):
            w = self.col_widths[col]
            for row in self.entries:
                row["entries"][col].config(width=w)

        def on_canvas_configure(event):
            canvas.itemconfigure(window_id, width=event.width)

        def on_frame_configure(event):
            canvas.configure(scrollregion=canvas.bbox("all"))

        canvas.bind("<Configure>", on_canvas_configure)
        self.grid_frame.bind("<Configure>", on_frame_configure)

        def focus_cell(row_idx, col_idx):
            if row_idx < 0:
                return

            # add new row if needed
            if row_idx >= len(self.entries):
                add_row()

            row = self.entries[row_idx]
            if col_idx < len(row["entries"]):
                row["entries"][col_idx].focus_set()

        # ---- Row logic ----
        def get_row_index(row_obj):
            return self.entries.index(row_obj)

        def refresh_grid():
            for i, row in enumerate(self.entries):
                for c, e in enumerate(row["entries"]):
                    e.grid(row=i, column=c * 2, sticky="nsew", padx=1, pady=1)
                base = len(self.columns) * 2

                row["btn_del"].grid(row=i, column=base)
                row["btn_insert_above"].grid(row=i, column=base + 1)
                row["btn_insert_below"].grid(row=i, column=base + 2)
                row["btn_toggle_money"].grid(row=i, column=base + 3, padx=(2, 0))

        def update_row_money_button(row_obj):
            if row_obj["exclude_from_total"]:
                row_obj["btn_toggle_money"].config(text="No$", bootstyle="warning")
            else:
                row_obj["btn_toggle_money"].config(text="T$", bootstyle="success")

        def delete_row(row_obj):
            idx = get_row_index(row_obj)
            for w in row_obj["entries"] + [
                row_obj["btn_del"],
                row_obj["btn_insert_above"],
                row_obj["btn_insert_below"],
                row_obj["btn_toggle_money"],
            ]:
                w.destroy()
            self.entries.pop(idx)
            refresh_grid()
            self._mark_dirty()

        def insert_row_above(index):
            add_row_at_index(index)

        def insert_row_below(index):
            add_row_at_index(index + 1)

        def toggle_row_money(row_obj):
            row_obj["exclude_from_total"] = not row_obj["exclude_from_total"]
            update_row_money_button(row_obj)
            self._mark_dirty()

        def normalize_numeric_entry(entry):
            value = entry.get().strip()
            formatted = format_dose_value(value)
            entry.delete(0, "end")
            entry.insert(0, formatted)

        def add_row_at_index(index, values=None):
            # Use factory to create row structure
            row_obj = factory.create_row_structure(values)
            
            # Setup button commands
            row_obj["btn_del"].config(command=lambda ro=row_obj: delete_row(ro))
            row_obj["btn_insert_above"].config(command=lambda ro=row_obj: insert_row_above(get_row_index(ro)))
            row_obj["btn_insert_below"].config(command=lambda ro=row_obj: insert_row_below(get_row_index(ro)))
            row_obj["btn_toggle_money"].config(command=lambda ro=row_obj: toggle_row_money(ro))
            update_row_money_button(row_obj)

            # Setup entry events
            for c, entry in enumerate(row_obj["entries"]):
                factory.setup_entry_events(entry, c, on_cell_motion, on_cell_press, on_cell_drag, on_cell_release)
                if c > 0:
                    entry.bind(
                        "<FocusOut>",
                        lambda _event, e=entry: (normalize_numeric_entry(e), self._mark_dirty()),
                    )
                else:
                    entry.bind("<FocusOut>", lambda *_: self._mark_dirty())
                
                # Setup enter key handler
                enter_handler = factory.create_enter_handler(row_obj, c, get_row_index, focus_cell)
                entry.bind("<Return>", enter_handler)

            # Insert at specific index
            self.entries.insert(index, row_obj)

            refresh_grid()
            canvas.update_idletasks()
            canvas.configure(scrollregion=canvas.bbox("all"))
            
            # Focus on the first entry of the newly inserted row
            self.entries[index]["entries"][0].focus_set()

        def add_row(values=None):
            add_row_at_index(len(self.entries), values)

        # ---- Seed data ----
        if self.donthuoc and getattr(self.donthuoc, "chidinh_list", None):
            for chi in self.donthuoc.chidinh_list:
                add_row({
                    "entries": [
                        chi.thuoc.Ten if chi.thuoc else "",
                        chi.SangTruocAn or "",
                        chi.SangSauAn or "",
                        chi.TruaTruocAn or "",
                        chi.TruaSauAn or "",
                        chi.ChieuTruocAn or "",
                        chi.ChieuSauAn or "",
                        chi.Toi or "",
                    ],
                    "excluded": bool(getattr(chi, "KhongTinhTien", 0)),
                })
        elif seed_rows:
            for row in seed_rows:
                add_row(row)
        else:
            add_row()

        self._add_row_at_index = add_row_at_index

    def add_row(self, values=None, index=None):
        """Add a row at the end (or at a specific index)"""
        if not hasattr(self, "_add_row_at_index"):
            raise RuntimeError("Table not yet initialized")
        if index is None:
            index = len(self.entries)
        self._add_row_at_index(index, values)

    def get_total(self, price_lookup):
        total = 0.0
        for row in self.entries:
            if row["exclude_from_total"]:
                continue

            name = row["entries"][0].get().strip()
            if not name:
                continue

            price = float(price_lookup.get(name, 0) or 0)
            doses = [safe_float(entry.get().strip()) for entry in row["entries"][1:]]
            total += sum(doses) * price

        return total


    def _mark_dirty(self):
        self.dirty = True
        if self.on_change:
            self.on_change()
