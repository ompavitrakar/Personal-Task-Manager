"""
todo_core.py - Shared SQLite logic used by both the CLI (todo_cli.py) and
the desktop GUI (todo_gui.py). Keeping this logic in one place means both
interfaces stay in sync and always read/write the same database file.
"""

import os
import sqlite3
from datetime import datetime

DB_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "todo.db")

VALID_PRIORITIES = ["low", "medium", "high"]
VALID_STATUSES = ["pending", "in-progress", "done"]


class ValidationError(Exception):
    """Raised when a caller passes an invalid priority/status/id."""


# --------------------------------------------------------------------------
# Database setup
# --------------------------------------------------------------------------

def get_connection():
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_connection()
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS tasks (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            title       TEXT NOT NULL,
            description TEXT DEFAULT '',
            priority    TEXT NOT NULL DEFAULT 'medium',
            status      TEXT NOT NULL DEFAULT 'pending',
            created_at  TEXT NOT NULL,
            updated_at  TEXT NOT NULL
        )
        """
    )
    conn.commit()
    conn.close()


def now():
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def validate_choice(value, choices, field_name):
    value = value.lower().strip()
    if value not in choices:
        raise ValidationError(
            f"invalid {field_name} '{value}'. Must be one of: {', '.join(choices)}"
        )
    return value


# --------------------------------------------------------------------------
# Core operations
# --------------------------------------------------------------------------

def create_task(title, description="", priority="medium"):
    priority = validate_choice(priority, VALID_PRIORITIES, "priority")
    conn = get_connection()
    ts = now()
    cur = conn.execute(
        "INSERT INTO tasks (title, description, priority, status, created_at, updated_at) "
        "VALUES (?, ?, ?, ?, ?, ?)",
        (title, description, priority, "pending", ts, ts),
    )
    conn.commit()
    task_id = cur.lastrowid
    conn.close()
    return task_id


def list_tasks(status_filter=None, priority_filter=None):
    conn = get_connection()
    query = "SELECT * FROM tasks WHERE 1=1"
    params = []
    if status_filter:
        query += " AND status = ?"
        params.append(validate_choice(status_filter, VALID_STATUSES, "status"))
    if priority_filter:
        query += " AND priority = ?"
        params.append(validate_choice(priority_filter, VALID_PRIORITIES, "priority"))
    query += " ORDER BY CASE priority WHEN 'high' THEN 0 WHEN 'medium' THEN 1 ELSE 2 END, id"

    rows = conn.execute(query, params).fetchall()
    conn.close()
    return rows


def get_task(task_id):
    conn = get_connection()
    row = conn.execute("SELECT * FROM tasks WHERE id = ?", (task_id,)).fetchone()
    conn.close()
    if row is None:
        raise ValidationError(f"no task found with id {task_id}")
    return row


def edit_task(task_id, title=None, description=None, priority=None, status=None):
    get_task(task_id)  # raises if it doesn't exist

    updates = []
    params = []
    if title is not None:
        updates.append("title = ?")
        params.append(title)
    if description is not None:
        updates.append("description = ?")
        params.append(description)
    if priority is not None:
        updates.append("priority = ?")
        params.append(validate_choice(priority, VALID_PRIORITIES, "priority"))
    if status is not None:
        updates.append("status = ?")
        params.append(validate_choice(status, VALID_STATUSES, "status"))

    if not updates:
        return False

    updates.append("updated_at = ?")
    params.append(now())
    params.append(task_id)

    conn = get_connection()
    conn.execute(f"UPDATE tasks SET {', '.join(updates)} WHERE id = ?", params)
    conn.commit()
    conn.close()
    return True


def set_priority(task_id, priority):
    return edit_task(task_id, priority=priority)


def set_status(task_id, status):
    return edit_task(task_id, status=status)


def delete_task(task_id):
    get_task(task_id)  # raises if it doesn't exist
    conn = get_connection()
    conn.execute("DELETE FROM tasks WHERE id = ?", (task_id,))
    conn.commit()
    conn.close()


def renumber_ids():
    """
    Resequence task IDs to be contiguous starting at 1, in their current
    (priority-sorted) order stays untouched here - this renumbers by
    original id order, which is the order tasks were created in. This is
    what fixes the "IDs just keep climbing forever" issue after deletes.

    Returns the number of tasks renumbered.
    """
    conn = get_connection()
    rows = conn.execute("SELECT id FROM tasks ORDER BY id").fetchall()
    if not rows:
        conn.close()
        return 0

    # Shift everything to a temporary high range first so we never collide
    # with an existing id while reassigning (ids 1..N are likely already taken).
    max_id = rows[-1]["id"]
    offset = max_id + len(rows) + 1000

    conn.execute("BEGIN TRANSACTION")
    for new_id, row in enumerate(rows, start=1):
        conn.execute("UPDATE tasks SET id = ? WHERE id = ?", (new_id + offset, row["id"]))
    for new_id, row in enumerate(rows, start=1):
        conn.execute("UPDATE tasks SET id = ? WHERE id = ?", (new_id, new_id + offset))

    # Reset the AUTOINCREMENT counter so the next new task continues from N, not from the old max.
    conn.execute("DELETE FROM sqlite_sequence WHERE name = 'tasks'")
    conn.execute("INSERT INTO sqlite_sequence (name, seq) VALUES ('tasks', ?)", (len(rows),))

    conn.commit()
    conn.close()
    return len(rows)
