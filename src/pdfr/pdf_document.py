from __future__ import annotations

from dataclasses import dataclass
from math import ceil
from pathlib import Path
from types import TracebackType

import fitz

from pdfr.consts import DEFAULT_ZOOM, MAX_ZOOM, MIN_ZOOM, ZOOM_FACTOR

__all__ = [
    "DEFAULT_ZOOM",
    "MAX_ZOOM",
    "MIN_ZOOM",
    "PageSize",
    "PdfDocument",
    "RenderedPage",
    "clamp_zoom",
    "zoom_in",
    "zoom_out",
]


def clamp_zoom(value: float) -> float:
    return min(MAX_ZOOM, max(MIN_ZOOM, value))


def zoom_in(value: float) -> float:
    return clamp_zoom(value * ZOOM_FACTOR)


def zoom_out(value: float) -> float:
    return clamp_zoom(value / ZOOM_FACTOR)


@dataclass(frozen=True)
class RenderedPage:
    width: int
    height: int
    ppm_data: bytes


@dataclass(frozen=True)
class PageSize:
    width: int
    height: int


class PdfDocument:
    def __init__(self, path: Path, document: fitz.Document) -> None:
        self.path = path
        self._document = document

    @classmethod
    def open(cls, path: str | Path) -> PdfDocument:
        resolved_path = Path(path).expanduser().resolve()
        if not resolved_path.exists():
            raise FileNotFoundError(f"File does not exist: {resolved_path}")
        if resolved_path.suffix.lower() != ".pdf":
            raise ValueError(f"Expected a PDF file: {resolved_path}")

        document = fitz.open(str(resolved_path))
        if document.page_count == 0:
            document.close()
            raise ValueError("PDF has no pages.")

        return cls(resolved_path, document)

    @property
    def page_count(self) -> int:
        return self._document.page_count

    @property
    def title(self) -> str:
        if self._document.metadata is not None:
            metadata_title = self._document.metadata.get("title", "").strip()
            return metadata_title
        return self.path.name

    def render_page(self, page_index: int, zoom: float) -> RenderedPage:
        if page_index < 0 or page_index >= self.page_count:
            raise IndexError(f"Page index out of range: {page_index}")

        page = self._document.load_page(page_index)
        scale = clamp_zoom(zoom)
        matrix = fitz.Matrix(scale, scale)
        pixmap = page.get_pixmap(matrix=matrix, alpha=False)
        return RenderedPage(
            width=pixmap.width,
            height=pixmap.height,
            ppm_data=pixmap.tobytes("ppm"),
        )

    def page_size(self, page_index: int, zoom: float) -> PageSize:
        if page_index < 0 or page_index >= self.page_count:
            raise IndexError(f"Page index out of range: {page_index}")

        page = self._document.load_page(page_index)
        scale = clamp_zoom(zoom)
        return PageSize(
            width=max(1, ceil(page.rect.width * scale)),
            height=max(1, ceil(page.rect.height * scale)),
        )

    def close(self) -> None:
        self._document.close()

    def __enter__(self) -> PdfDocument:
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_value: BaseException | None,
        traceback: TracebackType | None,
    ) -> None:
        self.close()
