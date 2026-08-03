from pathlib import Path

from pdfr.__main__ import parse_args


def test_parse_args_accepts_optional_pdf_path() -> None:
    args = parse_args(["document.pdf"])

    assert args.pdf == Path("document.pdf")


def test_parse_args_allows_no_pdf_path() -> None:
    args = parse_args([])

    assert args.pdf is None
