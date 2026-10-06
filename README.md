# Personal-Task-Manager
A lightweight todo app with two interfaces, a CLI and a GUI to be more user-friendly, both of which are connected to same local SQLite database. Create tasks, assign priorities, track status, write detailed descriptions.

####Features:

    Create tasks with title, description(optional), and priority (medium by default).
    Assign priority [low, medium, high] at creation of the task or after creating the task.
    Tasks with different priority will be highlighted with different colour.
    Track status of the task if it is pending, in-progress, or done.
    Edit any task's title, description, priority, or status.
    delete tasks if you no longer need them.
    shared SQLite database for the CLI and GUI programs.

Todo is my final project for cs50x. It is kind of a task manager that runs 2 interfaces, CLI (command line interface) and GUI (graphical user interface) build with tkinter. Both use the same SQLite database, i firstly started with CLI bus as i moved forward i felt it was getting more and more tedious for the user so had to learn how to move it to GUI. As this was my first independent project i marked a boundary for myself early on and focused on only few core features instead of 10. The core requirement I set for myself were create a task, give it a priority, give it a status, and be able to edit any of that later. to further manage my project i divided my project across 3 files 1 for core functions and others for CLI and GUI. this splitting was one of the more important design decision for me. Early on, I wrote everything as one script with argparse, and it worked fine for the CLI but as soon as i started thinking about GUI i realized i'd either have to duplicate database functions or import CLI script and deal with its if__name__ == "__main__" structure. instead i took all SQLite code used to create, insert, update, delete and validate into its own separate file todo_core.py. then both todo_cli.py and todo_gui imported it and called the same function.

this in turn made things straight for me, I could build and test the CLI first, then add the GUI on top.

todo_core.py defines schema an id, title, description, priority, status, and timestamp for when the task was created. and functions like create_task, edit_task, set_priority, set_status, delete_task, and list_tasks, which can then support sorting by status and priority. there is also a ValidationError if something invalid is passed in like something that is not [low, high, medium] for priority or something other than [done, pending, in-progress] for status, so the program can handle bad input.

todo_cli.py is the command-line interface, built with argparse and subcommands (add, list, show, edit, priority, status, delete, renumber).

todo_gui.py is the desktop interface, built with Tkinter's ttk widgets. It shows all tasks in a sortable table, color-coded by priority, with dropdown filters for status and priority at the top. Selecting a task and clicking Edit, Change Priority, Change Status, or Delete opens a small popup dialog, double-clicking a row opens the edit dialog directly.

A problem I ran into very later, when I was testing deletions, SQLite's AUTOINCREMENT never reuses an ID, so after adding and deleting a few tasks during testing, my IDs looked like 1, 2, 5, 9, 14 instead of a clean sequence. My first responce was to just not use AUTOINCREMENT, but that created its own problems. Instead I added a renumber_ids function that reassigns every task's ID to be contiguous again and resets SQLite's internal sequence counter to match. it first shifts every row to a temporary high range, then reassigns the final IDs a two-pass update inside a single transaction. I added this as renumber command in the CLI and a "Refresh IDs" button in the GUI.

####Requirements:

    Python 3.7+
    SQLite3
    tkinter

####Files:

    todo_core.py - Core Functions are defined here for both interfaces to work.
    todo_cli.py - Command line interface for command line program.
    todo_gui.py - Tkinter desktop interface for graphical user interface.
    todo.db - SQLite3 database file, created automatically of first launch shared between both interfaces and used by todo_core.py
