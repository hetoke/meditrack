import tkinter as tk

class AutocompleteEntry(tk.Entry):
    def __init__(self, master=None, fetch_suggestions=None, **kwargs):
        super().__init__(master, **kwargs)
        self.fetch_suggestions = fetch_suggestions
        self.var = tk.StringVar()
        self.config(textvariable=self.var)
        self.var.trace_add("write", self.on_change)
        self.listbox = None
        self.listbox_visible = False
        self._suppress = False

        self.bind("<Escape>", lambda e: self.destroy_listbox())
        self.winfo_toplevel().bind("<Button-1>", self._click_outside, add="+")
        self.bind("<Down>", self.move_down)
        self.bind("<Destroy>", self._cleanup)
        self.bind("<Return>", self._on_entry_return)

    def _cleanup(self, event=None):
        self.destroy_listbox()
        try:
            self.winfo_toplevel().unbind("<Button-1>")
        except Exception:
            pass

    def _click_outside(self, event):
        if self.listbox and event.widget not in (self, self.listbox):
            self.destroy_listbox()

    def _on_entry_return(self, event):
        if self.listbox:
            self._suppress = True
            self.destroy_listbox()
            self._suppress = False
            return "break"

    def destroy_listbox(self):
        if self.listbox:
            self.listbox.destroy()
            self.listbox = None
            self.listbox_visible = False

    def on_change(self, *args):
        if self._suppress:
            return
        self.destroy_listbox()
        value = self.var.get()
        if not value or not self.fetch_suggestions:
            return

        try:
            suggestions = self.fetch_suggestions(value)
        except Exception:
            suggestions = []
        if not suggestions:
            return

        self.listbox = tk.Listbox(self.winfo_toplevel(), height=min(5, len(suggestions)))
        self.listbox_visible = True

        for m in suggestions:
            self.listbox.insert("end", m)

        self.listbox.bind("<Double-Button-1>", self.select_suggestion)
        self.listbox.bind("<Return>", self.select_suggestion)
        self.listbox.bind("<Escape>", lambda e: (self.destroy_listbox(), self.focus_set()))

        x = self.winfo_rootx() - self.winfo_toplevel().winfo_rootx()
        y = self.winfo_rooty() - self.winfo_toplevel().winfo_rooty() + self.winfo_height()
        self.listbox.place(x=x, y=y, width=self.winfo_width())

    def select_suggestion(self, event=None):
        if self.listbox:
            index = self.listbox.curselection()
            index = index[0] if index else self.listbox.index("active")
            value = self.listbox.get(index)
            self._suppress = True
            self.destroy_listbox()
            self.var.set(value)
            self._suppress = False
            self.event_generate("<<AutocompleteSelected>>")
            self.focus_set()
            return "break"
        self.destroy_listbox()
        self.focus_set()

    def move_down(self, event):
        if self.listbox:
            self.listbox.focus()
            self.listbox.selection_set(0)
            self.listbox.activate(0)
            return "break"