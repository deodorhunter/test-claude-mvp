# Model Comparison: Claude API vs Copilot vs Local Ollama

> Three AI setup approaches for development, with trade-offs across quality, cost, latency, compliance, offline capability, and context window.

---

## Setup Comparison Matrix

| Dimension | Claude API (Anthropic) | Copilot (GitHub) | Claude Code + Ollama |
|---|---|---|---|
| **Primary Model** | claude-sonnet-4-6 (MEDIUM), claude-haiku-4-5 (LOW) | GPT-4o or Claude 3.5 (subscription-dependent) | qwen2.5-coder:7b or deepseek-coder-v2:16b |
| **Quality / Reasoning** | Excellent (MEDIUM → enterprise logic; LOW → config tweaks) | Good (GPT-4o strong for code) | Good for coding (Qwen2.5-coder trained on CodeSearchNet) |
| **Cost** | ~$0.003–$0.015 per 1K input tokens; $0.012–$0.060 per 1K output | $10–$20/month (capped token allowance) or pay-as-you-go | $0 (one-time local compute; electricity only) |
| **Latency** | 2–5 seconds (network round-trip) | 3–10 seconds (GitHub API + model latency) | <1 second (local inference; depends on hardware) |
| **GDPR / EU AI Act** | Requires Anthropic EU DPA (Standard Contractual Clauses in place). Data leaves your machine briefly. GDPR Art. 46 compliant if DPA signed. | Requires GitHub terms review; GPT-4o may route through US servers. GDPR requires data processing agreement. | **Zero risk** — all inference local (no data leaves machine). Automatic GDPR Art. 46 compliance. |
| **Offline Capability** | Requires internet (API calls fail if unreachable) | Requires internet (GitHub Copilot requires authentication) | **Fully offline** — Ollama runs locally in Docker; no API calls needed |
| **Context Window** | Sonnet: 200K tokens; Haiku: 200K tokens | GPT-4o: 128K tokens | Qwen2.5-coder:7b: 32K tokens; deepseek-coder-v2: 128K tokens |
| **Setup Complexity** | 1. Get Anthropic API key 2. Set `ANTHROPIC_API_KEY` in `.env` | 1. GitHub account + Copilot subscription 2. Login to Copilot in IDE | 1. `docker compose up` (Ollama runs in `infra/docker-compose.yml`) 2. Pull model: `docker exec ai-platform-ollama ollama pull qwen2.5-coder:7b` |
| **Where It Runs** | Anthropic servers (US/EU depending on endpoint) | GitHub/OpenAI servers (US) | Local Docker container (your machine) |

---

## Use Case Recommendation Matrix

| Use Case | Best Choice | Why |
|---|---|---|
| **Production code reviews, complex refactors** | Claude API (Sonnet) | MEDIUM/HIGH complexity needs better reasoning; EU DPA provides legal cover |
| **Quick typo fixes, config tweaks, Speed 1** | Copilot (GitHub) or Local Ollama | Low-complexity work; Copilot has subscription model, Ollama has zero cost |
| **GDPR/regulated environments (finance, health)** | **Local Ollama** | Only zero-risk option; no data leaves machine; automatic Art. 46 compliance |
| **Development with intermittent internet** | **Local Ollama** | Offline-capable; useful for planes, poor connectivity, isolated networks |
| **Prototyping & rapid iteration** | Local Ollama | <1s latency; free; fast feedback loop; ideal for trying multiple approaches |
| **Enterprise AI reference architecture** | Claude Code + Claude API | Per-US model routing (Task Complexity Matrix); cost optimization via dynamic tier assignment |
| **Hybrid setup (best of both)** | Claude Code with LiteLLM proxy | Use Ollama for fast local testing (Phase 1), Claude API for production (Phase 2+); seamless switchover via proxy |

---

## Technical Architecture

### Claude API Flow

```
Your IDE (Claude Code)
  ↓
Anthropic Claude API
  ↓ (requires ANTHROPIC_API_KEY)
Claude Sonnet or Haiku (cloud inference)
  ↓ (results back over HTTPS)
IDE displays completion / explanation
```

**Setup:**
```bash
# In .env
ANTHROPIC_API_KEY=sk-ant-...

# Claude Code uses this automatically
# No LiteLLM proxy needed for Claude API
```

### GitHub Copilot Flow

```
Your IDE (VS Code, JetBrains, etc.)
  ↓ (Copilot extension)
GitHub API
  ↓ (with OAuth token from GitHub account)
GitHub Models or OpenAI backend
  ↓ (results back)
IDE displays suggestion
```

**Setup:**
```bash
# 1. Install Copilot extension
# 2. Sign in with GitHub account
# 3. Copilot subscription required ($10–$20/month or pay-as-you-go)
```

### Local Ollama + Claude Code Flow

```
Your IDE (Claude Code)
  ↓
LiteLLM proxy (localhost:4000, OpenAI-compatible wrapper)
  ↓
Ollama (localhost:11434, Docker container)
  ↓ (all local — zero network latency after first pull)
Qwen2.5-coder or other local model
  ↓ (inference result back)
LiteLLM wraps response in OpenAI format
  ↓
Claude Code displays completion
```

**Setup:**
```bash
# 1. Start all services (Ollama included)
make up

# 2. Pull a model (run once)
docker exec ai-platform-ollama ollama pull qwen2.5-coder:7b

# 3. Configure Claude Code to use LiteLLM proxy
# In Claude Code: set model endpoint to http://localhost:4000
# In .env: ANTHROPIC_BASE_URL=http://localhost:4000

# 4. Verify:
curl http://localhost:11434/api/tags  # list available models
curl http://localhost:4000/health     # check LiteLLM
```

---

## Recommended Model Specs (Ollama)

| Model | Size | Use Case | Hardware | Context Window |
|---|---|---|---|---|
| `qwen2.5-coder:7b` | ~4 GB | Fast code completion, refactors, Speed 1 | CPU / 8 GB RAM (good default) | 32K tokens |
| `qwen2.5-coder:32b` | ~20 GB | Complex multi-file reasoning, full-file understanding | GPU, 24 GB VRAM (H100/A100) | 128K tokens |
| `deepseek-coder-v2:16b` | ~9 GB | Balanced: quality + speed | GPU, 12 GB VRAM (RTX 4090) | 128K tokens |
| `codestral:22b` | ~13 GB | Strong for Python + TypeScript logic, RAG tasks | GPU, 16 GB VRAM (RTX 6000) | 32K tokens |
| `tinyllama:latest` | ~637 MB | Testing, CI/CD, mock completions (very fast) | CPU only | 2K tokens |

**Pull command:**
```bash
docker exec ai-platform-ollama ollama pull qwen2.5-coder:7b
```

**Qwen3 is now available (verified April 2026):**
```bash
docker exec ai-platform-ollama ollama pull qwen3:8b    # 5.2 GB — best CPU option
docker exec ai-platform-ollama ollama pull qwen3:14b   # 9.3 GB — GPU recommended
```

| Model | Size | Best for | Hardware |
|---|---|---|---|
| `qwen3:8b` | ~5.2 GB | Strong reasoning, tool use, coding | CPU / 8 GB RAM |
| `qwen3:14b` | ~9.3 GB | Complex multi-step reasoning | GPU, 12 GB VRAM |
| `qwen3-coder:30b` | ~19 GB | Dedicated coding tasks | GPU, 24 GB VRAM |

Qwen3 supports a `thinking` mode (chain-of-thought) and `tools` tag for function calling. See [ollama.com/library/qwen3](https://ollama.com/library/qwen3) for all variants.

---

## EU AI Act & GDPR Notes

### Claude API
- **GDPR Art. 46 Compliance:** Yes, if you use Anthropic's EU DPA (Standard Contractual Clauses). Consult your Legal team before processing.
- **EU AI Act Art. 14 (Transparency):** Anthropic publishes model cards for Claude Sonnet and Haiku. Use Claude API in "transparent logging" mode.
- **Risk:** Data temporarily leaves your infrastructure (network transit to Anthropic servers).

### GitHub Copilot
- **GDPR Compliance:** GitHub has a DPA; review with your Legal team. Some enterprises require opt-out of training data collection.
- **EU AI Act:** GitHub publishes transparency reports. Recommended for enterprises with GitHub Enterprise agreement.
- **Risk:** Code snippets may be routed through US servers (GitHub/OpenAI).

### Local Ollama (Recommended for Regulated Environments)
- **GDPR Art. 46 Compliance:** **Automatic** — no data transfer = no GDPR Art. 46 required. Data stays on your machine.
- **EU AI Act Art. 9 (Supply Chain Risk):** Zero third-party AI service dependencies. Eliminates supply-chain regulatory exposure.
- **Limitation:** Lower quality for very complex tasks; best used for Phase 1 (prototyping) or Speed 1 (config/typo fixes).
- **Recommended:** Use Local Ollama in early phases; upgrade to Claude API once you move to production (Phase 2+) and have legal clearance.

---

## Decision Tree: Which Setup for Your Project?

```
START: Do you have a production compliance requirement (GDPR, HIPAA, PCI-DSS)?
├─ YES → Use Local Ollama for Phase 1 prototyping
│         For Phase 2+, upgrade to Claude API with EU DPA signed
│         (Consult Legal before processing customer data)
│
├─ NO (internal/startup project) → Do you need best-in-class reasoning?
│   ├─ YES → Claude API (Sonnet) via Claude Code
│   │         Set up per-US model routing (Task Complexity Matrix)
│   │
│   └─ NO → Use Local Ollama OR Copilot
│           Ollama preferred: zero cost, offline-capable, <1s latency
│           Copilot OK: $10–$20/month, easy GitHub integration
```

---

## Performance Benchmarks

**Latency (typical):**
- Claude API: 2–5 seconds (includes network)
- Copilot: 3–10 seconds (GitHub API + inference)
- Local Ollama (qwen2.5-coder:7b on 2020 MacBook): <1 second (cached model)

**Cost per 1,000 requests (assuming average 500 input + 200 output tokens per request):**
- Claude API Sonnet: ~$3.50 (expensive; use for high-value decisions)
- Claude API Haiku: ~$0.75 (cheap; use for config tweaks)
- Copilot: ~$0.10–$0.50 (if subscription cost amortized over 10k requests/month)
- Local Ollama: ~$0.00 (electricity only; assume <$0.01 per 1k requests)

**Quality ranking (0–10 for code reasoning):**
1. Claude Sonnet: 9.5 (reasoning, complex logic, security)
2. GPT-4o (Copilot): 8.5 (code generation, patterns)
3. Claude Haiku: 7.5 (config, simple refactors)
4. Qwen2.5-coder:7b: 7.0 (solid for most code work)
5. Deepseek-coder-v2:16b: 7.5 (good multi-file understanding)

---

## Implementation Checklist

### To use Claude API:
- [ ] Get API key from [console.anthropic.com](https://console.anthropic.com)
- [ ] Add to `.env`: `ANTHROPIC_API_KEY=sk-ant-...`
- [ ] Verify: `curl https://api.anthropic.com/v1/messages` (should authenticate)
- [ ] Legal: Confirm Anthropic EU DPA (if GDPR-regulated)

### To use GitHub Copilot:
- [ ] Install Copilot extension in your IDE
- [ ] Sign in with GitHub account
- [ ] Subscribe to Copilot ($10–$20/month)
- [ ] Verify: Code completions appear in editor

### To use Local Ollama:
- [ ] Start stack: `make up`
- [ ] Wait for Ollama container to be healthy
- [ ] Pull model: `docker exec ai-platform-ollama ollama pull qwen2.5-coder:7b`
- [ ] Verify: `curl http://localhost:11434/api/tags` (returns list of models)
- [ ] Optional: Configure LiteLLM proxy for OpenAI-compatible access

---

## Migration Path (Recommended for Most Projects)

**Phase 1 (Prototyping):** Local Ollama only
- Fast feedback, zero cost, zero compliance friction
- Limitation: quality may not be sufficient for complex tasks

**Phase 2 (MVP):** Claude API + Local Ollama (hybrid)
- Use Claude API (Sonnet) for high-complexity tasks (MEDIUM/HIGH per Task Complexity Matrix)
- Use Local Ollama for low-complexity tasks (Speed 1, config tweaks)
- LiteLLM proxy at localhost:4000 supports both via single OpenAI-compatible interface

**Phase 3+ (Production):** Claude API (with legal review & compliance)
- Full use of Claude API with per-task model routing
- Local Ollama as fallback for offline development
- Ensure EU DPA or equivalent compliance agreement is signed

---

## See Also

- `docs/AI_TOOLS_SETUP.md` — Installation & setup guide for Serena, Ollama, Context7, LiteLLM
- `docs/AI_REFERENCE.md` → Model Routing section → Task Complexity Matrix for per-US model assignment
- `.claude/agents/` — Agent frontmatter specifies `model:` (fixed or `dynamic`)

