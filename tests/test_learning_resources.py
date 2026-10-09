from __future__ import annotations

from src.learning_resources import recommendation_for


def test_gap_recommendation_includes_resource_and_truthful_project_prompt() -> None:
    title, url, project = recommendation_for("SQL")
    assert title == "SQLBolt interactive lessons"
    assert url.startswith("https://")
    assert "verifiable results" in project
