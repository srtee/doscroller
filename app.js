// PiTodoist - Frontend Application

// ===== STATE MANAGEMENT =====

const state = {
    taskList: [],
    doneTaskList: [],
    currentIndex: 0,
    viewingDone: false,
    activeTaskId: null,
    apiToken: null,
    lastPollTime: 0
};

// ===== API COMMUNICATION =====

async function apiRequest(endpoint, options = {}) {
    const url = `/api${endpoint}`;
    const headers = {
        'Content-Type': 'application/json',
        ...options.headers
    };

    if (state.apiToken && !headers['Authorization']) {
        headers['Authorization'] = `Bearer ${state.apiToken}`;
    }

    try {
        const response = await fetch(url, { ...options, headers });
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

async function fetchTasks() {
    return apiRequest('/tasks');
}

async function fetchCompletedTasks() {
    return apiRequest('/tasks/completed');
}

async function fetchActiveTask() {
    return apiRequest('/active');
}

async function startTask(taskId) {
    return apiRequest(`/start/${taskId}`, { method: 'POST' });
}

async function stopTask(taskId) {
    return apiRequest(`/stop/${taskId}`, { method: 'POST' });
}

async function completeTask(taskId) {
    return apiRequest(`/complete/${taskId}`, { method: 'POST' });
}

async function fetchTaskTime(taskId) {
    return apiRequest(`/time/${taskId}`);
}

async function syncTasks() {
    return apiRequest('/sync');
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
    const playBtn = document.getElementById('btn-play');
    const stopBtn = document.getElementById('btn-stop');

    const currentTask = getCurrentTask();
    const isActive = currentTask && currentTask.id === state.activeTaskId;

    // Play button: disabled if current task is already active
    playBtn.disabled = isActive || !currentTask;

    // Stop button: enabled only if a task is active
    stopBtn.disabled = !state.activeTaskId;
}

function updateActiveTaskState(activeSummary) {
    if (activeSummary) {
        state.activeTaskId = activeSummary.task.id;
    } else {
        state.activeTaskId = null;
    }
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

async function handlePlay() {
    const task = getCurrentTask();
    if (!task) return;

    try {
        await startTask(task.id);
        state.activeTaskId = task.id;
        updateButtonStates();
        showMessage('Task started');
    } catch (error) {
        showMessage(error.message, 'error');
    }
}

async function handleStop() {
    const task = getCurrentTask();
    if (!task) return;

    try {
        await stopTask(task.id);
        state.activeTaskId = null;
        updateButtonStates();
        showMessage('Task stopped');
    } catch (error) {
        showMessage(error.message, 'error');
    }
}

// Done button click handler with double-click detection
let doneClickTimeout = null;

function handleDone() {
    const task = getCurrentTask();
    if (!task) return;

    // Clear any existing timeout
    if (doneClickTimeout) {
        clearTimeout(doneClickTimeout);
        doneClickTimeout = null;
    }

    // Set timeout for single-click action
    doneClickTimeout = setTimeout(async () => {
        // Single-click: complete the task
        try {
            await completeTask(task.id);
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
        } catch (error) {
            showMessage(error.message, 'error');
        }

        doneClickTimeout = null;
    }, 300);
}

function handleDoneDoubleClick() {
    // Double-click: toggle done view
    if (doneClickTimeout) {
        clearTimeout(doneClickTimeout);
        doneClickTimeout = null;
    }

    toggleDoneView();
}

async function toggleDoneView() {
    state.viewingDone = !state.viewingDone;
    state.currentIndex = 0;

    if (state.viewingDone) {
        // Load completed tasks if not already loaded
        if (state.doneTaskList.length === 0) {
            try {
                state.doneTaskList = await fetchCompletedTasks();
            } catch (error) {
                showMessage(error.message, 'error');
                state.viewingDone = false;
                return;
            }
        }
    }

    updateTaskDisplay();
    updateButtonStates();
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
    let token = localStorage.getItem('pitodoist_token');
    if (token) return token;

    // Check URL parameter
    const urlParams = new URLSearchParams(window.location.search);
    token = urlParams.get('token');
    if (token) {
        localStorage.setItem('pitodoist_token', token);
        // Remove token from URL
        window.history.replaceState({}, '', window.location.pathname);
        return token;
    }

    // Prompt user
    token = prompt('Please enter your Todoist API token:');
    if (token) {
        localStorage.setItem('pitodoist_token', token);
        return token;
    }

    throw new Error('API token required');
}

// ===== POLLING =====

async function pollActiveTask() {
    try {
        const summary = await fetchActiveTask();
        updateActiveTaskState(summary);
    } catch (error) {
        console.error('Polling error:', error);
    }

    // Poll every 20 seconds (since no timer display is shown)
    setTimeout(pollActiveTask, 20000);
}

// ===== INITIALIZATION =====

async function initialize() {
    try {
        // Get API token
        state.apiToken = await getApiToken();

        // Sync tasks with Todoist first
        await syncTasks();

        // Fetch tasks
        const [tasks, completedTasks, activeSummary] = await Promise.all([
            fetchTasks(),
            fetchCompletedTasks(),
            fetchActiveTask()
        ]);

        state.taskList = tasks;
        state.doneTaskList = completedTasks;

        // Resume active task if exists, otherwise show first incomplete task
        if (activeSummary) {
            state.activeTaskId = activeSummary.task.id;
            // Find active task in list and set index
            const activeIndex = state.taskList.findIndex(t => t.id === state.activeTaskId);
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
    document.getElementById('btn-play').addEventListener('click', handlePlay);
    document.getElementById('btn-stop').addEventListener('click', handleStop);
    document.getElementById('btn-done').addEventListener('click', handleDone);
    document.getElementById('btn-done').addEventListener('dblclick', handleDoneDoubleClick);

    // Start initialization
    initialize();
});