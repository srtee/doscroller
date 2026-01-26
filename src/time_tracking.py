"""
PiTodoist - Time Tracking

Tracks time spent on tasks with start/stop functionality and CSV export.
"""

import csv
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any

from .storage import load_time_entries, save_time_entries, get_exports_dir
from .task_state import get_active_task_id, set_active_task_id, set_current_time_entry_id, task_exists


# ===== TIME ENTRY MANAGEMENT =====

def _generate_entry_id() -> str:
    """Generate a unique time entry ID."""
    return f"time-{uuid.uuid4().hex[:12]}"


def _now_iso() -> str:
    """Get current UTC time as ISO 8601 string."""
    return datetime.utcnow().isoformat() + "Z"


def record_time_entry(task_id: str, start: str, stop: str | None = None, notes: str | None = None) -> bool:
    """
    Record a time tracking entry.

    Args:
        task_id: Task ID to associate with the entry
        start: ISO 8601 datetime string when work started
        stop: ISO 8601 datetime string when work stopped, or None if active
        notes: Optional notes about this session

    Returns:
        True on success, False on failure
    """
    entries = load_time_entries()

    entry = {
        "entry_id": _generate_entry_id(),
        "task_id": task_id,
        "start_time": start,
        "stop_time": stop,
        "duration_seconds": 0 if stop is None else _calculate_duration(start, stop),
        "notes": notes
    }

    entries.append(entry)
    return save_time_entries(entries)


def _calculate_duration(start: str, stop: str | None) -> int:
    """
    Calculate duration in seconds between start and stop times.

    Args:
        start: ISO 8601 datetime string
        stop: ISO 8601 datetime string, or None for active session

    Returns:
        Duration in seconds (0 if stop is None)
    """
    if stop is None:
        return 0

    try:
        start_dt = datetime.fromisoformat(start.replace("Z", "+00:00"))
        stop_dt = datetime.fromisoformat(stop.replace("Z", "+00:00"))
        return int((stop_dt - start_dt).total_seconds())
    except (ValueError, TypeError):
        return 0


def get_total_time_for_task(task_id: str) -> int:
    """
    Get total time spent on a task.

    Args:
        task_id: Task ID to get total time for

    Returns:
        Total duration in seconds
    """
    entries = load_time_entries()
    total = 0
    for entry in entries:
        if entry.get("task_id") == task_id:
            duration = entry.get("duration_seconds", 0)
            # Update duration for active entries
            if entry.get("stop_time") is None:
                duration = get_current_session_duration(entry.get("entry_id", ""))
            total += duration
    return total


def get_time_entries_for_task(task_id: str) -> list[dict]:
    """
    Get all time entries for a specific task.

    Args:
        task_id: Task ID to get entries for

    Returns:
        List of time entry dictionaries
    """
    entries = load_time_entries()
    return [e for e in entries if e.get("task_id") == task_id]


def get_all_time_entries() -> list[dict]:
    """
    Get all time entries across all tasks.

    Returns:
        List of time entry dictionaries
    """
    return load_time_entries()


def get_active_time_entry() -> dict | None:
    """
    Get the currently active time entry.

    Returns:
        Time entry dictionary, or None if no active entry
    """
    entries = load_time_entries()
    for entry in entries:
        if entry.get("stop_time") is None:
            return entry
    return None


def get_current_session_duration(entry_id: str | None = None) -> int:
    """
    Get duration of current work session in seconds.

    Args:
        entry_id: Specific entry ID to check, or None for any active entry

    Returns:
        Duration in seconds
    """
    entries = load_time_entries()

    if entry_id:
        for entry in entries:
            if entry.get("entry_id") == entry_id:
                start_time = entry.get("start_time")
                if start_time and entry.get("stop_time") is None:
                    return _calculate_duration(start_time, _now_iso())
        return 0

    active_entry = get_active_time_entry()
    if active_entry:
        start_time = active_entry.get("start_time")
        if start_time:
            return _calculate_duration(start_time, _now_iso())
    return 0


# ===== TASK TIMER FUNCTIONS =====

def start_task(task_id: str) -> bool:
    """
    Start working on a specific task (activates timer).

    Only one task can be active at a time. If another task is already active,
    this operation fails silently.

    Args:
        task_id: Task ID to start working on

    Returns:
        True on success, False on failure
    """
    # Check if task exists
    if not task_exists(task_id):
        return False

    # Check if a task is already active
    if get_active_task_id() is not None:
        return False

    # Create new time entry
    start_time = _now_iso()
    entry_id = _generate_entry_id()

    entry = {
        "entry_id": entry_id,
        "task_id": task_id,
        "start_time": start_time,
        "stop_time": None,
        "duration_seconds": 0,
        "notes": None
    }

    entries = load_time_entries()
    entries.append(entry)

    if not save_time_entries(entries):
        return False

    # Update state
    set_active_task_id(task_id)
    set_current_time_entry_id(entry_id)

    return True


def stop_task(task_id: str) -> bool:
    """
    Stop working on a specific task (deactivates timer).

    Args:
        task_id: Task ID to stop working on

    Returns:
        True on success, False on failure
    """
    # Check if this task is active
    if get_active_task_id() != task_id:
        return False

    # Find active entry for this task
    entries = load_time_entries()
    updated = False
    entry_id = None

    for entry in entries:
        if entry.get("task_id") == task_id and entry.get("stop_time") is None:
            stop_time = _now_iso()
            entry["stop_time"] = stop_time
            entry["duration_seconds"] = _calculate_duration(entry["start_time"], stop_time)
            updated = True
            entry_id = entry.get("entry_id")
            break

    if not updated:
        return False

    if not save_time_entries(entries):
        return False

    # Clear state
    set_active_task_id(None)
    set_current_time_entry_id(None)

    return True


def stop_all_tasks() -> None:
    """Stop all active tasks (cleanup)."""
    entries = load_time_entries()
    updated = False
    stop_time = _now_iso()

    for entry in entries:
        if entry.get("stop_time") is None:
            entry["stop_time"] = stop_time
            entry["duration_seconds"] = _calculate_duration(entry["start_time"], stop_time)
            updated = True

    if updated:
        save_time_entries(entries)

    set_active_task_id(None)
    set_current_time_entry_id(None)


# ===== CSV EXPORT =====

def _format_duration(seconds: int) -> str:
    """Format duration in seconds as human-readable string."""
    if seconds == 0:
        return "0m"

    hours = seconds // 3600
    minutes = (seconds % 3600) // 60
    remaining_seconds = seconds % 60

    parts = []
    if hours > 0:
        parts.append(f"{hours}h")
    if minutes > 0:
        parts.append(f"{minutes}m")
    if remaining_seconds > 0 and hours == 0:
        parts.append(f"{remaining_seconds}s")

    return " ".join(parts) if parts else "0m"


def export_time_report_csv(task_id: str | None = None, filepath: str | None = None) -> bool:
    """
    Export time report to CSV file.

    Args:
        task_id: Specific task ID to report on, or None for all tasks
        filepath: Output file path, or None for default

    Returns:
        True on success, False on failure
    """
    entries = load_time_entries()

    # Filter by task_id if specified
    if task_id:
        entries = [e for e in entries if e.get("task_id") == task_id]

    if not entries:
        # Create empty file with headers
        pass

    # Determine filepath
    if filepath is None:
        exports_dir = get_exports_dir()
        filename = "time_report.csv" if task_id is None else f"time_report_{task_id}.csv"
        filepath = str(exports_dir / filename)

    try:
        # Load tasks for task content
        from .storage import load_tasks
        tasks_dict = {t["id"]: t.get("content", "") for t in load_tasks()}

        with open(filepath, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)

            # Write header
            writer.writerow([
                "task_id",
                "task_content",
                "entry_id",
                "start_time",
                "stop_time",
                "duration_seconds",
                "duration_human",
                "notes"
            ])

            # Write entries
            for entry in entries:
                task_id_entry = entry.get("task_id", "")
                stop_time = entry.get("stop_time", "ACTIVE")
                duration = entry.get("duration_seconds", 0)

                # Calculate current duration for active entries
                if stop_time == "ACTIVE":
                    duration = get_current_session_duration(entry.get("entry_id", ""))

                writer.writerow([
                    task_id_entry,
                    tasks_dict.get(task_id_entry, ""),
                    entry.get("entry_id", ""),
                    entry.get("start_time", ""),
                    stop_time,
                    duration,
                    _format_duration(duration),
                    entry.get("notes", "") or ""
                ])

        return True
    except (IOError, OSError):
        return False