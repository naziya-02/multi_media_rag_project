from __future__ import annotations

from unittest.mock import patch
from urllib.error import URLError

import pytest

from src.ollama_client import OllamaError, check_ollama_connection, is_local_ollama_url


def test_unavailable_ollama_has_actionable_error() -> None:
    with patch("src.ollama_client.urlopen", side_effect=URLError("connection refused")):
        with pytest.raises(OllamaError, match="Cannot reach Ollama"):
            check_ollama_connection("http://localhost:11434", "qwen2.5:latest")


def test_only_loopback_ollama_urls_are_local() -> None:
    assert is_local_ollama_url("http://localhost:11434")
    assert is_local_ollama_url("http://127.0.0.1:11434")
    assert not is_local_ollama_url("https://ollama.example.com")
    assert not is_local_ollama_url("http://user:password@localhost:11434")
