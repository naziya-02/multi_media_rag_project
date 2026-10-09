from __future__ import annotations

from src.storage import clear_history, get_history, save_analysis


def test_local_history_round_trip_and_delete(tmp_path) -> None:
    database = tmp_path / "history.db"
    entry = {
        "job_title": "Analyst",
        "score": 82.5,
        "created_at": "2026-10-09T00:00:00.000+00:00",
        "components": {"skills": {"score": 80.0}},
    }
    save_analysis(entry, database)
    assert get_history(database) == [entry]
    clear_history(database)
    assert get_history(database) == []
