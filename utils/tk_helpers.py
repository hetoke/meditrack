from __future__ import annotations

from typing import Optional, Union

import tkinter as tk


def clear_parents(
    widget: tk.Misc,
    stop_at: Optional[tk.Misc] = None,
    levels: int = 1,
) -> tk.Misc:
    """Destroy all children of `widget`, then optionally walk up `levels`
    parents and return that widget."""
    current: tk.Misc = widget

    for _ in range(levels):
        if current is None or current == stop_at:
            break
        parent = current.master
        current.destroy()
        current = parent

    for child in current.winfo_children():
        child.destroy()

    return current
