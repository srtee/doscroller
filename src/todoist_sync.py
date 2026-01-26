"""
PiTodoist - Todoist API Integration

Synchronizes with Todoist REST API to fetch tasks and mark complete.
"""

from datetime import datetime
from typing import Any

import requests

from .storage import save_tasks, load_tasks
from .task_state import set_last_sync, task_exists, get_task_by_id


# ===== API ENDPOINTS =====

TODOIST_API_BASE = "https://api.todoist.com/rest/v2"


def _make_request(api_token: str, endpoint: str, method: str = "GET", data: Any = None) -> dict | None:
    """
    Make a request to the Todoist API.

    Args:
        api_token: Todoist API token
        endpoint: API endpoint path (e.g., "/tasks")
        method: HTTP method ("GET", "POST", etc.)
        data: Request body data for POST/PUT

    Returns:
        JSON response as dict, or None on failure (silent handling)
    """
    try:
        url = f"{TODOIST_API_BASE}{endpoint}"
        headers = {"Authorization": f"Bearer {api_token}"}

        if method == "GET":
            response = requests.get(url, headers=headers, timeout=30)
        elif method == "POST":
            headers["Content-Type"] = "application/json"
            response = requests.post(url, headers=headers, json=data, timeout=30)
        elif method == "POST_FORM":
            headers["Content-Type"] = "application/x-www-form-urlencoded"
            response = requests.post(url, headers=headers, data=data, timeout=30)
        else:
            return None

        response.raise_for_status()

        if response.text:
            return response.json()
        return {}

    except (requests.RequestException, ValueError):
        return None


# ===== TASK FETCHING =====

def fetch_tasks_from_api(api_token: str) -> list[dict]:
    """
    Fetch all tasks from Todoist API.

    Args:
        api_token: Todoist API token

    Returns:
        List of task dictionaries, or empty list on failure
    """
    data = _make_request(api_token, "/tasks", method="GET")
    if data is None:
        return []
    return data if isinstance(data, list) else []


def _convert_todoist_task(todoist_task: dict) -> dict:
    """
    Convert a Todoist API task to local format.

    Args:
        todoist_task: Task from Todoist API

    Returns:
        Task in local format
    """
    return {
        "id": todoist_task.get("id"),
        "content": todoist_task.get("content", ""),
        "description": todoist_task.get("description") or None,
        "due_date": todoist_task.get("due", {}).get("datetime") if todoist_task.get("due") else None,
        "priority": todoist_task.get("priority", 1),
        "project_id": todoist_task.get("project_id"),
        "labels": todoist_task.get("labels", []),
        "is_completed": todoist_task.get("is_completed", False),
        "completed_at": todoist_task.get("completed_at") or None,
        "order": todoist_task.get("order", 0),
        "url": todoist_task.get("url") or None
    }


def save_tasks_locally(tasks: list[dict]) -> bool:
    """
    Save tasks to local cache.

    Args:
        tasks: List of task dictionaries

    Returns:
        True on success, False on failure
    """
    return save_tasks(tasks)


def load_tasks_locally() -> list[dict]:
    """
    Load tasks from local cache.

    Returns:
        List of task dictionaries, or empty list on failure
    """
    return load_tasks()


def sync_tasks(api_token: str) -> bool:
    """
    Perform full sync (fetch from API and save locally).

    Args:
        api_token: Todoist API token

    Returns:
        True on success, False on failure
    """
    # Fetch tasks from API
    todoist_tasks = fetch_tasks_from_api(api_token)
    if not todoist_tasks:
        # Empty result could be valid (no tasks) or failure
        # Save empty list and continue
        tasks = []
    else:
        # Convert to local format
        tasks = [_convert_todoist_task(t) for t in todoist_tasks]

    # Save locally
    if not save_tasks_locally(tasks):
        return False

    # Update last sync timestamp
    timestamp = datetime.utcnow().isoformat() + "Z"
    set_last_sync(timestamp)

    return True


# ===== TASK COMPLETION =====

def mark_complete_remote(task_id: str, api_token: str) -> bool:
    """
    Mark task complete on Todoist.

    Args:
        task_id: Task ID to mark complete
        api_token: Todoist API token

    Returns:
        True on success, False on failure
    """
    # Use POST to close endpoint
    data = _make_request(api_token, f"/tasks/{task_id}/close", method="POST")
    return data is not None


def mark_complete_local(task_id: str) -> bool:
    """
    Mark task complete locally only (does not sync to Todoist).

    Args:
        task_id: Task ID to mark complete

    Returns:
        True on success, False on failure
    """
    tasks = load_tasks()

    updated = False
    for task in tasks:
        if task.get("id") == task_id:
            task["is_completed"] = True
            task["completed_at"] = datetime.utcnow().isoformat() + "Z"
            updated = True
            break

    if not updated:
        return False

    return save_tasks(tasks)


# ===== TASK CREATION (Optional Future Feature) =====

def create_task_remote(content: str, api_token: str, **kwargs) -> dict | None:
    """
    Create a new task on Todoist (optional future feature).

    Args:
        content: Task content/title
        api_token: Todoist API token
        **kwargs: Additional task fields (due_date, priority, etc.)

    Returns:
        Created task dict, or None on failure
    """
    data = {"content": content}
    data.update(kwargs)

    return _make_request(api_token, "/tasks", method="POST", data=data)


# ===== HELPER FUNCTIONS =====

def get_api_status(api_token: str) -> bool:
    """
    Check if API token is valid by making a simple request.

    Args:
        api_token: Todoist API token

    Returns:
        True if valid, False otherwise
    """
    data = _make_request(api_token, "/projects", method="GET")
    return data is not None