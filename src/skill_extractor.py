from __future__ import annotations

import re

SKILL_ALIASES: dict[str, tuple[str, ...]] = {
    "Python": ("python",),
    "SQL": ("sql", "structured query language"),
    "Machine Learning": ("machine learning", "ml"),
    "Natural Language Processing": ("natural language processing", "nlp"),
    "Large Language Models": ("large language model", "large language models", "llm", "llms"),
    "Prompt Engineering": ("prompt engineering", "prompt design"),
    "Data Analysis": ("data analysis", "data analytics"),
    "Data Visualization": ("data visualization", "data visualisation"),
    "Statistics": ("statistics", "statistical analysis"),
    "scikit-learn": ("scikit-learn", "sklearn"),
    "PyTorch": ("pytorch", "torch"),
    "TensorFlow": ("tensorflow",),
    "Pandas": ("pandas",),
    "NumPy": ("numpy",),
    "Apache Spark": ("apache spark", "spark"),
    "Databricks": ("databricks",),
    "AWS": ("amazon web services", "aws"),
    "Azure": ("microsoft azure", "azure"),
    "Google Cloud": ("google cloud platform", "google cloud", "gcp"),
    "Docker": ("docker",),
    "Kubernetes": ("kubernetes", "k8s"),
    "Git": ("git", "github", "gitlab"),
    "Linux": ("linux",),
    "CI/CD": ("ci/cd", "continuous integration", "continuous delivery"),
    "REST APIs": ("rest api", "rest apis", "restful api", "restful apis"),
    "FastAPI": ("fastapi",),
    "Django": ("django",),
    "Flask": ("flask",),
    "JavaScript": ("javascript", "js"),
    "TypeScript": ("typescript", "ts"),
    "React": ("react", "react.js"),
    "Excel": ("microsoft excel", "excel"),
    "Power BI": ("power bi",),
    "Tableau": ("tableau",),
    "Project Management": ("project management",),
    "Agile": ("agile", "scrum"),
    "Communication": ("communication", "communicate effectively"),
    "Leadership": ("leadership", "team leadership"),
}


def _has_term(text: str, term: str) -> bool:
    escaped = re.escape(term.lower())
    return re.search(rf"(?<![a-z0-9]){escaped}(?![a-z0-9])", text.lower()) is not None


def normalize_skill(skill: str) -> str:
    candidate = skill.strip().lower()
    for canonical, aliases in SKILL_ALIASES.items():
        if candidate == canonical.lower() or candidate in aliases:
            return canonical
    return skill.strip()


def extract_skills(text: str) -> list[str]:
    found = []
    for canonical, aliases in SKILL_ALIASES.items():
        if any(_has_term(text, alias) for alias in aliases):
            found.append(canonical)
    return found
