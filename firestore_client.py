"""Firestore database client for task persistence.

Handles CRUD operations for tasks with lazy client initialization.
Falls back to in-memory storage if Firestore is unavailable.
"""

import uuid
from typing import Any, Optional

from config import GOOGLE_CLOUD_PROJECT

# Collection name constant
TASKS_COLLECTION: str = "tasks"


def _get_firestore_client() -> Any:
    """Lazy initialization of Firestore client.

    Returns None if Firestore is unavailable (local dev without credentials).
    """
    try:
        from google.cloud import firestore
        return firestore.Client(project=GOOGLE_CLOUD_PROJECT)
    except Exception:
        return None


def generate_task_id() -> str:
    """Generate a unique task ID."""
    return f"T{uuid.uuid4().hex[:6].upper()}"


def save_task(task: dict[str, Any]) -> bool:
    """Save a task to Firestore. Returns True on success."""
    client = _get_firestore_client()
    if client is None:
        return False
    try:
        task_id = task.get("id", generate_task_id())
        client.collection(TASKS_COLLECTION).document(task_id).set(task)
        return True
    except Exception:
        return False


def get_all_tasks() -> Optional[list[dict[str, Any]]]:
    """Fetch all tasks from Firestore. Returns None if unavailable."""
    client = _get_firestore_client()
    if client is None:
        return None
    try:
        docs = client.collection(TASKS_COLLECTION).stream()
        return [doc.to_dict() for doc in docs]
    except Exception:
        return None


def update_task(task_id: str, updates: dict[str, Any]) -> bool:
    """Update specific fields of a task. Returns True on success."""
    client = _get_firestore_client()
    if client is None:
        return False
    try:
        client.collection(TASKS_COLLECTION).document(task_id).update(updates)
        return True
    except Exception:
        return False


def delete_task(task_id: str) -> bool:
    """Delete a task from Firestore. Returns True on success."""
    client = _get_firestore_client()
    if client is None:
        return False
    try:
        client.collection(TASKS_COLLECTION).document(task_id).delete()
        return True
    except Exception:
        return False
