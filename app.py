from __future__ import annotations

import base64

import streamlit as st

from components.charts import render_score_chart
from components.dashboard import render_dashboard
from components.match_results import render_match_results
from components.resume_upload import render_resume_upload
from components.sidebar import render_sidebar
from src.career_assistant import build_assistant_context
from src.config import DEFAULT_WEIGHTS, MODEL_NAME, OLLAMA_BASE_URL, ROOT_DIR
from src.job_parser import JobDescriptionError, parse_job_description
from src.learning_resources import recommendation_for
from src.matching_engine import MatchingError, calculate_match
from src.ollama_client import (
    OllamaError,
    check_ollama_connection,
    chat_with_ollama,
    is_local_ollama_url,
)
from src.resume_parser import ResumeParseError, parse_resume
from src.storage import clear_history, get_history, save_analysis

st.set_page_config(
    page_title="HireSense AI | Career intelligence",
    page_icon="✦",
    layout="wide",
    initial_sidebar_state="expanded",
)


def _background_css(theme: str) -> str:
    css_path = ROOT_DIR / "styles" / "main.css"
    css = css_path.read_text(encoding="utf-8")
    declarations = []
    for name, filename in (
        ("--hero-image", "hero-abstract.jpg"),
        ("--landing-image", "landing-dark.jpg"),
    ):
        path = ROOT_DIR / "assets" / "backgrounds" / filename
        if path.is_file():
            encoded = base64.b64encode(path.read_bytes()).decode("ascii")
            declarations.append(f"{name}: url(data:image/jpeg;base64,{encoded});")
    theme_attribute = " data-theme='high-contrast'" if theme == "High contrast" else ""
    return f"<style>{css}\n:root{{{''.join(declarations)}}}</style><div{theme_attribute} class='theme-marker'></div>"


st.markdown(_background_css(st.session_state.get("theme", "Dark")), unsafe_allow_html=True)

for key, default in {
    "resume": None,
    "job": None,
    "match": None,
    "analysis_history": [],
    "assistant_messages": [],
    "ollama_url": OLLAMA_BASE_URL,
    "ollama_model": MODEL_NAME,
    "persist_history": False,
    "theme": "Dark",
    "weights": DEFAULT_WEIGHTS.copy(),
    "semantic_model": "sentence-transformers/all-MiniLM-L6-v2",
    "allow_remote_ollama": False,
    "resume_upload_digest": None,
}.items():
    if key not in st.session_state:
        st.session_state[key] = default

page = render_sidebar()


def _profile_items(value: object, *, comma_separated: bool = False) -> list[str]:
    if isinstance(value, str):
        pieces = value.split(",") if comma_separated else value.splitlines()
    elif isinstance(value, list):
        pieces = value
    else:
        return []
    items = [str(item).strip() for item in pieces if str(item).strip()]
    if len(items) > 3 and all(len(item) == 1 for item in items):
        joined = "".join(items)
        pieces = joined.split(",") if comma_separated else joined.splitlines()
        items = [str(item).strip() for item in pieces if str(item).strip()]
    return items


def _analyse_current_pair() -> None:
    resume = st.session_state.get("resume")
    job = st.session_state.get("job")
    if not resume or not job:
        st.warning("Add a resume and a job description before running a match.")
        return
    try:
        with st.spinner("Comparing resume and role evidence locally..."):
            result = calculate_match(
                resume,
                job,
                weights=st.session_state["weights"],
                model_name=st.session_state["semantic_model"],
            )
    except MatchingError as error:
        st.error(str(error))
        return
    st.session_state["match"] = result
    entry = {
        "job_title": job.get("job_title") or "Untitled role",
        "score": result["overall_score"],
        "created_at": result["created_at"],
        "components": result["components"],
    }
    st.session_state["analysis_history"].insert(0, entry)
    if st.session_state["persist_history"]:
        save_analysis(entry)


def _send_assistant_prompt(prompt: str) -> None:
    context = build_assistant_context(
        st.session_state["resume"], st.session_state.get("job"), st.session_state.get("match")
    )
    st.session_state["assistant_messages"].append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)
    with st.chat_message("assistant"):
        with st.spinner("Thinking locally with Ollama..."):
            try:
                answer = chat_with_ollama(
                    prompt,
                    context,
                    st.session_state["assistant_messages"][:-1],
                    base_url=st.session_state["ollama_url"],
                    model=st.session_state["ollama_model"],
                )
            except OllamaError as error:
                st.error(str(error))
            else:
                st.markdown(answer)
                st.session_state["assistant_messages"].append(
                    {"role": "assistant", "content": answer}
                )


if page == "Dashboard":
    render_dashboard(
        st.session_state.get("analysis_history", []),
        get_history() if st.session_state["persist_history"] else [],
        has_resume=bool(st.session_state.get("resume")),
        has_job=bool(st.session_state.get("job")),
    )
    left, right = st.columns([1, 1])
    with left:
        if st.button("Analyze a resume", use_container_width=True, type="primary"):
            st.session_state["page"] = "Resume Analyzer"
            st.rerun()
    with right:
        if st.button("Match with a job", use_container_width=True):
            st.session_state["page"] = "Job Description Analyzer"
            st.rerun()
elif page == "Resume Analyzer":
    profile = render_resume_upload()
    if profile:
        st.session_state["resume"] = profile
        st.success("Resume parsed locally. Review and edit the extracted details below.")
        with st.form("resume_review"):
            name = st.text_input("Name", value=profile.get("name", ""), key="review_resume_name")
            skills_text = st.text_area(
                "Skills (comma-separated)",
                value=", ".join(_profile_items(profile.get("skills", []), comma_separated=True)),
                height=90,
                key="review_resume_skills",
            )
            education_text = st.text_area(
                "Education",
                value="\n".join(_profile_items(profile.get("education", []))),
                height=110,
                key="review_resume_education",
            )
            experience_text = st.text_area(
                "Work experience",
                value="\n".join(_profile_items(profile.get("experience", []))),
                height=160,
                key="review_resume_experience",
            )
            projects_text = st.text_area(
                "Projects",
                value="\n".join(_profile_items(profile.get("projects", []))),
                height=120,
                key="review_resume_projects",
            )
            certifications_text = st.text_area(
                "Certifications",
                value="\n".join(_profile_items(profile.get("certifications", []))),
                height=90,
                key="review_resume_certifications",
            )
            with st.expander("Contact details (private)"):
                email = st.text_input("Email", value=profile.get("email", ""), key="review_resume_email")
                phone = st.text_input("Phone", value=profile.get("phone", ""), key="review_resume_phone")
                links_text = st.text_area(
                    "Links",
                    value="\n".join(_profile_items(profile.get("links", []))),
                    height=70,
                    key="review_resume_links",
                )
            saved = st.form_submit_button("Save reviewed resume", type="primary")
        if saved:
            reviewed_profile = {
                **profile,
                "name": name.strip(),
                "email": email.strip(),
                "phone": phone.strip(),
                "skills": _profile_items(skills_text, comma_separated=True),
                "education": _profile_items(education_text),
                "experience": _profile_items(experience_text),
                "projects": _profile_items(projects_text),
                "certifications": _profile_items(certifications_text),
                "links": _profile_items(links_text),
            }
            reviewed_profile["raw_text"] = "\n".join(
                [
                    reviewed_profile["name"],
                    "Skills",
                    ", ".join(reviewed_profile["skills"]),
                    "Education",
                    *reviewed_profile["education"],
                    "Experience",
                    *reviewed_profile["experience"],
                    "Projects",
                    *reviewed_profile["projects"],
                    "Certifications",
                    *reviewed_profile["certifications"],
                ]
            )
            st.session_state["resume"] = reviewed_profile
            st.session_state["match"] = None
            st.success("Your reviewed resume is ready to match.")
elif page == "Job Description Analyzer":
    st.title("Job Description Analyzer")
    st.caption("Paste the role details. Your text stays in this app unless you choose Ollama assistance.")
    title = st.text_input(
        "Target job title",
        value=(st.session_state.get("job") or {}).get("job_title", ""),
        placeholder="e.g. Senior Data Analyst",
    )
    description = st.text_area(
        "Job description",
        value=(st.session_state.get("job") or {}).get("raw_text", ""),
        height=300,
        placeholder="Paste responsibilities, required skills, qualifications, and experience expectations...",
    )
    if st.button("Analyze job description", type="primary"):
        try:
            parsed = parse_job_description(description, job_title=title)
        except JobDescriptionError as error:
            st.error(str(error))
        else:
            st.session_state["job"] = parsed
            st.session_state["match"] = None
            st.success("Job description analyzed.")
            st.subheader("Extracted requirements")
            st.write("**Required skills**")
            st.write(", ".join(parsed["required_skills"]) or "None explicitly identified")
            st.write("**Preferred skills**")
            st.write(", ".join(parsed["preferred_skills"]) or "None explicitly identified")
            if parsed["responsibilities"]:
                st.write("**Responsibilities**")
                for item in parsed["responsibilities"]:
                    st.markdown(f"- {item}")
            if parsed["qualifications"]:
                st.write("**Qualifications**")
                for item in parsed["qualifications"]:
                    st.markdown(f"- {item}")
            if parsed["minimum_years_experience"] is not None:
                st.info(
                    f"Explicit experience requirement detected: "
                    f"{parsed['minimum_years_experience']} years."
                )
elif page == "Job Match Results":
    st.title("Job Match Results")
    if st.session_state.get("resume") and st.session_state.get("job"):
        if st.button("Calculate match", type="primary"):
            _analyse_current_pair()
        result = st.session_state.get("match")
        if result:
            render_match_results(result)
            render_score_chart(result["components"])
    else:
        st.info("Upload a resume and analyze a job description first.")
elif page == "Skill Gap Analysis":
    st.title("Skill Gap Analysis")
    result = st.session_state.get("match")
    if not result:
        st.info("Run a job match to see skills you can focus on.")
    else:
        st.subheader("Skills found in your resume and requested by the role")
        st.write(", ".join(result["matching_skills"]) or "No direct skill overlap detected.")
        st.subheader("Missing required skills")
        st.write(", ".join(result["missing_required_skills"]) or "No required skill gaps detected.")
        st.subheader("Missing preferred skills")
        st.write(", ".join(result["missing_preferred_skills"]) or "No preferred skill gaps detected.")
        st.subheader("Other skills listed in your resume")
        st.write(", ".join(result["additional_resume_skills"]) or "No additional extracted skills.")
        st.subheader("Learning resources and project ideas")
        for skill in result["missing_required_skills"] + result["missing_preferred_skills"]:
            resource, url, project = recommendation_for(skill)
            st.markdown(f"**{skill}**")
            st.markdown(f"Resource: [{resource}]({url})")
            st.write(project)
        st.subheader("Bullet point improvement prompts")
        st.caption("Use these as editing prompts, not as claims to copy. Keep only details that are true.")
        for line in (st.session_state.get("resume") or {}).get("experience", []):
            st.markdown(f"- Clarify the action, tools used, and verifiable outcome in: “{line}”")
elif page == "AI Career Assistant":
    st.title("AI Career Assistant")
    if not st.session_state.get("resume"):
        st.info("Upload a resume to start a grounded career conversation.")
    else:
        remote_ollama = not is_local_ollama_url(st.session_state["ollama_url"])
        if remote_ollama and not st.session_state["allow_remote_ollama"]:
            st.warning(
                "This Ollama URL is not a loopback address. Resume context will not be sent "
                "unless you explicitly enable remote Ollama consent in Settings."
            )
        st.caption(
            "Assistant prompts and resume/job context go only to the Ollama URL configured by you. "
            "Remote Ollama URLs require explicit consent in Settings."
        )
        can_send = not remote_ollama or st.session_state["allow_remote_ollama"]
        quick_prompt = None
        if st.session_state.get("job") and can_send:
            a, b, c = st.columns(3)
            if a.button("Suggest resume improvements"):
                quick_prompt = "Suggest truthful improvements to my resume for this job."
            if b.button("Interview practice"):
                quick_prompt = "Generate relevant interview questions and sample answers grounded in my experience."
            if c.button("Explain my match"):
                quick_prompt = "Explain the match result, strengths, and skill gaps."
        for message in st.session_state["assistant_messages"]:
            with st.chat_message(message["role"]):
                st.markdown(message["content"])
        if can_send:
            prompt = st.chat_input("Ask about your resume, skill gaps, or interview preparation")
        else:
            st.info("Enable remote Ollama consent in Settings to start a conversation.")
            prompt = None
        if prompt or quick_prompt:
            _send_assistant_prompt(prompt or quick_prompt)
elif page == "Settings":
    st.title("Settings")
    st.subheader("Local AI")
    st.session_state["ollama_url"] = st.text_input(
        "Ollama base URL", value=st.session_state["ollama_url"], help="Usually http://localhost:11434"
    ).rstrip("/")
    st.session_state["ollama_model"] = st.text_input(
        "Ollama model", value=st.session_state["ollama_model"], help="For example qwen2.5:latest"
    )
    remote_ollama = not is_local_ollama_url(st.session_state["ollama_url"])
    if remote_ollama:
        st.session_state["allow_remote_ollama"] = st.checkbox(
            "I explicitly consent to sending resume/job context to this non-local Ollama server",
            value=st.session_state["allow_remote_ollama"],
        )
    else:
        st.session_state["allow_remote_ollama"] = False
    if st.button("Check Ollama connection"):
        with st.spinner("Checking your local Ollama service..."):
            try:
                status = check_ollama_connection(
                    st.session_state["ollama_url"], st.session_state["ollama_model"]
                )
            except OllamaError as error:
                st.error(str(error))
            else:
                st.success(status)
    st.session_state["semantic_model"] = st.text_input(
        "Sentence-transformer model",
        value=st.session_state.get("semantic_model", "sentence-transformers/all-MiniLM-L6-v2"),
        help="Downloaded model runs locally; first use may download model files.",
    )
    st.subheader("Scoring weights")
    st.caption("Components are normalized over only the criteria with enough evidence to evaluate.")
    weight_columns = st.columns(4)
    labels = {
        "skills": "Skills coverage",
        "semantic": "Semantic relevance",
        "experience": "Relevant experience",
        "education": "Education / qualifications",
    }
    current_weights = st.session_state["weights"]
    proposed_weights = {}
    for column, (key, label) in zip(weight_columns, labels.items()):
        with column:
            proposed_weights[key] = st.number_input(
                label,
                min_value=0,
                max_value=100,
                value=int(current_weights[key] * 100),
                step=5,
            ) / 100
    weight_sum = sum(proposed_weights.values())
    if weight_sum > 0:
        st.session_state["weights"] = proposed_weights
        st.caption(f"Configured weights total {weight_sum * 100:.0f}%; active weights are normalized.")
    else:
        st.error("At least one scoring weight must be greater than zero.")
    st.subheader("Privacy and history")
    st.session_state["persist_history"] = st.checkbox(
        "Save match summaries to local SQLite history",
        value=st.session_state["persist_history"],
        help="Resume files are never persisted. Disable this to keep history only in this browser session.",
    )
    if st.button("Delete saved analysis history"):
        clear_history()
        st.session_state["analysis_history"] = []
        st.session_state["match"] = None
        st.success("Local analysis history cleared.")
    if st.button("Clear current session data", type="secondary"):
        for key in ("resume", "job", "match", "analysis_history", "assistant_messages"):
            st.session_state[key] = [] if key in ("analysis_history", "assistant_messages") else None
        st.session_state["resume_upload_digest"] = None
        st.session_state.pop("resume_uploader", None)
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
        st.success("Current resume, job, match, and assistant conversation cleared.")
    st.selectbox(
        "Theme preference",
        ["Dark", "High contrast"],
        index=["Dark", "High contrast"].index(st.session_state["theme"]),
        key="theme",
    )
    st.caption("Theme preference is applied immediately and retained for this session.")
