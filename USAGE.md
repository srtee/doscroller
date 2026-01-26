# PiTodoist Documentation

PiTodoist is a Python library for maintaining an efficient local copy of Todoist tasks with time tracking, state management, and workflow automation.

## Installation

```bash
# Clone or place the PiTodoist directory in your project
cd /path/to/your/project
import src as pitodoist
```

## Quick Start

```python
import src as pitodoist

# Configure your Todoist API token
API_TOKEN = "your_todoist_api_token"

# Sync tasks from Todoist
pitodoist.todoist_sync.sync_tasks(API_TOKEN)

# Start working on a task
pitodoist.task_manager.start_work_on_task("task_id_123", API_TOKEN)

# Stop working
pitodoist.task_manager.stop_work_on_task("task_id_123")

# Mark task as complete
pitodoist.task_manager.complete_task("task_id_123", API_TOKEN)
```

---

## Modules Reference

### `task_manager` - High-Level Workflow

Main entry point for task operations. These combine multiple lower-level operations.

#### `start_work_on_task(task_id, api_token)`
Start working on a task. First syncs from Todoist to ensure latest data, then starts the timer.

```python
pitodoist.task_manager.start_work_on_task("1234567890", API_TOKEN)
# Returns: True on success, False on failure
```

#### `stop_work_on_task(task_id)`
Stop working on a task by stopping its timer.

```python
pitodoist.task_manager.stop_work_on_task("1234567890")
# Returns: True on success, False on failure
```

#### `complete_task(task_id, api_token)`
Stop the task timer and mark it complete both locally and on Todoist.

```python
pitodoist.task_manager.complete_task("1234567890", API_TOKEN)
# Returns: True on success (or partial success), False on total failure
```

#### `get_task_summary(task_id)`
Get comprehensive information about a task including time spent.

```python
summary = pitodoist.task_manager.get_task_summary("1234567890")
# Returns: {
#     "task": {...},
#     "total_time_seconds": 3600,
#     "total_time_entries": 3,
#     "is_active": True,
#     "current_session_duration": 180,
#     "time_entries": [...]
# }
```

#### `get_active_task_summary()`
Get summary for the currently active task.

```python
summary = pitodoist.task_manager.get_active_task_summary()
# Returns: dict or None if no active task
```

#### `get_all_tasks(include_completed=False)`
Get all tasks from local cache.

```python
all_tasks = pitodoist.task_manager.get_all_tasks()
incomplete_tasks = pitodoist.task_manager.get_all_tasks(include_completed=False)
completed_tasks = pitodoist.task_manager.get_all_tasks(include_completed=True)
```

#### `get_incomplete_tasks()`
Get only incomplete tasks.

```python
incomplete = pitodoist.task_manager.get_incomplete_tasks()
```

#### `get_completed_tasks()`
Get only completed tasks.

```python
completed = pitodoist.task_manager.get_completed_tasks()
```

---

### `time_tracking` - Timer and Time Records

Start, stop, and track time spent on tasks.

#### `start_task(task_id)`
Start working on a task. Only one task can be active at a time.

```python
pitodoist.time_tracking.start_task("1234567890")
# Returns: True on success, False if another task is already active
```

#### `stop_task(task_id)`
Stop working on a task.

```python
pitodoist.time_tracking.stop_task("1234567890")
# Returns: True on success, False if task is not active
```

#### `stop_all_tasks()`
Stop all active tasks (cleanup function).

```python
pitodoist.time_tracking.stop_all_tasks()
```

#### `get_total_time_for_task(task_id)`
Get total time spent on a task in seconds.

```python
total_seconds = pitodoist.time_tracking.get_total_time_for_task("1234567890")
```

#### `get_time_entries_for_task(task_id)`
Get all time entries for a specific task.

```python
entries = pitodoist.time_tracking.get_time_entries_for_task("1234567890")
```

#### `get_all_time_entries()`
Get all time entries across all tasks.

```python
all_entries = pitodoist.time_tracking.get_all_time_entries()
```

#### `get_current_session_duration(entry_id=None)`
Get duration of current work session in seconds.

```python
duration = pitodoist.time_tracking.get_current_session_duration()
```

#### `export_time_report_csv(task_id=None, filepath=None)`
Export time report to CSV file.

```python
# Export all tasks
pitodoist.time_tracking.export_time_report_csv()

# Export specific task
pitodoist.time_tracking.export_time_report_csv(task_id="1234567890")

# Export to custom path
pitodoist.time_tracking.export_time_report_csv(filepath="/path/to/report.csv")
```

---

### `todoist_sync` - Todoist API Integration

Sync tasks with Todoist's REST API.

#### `sync_tasks(api_token)`
Perform full sync (fetch from API and save locally).

```python
pitodoist.todoist_sync.sync_tasks(API_TOKEN)
# Returns: True on success, False on failure
```

#### `fetch_tasks_from_api(api_token)`
Fetch all tasks from Todoist API (does not save locally).

```python
tasks = pitodoist.todoist_sync.fetch_tasks_from_api(API_TOKEN)
```

#### `save_tasks_locally(tasks)`
Save tasks to local cache.

```python
pitodoist.todoist_sync.save_tasks_locally(tasks)
```

#### `load_tasks_locally()`
Load tasks from local cache.

```python
tasks = pitodoist.todoist_sync.load_tasks_locally()
```

#### `mark_complete_remote(task_id, api_token)`
Mark task complete on Todoist.

```python
pitodoist.todoist_sync.mark_complete_remote("1234567890", API_TOKEN)
# Returns: True on success, False on failure
```

#### `mark_complete_local(task_id)`
Mark task complete locally only (does not sync to Todoist).

```python
pitodoist.todoist_sync.mark_complete_local("1234567890")
```

#### `get_api_status(api_token)`
Check if API token is valid.

```python
is_valid = pitodoist.todoist_sync.get_api_status(API_TOKEN)
```

---

### `task_state` - Active Task Management

Track which task is currently active.

#### `get_active_task()`
Get the currently active task object.

```python
task = pitodoist.task_state.get_active_task()
# Returns: dict or None if no active task
```

#### `get_active_task_id()`
Get the ID of the currently active task.

```python
task_id = pitodoist.task_state.get_active_task_id()
# Returns: str or None
```

#### `is_task_active(task_id)`
Check if a task is currently active.

```python
is_active = pitodoist.task_state.is_task_active("1234567890")
```

#### `clear_active_task()`
Clear the active task (set to None).

```python
pitodoist.task_state.clear_active_task()
```

#### `get_task_by_id(task_id)`
Get a task by its ID.

```python
task = pitodoist.task_state.get_task_by_id("1234567890")
```

#### `task_exists(task_id)`
Check if a task exists in the local cache.

```python
exists = pitodoist.task_state.task_exists("1234567890")
```

---

### `background_sync` - Periodic Auto-Sync

Automatically sync with Todoist at configurable intervals.

#### `start_background_sync(api_token, interval_seconds=300)`
Start periodic background sync thread.

```python
# Sync every 5 minutes (default)
pitodoist.background_sync.start_background_sync(API_TOKEN)

# Sync every minute
pitodoist.background_sync.start_background_sync(API_TOKEN, interval_seconds=60)
```

#### `stop_background_sync()`
Stop background sync thread.

```python
pitodoist.background_sync.stop_background_sync()
```

#### `is_sync_running()`
Check if background sync is active.

```python
running = pitodoist.background_sync.is_sync_running()
```

#### `set_sync_interval(interval_seconds)`
Update the sync interval without restarting.

```python
pitodoist.background_sync.set_sync_interval(120)  # 2 minutes
```

#### `trigger_sync_now()`
Trigger an immediate sync without waiting for interval.

```python
pitodoist.background_sync.trigger_sync_now()
```

---

### `storage` - Low-Level Data Storage

Direct access to JSON storage files.

#### File Paths

```python
# Get file paths
pitodoist.storage.get_tasks_filepath()        # data/tasks.json
pitodoist.storage.get_time_tracking_filepath() # data/time_tracking.json
pitodoist.storage.get_state_filepath()        # data/state.json
pitodoist.storage.get_exports_dir()           # exports/
```

#### Save/Load Functions

```python
# Tasks
pitodoist.storage.save_tasks(tasks_list)
pitodoist.storage.load_tasks()

# Time entries
pitodoist.storage.save_time_entries(entries_list)
pitodoist.storage.load_time_entries()

# State
pitodoist.storage.save_state(state_dict)
pitodoist.storage.load_state()
```

---

## Complete Example

```python
import src as pitodoist

# Configuration
API_TOKEN = "your_todoist_api_token"

# 1. Initial sync
pitodoist.todoist_sync.sync_tasks(API_TOKEN)

# 2. Start background sync (every 5 minutes)
pitodoist.background_sync.start_background_sync(API_TOKEN, 300)

# 3. List incomplete tasks
tasks = pitodoist.task_manager.get_incomplete_tasks()
for task in tasks:
    print(f"{task['id']}: {task['content']}")

# 4. Start working on a task
task_id = tasks[0]['id']
pitodoist.task_manager.start_work_on_task(task_id, API_TOKEN)

# 5. Check what we're working on
active = pitodoist.task_manager.get_active_task_summary()
print(f"Working on: {active['task']['content']}")

# 6. After some time, stop and export report
pitodoist.task_manager.stop_work_on_task(task_id)
pitodoist.time_tracking.export_time_report_csv(task_id)

# 7. Mark task as complete
pitodoist.task_manager.complete_task(task_id, API_TOKEN)

# 8. Stop background sync when done
pitodoist.background_sync.stop_background_sync()
```

---

## Data Model

### Task Object

```python
{
    "id": str,                    # Unique Todoist ID
    "content": str,               # Task title
    "description": str | None,    # Task description
    "due_date": str | None,       # ISO 8601 due date
    "priority": int,              # 1-4 (4=highest)
    "project_id": str,            # Parent project ID
    "labels": list[str],          # Associated labels
    "is_completed": bool,         # Completion status
    "completed_at": str | None,   # ISO 8601 completion time
    "order": int,                 # Display order
    "url": str | None             # Todoist web URL
}
```

### Time Entry Object

```python
{
    "entry_id": str,              # Unique entry ID
    "task_id": str,               # Associated task ID
    "start_time": str,            # ISO 8601 start time
    "stop_time": str | None,      # ISO 8601 stop time (None if active)
    "duration_seconds": int,      # Duration in seconds
    "notes": str | None           # Optional notes
}
```

---

## Error Handling

All functions follow a "silent/graceful" error handling strategy:

- Functions return `False` or `None` on failure
- Errors are logged as warnings
- The system continues operating with cached data when possible
- Network failures fall back to local data

---

## File Structure

```
PiTodoist/
├── data/
│   ├── tasks.json           # Local task cache
│   ├── time_tracking.json   # Time tracking records
│   └── state.json           # Current application state
├── exports/
│   └── time_report.csv      # Exported CSV time reports
├── src/
│   ├── __init__.py
│   ├── background_sync.py   # Background sync
│   ├── storage.py           # JSON file I/O
│   ├── task_manager.py      # High-level workflow
│   ├── task_state.py        # Active task tracking
│   ├── time_tracking.py     # Timer and time records
│   └── todoist_sync.py      # Todoist API
└── USAGE.md                 # This file
```

---

## Getting Your Todoist API Token

1. Go to https://todoist.com/app/settings/integrations
2. Scroll down to "Developer" section
3. Click "Create new token"
4. Copy the token (it will only be shown once)
5. Use this token as your `API_TOKEN`