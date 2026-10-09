from __future__ import annotations

from typing import Any

from src.privacy import redact_personal_details


def build_assistant_context(
    resume: dict[str, Any], job: dict[str, Any] | None, match: dict[str, Any] | None
) -> str:
    parts = [
        "Resume facts (user-provided):",
        f"Skills: {redact_personal_details(', '.join(resume.get('skills', []))) or 'not extracted'}",
        f"Education: {redact_personal_details('; '.join(resume.get('education', []))) or 'not provided'}",
        f"Experience: {redact_personal_details('; '.join(resume.get('experience', []))) or 'not provided'}",
        f"Projects: {redact_personal_details('; '.join(resume.get('projects', []))) or 'not provided'}",
        f"Certifications: {redact_personal_details('; '.join(resume.get('certifications', []))) or 'not provided'}",
        "Resume text:",
        redact_personal_details(
            resume.get("raw_text", ""), resume.get("name", "")
        )[:8000],
    ]
    if job:
        parts.extend(
            [
                f"Target job: {job.get('job_title') or 'not specified'}",
                f"Required skills: {', '.join(job.get('required_skills', [])) or 'not detected'}",
                f"Preferred skills: {', '.join(job.get('preferred_skills', [])) or 'not detected'}",
                f"Job description: {redact_personal_details(job.get('raw_text', ''))[:6000]}",
            ]
        )
    if match:
        parts.extend(
            [
                f"Measured estimated match score: {match['overall_score']}%",
                f"Matching skills: {', '.join(match.get('matching_skills', []))}",
                f"Missing required skills: {', '.join(match.get('missing_required_skills', []))}",
                f"Missing preferred skills: {', '.join(match.get('missing_preferred_skills', []))}",
                f"Scoring method: {match.get('semantic_method')}; {match.get('limitations')}",
            ]
        )
    return "\n".join(parts)
