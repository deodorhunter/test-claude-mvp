import asyncio
from typing import Optional

from ai.models.base import ModelAdapter, OllamaUnavailableError, ClaudeConfigError
from ai.models.factory import get_model_adapter
from ai.models.claude import ClaudeAdapter
from ai.planner.plan import ExecutionPlan


class PlannerError(Exception):
    """Base exception for planner errors."""


class QuotaExceededError(PlannerError):
    """Raised when the tenant has no remaining token quota."""


class NoPlannerAvailableError(PlannerError):
    """Raised when no model adapter is reachable and no fallback is available."""


class Planner:
    async def plan(
        self,
        prompt: str,
        context: str,
        quota_remaining: int,
        settings,
        _primary_adapter: Optional[ModelAdapter] = None,
    ) -> ExecutionPlan:
        """
        Select an appropriate model adapter for the given prompt and context.

        Args:
            prompt: The user prompt.
            context: Additional context to include in the request.
            quota_remaining: Token budget remaining for the tenant (caller-supplied).
            settings: Application Settings instance.
            _primary_adapter: Optional override for the primary adapter (test injection only).

        Returns:
            ExecutionPlan with the selected adapter and metadata.

        Raises:
            QuotaExceededError: If quota_remaining <= 0 or estimated tokens exceed quota.
            NoPlannerAvailableError: If no adapter is reachable and no fallback exists.
        """
        # Step 1 — estimate token cost
        estimated = (len(prompt) + len(context)) // 4

        # Step 2 — quota guard
        if quota_remaining <= 0:
            raise QuotaExceededError(
                f"Tenant has no remaining token quota (quota_remaining={quota_remaining})"
            )
        if estimated > quota_remaining:
            raise QuotaExceededError(
                f"Estimated tokens ({estimated}) exceed remaining quota ({quota_remaining})"
            )

        # Step 3 — resolve primary adapter
        primary = _primary_adapter if _primary_adapter is not None else get_model_adapter(settings)

        # Step 4 — probe primary adapter availability (30s timeout, matches OllamaAdapter httpx timeout)
        try:
            probe_response = await asyncio.wait_for(primary.generate("ping", ""), timeout=30.0)
            return ExecutionPlan(
                adapter=primary,
                model_used=probe_response.model_used,
                estimated_tokens=estimated,
                fallback=False,
                provider=probe_response.provider,
            )
        except (OllamaUnavailableError, asyncio.TimeoutError):
            pass  # fall through to fallback logic

        # Step 5 — attempt fallback to Claude
        if settings.ANTHROPIC_API_KEY:
            try:
                fallback_adapter = ClaudeAdapter(settings)
                probe = await asyncio.wait_for(
                    fallback_adapter.generate("ping", ""), timeout=30.0
                )
                return ExecutionPlan(
                    adapter=fallback_adapter,
                    model_used=probe.model_used,
                    estimated_tokens=estimated,
                    fallback=True,
                    provider=probe.provider,
                )
            except (ClaudeConfigError, asyncio.TimeoutError, Exception):
                pass

        raise NoPlannerAvailableError(
            "Primary adapter is unavailable and no fallback is configured or reachable."
        )
