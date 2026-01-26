"""
PiTodoist - Task State Management

Manages which task is currently active (displayed and being worked on).
"""

from typing import Any

from .storage import load_state, save_state, load_tasks


# ===== ACTIVE TASK MANAGEMENT =====

def get_active_task_id() -> str | None:
    """
    Get the ID of the currently active task.

    Returns:
        Task ID string, or None if no task is active
    """
    state = load_state()
    return state.get("active_task_id")


def set_active_task_id(task_id: str | None) -> bool:
    """
    Set the active task ID.

    Args:
        task_id: Task ID to set as active, or None to clear

    Returns:
        True on success, False on failure
    """
    state = load_state()
    state["active_task_id"] = task_id
    return save_state(state)


def get_active_task() -> dict | None:
    """
    Get the currently active task object.

    Returns:
        Task dictionary, or None if no task is active
    """
    active_task_id = get_active_task_id()
    if active_task_id is None:
        return None

    tasks = load_tasks()
    for task in tasks:
        if task.get("id") == active_task_id:
            return task
    return None


def is_task_active(task_id: str) -> bool:
    """
    Check if a task is currently active.

    Args:
        task_id: Task ID to check

    Returns:
        True if task is active, False otherwise
    """
    return get_active_task_id() == task_id


def clear_active_task() -> bool:
    """
    Clear the active task (set to None).

    Returns:
        True on success, False on failure
    """
    return set_active_task_id(None)


# ===== CURRENT TIME ENTRY ID TRACKING =====

def get_current_time_entry_id() -> str | None:
    """
    Get the ID of the currently running time entry.

    Returns:
        Time entry ID string, or None if no entry is running
    """
    state = load_state()
    return state.get("current_time_entry_id")


def set_current_time_entry_id(entry_id: str | None) -> bool:
    """
    Set the current time entry ID.

    Args:
        entry_id: Time entry ID to set, or None to clear

    Returns:
        True on success, False on failure
    """
    state = load_state()
    state["current_time_entry_id"] = entry_id
    return save_state(state)


def clear_current_time_entry_id() -> bool:
    """
    Clear the current time entry ID.

    Returns:
        True on success, False on failure
    """
    return set_current_time_entry_id(None)


# ===== SESSION TRACKING =====

def get_session_start() -> str | None:
    """
    Get the session start timestamp.

    Returns:
        ISO 8601 datetime string, or None if not set
    """
    state = load_state()
    return state.get("session_start")


def set_session_start(timestamp: str | None) -> bool:
    """
    Set the session start timestamp.

    Args:
        timestamp: ISO 8601 datetime string, or None to clear

    Returns:
        True on success, False on failure
    """
    state = load_state()
    state["session_start"] = timestamp
    return save_state(state)


def start_session(timestamp: str) -> bool:
    """
    Start a new session with the given timestamp.

    Args:
        timestamp: ISO 8601 datetime string

    Returns:
        True on success, False on failure
    """
    return set_session_start(timestamp)


def clear_session() -> bool:
    """
    Clear the session information.

    Returns:
        True on success, False on failure
    """
    state = load_state()
    state["session_start"] = None
    return save_state(state)


# ===== LAST SYNC TRACKING =====

def get_last_sync() -> str | None:
    """
    Get the timestamp of the last Todoist sync.

    Returns:
        ISO 8601 datetime string, or None if never synced
    """
    state = load_state()
    return state.get("last_sync")


def set_last_sync(timestamp: str | None) -> bool:
    """
    Set the timestamp of the last Todoist sync.

    Args:
        timestamp: ISO 8601 datetime string, or None to clear

    Returns:
        True on success, False on failure
    """
    state = load_state()
    state["last_sync"] = timestamp
    return save_state(state)


def update_last_sync(timestamp: str) -> bool:
    """
    Update the last sync timestamp.

    Args:
        timestamp: ISO 8601 datetime string

    Returns:
        True on success, False on failure
    """
    return set_last_sync(timestamp)


# ===== TASK LOOKUP =====

def get_task_by_id(task_id: str) -> dict | None:
    """
    Get a task by its ID.

    Args:
        task_id: Task ID to look up

    Returns:
        Task dictionary, or None if not found
    """
    tasks = load_tasks()
    for task in tasks:
        if task.get("id") == task_id:
            return task
    return None


def task_exists(task_id: str) -> bool:
    """
    Check if a task exists in the local cache.

    Args:
        task_id: Task ID to check

    Returns:
        True if task exists, False otherwise
    """
    return get_task_by_id(task_id) is not None