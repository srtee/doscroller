# PiTodoist

A Python project for local task management and time tracking, designed to work with Todoist tasks.

## Overview

PiTodoist maintains an efficient local copy of Todoist tasks and provides functionality for:

- Tracking which task is currently active
- Starting and stopping work on ONE particular task locally
- Tracking time spent on each task with timestamp-based recording
- Marking tasks as complete with automatic Todoist sync

## Status

**Ready for Implementation** - Planning complete, all decisions resolved.

## Documentation

| Document | Description |
|----------|-------------|
| [PROJECT_PLAN.md](PROJECT_PLAN.md) | Data architecture, proposed functions, implementation phases |
| [DATA_MODEL.md](DATA_MODEL.md) | Detailed data structures, schemas, and invariants |

## Key Decisions (Resolved)

| Decision | Choice |
|----------|--------|
| API Integration | Official Todoist API |
| Storage Format | JSON |
| Time Tracking | One task only (strict mode) |
| Task Completion | Always sync to remote |
| Display vs Active | Same task (always) |
| Sync Frequency | Periodic background |
| Error Handling | Silent/Graceful |
| Interface | Python API only |
| Reports | CSV exportable |
| Filtering | None initially |

## Implementation Phases

1. Data storage layer (JSON read/write)
2. State management (active task tracking)
3. Time tracking (start/stop, CSV export)
4. Todoist API integration
5. High-level task manager functions
6. Background periodic sync

## License

MIT License

## Author

To be determined.