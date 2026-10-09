from __future__ import annotations

from pathlib import Path

import pytest

from src.job_parser import JobDescriptionError, parse_job_description

FIXTURE = Path(__file__).parent / "fixtures" / "sample_job_description.txt"


def test_parse_job_sections_skills_and_years() -> None:
    job = parse_job_description(FIXTURE.read_text(encoding="utf-8"), "Senior Data Analyst")
    assert job["job_title"] == "Senior Data Analyst"
    assert {"Python", "SQL"} <= set(job["required_skills"])
    assert {"Tableau", "Machine Learning"} <= set(job["preferred_skills"])
    assert job["minimum_years_experience"] == 3
    assert any("Analyze product" in line for line in job["responsibilities"])
    assert not any("Required skills" in line for line in job["responsibilities"])


def test_reject_short_job_description() -> None:
    with pytest.raises(JobDescriptionError, match="30 characters"):
        parse_job_description("Too short.")


def test_year_ranges_use_the_minimum_years() -> None:
    for phrase in ("3-5 years", "between 3 and 5 years"):
        job = parse_job_description(
            f"We need an analyst with {phrase} of experience in Python."
        )
        assert job["minimum_years_experience"] == 3
