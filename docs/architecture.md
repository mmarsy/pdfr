# Architecture

`pdfr` has four small runtime modules.

## `pdfr.__main__`

Parses command line arguments and starts the application. GUI imports happen
inside `main()` so tests can import the parser without creating Tkinter objects.

## `pdfr.pdf_document`

Wraps PyMuPDF. It validates input paths, opens PDFs, exposes page count/title,
and renders pages into PPM image bytes. Tkinter can load those bytes without an
extra image library.

## `pdfr.app`

Builds the desktop UI. The application computes a continuous page layout for the
scrollable canvas, draws lightweight placeholders for all pages, and renders only
pages near the visible viewport to Tkinter `PhotoImage` objects. This keeps large
PDFs responsive and avoids storing every rendered page image in memory.

Scrolling is handled by canvas view operations:

- Mouse wheel changes the vertical view.
- Arrow keys move the vertical or horizontal view.
- Mouse drag uses `scan_mark` and `scan_dragto` for panning.

Zoom changes re-render the visible document at the selected scale and preserve
the current vertical scroll position.

## `pdfr.storage`

Owns Windows-compatible app data persistence. Runtime state is stored under
`%APPDATA%\pdfr` so the installed `pdfr` entry point can be launched globally
without relying on the project directory. The first persisted file is
`viewer_state.json`, keyed by a per-document identity derived from the resolved
PDF path and validated with file size and modification time.
