#!/usr/bin/env python3
"""
todo_gui.py - Desktop GUI front-end for the SQLite todo app, built with
Tkinter (part of the Python standard library, no extra install needed).

Uses the exact same todo_core.py module and todo.db database file as
todo_cli.py, so tasks created in one show up in the other.

Run with:
    python todo_gui.py
"""

import tkinter as tk
from tkinter import ttk, messagebox

import todo_core as core

PRIORITY_COLORS = {"high": "#d9534f", "medium": "#f0ad4e", "low": "#5cb85c"}


class TodoApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Todo")
        self.geometry("760x480")
        self.minsize(620, 400)

        core.init_db()

        self.status_filter = tk.StringVar(value="all")
        self.priority_filter = tk.StringVar(value="all")

        self._build_layout()
        self.refresh_list()

    # ------------------------------------------------------------------
    # Layout
    # ------------------------------------------------------------------

    def _build_layout(self):
        top = ttk.Frame(self, padding=10)
        top.pack(fill="x")

        ttk.Label(top, text="Status:").pack(side="left")
        status_menu = ttk.OptionMenu(
            top, self.status_filter, "all", "all", *core.VALID_STATUSES,
            command=lambda _: self.refresh_list(),
        )
        status_menu.pack(side="left", padx=(4, 12))

        ttk.Label(top, text="Priority:").pack(side="left")
        priority_menu = ttk.OptionMenu(
            top, self.priority_filter, "all", "all", *core.VALID_PRIORITIES,
            command=lambda _: self.refresh_list(),
        )
        priority_menu.pack(side="left", padx=(4, 12))

        ttk.Button(top, text="Refresh IDs", command=self.on_renumber).pack(side="right")
        ttk.Button(top, text="+ New Task", command=self.on_add).pack(side="right", padx=(0, 8))

        # Task table
        columns = ("id", "title", "priority", "status")
        self.tree = ttk.Treeview(self, columns=columns, show="headings", selectmode="browse")
        self.tree.heading("id", text="ID")
        self.tree.heading("title", text="Title")
        self.tree.heading("priority", text="Priority")
        self.tree.heading("status", text="Status")
        self.tree.column("id", width=50, anchor="center")
        self.tree.column("title", width=380)
        self.tree.column("priority", width=100, anchor="center")
        self.tree.column("status", width=110, anchor="center")
        self.tree.pack(fill="both", expand=True, padx=10)
        self.tree.bind("<Double-1>", lambda e: self.on_edit())

        for prio, color in PRIORITY_COLORS.items():
            self.tree.tag_configure(prio, foreground=color)

        # Bottom action bar
        bottom = ttk.Frame(self, padding=10)
        bottom.pack(fill="x")
        ttk.Button(bottom, text="Edit", command=self.on_edit).pack(side="left")
        ttk.Button(bottom, text="Change Priority", command=self.on_change_priority).pack(
            side="left", padx=8
        )
        ttk.Button(bottom, text="Change Status", command=self.on_change_status).pack(side="left")
        ttk.Button(bottom, text="Delete", command=self.on_delete).pack(side="right")

    # ------------------------------------------------------------------
    # Data refresh
    # ------------------------------------------------------------------

    def refresh_list(self):
        for row in self.tree.get_children():
            self.tree.delete(row)

        status = None if self.status_filter.get() == "all" else self.status_filter.get()
        priority = None if self.priority_filter.get() == "all" else self.priority_filter.get()

        for row in core.list_tasks(status, priority):
            self.tree.insert(
                "", "end", iid=str(row["id"]),
                values=(row["id"], row["title"], row["priority"], row["status"]),
                tags=(row["priority"],),
            )

    def get_selected_id(self):
        selection = self.tree.selection()
        if not selection:
            messagebox.showinfo("No selection", "Select a task first.")
            return None
        return int(selection[0])

    # ------------------------------------------------------------------
    # Actions
    # ------------------------------------------------------------------

    def on_add(self):
        TaskDialog(self, on_submit=self.handle_create)

    def handle_create(self, title, description, priority):
        if not title.strip():
            messagebox.showerror("Missing title", "Title can't be empty.")
            return False
        core.create_task(title.strip(), description.strip(), priority)
        self.refresh_list()
        return True

    def on_edit(self):
        task_id = self.get_selected_id()
        if task_id is None:
            return
        row = core.get_task(task_id)
        TaskDialog(
            self,
            title_text="Edit Task",
            initial_title=row["title"],
            initial_description=row["description"],
            initial_priority=row["priority"],
            on_submit=lambda t, d, p: self.handle_edit(task_id, t, d, p),
        )

    def handle_edit(self, task_id, title, description, priority):
        if not title.strip():
            messagebox.showerror("Missing title", "Title can't be empty.")
            return False
        core.edit_task(task_id, title.strip(), description.strip(), priority)
        self.refresh_list()
        return True

    def on_change_priority(self):
        task_id = self.get_selected_id()
        if task_id is None:
            return
        row = core.get_task(task_id)
        ChoiceDialog(
            self, "Change Priority", core.VALID_PRIORITIES, row["priority"],
            on_submit=lambda val: self._apply_priority(task_id, val),
        )

    def _apply_priority(self, task_id, value):
        core.set_priority(task_id, value)
        self.refresh_list()

    def on_change_status(self):
        task_id = self.get_selected_id()
        if task_id is None:
            return
        row = core.get_task(task_id)
        ChoiceDialog(
            self, "Change Status", core.VALID_STATUSES, row["status"],
            on_submit=lambda val: self._apply_status(task_id, val),
        )

    def _apply_status(self, task_id, value):
        core.set_status(task_id, value)
        self.refresh_list()

    def on_delete(self):
        task_id = self.get_selected_id()
        if task_id is None:
            return
        row = core.get_task(task_id)
        if messagebox.askyesno("Delete task", f"Delete task #{task_id}: \"{row['title']}\"?"):
            core.delete_task(task_id)
            self.refresh_list()

    def on_renumber(self):
        if messagebox.askyesno(
            "Refresh IDs",
            "Resequence all task IDs to be contiguous again (1, 2, 3, ...)?\n"
            "This fixes gaps left by deleted tasks.",
        ):
            count = core.renumber_ids()
            self.refresh_list()
            messagebox.showinfo("Done", f"Renumbered {count} task(s).")


class TaskDialog(tk.Toplevel):
    """Popup used for both creating and editing a task."""

    def __init__(
        self, parent, on_submit, title_text="New Task",
        initial_title="", initial_description="", initial_priority="medium",
    ):
        super().__init__(parent)
        self.title(title_text)
        self.resizable(False, False)
        self.on_submit = on_submit
        self.transient(parent)
        self.grab_set()

        pad = {"padx": 10, "pady": 6}

        ttk.Label(self, text="Title").grid(row=0, column=0, sticky="w", **pad)
        self.title_entry = ttk.Entry(self, width=40)
        self.title_entry.insert(0, initial_title)
        self.title_entry.grid(row=0, column=1, **pad)

        ttk.Label(self, text="Description").grid(row=1, column=0, sticky="nw", **pad)
        self.desc_text = tk.Text(self, width=30, height=4)
        self.desc_text.insert("1.0", initial_description)
        self.desc_text.grid(row=1, column=1, **pad)

        ttk.Label(self, text="Priority").grid(row=2, column=0, sticky="w", **pad)
        self.priority_var = tk.StringVar(value=initial_priority)
        ttk.OptionMenu(
            self, self.priority_var, initial_priority, *core.VALID_PRIORITIES
        ).grid(row=2, column=1, sticky="w", **pad)

        btn_frame = ttk.Frame(self)
        btn_frame.grid(row=3, column=0, columnspan=2, pady=(4, 10))
        ttk.Button(btn_frame, text="Save", command=self._submit).pack(side="left", padx=6)
        ttk.Button(btn_frame, text="Cancel", command=self.destroy).pack(side="left")

        self.title_entry.focus_set()

    def _submit(self):
        title = self.title_entry.get()
        description = self.desc_text.get("1.0", "end").strip()
        priority = self.priority_var.get()
        if self.on_submit(title, description, priority):
            self.destroy()


class ChoiceDialog(tk.Toplevel):
    """Small popup for picking one of a fixed set of values (priority/status)."""

    def __init__(self, parent, title_text, choices, current, on_submit):
        super().__init__(parent)
        self.title(title_text)
        self.resizable(False, False)
        self.on_submit = on_submit
        self.transient(parent)
        self.grab_set()

        self.var = tk.StringVar(value=current)
        frame = ttk.Frame(self, padding=15)
        frame.pack()
        for choice in choices:
            ttk.Radiobutton(frame, text=choice, value=choice, variable=self.var).pack(
                anchor="w", pady=2
            )

        btn_frame = ttk.Frame(self, padding=(0, 0, 0, 10))
        btn_frame.pack()
        ttk.Button(btn_frame, text="Save", command=self._submit).pack(side="left", padx=6)
        ttk.Button(btn_frame, text="Cancel", command=self.destroy).pack(side="left")

    def _submit(self):
        self.on_submit(self.var.get())
        self.destroy()


if __name__ == "__main__":
    app = TodoApp()
    app.mainloop()
