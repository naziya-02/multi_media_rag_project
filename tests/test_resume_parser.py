from __future__ import annotations

from io import BytesIO
from pathlib import Path

import pymupdf as fitz
import pytest
from docx import Document

from src.resume_parser import ResumeParseError, parse_resume
from src.config import MAX_UPLOAD_BYTES


def _docx_bytes() -> bytes:
    document = Document()
    for line in [
        "Maya Chen",
        "maya.chen@example.test",
        "Skills",
        "Python, SQL, Pandas",
        "Experience",
        "Data Analyst | 2022 - Present",
        "Education",
        "Bachelor of Science in Statistics",
    ]:
        document.add_paragraph(line)
    result = BytesIO()
    document.save(result)
    return result.getvalue()


def _pdf_bytes() -> bytes:
    document = fitz.open()
    page = document.new_page()
    page.insert_text((72, 72), "Maya Chen\nmaya.chen@example.test\nSkills\nPython, SQL")
    data = document.tobytes()
    document.close()
    return data


def test_parse_docx_sections_contacts_and_skills() -> None:
    result = parse_resume(_docx_bytes(), "maya.docx")
    assert result["name"] == "Maya Chen"
    assert result["email"] == "maya.chen@example.test"
    assert {"Python", "SQL", "Pandas", "Statistics"} <= set(result["skills"])
    assert any("Statistics" in line for line in result["education"])


def test_parse_pdf_text() -> None:
    result = parse_resume(_pdf_bytes(), "maya.pdf")
    assert result["name"] == "Maya Chen"
    assert "Python" in result["skills"]


@pytest.mark.parametrize(
    ("data", "filename", "message"),
    [
        (b"not a PDF document with sufficient text", "resume.pdf", "signature"),
        (b"small", "resume.txt", "Unsupported"),
        (b"", "resume.docx", "empty"),
        (b"x" * (MAX_UPLOAD_BYTES + 1), "resume.pdf", "10 MB"),
    ],
    ids=["invalid-pdf-signature", "unsupported-type", "empty-file", "oversized-file"],
)
def test_reject_invalid_uploads(data: bytes, filename: str, message: str) -> None:
    with pytest.raises(ResumeParseError, match=message):
        parse_resume(data, filename)


def test_corrupt_docx_reports_clear_error() -> None:
    with pytest.raises(ResumeParseError, match="DOCX"):
        parse_resume(b"PKnot-a-valid-docx", "resume.docx")
