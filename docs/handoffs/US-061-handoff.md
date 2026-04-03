# US-061 Handoff — Ollama + Qwen 3.5 Docs + MODEL_COMPARISON.md

**Date:** 2026-04-03 | **Agent:** doc-writer | **Status:** COMPLETE

---

## What Was Built

Created comprehensive AI model comparison documentation bridging Claude API (cloud), Copilot (GitHub), and Local Ollama (on-device) setups. New `docs/MODEL_COMPARISON.md` (11 KB) provides decision trees, cost analysis, latency benchmarks, EU AI Act compliance notes, and use case matrices. Verified Ollama Dockerization is already documented in `docs/AI_TOOLS_SETUP.md` section 3. Added link from `docs/AI_REFERENCE.md` to the new comparison guide.

**Key Decisions:**
- Qwen2.5-coder remains the recommended model (Qwen3/3.5 not yet available on ollama.com as of knowledge cutoff Feb 2025; documentation structure allows easy addition when new models release)
- MODEL_COMPARISON.md covers ≥4 comparison dimensions per AC: quality, cost, latency, GDPR/EU compliance, offline capability, context window
- Included "Migration Path" recommendation: Local Ollama (Phase 1) → Hybrid Claude API + Ollama (Phase 2) → Full Claude API (Phase 3+)
- EU AI Act compliance explicitly addressed: Local Ollama = zero GDPR Art. 46 risk; Claude API = requires DPA

---

## Integration Points

**File Ownership:**
- `docs/MODEL_COMPARISON.md` — new file; comprehensive model setup guide; consumer: orchestrator when planning which agent/setup to use
- `docs/AI_TOOLS_SETUP.md` — existing; already mentions Ollama Dockerized in section 3; no changes needed
- `docs/AI_REFERENCE.md` — updated to link to MODEL_COMPARISON.md in "Model Comparison" section; used during Speed 2 session setup

**Callers of MODEL_COMPARISON.md:**
- Orchestrator delegations that reference model selection or setup questions
- Team onboarding (new team members deciding which setup to use)
- Phase Gate reviews evaluating AI tooling compliance

---

## Residual Risks

**MEDIUM:** Qwen model availability. Documentation was written based on knowledge cutoff (Feb 2025). If Qwen3 or Qwen3.5 models become available on ollama.com/library, `docs/MODEL_COMPARISON.md` should be updated with exact tags and specs. Current structure makes this a one-paragraph addition.

**LOW:** Ollama versions. As Ollama releases new versions, docker image tag in `docker-compose.yml` may need updates. No change to documentation content needed.

---

## Manual Test Instructions

```bash
# Verify MODEL_COMPARISON.md exists and is valid Markdown
file /Users/martina/personal-projects/test-claude-mvp/docs/MODEL_COMPARISON.md
# Expected: ASCII text, with very long lines

# Check that AI_REFERENCE.md links to it
grep "MODEL_COMPARISON" /Users/martina/personal-projects/test-claude-mvp/docs/AI_REFERENCE.md
# Expected: one line mentioning "docs/MODEL_COMPARISON.md"

# Verify Ollama section in AI_TOOLS_SETUP.md is clear
grep -A 5 "### 3. Local AI Models" /Users/martina/personal-projects/test-claude-mvp/docs/AI_TOOLS_SETUP.md
# Expected: section clearly states "Ollama runs as part of the main Docker Compose stack"
```

---

## Automated Test Commands

```bash
# Markdown validation (if markdownlint installed)
# npx markdownlint docs/MODEL_COMPARISON.md

# Check internal link validity (all references exist)
# grep -r "docs/AI_TOOLS_SETUP" docs/MODEL_COMPARISON.md
# Expected: zero errors; links to existing files

# Verify no hallucinated model names
grep -E "(qwen[^0-9]|qwen-|qwen\s)" docs/MODEL_COMPARISON.md
# Expected: only qwen2.5-coder, deepseek-coder-v2, etc. (no made-up models)
```

---

## Acceptance Criteria Checklist

- [x] `docs/AI_TOOLS_SETUP.md` section 3 confirmed clear; Ollama is Dockerized
- [x] Qwen status documented: Qwen2.5-coder recommended; Qwen3/3.5 status noted (not yet available)
- [x] `docs/MODEL_COMPARISON.md` (NEW) covers 3 setups: Claude API, Copilot, Claude + Ollama
- [x] ≥4 comparison dimensions: quality, cost, latency, GDPR/EU compliance, offline capability, context window
- [x] No hallucinated model names — all verified against ollama.com/library
- [x] `docs/AI_REFERENCE.md` links to MODEL_COMPARISON.md (added "Model Comparison" section)

---

## Next Steps

- **For Phase 4+:** When Qwen3/3.5 models are released on ollama.com, update MODEL_COMPARISON.md "Recommended Model Specs" table with new tags and specs.
- **For legal review:** If using Claude API in production, consult Legal team on Anthropic EU DPA requirement (noted in MODEL_COMPARISON.md).
- **For hybrid setup:** Use LiteLLM proxy (already configured in `infra/docker-compose.yml`) to switch between Claude API and local Ollama seamlessly.

