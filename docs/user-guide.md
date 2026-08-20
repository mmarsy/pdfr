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

If `pdfr` appears to do nothing, run the console diagnostic launcher:

```powershell
pdfr-debug C:\path\to\file.pdf
```

The normal `pdfr` command is a GUI launcher, so it does not print terminal
tracebacks.

## Installing the Global Entry Point

Use a user-level install when you want the `pdfr` command available outside the
project directory:

```powershell
py -m pip install --user .
```

Run the same command again after project changes so the global launcher points
at the current package code.

On Windows, ensure Python's user `Scripts` directory is on `PATH`. Find the base
directory with:

```powershell
py -m site --user-base
```

The `pdfr.exe` entry point is created under that path's `Scripts` directory.

## Controls

- Open a PDF with the toolbar button, the File menu, or `Ctrl+O`.
- Right-click a PDF tab to view or close it. `Ctrl+W` and the toolbar button close the current tab.
- Zoom with the toolbar buttons or `Ctrl++`, `Ctrl+=`, `Ctrl+-`, and `Ctrl+0`.
- Scroll with the mouse wheel.
- Pan by dragging the page area with the left mouse button.
- Use arrow keys to scroll: up and down to emulate mouse scroll, left and right to jump pages.

## Saved Viewer State

`pdfr` saves zoom and scroll position when a tab or window closes. On Windows,
this state is stored in:

```powershell
%APPDATA%\pdfr\viewer_state.json
```

The state is matched to the opened PDF path, file size, and modification time.
Future notes and drawing data will be stored under the same `%APPDATA%\pdfr`
directory.

Startup errors are written to:

```powershell
%APPDATA%\pdfr\pdfr.log
```

## Troubleshooting

- If `pdfr` is not found, check that the Python Scripts directory is on `PATH`.
- If `pdfr` exits silently, run `pdfr-debug` or inspect `%APPDATA%\pdfr\pdfr.log`.
- If a PDF does not open, verify that the file exists and has a `.pdf` extension.
- Very large PDFs may take a moment to render newly visible pages while
  scrolling or after zoom changes.
