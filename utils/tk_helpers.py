def clear_parents(widget, stop_at=None, levels=1):
    """
    Destroy all children of `widget`, then optionally walk up `levels`
    parents and return that widget.
    """
    current = widget

    for _ in range(levels):
        if current is None or current == stop_at:
            break
        parent = current.master
        current.destroy()
        current = parent

    for child in current.winfo_children():
        child.destroy()

    return current
