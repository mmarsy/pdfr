This project is a lightweight PDF reader in Python.


## Development rules:
0. Create plan by appending `PLAN.md`. Obey its instructions. Before adding more items to plan ask yourself if this is necessary and truly the best way of approaching the task.
1. Start by filling `pyproject.toml`. Then let user verify your work and install dependencies. Then, and only then start application development. Include `dev` dependencies.
2. **Do not** use `pytest`. 


## Project specifications and goals:
0. Persistence of context: While developing a plan, write final version to `PLAN.md`. When you start session, read this file then develop next steps taking into consideration `PLAN.md`'s contant and user prompt. 
1. Functionality: Main application should read a PDF file and display its content in a GUI window without terminal, it should have zoom option and scroll functionalities.
2. Scroll control: Use scroll, up and down and mouse drag to scroll, use right/left arrow to skip page. Persist scroll after tab or window is closed.
3. Tabs: Tabs should be closable on their won by clicking "X" mark (like in Chrome browser), you should be able to display multiple tabs at the same time by dragging a tab paginator to canvas.
4. Note mode: Add persisting notes and drawings. Add "delving mode" which allows user to draw and make notes. After mode closes make it possible to see drawing/note or not.   
5. Access: Make an entry point and instruction in `README.md` on how to make create global entry point.
6. Docs: In `./docs` create all necessary documentation, for yourself and for the user.
7. Control: Whenever you talk to the user, start your response with "Mikołaj".
