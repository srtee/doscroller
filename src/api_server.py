"""
PiTodoist - Web API Server

Flask web server that exposes Python backend functions as HTTP endpoints.
"""

import os
from functools import wraps
from typing import Any

from flask import Flask, jsonify, request, send_from_directory
from flask_cors import CORS

from .task_manager import (
    complete_task,
    get_all_tasks,
    get_completed_tasks,
    get_incomplete_tasks,
    get_task_summary,
    start_work_on_task,
    stop_work_on_task,
)
from .time_tracking import get_total_time_for_task
from .todoist_sync import sync_tasks


# ===== FLASK APP SETUP =====

app = Flask(__name__)
CORS(app)


# ===== HELPER FUNCTIONS =====

def _get_api_token() -> str | None:
    """
    Get API token from Authorization header.

    Returns:
        Token string, or None if not found or invalid format
    """
    auth_header = request.headers.get("Authorization")
    if auth_header and auth_header.startswith("Bearer "):
        return auth_header[7:]  # Remove "Bearer " prefix
    return None


def _success_response(data: Any = None) -> tuple[dict, int]:
    """
    Create a successful API response.

    Args:
        data: Response data

    Returns:
        Tuple of (response_dict, status_code)
    """
    response = {"success": True, "data": data, "error": None}
    return response, 200


def _error_response(message: str, status_code: int = 400) -> tuple[dict, int]:
    """
    Create an error API response.

    Args:
        message: Error message
        status_code: HTTP status code

    Returns:
        Tuple of (response_dict, status_code)
    """
    response = {"success": False, "data": None, "error": message}
    return response, status_code


def _require_token(f):
    """
    Decorator to require API token for Todoist endpoints.

    The token is extracted from the Authorization header and passed as
    the `api_token` argument to the decorated function.
    """
    @wraps(f)
    def decorated(*args, **kwargs):
        api_token = _get_api_token()
        if api_token is None:
            return _error_response("Authorization token required", 401)
        kwargs["api_token"] = api_token
        return f(*args, **kwargs)
    return decorated


# ===== STATIC FILE SERVING =====

@app.route("/")
def index():
    """Serve the main HTML page."""
    return send_from_directory(os.path.dirname(__file__) + "/../", "index.html")


@app.route("/styles.css")
def styles():
    """Serve the CSS file."""
    return send_from_directory(os.path.dirname(__file__) + "/../", "styles.css")


@app.route("/app.js")
def app_js():
    """Serve the JavaScript file."""
    return send_from_directory(os.path.dirname(__file__) + "/../", "app.js")


# ===== API ENDPOINTS =====

@app.route("/api/tasks")
def api_get_tasks():
    """
    Fetch all incomplete tasks.

    Returns:
        JSON with success, data, error fields
    """
    try:
        tasks = get_incomplete_tasks()
        return _success_response(tasks)
    except Exception as e:
        return _error_response(str(e), 500)


@app.route("/api/tasks/completed")
def api_get_completed_tasks():
    """
    Fetch all completed tasks, sorted newest first.

    Returns:
        JSON with success, data, error fields
    """
    try:
        tasks = get_completed_tasks()
        # Sort by completed_at (newest first)
        tasks.sort(key=lambda t: t.get("completed_at") or "", reverse=True)
        return _success_response(tasks)
    except Exception as e:
        return _error_response(str(e), 500)


@app.route("/api/task/<task_id>")
def api_get_task(task_id: str):
    """
    Get details for a specific task.

    Args:
        task_id: Task ID

    Returns:
        JSON with success, data, error fields
    """
    try:
        summary = get_task_summary(task_id)
        if summary is None:
            return _error_response("Task not found", 404)
        return _success_response(summary)
    except Exception as e:
        return _error_response(str(e), 500)


@app.route("/api/active")
def api_get_active():
    """
    Get the currently active task.

    Returns:
        JSON with success, data, error fields
    """
    try:
        from .task_manager import get_active_task_summary
        summary = get_active_task_summary()
        return _success_response(summary)
    except Exception as e:
        return _error_response(str(e), 500)


@app.route("/api/start/<task_id>", methods=["POST"])
@_require_token
def api_start_task(task_id: str, api_token: str):
    """
    Start timing a task.

    Args:
        task_id: Task ID
        api_token: Todoist API token (injected by decorator)

    Returns:
        JSON with success, data, error fields
    """
    try:
        result = start_work_on_task(task_id, api_token)
        if result:
            from .task_manager import get_active_task_summary
            summary = get_active_task_summary()
            return _success_response(summary)
        return _error_response("Failed to start task", 500)
    except Exception as e:
        return _error_response(str(e), 500)


@app.route("/api/stop/<task_id>", methods=["POST"])
def api_stop_task(task_id: str):
    """
    Stop timing a task.

    Args:
        task_id: Task ID

    Returns:
        JSON with success, data, error fields
    """
    try:
        result = stop_work_on_task(task_id)
        if result:
            return _success_response({"stopped": True})
        return _error_response("Failed to stop task", 500)
    except Exception as e:
        return _error_response(str(e), 500)


@app.route("/api/complete/<task_id>", methods=["POST"])
@_require_token
def api_complete_task(task_id: str, api_token: str):
    """
    Mark a task as complete.

    Args:
        task_id: Task ID
        api_token: Todoist API token (injected by decorator)

    Returns:
        JSON with success, data, error fields
    """
    try:
        result = complete_task(task_id, api_token)
        if result:
            return _success_response({"completed": True})
        return _error_response("Failed to complete task", 500)
    except Exception as e:
        return _error_response(str(e), 500)


@app.route("/api/time/<task_id>")
def api_get_time(task_id: str):
    """
    Get total time spent on a task.

    Args:
        task_id: Task ID

    Returns:
        JSON with success, data, error fields
    """
    try:
        total_seconds = get_total_time_for_task(task_id)
        return _success_response({"task_id": task_id, "total_seconds": total_seconds})
    except Exception as e:
        return _error_response(str(e), 500)


@app.route("/api/sync")
@_require_token
def api_sync(api_token: str):
    """
    Sync tasks with Todoist.

    Args:
        api_token: Todoist API token (injected by decorator)

    Returns:
        JSON with success, data, error fields
    """
    try:
        result = sync_tasks(api_token)
        if result:
            tasks = get_incomplete_tasks()
            return _success_response({"synced": True, "task_count": len(tasks)})
        return _error_response("Sync failed", 500)
    except Exception as e:
        return _error_response(str(e), 500)


# ===== SERVER ENTRY POINT =====

def run_server(host: str = "127.0.0.1", port: int = 5000, debug: bool = False):
    """
    Run the Flask development server.

    Args:
        host: Host address to bind to
        port: Port to listen on
        debug: Enable debug mode
    """
    print(f"Starting PiTodoist API server on http://{host}:{port}")
    app.run(host=host, port=port, debug=debug)


if __name__ == "__main__":
    run_server()