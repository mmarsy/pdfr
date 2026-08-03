import tkinter as tk
from pathlib import Path

import fitz
import pytest

from pdfr.app import PdfReaderApp


def create_sample_pdf(path: Path, page_count: int = 1) -> None:
    document = fitz.open()
    for page_number in range(page_count):
        page = document.new_page(width=200, height=120)
        page.insert_text((30, 60), f"Visible text {page_number + 1}")
    document.save(path)
    document.close()


def create_tk_root_or_skip() -> tk.Tk:
    try:
        root = tk.Tk()
    except tk.TclError as error:
        pytest.skip(f"Tk is not available: {error}")
    root.withdraw()
    return root


def test_photo_from_ppm_accepts_raw_ppm_bytes() -> None:
    root = create_tk_root_or_skip()
    ppm_data = b"P6\n2 1\n255\n" + bytes([255, 0, 0, 0, 255, 0])

    try:
        image = PdfReaderApp._photo_from_ppm(ppm_data)

        assert image.width() == 2
        assert image.height() == 1
    finally:
        root.destroy()


def test_open_pdf_renders_page_images(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    pdf_path = tmp_path / "sample.pdf"
    create_sample_pdf(pdf_path)
    root = create_tk_root_or_skip()
    errors: list[str] = []
    monkeypatch.setattr(
        "pdfr.app.messagebox.showerror",
        lambda _title, message: errors.append(message),
    )

    app = PdfReaderApp(root)
    try:
        app.open_pdf(pdf_path)
        root.update_idletasks()

        assert errors == []
        assert app.document is not None
        assert len(app.page_images) == 1
        assert len(app.canvas.find_all()) >= 2
    finally:
        app.close()


def test_open_pdf_renders_only_visible_page_cache(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    pdf_path = tmp_path / "multi-page.pdf"
    create_sample_pdf(pdf_path, page_count=6)
    root = create_tk_root_or_skip()
    monkeypatch.setattr("pdfr.app.messagebox.showerror", lambda _title, _message: None)

    app = PdfReaderApp(root)
    try:
        app.open_pdf(pdf_path)
        root.update_idletasks()

        assert len(app.page_layouts) == 6
        assert 0 < len(app.page_images) < 6
    finally:
        app.close()
