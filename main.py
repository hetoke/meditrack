import os
import sys
from pathlib import Path
import ttkbootstrap as tb
from tkinter import font as tkfont, messagebox
from ctypes import windll, c_int, byref, sizeof
from medicine import show_thuoc_window
from ui.record.screen import show_ho_so_window
import traceback

def show_primary_window(root: tb.Window, container: tb.Frame) -> None:
    """Render the home screen."""
    for w in container.winfo_children():
        w.destroy()

    tb.Label(
        container,
        text="🏥 Phòng khám Thành Tâm",
        font=("Quicksand", 18, "bold")
    ).pack(pady=30)

    tb.Button(
        container,
        text="💊 Quản lý Thuốc",
        bootstyle="primary",
        command=lambda: show_thuoc_window(root, container, show_primary_window)
    ).pack(pady=20)

    tb.Button(
        container,
        text="🩺 Hồ sơ bệnh nhân",
        bootstyle="primary",
        command=lambda: show_ho_so_window(root, container, show_primary_window)
    ).pack(pady=20)

    tb.Button(
        container,
        text="🚪 Thoát",
        bootstyle="danger",
        command=root.destroy
    ).pack(pady=20)


def main() -> None:
    root = tb.Window(themename="flatly")
    root.title("Phòng khám Thành Tâm")

    # Prevent black flash on minimize/maximize (Windows DWM issue)
    if os.name == "nt":
        try:
            DWMWA_TRANSITIONS_FORCEDISABLED = 3
            hwnd = windll.user32.GetParent(root.winfo_id())
            windll.dwmapi.DwmSetWindowAttribute(
                hwnd, DWMWA_TRANSITIONS_FORCEDISABLED,
                byref(c_int(1)), sizeof(c_int)
            )
        except Exception:
            pass

    root.configure(bg="white")
    root.update_idletasks()

    # --- Load custom TTF font ---
    if getattr(sys, "frozen", False):
        app_dir = Path(sys.executable).parent
    else:
        app_dir = Path(__file__).resolve().parent
    font_path = str(app_dir / "Quicksand-Regular.ttf")
    if os.name == "nt":
        windll.gdi32.AddFontResourceW(font_path)

    # Apply globally (if font is found)
    for f in ["TkDefaultFont", "TkTextFont", "TkHeadingFont"]:
        tkfont.nametofont(f).config(family="Quicksand", size=12)

    container = tb.Frame(root)
    container.pack(fill="both", expand=True)

    style = tb.Style()
    style.theme_use("flatly")

    # Force white background on all frames
    style.configure(".", background="white")

    # --- COMPACT INFO OUTLINE ---
    style.configure(
        "CompactInfo.TButton",
        font=("Quicksand", 9),
        padding=(5, 0),
        anchor="center",
        relief="solid",
        borderwidth=1,
        background=style.colors.bg,  # white
        focuscolor=style.colors.info,
    )
    style.map(
        "CompactInfo.TButton",
        foreground=[
            ("pressed", "#ffffff"),
            ("active", "#ffffff"),  # white text on hover
            ("!disabled", style.colors.info),
        ],
        background=[
            ("pressed", style.colors.info),
            ("active", style.colors.info),  # info color background on hover
            ("!disabled", style.colors.bg),
        ],
        bordercolor=[
            ("pressed", style.colors.info),
            ("active", style.colors.info),
            ("!disabled", style.colors.info),
        ],
    )

    # --- COMPACT DANGER OUTLINE ---
    style.configure(
        "CompactDanger.TButton",
        font=("Quicksand", 9),
        padding=(5, 0),
        anchor="center",
        relief="solid",
        borderwidth=1,
        background=style.colors.bg,
        focuscolor=style.colors.danger,
    )
    style.map(
        "CompactDanger.TButton",
        foreground=[
            ("pressed", "#ffffff"),
            ("active", "#ffffff"),  # white text on hover
            ("!disabled", style.colors.danger),
        ],
        background=[
            ("pressed", style.colors.danger),
            ("active", style.colors.danger),  # danger color background on hover
            ("!disabled", style.colors.bg),
        ],
        bordercolor=[
            ("pressed", style.colors.danger),
            ("active", style.colors.danger),
            ("!disabled", style.colors.danger),
        ],
    )




    # Load the home screen first
    show_primary_window(root, container)

    # Defer maximize until after first frame is painted
    root.after(50, lambda: root.state("zoomed"))

    root.mainloop()


if __name__ == "__main__":
    try:
        main()
    except Exception:
        # Show any errors in a popup if double-clicked
        tb.Window().withdraw()  # hide root
        messagebox.showerror(
            "Application Error",
            "An unexpected error occurred:\n\n" + traceback.format_exc()
        )
        sys.exit(1)
