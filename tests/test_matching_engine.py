from __future__ import annotations

from pathlib import Path
from unittest.mock import patch

import pytest

from src.job_parser import parse_job_description
from src.matching_engine import MatchingError, calculate_match

FIXTURES = Path(__file__).parent / "fixtures"
RESUME_TEXT = (FIXTURES / "sample_resume.txt").read_text(encoding="utf-8")
JOB = parse_job_description(
    (FIXTURES / "sample_job_description.txt").read_text(encoding="utf-8"), "Senior Data Analyst"
)
RESUME = {
    "raw_text": RESUME_TEXT,
    "skills": ["Python", "SQL", "Pandas", "scikit-learn", "Data Visualization", "Git"],
    "education": ["Bachelor of Science in Statistics, Fictional State University, 2021"],
    "experience": ["Data Analyst | Northstar Labs | 2022 - Present"],
}


def test_match_score_has_transparent_components_and_expected_skill_gaps() -> None:
    result = calculate_match(RESUME, JOB, use_sentence_transformer=False)
    assert 0 <= result["overall_score"] <= 100
    assert result["components"]["skills"]["score"] is not None
    assert result["components"]["semantic"]["score"] is not None
    assert result["components"]["experience"]["score"] is not None
    assert "Python" in result["matching_skills"]
    assert "Machine Learning" in result["missing_preferred_skills"]
    assert "TF-IDF" in result["semantic_method"]
    assert abs(sum(component["normalized_weight"] for component in result["components"].values()) - 1) < 0.001


def test_unavailable_components_are_excluded_and_weights_normalized() -> None:
    job = {"raw_text": "Python role requires analysis and reporting.", "required_skills": ["Python"], "preferred_skills": []}
    result = calculate_match(
        {"raw_text": "Python analysis and reporting.", "skills": ["Python"], "education": []},
        job,
        use_sentence_transformer=False,
    )
    assert result["components"]["experience"]["score"] is None
    assert result["components"]["education"]["score"] is None
    assert result["components"]["experience"]["normalized_weight"] == 0
    assert sum(item["normalized_weight"] for item in result["components"].values()) == pytest.approx(1)


def test_education_dates_are_not_counted_as_work_experience() -> None:
    job = {
        "raw_text": "Python role requires five years of experience.",
        "required_skills": ["Python"],
        "preferred_skills": [],
        "minimum_years_experience": 5,
    }
    resume = {
        "raw_text": "Python\nBachelor of Science, 2010 - 2020",
        "skills": ["Python"],
        "education": ["Bachelor of Science, 2010 - 2020"],
        "experience": [],
    }
    result = calculate_match(resume, job, use_sentence_transformer=False)
    assert result["components"]["experience"]["score"] is None


def test_invalid_weights_are_rejected() -> None:
    with pytest.raises(MatchingError, match="non-negative"):
        calculate_match(RESUME, JOB, weights={"skills": -1, "semantic": 1, "experience": 1, "education": 1})


def test_sentence_transformer_score_uses_local_injected_model() -> None:
    class Model:
        def encode(self, texts, normalize_embeddings):
            assert normalize_embeddings is True
            return [[1.0, 0.0], [0.8, 0.6]]

    result = calculate_match(
        RESUME,
        JOB,
        semantic_model_loader=lambda model_name: Model(),
        use_sentence_transformer=True,
    )
    assert result["components"]["semantic"]["score"] == 80.0
    assert "Sentence-transformer" in result["semantic_method"]


def test_sentence_transformer_failure_is_reported_with_lexical_fallback() -> None:
    with patch("src.matching_engine._sentence_transformer_similarity", side_effect=OSError("offline")):
        result = calculate_match(RESUME, JOB)
    assert result["semantic_method"] == "TF-IDF lexical similarity"
    assert "offline" in result["semantic_note"]
