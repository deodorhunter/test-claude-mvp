import anthropic
from .base import ModelAdapter, ModelResponse, ClaudeConfigError

_CLAUDE_MODEL = "claude-haiku-4-5-20251001"


class ClaudeAdapter(ModelAdapter):
    def __init__(self, settings):
        if not settings.ANTHROPIC_API_KEY:
            raise ClaudeConfigError(
                "ANTHROPIC_API_KEY is not set. "
                "Set AI_MODE=demo to use Ollama instead, or provide a valid API key."
            )
        self._client = anthropic.AsyncAnthropic(api_key=settings.ANTHROPIC_API_KEY)

    async def generate(self, prompt: str, context: str = "") -> ModelResponse:
        full_content = prompt + context
        message = await self._client.messages.create(
            model=_CLAUDE_MODEL,
            max_tokens=1024,
            messages=[{"role": "user", "content": full_content}],
        )
        text = message.content[0].text if message.content else ""
        tokens_used = message.usage.input_tokens + message.usage.output_tokens
        return ModelResponse(
            text=text,
            model_used=_CLAUDE_MODEL,
            tokens_used=tokens_used,
            provider="claude",
        )
