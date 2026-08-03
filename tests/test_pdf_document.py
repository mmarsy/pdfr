from pathlib import Path

import fitz
import pytest

from pdfr.pdf_document import PdfDocument


def create_sample_pdf(path: Path) -> None:
    document = fitz.open()
    page = document.new_page(width=200, height=100)
    page.insert_text((36, 54), "Hello pdfr")
    document.save(path)
    document.close()


def test_open_pdf_and_render_page(tmp_path: Path) -> None:
    pdf_path = tmp_path / "sample.pdf"
    create_sample_pdf(pdf_path)

    with PdfDocument.open(pdf_path) as document:
        page_count = document.page_count
        rendered_page = document.render_page(0, zoom=1.0)

    assert page_count == 1
    assert rendered_page.width > 0
    assert rendered_page.height > 0
    assert rendered_page.ppm_data.startswith(b"P6")


def test_render_page_applies_zoom(tmp_path: Path) -> None:
    pdf_path = tmp_path / "sample.pdf"
    create_sample_pdf(pdf_path)

    with PdfDocument.open(pdf_path) as document:
        normal = document.render_page(0, zoom=1.0)
        enlarged = document.render_page(0, zoom=2.0)

    assert enlarged.width > normal.width
    assert enlarged.height > normal.height


def test_open_pdf_rejects_missing_file(tmp_path: Path) -> None:
    with pytest.raises(FileNotFoundError):
        PdfDocument.open(tmp_path / "missing.pdf")
