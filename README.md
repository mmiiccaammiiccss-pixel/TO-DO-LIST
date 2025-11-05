# TO DO LIST (Tkinter)

A simple desktop To Do List application written in Python using Tkinter. Each list is saved as a JSON file inside the `lists/` folder; creating a new list will immediately save it.

Requirements
- Python 3.8+ (Tkinter is included in standard Windows Python installers)

Run

You can launch the app in one of these ways on Windows:

- Recommended (uses Windows Python launcher):

```batch
run.bat
```

- If `python` is on your PATH:

```batch
python main.py
```

- Alternative direct launcher:

```batch
run_python.bat
```

How it works
- Use the "New List" button to create a named list — it is saved immediately to `lists/<name>.json`.
- Add tasks in the text entry and press Enter or click "Add" — tasks are auto-saved.
- Select a list from the dropdown to load it.

Notes
- No external packages required.
- The `lists/` folder is created automatically on first run.