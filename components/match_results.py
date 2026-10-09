from __future__ import annotations

from typing import Any

import streamlit as st


def render_match_results(result: dict[str, Any]) -> None:
    score = result["overall_score"]
    st.markdown(
        f"<div class='score-card'><span class='eyebrow'>ESTIMATED ROLE COMPATIBILITY</span>"
        f"<strong>{score:.1f}<small>%</small></strong>"
        f"<p>Evidence-based estimate · not a prediction of hiring success</p></div>",
        unsafe_allow_html=True,
    )
    st.subheader("What the score means")
    if result["matching_skills"]:
        st.write(
            f"Your resume provides evidence of **{', '.join(result['matching_skills'])}** "
            "requested skills."
        )
    if result["missing_required_skills"]:
        st.write(
            f"The description also requests **{', '.join(result['missing_required_skills'])}**, "
            "which were not found in the resume text."
        )
    if not result["matching_skills"] and not result["missing_required_skills"]:
        st.write("No direct skill matches or explicit required-skill gaps were detected.")
    st.write(result["limitations"])
    st.caption(f"Semantic component: {result['semantic_method']}. {result['semantic_note']}")
    with st.expander("How this score is calculated"):
        st.markdown(
            "- Skills coverage counts extracted resume skills present in the role. Required skills "
            "carry 80% of that component when preferred skills are also listed; otherwise the "
            "detected skills are equally weighted.\n"
            "- Semantic relevance is local sentence-transformer cosine similarity. If unavailable, "
            "the result explicitly switches to TF-IDF word/phrase overlap.\n"
            "- Experience estimates calendar years from explicit date ranges in the experience "
            "section and compares them with a stated minimum. It is not inferred from education dates.\n"
            "- Education/qualification evidence is compared only when the job states a qualification "
            "and the resume includes an education section.\n"
            "- Each available component uses your configured weight. Unavailable components are "
            "omitted, then remaining weights are normalized to 100%."
        )
    st.subheader("Score breakdown")
    labels = {
        "skills": "Skills coverage",
        "semantic": "Semantic relevance",
        "experience": "Relevant experience",
        "education": "Education / qualifications",
    }
    columns = st.columns(4)
    for column, (key, label) in zip(columns, labels.items()):
        component = result["components"][key]
        with column:
            value = component["score"]
            st.metric(label, f"{value:.1f}%" if value is not None else "Not evaluated")
            st.caption(f"Normalized weight: {component['normalized_weight'] * 100:.1f}%")
    st.subheader("Skills evidence")
    st.write("**Matching skills:** " + (", ".join(result["matching_skills"]) or "None detected"))
    st.write(
        "**Missing required:** "
        + (", ".join(result["missing_required_skills"]) or "None detected")
    )
    st.write(
        "**Missing preferred:** "
        + (", ".join(result["missing_preferred_skills"]) or "None detected")
    )
