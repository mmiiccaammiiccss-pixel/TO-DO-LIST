import tkinter as tk
from tkinter import simpledialog, messagebox, ttk
import json
import os
from pathlib import Path

APP_DIR = Path(__file__).parent
LISTS_DIR = APP_DIR / "lists"

class TodoApp:
    def __init__(self, root):
        self.root = root
        root.title("TO DO LIST")
        root.geometry('500x400')

        LISTS_DIR.mkdir(exist_ok=True)

        # Top frame: list selector and New List button
        top_frame = tk.Frame(root)
        top_frame.pack(fill=tk.X, padx=8, pady=6)

        tk.Label(top_frame, text="Select list:").pack(side=tk.LEFT)
        self.list_var = tk.StringVar()
        self.list_selector = ttk.Combobox(top_frame, textvariable=self.list_var, state='readonly')
        self.list_selector.pack(side=tk.LEFT, padx=6)
        self.list_selector.bind('<<ComboboxSelected>>', lambda e: self.select_list(self.list_var.get()))

        tk.Button(top_frame, text="New List", command=self.new_list).pack(side=tk.LEFT, padx=6)

        # Middle: listbox with tasks
        middle = tk.Frame(root)
        middle.pack(fill=tk.BOTH, expand=True, padx=8)

        self.tasks_box = tk.Listbox(middle, activestyle='dotbox')
        self.tasks_box.pack(fill=tk.BOTH, expand=True, side=tk.LEFT)

        scrollbar = tk.Scrollbar(middle, orient=tk.VERTICAL, command=self.tasks_box.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.tasks_box.config(yscrollcommand=scrollbar.set)

        # Bottom: add/remove
        bottom = tk.Frame(root)
        bottom.pack(fill=tk.X, padx=8, pady=6)

        self.entry = tk.Entry(bottom)
        self.entry.pack(side=tk.LEFT, fill=tk.X, expand=True)
        self.entry.bind('<Return>', lambda e: self.add_task())

        tk.Button(bottom, text="Add", command=self.add_task).pack(side=tk.LEFT, padx=6)
        tk.Button(bottom, text="Remove", command=self.remove_task).pack(side=tk.LEFT, padx=6)

        # Right side controls for list operations
        ctrl = tk.Frame(root)
        ctrl.pack(fill=tk.X, padx=8, pady=4)
        tk.Button(ctrl, text="Rename List", command=self.rename_list).pack(side=tk.LEFT, padx=6)
        tk.Button(ctrl, text="Delete List", command=self.delete_list).pack(side=tk.LEFT, padx=6)

        # load lists and select default
        self.lists = {} # type: ignore
        self.current_list = None
        self.load_lists()
        if self.list_selector['values']:
            self.list_selector.current(0)
            self.select_list(self.list_selector.get())

        # Bindings: double-click to edit task, keyboard shortcuts
        self.tasks_box.bind('<Double-Button-1>', lambda e: self.edit_task())
        root.bind('<Control-n>', lambda e: self.new_list())
        root.bind('<Control-N>', lambda e: self.new_list())
        root.bind('<Control-r>', lambda e: self.rename_list())
        root.bind('<Control-R>', lambda e: self.rename_list())
        root.bind('<Control-d>', lambda e: self.delete_list())
        root.bind('<Control-D>', lambda e: self.delete_list())
        root.bind('<Delete>', lambda e: self.remove_task())

        # Menu
        menubar = tk.Menu(root)
        filemenu = tk.Menu(menubar, tearoff=0)
        filemenu.add_command(label='New List (Ctrl+N)', command=self.new_list)
        filemenu.add_command(label='Rename List (Ctrl+R)', command=self.rename_list)
        filemenu.add_command(label='Delete List (Ctrl+D)', command=self.delete_list)
        filemenu.add_separator()
        filemenu.add_command(label='Exit', command=root.quit)
        menubar.add_cascade(label='File', menu=filemenu)

        helpmenu = tk.Menu(menubar, tearoff=0)
        helpmenu.add_command(label='About', command=lambda: messagebox.showinfo('About', 'Simple TO DO LIST - Tkinter'))
        menubar.add_cascade(label='Help', menu=helpmenu)

        root.config(menu=menubar)

    def load_lists(self):
        self.lists = {}
        files = sorted(LISTS_DIR.glob('*.json'))
        names = []
        for p in files:
            try:
                with open(p, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    name = data.get('name', p.stem)
                    self.lists[name] = {'path': p, 'tasks': data.get('tasks', [])}
                    names.append(name)
            except Exception:
                # skip corrupt file
                continue
        if not names:
            # create default list
            self.create_list_file('default')
            self.load_lists()
            return
        self.list_selector['values'] = names

    def select_list(self, name):
        if name not in self.lists:
            return
        self.current_list = name
        self.tasks_box.delete(0, tk.END)
        for t in self.lists[name]['tasks']:
            self.tasks_box.insert(tk.END, t)

    def add_task(self):
        text = self.entry.get().strip()
        if not text:
            return
        if not self.current_list:
            messagebox.showinfo('No list', 'Please create or select a list first.')
            return
        self.lists[self.current_list]['tasks'].append(text)
        self.tasks_box.insert(tk.END, text)
        self.entry.delete(0, tk.END)
        self.save_current_list()

    def remove_task(self):
        sel = self.tasks_box.curselection()
        if not sel:
            return
        idx = sel[0]
        self.tasks_box.delete(idx)
        del self.lists[self.current_list]['tasks'][idx]
        self.save_current_list()

    def edit_task(self):
        sel = self.tasks_box.curselection()
        if not sel or not self.current_list:
            return
        idx = sel[0]
        old = self.lists[self.current_list]['tasks'][idx]
        new = simpledialog.askstring('Edit task', 'Edit task:', initialvalue=old)
        if new is None:
            return
        new = new.strip()
        if not new:
            # empty -> remove
            self.tasks_box.delete(idx)
            del self.lists[self.current_list]['tasks'][idx]
        else:
            self.lists[self.current_list]['tasks'][idx] = new
            self.tasks_box.delete(idx)
            self.tasks_box.insert(idx, new)
        self.save_current_list()

    def new_list(self):
        name = simpledialog.askstring('New list', 'Enter name for the new list:')
        if not name:
            return
        name = name.strip()
        if name in self.lists:
            messagebox.showinfo('Exists', 'A list with that name already exists.')
            return
        self.create_list_file(name)
        self.load_lists()
        self.list_selector.set(name)
        self.select_list(name)
        messagebox.showinfo('Created', f'List "{name}" created and saved.')

    def rename_list(self):
        if not self.current_list:
            messagebox.showinfo('No list', 'Please select a list first.')
            return
        old = self.current_list
        new = simpledialog.askstring('Rename list', 'Enter new name for the list:', initialvalue=old)
        if not new:
            return
        new = new.strip()
        if new == old:
            return
        if new in self.lists:
            messagebox.showinfo('Exists', 'A list with that name already exists.')
            return
        # create new file and remove old file
        old_path = self.lists[old]['path']
        new_path = LISTS_DIR / f"{new}.json"
        data = {"name": new, "tasks": self.lists[old]['tasks']}
        with open(new_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2)
        try:
            old_path.unlink()
        except Exception:
            pass
        self.load_lists()
        self.list_selector.set(new)
        self.select_list(new)
        messagebox.showinfo('Renamed', f'List renamed to "{new}"')

    def delete_list(self):
        if not self.current_list:
            messagebox.showinfo('No list', 'Please select a list first.')
            return
        name = self.current_list
        if not messagebox.askyesno('Delete', f'Delete list "{name}"? This will remove the file from disk.'):
            return
        path = self.lists[name]['path']
        try:
            path.unlink()
        except Exception:
            pass
        # reload and pick another
        self.load_lists()
        if self.list_selector['values']:
            self.list_selector.current(0)
            self.select_list(self.list_selector.get())
        else:
            self.current_list = None
            self.tasks_box.delete(0, tk.END)
        messagebox.showinfo('Deleted', f'List "{name}" deleted.')

    def create_list_file(self, name):
        p = LISTS_DIR / f"{name}.json"
        data = {"name": name, "tasks": []}
        with open(p, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2)

    def save_current_list(self):
        if not self.current_list:
            return
        p = self.lists[self.current_list]['path']
        data = {"name": self.current_list, "tasks": self.lists[self.current_list]['tasks']}
        with open(p, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2)


if __name__ == '__main__':
    root = tk.Tk()
    app = TodoApp(root)
    root.mainloop()
