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
        self.col_widths = [22, 12, 12, 12, 12, 12, 12, 12]

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
        columns = [
            "Thuốc",
            "Sáng trước ăn",
            "Sáng sau ăn",
            "Trưa trước ăn",
            "Trưa sau ăn",
            "Chiều trước ăn",
            "Chiều sau ăn",
            "Tối",
        ]
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

        def on_canvas_configure(event):
            canvas.itemconfigure(window_id, width=event.width)

        def on_frame_configure(event):
            canvas.configure(scrollregion=canvas.bbox("all"))

        canvas.bind("<Configure>", on_canvas_configure)
        self.grid_frame.bind("<Configure>", on_frame_configure)

        # ---- Header row ----
        for c, name in enumerate(columns):
            lbl = tb.Label(
                self.grid_frame,
                text=name,
                anchor="center",
                font=("Quicksand", 11, "bold"),
            )
            if c in sau_an_indices:
                lbl.config(background="#FFC107")
            lbl.grid(row=0, column=c, sticky="nsew", padx=1, pady=1)

        tb.Label(
            self.grid_frame,
            text="Xóa",
            anchor="center",
            font=("Quicksand", 11, "bold"),
        ).grid(row=0, column=len(columns), sticky="nsew", padx=1, pady=1)

        # ---- Row logic ----

        def add_row(values=None):
            row_idx = len(self.entries) + 1
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

                e.grid(row=row_idx, column=c, sticky="nsew", padx=1, pady=1)
                e.bind("<KeyRelease>", lambda *_: self._mark_dirty())
                e.bind("<FocusOut>", lambda *_: self._mark_dirty())

                row_entries.append(e)

            def delete_row():
                for w in row_entries + [btn]:
                    w.destroy()
                if row_entries in self.entries:
                    self.entries.remove(row_entries)
                self.dirty = True
                canvas.update_idletasks()
                canvas.configure(scrollregion=canvas.bbox("all"))

            btn = tb.Button(
                self.grid_frame,
                text="X",
                bootstyle="danger",
                command=delete_row,
            )
            btn.grid(row=row_idx, column=len(columns), sticky="nsew", padx=1, pady=1)

            self.entries.append(row_entries)

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
