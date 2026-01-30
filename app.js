// DoScroll - Client-Side Frontend Application

// ===== STORAGE LAYER =====

const STORAGE_KEYS = {
    TOKEN: 'doscroll:token',
    ACTIVE: 'doscroll:active',
    ENTRIES: 'doscroll:entries'
};

const Storage = {
    getToken() {
        return localStorage.getItem(STORAGE_KEYS.TOKEN);
    },

    setToken(token) {
        localStorage.setItem(STORAGE_KEYS.TOKEN, token);
    },

    getActive() {
        const data = localStorage.getItem(STORAGE_KEYS.ACTIVE);
        return data ? JSON.parse(data) : null;
    },

    setActive(entry) {
        if (entry === null) {
            localStorage.removeItem(STORAGE_KEYS.ACTIVE);
        } else {
            localStorage.setItem(STORAGE_KEYS.ACTIVE, JSON.stringify(entry));
        }
    },

    getEntries() {
        const data = localStorage.getItem(STORAGE_KEYS.ENTRIES);
        return data ? JSON.parse(data) : [];
    },

    saveEntries(entries) {
        localStorage.setItem(STORAGE_KEYS.ENTRIES, JSON.stringify(entries));
    },

    addEntry(entry) {
        const entries = this.getEntries();
        entries.push(entry);
        this.saveEntries(entries);
    },

    // Calculate duration in seconds from timestamps
    calculateDuration(startTs, endTs) {
        if (!endTs) {
            // Active session - calculate current duration
            return Math.floor((Date.now() / 1000) - startTs);
        }
        return endTs - startTs;
    },

    // Get total time for a task ID
    getTotalTimeForTask(taskId) {
        const entries = this.getEntries();
        const active = this.getActive();

        let total = 0;

        // Sum completed entries
        for (const entry of entries) {
            if (entry.t === taskId) {
                total += entry.e - entry.s;
            }
        }

        // Add active entry if it's this task
        if (active && active.t === taskId) {
            total += this.calculateDuration(active.s, null);
        }

        return total;
    }
};

// ===== TODOIST API =====

const Todoist = {
    BASE_URL: 'https://api.todoist.com/rest/v2',

    async request(endpoint, options = {}) {
        const token = Storage.getToken();
        const url = `${this.BASE_URL}${endpoint}`;
        const headers = {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${token}`,
            ...options.headers
        };

        try {
            const response = await fetch(url, { ...options, headers });
            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }
            if (response.status === 204) {
                return null;
            }
            return await response.json();
        } catch (error) {
            console.error('Todoist API Error:', error);
            throw error;
        }
    },

    async getTasks(filter = null) {
        let url = '/tasks';
        if (filter) {
            url += `?filter=${encodeURIComponent(filter)}`;
        }
        return this.request(url);
    },

    async closeTask(taskId) {
        return this.request(`/tasks/${taskId}/close`, { method: 'POST' });
    },

    async addComment(taskId, content) {
        return this.request('/comments', {
            method: 'POST',
            body: JSON.stringify({ task_id: taskId, content })
        });
    }
};

// ===== STATE MANAGEMENT =====

const state = {
    taskList: [],
    doneTaskList: [],
    currentIndex: 0,
    viewingDone: false,
    activeTaskId: null
};

// ===== TASK MANAGEMENT =====

const TaskManager = {
    async syncTasks() {
        try {
            const tasks = await Todoist.getTasks();
            // Filter into incomplete and completed
            state.taskList = tasks.filter(t => !t.is_completed);
            state.doneTaskList = tasks.filter(t => t.is_completed);
            // Sort completed by newest first
            state.doneTaskList.sort((a, b) => {
                const aTime = b.completed_at ? new Date(b.completed_at).getTime() : 0;
                const bTime = a.completed_at ? new Date(a.completed_at).getTime() : 0;
                return aTime - bTime;
            });
            return true;
        } catch (error) {
            console.error('Sync failed:', error);
            return false;
        }
    },

    async startWork(taskId) {
        // First sync to get latest data
        await this.syncTasks();

        // Check if a task is already active
        const active = Storage.getActive();
        if (active) {
            throw new Error('A task is already active');
        }

        // Start the timer
        const now = Math.floor(Date.now() / 1000);
        const entry = { t: taskId, s: now };
        Storage.setActive(entry);
        state.activeTaskId = taskId;

        return true;
    },

    stopWork(taskId) {
        const active = Storage.getActive();
        if (!active || active.t !== taskId) {
            throw new Error('This task is not active');
        }

        // Calculate end time
        const endTs = Math.floor(Date.now() / 1000);
        const entry = { ...active, e: endTs };

        // Save as completed entry
        Storage.addEntry(entry);

        // Clear active
        Storage.setActive(null);
        state.activeTaskId = null;

        return true;
    },

    async completeTask(taskId) {
        // Stop timer if active
        const active = Storage.getActive();
        if (active && active.t === taskId) {
            this.stopWork(taskId);
        }

        // Mark complete on Todoist
        await Todoist.closeTask(taskId);

        // Add comment with total time spent
        const totalSeconds = Storage.getTotalTimeForTask(taskId);
        if (totalSeconds > 0) {
            const formattedTime = formatTime(totalSeconds);
            try {
                await Todoist.addComment(taskId, `Total time: ${formattedTime}`);
            } catch (error) {
                // Comment is optional, don't fail if it doesn't work
                console.error('Failed to add comment:', error);
            }
        }

        // Refresh tasks
        await this.syncTasks();
    },

    getActiveTaskSummary() {
        const active = Storage.getActive();
        if (!active) return null;

        // Find task in list
        const task = state.taskList.find(t => t.id === active.t);
        if (!task) return null;

        const duration = Storage.calculateDuration(active.s, null);

        return {
            task: task,
            total_time_seconds: duration,
            total_time_entries: 1,
            is_active: true,
            current_session_duration: duration,
            time_entries: [{ entry_id: 'active', task_id: active.t, start_time: active.s, stop_time: null }]
        };
    },

    getTaskSummary(taskId) {
        const entries = Storage.getEntries();
        const taskEntries = entries.filter(e => e.t === taskId);
        const active = Storage.getActive();

        const totalSeconds = Storage.getTotalTimeForTask(taskId);

        const isActive = active && active.t === taskId;
        const currentDuration = isActive ? Storage.calculateDuration(active.s, null) : 0;

        return {
            task: { id: taskId },
            total_time_seconds: totalSeconds,
            total_time_entries: taskEntries.length + (isActive ? 1 : 0),
            is_active: isActive,
            current_session_duration: currentDuration,
            time_entries: taskEntries
        };
    }
};

// ===== API WRAPPER (for compatibility with existing UI code) =====

async function apiRequest(endpoint, options = {}) {
    const headers = {
        'Content-Type': 'application/json',
        ...options.headers
    };

    // Add auth header if we have a token
    const token = Storage.getToken();
    if (token && !headers['Authorization']) {
        headers['Authorization'] = `Bearer ${token}`;
    }

    try {
        const response = await fetch(endpoint, { ...options, headers });
        const data = await response.json();

        if (!data.success) {
            throw new Error(data.error || 'Request failed');
        }

        return data.data;
    } catch (error) {
        console.error('API Error:', error);
        throw error;
    }
}

// Forward to Todoist or TaskManager
async function fetchTasks() {
    await TaskManager.syncTasks();
    return state.taskList;
}

async function fetchCompletedTasks() {
    await TaskManager.syncTasks();
    return state.doneTaskList;
}

async function fetchActiveTask() {
    return TaskManager.getActiveTaskSummary();
}

async function startTask(taskId) {
    await TaskManager.startWork(taskId);
    return TaskManager.getActiveTaskSummary();
}

async function stopTask(taskId) {
    TaskManager.stopWork(taskId);
    return { stopped: true };
}

async function completeTask(taskId) {
    await TaskManager.completeTask(taskId);
    return { completed: true };
}

async function fetchTaskTime(taskId) {
    const totalSeconds = Storage.getTotalTimeForTask(taskId);
    return { task_id: taskId, total_seconds: totalSeconds };
}

async function syncTasks() {
    const success = await TaskManager.syncTasks();
    return { synced: success, task_count: state.taskList.length };
}

// ===== STATE UPDATES =====

function getCurrentTask() {
    const list = state.viewingDone ? state.doneTaskList : state.taskList;
    if (list.length === 0) return null;
    return list[state.currentIndex];
}

function updateTaskDisplay() {
    const task = getCurrentTask();

    const titleEl = document.getElementById('task-title');
    const descEl = document.getElementById('task-description');
    const metaEl = document.getElementById('task-meta');
    const timeEl = document.getElementById('task-time');

    if (!task) {
        titleEl.textContent = state.viewingDone ? 'No completed tasks' : 'No tasks available';
        descEl.textContent = '';
        metaEl.textContent = '';
        timeEl.textContent = '';
        return;
    }

    // Display task title
    titleEl.textContent = task.content || 'Untitled task';

    // Display description
    descEl.textContent = task.description || '';

    // Display progress indicator for incomplete tasks
    const list = state.viewingDone ? state.doneTaskList : state.taskList;
    if (!state.viewingDone) {
        metaEl.textContent = `${state.currentIndex + 1} of ${list.length}`;
    } else {
        metaEl.textContent = '';
    }

    // Display total time for completed tasks
    if (state.viewingDone) {
        timeEl.textContent = 'Loading time...';
        fetchTaskTime(task.id).then(data => {
            if (getCurrentTask()?.id === task.id) {
                timeEl.textContent = `Total time: ${formatTime(data.total_seconds)}`;
            }
        }).catch(() => {
            timeEl.textContent = '';
        });
    } else {
        timeEl.textContent = '';
    }
}

function updateButtonStates() {
    const toggleBtn = document.getElementById('btn-toggle');
    const prevBtn = document.getElementById('btn-previous');
    const nextBtn = document.getElementById('btn-next');

    const currentTask = getCurrentTask();
    const isActive = currentTask && currentTask.id === state.activeTaskId;

    // Toggle button: disabled if no current task
    toggleBtn.disabled = !currentTask;

    // Update toggle button icon and state
    const icon = toggleBtn.querySelector('i');
    if (isActive) {
        icon.className = 'fa-solid fa-pause';
        toggleBtn.classList.add('active');
        toggleBtn.title = 'Stop task';
    } else {
        icon.className = 'fa-solid fa-play';
        toggleBtn.classList.remove('active');
        toggleBtn.title = 'Start task';
    }

    // Disable navigation buttons when a task is active
    prevBtn.disabled = isActive;
    nextBtn.disabled = isActive;
}

function updateActiveTaskState(activeSummary) {
    const active = Storage.getActive();
    state.activeTaskId = active ? active.t : null;
    updateButtonStates();
}

// ===== EVENT HANDLERS =====

function handlePrevious() {
    const list = state.viewingDone ? state.doneTaskList : state.taskList;
    if (list.length === 0) return;

    // Wrap around (circular navigation)
    state.currentIndex = (state.currentIndex - 1 + list.length) % list.length;
    updateTaskDisplay();
}

function handleNext() {
    const list = state.viewingDone ? state.doneTaskList : state.taskList;
    if (list.length === 0) return;

    // Wrap around (circular navigation)
    state.currentIndex = (state.currentIndex + 1) % list.length;
    updateTaskDisplay();
}

async function handleToggle() {
    const task = getCurrentTask();
    if (!task) return;

    const isActive = task.id === state.activeTaskId;

    try {
        if (isActive) {
            await stopTask(task.id);
            state.activeTaskId = null;
            showMessage('Task stopped');
        } else {
            await startTask(task.id);
            const active = Storage.getActive();
            state.activeTaskId = active ? active.t : null;
            showMessage('Task started');
        }
        updateButtonStates();
    } catch (error) {
        showMessage(error.message, 'error');
    }
}

function handleDone() {
    const task = getCurrentTask();
    if (!task) return;

    // Complete the task
    completeTask(task.id).then(() => {
        state.activeTaskId = null;

        // Remove from current list
        const list = state.viewingDone ? state.doneTaskList : state.taskList;
        const index = list.findIndex(t => t.id === task.id);
        if (index !== -1) {
            list.splice(index, 1);
        }

        // Move to next task
        if (state.viewingDone) {
            state.currentIndex = Math.min(state.currentIndex, list.length - 1);
        } else {
            state.currentIndex = state.currentIndex % list.length;
        }

        updateTaskDisplay();
        updateButtonStates();
        showMessage('Task completed!');
    }).catch(error => {
        showMessage(error.message, 'error');
    });
}

async function handleSync() {
    try {
        await syncTasks();
        showMessage('Tasks synced from Todoist');
    } catch (error) {
        showMessage(error.message, 'error');
    }
}

async function handleExport() {
    try {
        // First sync to get the latest task data
        await syncTasks();

        // Build export data with task name, duration, and completion status
        const exportData = [];
        const processedTaskIds = new Set();

        // Process all tasks (both incomplete and completed)
        const allTasks = [...state.taskList, ...state.doneTaskList];

        for (const task of allTasks) {
            if (processedTaskIds.has(task.id)) continue;
            processedTaskIds.add(task.id);

            const totalSeconds = Storage.getTotalTimeForTask(task.id);
            const isComplete = task.is_completed || false;
            const duration = formatTime(totalSeconds);

            exportData.push({
                taskName: task.content || 'Unnamed task',
                durationSeconds: totalSeconds,
                durationFormatted: duration,
                isComplete: isComplete ? 'Complete' : 'Incomplete'
            });
        }

        // Sort by duration descending
        exportData.sort((a, b) => b.durationSeconds - a.durationSeconds);

        // Generate CSV
        let csv = 'Task Name,Duration,Status\n';
        for (const row of exportData) {
            // Escape task name if it contains commas or quotes
            const escapedName = row.taskName.includes(',') || row.taskName.includes('"')
                ? `"${row.taskName.replace(/"/g, '""')}"`
                : row.taskName;
            csv += `${escapedName},${row.durationFormatted},${row.isComplete}\n`;
        }

        // Create download
        const blob = new Blob([csv], { type: 'text/csv;charset=utf-8;' });
        const url = URL.createObjectURL(blob);
        const link = document.createElement('a');
        link.setAttribute('href', url);
        link.setAttribute('download', `doscroll-time-tracking-${new Date().toISOString().slice(0, 10)}.csv`);
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
        URL.revokeObjectURL(url);

        showMessage('CSV exported successfully');
    } catch (error) {
        showMessage(error.message, 'error');
    }
}

// ===== UTILITY FUNCTIONS =====

function formatTime(seconds) {
    if (seconds === 0) return '0m';

    const hours = Math.floor(seconds / 3600);
    const minutes = Math.floor((seconds % 3600) / 60);
    const remainingSeconds = seconds % 60;

    const parts = [];
    if (hours > 0) parts.push(`${hours}h`);
    if (minutes > 0) parts.push(`${minutes}m`);
    if (remainingSeconds > 0 && hours === 0) parts.push(`${remainingSeconds}s`);

    return parts.join(' ') || '0m';
}

function showMessage(message, type = 'success') {
    const messageEl = document.getElementById('message');
    messageEl.textContent = message;
    messageEl.className = `message ${type} show`;

    setTimeout(() => {
        messageEl.className = 'message';
    }, 2000);
}

async function getApiToken() {
    // Check localStorage first
    let token = Storage.getToken();
    if (token) return token;

    // Check URL parameter
    const urlParams = new URLSearchParams(window.location.search);
    token = urlParams.get('token');
    if (token) {
        Storage.setToken(token);
        // Remove token from URL
        window.history.replaceState({}, '', window.location.pathname);
        return token;
    }

    // Prompt user
    token = prompt('Please enter your Todoist API token:');
    if (token) {
        Storage.setToken(token);
        return token;
    }

    throw new Error('API token required');
}

// ===== POLLING =====

async function pollActiveTask() {
    // Just update local state - no server polling needed
    updateActiveTaskState();

    // Poll every 20 seconds (since no timer display is shown)
    setTimeout(pollActiveTask, 20000);
}

// ===== INITIALIZATION =====

async function initialize() {
    try {
        // Get API token
        await getApiToken();

        // Sync tasks with Todoist first
        await syncTasks();

        // Set active task from localStorage if exists
        const active = Storage.getActive();
        if (active) {
            state.activeTaskId = active.t;
            // Find active task in list and set index
            const activeIndex = state.taskList.findIndex(t => t.id === active.t);
            if (activeIndex !== -1) {
                state.currentIndex = activeIndex;
            }
        }

        updateTaskDisplay();
        updateButtonStates();

        // Start polling
        pollActiveTask();

    } catch (error) {
        console.error('Initialization error:', error);
        document.getElementById('task-title').textContent = 'Error';
        document.getElementById('task-description').textContent = error.message;
    }
}

// ===== EVENT LISTENERS =====

document.addEventListener('DOMContentLoaded', () => {
    document.getElementById('btn-previous').addEventListener('click', handlePrevious);
    document.getElementById('btn-next').addEventListener('click', handleNext);
    document.getElementById('btn-toggle').addEventListener('click', handleToggle);
    document.getElementById('btn-done').addEventListener('click', handleDone);
    document.getElementById('btn-sync').addEventListener('click', handleSync);
    document.getElementById('btn-export').addEventListener('click', handleExport);

    // Start initialization
    initialize();
});