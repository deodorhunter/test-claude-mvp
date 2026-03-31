import os
import anthropic
from .base import ModelAdapter, ModelResponse, ClaudeConfigError

_CLAUDE_MODEL = "claude-haiku-4-5-20251001"
# Cache TTL: "ephemeral" (5min default) or use extended cache header for long sessions
_CACHE_TTL = os.environ.get("AI_CACHE_TTL", "ephemeral")


class ClaudeAdapter(ModelAdapter):
    def __init__(self, settings):
        if not settings.ANTHROPIC_API_KEY:
            raise ClaudeConfigError(
                "ANTHROPIC_API_KEY is not set. "
                "Set AI_MODE=demo to use Ollama instead, or provide a valid API key."
            )
        extra_headers = {}
        if _CACHE_TTL != "ephemeral":
            extra_headers["anthropic-beta"] = "prompt-caching-2024-07-31"
        self._client = anthropic.AsyncAnthropic(
            api_key=settings.ANTHROPIC_API_KEY,
            default_headers=extra_headers if extra_headers else None,
        )

    async def generate(
        self,
        prompt: str,
        context: str = "",
        system: str = "",
        cache_system: bool = True,
    ) -> ModelResponse:
        """Generate a response with optional prompt caching.

        Args:
            prompt: User message content.
            context: Additional context appended to the user message.
            system: Stable system instructions (cached when cache_system=True).
            cache_system: Whether to apply cache_control to the system block.
        """
        full_content = prompt + context

        # Build system block with cache_control on stable content
        system_blocks = []
        if system:
            block = {"type": "text", "text": system}
            if cache_system:
                block["cache_control"] = {"type": _CACHE_TTL}
            system_blocks.append(block)

        kwargs = {
            "model": _CLAUDE_MODEL,
            "max_tokens": 1024,
            "messages": [{"role": "user", "content": full_content}],
        }
        if system_blocks:
            kwargs["system"] = system_blocks

        message = await self._client.messages.create(**kwargs)
        text = message.content[0].text if message.content else ""
        usage = message.usage

        # Track cache metrics when available
        cache_read = getattr(usage, "cache_read_input_tokens", 0) or 0
        cache_creation = getattr(usage, "cache_creation_input_tokens", 0) or 0
        tokens_used = usage.input_tokens + usage.output_tokens

        return ModelResponse(
            text=text,
            model_used=_CLAUDE_MODEL,
            tokens_used=tokens_used,
            provider="claude",
            cache_read_tokens=cache_read,
            cache_creation_tokens=cache_creation,
        )
