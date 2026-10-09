from __future__ import annotations

import re

EMAIL_RE = re.compile(r"\b[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}\b", re.I)
PHONE_RE = re.compile(r"(?<!\w)\+?\d[\d\s().-]{8,}\d(?!\w)")
URL_RE = re.compile(r"\b(?:https?://|www\.)\S+", re.I)
PROTECTED_INFO_RE = re.compile(
    r"\b(?:age|aged|date of birth|dob|gender|sex|female|male|non[- ]?binary|"
    r"transgender|religion|caste|race|racial|ethnicity|ethnic|nationality|"
    r"citizenship|marital status|sexual orientation|disability)\b",
    re.I,
)


def redact_personal_details(text: str, name: str = "") -> str:
    lines = []
    for line in text.splitlines():
        if PROTECTED_INFO_RE.search(line):
            continue
        cleaned = EMAIL_RE.sub(" ", line)
        cleaned = PHONE_RE.sub(
            lambda match: " " if sum(character.isdigit() for character in match.group()) >= 10 else match.group(),
            cleaned,
        )
        cleaned = URL_RE.sub(" ", cleaned)
        if name.strip():
            cleaned = re.sub(re.escape(name.strip()), " ", cleaned, flags=re.I)
        cleaned = re.sub(r"\s+", " ", cleaned).strip()
        if cleaned:
            lines.append(cleaned)
    return "\n".join(lines)


def resume_evidence_text(resume: dict) -> str:
    fields = ("skills", "education", "experience", "projects", "certifications")
    sections = []
    for field in fields:
        values = resume.get(field, [])
        if isinstance(values, str):
            values = [values]
        sections.extend(line for line in values if isinstance(line, str))
    evidence = "\n".join(sections)
    if not evidence.strip():
        evidence = resume.get("raw_text", "")
    return redact_personal_details(evidence, resume.get("name", ""))
