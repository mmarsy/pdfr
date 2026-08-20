from __future__ import annotations

import argparse
import traceback
from collections.abc import Sequence
from pathlib import Path

from pdfr import __version__
from pdfr.storage import app_data_dir


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        prog="pdfr",
        description="Open a PDF in a lightweight desktop reader.",
    )
    parser.add_argument("pdf", nargs="?", type=Path, help="PDF file to open.")
    parser.add_argument("--version", action="version", version=f"%(prog)s {__version__}")
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> int:
    try:
        args = parse_args(argv)

        from pdfr.app import run

        run(args.pdf)
        return 0
    except SystemExit:
        raise
    except Exception as error:
        _report_startup_error(error)
        return 1


def _report_startup_error(error: Exception) -> None:
    log_path = app_data_dir() / "pdfr.log"
    log_path.parent.mkdir(parents=True, exist_ok=True)
    log_path.write_text(traceback.format_exc(), encoding="utf-8")

    try:
        from tkinter import messagebox

        messagebox.showerror(
            "pdfr",
            f"pdfr failed to start:\n{error}\n\nDetails were written to:\n{log_path}",
        )
    except Exception:
        return


if __name__ == "__main__":
    raise SystemExit(main())
