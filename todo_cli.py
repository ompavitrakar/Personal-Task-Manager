#!/usr/bin/env python3
"""
todo_cli.py - CLI front-end for the SQLite todo app.

Commands:
    add       Create a new task
    list      List tasks (optionally filtered by status/priority)
    show      Show full details of a single task
    edit      Edit a task's title/description/priority/status
    priority  Assign/change a task's priority
    status    Assign/change a task's status
    delete    Delete a task
    renumber  Resequence task IDs to be contiguous again (1, 2, 3, ...)

Examples:
    python todo_cli.py add "Buy milk" -d "2% milk, 1 gallon" -p high
    python todo_cli.py list
    python todo_cli.py list --status pending --priority high
    python todo_cli.py priority 3 low
    python todo_cli.py status 3 done
    python todo_cli.py edit 3 --title "Buy oat milk" --description "Trader Joe's"
    python todo_cli.py delete 3
    python todo_cli.py renumber
"""

import argparse
import sys

import todo_core as core


def cmd_add(args):
    task_id = core.create_task(args.title, args.description, args.priority)
    print(f"Created task #{task_id}: {args.title}")


def cmd_list(args):
    rows = core.list_tasks(args.status, args.priority)
    if not rows:
        print("No tasks found.")
        return

    id_w, title_w, prio_w, stat_w = 4, 30, 8, 12
    header = f"{'ID':<{id_w}} {'TITLE':<{title_w}} {'PRIORITY':<{prio_w}} {'STATUS':<{stat_w}}"
    print(header)
    print("-" * len(header))
    for r in rows:
        title = r["title"] if len(r["title"]) <= title_w else r["title"][: title_w - 3] + "..."
        print(f"{r['id']:<{id_w}} {title:<{title_w}} {r['priority']:<{prio_w}} {r['status']:<{stat_w}}")


def cmd_show(args):
    row = core.get_task(args.id)
    print(f"ID:          {row['id']}")
    print(f"Title:       {row['title']}")
    print(f"Description: {row['description'] or '(none)'}")
    print(f"Priority:    {row['priority']}")
    print(f"Status:      {row['status']}")
    print(f"Created:     {row['created_at']}")
    print(f"Updated:     {row['updated_at']}")


def cmd_edit(args):
    changed = core.edit_task(args.id, args.title, args.description, args.priority, args.status)
    if changed:
        print(f"Updated task #{args.id}.")
    else:
        print("Nothing to update. Provide --title, --description, --priority, and/or --status.")


def cmd_priority(args):
    core.set_priority(args.id, args.priority)
    print(f"Task #{args.id} priority set to {args.priority}.")


def cmd_status(args):
    core.set_status(args.id, args.status)
    print(f"Task #{args.id} status set to {args.status}.")


def cmd_delete(args):
    core.delete_task(args.id)
    print(f"Deleted task #{args.id}.")


def cmd_renumber(args):
    count = core.renumber_ids()
    if count:
        print(f"Renumbered {count} task(s). IDs are now contiguous (1..{count}).")
    else:
        print("No tasks to renumber.")


def build_parser():
    parser = argparse.ArgumentParser(description="A simple CLI todo app backed by SQLite.")
    sub = parser.add_subparsers(dest="command", required=True)

    p_add = sub.add_parser("add", help="Create a new task")
    p_add.add_argument("title", help="Task title")
    p_add.add_argument("-d", "--description", default="", help="Task description")
    p_add.add_argument(
        "-p", "--priority", default="medium", choices=core.VALID_PRIORITIES, help="Task priority"
    )
    p_add.set_defaults(func=cmd_add)

    p_list = sub.add_parser("list", help="List tasks")
    p_list.add_argument("--status", choices=core.VALID_STATUSES, help="Filter by status")
    p_list.add_argument("--priority", choices=core.VALID_PRIORITIES, help="Filter by priority")
    p_list.set_defaults(func=cmd_list)

    p_show = sub.add_parser("show", help="Show a single task's details")
    p_show.add_argument("id", type=int, help="Task ID")
    p_show.set_defaults(func=cmd_show)

    p_edit = sub.add_parser("edit", help="Edit a task")
    p_edit.add_argument("id", type=int, help="Task ID")
    p_edit.add_argument("--title", help="New title")
    p_edit.add_argument("--description", help="New description")
    p_edit.add_argument("--priority", choices=core.VALID_PRIORITIES, help="New priority")
    p_edit.add_argument("--status", choices=core.VALID_STATUSES, help="New status")
    p_edit.set_defaults(func=cmd_edit)

    p_priority = sub.add_parser("priority", help="Assign/change a task's priority")
    p_priority.add_argument("id", type=int, help="Task ID")
    p_priority.add_argument("priority", choices=core.VALID_PRIORITIES, help="New priority")
    p_priority.set_defaults(func=cmd_priority)

    p_status = sub.add_parser("status", help="Assign/change a task's status")
    p_status.add_argument("id", type=int, help="Task ID")
    p_status.add_argument("status", choices=core.VALID_STATUSES, help="New status")
    p_status.set_defaults(func=cmd_status)

    p_delete = sub.add_parser("delete", help="Delete a task")
    p_delete.add_argument("id", type=int, help="Task ID")
    p_delete.set_defaults(func=cmd_delete)

    p_renumber = sub.add_parser(
        "renumber", help="Resequence task IDs to be contiguous (fixes gaps left by deletes)"
    )
    p_renumber.set_defaults(func=cmd_renumber)

    return parser


def main():
    core.init_db()
    parser = build_parser()
    args = parser.parse_args()
    try:
        args.func(args)
    except core.ValidationError as e:
        print(f"Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
