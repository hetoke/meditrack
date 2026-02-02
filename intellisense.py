import tkinter as tk


class AutocompleteEntry(tk.Entry):
    def __init__(self, master=None, fetch_suggestions=None, **kwargs):
        super().__init__(master, **kwargs)
        self.fetch_suggestions = fetch_suggestions  # callable: takes current text, returns list
        self.var = tk.StringVar()
        self.config(textvariable=self.var)
        self.var.trace_add("write", self.on_change)
        self.listbox = None
        self.bind("<Return>", self.select_suggestion)
        self.bind("<Down>", self.move_down)
        self.bind("<Destroy>", lambda e: self.destroy_listbox())

    def destroy_listbox(self):
        if self.listbox:
            self.listbox.destroy()
            self.listbox = None

    def on_change(self, *args):
        self.destroy_listbox()
        value = self.var.get()
        if not value or not self.fetch_suggestions:
            return

        # Pass current entry text as query
        try:
            suggestions = self.fetch_suggestions(value)
        except Exception:
            suggestions = []

        matches = [s for s in suggestions if s.lower().startswith(value.lower())]
        if not matches:
            return

        self.listbox = tk.Listbox(self.winfo_toplevel(), height=min(5, len(matches)))
        for m in matches:
            self.listbox.insert("end", m)

        self.listbox.bind("<<ListboxSelect>>", self.select_suggestion)

        x = self.winfo_rootx() - self.winfo_toplevel().winfo_rootx()
        y = self.winfo_rooty() - self.winfo_toplevel().winfo_rooty() + self.winfo_height()
        self.listbox.place(x=x, y=y, width=self.winfo_width())

    def select_suggestion(self, event=None):
        if self.listbox and self.listbox.curselection():
            index = self.listbox.curselection()[0]
            value = self.listbox.get(index)
            self.var.set(value)
        self.destroy_listbox()

    def move_down(self, event):
        if self.listbox:
            self.listbox.focus()
            self.listbox.selection_set(0)
            self.listbox.activate(0)
            self.listbox.bind("<Return>", self.select_suggestion)
