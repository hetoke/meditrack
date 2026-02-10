import ttkbootstrap as tb
import tkinter as tk
import tkinter.font as tkfont

from intellisense import AutocompleteEntry
from services.prescription_service import fetch_thuoc_suggestions


class PrescriptionTable:
    def __init__(self, parent, donthuoc=None, seed_rows=None, seed_chandoan=None):
        self.frame = tb.Frame(parent, padding=10)

        self.donthuoc = donthuoc
        self.entries = []
        self.dirty = False
        self.zoom = 1.0

        self.grid_frame = None
        self.row_count = 0
        self.col_widths = [22, 6, 6, 6, 6, 6, 6, 6]

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
        columns = ["Thuốc", "Sáng trước ăn", "Sáng sau ăn", "Trưa trước ăn", "Trưa sau ăn", "Chiều trước ăn", "Chiều sau ăn", "Tối"]
        sau_an_indices = {2, 4, 6}

        table_outer = tb.Frame(self.frame)
        table_outer.pack(fill="both", expand=True, padx=20, pady=(2, 6))

        canvas = tk.Canvas(table_outer)
        vsb = tb.Scrollbar(table_outer, orient="vertical", command=canvas.yview)
        canvas.configure(yscrollcommand=vsb.set)

        vsb.pack(side="right", fill="y")
        canvas.pack(side="left", fill="both", expand=True)

        self.grid_frame = tb.Frame(canvas)
        window_id = canvas.create_window((0, 0), window=self.grid_frame, anchor="nw")

        for c in range(len(columns)):
            self.grid_frame.columnconfigure(c * 2, minsize=40)



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
                base = len(columns) * 2

                row["btn_del"].grid(row=i, column=base)
                row["btn_up"].grid(row=i, column=base + 1)
                row["btn_down"].grid(row=i, column=base + 2)

        def add_row(values=None):
            row_entries = []
            values = values or [""] * len(columns)

            for c in range(len(columns)):
                if c == 0:
                    e = AutocompleteEntry(
                        self.grid_frame,
                        fetch_suggestions=fetch_thuoc_suggestions,
                        width=self.col_widths[c],
                    )
                else:
                    e = tk.Entry(self.grid_frame, width=self.col_widths[c])

                if c < len(values):
                    e.insert(0, values[c])
                    if values[c]:
                        self.dirty = True

                if c in sau_an_indices:
                    e.config(bg="#FFC107")

                e.bind("<KeyRelease>", lambda *_: self._mark_dirty())
                e.bind("<FocusOut>", lambda *_: self._mark_dirty())
                e.bind("<Motion>", lambda ev, col=c: on_cell_motion(ev, col))
                e.bind("<Button-1>", lambda ev, col=c: on_cell_press(ev, col))
                e.bind("<B1-Motion>", on_cell_drag)
                e.bind("<ButtonRelease-1>", on_cell_release)

                row_entries.append(e)

            row_obj = {"entries": row_entries}

            btn_del = tb.Button(
                self.grid_frame,
                text="X",
                bootstyle="danger",
                command=lambda ro=row_obj: delete_row(ro),
            )

            btn_up = tb.Button(
                self.grid_frame,
                text="▲",
                width=2,
                command=lambda ro=row_obj: swap_rows(
                    get_row_index(ro),
                    get_row_index(ro) - 1
                ),
            )

            btn_down = tb.Button(
                self.grid_frame,
                text="▼",
                width=2,
                command=lambda ro=row_obj: swap_rows(
                    get_row_index(ro),
                    get_row_index(ro) + 1
                ),
            )

            row_obj.update({
                "btn_del": btn_del,
                "btn_up": btn_up,
                "btn_down": btn_down,
            })

            self.entries.append(row_obj)

            def make_on_enter(row_obj, col):
                def on_enter(event):
                    row_idx = get_row_index(row_obj)

                    # Medicine column (autocomplete handling)
                    if col == 0:
                        widget = event.widget
                        
                        # If autocomplete is showing
                        if widget.listbox_visible and widget.listbox:
                            # Select from listbox and close it
                            widget.select_suggestion()
                            # Move to next cell after brief delay
                            widget.after(50, lambda: focus_cell(row_idx, 1))
                            return "break"
                        
                        # No autocomplete visible, move to next cell immediately
                        focus_cell(row_idx, 1)
                        return "break"

                    # Normal columns (not medicine)
                    next_col = col + 1
                    if next_col < len(columns):
                        # Move to next column in same row
                        focus_cell(row_idx, next_col)
                    else:
                        # Last column → create new row and focus on medicine cell
                        focus_cell(row_idx + 1, 0)

                    return "break"

                return on_enter

            def delete_row(row_obj):
                idx = get_row_index(row_obj)
                for w in row_obj["entries"] + [
                    row_obj["btn_del"],
                    row_obj["btn_up"],
                    row_obj["btn_down"],
                ]:
                    w.destroy()
                self.entries.pop(idx)
                refresh_grid()
                self._mark_dirty()

            def swap_rows(i, j):
                if i < 0 or j < 0 or i >= len(self.entries) or j >= len(self.entries):
                    return
                self.entries[i], self.entries[j] = self.entries[j], self.entries[i]
                refresh_grid()
                self._mark_dirty()

            # **BIND THE ENTER KEY TO EACH ENTRY**
            for c, e in enumerate(row_entries):
                e.bind("<Return>", make_on_enter(row_obj, c))

            refresh_grid()
            canvas.update_idletasks()
            canvas.configure(scrollregion=canvas.bbox("all"))


    
            
            
            canvas.update_idletasks()
            canvas.configure(scrollregion=canvas.bbox("all"))

        # ---- Seed data ----
        if self.donthuoc and getattr(self.donthuoc, "chidinh_list", None):
            for chi in self.donthuoc.chidinh_list:
                add_row([
                    chi.thuoc.Ten if chi.thuoc else "",
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

        tb.Button(
            self.frame,
            text="Thêm dòng",
            bootstyle="success",
            command=lambda: add_row(),
        ).pack(anchor="e", pady=5)

    # -------------------------------------------------
    # Internal
    # -------------------------------------------------

    def _mark_dirty(self):
        self.dirty = True
