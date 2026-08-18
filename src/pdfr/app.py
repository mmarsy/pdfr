from __future__ import annotations

import tkinter as tk
from dataclasses import dataclass
from pathlib import Path
from tkinter import filedialog, messagebox, ttk

import fitz

from pdfr import __version__
from pdfr.consts import PAGE_GAP, PAGE_MARGIN, PAGE_RENDER_BUFFER, SCROLL_UNITS, DEFAULT_ZOOM
from pdfr.pdf_document import PdfDocument, clamp_zoom, zoom_in, zoom_out
from pdfr.storage import AppStorage, DocumentIdentity, ViewerState, document_identity


@dataclass
class PageLayout:
    page_index: int
    x: int
    y: int
    width: int
    height: int

    @property
    def bottom(self) -> int:
        return self.y + self.height


class PdfTab:
    def __init__(
        self,
        parent: tk.Widget,
        document: PdfDocument,
        initial_state: ViewerState | None = None,
    ) -> None:
        self.document = document
        self.zoom = clamp_zoom(initial_state.zoom) if initial_state is not None else DEFAULT_ZOOM
        self.page_layouts: list[PageLayout] = []
        self.page_images: dict[int, tk.PhotoImage] = {}
        self.page_image_items: dict[int, int] = {}
        self.page_rect_items: dict[int, int] = {}
        self.page_label_items: dict[int, int] = {}
        self._last_canvas_width = 0
        self._initial_yview = initial_state.yview if initial_state is not None else 0.0

        self.frame = ttk.Frame(parent)
        self.frame.columnconfigure(0, weight=1)
        self.frame.rowconfigure(0, weight=1)

        self.canvas = tk.Canvas(self.frame, background="#303030", highlightthickness=0)
        y_scrollbar = ttk.Scrollbar(self.frame, orient="vertical", command=self._set_yview)
        x_scrollbar = ttk.Scrollbar(self.frame, orient="horizontal", command=self.canvas.xview)
        self.canvas.configure(
            yscrollcommand=y_scrollbar.set,
            xscrollcommand=x_scrollbar.set,
            xscrollincrement=18,
            yscrollincrement=18,
        )

        self.canvas.grid(row=0, column=0, sticky="nsew")
        y_scrollbar.grid(row=0, column=1, sticky="ns")
        x_scrollbar.grid(row=1, column=0, sticky="ew")

        self.canvas.bind("<MouseWheel>", self._mouse_wheel_event)
        self.canvas.bind("<Button-4>", self._mouse_wheel_event)
        self.canvas.bind("<Button-5>", self._mouse_wheel_event)
        self.canvas.bind("<Configure>", self._canvas_configure_event)
        self.canvas.bind("<ButtonPress-1>", self._start_drag_event)
        self.canvas.bind("<B1-Motion>", self._drag_event)
        self.canvas.bind("<ButtonRelease-1>", self._end_drag_event)

        self._render_document(preserve_scroll=False)
        self.canvas.yview_moveto(self._initial_yview)
        self._render_visible_pages()

    @property
    def title(self) -> str:
        return self.document.title

    def focus(self) -> None:
        self.canvas.focus_set()
        self._render_visible_pages()

    def close(self) -> None:
        self.document.close()
        self.frame.destroy()

    def increase_zoom(self) -> None:
        self._set_zoom(zoom_in(self.zoom))

    def decrease_zoom(self) -> None:
        self._set_zoom(zoom_out(self.zoom))

    def reset_zoom(self) -> None:
        self._set_zoom(DEFAULT_ZOOM)

    def scroll_by_key(self, keysym: str) -> None:
        if keysym == "Up":
            self.canvas.yview_scroll(-SCROLL_UNITS, "units")
        elif keysym == "Down":
            self.canvas.yview_scroll(SCROLL_UNITS, "units")
        elif keysym == "Left":
            self.scroll_to_relative_page(-1)
        elif keysym == "Right":
            self.scroll_to_relative_page(1)
        self._render_visible_pages()

    def scroll_to_relative_page(self, offset: int) -> None:
        if not self.page_layouts:
            return

        current_index = self.current_page_index()
        next_index = min(max(current_index + offset, 0), len(self.page_layouts) - 1)
        self.scroll_to_page(next_index)

    def scroll_to_page(self, page_index: int) -> None:
        if not self.page_layouts:
            return

        page_index = min(max(page_index, 0), len(self.page_layouts) - 1)
        scrollregion = self.canvas.cget("scrollregion").split()
        total_height = float(scrollregion[3]) if len(scrollregion) == 4 else 1.0
        target_y = self.page_layouts[page_index].y
        self.canvas.yview_moveto(min(max(target_y / max(1.0, total_height), 0.0), 1.0))
        self._render_visible_pages()

    def current_page_index(self) -> int:
        if not self.page_layouts:
            return 0

        top = self.canvas.canvasy(0)
        return min(
            range(len(self.page_layouts)),
            key=lambda index: abs(self.page_layouts[index].y - top),
        )

    def viewer_state(self) -> ViewerState:
        return ViewerState(
            zoom=self.zoom,
            yview=float(self.canvas.yview()[0]),
            current_page=self.current_page_index(),
        )

    def _set_zoom(self, zoom: float) -> None:
        next_zoom = clamp_zoom(zoom)
        if next_zoom == self.zoom:
            return
        self.zoom = next_zoom
        self._render_document(preserve_scroll=True)

    def _render_document(self, preserve_scroll: bool) -> None:
        y_fraction = self.canvas.yview()[0] if preserve_scroll else 0.0
        self.canvas.delete("all")
        self.page_images.clear()
        self.page_image_items.clear()
        self.page_rect_items.clear()
        self.page_label_items.clear()
        self.page_layouts.clear()

        y_position = PAGE_GAP
        max_width = 0

        for page_index in range(self.document.page_count):
            page_size = self.document.page_size(page_index, self.zoom)
            x_position = self._page_x(page_size.width)
            self.page_layouts.append(
                PageLayout(
                    page_index=page_index,
                    x=x_position,
                    y=y_position,
                    width=page_size.width,
                    height=page_size.height,
                )
            )
            self.page_rect_items[page_index] = self.canvas.create_rectangle(
                x_position - 1,
                y_position - 1,
                x_position + page_size.width + 1,
                y_position + page_size.height + 1,
                fill="#f7f7f7",
                outline="#1f1f1f",
            )
            self.page_label_items[page_index] = self.canvas.create_text(
                x_position + 12,
                y_position + 12,
                text=f"Page {page_index + 1}",
                fill="#777777",
                anchor="nw",
            )

            y_position += page_size.height + PAGE_GAP
            max_width = max(max_width, page_size.width)

        self._configure_scrollregion(max_width=max_width, total_height=y_position)
        self.canvas.yview_moveto(y_fraction)
        self._render_visible_pages(raise_errors=True)

    def _page_x(self, page_width: int) -> int:
        canvas_width = max(1, self.canvas.winfo_width())
        return max(PAGE_MARGIN, (canvas_width - page_width) // 2)

    def _configure_scrollregion(self, *, max_width: int, total_height: int) -> None:
        canvas_width = max(1, self.canvas.winfo_width())
        self.canvas.configure(
            scrollregion=(
                0,
                0,
                max(max_width + (PAGE_MARGIN * 2), canvas_width),
                max(total_height, self.canvas.winfo_height()),
            ),
        )

    def _recenter_pages(self) -> None:
        if not self.page_layouts:
            return

        max_width = 0
        total_height = PAGE_GAP
        for layout in self.page_layouts:
            next_x = self._page_x(layout.width)
            delta_x = next_x - layout.x
            layout.x = next_x
            max_width = max(max_width, layout.width)
            total_height = max(total_height, layout.bottom + PAGE_GAP)

            if delta_x == 0:
                continue

            self.canvas.move(self.page_rect_items[layout.page_index], delta_x, 0)
            self.canvas.move(self.page_label_items[layout.page_index], delta_x, 0)
            image_item = self.page_image_items.get(layout.page_index)
            if image_item is not None:
                self.canvas.move(image_item, delta_x, 0)

        self._configure_scrollregion(max_width=max_width, total_height=total_height)

    @staticmethod
    def _photo_from_ppm(ppm_data: bytes) -> tk.PhotoImage:
        return tk.PhotoImage(data=ppm_data, format="PPM")

    def _set_yview(self, *args: object) -> None:
        self.canvas.yview(*args)
        self._render_visible_pages()

    def _render_visible_pages(self, *, raise_errors: bool = False) -> None:
        if not self.page_layouts:
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
        except (fitz.FileDataError, RuntimeError, tk.TclError):
            if raise_errors:
                raise
            messagebox.showerror("pdfr", "Could not render PDF page.")

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

    def _mouse_wheel_event(self, event: tk.Event) -> str:
        if getattr(event, "num", None) == 4 or getattr(event, "delta", 0) > 0:
            self.canvas.yview_scroll(-SCROLL_UNITS, "units")
        else:
            self.canvas.yview_scroll(SCROLL_UNITS, "units")
        self._render_visible_pages()
        return "break"

    def _canvas_configure_event(self, _event: tk.Event) -> None:
        canvas_width = self.canvas.winfo_width()
        if canvas_width != self._last_canvas_width:
            self._last_canvas_width = canvas_width
            self._recenter_pages()
        self._render_visible_pages()

    def _start_drag_event(self, event: tk.Event) -> None:
        self.canvas.scan_mark(event.x, event.y)
        self.canvas.configure(cursor="fleur")

    def _drag_event(self, event: tk.Event) -> None:
        self.canvas.scan_dragto(event.x, event.y, gain=1)
        self._render_visible_pages()

    def _end_drag_event(self, _event: tk.Event) -> None:
        self.canvas.configure(cursor="")


class PdfReaderApp:
    def __init__(self, root: tk.Tk, initial_path: Path | None = None) -> None:
        self.root = root
        self.root.title(f"pdfr {__version__}")
        self.root.state("zoomed")
        self.root.geometry("960x720")
        self.root.minsize(500, 360)
        self.tabs: dict[str, PdfTab] = {}
        self.tab_documents: dict[str, DocumentIdentity] = {}
        self.storage = AppStorage()

        self.zoom_label: ttk.Label
        self.notebook: ttk.Notebook
        self.empty_frame: ttk.Frame

        self._build_menu()
        self._build_layout()
        self._bind_events()
        self._show_empty_state()

        if initial_path is not None:
            self.root.after(0, lambda: self.open_pdf(initial_path))

    @property
    def document(self) -> PdfDocument | None:
        tab = self.current_tab()
        return tab.document if tab is not None else None

    @property
    def page_layouts(self) -> list[PageLayout]:
        tab = self.current_tab()
        return tab.page_layouts if tab is not None else []

    @property
    def page_images(self) -> dict[int, tk.PhotoImage]:
        tab = self.current_tab()
        return tab.page_images if tab is not None else {}

    @property
    def canvas(self) -> tk.Canvas:
        tab = self.current_tab()
        if tab is None:
            raise RuntimeError("No active PDF tab.")
        return tab.canvas

    @staticmethod
    def _photo_from_ppm(ppm_data: bytes) -> tk.PhotoImage:
        return PdfTab._photo_from_ppm(ppm_data)

    def _build_menu(self) -> None:
        menu = tk.Menu(self.root)

        file_menu = tk.Menu(menu, tearoff=False)
        file_menu.add_command(label="Open...", accelerator="Ctrl+O", command=self.choose_pdf)
        file_menu.add_command(
            label="Close Tab",
            accelerator="Ctrl+W",
            command=self.close_current_tab,
        )
        file_menu.add_separator()
        file_menu.add_command(label="Exit", command=self.close)

        view_menu = tk.Menu(menu, tearoff=False)
        view_menu.add_command(label="Zoom In", accelerator="Ctrl++", command=self.increase_zoom)
        view_menu.add_command(label="Zoom Out", accelerator="Ctrl+-", command=self.decrease_zoom)
        view_menu.add_command(label="Actual Size", accelerator="Ctrl+0", command=self.reset_zoom)
        view_menu.add_separator()
        view_menu.add_command(
            label="Previous Tab",
            accelerator="Ctrl+Shift+Tab",
            command=self.previous_tab,
        )
        view_menu.add_command(label="Next Tab", accelerator="Ctrl+Tab", command=self.next_tab)

        menu.add_cascade(label="File", menu=file_menu)
        menu.add_cascade(label="View", menu=view_menu)
        self.root.config(menu=menu)

    def _build_layout(self) -> None:
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(1, weight=1)

        toolbar = ttk.Frame(self.root, padding=(8, 8, 8, 6))
        toolbar.grid(row=0, column=0, sticky="ew")

        ttk.Button(toolbar, text="Open", command=self.choose_pdf).pack(side="left")
        ttk.Button(toolbar, text="Close", command=self.close_current_tab).pack(
            side="left",
            padx=(6, 0),
        )
        ttk.Separator(toolbar, orient="vertical").pack(side="left", fill="y", padx=8)
        ttk.Button(toolbar, text="-", width=3, command=self.decrease_zoom).pack(side="left")
        self.zoom_label = ttk.Label(toolbar, text="-", width=7, anchor="center")
        self.zoom_label.pack(side="left", padx=4)
        ttk.Button(toolbar, text="+", width=3, command=self.increase_zoom).pack(side="left")
        ttk.Button(toolbar, text="1:1", width=4, command=self.reset_zoom).pack(
            side="left",
            padx=(6, 0),
        )
        ttk.Separator(toolbar, orient="vertical").pack(side="left", fill="y", padx=8)
        ttk.Button(toolbar, text="Prev Tab", command=self.previous_tab).pack(side="left")
        ttk.Button(toolbar, text="Next Tab", command=self.next_tab).pack(
            side="left",
            padx=(6, 0),
        )

        viewer_stack = ttk.Frame(self.root)
        viewer_stack.grid(row=1, column=0, sticky="nsew")
        viewer_stack.columnconfigure(0, weight=1)
        viewer_stack.rowconfigure(0, weight=1)

        self.empty_frame = ttk.Frame(viewer_stack)
        self.empty_frame.grid(row=0, column=0, sticky="nsew")
        self.empty_frame.columnconfigure(0, weight=1)
        self.empty_frame.rowconfigure(0, weight=1)
        ttk.Label(
            self.empty_frame,
            text="Open PDF",
            font=("Segoe UI", 22, "bold"),
            anchor="center",
        ).grid(row=0, column=0, sticky="nsew")

        self.notebook = ttk.Notebook(viewer_stack)
        self.notebook.grid(row=0, column=0, sticky="nsew")
        self.notebook.bind("<<NotebookTabChanged>>", self._notebook_tab_changed_event)
        self.notebook.bind("<ButtonRelease-1>", self._notebook_button_release_event)

    def _bind_events(self) -> None:
        self.root.bind_all("<Control-o>", self._choose_pdf_event)
        self.root.bind_all("<Control-O>", self._choose_pdf_event)
        self.root.bind_all("<Control-w>", self._close_current_tab_event)
        self.root.bind_all("<Control-W>", self._close_current_tab_event)
        self.root.bind_all("<Control-plus>", self._increase_zoom_event)
        self.root.bind_all("<Control-equal>", self._increase_zoom_event)
        self.root.bind_all("<Control-minus>", self._decrease_zoom_event)
        self.root.bind_all("<Control-0>", self._reset_zoom_event)
        self.root.bind_all("<Control-Tab>", self._next_tab_event)
        self.root.bind_all("<Control-Shift-Tab>", self._previous_tab_event)
        self.root.bind_all("<Control-ISO_Left_Tab>", self._previous_tab_event)

        # Arrows
        self.root.bind_all("<Up>", self._arrow_scroll_event)
        self.root.bind_all("<Down>", self._arrow_scroll_event)
        self.root.bind_all("<Left>", self._arrow_scroll_event)
        self.root.bind_all("<Right>", self._arrow_scroll_event)

        # Close
        self.root.protocol("WM_DELETE_WINDOW", self.close)

    def choose_pdf(self) -> None:
        current_tab = self.current_tab()
        options: dict[str, object] = {
            "title": "Open PDF",
            "filetypes": [("PDF files", "*.pdf"), ("All files", "*.*")],
        }
        if current_tab is not None:
            options["initialdir"] = str(current_tab.document.path.parent)

        selected_path = filedialog.askopenfilename(**options)
        if selected_path:
            self.open_pdf(Path(selected_path))

    def open_pdf(self, path: str | Path) -> PdfTab | None:
        try:
            document = PdfDocument.open(path)
        except (FileNotFoundError, ValueError, fitz.FileDataError, RuntimeError) as error:
            messagebox.showerror("pdfr", f"Could not open PDF:\n{error}")
            return None

        identity = document_identity(document.path)
        initial_state = self.storage.load_viewer_state(identity)

        try:
            tab = PdfTab(self.notebook, document, initial_state=initial_state)
        except (fitz.FileDataError, RuntimeError, tk.TclError) as error:
            document.close()
            messagebox.showerror("pdfr", f"Could not render PDF:\n{error}")
            return None

        frame_id = str(tab.frame)
        self.tabs[frame_id] = tab
        self.tab_documents[frame_id] = identity
        self.notebook.add(tab.frame, text=f"{tab.document.path.name}  x")
        self.notebook.select(tab.frame)
        self._show_tabs()
        self._update_title()
        self._update_zoom_label()
        tab.focus()
        return tab

    def current_tab(self) -> PdfTab | None:
        selected_tab = self.notebook.select()
        if not selected_tab:
            return None
        return self.tabs.get(selected_tab)

    def increase_zoom(self) -> None:
        tab = self.current_tab()
        if tab is None:
            return
        tab.increase_zoom()
        self._update_zoom_label()

    def decrease_zoom(self) -> None:
        tab = self.current_tab()
        if tab is None:
            return
        tab.decrease_zoom()
        self._update_zoom_label()

    def reset_zoom(self) -> None:
        tab = self.current_tab()
        if tab is None:
            return
        tab.reset_zoom()
        self._update_zoom_label()

    def next_tab(self) -> None:
        self._select_relative_tab(1)

    def previous_tab(self) -> None:
        self._select_relative_tab(-1)

    def close_current_tab(self) -> None:
        selected_tab = self.notebook.select()
        if not selected_tab:
            return
        self.close_tab(selected_tab)

    def close_tab(self, tab_id: str) -> None:
        tab = self.tabs.pop(tab_id, None)
        if tab is None:
            return

        identity = self.tab_documents.pop(tab_id, None)
        if identity is not None:
            self._save_viewer_state(identity, tab)

        self.notebook.forget(tab_id)
        tab.close()

        if self.notebook.index("end") == 0:
            self._show_empty_state()
        else:
            self._show_tabs()
        self._update_title()
        self._update_zoom_label()

    def close(self) -> None:
        for frame_id, tab in list(self.tabs.items()):
            self.tabs.pop(frame_id, None)
            identity = self.tab_documents.pop(frame_id, None)
            if identity is not None:
                self._save_viewer_state(identity, tab)
            tab.close()
        self.root.destroy()

    def _save_viewer_state(self, identity: DocumentIdentity, tab: PdfTab) -> None:
        try:
            self.storage.save_viewer_state(identity, tab.viewer_state())
        except OSError:
            return

    def _select_relative_tab(self, offset: int) -> None:
        tab_count = self.notebook.index("end")
        if tab_count == 0:
            return

        current_index = self.notebook.index("current")
        next_index = (current_index + offset) % tab_count
        self.notebook.select(next_index)
        selected_tab = self.current_tab()
        if selected_tab is not None:
            selected_tab.focus()
        self._update_title()
        self._update_zoom_label()

    def _show_tabs(self) -> None:
        self.empty_frame.grid_remove()
        self.notebook.grid()

    def _show_empty_state(self) -> None:
        self.notebook.grid_remove()
        self.empty_frame.grid()
        self._update_title()
        self._update_zoom_label()

    def _update_title(self) -> None:
        tab = self.current_tab()
        if tab is None:
            self.root.title(f"pdfr {__version__}")
            return
        self.root.title(f"{tab.title} - pdfr")

    def _update_zoom_label(self) -> None:
        tab = self.current_tab()
        self.zoom_label.configure(text=f"{round(tab.zoom * 100)}%" if tab is not None else "-")

    def _choose_pdf_event(self, _event: tk.Event) -> str:
        self.choose_pdf()
        return "break"

    def _close_current_tab_event(self, _event: tk.Event) -> str:
        self.close_current_tab()
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

    def _next_tab_event(self, _event: tk.Event) -> str:
        self.next_tab()
        return "break"

    def _previous_tab_event(self, _event: tk.Event) -> str:
        self.previous_tab()
        return "break"

    def _arrow_scroll_event(self, event: tk.Event) -> str:
        tab = self.current_tab()
        if tab is not None:
            tab.scroll_by_key(event.keysym)
        return "break"

    def _notebook_tab_changed_event(self, _event: tk.Event) -> None:
        tab = self.current_tab()
        if tab is not None:
            tab.focus()
        self._update_title()
        self._update_zoom_label()

    def _notebook_button_release_event(self, event: tk.Event) -> None:
        tab_id = self._tab_close_target(event)
        if tab_id is not None:
            self.close_tab(tab_id)

    def _tab_close_target(self, event: tk.Event) -> str | None:
        try:
            index = self.notebook.index(f"@{event.x},{event.y}")
            x, y, width, height = self.notebook.bbox(index)
        except tk.TclError:
            return None

        close_area_width = 24
        if event.x < x + width - close_area_width or event.x > x + width:
            return None
        if event.y < y or event.y > y + height:
            return None
        return self.notebook.tabs()[index]


def run(initial_path: Path | None = None) -> None:
    root = tk.Tk()
    PdfReaderApp(root, initial_path)
    root.mainloop()
