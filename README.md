# PiTodoist

A client-side task manager and time tracker that works directly with Todoist.

## Overview

PiTodoist is a purely browser-contained application that:

- Fetches tasks directly from Todoist API
- Tracks time spent on tasks with start/stop timers
- Marks tasks complete with automatic Todoist sync
- Stores all data locally using localStorage

## Features

- **Direct Todoist Integration** - No backend server required, calls Todoist API directly from the browser
- **Time Tracking** - Start and stop timers on tasks, view total time spent
- **Local Storage** - All time entries and state stored in browser localStorage
- **Simple Interface** - Navigate tasks with arrow buttons, start/stop/done with action buttons
- **Minimal Storage** - Optimized to use very little space (~50 bytes + ~25 bytes per time entry)

## Quick Start

### Option 1: Open the HTML file directly

1. Clone or download this repository
2. Open `index.html` in your web browser
3. Enter your Todoist API token when prompted

### Option 2: Use with a token in URL

Open `index.html?token=YOUR_TODOIST_API_TOKEN` to skip the prompt.

### Getting a Todoist API Token

1. Go to [Todoist Integrations Settings](https://todoist.com/app/settings/integrations/developer)
2. Create a new token
3. Copy and paste it when prompted

## Usage

### Navigation

- **`<-` / `->`** - Navigate between tasks
- **`▶`** - Start timing the current task
- **`||`** - Stop timing the active task
- **`✓`** (single-click) - Mark current task as complete
- **`✓`** (double-click) - Toggle between incomplete and completed tasks view

### Time Tracking

1. Navigate to a task
2. Press `▶` to start the timer
3. When done, press `||` to stop, or `✓` to complete the task
4. View total time on completed tasks in the done view

## Storage

All data is stored in the browser using localStorage under these keys:

| Key | Purpose |
|-----|---------|
| `pitodoist:token` | Todoist API token |
| `pitodoist:active` | Active time entry `{t, s}` or `null` |
| `pitodoist:entries` | Array of completed time entries `[{t, s, e}]` |

Entry structure:
- `t` - Task ID
- `s` - Start timestamp (Unix epoch seconds)
- `e` - End timestamp (Unix epoch seconds)

## Architecture

The application is entirely client-side:

```
Browser
├── HTML (index.html)
├── CSS (styles.css)
└── JavaScript (app.js)
    ├── Storage layer (localStorage)
    ├── Todoist API client
    └── UI logic
```

No backend server is required. The app can be:
- Opened directly as a file
- Hosted on GitHub Pages, Netlify, or any static host
- Used offline (with cached tasks in memory, but time entries persist)

## Development

### Files

- `index.html` - Main HTML structure
- `styles.css` - Styling
- `app.js` - All JavaScript logic

### Storage Optimization

See [STORAGE_OPTIMIZATION.md](STORAGE_OPTIMIZATION.md) for details on how storage was minimized.

## License

MIT License