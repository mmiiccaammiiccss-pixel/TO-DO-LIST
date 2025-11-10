import tkinter as tk
from tkinter import simpledialog, messagebox, ttk, PhotoImage
import tkinter.font as tkfont
import json
import os
from pathlib import Path
import base64

APP_DIR = Path(__file__).parent
LISTS_DIR = APP_DIR / "lists"

class TodoApp:
    def __init__(self, root):
        self.root = root
        root.title("TO DO LIST")
        root.geometry('720x520')  # Slightly larger to accommodate padding
        root.minsize(620, 480)

        # Add main padding container
        main_container = ttk.Frame(root, style='Main.TFrame')
        main_container.pack(fill=tk.BOTH, expand=True, padx=12, pady=12)

        LISTS_DIR.mkdir(exist_ok=True)

        # Setup cotton candy theme
        self.setup_style()

        # Top frame: list selector and New List button (with shadow)
        top_shadow = ttk.Frame(main_container, style='Shadow.TFrame')
        top_shadow.pack(fill=tk.X, padx=8, pady=(0, 8))
        
        top_frame = ttk.Frame(top_shadow, style='Card.TFrame')
        top_frame.pack(fill=tk.X, padx=1, pady=1)

        ttk.Label(top_frame, text="Select list:", style='Cotton.TLabel').pack(side=tk.LEFT)
        self.list_var = tk.StringVar()
        self.list_selector = ttk.Combobox(top_frame, textvariable=self.list_var, state='readonly',
                                         style='Cotton.TCombobox', width=30)
        self.list_selector.pack(side=tk.LEFT, padx=6)
        self.list_selector.bind('<<ComboboxSelected>>', lambda e: self.select_list(self.list_var.get()))

        ttk.Button(top_frame, text="New List", command=self.new_list,
                  style='Accent.TButton').pack(side=tk.LEFT, padx=6)

        # Middle: tree view for tasks with more details (with shadow)
        middle_shadow = ttk.Frame(main_container, style='Shadow.TFrame')
        middle_shadow.pack(fill=tk.BOTH, expand=True, padx=8, pady=8)
        
        middle = ttk.Frame(middle_shadow, style='Card.TFrame')
        middle.pack(fill=tk.BOTH, expand=True, padx=2, pady=2)

        # Tree view for tasks
        self.tree = ttk.Treeview(middle, columns=("Done", "Task", "Deadline", "Subtasks"),
                                show="headings", style="Cotton.Treeview")
        
        self.tree.heading("Done", text="✓")
        self.tree.heading("Task", text="Task")
        self.tree.heading("Deadline", text="Deadline")
        self.tree.heading("Subtasks", text="Subtasks")

        self.tree.column("Done", width=30, anchor="center")
        self.tree.column("Task", width=300)
        self.tree.column("Deadline", width=100, anchor="center")
        self.tree.column("Subtasks", width=170)

        self.tree.pack(fill=tk.BOTH, expand=True, side=tk.LEFT)
        self.tree.bind("<Double-1>", self.edit_task)
        self.tree.bind("<space>", lambda e: self.toggle_task_done())

        scrollbar = ttk.Scrollbar(middle, orient=tk.VERTICAL, command=self.tree.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.tree.configure(yscrollcommand=scrollbar.set)

        # Bottom: task entry and controls
        bottom = ttk.Frame(main_container, style='Card.TFrame')
        bottom.pack(fill=tk.X, padx=8, pady=(8, 0))

        # Task input area
        input_frame = ttk.Frame(bottom, style='Card.TFrame')
        input_frame.pack(fill=tk.X, expand=True, pady=4)

        # First row: main task entry and priority
        row1 = ttk.Frame(input_frame)
        row1.pack(fill=tk.X, pady=2)
        
        self.entry = ttk.Entry(row1, style='Cotton.TEntry')
        self.entry.insert(0, "Enter task...")
        self.entry.bind('<FocusIn>', lambda e: self.entry.delete(0, tk.END) if self.entry.get() == "Enter task..." else None)
        self.entry.bind('<FocusOut>', lambda e: self.entry.insert(0, "Enter task...") if not self.entry.get() else None)
        self.entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=4)
        self.entry.bind('<Return>', lambda e: self.add_task())

        # Second row: deadline and subtasks
        row2 = ttk.Frame(input_frame)
        row2.pack(fill=tk.X, pady=2)
        
        ttk.Label(row2, text="Deadline:", style='Cotton.TLabel').pack(side=tk.LEFT, padx=4)
        self.deadline_var = tk.StringVar()
        self.deadline_entry = ttk.Entry(row2, textvariable=self.deadline_var,
                                      style='Cotton.TEntry', width=15)
        self.deadline_entry.pack(side=tk.LEFT, padx=4)
        
        ttk.Label(row2, text="Subtasks:", style='Cotton.TLabel').pack(side=tk.LEFT, padx=4)
        self.subtasks_var = tk.StringVar()
        self.subtasks_entry = ttk.Entry(row2, textvariable=self.subtasks_var,
                                      style='Cotton.TEntry')
        self.subtasks_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=4)

        # Buttons frame
        btn_frame = ttk.Frame(bottom)
        btn_frame.pack(fill=tk.X, pady=4)
        
        ttk.Button(btn_frame, text="Add Task", command=self.add_task,
                  style='Cotton.TButton').pack(side=tk.LEFT, padx=4)
        ttk.Button(btn_frame, text="Edit", command=lambda: self.edit_task(),
                  style='Cotton.TButton').pack(side=tk.LEFT, padx=4)
        ttk.Button(btn_frame, text="Remove", command=self.remove_task,
                  style='Cotton.TButton').pack(side=tk.LEFT, padx=4)
        ttk.Button(btn_frame, text="Toggle Done", command=self.toggle_task_done,
                  style='Cotton.TButton').pack(side=tk.LEFT, padx=4)

        # Right side controls for list operations
        ctrl = ttk.Frame(main_container, style='Card.TFrame')
        ctrl.pack(fill=tk.X, padx=8, pady=(8, 0))
        ttk.Button(ctrl, text="Rename List", command=self.rename_list,
                  style='Cotton.TButton').pack(side=tk.LEFT, padx=6)
        ttk.Button(ctrl, text="Delete List", command=self.delete_list,
                  style='Cotton.TButton').pack(side=tk.LEFT, padx=6)

        # load lists and select default
        self.lists = {} # type: ignore
        self.current_list = None
        self.load_lists()
        if self.list_selector['values']:
            self.list_selector.current(0)
            self.select_list(self.list_selector.get())

        # Bindings: double-click to edit task, keyboard shortcuts
        self.tree.bind('<Double-Button-1>', lambda e: self.edit_task())
        # Keyboard shortcuts
        # List management
        root.bind('<Control-n>', lambda e: self.new_list())
        root.bind('<Control-N>', lambda e: self.new_list())
        root.bind('<Control-r>', lambda e: self.rename_list())
        root.bind('<Control-R>', lambda e: self.rename_list())
        root.bind('<Control-d>', lambda e: self.delete_list())
        root.bind('<Control-D>', lambda e: self.delete_list())
        
        # Task management
        root.bind('<Control-a>', lambda e: self.focus_add_task())
        root.bind('<Control-A>', lambda e: self.focus_add_task())
        root.bind('<Delete>', lambda e: self.remove_task())
        root.bind('<Control-e>', lambda e: self.edit_task())
        root.bind('<Control-E>', lambda e: self.edit_task())
        root.bind('<space>', lambda e: self.toggle_task_done())
        
        # Navigation
        root.bind('<Control-Up>', lambda e: self.move_task_up())
        root.bind('<Control-Down>', lambda e: self.move_task_down())
        root.bind('<Control-Home>', lambda e: self.select_first_task())
        root.bind('<Control-End>', lambda e: self.select_last_task())
        
        # Task selection
        root.bind('<Up>', lambda e: self.select_previous_task())
        root.bind('<Down>', lambda e: self.select_next_task())

        # Menu
        menubar = tk.Menu(root)
        
        # File menu
        filemenu = tk.Menu(menubar, tearoff=0)
        filemenu.add_command(label='New List (Ctrl+N)', command=self.new_list)
        filemenu.add_command(label='Rename List (Ctrl+R)', command=self.rename_list)
        filemenu.add_command(label='Delete List (Ctrl+D)', command=self.delete_list)
        filemenu.add_separator()
        filemenu.add_command(label='Exit (Alt+F4)', command=root.quit)
        menubar.add_cascade(label='File', menu=filemenu)

        # Task menu
        taskmenu = tk.Menu(menubar, tearoff=0)
        taskmenu.add_command(label='Add Task (Ctrl+A)', command=self.focus_add_task)
        taskmenu.add_command(label='Edit Task (Ctrl+E)', command=self.edit_task)
        taskmenu.add_command(label='Remove Task (Delete)', command=self.remove_task)
        taskmenu.add_command(label='Toggle Done (Space)', command=self.toggle_task_done)
        taskmenu.add_separator()
        taskmenu.add_command(label='Move Up (Ctrl+↑)', command=lambda: self.move_task_up())
        taskmenu.add_command(label='Move Down (Ctrl+↓)', command=lambda: self.move_task_down())
        menubar.add_cascade(label='Task', menu=taskmenu)

        # Help menu
        helpmenu = tk.Menu(menubar, tearoff=0)
        helpmenu.add_command(label='Keyboard Shortcuts', command=self.show_shortcuts)
        helpmenu.add_command(label='About', command=lambda: messagebox.showinfo('About', 'Simple TO DO LIST - Tkinter\\n\\nUse keyboard shortcuts for quick access!'))
        menubar.add_cascade(label='Help', menu=helpmenu)

        root.config(menu=menubar)

    def setup_style(self):
        """Configure cotton candy theme with pastels."""
        self.colors = {
            'bg_light': '#FFF0F5',    # Light pink background
            'bg_mid': '#FFE4F3',      # Mid pink
            'accent': '#FF9ECD',      # Cotton candy pink
            'button': '#E0B1FF',      # Soft purple
            'button_hover': '#D094FF', # Darker purple
            'text': '#6B4E71',        # Muted purple text
            'highlight': '#B6D0FF',    # Soft blue highlight
            'shadow': '#FFD6E5',      # Soft pink shadow
            'border': '#FFB6E1'       # Border pink
        }

        # Setup fonts
        base_font = tkfont.nametofont('TkDefaultFont')
        self.fonts = {
            'regular': (base_font.actual('family'), 10),
            'bold': (base_font.actual('family'), 10, 'bold')
        }

        # Configure ttk styles
        style = ttk.Style()
        try:
            style.theme_use('clam')  # Use clam as base
        except:
            pass  # Fallback to default if clam isn't available

        # Frame styling with shadow effect
        style.configure('Card.TFrame', 
                       background=self.colors['bg_light'],
                       borderwidth=1,
                       relief='solid',
                       bordercolor=self.colors['border'])
        
        # Add shadow effect class
        style.configure('Shadow.TFrame',
                       background=self.colors['shadow'],
                       borderwidth=2,
                       relief='solid',
                       bordercolor=self.colors['border'])
        
        # Label styling
        style.configure('Cotton.TLabel',
                       background=self.colors['bg_light'],
                       foreground=self.colors['text'],
                       font=self.fonts['regular'])

        # Button styling with enhanced hover effects
        style.configure('Cotton.TButton',
                       background=self.colors['button'],
                       foreground=self.colors['text'],
                       font=self.fonts['regular'],
                       padding=6,
                       relief='raised',
                       borderwidth=2)
        style.map('Cotton.TButton',
                 background=[('active', self.colors['button_hover']),
                           ('pressed', self.colors['accent'])],
                 relief=[('pressed', 'sunken'),
                        ('active', 'ridge')],
                 borderwidth=[('pressed', 1),
                            ('active', 3)],
                 foreground=[('pressed', 'white'),
                           ('active', self.colors['text'])])

        # Accent button (New List) with enhanced hover effects
        style.configure('Accent.TButton',
                       background=self.colors['accent'],
                       foreground='white',
                       font=self.fonts['bold'],
                       padding=6,
                       relief='raised',
                       borderwidth=2)
        style.map('Accent.TButton',
                 background=[('pressed', '#FF5AA8'),
                           ('active', '#FF7AB8')],
                 relief=[('pressed', 'sunken'),
                        ('active', 'ridge')],
                 borderwidth=[('pressed', 1),
                            ('active', 3)],
                 foreground=[('pressed', 'white'),
                           ('active', 'white')])

        # Entry styling
        style.configure('Cotton.TEntry',
                       fieldbackground=self.colors['bg_mid'],
                       foreground=self.colors['text'],
                       padding=6)

        # Combobox styling
        style.configure('Cotton.TCombobox',
                       background=self.colors['bg_mid'],
                       fieldbackground=self.colors['bg_mid'],
                       foreground=self.colors['text'],
                       arrowcolor=self.colors['text'],
                       padding=6)

        # Configure root background
        self.root.configure(bg=self.colors['bg_light'])
        
        # Load the application logo
        ico_path = APP_DIR / 'assets' / 'logo.ico'
        try:
            if ico_path.exists():
                print(f"Loading logo from: {ico_path}")
                self.root.iconbitmap(str(ico_path))
            else:
                print(f"Logo file not found at: {ico_path}")
        except Exception as e:
            print(f"Error loading logo: {e}")

    def load_lists(self):
        self.lists = {}
        files = sorted(LISTS_DIR.glob('*.json'))
        names = []
        for p in files:
            try:
                with open(p, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    name = data.get('name', p.stem)
                    # Convert old format to new format if needed
                    tasks = data.get('tasks', [])
                    if isinstance(tasks, list) and tasks and isinstance(tasks[0], str):
                        # Convert old string tasks to new dictionary format
                        tasks = [{'text': t, 'done': False,
                                'deadline': '', 'subtasks': ''} for t in tasks]
                    self.lists[name] = {'path': p, 'tasks': tasks}
                    names.append(name)
            except Exception as e:
                print(f"Error loading {p}: {e}")  # For debugging
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
        self.refresh_task_view()

    def refresh_task_view(self):
        if not self.current_list:
            return
        
        # Clear existing items
        for item in self.tree.get_children():
            self.tree.delete(item)
        
        tasks = self.lists[self.current_list]['tasks']
            
        # Sort tasks: incomplete first
        tasks.sort(key=lambda x: x['done'])
            
        # Add tasks to tree
        for task in tasks:
            self.tree.insert("", tk.END, values=(
                "✓" if task['done'] else "",
                task['text'],
                task['deadline'],
                task['subtasks']
            ))

    def filter_tasks(self):
        self.refresh_task_view()

    def add_task(self):
        text = self.entry.get().strip()
        if not text:
            return
        if not self.current_list:
            messagebox.showinfo('No list', 'Please create or select a list first.')
            return

        # Create new task with all properties
        task = {
            'text': text,
            'done': False,
            'deadline': self.deadline_var.get().strip(),
            'subtasks': self.subtasks_var.get().strip()
        }
        
        self.lists[self.current_list]['tasks'].append(task)
        self.refresh_task_view()
        
        # Clear all input fields
        self.entry.delete(0, tk.END)
        self.deadline_var.set("")
        self.subtasks_var.set("")
        self.save_current_list()

    def remove_task(self):
        selection = self.tree.selection()
        if not selection:
            return
        
        # Get the index in the original task list
        task_text = self.tree.item(selection[0])['values'][1]  # Get task text
        tasks = self.lists[self.current_list]['tasks']
        for i, task in enumerate(tasks):
            if task['text'] == task_text:
                del tasks[i]
                break
                
        self.refresh_task_view()
        self.save_current_list()

    def toggle_task_done(self):
        selection = self.tree.selection()
        if not selection:
            return
            
        # Get the task text and find it in the original list
        task_text = self.tree.item(selection[0])['values'][1]
        tasks = self.lists[self.current_list]['tasks']
        for task in tasks:
            if task['text'] == task_text:
                task['done'] = not task['done']
                break
                
        self.refresh_task_view()
        self.save_current_list()

    def edit_task(self, event=None):
        selection = self.tree.selection()
        if not selection:
            return
        
        item = selection[0]
        values = self.tree.item(item)['values']
        
        # Create a dialog for editing
        dialog = tk.Toplevel(self.root)
        dialog.title("Edit Task")
        dialog.geometry("400x250")
        dialog.transient(self.root)
        dialog.grab_set()
        
        # Task text
        ttk.Label(dialog, text="Task:", style='Cotton.TLabel').pack(pady=4)
        text_var = tk.StringVar(value=values[1])
        text_entry = ttk.Entry(dialog, textvariable=text_var, style='Cotton.TEntry')
        text_entry.pack(fill=tk.X, padx=8, pady=4)
        
        # Deadline
        ttk.Label(dialog, text="Deadline:", style='Cotton.TLabel').pack(pady=4)
        deadline_var = tk.StringVar(value=values[2])
        deadline_entry = ttk.Entry(dialog, textvariable=deadline_var, style='Cotton.TEntry')
        deadline_entry.pack(fill=tk.X, padx=8, pady=4)
        
        # Subtasks
        ttk.Label(dialog, text="Subtasks:", style='Cotton.TLabel').pack(pady=4)
        subtasks_var = tk.StringVar(value=values[3])
        subtasks_entry = ttk.Entry(dialog, textvariable=subtasks_var, style='Cotton.TEntry')
        subtasks_entry.pack(fill=tk.X, padx=8, pady=4)
        
        def save_changes():
            # Find and update the task
            task_text = values[1]
            tasks = self.lists[self.current_list]['tasks']
            for task in tasks:
                if task['text'] == task_text:
                    task.update({
                        'text': text_var.get().strip(),
                        'deadline': deadline_var.get().strip(),
                        'subtasks': subtasks_var.get().strip()
                    })
                    break
            self.refresh_task_view()
            self.save_current_list()
            dialog.destroy()
        
        ttk.Button(dialog, text="Save", command=save_changes,
                  style='Cotton.TButton').pack(pady=16)

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

    def setup_style(self):
        """Configure cotton candy theme with pastels."""
        self.colors = {
            'bg_light': '#FFF0F5',    # Light pink background
            'bg_mid': '#FFE4F3',      # Mid pink
            'accent': '#FF9ECD',      # Cotton candy pink
            'button': '#E0B1FF',      # Soft purple
            'button_hover': '#D094FF', # Darker purple
            'text': '#6B4E71',        # Muted purple text
            'highlight': '#B6D0FF',    # Soft blue highlight
            'shadow': '#FFD6E5',      # Soft pink shadow
            'border': '#FFB6E1'       # Border pink
        }

        # Setup fonts
        base_font = tkfont.nametofont('TkDefaultFont')
        self.fonts = {
            'regular': (base_font.actual('family'), 10),
            'bold': (base_font.actual('family'), 10, 'bold')
        }

        # Configure ttk styles
        style = ttk.Style()
        try:
            style.theme_use('clam')  # Use clam as base
        except:
            pass  # Fallback to default if clam isn't available

        # Frame styling with shadow effect
        style.configure('Card.TFrame', 
                       background=self.colors['bg_light'],
                       borderwidth=1,
                       relief='solid',
                       bordercolor=self.colors['border'])
        
        # Add shadow effect class
        style.configure('Shadow.TFrame',
                       background=self.colors['shadow'],
                       borderwidth=2,
                       relief='solid',
                       bordercolor=self.colors['border'])
        
        # Label styling
        style.configure('Cotton.TLabel',
                       background=self.colors['bg_light'],
                       foreground=self.colors['text'],
                       font=self.fonts['regular'])

        # Button styling with enhanced hover effects
        style.configure('Cotton.TButton',
                       background=self.colors['button'],
                       foreground=self.colors['text'],
                       font=self.fonts['regular'],
                       padding=6,
                       relief='raised',
                       borderwidth=2)
        style.map('Cotton.TButton',
                 background=[('active', self.colors['button_hover']),
                           ('pressed', self.colors['accent'])],
                 relief=[('pressed', 'sunken'),
                        ('active', 'ridge')],
                 borderwidth=[('pressed', 1),
                            ('active', 3)],
                 foreground=[('pressed', 'white'),
                           ('active', self.colors['text'])])

        # Accent button (New List) with enhanced hover effects
        style.configure('Accent.TButton',
                       background=self.colors['accent'],
                       foreground='white',
                       font=self.fonts['bold'],
                       padding=6,
                       relief='raised',
                       borderwidth=2)
        style.map('Accent.TButton',
                 background=[('pressed', '#FF5AA8'),
                           ('active', '#FF7AB8')],
                 relief=[('pressed', 'sunken'),
                        ('active', 'ridge')],
                 borderwidth=[('pressed', 1),
                            ('active', 3)],
                 foreground=[('pressed', 'white'),
                           ('active', 'white')])

        # Entry styling
        style.configure('Cotton.TEntry',
                       fieldbackground=self.colors['bg_mid'],
                       foreground=self.colors['text'],
                       padding=6)

        # Combobox styling
        style.configure('Cotton.TCombobox',
                       background=self.colors['bg_mid'],
                       fieldbackground=self.colors['bg_mid'],
                       foreground=self.colors['text'],
                       arrowcolor=self.colors['text'],
                       padding=6)

        # Treeview styling
        style.configure("Cotton.Treeview",
                       background=self.colors['bg_light'],
                       fieldbackground=self.colors['bg_light'],
                       foreground=self.colors['text'],
                       rowheight=25)
        
        style.configure("Cotton.Treeview.Heading",
                       background=self.colors['bg_mid'],
                       foreground=self.colors['text'],
                       relief='flat')
        
        style.map("Cotton.Treeview",
                 background=[('selected', self.colors['accent'])],
                 foreground=[('selected', 'white')])

        # Configure root background
        self.root.configure(bg=self.colors['bg_light'])
        
        # Load the application logo
        try:
            icon_path = APP_DIR / 'assets' / 'app_icon.ico'
            if icon_path.exists():
                print(f"Loading icon from: {icon_path}")
                self.root.iconbitmap(default=str(icon_path))
                # Also try setting it as a window icon
                self.root.tk.call('wm', 'iconphoto', self.root._w, PhotoImage(file=str(icon_path)))
        except Exception as e:
            print(f"Error loading icon: {e}")

    def create_list_file(self, name):
        p = LISTS_DIR / f"{name}.json"
        data = {
            "name": name,
            "tasks": []
        }
        with open(p, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2)

    def save_current_list(self):
        if not self.current_list:
            return
        p = self.lists[self.current_list]['path']
        data = {"name": self.current_list, "tasks": self.lists[self.current_list]['tasks']}
        with open(p, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2)

    # Keyboard shortcut methods
    def focus_add_task(self, event=None):
        """Focus the task entry field (Ctrl+A)"""
        self.entry.focus_set()
        if self.entry.get() == "Enter task...":
            self.entry.delete(0, tk.END)

    def move_task_up(self, event=None):
        """Move selected task up (Ctrl+Up)"""
        selection = self.tree.selection()
        if not selection:
            return
        
        item = selection[0]
        idx = self.tree.index(item)
        if idx > 0:
            # Move task in the data
            tasks = self.lists[self.current_list]['tasks']
            tasks.insert(idx - 1, tasks.pop(idx))
            # Refresh view and reselect item
            self.refresh_task_view()
            items = self.tree.get_children()
            self.tree.selection_set(items[idx - 1])
            self.tree.see(items[idx - 1])
            self.save_current_list()

    def move_task_down(self, event=None):
        """Move selected task down (Ctrl+Down)"""
        selection = self.tree.selection()
        if not selection:
            return
        
        item = selection[0]
        idx = self.tree.index(item)
        last_idx = len(self.tree.get_children()) - 1
        if idx < last_idx:
            # Move task in the data
            tasks = self.lists[self.current_list]['tasks']
            tasks.insert(idx + 1, tasks.pop(idx))
            # Refresh view and reselect item
            self.refresh_task_view()
            items = self.tree.get_children()
            self.tree.selection_set(items[idx + 1])
            self.tree.see(items[idx + 1])
            self.save_current_list()

    def select_first_task(self, event=None):
        """Select the first task (Ctrl+Home)"""
        items = self.tree.get_children()
        if items:
            self.tree.selection_set(items[0])
            self.tree.see(items[0])

    def select_last_task(self, event=None):
        """Select the last task (Ctrl+End)"""
        items = self.tree.get_children()
        if items:
            self.tree.selection_set(items[-1])
            self.tree.see(items[-1])

    def select_previous_task(self, event=None):
        """Select the previous task (Up arrow)"""
        selection = self.tree.selection()
        if not selection:
            self.select_last_task()
            return
            
        item = selection[0]
        idx = self.tree.index(item)
        if idx > 0:
            items = self.tree.get_children()
            self.tree.selection_set(items[idx - 1])
            self.tree.see(items[idx - 1])

    def select_next_task(self, event=None):
        """Select the next task (Down arrow)"""
        selection = self.tree.selection()
        if not selection:
            self.select_first_task()
            return
            
        item = selection[0]
        idx = self.tree.index(item)
        items = self.tree.get_children()
        if idx < len(items) - 1:
            self.tree.selection_set(items[idx + 1])
            self.tree.see(items[idx + 1])

    def show_shortcuts(self):
        """Show the keyboard shortcuts help dialog"""
        shortcuts = """
Keyboard Shortcuts:

List Management:
• Ctrl+N - Create new list
• Ctrl+R - Rename current list
• Ctrl+D - Delete current list

Task Management:
• Ctrl+A - Focus add task field
• Enter - Add task (when in entry field)
• Delete - Remove selected task
• Ctrl+E - Edit selected task
• Space - Toggle task done/undone

Navigation:
• ↑ / ↓ - Select previous/next task
• Ctrl+↑ - Move task up
• Ctrl+↓ - Move task down
• Ctrl+Home - Select first task
• Ctrl+End - Select last task

Other:
• Alt+F4 - Exit application
"""
        messagebox.showinfo('Keyboard Shortcuts', shortcuts)


if __name__ == '__main__':
    root = tk.Tk()
    app = TodoApp(root)
    root.mainloop()
