from __future__ import annotations

RESOURCES: dict[str, tuple[str, str]] = {
    "Python": ("Python tutorial", "https://docs.python.org/3/tutorial/"),
    "SQL": ("SQLBolt interactive lessons", "https://sqlbolt.com/"),
    "Machine Learning": ("Google Machine Learning Crash Course", "https://developers.google.com/machine-learning/crash-course"),
    "Natural Language Processing": ("Hugging Face NLP course", "https://huggingface.co/learn/nlp-course/chapter1/1"),
    "Large Language Models": ("Hugging Face LLM course", "https://huggingface.co/learn/llm-course/chapter1/1"),
    "Prompt Engineering": ("Anthropic prompt engineering guide", "https://docs.anthropic.com/en/docs/build-with-claude/prompt-engineering/overview"),
    "Data Analysis": ("pandas getting started", "https://pandas.pydata.org/docs/getting_started/intro_tutorials/"),
    "Data Visualization": ("Plotly Python fundamentals", "https://plotly.com/python/"),
    "Statistics": ("OpenStax Introductory Statistics", "https://openstax.org/details/books/introductory-statistics"),
    "scikit-learn": ("scikit-learn tutorials", "https://scikit-learn.org/stable/tutorial/index.html"),
    "PyTorch": ("PyTorch tutorials", "https://pytorch.org/tutorials/"),
    "TensorFlow": ("TensorFlow tutorials", "https://www.tensorflow.org/tutorials"),
    "Pandas": ("pandas getting started", "https://pandas.pydata.org/docs/getting_started/intro_tutorials/"),
    "NumPy": ("NumPy user guide", "https://numpy.org/doc/stable/user/"),
    "Apache Spark": ("Apache Spark quick start", "https://spark.apache.org/docs/latest/quick-start.html"),
    "Databricks": ("Databricks learning", "https://docs.databricks.com/en/getting-started/index.html"),
    "AWS": ("AWS getting started", "https://aws.amazon.com/getting-started/"),
    "Azure": ("Microsoft Learn: Azure", "https://learn.microsoft.com/en-us/training/azure/"),
    "Google Cloud": ("Google Cloud training", "https://cloud.google.com/learn/training"),
    "Docker": ("Docker getting started", "https://docs.docker.com/get-started/"),
    "Kubernetes": ("Kubernetes tutorials", "https://kubernetes.io/docs/tutorials/"),
    "Git": ("Pro Git book", "https://git-scm.com/book/en/v2"),
    "Linux": ("Linux command-line basics", "https://ubuntu.com/tutorials/command-line-for-beginners"),
    "CI/CD": ("GitHub Actions quickstart", "https://docs.github.com/en/actions/writing-workflows/quickstart"),
    "REST APIs": ("MDN: HTTP overview", "https://developer.mozilla.org/en-US/docs/Web/HTTP/Overview"),
    "FastAPI": ("FastAPI tutorial", "https://fastapi.tiangolo.com/tutorial/"),
    "Django": ("Django tutorial", "https://docs.djangoproject.com/en/stable/intro/tutorial01/"),
    "Flask": ("Flask quickstart", "https://flask.palletsprojects.com/en/stable/quickstart/"),
    "JavaScript": ("MDN JavaScript guide", "https://developer.mozilla.org/en-US/docs/Web/JavaScript/Guide"),
    "TypeScript": ("TypeScript handbook", "https://www.typescriptlang.org/docs/handbook/intro.html"),
    "React": ("React learn", "https://react.dev/learn"),
    "Excel": ("Microsoft Excel help", "https://support.microsoft.com/en-us/excel"),
    "Power BI": ("Microsoft Learn: Power BI", "https://learn.microsoft.com/en-us/training/powerplatform/power-bi/"),
    "Tableau": ("Tableau free training videos", "https://www.tableau.com/learn/training"),
}


def recommendation_for(skill: str) -> tuple[str, str, str]:
    resource, url = RESOURCES.get(
        skill,
        (f"{skill} documentation", f"https://www.google.com/search?q={skill.replace(' ', '+')}+official+documentation"),
    )
    project = (
        f"Create a small portfolio project that uses {skill} to solve a problem related to this role. "
        "Document your approach, decisions, and verifiable results before adding it to your resume."
    )
    return resource, url, project
