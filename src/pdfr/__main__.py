from __future__ import annotations

import argparse
from collections.abc import Sequence
from pathlib import Path

from pdfr import __version__


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        prog="pdfr",
        description="Open a PDF in a lightweight desktop reader.",
    )
    parser.add_argument("pdf", nargs="?", type=Path, help="PDF file to open.")
    parser.add_argument("--version", action="version", version=f"%(prog)s {__version__}")
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> int:
    args = parse_args(argv)

    from pdfr.app import run

    run(args.pdf)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
