# DoScroll Data Model

## Overview

This document describes the proposed data structures for DoScroll, including the local task cache, time tracking records, and application state.

---

## 1. Task Object

A single task as stored locally.

### Schema

```json
{
  "id": "string (required) - Unique Todoist task identifier",
  "content": "string (required) - Task title/name",
  "description": "string (optional) - Task description",
  "due_date": "string | null - ISO 8601 datetime string or null",
  "priority": "int (1-4) - Task priority (4=highest, 1=normal)",
  "project_id": "string (optional) - Parent project identifier",
  "project_name": "string (optional) - Parent project name (cached for display)",
  "labels": ["string"] - List of label names",
  "is_completed": "boolean - Whether task is marked complete",
  "completed_at": "string | null - ISO 8601 datetime when completed",
  "order": "int - Display order from Todoist",
  "url": "string | null - Todoist task URL"
}
```

### Example

```json
{
  "id": "1234567890",
  "content": "Write DoScroll documentation",
  "description": "Create initial markdown files planning the system",
  "due_date": "2026-01-30T18:00:00Z",
  "priority": 4,
  "project_id": "9876543210",
  "project_name": "DoScroll",
  "labels": ["planning", "documentation"],
  "is_completed": false,
  "completed_at": null,
  "order": 1,
  "url": "https://todoist.com/showTask?id=1234567890"
}
```

---

## 2. Time Entry Object

A record of a single work session on a task.

### Schema

```json
{
  "entry_id": "string (required) - Unique identifier for this time entry",
  "task_id": "string (required) - Reference to task.id",
  "start_time": "string (required) - ISO 8601 datetime when work started",
  "stop_time": "string | null - ISO 8601 datetime when work stopped, null if active",
  "duration_seconds": "int - Calculated duration (0 if active)",
  "notes": "string (optional) - Optional notes about this session"
}
```

### Example (Completed Session)

```json
{
  "entry_id": "time-001",
  "task_id": "1234567890",
  "start_time": "2026-01-26T09:00:00Z",
  "stop_time": "2026-01-26T11:30:00Z",
  "duration_seconds": 9000,
  "notes": "Initial planning session"
}
```

### Example (Active Session)

```json
{
  "entry_id": "time-002",
  "task_id": "1234567890",
  "start_time": "2026-01-26T14:00:00Z",
  "stop_time": null,
  "duration_seconds": 0,
  "notes": null
}
```

---

## 3. Application State Object

Current runtime state of the DoScroll application.

### Schema

```json
{
  "active_task_id": "string | null - ID of task currently being worked on (also the displayed task)",
  "current_time_entry_id": "string | null - ID of currently running time entry",
  "session_start": "string - ISO 8601 datetime when application session started",
  "last_sync": "string | null - ISO 8601 datetime of last Todoist sync"
}
```

**Note**: `active_task_id` and `displayed_task_id` are always the same, so only `active_task_id` is tracked.

### Example

```json
{
  "active_task_id": "1234567890",
  "current_time_entry_id": "time-002",
  "session_start": "2026-01-26T08:00:00Z",
  "last_sync": "2026-01-26T08:05:00Z"
}
```

---

## 4. File Storage Structure

### tasks.json

```json
{
  "version": "1",
  "last_updated": "2026-01-26T12:00:00Z",
  "tasks": [
    { ...task object... },
    { ...task object... }
  ]
}
```

### time_tracking.json

```json
{
  "version": "1",
  "entries": [
    { ...time entry object... },
    { ...time entry object... }
  ]
}
```

### state.json

```json
{
  "version": "1",
  "state": { ...application state object... }
}
```

---

## 5. Invariants

The following invariants should be maintained:

1. **Task Uniqueness**: Each `task_id` appears at most once in `tasks.json`

2. **Time Entry Task Validity**: Each time entry's `task_id` must reference a valid task in `tasks.json`

3. **Single Active Session**: At most one time entry can have `stop_time = null` (currently active)

4. **Active Task Consistency**: If `active_task_id` is set in state, there must be a corresponding time entry with `stop_time = null` for that task

5. **Session ID Consistency**: If `current_time_entry_id` is set, there must be a corresponding time entry in `time_tracking.json`

---

## 6. Indexing Strategy

For efficient lookups, the following indexes (implicit) should be maintained:

| Index | On Field | Purpose |
|-------|----------|---------|
| Task ID | `tasks[*].id` | Quick task lookup by ID |
| Completion Status | `tasks[*].is_completed` | Separate active/completed tasks |
| Time Entry Task ID | `entries[*].task_id` | Get all time entries for a task |
| Active Entry | `entries[*].stop_time` | Find currently active session |
| Date Range | `entries[*].start_time` | Time-based queries/reports |

---

## 7. CSV Export Format

Time reports are exported to CSV with the following columns:

| Column | Description |
|--------|-------------|
| `task_id` | Reference to task |
| `task_content` | Task title/name |
| `entry_id` | Unique identifier for time entry |
| `start_time` | ISO 8601 datetime when work started |
| `stop_time` | ISO 8601 datetime when work stopped, or "ACTIVE" if running |
| `duration_seconds` | Calculated duration (0 if active) |
| `duration_human` | Human-readable duration (e.g., "1h 30m") |
| `notes` | Optional notes about this session |

### CSV Example

```csv
task_id,task_content,entry_id,start_time,stop_time,duration_seconds,duration_human,notes
1234567890,Write DoScroll documentation,time-001,2026-01-26T09:00:00Z,2026-01-26T11:30:00Z,9000,2h 30m,Initial planning session
1234567890,Write DoScroll documentation,time-002,2026-01-26T14:00:00Z,ACTIVE,0,0m,
```

---

## 8. Calculated/Derived Data

The following data is calculated on-demand:

| Calculation | Description |
|-------------|-------------|
| Total Task Time | Sum of all `duration_seconds` for a task across all entries |
| Active Session Duration | Current time minus `start_time` for entry with `stop_time = null` |
| Task Age | Time between `completed_at` and original creation (if available) |
| Daily Total | Sum of durations for entries on a specific date |
| Weekly Total | Sum of durations for entries within a week |

---

*Last Updated: 2026-01-26*