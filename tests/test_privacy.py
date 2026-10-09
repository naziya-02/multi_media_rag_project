from __future__ import annotations

from pathlib import Path

from src.job_parser import parse_job_description
from src.matching_engine import calculate_match
from src.privacy import redact_personal_details, resume_evidence_text


def test_redaction_removes_direct_identifiers_and_protected_attribute_lines() -> None:
    result = redact_personal_details(
        "Maya Chen\nmaya@example.test\n+1 (555) 222-3311\nFemale candidate, age 29\nPython project",
        "Maya Chen",
    )
    assert "Maya" not in result
    assert "maya@example.test" not in result
    assert "555" not in result
    assert "Female" not in result
    assert "Python project" in result


def test_semantic_evidence_uses_resume_facts_not_header_personal_data() -> None:
    result = resume_evidence_text(
        {
            "name": "Maya Chen",
            "raw_text": "Maya Chen\nmaya@example.test\nPython",
            "skills": ["Python"],
            "experience": ["Built a Python reporting tool."],
            "education": [],
            "projects": [],
            "certifications": [],
        }
    )
    assert "Maya" not in result
    assert "maya@example.test" not in result
    assert "Python" in result


def test_names_and_protected_resume_lines_do_not_change_match_score() -> None:
    fixture = Path(__file__).parent / "fixtures" / "sample_job_description.txt"
    job = parse_job_description(fixture.read_text(encoding="utf-8"))
    first = {
        "name": "Maya Chen",
        "raw_text": "Maya Chen\nPython SQL\nFemale candidate, age 29",
        "skills": ["Python", "SQL"],
        "education": [],
        "experience": ["Built Python and SQL dashboards."],
        "projects": [],
        "certifications": [],
    }
    second = {
        **first,
        "name": "Jordan Lee",
        "raw_text": "Jordan Lee\nPython SQL\nMale candidate, age 50",
    }
    score_one = calculate_match(first, job, use_sentence_transformer=False)["overall_score"]
    score_two = calculate_match(second, job, use_sentence_transformer=False)["overall_score"]
    assert score_one == score_two
