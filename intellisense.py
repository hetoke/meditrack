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
        
        # Bind events
        self.bind("<FocusOut>", self._on_focus_out)
        self.bind("<Escape>", lambda e: self.destroy_listbox())
        self.winfo_toplevel().bind("<Button-1>", self._click_outside, add="+")
        self.bind("<Down>", self.move_down)
        self.bind("<Destroy>", lambda e: self.destroy_listbox())
        
    def _on_focus_out(self, event):
        # Delay destruction to allow selection to complete
        self.after(100, self._delayed_destroy)
        
    def _delayed_destroy(self):
        # Only destroy if entry still doesn't have focus
        if self.focus_get() != self:
            self.destroy_listbox()
    
    def _click_outside(self, event):
        if self.listbox and event.widget not in (self, self.listbox):
            self.destroy_listbox()
    
    def destroy_listbox(self):
        if self.listbox:
            self.listbox.destroy()
            self.listbox = None
            self.listbox_visible = False
    
    def on_change(self, *args):
        self.destroy_listbox()
        value = self.var.get()
        if not value or not self.fetch_suggestions:
            return
        
        try:
            suggestions = self.fetch_suggestions(value)
        except Exception:
            suggestions = []
        
        matches = [s for s in suggestions if s.lower().startswith(value.lower())]
        if not matches:
            return
        
        self.listbox = tk.Listbox(self.winfo_toplevel(), height=min(5, len(matches)))
        self.listbox_visible = True
        
        for m in matches:
            self.listbox.insert("end", m)
        
        self.listbox.bind("<Double-Button-1>", self.select_suggestion)
        self.listbox.bind("<Return>", self.select_suggestion)
        
        x = self.winfo_rootx() - self.winfo_toplevel().winfo_rootx()
        y = self.winfo_rooty() - self.winfo_toplevel().winfo_rooty() + self.winfo_height()
        self.listbox.place(x=x, y=y, width=self.winfo_width())
    
    def select_suggestion(self, event=None):
        if self.listbox and self.listbox.curselection():
            index = self.listbox.curselection()[0]
            value = self.listbox.get(index)
            self.var.set(value)
            self.destroy_listbox()
            self.event_generate("<<AutocompleteSelected>>")
            self.focus_set()  # Return focus to entry
            return "break"
        self.destroy_listbox()
    
    def move_down(self, event):
        if self.listbox:
            self.listbox.focus()
            self.listbox.selection_set(0)
            self.listbox.activate(0)
            return "break"