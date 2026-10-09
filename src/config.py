from __future__ import annotations

import os
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[1]
MAX_UPLOAD_BYTES = 10 * 1024 * 1024
MODEL_NAME = os.getenv("HIRESENSE_OLLAMA_MODEL", "qwen2.5:latest")
OLLAMA_BASE_URL = os.getenv("HIRESENSE_OLLAMA_URL", "http://localhost:11434").rstrip("/")
DATABASE_PATH = Path(os.getenv("HIRESENSE_DATABASE", str(ROOT_DIR / "data" / "hiresense.db")))
DEFAULT_WEIGHTS = {
    "skills": 0.50,
    "semantic": 0.25,
    "experience": 0.15,
    "education": 0.10,
}
