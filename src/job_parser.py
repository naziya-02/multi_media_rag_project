from __future__ import annotations

import re
from typing import Any

from src.privacy import redact_personal_details
from src.skill_extractor import extract_skills


class JobDescriptionError(ValueError):
    """A clear validation error for an insufficient job description."""


YEARS_RE = re.compile(
    r"\b(?:between\s+)?(\d{1,2})(?:\s*(?:-|–|to|and)\s*\d{1,2})?\+?\s+years?\b",
    re.I,
)
PREFERRED_CUE = re.compile(r"\b(preferred|desirable|bonus|nice to have|a plus|ideally)\b", re.I)
REQUIRED_CUE = re.compile(r"\b(required|must have|minimum qualifications|you will need)\b", re.I)
SECTION_NAMES = {
    "responsibilities": ("responsibilities", "what you will do", "what you'll do", "key duties"),
    "qualifications": ("qualifications", "requirements", "what we are looking for", "your qualifications"),
}
OTHER_SECTION_HEADINGS = {
    "experience requirements",
    "preferred skills",
    "required skills",
    "skills",
    "what you bring",
}


def _classify_skills(text: str) -> tuple[list[str], list[str]]:
    required: list[str] = []
    preferred: list[str] = []
    active: str | None = None
    for line in redact_personal_details(text).splitlines():
        cleaned = line.strip(" \t-*•")
        if not cleaned:
            continue
        heading = re.sub(r"[^a-z ]", "", cleaned.lower()).strip()
        if "preferred" in heading or "nice to have" in heading or "desired" in heading:
            active = "preferred"
        elif "required" in heading or "must have" in heading or "qualifications" in heading:
            active = "required"
        line_skills = extract_skills(cleaned)
        if not line_skills:
            continue
        if PREFERRED_CUE.search(cleaned) or active == "preferred":
            preferred.extend(line_skills)
        elif REQUIRED_CUE.search(cleaned) or active == "required":
            required.extend(line_skills)
        else:
            required.extend(line_skills)
    required = list(dict.fromkeys(required))
    preferred = [skill for skill in dict.fromkeys(preferred) if skill not in required]
    return required, preferred


def _extract_sections(text: str) -> dict[str, list[str]]:
    result = {key: [] for key in SECTION_NAMES}
    active: str | None = None
    for line in redact_personal_details(text).splitlines():
        cleaned = line.strip(" \t-*•")
        if not cleaned:
            continue
        normalized = re.sub(r"[^a-z ]", "", cleaned.lower()).strip()
        matching = next(
            (name for name, aliases in SECTION_NAMES.items() if normalized in aliases),
            None,
        )
        if matching:
            active = matching
            continue
        if normalized in OTHER_SECTION_HEADINGS:
            active = None
            continue
        if active and len(cleaned) > 5:
            result[active].append(cleaned)
    return result


def parse_job_description(text: str, job_title: str = "") -> dict[str, Any]:
    content = text.strip()
    if len(content) < 30 or len(content.split()) < 5:
        raise JobDescriptionError(
            "Add at least 30 characters and five words so the role can be analyzed meaningfully."
        )
    required, preferred = _classify_skills(content)
    sections = _extract_sections(content)
    safe_content = redact_personal_details(content)
    years = [int(match) for match in YEARS_RE.findall(safe_content)]
    qualifications = sections["qualifications"]
    if not qualifications:
        qualifications = [
            line.strip(" \t-*•")
            for line in safe_content.splitlines()
            if re.search(r"\b(degree|bachelor|master|ph\.?d|certification|diploma)\b", line, re.I)
        ]
    return {
        "job_title": job_title.strip(),
        "raw_text": content,
        "required_skills": required,
        "preferred_skills": preferred,
        "responsibilities": sections["responsibilities"],
        "qualifications": list(dict.fromkeys(qualifications)),
        "minimum_years_experience": min(years) if years else None,
    }
