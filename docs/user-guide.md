# User Guide

## Starting pdfr

After installation, run:

```powershell
pdfr
```

To open a file immediately:

```powershell
pdfr C:\path\to\file.pdf
```

## Installing the Global Entry Point

Use a user-level install when you want the `pdfr` command available outside the
project directory:

```powershell
py -m pip install --user .
```

On Windows, ensure Python's user `Scripts` directory is on `PATH`. Find the base
directory with:

```powershell
py -m site --user-base
```

The `pdfr.exe` entry point is created under that path's `Scripts` directory.

## Controls

- Open a PDF with the toolbar button, the File menu, or `Ctrl+O`.
- Zoom with the toolbar buttons or `Ctrl++`, `Ctrl+=`, `Ctrl+-`, and `Ctrl+0`.
- Scroll with the mouse wheel.
- Pan by dragging the page area with the left mouse button.
- Use arrow keys to scroll.

## Troubleshooting

- If `pdfr` is not found, check that the Python Scripts directory is on `PATH`.
- If a PDF does not open, verify that the file exists and has a `.pdf` extension.
- Very large PDFs may take a moment to render newly visible pages while
  scrolling or after zoom changes.
