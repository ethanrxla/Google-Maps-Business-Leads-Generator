import os

from leadgen.llm_insights import llm_analyze_website


def test_llm_insights_disabled_by_default(monkeypatch):
    monkeypatch.delenv("ENABLE_LLM", raising=False)
    assert llm_analyze_website("anything") == {}


def test_llm_insights_placeholder_when_enabled(monkeypatch):
    monkeypatch.setenv("ENABLE_LLM", "1")
    result = llm_analyze_website("hello world")
    assert result.get("insight") == "placeholder"
    assert "summary" in result
