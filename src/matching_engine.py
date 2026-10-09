from __future__ import annotations

import re
from datetime import datetime, timezone
from functools import lru_cache
from typing import Any, Callable

import numpy as np
from requests.exceptions import RequestException
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

from src.config import DEFAULT_WEIGHTS
from src.privacy import redact_personal_details, resume_evidence_text
from src.skill_extractor import extract_skills, normalize_skill

ModelLoader = Callable[[str], Any]


class MatchingError(ValueError):
    """Invalid scoring settings or inputs."""


def _tfidf_similarity(resume_text: str, job_text: str) -> float:
    vectorizer = TfidfVectorizer(stop_words="english", ngram_range=(1, 2))
    try:
        vectors = vectorizer.fit_transform([resume_text, job_text])
    except ValueError:
        return 0.0
    return float(np.clip(cosine_similarity(vectors[0:1], vectors[1:2])[0, 0], 0, 1))


@lru_cache(maxsize=2)
def _load_sentence_model(model_name: str) -> Any:
    from sentence_transformers import SentenceTransformer

    return SentenceTransformer(model_name)


def _sentence_transformer_similarity(
    resume_text: str,
    job_text: str,
    model_name: str,
    model_loader: ModelLoader | None = None,
) -> float:
    if model_loader is None:
        model = _load_sentence_model(model_name)
    else:
        model = model_loader(model_name)
    vectors = model.encode([resume_text, job_text], normalize_embeddings=True)
    return float(np.clip(np.dot(vectors[0], vectors[1]), 0, 1))


def _experience_years(resume_text: str) -> float | None:
    date_pattern = re.compile(
        r"\b(?:(?:jan(?:uary)?|feb(?:ruary)?|mar(?:ch)?|apr(?:il)?|may|jun(?:e)?|"
        r"jul(?:y)?|aug(?:ust)?|sep(?:tember)?|oct(?:ober)?|nov(?:ember)?|dec(?:ember)?)\s+)?"
        r"(20\d{2})\s*(?:[-–—]|to)\s*(?:(?:jan(?:uary)?|feb(?:ruary)?|mar(?:ch)?|"
        r"apr(?:il)?|may|jun(?:e)?|jul(?:y)?|aug(?:ust)?|sep(?:tember)?|oct(?:ober)?|"
        r"nov(?:ember)?|dec(?:ember)?|present|current)?\s*(20\d{2}|present|current))",
        re.I,
    )
    periods = []
    current_year = datetime.now(timezone.utc).year
    for start, end in date_pattern.findall(resume_text):
        start_year = int(start)
        end_year = current_year if end.lower() in {"present", "current"} else int(end)
        if start_year <= end_year <= current_year and end_year - start_year <= 50:
            periods.append((start_year, end_year))
    if not periods:
        return None
    years = set()
    for start, end in periods:
        years.update(range(start, end + 1))
    return float(len(years))


def _education_score(resume_text: str, job: dict[str, Any]) -> float | None:
    requirement = " ".join(job.get("qualifications", []))
    if not re.search(r"\b(degree|bachelor|master|ph\.?d|diploma|certification)\b", requirement, re.I):
        return None
    education = " ".join(job.get("qualifications", []))
    resume_education = redact_personal_details(
        "\n".join(job.get("_resume_education", []))
    )
    if not resume_education:
        return None
    keywords = re.findall(
        r"\b(?:degree|bachelor|master|ph\.?d|diploma|certification|computer science|engineering|statistics|mathematics)\b",
        education,
        re.I,
    )
    if not keywords:
        return None
    matched = sum(1 for keyword in set(word.lower() for word in keywords) if re.search(rf"\b{re.escape(keyword)}\b", resume_education, re.I))
    return matched / len(set(keywords))


def calculate_match(
    resume: dict[str, Any],
    job: dict[str, Any],
    *,
    weights: dict[str, float] | None = None,
    model_name: str = "sentence-transformers/all-MiniLM-L6-v2",
    semantic_model_loader: ModelLoader | None = None,
    use_sentence_transformer: bool = True,
) -> dict[str, Any]:
    if not resume.get("raw_text") or not job.get("raw_text"):
        raise MatchingError("Resume and job description text are both required.")
    configured = dict(DEFAULT_WEIGHTS if weights is None else weights)
    expected = set(DEFAULT_WEIGHTS)
    if set(configured) != expected or any(
        not isinstance(weight, (int, float)) or weight < 0 for weight in configured.values()
    ):
        raise MatchingError("Scoring weights must define non-negative skills, semantic, experience, and education values.")
    if sum(configured.values()) <= 0:
        raise MatchingError("At least one scoring weight must be greater than zero.")

    required = list(dict.fromkeys(normalize_skill(skill) for skill in job.get("required_skills", [])))
    preferred = [
        skill
        for skill in dict.fromkeys(normalize_skill(skill) for skill in job.get("preferred_skills", []))
        if skill not in required
    ]
    resume_skills = set(normalize_skill(skill) for skill in resume.get("skills", []))
    if not resume_skills:
        resume_skills = set(extract_skills(resume["raw_text"]))
    target_skills = required + preferred
    matching = [skill for skill in target_skills if skill in resume_skills]
    missing_required = [skill for skill in required if skill not in resume_skills]
    missing_preferred = [skill for skill in preferred if skill not in resume_skills]
    if required and preferred:
        skill_score = 0.8 * (len(required) - len(missing_required)) / len(required)
        skill_score += 0.2 * (len(preferred) - len(missing_preferred)) / len(preferred)
    elif target_skills:
        skill_score = len(matching) / len(target_skills)
    else:
        skill_score = None

    semantic_method = "TF-IDF lexical similarity"
    semantic_note = (
        "The local sentence-transformer model was not enabled; TF-IDF measures word/phrase overlap, "
        "not deep semantic understanding."
    )
    resume_text = resume_evidence_text(resume)
    job_text = redact_personal_details(
        "\n".join(part for part in (job.get("job_title", ""), job["raw_text"]) if part)
    )
    if use_sentence_transformer:
        try:
            semantic_score = _sentence_transformer_similarity(
                resume_text, job_text, model_name, semantic_model_loader
            )
            semantic_method = f"Sentence-transformer cosine similarity ({model_name})"
            semantic_note = "Embeddings were calculated locally. Model files may be downloaded on first use."
        except (ImportError, OSError, RequestException, RuntimeError, ValueError) as error:
            semantic_score = _tfidf_similarity(resume_text, job_text)
            semantic_note = (
                f"Sentence-transformer scoring was unavailable ({error}). "
                "The score uses TF-IDF lexical similarity instead."
            )
    else:
        semantic_score = _tfidf_similarity(resume_text, job_text)

    minimum_years = job.get("minimum_years_experience")
    experience_lines = resume.get("experience", [])
    if isinstance(experience_lines, str):
        experience_lines = [experience_lines]
    experience_text = redact_personal_details("\n".join(experience_lines))
    years = _experience_years(experience_text)
    experience_score = (
        min(years / minimum_years, 1.0)
        if minimum_years and years is not None
        else None
    )
    job_with_education = dict(job)
    job_with_education["_resume_education"] = resume.get("education", [])
    education_score = _education_score(resume["raw_text"], job_with_education)
    available = {
        "skills": skill_score,
        "semantic": semantic_score,
        "experience": experience_score,
        "education": education_score,
    }
    active_weight = sum(configured[key] for key, value in available.items() if value is not None)
    if active_weight <= 0:
        raise MatchingError("No scoring components have enough evidence. Add resume skills or adjust scoring weights.")
    normalized = {
        key: (weight / active_weight if available[key] is not None else 0.0)
        for key, weight in configured.items()
    }
    total = sum(normalized[key] * value for key, value in available.items() if value is not None)
    additional = sorted(resume_skills - set(target_skills))
    return {
        "overall_score": round(total * 100, 1),
        "components": {
            key: {
                "score": round(value * 100, 1) if value is not None else None,
                "configured_weight": configured[key],
                "normalized_weight": round(normalized[key], 4),
            }
            for key, value in available.items()
        },
        "matching_skills": matching,
        "missing_required_skills": missing_required,
        "missing_preferred_skills": missing_preferred,
        "additional_resume_skills": additional,
        "semantic_method": semantic_method,
        "semantic_note": semantic_note,
        "available_weight": round(active_weight, 4),
        "limitations": (
            "This is an evidence-based estimate, not a prediction of hiring success. "
            "Unavailable components are excluded and the remaining configured weights are normalized. "
            "Dates, education, and extracted skills can be incomplete or ambiguous; review the source resume."
        ),
        "created_at": datetime.now(timezone.utc).isoformat(timespec="milliseconds"),
    }
