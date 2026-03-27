from .base import ModelAdapter
from .ollama import OllamaAdapter
from .claude import ClaudeAdapter
from .mock import MockAdapter


def get_model_adapter(settings) -> ModelAdapter:
    """Return the appropriate ModelAdapter based on settings.AI_MODE."""
    if settings.AI_MODE == "demo-api":
        return ClaudeAdapter(settings)
    elif settings.AI_MODE == "demo":
        return OllamaAdapter(settings)
    else:
        return MockAdapter()
