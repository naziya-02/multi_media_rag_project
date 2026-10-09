from __future__ import annotations

import hashlib

import streamlit as st

from src.config import MAX_UPLOAD_BYTES
from src.resume_parser import ResumeParseError, parse_resume


def render_resume_upload() -> dict | None:
    st.title("Resume Analyzer")
    st.caption("PDF or DOCX · maximum 10 MB · parsed on this device")
    uploaded = st.file_uploader(
        "Choose a resume",
        type=["pdf", "docx"],
        key="resume_uploader",
        help="Only PDF and DOCX are supported. Scanned PDFs require OCR before upload.",
    )
    if uploaded is None:
        existing = st.session_state.get("resume")
        if existing:
            st.success(f"Current session resume: {existing.get('filename', 'resume')}")
        else:
            st.info("Upload a resume to extract its details. Nothing is saved unless you enable local analysis history.")
        return None
    if uploaded.size > MAX_UPLOAD_BYTES:
        st.error("Resume is over the 10 MB upload limit.")
        return None
    data = uploaded.getvalue()
    digest = hashlib.sha256(data).hexdigest()
    if digest == st.session_state.get("resume_upload_digest"):
        return st.session_state.get("resume")
    try:
        profile = parse_resume(data, uploaded.name)
    except ResumeParseError as error:
        st.error(str(error))
        return None
    except (OSError, RuntimeError) as error:
        st.error(f"Could not read this resume: {error}")
        return None
    for key in (
        "review_resume_name",
        "review_resume_skills",
        "review_resume_education",
        "review_resume_experience",
        "review_resume_projects",
        "review_resume_certifications",
        "review_resume_email",
        "review_resume_phone",
        "review_resume_links",
    ):
        st.session_state.pop(key, None)
    st.session_state["resume_upload_digest"] = digest
    return profile
