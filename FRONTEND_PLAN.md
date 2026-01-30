# Frontend Documentation Plan

## Overview
This document outlines the plan for building a minimalistic HTML+JavaScript frontend that communicates with the DoScroll Python backend via a web API layer.

---

## 1. Backend API Layer (Prerequisite)

Before building the frontend, a Python web API server must be created to expose the backend functions. The frontend will communicate via HTTP endpoints.

### 1.1 Required API Endpoints

| HTTP Method | Endpoint | Auth | Purpose | Backend Function |
|-------------|----------|------|---------|------------------|
| GET | `/api/tasks` | Optional | Fetch all tasks | `task_manager.get_all_tasks(include_completed=False)` |
| GET | `/api/tasks/completed` | Optional | Fetch completed tasks | `task_manager.get_completed_tasks()` |
| GET | `/api/task/{id}` | Optional | Get task details | `task_manager.get_task_summary(task_id)` |
| GET | `/api/active` | Optional | Get active task | `task_manager.get_active_task_summary()` |
| POST | `/api/start/{id}` | Required | Start timing a task | `task_manager.start_work_on_task(task_id, api_token)` |
| POST | `/api/stop/{id}` | Optional | Stop timing a task | `task_manager.stop_work_on_task(task_id)` |
| POST | `/api/complete/{id}` | Required | Mark task complete | `task_manager.complete_task(task_id, api_token)` |
| GET | `/api/time/{id}` | Optional | Get total time for task | `time_tracking.get_total_time_for_task(task_id)` |
| GET | `/api/sync` | Required | Sync with Todoist | `todoist_sync.sync_tasks(api_token)` |

**Note:** Auth = Bearer token in Authorization header required for endpoints that interact with Todoist.

### 1.2 API Authentication

**DECISION (user):** API token is sent via Authorization header.

- Send API token in `Authorization: Bearer {token}` HTTP header
- Required for endpoints that interact with Todoist (start, complete, sync)

### 1.3 API Response Format
All endpoints should return JSON with consistent structure:
```json
{
  "success": true|false,
  "data": { ... } | null,
  "error": "error message" | null
}
```

### 1.4 Task Object Structure
```json
{
  "id": "string",
  "content": "string",
  "description": "string|null",
  "due_date": "string|null",
  "priority": 1-4,
  "project_id": "string|null",
  "labels": ["string"],
  "is_completed": boolean,
  "completed_at": "string|null",
  "order": number
}
```

---

## 2. Frontend Visual Design

The interface shall be minimalistic with the following elements centered on the screen:

### 2.1 Task Display Area
- **Task Title**: Large, prominent text showing current task `content`
- **Task Description** (optional): Smaller text below title if `description` exists
- **Progress Indicator**: Position in task list (e.g., "3 of 10")
- **Due Date** (optional): Subheading if `due_date` exists
- **Total Time** (completed tasks only): Total time spent displayed as subheading

**DECISION (user):** Progress indicator is shown as "X of Y" in the task display area.

### 2.2 Control Buttons
All buttons should be large, touch-friendly, with clear text symbols:

**DECISION (user):** Use text symbols for all buttons.

| Button | Symbol | Action | Default State |
|--------|--------|--------|---------------|
| Previous | `<-` | Navigate to previous task in list | Always enabled (wraps) |
| Next | `->` | Navigate to next task in list | Always enabled (wraps) |
| Play | `▶` | Start timing current task | Disabled if task already active |
| Stop | `||` | Pause/stop timing current task | Disabled if no active task |
| Done | `✓` | Mark task complete / Toggle done view | Always enabled |

**DECISION (user):** Navigation wraps around (circular) - left arrow at first item goes to last item, right arrow at last item goes to first item.

### 2.3 Layout Structure

**DECISION (user):** Two-row layout with navigation controls on top row, action buttons on bottom row.

```
+----------------------------------+
|           (empty space)          |
|                                  |
|   [<-]   [ Task Display ]   [->] |
|        (title + description)      |
|                                  |
|          [▶]  [||]  [✓]         |
|         (action button row)       |
|                                  |
|           (empty space)          |
+----------------------------------+
```

- **Top Row**: Left arrow, Task Display (centered), Right arrow
- **Bottom Row**: Play, Stop, Done buttons (centered)

---

## 3. Frontend Functionality

### 3.1 State Management
The frontend must maintain the following client-side state:

| State Variable | Type | Purpose |
|----------------|------|---------|
| `taskList` | Array | All incomplete tasks loaded from API |
| `doneTaskList` | Array | All completed tasks loaded from API |
| `currentIndex` | Number | Current position in task list |
| `viewingDone` | Boolean | Whether currently viewing completed tasks |
| `activeTaskId` | String | ID of currently active (timing) task |
| `apiToken` | String | Todoist API token for authentication |
| `currentSessionDuration` | Number | Seconds for current active session |

### 3.2 Initial Load Sequence

**DECISION (user):** Resume active task if one exists, otherwise show first incomplete task.

1. Fetch API token (from localStorage, URL param, or user prompt)
2. Fetch task lists via `/api/tasks` and `/api/tasks/completed`
3. Fetch active task via `/api/active`
4. If active task exists, display it (resume); otherwise display first incomplete task
5. Start polling for timer updates (if any active task)

### 3.3 Navigation Behavior

#### Previous Button (Left Arrow)
- Decrements `currentIndex`
- Wraps to last item if at first item
- Updates display with previous task data
- Updates button enabled/disabled states

#### Next Button (Right Arrow)
- Increments `currentIndex`
- Wraps to first item if at last item
- Updates display with next task data
- Updates button enabled/disabled states

### 3.4 Timer Controls

#### Play Button
- Calls `POST /api/start/{task_id}`
- On success: updates `activeTaskId`, disables Play, enables Stop
- On failure: displays error message to user
- Only enabled when current task is not already active

#### Stop Button
- Calls `POST /api/stop/{task_id}`
- On success: clears `activeTaskId`, enables Play, disables Stop
- On failure: displays error message
- Only enabled when a task is active

### 3.5 Task Completion

**DECISION (user):** Done button supports both single-click and double-click actions. Requires ~300ms delay to distinguish single vs double click.

#### Done Button (Single Click)
1. If task is active, stop timing first
2. Call `POST /api/complete/{task_id}`
3. On success: remove from task list, move to done list
4. Display next incomplete task
5. Show brief "Task completed!" confirmation

#### Done Button (Double Click)

**DECISION (user):** Completed tasks displayed newest first (most recently completed).

1. Toggle `viewingDone` state
2. If entering done view:
   - Load completed tasks (sorted newest first by `completed_at`)
   - Display most recently completed task
   - Show total time as subheading
3. If exiting done view:
   - Return to incomplete task view
   - Display previous incomplete task

### 3.6 Time Display for Completed Tasks

**DECISION (user):** No timer display for active/incomplete tasks.

When viewing done tasks, each task should show:
- Task title (as usual)
- **Total Time Spent**: Formatted as "Xh Ym Zs" or similar human-readable format
  - Retrieved via `GET /api/time/{task_id}`
  - Fetched when displaying each completed task
  - Displayed as a subheading below the task title

### 3.7 Timer Updates

**DECISION (user):** No timer display, so polling is only needed for internal state tracking.

- Poll `/api/active` every 10-30 seconds when a task is active to detect state changes
- No real-time time display needed (user decision)
- Update button states if active task changes

---

## 4. JavaScript Architecture

### 4.1 File Structure

**Location:** At project root for serving by web server.

```
# Root directory (DoScroll/)
index.html          # Main HTML file
styles.css          # Minimalistic styling
app.js              # All application logic
```

### 4.2 Key JavaScript Functions

#### API Communication
```javascript
// Wrapper functions for each API endpoint
async function fetchTasks() { }
async function fetchCompletedTasks() { }
async function fetchActiveTask() { }
async function startTask(taskId) { }
async function stopTask(taskId) { }
async function completeTask(taskId) { }
async function fetchTaskTime(taskId) { }
async function syncTasks() { }
```

#### State Management
```javascript
// State object and getters/setters
const state = { };
function updateTaskDisplay() { }
function updateButtonStates() { }
```

#### Event Handlers
```javascript
// Button click handlers
function handlePrevious() { }
function handleNext() { }
function handlePlay() { }
function handleStop() { }
function handleDone() { }
function handleDoneDoubleClick() { }
```

#### Utility Functions
```javascript
// Time formatting, error handling, etc.
function formatTime(seconds) { }
function showError(message) { }
function showSuccess(message) { }
```

---

## 5. Styling Guidelines

### 5.1 Design Principles
- **Minimalist**: Clean, uncluttered interface
- **High Contrast**: Clear visual hierarchy
- **Large Touch Targets**: Buttons at least 44x44px
- **Centered Layout**: All content vertically and horizontally centered
- **Responsive**: Adapts to various screen sizes

### 5.2 Color Scheme

**DECISION (user):** Light theme.

- Background: White/light neutral (#ffffff or similar)
- Task Text: High contrast dark (#000000 or similar)
- Active Task: Subtle highlight or indicator (e.g., light border or background tint)
- Buttons: Distinct colors for different actions
  - Play: Green/Primary action color
  - Stop: Orange/Yellow
  - Done: Blue/Success color
  - Navigation: Neutral (gray)

### 5.3 Typography
- Task Title: Large, bold (24-32px)
- Metadata: Medium (14-16px)
- Time Display: Monospace for consistency

---

## 6. User Flow Examples

### 6.1 Starting Work on a Task
1. User opens page, sees first incomplete task
2. User clicks "Play" button
3. Frontend calls `/api/start/{id}`
4. Timer begins, Play button disabled, Stop button enabled
5. Timer updates every second

### 6.2 Completing a Task
1. User is working on a task
2. User clicks "Done" button
3. Timer stops automatically
4. Task marked complete via API
5. Task removed from list
6. Next incomplete task displayed
7. Brief success message shown

### 6.3 Viewing Completed Tasks
1. User double-clicks "Done" button
2. View switches to completed tasks
3. Each task shows total time spent
4. User can navigate with arrow buttons
5. Double-click "Done" again to return to incomplete tasks

---

## 7. Error Handling

### 7.1 API Errors
- Network failures: Show retry option
- Authentication errors: Prompt for new token
- Task not found: Refresh task list
- Rate limiting: Implement backoff

### 7.2 Edge Cases
- Empty task list: Display "No tasks available" message
- Active task on different device: Show warning, offer to take over
- Sync failure: Allow continue with local data, offer manual retry

---

## 8. Technical Considerations

### 8.1 API Token Storage

**DECISION (user):** Prompt user for API token on first visit, store in localStorage for persistence.

- Store in localStorage for persistence
- Prompt user via browser dialog on first visit if no token found
- Provide way to update token if invalid (via prompt or settings button)
- Consider URL parameter for initial setup (optional fallback)

### 8.2 Polling vs WebSockets

**DECISION (user):** No timer display, so polling can be infrequent.

- Initial implementation: Simple polling (10-30s interval) for state changes only
- Future: WebSocket for real-time updates (if needed)

### 8.3 Offline Support (Future)
- Cache task data locally
- Allow basic operations offline
- Sync when connection restored

---

## 9. Dependencies

### 9.1 External Libraries

**DECISION (user):** Using text symbols for buttons, no icon library needed.

- None required for basic implementation (using text symbols)
- Optional: Axios for cleaner API calls (vanilla fetch is sufficient)

### 9.2 Browser Support
- Modern browsers (ES6+)
- Mobile-friendly touch events

---

## 10. Testing Checklist

### 10.1 Functional Tests
- [ ] Load incomplete tasks on startup
- [ ] Navigate between tasks
- [ ] Start timer on task
- [ ] Stop timer on task
- [ ] Complete task (single click)
- [ ] Toggle to completed tasks (double click)
- [ ] View time spent on completed tasks
- [ ] Return to incomplete tasks view

### 10.2 Edge Case Tests
- [ ] Handle empty task list
- [ ] Handle API failures gracefully
- [ ] Handle invalid API token
- [ ] Handle rapid button clicks
- [ ] Handle browser refresh during active timer

### 10.3 Visual Tests
- [ ] Verify button states (enabled/disabled)
- [ ] Verify active task indicator
- [ ] Verify time display formatting
- [ ] Verify responsive layout

---

## 11. Implementation Order

1. **Phase 1**: Python web API layer
2. **Phase 2**: Basic HTML structure and styling
3. **Phase 3**: JavaScript state management and API integration
4. **Phase 4**: Navigation and timer controls
5. **Phase 5**: Done button and completed tasks view
6. **Phase 6**: Error handling and polish
7. **Phase 7**: Testing and refinement