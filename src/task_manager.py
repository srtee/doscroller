"""
PiTodoist - Task Manager

High-level functions combining multiple operations for task workflow.
"""

from typing import Any

from .storage import load_tasks
from .task_state import get_active_task, get_active_task_id, set_active_task_id
from .time_tracking import (
    get_current_session_duration,
    get_time_entries_for_task,
    get_total_time_for_task,
    start_task,
    stop_task,
)
from .todoist_sync import mark_complete_remote, mark_complete_local, sync_tasks


# ===== WORKFLOW FUNCTIONS =====

def start_work_on_task(task_id: str, api_token: str) -> bool:
    """
    Start working on a task, syncing to get latest data first.

    This combines:
    1. Sync tasks from Todoist to ensure latest data
    2. Start the task timer

    Args:
        task_id: Task ID to start working on
        api_token: Todoist API token

    Returns:
        True on success, False on failure
    """
    # First, sync to get latest data
    if not sync_tasks(api_token):
        # Sync failed but continue anyway (graceful handling)
        pass

    # Start the task timer
    return start_task(task_id)


def stop_work_on_task(task_id: str) -> bool:
    """
    Stop working on a task (stop timer).

    Args:
        task_id: Task ID to stop working on

    Returns:
        True on success, False on failure
    """
    return stop_task(task_id)


def complete_task(task_id: str, api_token: str) -> bool:
    """
    Stop task timer and mark complete on Todoist.

    This combines:
    1. Stop the task timer if active
    2. Mark task complete on Todoist
    3. Mark task complete locally

    Args:
        task_id: Task ID to complete
        api_token: Todoist API token

    Returns:
        True on success (or partial success), False on total failure
    """
    success = True

    # Stop the task timer if it's currently active
    if get_active_task_id() == task_id:
        if not stop_task(task_id):
            success = False

    # Mark complete on Todoist
    if not mark_complete_remote(task_id, api_token):
        # Remote completion failed, but still mark locally
        success = False

    # Mark complete locally regardless of remote result
    if not mark_complete_local(task_id):
        success = False

    return success


# ===== TASK SUMMARY =====

def get_task_summary(task_id: str) -> dict | None:
    """
    Get comprehensive task info including time spent.

    Args:
        task_id: Task ID to get summary for

    Returns:
        Dictionary with task summary, or None if not found
    """
    tasks = load_tasks()
    for task in tasks:
        if task.get("id") == task_id:
            total_seconds = get_total_time_for_task(task_id)
            time_entries = get_time_entries_for_task(task_id)

            # Check if task is currently active
            is_active = get_active_task_id() == task_id
            current_duration = get_current_session_duration() if is_active else 0

            return {
                "task": task,
                "total_time_seconds": total_seconds,
                "total_time_entries": len(time_entries),
                "is_active": is_active,
                "current_session_duration": current_duration,
                "time_entries": time_entries
            }
    return None


def get_active_task_summary() -> dict | None:
    """
    Get summary for the currently active task.

    Returns:
        Dictionary with active task summary, or None if no active task
    """
    active_task = get_active_task()
    if active_task is None:
        return None

    return get_task_summary(active_task["id"])


# ===== TASK LISTING =====

def get_all_tasks(include_completed: bool = False) -> list[dict]:
    """
    Get all tasks from local cache.

    Args:
        include_completed: Whether to include completed tasks

    Returns:
        List of task dictionaries
    """
    tasks = load_tasks()
    if include_completed:
        return tasks
    return [t for t in tasks if not t.get("is_completed", False)]


def get_active_tasks() -> list[dict]:
    """
    Get tasks that are currently being worked on.
    (In strict mode, this is at most one task.)

    Returns:
        List of active task dictionaries (0 or 1 items)
    """
    active_task = get_active_task()
    return [active_task] if active_task else []


def get_incomplete_tasks() -> list[dict]:
    """
    Get all incomplete tasks from local cache.

    Returns:
        List of incomplete task dictionaries
    """
    return get_all_tasks(include_completed=False)


def get_completed_tasks() -> list[dict]:
    """
    Get all completed tasks from local cache.

    Returns:
        List of completed task dictionaries
    """
    return [t for t in load_tasks() if t.get("is_completed", False)]