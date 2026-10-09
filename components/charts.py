from __future__ import annotations

from typing import Any

import plotly.graph_objects as go
import streamlit as st


def render_score_chart(components: dict[str, Any]) -> None:
    labels = {
        "skills": "Skills",
        "semantic": "Semantic relevance",
        "experience": "Experience",
        "education": "Education",
    }
    visible = [(labels[key], item["score"]) for key, item in components.items() if item["score"] is not None]
    if not visible:
        st.info("Not enough data to chart the match components.")
        return
    figure = go.Figure(
        go.Bar(
            x=[item[0] for item in visible],
            y=[item[1] for item in visible],
            marker={
                "color": ["#9b7cff", "#55a7ff", "#41d5d2", "#c78cff"][: len(visible)],
                "line": {"color": "rgba(255,255,255,.3)", "width": 1},
            },
            text=[f"{item[1]:.1f}%" for item in visible],
            textposition="outside",
            hovertemplate="%{x}: %{y:.1f}%<extra></extra>",
        )
    )
    figure.update_layout(
        title="Evidence by matching dimension",
        yaxis={"range": [0, 110], "title": "Component score", "gridcolor": "rgba(255,255,255,.08)"},
        xaxis={"title": ""},
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font={"color": "#e8e8f3"},
        margin={"l": 10, "r": 10, "t": 55, "b": 10},
        height=320,
        showlegend=False,
    )
    st.plotly_chart(figure, use_container_width=True, config={"displayModeBar": False})
