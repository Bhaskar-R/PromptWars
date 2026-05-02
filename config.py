"""Application configuration and environment validation."""

import os
from dotenv import load_dotenv

load_dotenv()

# --- API Configuration ---
GEMINI_API_KEY: str = os.getenv("GEMINI_API_KEY", "")
GEMINI_MODEL: str = "gemini-2.5-flash"
GEMINI_TIMEOUT: int = 15
GOOGLE_CLOUD_PROJECT: str = os.getenv("GOOGLE_CLOUD_PROJECT", "")

# --- Application Constants ---
APP_NAME: str = "TeamSync AI"
APP_DESCRIPTION: str = (
    "AI-powered team collaboration — smart standups, task management, "
    "and real-time visibility into your team's workflow."
)

# --- Validation Limits ---
MAX_INPUT_LENGTH: int = 5000
MAX_TASK_TITLE_LENGTH: int = 200
MAX_BLOCKER_LENGTH: int = 500
MIN_TEAM_MEMBERS: int = 1
MAX_TEAM_MEMBERS: int = 50

# --- Task Constants ---
VALID_STATUSES: list[str] = ["todo", "in_progress", "done"]
VALID_PRIORITIES: list[str] = ["low", "medium", "high", "critical"]

# --- Cache TTL (seconds) ---
GEMINI_CACHE_TTL: int = 300
FIRESTORE_CACHE_TTL: int = 60


def validate_config() -> bool:
    """Validate all required environment variables are set."""
    if not GEMINI_API_KEY:
        raise EnvironmentError(
            "GEMINI_API_KEY not set. Copy .env.example to .env and fill in values."
        )
    return True
