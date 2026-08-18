# Development Notes

## Setup

Install the project with development dependencies:

```powershell
py -m pip install -e ".[dev]"
```

## Validation

Run both checks before considering work complete:

```powershell
ruff check .
py -m compileall src
```

## Packaging

The project uses `setuptools` with a `src` layout. The desktop entry point is
configured in `pyproject.toml` under `[project.gui-scripts]`:

```toml
pdfr = "pdfr.__main__:main"
```

On Windows, this creates a GUI launcher that starts without a terminal window.

## Implementation Notes

- `pdfr.__main__` parses optional command line arguments and lazily imports GUI
  code so argument parsing remains easy to test.
- `pdfr.pdf_document` owns PyMuPDF document loading and page rendering.
- `pdfr.app` owns the Tkinter window, toolbar, canvas, scrolling, panning, and
  zoom behavior.
- `pdfr.storage` owns Windows app-data paths and JSON persistence under
  `%APPDATA%\pdfr`.
- GUI behavior is intentionally thin around the rendering wrapper so core logic
  can be validated without launching a window.
