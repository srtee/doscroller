# PiTodoist - Storage Optimization Analysis

## Current Storage Architecture

The current Python backend stores three JSON files:

| File | Current Size | Purpose |
|------|--------------|---------|
| `tasks.json` | ~24KB | Full task cache from Todoist API |
| `time_tracking.json` | ~37B (grows) | Time entries for completed work |
| `state.json` | ~175B | Active task, session, sync state |

---

## Data Usage Analysis

### Tasks - What is Actually Used?

Frontend (`app.js`) only uses these task fields:

| Field | Used | Where |
|-------|------|-------|
| `id` | ✓ | API calls, lookups, filtering |
| `content` | ✓ | Task title display |
| `description` | ✓ | Optional description display |
| `is_completed` | ✓ | Incomplete vs completed list (implicit) |
| `completed_at` | ✓ | Sorting completed tasks by newest |

### Task Fields NOT Used by Frontend

| Field | Unused | Size Impact |
|-------|--------|-------------|
| `due_date` | ✓ | ~25 bytes per task |
| `priority` | ✓ | ~5 bytes per task |
| `project_id` | ✓ | ~15 bytes per task |
| `labels` | ✓ | ~20+ bytes per task |
| `order` | ✓ | ~5 bytes per task |
| `url` | ✓ | ~50+ bytes per task |

**Estimated savings:** ~120 bytes per task × ~200 tasks = ~24KB saved

### State Fields - What is Actually Used?

| Field | Used | Purpose |
|-------|------|---------|
| `active_task_id` | ✓ | Currently running task |
| `current_time_entry_id` | ✓ | Active time tracking session |
| `session_start` | ⚠ | Redundant with time entry start |
| `last_sync` | ✗ | Not used for sync logic |

---

## Storage Optimization Decisions

### Decision 1: Eliminate Task Caching Entirely

**Status:** ELIMINATED

**Rationale:**
- Todoist API is fast and allows CORS
- Tasks should be fresh on every load
- Tasks that are completed on Todoist won't reflect in cache
- The "done" view showing completed tasks should fetch from Todoist, not stale cache

**Implementation:**
- Fetch tasks from Todoist on app initialization
- Fetch completed tasks on demand when viewing "done" section
- No local task storage required

**Trade-offs:**
- + ~24KB saved
- + Always fresh data
- - Slight latency on load (API call)
- - No offline viewing

---

### Decision 2: Store Minimal Time Entry Data

**Status:** MINIMIZED

**Original time entry structure:**
```json
{
  "entry_id": "time-abc123...",
  "task_id": "123456789",
  "start_time": "2024-01-30T10:00:00Z",
  "stop_time": "2024-01-30T10:30:00Z",
  "duration_seconds": 1800,
  "notes": null
}
```

**Optimized structure:**
```json
{
  "t": "123456789",      // task_id (key)
  "s": 1706623200,       // start timestamp (unix)
  "e": 1706625000        // end timestamp (unix, null if active)
}
```

**Rationale:**
- `entry_id` can be auto-generated on the fly or not needed
- `duration_seconds` is calculated from start/end
- `notes` feature is unused in current implementation
- Shortened keys save space
- Unix timestamps are more compact than ISO strings

**Estimated savings:** ~40 bytes per entry → ~25 bytes per entry

---

### Decision 3: Consolidate State into Time Entry

**Status:** CONSOLIDATED

**Rationale:**
- `active_task_id` is redundant with the active time entry's task_id
- `current_time_entry_id` is not needed if we use the active time entry's data
- `session_start` duplicates the active time entry's start_time

**New state structure (single object):**
```json
{
  "a": {  // active (time entry or null)
    "t": "123456789",
    "s": 1706623200
  }
}
```

If no active task: `{"a": null}`

**Estimated savings:** ~150 bytes → ~50 bytes

---

### Decision 4: Remove Unused State Fields

**Status:** ELIMINATED

| Field | Reason |
|-------|--------|
| `last_sync` | Not used anywhere in codebase |

**Rationale:**
- The `last_sync` timestamp is set but never read
- No differential sync is implemented
- App always syncs on load

---

## Optimized Storage Summary

### Before Optimization
| Data Type | Storage | Size |
|-----------|---------|------|
| Task cache | tasks.json | ~24KB |
| Time entries | time_tracking.json | 37B (grows) |
| State | state.json | 175B |
| **Total** | | **~24.2KB** |

### After Optimization
| Data Type | Storage | Size |
|-----------|---------|------|
| Task cache | API only | 0B |
| Time entries | localStorage | ~25B per entry |
| Active state | localStorage | ~50B |
| API Token | localStorage | ~40B |
| **Total** | | **~115B + 25B per entry** |

### Storage Growth Comparison

| Entries | Before | After | Savings |
|---------|--------|-------|---------|
| 10 entries | ~24.4KB | ~0.4KB | 98% |
| 100 entries | ~26KB | ~2.6KB | 90% |
| 1000 entries | ~44KB | ~25KB | 43% |

---

## Browser Storage Options

Given the minimized requirements:

| Option | Capacity | Recommended for PiTodoist |
|--------|----------|--------------------------|
| Cookies | ~4KB | ❌ Too small |
| localStorage | ~5-10MB | ✅ More than sufficient |
| sessionStorage | ~5-10MB | ⚠ Cleared on close (bad for time entries) |
| IndexedDB | ~50-250MB | ✅ Overkill but works |

**Recommendation:** Use `localStorage` - simple API, sufficient capacity, persists across sessions.

---

## Migration Plan

1. Remove all task caching from storage
2. Consolidate time entry format (shortened keys, unix timestamps)
3. Consolidate active state into time entries
4. Store active entry at a special key (e.g., `pitodoist:active`)
5. Store historical entries as array under `pitodoist:entries`
6. Remove `last_sync` tracking

---

## Storage Schema (Final)

### localStorage keys:

```
pitodoist:token          - Todoist API token (string)
pitodoist:active         - Active time entry or null (object)
pitodoist:entries        - Array of completed time entries (array)
```

### Entry object structure:

```javascript
{
  t: "task_id",           // string: Todoist task ID
  s: 1706623200,         // number: Unix timestamp (start)
  e: 1706625000          // number: Unix timestamp (end, null if active)
}
```

### Active object structure:

```javascript
null  // or
{
  t: "task_id",           // string: Todoist task ID
  s: 1706623200          // number: Unix timestamp (start)
}
```

---

## Future Considerations

If storage becomes a concern (thousands of entries):

1. **Trim old entries** - Archive entries older than X days
2. **Aggregate data** - Store summary by day/week instead of raw entries
3. **Export to file** - Allow user to download CSV and clear local storage
4. **IndexedDB** - Migrate to IndexedDB if localStorage limit reached (~5-10MB)