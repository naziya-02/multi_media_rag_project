from __future__ import annotations

from typing import Any

import pandas as pd
import streamlit as st


def render_dashboard(
    session_history: list[dict[str, Any]],
    saved_history: list[dict[str, Any]],
    *,
    has_resume: bool,
    has_job: bool,
) -> None:
    session_dates = {item["created_at"] for item in session_history}
    history = session_history + [
        item for item in saved_history if item["created_at"] not in session_dates
    ]
    scores = [float(item["score"]) for item in history]
    average = float(pd.Series(scores).mean()) if scores else None
    st.markdown(
        """
        <section class="hero">
          <div class="hero-content">
            <span class="eyebrow">CAREER INTELLIGENCE, BUILT AROUND YOU</span>
            <h1>Your Next Career Move<br>Starts Here.</h1>
            <p>Understand your strengths, close skill gaps, and move forward with confidence.</p>
          </div>
        </section>
        """,
        unsafe_allow_html=True,
    )
    st.markdown("<div class='section-heading'><h2>Your overview</h2><span>Grounded in your analyses</span></div>", unsafe_allow_html=True)
    first, second, third = st.columns(3)
    with first:
        st.metric(
            "Resumes analyzed",
            str(len(history)),
            help="Each completed match analyzes one resume against one job description.",
        )
    with second:
        st.metric("Average match score", f"{average:.1f}%" if average is not None else "—")
    with third:
        st.metric("Job descriptions analyzed", str(len(history)))
    st.markdown("<div class='section-heading'><h2>Recent analyses</h2></div>", unsafe_allow_html=True)
    if history:
        for item in history[:5]:
            left, middle, right = st.columns([3, 1, 2])
            left.write(item["job_title"])
            middle.write(f"{item['score']:.1f}%")
            right.caption(item["created_at"][:10])
    else:
        st.info("Your analysis history will appear here after your first match.")
    st.markdown("<div class='section-heading'><h2>Suggested next steps</h2></div>", unsafe_allow_html=True)
    actions = [
        ("01", "Add your resume", "Your data is parsed locally and never sent by default.", has_resume),
        ("02", "Paste a job description", "We identify role requirements from the text you provide.", has_job),
        ("03", "Explore your match", "Review evidence, scoring weights, and skill gaps.", bool(history)),
    ]
    columns = st.columns(3)
    for column, (number, title, body, complete) in zip(columns, actions):
        with column:
            st.markdown(
                f"<div class='glass-card'><span class='action-number'>{number}</span>"
                f"<h3>{title}</h3><p>{body}</p><small>{'Complete' if complete else 'Ready when you are'}</small></div>",
                unsafe_allow_html=True,
            )
