import os


def llm_analyze_website(text: str | None) -> dict:
    """
    Placeholder for LLM insights (disabled in tests).
    Only runs when ENABLE_LLM environment variable is set to "1".
    """
    if os.getenv("ENABLE_LLM") != "1":
        return {}

    if not text:
        return {"insight": "placeholder"}

    return {
        "insight": "placeholder",
        "summary": f"Analyzed {len(text)} characters of content.",
    }
