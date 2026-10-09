from __future__ import annotations

import json
import sqlite3
from pathlib import Path
from typing import Any

from src.config import DATABASE_PATH


def _connect(path: Path | None = None) -> sqlite3.Connection:
    database = path or DATABASE_PATH
    database.parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(database)
    connection.execute(
        """
        CREATE TABLE IF NOT EXISTS analyses (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            job_title TEXT NOT NULL,
            score REAL NOT NULL,
            created_at TEXT NOT NULL,
            components_json TEXT NOT NULL
        )
        """
    )
    return connection


def save_analysis(analysis: dict[str, Any], path: Path | None = None) -> None:
    with _connect(path) as connection:
        connection.execute(
            "INSERT INTO analyses (job_title, score, created_at, components_json) VALUES (?, ?, ?, ?)",
            (
                analysis["job_title"],
                analysis["score"],
                analysis["created_at"],
                json.dumps(analysis["components"]),
            ),
        )


def get_history(path: Path | None = None, limit: int = 100) -> list[dict[str, Any]]:
    with _connect(path) as connection:
        rows = connection.execute(
            "SELECT job_title, score, created_at, components_json FROM analyses "
            "ORDER BY id DESC LIMIT ?",
            (limit,),
        ).fetchall()
    return [
        {
            "job_title": title,
            "score": score,
            "created_at": created_at,
            "components": json.loads(components),
        }
        for title, score, created_at, components in rows
    ]


def clear_history(path: Path | None = None) -> None:
    with _connect(path) as connection:
        connection.execute("DELETE FROM analyses")
