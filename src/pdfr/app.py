from __future__ import annotations

import tkinter as tk
from dataclasses import dataclass
from pathlib import Path
from tkinter import filedialog, messagebox, ttk

import fitz

from pdfr import __version__
from pdfr.pdf_document import DEFAULT_ZOOM, PdfDocument, clamp_zoom, zoom_in, zoom_out

PAGE_MARGIN = 20
PAGE_GAP = 22
SCROLL_UNITS = 3
PAGE_RENDER_BUFFER = 1


@dataclass(frozen=True)
class PageLayout:
    page_index: int
    x: int
    y: int
    width: int
    height: int

    @property
    def bottom(self) -> int:
        return self.y + self.height


class PdfReaderApp:
    def __init__(self, root: tk.Tk, initial_path: Path | None = None) -> None:
        self.root = root
        self.root.title(f"pdfr {__version__}")
        self.root.geometry("960x720")
        self.root.minsize(500, 360)

        self.document: PdfDocument | None = None
        self.zoom = DEFAULT_ZOOM
        self.page_layouts: list[PageLayout] = []
        self.page_images: dict[int, tk.PhotoImage] = {}
        self.page_image_items: dict[int, int] = {}

        self.zoom_label: ttk.Label
        self.canvas: tk.Canvas

        self._build_menu()
        self._build_layout()
        self._bind_events()
        self._show_empty_state()

        if initial_path is not None:
            self.root.after(0, lambda: self.open_pdf(initial_path))

    def _build_menu(self) -> None:
        menu = tk.Menu(self.root)

        file_menu = tk.Menu(menu, tearoff=False)
        file_menu.add_command(label="Open...", accelerator="Ctrl+O", command=self.choose_pdf)
        file_menu.add_separator()
        file_menu.add_command(label="Exit", command=self.close)

        view_menu = tk.Menu(menu, tearoff=False)
        view_menu.add_command(label="Zoom In", accelerator="Ctrl++", command=self.increase_zoom)
        view_menu.add_command(label="Zoom Out", accelerator="Ctrl+-", command=self.decrease_zoom)
        view_menu.add_command(label="Actual Size", accelerator="Ctrl+0", command=self.reset_zoom)

        menu.add_cascade(label="File", menu=file_menu)
        menu.add_cascade(label="View", menu=view_menu)
        self.root.config(menu=menu)

    def _build_layout(self) -> None:
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(1, weight=1)

        toolbar = ttk.Frame(self.root, padding=(8, 8, 8, 6))
        toolbar.grid(row=0, column=0, sticky="ew")

        ttk.Button(toolbar, text="Open", command=self.choose_pdf).pack(side="left")
        ttk.Separator(toolbar, orient="vertical").pack(side="left", fill="y", padx=8)
        ttk.Button(toolbar, text="-", width=3, command=self.decrease_zoom).pack(side="left")
        self.zoom_label = ttk.Label(toolbar, text="100%", width=7, anchor="center")
        self.zoom_label.pack(side="left", padx=4)
        ttk.Button(toolbar, text="+", width=3, command=self.increase_zoom).pack(side="left")
        ttk.Button(toolbar, text="1:1", width=4, command=self.reset_zoom).pack(
            side="left",
            padx=(6, 0),
        )

        viewer = ttk.Frame(self.root)
        viewer.grid(row=1, column=0, sticky="nsew")
        viewer.columnconfigure(0, weight=1)
        viewer.rowconfigure(0, weight=1)

        self.canvas = tk.Canvas(viewer, background="#303030", highlightthickness=0)
        y_scrollbar = ttk.Scrollbar(viewer, orient="vertical", command=self._set_yview)
        x_scrollbar = ttk.Scrollbar(viewer, orient="horizontal", command=self.canvas.xview)
        self.canvas.configure(
            yscrollcommand=y_scrollbar.set,
            xscrollcommand=x_scrollbar.set,
            xscrollincrement=18,
            yscrollincrement=18,
        )

        self.canvas.grid(row=0, column=0, sticky="nsew")
        y_scrollbar.grid(row=0, column=1, sticky="ns")
        x_scrollbar.grid(row=1, column=0, sticky="ew")

    def _bind_events(self) -> None:
        self.root.bind_all("<Control-o>", self._choose_pdf_event)
        self.root.bind_all("<Control-O>", self._choose_pdf_event)
        self.root.bind_all("<Control-plus>", self._increase_zoom_event)
        self.root.bind_all("<Control-equal>", self._increase_zoom_event)
        self.root.bind_all("<Control-minus>", self._decrease_zoom_event)
        self.root.bind_all("<Control-0>", self._reset_zoom_event)
        self.root.bind_all("<Up>", self._arrow_scroll_event)
        self.root.bind_all("<Down>", self._arrow_scroll_event)
        self.root.bind_all("<Left>", self._arrow_scroll_event)
        self.root.bind_all("<Right>", self._arrow_scroll_event)
        self.root.protocol("WM_DELETE_WINDOW", self.close)

        self.canvas.bind("<MouseWheel>", self._mouse_wheel_event)
        self.canvas.bind("<Button-4>", self._mouse_wheel_event)
        self.canvas.bind("<Button-5>", self._mouse_wheel_event)
        self.canvas.bind("<Configure>", self._canvas_configure_event)
        self.canvas.bind("<ButtonPress-1>", self._start_drag_event)
        self.canvas.bind("<B1-Motion>", self._drag_event)
        self.canvas.bind("<ButtonRelease-1>", self._end_drag_event)

    def choose_pdf(self) -> None:
        initial_dir = str(self.document.path.parent) if self.document else None
        selected_path = filedialog.askopenfilename(
            title="Open PDF",
            initialdir=initial_dir,
            filetypes=[("PDF files", "*.pdf"), ("All files", "*.*")],
        )
        if selected_path:
            self.open_pdf(Path(selected_path))

    def open_pdf(self, path: str | Path) -> None:
        try:
            next_document = PdfDocument.open(path)
        except (FileNotFoundError, ValueError, fitz.FileDataError, RuntimeError) as error:
            messagebox.showerror("pdfr", f"Could not open PDF:\n{error}")
            return

        previous_document = self.document
        previous_zoom = self.zoom

        self.document = next_document
        self.zoom = DEFAULT_ZOOM
        try:
            self._render_document(preserve_scroll=False)
        except (fitz.FileDataError, RuntimeError, tk.TclError) as error:
            next_document.close()
            self.document = previous_document
            self.zoom = previous_zoom
            if self.document is None:
                self._show_empty_state()
            else:
                self._render_document(preserve_scroll=False)
            messagebox.showerror("pdfr", f"Could not render PDF:\n{error}")
            return

        if previous_document is not None:
            previous_document.close()
        self._update_title()

    def increase_zoom(self) -> None:
        self._set_zoom(zoom_in(self.zoom))

    def decrease_zoom(self) -> None:
        self._set_zoom(zoom_out(self.zoom))

    def reset_zoom(self) -> None:
        self._set_zoom(DEFAULT_ZOOM)

    def close(self) -> None:
        if self.document is not None:
            self.document.close()
            self.document = None
        self.root.destroy()

    def _set_zoom(self, zoom: float) -> None:
        next_zoom = clamp_zoom(zoom)
        if next_zoom == self.zoom:
            return
        self.zoom = next_zoom
        self._render_document(preserve_scroll=True)

    def _render_document(self, preserve_scroll: bool) -> None:
        if self.document is None:
            self._show_empty_state()
            return

        y_fraction = self.canvas.yview()[0] if preserve_scroll else 0.0
        self.root.config(cursor="watch")
        self.root.update_idletasks()

        self.canvas.delete("all")
        self.page_images.clear()
        self.page_image_items.clear()
        self.page_layouts.clear()
        y_position = PAGE_GAP
        max_width = 0

        try:
            for page_index in range(self.document.page_count):
                page_size = self.document.page_size(page_index, self.zoom)

                x_position = PAGE_MARGIN
                self.page_layouts.append(
                    PageLayout(
                        page_index=page_index,
                        x=x_position,
                        y=y_position,
                        width=page_size.width,
                        height=page_size.height,
                    )
                )
                self.canvas.create_rectangle(
                    x_position - 1,
                    y_position - 1,
                    x_position + page_size.width + 1,
                    y_position + page_size.height + 1,
                    fill="#f7f7f7",
                    outline="#1f1f1f",
                )
                self.canvas.create_text(
                    x_position + 12,
                    y_position + 12,
                    text=f"Page {page_index + 1}",
                    fill="#777777",
                    anchor="nw",
                )

                y_position += page_size.height + PAGE_GAP
                max_width = max(max_width, page_size.width)
        finally:
            self.root.config(cursor="")

        self.canvas.configure(
            scrollregion=(
                0,
                0,
                max_width + (PAGE_MARGIN * 2),
                max(y_position, self.canvas.winfo_height()),
            ),
        )
        self.canvas.yview_moveto(y_fraction)
        self._render_visible_pages(raise_errors=True)
        self._update_zoom_label()

    def _show_empty_state(self) -> None:
        self.canvas.delete("all")
        self.page_images.clear()
        self.page_image_items.clear()
        self.page_layouts.clear()
        self.canvas.configure(scrollregion=(0, 0, 800, 600))
        self.canvas.create_text(
            400,
            280,
            text="Open PDF",
            fill="#e0e0e0",
            font=("Segoe UI", 22, "bold"),
        )
        self._update_zoom_label()

    def _update_title(self) -> None:
        if self.document is None:
            self.root.title(f"pdfr {__version__}")
            return
        self.root.title(f"{self.document.title} - pdfr")

    def _update_zoom_label(self) -> None:
        self.zoom_label.configure(text=f"{round(self.zoom * 100)}%")

    @staticmethod
    def _photo_from_ppm(ppm_data: bytes) -> tk.PhotoImage:
        return tk.PhotoImage(data=ppm_data, format="PPM")

    def _set_yview(self, *args: object) -> None:
        self.canvas.yview(*args)
        self._render_visible_pages()

    def _render_visible_pages(self, *, raise_errors: bool = False) -> None:
        if self.document is None or not self.page_layouts:
            return

        visible_indexes = self._visible_page_indexes()
        self._discard_hidden_page_images(visible_indexes)

        try:
            for page_index in sorted(visible_indexes):
                if page_index in self.page_images:
                    continue

                layout = self.page_layouts[page_index]
                rendered_page = self.document.render_page(page_index, self.zoom)
                photo = self._photo_from_ppm(rendered_page.ppm_data)
                self.page_images[page_index] = photo
                self.page_image_items[page_index] = self.canvas.create_image(
                    layout.x,
                    layout.y,
                    image=photo,
                    anchor="nw",
                )
        except (fitz.FileDataError, RuntimeError, tk.TclError) as error:
            if raise_errors:
                raise
            messagebox.showerror("pdfr", f"Could not render PDF page:\n{error}")

    def _visible_page_indexes(self) -> set[int]:
        if not self.page_layouts:
            return set()

        top = self.canvas.canvasy(0)
        bottom = self.canvas.canvasy(max(1, self.canvas.winfo_height()))
        visible_indexes = {
            layout.page_index
            for layout in self.page_layouts
            if layout.bottom >= top and layout.y <= bottom
        }

        if not visible_indexes:
            return {0}

        buffered_indexes: set[int] = set()
        for page_index in visible_indexes:
            start = max(0, page_index - PAGE_RENDER_BUFFER)
            stop = min(len(self.page_layouts), page_index + PAGE_RENDER_BUFFER + 1)
            buffered_indexes.update(range(start, stop))
        return buffered_indexes

    def _discard_hidden_page_images(self, visible_indexes: set[int]) -> None:
        for page_index in list(self.page_images):
            if page_index in visible_indexes:
                continue

            image_item = self.page_image_items.pop(page_index, None)
            if image_item is not None:
                self.canvas.delete(image_item)
            del self.page_images[page_index]

    def _choose_pdf_event(self, _event: tk.Event) -> str:
        self.choose_pdf()
        return "break"

    def _increase_zoom_event(self, _event: tk.Event) -> str:
        self.increase_zoom()
        return "break"

    def _decrease_zoom_event(self, _event: tk.Event) -> str:
        self.decrease_zoom()
        return "break"

    def _reset_zoom_event(self, _event: tk.Event) -> str:
        self.reset_zoom()
        return "break"

    def _arrow_scroll_event(self, event: tk.Event) -> str:
        if event.keysym == "Up":
            self.canvas.yview_scroll(-SCROLL_UNITS, "units")
        elif event.keysym == "Down":
            self.canvas.yview_scroll(SCROLL_UNITS, "units")
        elif event.keysym == "Left":
            self.canvas.xview_scroll(-SCROLL_UNITS, "units")
        elif event.keysym == "Right":
            self.canvas.xview_scroll(SCROLL_UNITS, "units")
        self._render_visible_pages()
        return "break"

    def _mouse_wheel_event(self, event: tk.Event) -> str:
        if getattr(event, "num", None) == 4 or getattr(event, "delta", 0) > 0:
            self.canvas.yview_scroll(-SCROLL_UNITS, "units")
        else:
            self.canvas.yview_scroll(SCROLL_UNITS, "units")
        self._render_visible_pages()
        return "break"

    def _canvas_configure_event(self, _event: tk.Event) -> None:
        self._render_visible_pages()

    def _start_drag_event(self, event: tk.Event) -> None:
        self.canvas.scan_mark(event.x, event.y)
        self.canvas.configure(cursor="fleur")

    def _drag_event(self, event: tk.Event) -> None:
        self.canvas.scan_dragto(event.x, event.y, gain=1)
        self._render_visible_pages()

    def _end_drag_event(self, _event: tk.Event) -> None:
        self.canvas.configure(cursor="")


def run(initial_path: Path | None = None) -> None:
    root = tk.Tk()
    PdfReaderApp(root, initial_path)
    root.mainloop()
