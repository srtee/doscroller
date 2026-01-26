"""
PiTodoist - Background Periodic Sync

Thread-based auto-sync with Todoist at configurable intervals.
"""

import threading
import time
import warnings
from typing import Any

from .todoist_sync import sync_tasks


# ===== BACKGROUND SYNC STATE =====

_sync_thread: threading.Thread | None = None
_sync_stop_event: threading.Event | None = None
_sync_token: str | None = None
_sync_interval: int = 300  # Default 5 minutes
_sync_lock = threading.Lock()


# ===== CONTROL FUNCTIONS =====

def start_background_sync(api_token: str, interval_seconds: int = 300) -> bool:
    """
    Start periodic background sync thread.

    Args:
        api_token: Todoist API token
        interval_seconds: Sync interval in seconds (default 300 = 5 minutes)

    Returns:
        True if sync started, False if already running
    """
    global _sync_thread, _sync_stop_event, _sync_token, _sync_interval

    with _sync_lock:
        # Check if already running
        if _sync_thread is not None and _sync_thread.is_alive():
            return False

        # Store configuration
        _sync_token = api_token
        _sync_interval = max(interval_seconds, 60)  # Minimum 60 seconds

        # Create stop event
        _sync_stop_event = threading.Event()

        # Create and start thread as daemon (will not prevent program exit)
        _sync_thread = threading.Thread(
            target=_sync_loop,
            daemon=True,
            name="PiTodoist_Background_Sync"
        )
        _sync_thread.start()

        return True


def stop_background_sync() -> bool:
    """
    Stop background sync thread.

    Returns:
        True if sync was stopped, False if not running
    """
    global _sync_thread, _sync_stop_event

    with _sync_lock:
        if _sync_stop_event is None or _sync_thread is None:
            return False

        # Signal thread to stop
        _sync_stop_event.set()

        # Wait for thread to finish (with timeout)
        if _sync_thread.is_alive():
            _sync_thread.join(timeout=5)

        # Clean up
        _sync_thread = None
        _sync_stop_event = None
        _sync_token = None

        return True


def is_sync_running() -> bool:
    """
    Check if background sync is active.

    Returns:
        True if sync thread is running, False otherwise
    """
    with _sync_lock:
        return _sync_thread is not None and _sync_thread.is_alive()


def get_sync_interval() -> int:
    """
    Get the current sync interval in seconds.

    Returns:
        Sync interval in seconds, or 0 if not configured
    """
    with _sync_lock:
        return _sync_interval if _sync_interval else 0


def set_sync_interval(interval_seconds: int) -> bool:
    """
    Update the sync interval without restarting.

    Args:
        interval_seconds: New sync interval in seconds (minimum 60)

    Returns:
        True if updated, False if not running
    """
    global _sync_interval

    with _sync_lock:
        if not is_sync_running():
            return False
        _sync_interval = max(interval_seconds, 60)
        return True


# ===== INTERNAL SYNC LOOP =====

def _sync_loop() -> None:
    """
    Internal function that runs in the background thread.
    Performs periodic syncs until stop event is set.
    """
    global _sync_stop_event, _sync_token, _sync_interval

    while True:
        # Check if we should stop
        if _sync_stop_event is None or _sync_stop_event.is_set():
            break

        # Perform sync
        try:
            if _sync_token:
                sync_tasks(_sync_token)
        except Exception:
            # Silent handling - continue running loop
            warnings.warn(
                "Background sync encountered an error",
                RuntimeWarning,
                stacklevel=2
            )

        # Wait for interval or stop event
        if _sync_stop_event is None:
            break
        _sync_stop_event.wait(_sync_interval)


# ===== MANUAL SYNC =====

def trigger_sync_now() -> bool:
    """
    Trigger an immediate sync without waiting for interval.

    Returns:
        True if sync was triggered, False if not configured
    """
    global _sync_token

    with _sync_lock:
        if _sync_token is None:
            return False
        return sync_tasks(_sync_token)