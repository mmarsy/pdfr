This project is a lightweight PDF reader in Python.


## Development rules:
0. Create plan by appending `PLAN.md`. Obey its instructions. Before adding more items to plan ask yourself if this is necessary and truly the best way of approaching the task.
1. Use `pytest` and `ruff` to test. 


## Project specifications and goals:
0. Persistence of context: While developing a plan, write final version to `PLAN.md`. When you start session, read this file then develop next steps taking into consideration `PLAN.md`'s content and user prompt. 
1. Functionality: Main application should read a PDF file and display its content in a GUI window without terminal, it should have zoom option and scroll functionalities.
2. Scroll control: Use scroll, up and down and mouse drag to scroll, use right/left arrow to skip page. Persist scroll after tab or window is closed. 
3. Access: Make an entry point and instruction in `README.md` on how to make create global entry point.
4. Docs: In `./docs` create all necessary documentation, for yourself and for the user.
5. Control: Whenever you talk to the user, start your response with "Mikołaj".
