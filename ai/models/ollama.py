import httpx
from .base import ModelAdapter, ModelResponse, OllamaUnavailableError


class OllamaAdapter(ModelAdapter):
    def __init__(self, settings):
        self._url = settings.OLLAMA_URL
        self._model = settings.OLLAMA_MODEL

    async def generate(self, prompt: str, context: str = "") -> ModelResponse:
        full_prompt = prompt + context
        payload = {
            "model": self._model,
            "prompt": full_prompt,
            "stream": False,
        }
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    f"{self._url}/api/generate",
                    json=payload,
                )
                response.raise_for_status()
                data = response.json()
        except (httpx.TimeoutException, httpx.ConnectError) as exc:
            raise OllamaUnavailableError(
                f"Ollama service unreachable at {self._url}: {exc}"
            ) from exc

        return ModelResponse(
            text=data["response"],
            model_used=self._model,
            tokens_used=data.get("eval_count", 0),
            provider="ollama",
        )
