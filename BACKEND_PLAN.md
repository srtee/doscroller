# PiTodoist Project Plan

## Project Overview

PiTodoist is a Python project to maintain an efficient local copy of Todoist tasks and provide functionality for task management, time tracking, and state management. The system will run locally and interact with Todoist's data, allowing users to start/stop work on tasks, track time, and mark tasks as complete.

## Goals

1. **Synchronization**: Maintain an efficient local cache of Todoist tasks
2. **State Management**: Track which task is currently displayed/active
3. **Task Activation**: Start and stop working on ONE particular task locally
4. **Time Tracking**: Record timestamps when start/stop functions are invoked to track time spent
5. **Task Completion**: Mark tasks as "complete" upon user input

---

## Data System Architecture

### 1. Local Data Storage

#### Storage Format: JSON
The local data will be stored in JSON files (simple, human-readable).

#### Proposed Data Structures

#### Local Task Cache
A collection of task objects with the following attributes:

| Attribute | Type | Description |
|-----------|------|-------------|
| `id` | string | Unique Todoist task identifier |
| `content` | string | Task title/name |
| `description` | string | Task description |
| `due_date` | string/None | Due date from Todoist |
| `priority` | int | Task priority (1-4) |
| `project_id` | string | Parent project identifier |
| `labels` | list[str] | Associated labels |
| `is_completed` | bool | Completion status |
| `completed_at` | datetime/None | When task was marked complete |

#### Time Tracking Records
Separate storage for time tracking data:

| Attribute | Type | Description |
|-----------|------|-------------|
| `task_id` | string | Reference to task |
| `start_time` | datetime | When work started |
| `stop_time` | datetime/None | When work stopped (NULL if active) |
| `duration_seconds` | int | Calculated duration (0 if active) |

#### Active Task State
A small state file tracking current application state:

| Attribute | Type | Description |
|-----------|------|-------------|
| `active_task_id` | string/None | ID of currently active task |
| `session_start` | datetime | When current session started |
| `last_sync` | datetime/None | Timestamp of last Todoist sync |

**Note**: Since "displayed" task and "active" task are always the same, only `active_task_id` is tracked.

### 2. Directory Structure (Proposed)

```
PiTodoist/
├── data/
│   ├── tasks.json           # Local task cache
│   ├── time_tracking.json   # Time tracking records
│   └── state.json           # Current application state
├── exports/
│   └── time_reports.csv     # Exported CSV time reports
├── docs/                    # Documentation
├── src/                     # Python modules (to be created later)
└── PROJECT_PLAN.md          # This file
```

---

## Proposed Python Functions

### Module: `todoist_sync.py`

Functions for synchronizing with Todoist API:

| Function | Proposed Signature | Description |
|----------|-------------------|-------------|
| `fetch_tasks_from_api` | `fetch_tasks_from_api(api_token: str) -> list[dict]` | Fetch all tasks from Todoist API |
| `save_tasks_locally` | `save_tasks_locally(tasks: list[dict]) -> None` | Save tasks to local cache |
| `load_tasks_locally` | `load_tasks_locally() -> list[dict]` | Load tasks from local cache |
| `sync_tasks` | `sync_tasks(api_token: str) -> bool` | Perform full sync (fetch + save), returns True on success |
| `mark_complete_remote` | `mark_complete_remote(task_id: str, api_token: str) -> bool` | Mark task complete on Todoist, returns True on success |

### Module: `task_state.py`

Functions for managing which task is active:

| Function | Proposed Signature | Description |
|----------|-------------------|-------------|
| `get_active_task` | `get_active_task() -> dict | None` | Get the currently active task |
| `is_task_active` | `is_task_active(task_id: str) -> bool` | Check if a task is currently active |

### Module: `task_timer.py`

Functions for starting/stopping work on tasks:

| Function | Proposed Signature | Description |
|----------|-------------------|-------------|
| `start_task` | `start_task(task_id: str) -> bool` | Start working on a specific task (activates timer) |
| `stop_task` | `stop_task(task_id: str) -> bool` | Stop working on a specific task (deactivates timer) |
| `get_active_task` | `get_active_task() -> dict | None` | Get the currently active task (being worked on) |
| `is_task_active` | `is_task_active(task_id: str) -> bool` | Check if a task is currently active |
| `stop_all_tasks` | `stop_all_tasks() -> None` | Stop all active tasks (cleanup) |
| `get_current_session_duration` | `get_current_session_duration(task_id: str) -> int` | Get duration of current work session in seconds |

### Module: `time_tracking.py`

Functions for tracking and recording time:

| Function | Proposed Signature | Description |
|----------|-------------------|-------------|
| `record_time_entry` | `record_time_entry(task_id: str, start: datetime, stop: datetime | None) -> None` | Record a time tracking entry |
| `get_total_time_for_task` | `get_total_time_for_task(task_id: str) -> int` | Get total time spent on a task (seconds) |
| `get_time_entries_for_task` | `get_time_entries_for_task(task_id: str) -> list[dict]` | Get all time entries for a task |
| `get_all_time_entries` | `get_all_time_entries() -> list[dict]` | Get all time entries across all tasks |
| `export_time_report_csv` | `export_time_report_csv(task_id: str | None = None, filepath: str = "exports/time_reports.csv") -> bool` | Export time report to CSV file |

### Module: `task_manager.py`

High-level functions combining multiple operations:

| Function | Proposed Signature | Description |
|----------|-------------------|-------------|
| `start_work_on_task` | `start_work_on_task(task_id: str, api_token: str) -> bool` | Start working on task, syncs to get latest data first |
| `stop_work_on_task` | `stop_work_on_task(task_id: str) -> bool` | Stop working on task (stop timer) |
| `complete_task` | `complete_task(task_id: str, api_token: str) -> bool` | Stop task timer and mark complete on Todoist |
| `get_task_summary` | `get_task_summary(task_id: str) -> dict` | Get comprehensive task info including time spent |

### Module: `background_sync.py`

Background periodic synchronization:

| Function | Proposed Signature | Description |
|----------|-------------------|-------------|
| `start_background_sync` | `start_background_sync(api_token: str, interval_seconds: int) -> None` | Start periodic background sync thread |
| `stop_background_sync` | `stop_background_sync() -> None` | Stop background sync thread |
| `is_sync_running` | `is_sync_running() -> bool` | Check if background sync is active |

---

## Resolved Decisions

All ambiguities have been resolved:

| # | Question | Decision |
|---|----------|----------|
| 1 | API Integration | **Official Todoist API** - Sync with Todoist using their REST API |
| 2 | Storage Format | **JSON** - Simple, human-readable text files |
| 3 | Time Tracking | **One task only** - Strict mode, only one active task at a time |
| 4 | Task Completion | **Always sync to remote** - Mark complete on Todoist automatically |
| 5 | Display vs Active Task | **Same task** - No separate "displayed" concept; active = displayed |
| 6 | Sync Frequency | **Periodic background** - Auto sync at configurable intervals |
| 7 | Error Handling | **Silent/Graceful** - Return False/None, log warnings, continue if possible |
| 8 | User Interface | **Python API only** - No CLI; functions imported by other programs |
| 9 | Time Report Format | **CSV exportable** - Reports exported to CSV files |
| 10 | Filtering/Selection | **None initially** - No filtering or search functionality (can add later) |

---

## Error Handling Strategy

Based on the "silent/graceful" decision:

| Error Scenario | Behavior |
|----------------|----------|
| Task already being started | Return `False`, log warning, keep existing timer running |
| Task being stopped is not active | Return `False`, log warning, no state change |
| Network sync fails | Return `False`, log warning, use local cached data |
| Local data corrupted | Return `False`, log warning, attempt recovery/create new files |
| Task not found | Return `False` or `None`, log warning |
| Invalid task ID format | Return `False`, log warning |

---

## Implementation Phases

Implementation will proceed in this order:

1. **Phase 1**: Data storage layer (read/write JSON files for tasks, time entries, state)
2. **Phase 2**: State management (active task tracking, single-task timer enforcement)
3. **Phase 3**: Time tracking (start/stop, record timestamps, CSV export)
4. **Phase 4**: Todoist API integration (fetch tasks, mark complete)
5. **Phase 5**: High-level task manager functions (combine operations)
6. **Phase 6**: Background periodic sync (thread-based auto-sync)

---

*Last Updated: 2026-01-26*