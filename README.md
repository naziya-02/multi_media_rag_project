# HireSense AI

A local-first resume and job-description analysis dashboard. It extracts resume facts from PDF/DOCX, compares them to job requirements using a transparent weighted score, and can optionally use a locally running Ollama model for career coaching.

> Scores are decision-support estimates, not predictions of hiring success. The app does not evaluate protected traits and does not invent qualifications.

## Requirements and Python 3.14.8 compatibility

The project is set up for **Python 3.14.8**. It does not change or choose another interpreter. On Windows, verify the active interpreter first:

```powershell
python --version
py -0p
```

Verified in this Windows workspace with Python 3.14.8: Streamlit 1.65.0, PyMuPDF 1.28.2, python-docx 1.2.0, sentence-transformers 6.1.0, scikit-learn 1.9.1, PyTorch 2.14.1+cpu, pandas 3.0.6, and Plotly 7.1.0; all imports succeeded and `pip check` reported no broken requirements. The pinned Streamlit, PyMuPDF, python-docx, scikit-learn, and sentence-transformers distributions provide Windows-compatible binary wheels for CPython 3.14. If pip reports that a required wheel is unavailable, stop and use the troubleshooting section rather than switching Python versions silently.

## Windows and VS Code setup

Open this folder in VS Code and use its integrated PowerShell terminal:

```powershell
python --version
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
streamlit run app.py
```

If PowerShell blocks activation, run `Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass` in that terminal and activate again. In VS Code, select `.venv\Scripts\python.exe` using **Python: Select Interpreter**. Confirm `python --version` still reports 3.14.8.

## Ollama (optional)

Resume parsing and matching work without Ollama. To use the AI Career Assistant:

1. Install Ollama for Windows from [ollama.com/download](https://ollama.com/download).
2. In PowerShell, run `ollama pull qwen2.5:latest`.
3. Start Ollama (the desktop app or `ollama serve`).
4. Launch HireSense AI and open **Settings** to verify the local connection. Default URL: `http://localhost:11434`; default model: `qwen2.5:latest`.

Only the assistant conversation and the relevant, redacted resume/job context are sent to the Ollama service configured by you. The default is loopback-only; a non-local URL is blocked unless you explicitly opt in through Settings. The app does not send resume text to an external AI API.

## Semantic model

The match engine uses `sentence-transformers/all-MiniLM-L6-v2` locally for cosine similarity. On first match, Sentence Transformers may download its model files from Hugging Face; this transfers model files, not the candidate's resume. If the model cannot load, the app explicitly reports and labels a TF-IDF lexical-similarity fallback. You can change the model name in **Settings**.

## Background images

Downloaded Unsplash images are in `assets/backgrounds/`; their source/photo identifiers and licensing information are in [`assets/backgrounds/README.md`](assets/backgrounds/README.md). Images are decorative and are not required to run the app. If you delete or omit them, the dashboard uses fallback gradients. The requested Pexels recruitment page was reviewed but its featured result was not appropriate as an abstract background.

## Workflow

1. **Resume Analyzer**: upload a PDF or DOCX up to 10 MB. Text extraction is local; scanned-image PDFs need OCR before upload. Review and edit detected details before saving them in session.
2. **Job Description Analyzer**: enter a title and paste the job text (minimum 30 characters and five words).
3. **Job Match Results**: run the hybrid comparison and inspect the component chart, extracted skill overlap, and scoring method.
4. **Skill Gap Analysis**: compare missing required/preferred skills and get ethical practice ideas. Suggested bullet edits are prompts, not fabricated claims.
5. **AI Career Assistant**: ask questions, request truthful wording suggestions, or practice role-relevant interviews with local Ollama.

Default component weights: skills coverage 50%, semantic relevance 25%, relevant experience 15%, education/qualifications 10%. Weights are configurable; unavailable criteria are excluded and remaining weights are normalized. Required skills contribute 80% of skill coverage when preferred skills are also present. Semantic and lexical fallback methods are labelled separately.

Names, photographs, age, gender, religion, caste, and other protected characteristics are not matching features. Personal details are shown separately. Local SQLite analysis-history persistence is opt-in in **Settings**; uploaded files and raw resume text are not saved to SQLite. **Clear current session data** removes in-session resume/job/chat state; **Delete saved analysis history** deletes the local summaries.

Matching uses relevant resume sections (skills, education, experience, projects, certifications) and redacts direct identifiers and lines containing protected-attribute details before semantic comparison. Ineligible or insufficient evidence is reported as unavailable rather than treated as a negative result. The **Dark** and **High contrast** preferences are applied in the app for the current session.

## Sample fixtures

Fictional fixtures are in `tests/fixtures/`:

- `sample_resume.txt`
- `sample_job_description.txt`

The text resume fixture is intentionally plain text for portability; copy it into a DOCX document to try the upload interface. Parser tests create PDF and DOCX samples in memory.

## Tests

Run the tests using the same selected Python 3.14.8 interpreter:

```powershell
python -m pytest
```

Tests cover PDF/DOCX extraction, invalid/oversized uploads, job-description validation and classification, scoring, weight normalization, missing evidence, and Ollama connection failures.

## Troubleshooting

- **Wrong Python in VS Code:** select `.venv\Scripts\python.exe`, then check `python --version`; do not install packages into a different interpreter.
- **PowerShell activation denied:** `Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass`.
- **No readable PDF text:** the file may be an image scan; OCR it locally and upload a searchable PDF.
- **Sentence-transformer download fails:** matching falls back to labeled local TF-IDF similarity. Retry once network access is available or use a cached local model.
- **Ollama unavailable:** start Ollama, check `http://localhost:11434`, and run `ollama pull qwen2.5:latest`; matching does not depend on Ollama.
- **No images:** check that both image files exist under `assets/backgrounds/`; gradients are the intended fallback.
- **Native package install fails:** keep Python 3.14.8 and capture the complete pip error. Check that pip is current and that Windows architecture matches the interpreter (`py -0p`); do not silently switch interpreter versions.
