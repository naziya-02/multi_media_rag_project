from __future__ import annotations

import streamlit as st


def render_sidebar() -> str:
    st.sidebar.markdown(
        '<div class="brand"><span class="brand-mark">✦</span><span>HireSense <b>AI</b></span></div>',
        unsafe_allow_html=True,
    )
    pages = [
        "Dashboard",
        "Resume Analyzer",
        "Job Description Analyzer",
        "Job Match Results",
        "Skill Gap Analysis",
        "AI Career Assistant",
        "Settings",
    ]
    icons = ["◈", "▤", "⌕", "◎", "◇", "✧", "⚙"]
    selected = st.session_state.get("page", "Dashboard")
    if selected not in pages:
        selected = "Dashboard"
    st.sidebar.caption("WORKSPACE")
    for icon, name in zip(icons, pages):
        if st.sidebar.button(
            f"{icon}  {name}",
            key=f"navigate_{name}",
            type="primary" if selected == name else "secondary",
            use_container_width=True,
        ):
            st.session_state["page"] = name
            st.rerun()
            return name
    st.sidebar.markdown("---")
    st.sidebar.markdown(
        '<div class="privacy-note"><span>●</span> Private by design<br>'
        '<small>Resume processing stays on this device.</small></div>',
        unsafe_allow_html=True,
    )
    st.sidebar.caption("Decision support, not a hiring decision.")
    return selected
