# AI Tools Setup Guide

> Local AI tooling for this project: Serena (code navigation), Context7 (library docs), Ollama + Qwen2.5 (local inference), and LiteLLM (OpenAI-compatible proxy).
> Both VS Code Copilot and Claude Code users are first-class citizens for all tools in this guide.

---

## 1. Serena — Semantic Code Navigation

Serena is an MCP server that exposes LSP-level intelligence (symbols, definitions, diagnostics) to AI assistants. It replaces full-file reads with targeted symbol lookups — ~200 tokens per file instead of ~2,000.

### What it provides

| Tool | Cost | Use case |
|---|---|---|
| `get_symbols_overview` | ~200 tokens | List all classes/functions in a file before reading it |
| `find_symbol` | ~50 tokens | Locate a specific function/class — returns file + line |
| `get_diagnostics` | ~100 tokens | Check type errors in a file before editing |
| `read_file` (range) | proportional | Read a targeted line range after locating the symbol |

### Prerequisites

```bash
# uv must be installed (used by uvx to run Serena without global install)
curl -LsSf https://astral.sh/uv/install.sh | sh
```

### Option A — Local (personal / trusted repos)

VS Code: already configured in `.vscode/mcp.json` — no action needed.

For Claude Code:
```bash
claude mcp add serena -- uvx --from git+https://github.com/oraios/serena serena start-mcp-server --context ide --project .
```

To make it available in all Claude Code sessions (global):
```bash
claude mcp add serena --scope user -- uvx --from git+https://github.com/oraios/serena serena start-mcp-server --context ide --project .
```

### Option B — Docker (enterprise / regulated environments)

Use `infra/docker-compose.ai-tools.yml` for sandboxed Serena. This is **required** when the project codebase contains sensitive schemas or credentials that must not be accessible to an uncontrolled process.

```bash
# Start sandboxed Serena (HTTP/SSE mode, exposed on localhost:9121)
make up-ai-tools
# or: docker compose -f infra/docker-compose.ai-tools.yml up -d serena
```

For VS Code (HTTP mode), Serena must be configured as a remote SSE server instead of stdio. VS Code MCP HTTP support is experimental — check the MCP extension settings.

For Claude Code (HTTP mode):
```bash
claude mcp add serena --transport http --url http://localhost:9121/sse
```

### Security analysis

| Threat | Local install | Docker install |
|---|---|---|
| Serena reads workspace files | Both modes have equal access — workspace is always mounted | Docker adds process isolation but identical file access |
| Serena network access | Unrestricted (local process) | Restricted by `networks: internal` in compose |
| Process escape | Not sandboxed | Contained in Docker namespace |
| Supply chain (Serena package) | uvx pulls latest from GitHub | Same source, but isolated from host Python env |

**Decision guide:**
- Personal project or developer workstation with no regulated data: local install (Option A) is sufficient.
- Enterprise project, regulated data, or PCI/GDPR production context: use Docker (Option B) with the `internal` network flag set.

---

## 2. Context7 — Library Documentation

Context7 is a cloud MCP service that returns up-to-date library documentation into the AI context. It is operated by Upstash (US-based).

### What it does

When you ask about a library (e.g., "how does SQLAlchemy's `select` work?"), Context7 fetches the current official docs and injects them into the AI context — no hallucinated APIs, no stale version information.

### Data flow (important for GDPR Art. 46)

```
Your query: "How does async select work in SQLAlchemy?"
↓
context7-mcp sends to mcp.context7.com:
  - library identifier: "sqlalchemy"
  - query string: "async select"
  ← NEVER: source code, file paths, schema, session content, tenant data
↓
Response: current docs excerpt
```

**GDPR Art. 46 [Verified — EUR-Lex](https://eur-lex.europa.eu/legal-content/EN/TXT/?uri=CELEX:32016R0679) position:** Context7 receives only library names and query strings — this is equivalent to a documentation site search. Before production use, obtain Upstash's Data Processing Agreement (DPA) or verify Standard Contractual Clauses (SCCs) are in place.

### Setup

VS Code: already configured in `.vscode/mcp.json`. Set the API key:
```bash
# Add to your shell profile or .env (never commit)
export CONTEXT7_API_KEY=your_key_here
```

For Claude Code:
```bash
claude mcp add context7 --env CONTEXT7_API_KEY=your_key -- npx -y @upstash/context7-mcp@latest
```

### Why Context7 is NOT Dockerized

Context7 is a cloud client — it makes HTTPS calls to `mcp.context7.com`. Dockerizing the stdio bridge provides zero security benefit because the outbound call still reaches the same endpoint. The policy control for Context7 is at the GDPR Art. 46 DPA level (Upstash agreement), not at the process isolation level.

---

## 3. Local AI Models — Ollama + Qwen2.5

Running models locally satisfies GDPR Art. 46 automatically — no data leaves the machine. This is the preferred setup for coding tasks on sensitive codebases.

### Ollama is already in the project

Ollama runs as part of the main Docker Compose stack (`infra/docker-compose.yml`, port 11434). You do not need a separate Ollama install.

```bash
# Pull recommended coding models (run once)
docker exec ai-platform-ollama ollama pull qwen2.5-coder:7b
docker exec ai-platform-ollama ollama pull deepseek-coder-v2:16b
```

### Recommended models

| Model | Size | Best for | Hardware |
|---|---|---|---|
| `qwen3:8b` | ~5.2 GB | **Recommended** — reasoning + tool use + coding | CPU / 8 GB RAM |
| `qwen3:14b` | ~9.3 GB | Complex multi-step reasoning | GPU, 12 GB VRAM |
| `qwen2.5-coder:7b` | ~4 GB | Fast code completion, refactors (stable) | CPU / 8 GB RAM |
| `qwen2.5-coder:32b` | ~20 GB | Complex multi-file reasoning | GPU, 24 GB VRAM |
| `deepseek-coder-v2:16b` | ~9 GB | Balanced: quality + speed | GPU, 12 GB VRAM |
| `codestral:22b` | ~13 GB | Strong for Python + TypeScript | GPU, 16 GB VRAM |

### Using local models with Claude Code via LiteLLM

LiteLLM acts as an OpenAI-compatible proxy in front of Ollama, translating Anthropic-formatted API calls. Claude Code connects to LiteLLM instead of the Anthropic API.

```bash
# Start LiteLLM (from the ai-tools compose)
make up-ai-tools
# or: docker compose -f infra/docker-compose.ai-tools.yml up -d litellm

# Point Claude Code at local models
export ANTHROPIC_BASE_URL=http://localhost:4000
export ANTHROPIC_API_KEY=unused  # LiteLLM does not require this but the SDK checks for it

# Start Claude Code — it will use Ollama via LiteLLM
claude
```

LiteLLM config is in `infra/docker-compose.ai-tools.yml` under the `litellm` service. The default model mapping routes `claude-*` requests to `qwen2.5-coder:7b`.

### EU AI Act compliance advantage

Using local Ollama models satisfies:
- **GDPR Art. 46** [Verified — EUR-Lex](https://eur-lex.europa.eu/legal-content/EN/TXT/?uri=CELEX:32016R0679): no international data transfer — no DPA or SCCs required
- **EU AI Act Art. 10** [Verified — EUR-Lex](https://eur-lex.europa.eu/legal-content/EN/TXT/?uri=CELEX:32024R1689): your training data governance is not affected
- **EU AI Act Art. 9** [Verified — EUR-Lex](https://eur-lex.europa.eu/legal-content/EN/TXT/?uri=CELEX:32024R1689): supply chain risk reduced — model weights on your hardware

### Measuring Local vs Cloud Performance

For a data-driven comparison (token costs, quality, compliance implications), see:  
[`docs/TESTING_AND_FEEDBACK.md#experiment-1-local-ollama-vs-cloud-claude`](../docs/TESTING_AND_FEEDBACK.md#experiment-1-local-ollama-vs-cloud-claude)

Quick decision matrix:

| Factor | Local Ollama (qwen2.5-coder:7b) | Claude API |
|---|---|---|
| GDPR Art. 46 compliance | ✅ Automatic (no transfer) | ⚠ Requires Anthropic DPA |
| Speed of inference | ✅ Depends on hardware (CPU/GPU) | ✅ Fast cloud inference |
| Code quality | ⚠ Good for refactors, moderate complexity | ✅ Excellent on complex reasoning |
| Cost at scale (1000s of tokens) | ✅ Lower per-token cost | ⚠ Higher per-token cost |
| Deployment risk | ✅ Zero compliance risk | ⚠ DPA validation required |

---

## 4. Full Sandboxed Stack (Docker)

`infra/docker-compose.ai-tools.yml` provides a Docker-isolated AI tooling stack: Serena + Ollama + LiteLLM.

```bash
# Start everything
make up-ai-tools

# Services started:
#   serena       → localhost:9121  (HTTP/SSE mode, workspace read-only mount)
#   ollama-tools → localhost:11435 (local inference, shared model weights volume)
#   litellm      → localhost:4000  (OpenAI-compatible proxy for Ollama)
```

This compose file is separate from `infra/docker-compose.yml` — AI dev tools are not platform services and must not share the application network.

### Environment variables (add to `.env`, never commit values)

```
CONTEXT7_API_KEY=          # Required for Context7 MCP
OLLAMA_MODEL=qwen2.5-coder:7b  # Default model for LiteLLM routing
ANTHROPIC_BASE_URL=http://localhost:4000  # Point Claude Code at LiteLLM
```

---

## 5. Quick Reference

| Tool | VS Code config | Claude Code config |
|---|---|---|
| Serena (local) | `.vscode/mcp.json` (done) | `claude mcp add serena -- uvx ...` |
| Serena (Docker) | Remote SSE in MCP settings | `claude mcp add serena --transport http --url http://localhost:9121/sse` |
| Context7 | `.vscode/mcp.json` (done) | `claude mcp add context7 --env CONTEXT7_API_KEY=... -- npx ...` |
| Ollama | Runs in Docker via `make up` | Same |
| LiteLLM | `infra/docker-compose.ai-tools.yml` | `ANTHROPIC_BASE_URL=http://localhost:4000` |
