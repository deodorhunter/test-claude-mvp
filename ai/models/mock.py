from .base import ModelAdapter, ModelResponse


class MockAdapter(ModelAdapter):
    def __init__(self, response_text: str = "Mock response"):
        self._response_text = response_text

    async def generate(self, prompt: str, context: str = "") -> ModelResponse:
        return ModelResponse(
            text=self._response_text,
            model_used="mock",
            tokens_used=10,
            provider="mock",
        )
