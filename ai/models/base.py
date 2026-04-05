from dataclasses import dataclass
from abc import ABC, abstractmethod


@dataclass
class ModelResponse:
    text: str
    model_used: str
    tokens_used: int
    provider: str  # "ollama" | "claude" | "mock"
    cache_read_tokens: int = 0
    cache_creation_tokens: int = 0


class ModelAdapter(ABC):
    @abstractmethod
    async def generate(
        self, prompt: str, context: str = ""
    ) -> ModelResponse: ...


class ModelError(Exception):
    """Base exception for model layer errors."""


class OllamaUnavailableError(ModelError):
    """Raised when Ollama service is unreachable or times out."""


class ClaudeConfigError(ModelError):
    """Raised when Claude is misconfigured (e.g. missing API key)."""
