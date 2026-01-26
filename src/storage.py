"""
PiTodoist - Data Storage Layer

Provides JSON file read/write functionality for local data persistence.
"""

import json
import os
from datetime import datetime
from pathlib import Path
from typing import Any


# Data directory paths
DATA_DIR = Path(__file__).parent.parent / "data"
EXPORTS_DIR = Path(__file__).parent.parent / "exports"

# File paths
TASKS_FILE = DATA_DIR / "tasks.json"
TIME_TRACKING_FILE = DATA_DIR / "time_tracking.json"
STATE_FILE = DATA_DIR / "state.json"


def _ensure_directories() -> None:
    """Ensure data and exports directories exist."""
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    EXPORTS_DIR.mkdir(parents=True, exist_ok=True)


def _read_json(filepath: Path) -> Any:
    """
    Read JSON file and return parsed data.

    Returns None if file doesn't exist or on parse error (silent handling).
    """
    try:
        if not filepath.exists():
            return None
        with open(filepath, "r", encoding="utf-8") as f:
            return json.load(f)
    except (json.JSONDecodeError, IOError):
        return None


def _write_json(filepath: Path, data: Any) -> bool:
    """
    Write data to JSON file.

    Returns True on success, False on failure (silent handling).
    """
    try:
        _ensure_directories()
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        return True
    except IOError:
        return False


# ===== TASKS STORAGE =====

def save_tasks(tasks: list[dict]) -> bool:
    """
    Save tasks to local cache.

    Args:
        tasks: List of task dictionaries

    Returns:
        True on success, False on failure
    """
    data = {
        "version": "1",
        "last_updated": datetime.utcnow().isoformat() + "Z",
        "tasks": tasks
    }
    return _write_json(TASKS_FILE, data)


def load_tasks() -> list[dict]:
    """
    Load tasks from local cache.

    Returns:
        List of task dictionaries, or empty list on failure
    """
    data = _read_json(TASKS_FILE)
    if data is None or "tasks" not in data:
        return []
    return data["tasks"]


# ===== TIME TRACKING STORAGE =====

def save_time_entries(entries: list[dict]) -> bool:
    """
    Save time tracking entries to local storage.

    Args:
        entries: List of time entry dictionaries

    Returns:
        True on success, False on failure
    """
    data = {
        "version": "1",
        "entries": entries
    }
    return _write_json(TIME_TRACKING_FILE, data)


def load_time_entries() -> list[dict]:
    """
    Load time tracking entries from local storage.

    Returns:
        List of time entry dictionaries, or empty list on failure
    """
    data = _read_json(TIME_TRACKING_FILE)
    if data is None or "entries" not in data:
        return []
    return data["entries"]


# ===== STATE STORAGE =====

def save_state(state: dict) -> bool:
    """
    Save application state to local storage.

    Args:
        state: State dictionary

    Returns:
        True on success, False on failure
    """
    data = {
        "version": "1",
        "state": state
    }
    return _write_json(STATE_FILE, data)


def load_state() -> dict:
    """
    Load application state from local storage.

    Returns:
        State dictionary, or default empty state on failure
    """
    data = _read_json(STATE_FILE)
    if data is None or "state" not in data:
        return {
            "active_task_id": None,
            "current_time_entry_id": None,
            "session_start": None,
            "last_sync": None
        }
    return data["state"]


# ===== FILE PATHS =====

def get_tasks_filepath() -> Path:
    """Get the tasks.json file path."""
    return TASKS_FILE


def get_time_tracking_filepath() -> Path:
    """Get the time_tracking.json file path."""
    return TIME_TRACKING_FILE


def get_state_filepath() -> Path:
    """Get the state.json file path."""
    return STATE_FILE


def get_exports_dir() -> Path:
    """Get the exports directory path."""
    _ensure_directories()
    return EXPORTS_DIR