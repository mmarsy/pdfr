# Development plan.

## Instructions:

Create items of the form:
```
[ ] 1. Goal (brief goal description)
```
Whenever a goal is completed mark its completion like this:
```
[X] 1. Goal (brief goal description)
```

## Plan
[X] 1. Fill pyproject.toml with setuptools metadata, runtime/dev dependencies, entry point configuration, and tooling configuration; then pause for user verification before application development.
[X] 2. Build the pdfr package with a GUI entry point, PDF rendering, zoom controls, and mouse/keyboard scrolling.
[X] 3. Add README usage instructions and docs for users and maintainers.
[X] 4. Validate the project with the then-current checks; future validation must avoid pytest.
[X] 5. Investigate and fix the issue where the window opens but rendered PDF pages are not visible.
[X] 6. Add Windows app-data storage for globally installed app usage.
[X] 7. Persist PDF viewer state per document, including zoom and scroll position.
[X] 8. Make left/right arrows skip pages.
[X] 9. Update docs and validation instructions to avoid pytest.
[X] 10. Add startup error logging and a console diagnostic entry point for silent GUI launcher failures.
[X] 11. Replace broken tab X behavior with a right-click tab menu for viewing and closing tabs.
