from dataclasses import dataclass
from ai.models.base import ModelAdapter


@dataclass
class ExecutionPlan:
    adapter: ModelAdapter
    model_used: str        # e.g. "llama3" or "claude-haiku-4-5-20251001"
    estimated_tokens: int
    fallback: bool         # True if the primary adapter was not available
    provider: str          # "ollama" | "claude" | "mock"
