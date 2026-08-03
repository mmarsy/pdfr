# pdfr

`pdfr` is a lightweight desktop PDF reader written in Python. It uses Tkinter for
the GUI and PyMuPDF for rendering PDF pages.

## Install

For development:

```powershell
py -m pip install -e ".[dev]"
```

For a user-level install that creates the `pdfr` GUI entry point:

```powershell
py -m pip install --user .
```

If Windows cannot find `pdfr`, add Python's user Scripts directory to `PATH`.
You can locate the user base with:

```powershell
py -m site --user-base
```

The executable is usually in the `Scripts` directory inside that path. Because
`pdfr` is configured as a `gui-scripts` entry point, launching it on Windows does
not open a terminal window.

## Run

Open the application and choose a PDF from the file dialog:

```powershell
pdfr
```

Open a specific PDF:

```powershell
pdfr C:\path\to\file.pdf
```

## Controls

- `Open` or `Ctrl+O`: open a PDF.
- `+`, `Ctrl++`, or `Ctrl+=`: zoom in.
- `-` or `Ctrl+-`: zoom out.
- `1:1` or `Ctrl+0`: reset zoom to 100%.
- Mouse wheel: scroll vertically.
- Click and drag: pan the document.
- Arrow keys: scroll vertically or horizontally.

## Development

Run the validation commands before committing changes:

```powershell
ruff check .
pytest
```

Project documentation is in [docs](docs/).
