# AI Tools Setup Guide

> Local AI tooling for this project: Serena (code navigation), Codebase Memory (persistent indexing), Context7 (library docs), Ollama + Qwen2.5 (local inference), and LiteLLM (OpenAI-compatible proxy).
> Both VS Code Copilot and Claude Code users are first-class citizens for all tools in this guide.

---

## 1. Serena — Semantic Code Navigation

<https://github.com/oraios/serena>

Serena is an MCP server that exposes LSP-level intelligence (symbols, definitions, diagnostics) to AI assistants. It replaces full-file reads with targeted symbol lookups — ~200 tokens per file instead of ~2,000.

### Some tools it provides

| Tool | Cost | Use case |
|---|---|---|
| `get_symbols_overview` | ~200 tokens | List all classes/functions in a file before reading it |
| `find_symbol` | ~50 tokens | Locate a specific function/class — returns file + line |
| `get_diagnostics` | ~100 tokens | Check type errors in a file before editing |
| `read_file` (range) | proportional | Read a targeted line range after locating the symbol |

**Language scope:** Serena is configured for Python and TypeScript in this project (`.serena/project.yml`). Markdown, YAML, JSON, and Dockerfile files return errors — use Read/Grep for those.

You can update your Serena configuration in `.serena/project.yml` or `.serena/project.local.yml`, follow official docs.

> Serena also provides memories: these memories are in Markdown format and can be manually edited.
>
>Relying on manual redaction, or redaction by Claude with onboarding initialization or through  `/update-memories` skill can be detrimental, especially in context pressured sessions.
>
>*Too many memories also mean too many tokens to load in context window.*
>
>**Do not use Serena memories in large projects/codebases, best suited to small projects/codebases**.

### Prerequisites

```bash
# uv must be installed (used by uvx to run Serena without global install)
curl -LsSf [https://astral.sh/uv/install.sh](https://astral.sh/uv/install.sh) | sh
```

### Setup and Execution

Serena is defined in the project's ``.claude/settings.json or .mcp.json`` file.
To run it via Docker (recommended for  isolation), use the ai-tools compose stack:

```bash
# Start sandboxed Serena (HTTP/SSE mode, exposed on localhost:9121)
make up-ai-tools
# or: 
docker compose -f infra/docker-compose.ai-tools.yml up -d serena
```

## 2. Codebase Memory (CBM) — Persistent Indexing and UICodebase

<https://github.com/DeusData/codebase-memory-mcp>

Memory (codebase-memory-mcp) provides persistent, cross-session codebase indexing backed by a SQLite database.

It includes a real-time, interactive 3D graph UI to visualize your codebase architecture.

![real-time, interactive 3D graph UI to visualize your codebase architecture](https://raw.githubusercontent.com/DeusData/codebase-memory-mcp/main/docs/graph-ui-screenshot.png)

### Architecture

CBM runs in a **Daemonized Mode**:

- **The Daemon**: CBM runs 24/7 as a background service in docker-compose.ai-tools.yml. This keeps the graph UI continuously available at <http://localhost:9749> and maintains an open connection to the SQLite cache volume.
- **The Worker**: When Claude Code needs to use CBM, it executes `infra/scripts/cbm-mcp.sh` (via `.claude/settings.json or .mcp.json`). This script uses docker exec to instantly spawn a lightweight, headless worker process inside the running daemon container, securely sharing the cache and eliminating container spin-up time.

### Setup

CBM is pre-configured in your `.claude/settings.json or .mcp.json` and runs via Docker Compose.

```bash
# Ensure the CBM daemon is running
make up-ai-tools
# or: 
docker compose -f infra/docker-compose.ai-tools.yml up -d codebase-memory-mcp
```

### Activation

CBM is gated by an environment variable to prevent conflicts. You must set `NAVIGATION_BACKEND` before starting your AI session:

```bash
# Activate CBM exclusively
export NAVIGATION_BACKEND=cbm
claude

# Or activate both CBM and Serena simultaneously
export NAVIGATION_BACKEND=both
claude
```

Or update your settings

```json
"codebase-memory-mcp": {
      "type": "stdio",
      "command": "bash",
      "args": ["infra/scripts/cbm-mcp.sh"],
      "env": {
        "NAVIGATION_BACKEND": ("both"|"serena"|"cbm")
      }
    }
```

**UI Access**: Once the daemon is running, open <http://localhost:9749> in your browser to view the interactive codebase graph.

## 3. Context7 — Library Documentation

<https://github.com/upstash/context7>

Context7 is a cloud MCP service that returns up-to-date library documentation into the AI context. It is operated by Upstash (US-based).

### What it does

When you ask about a library (e.g., "how does SQLAlchemy's select work?"), Context7 fetches the current official docs and injects them into the AI context — no hallucinated APIs, no stale version information.

No code is passed to the MCP server, the only available tools are:

- `resolve-library-id`: Resolves a general library name into a Context7-compatible library ID.
  - `query (required)`: The user's question or task (used to rank results by relevance)
  - `libraryName (required)`: The name of the library to search for
- `query-docs`: Retrieves documentation for a library using a Context7-compatible library ID.
  - `libraryId (required)`: Exact Context7-compatible library ID (e.g., /mongodb/docs, /vercel/next.js)
  - `query (required)`: The question or task to get relevant documentation for

> You do not need an API key if you keep requests under the FREE tier limits.
You can set the API key in your shell profile if you have/need one:
>
>```bash
># Add to your shell profile or .env >(never commit)
>export CONTEXT7_API_KEY=your_key_here
>```

## 3. Local AI Models — Ollama + Qwen2.5 (or any other local Ollama model)

Running models locally satisfies GDPR Art. 46 automatically — no data leaves the machine.
This is the preferred setup for coding tasks on sensitive codebases.

> Feel free to experiment with other models through Ollama (Qwen3, Gemma, Deepseek, GLM), referenced models were just tested for smoke tests purposes!
>
>Use local Ollama installation for big models, Docker is CPU constrained and has no access to your GPU!

### Setup

Ollama runs as part of the main Docker Compose stack (`infra/docker-compose.yml`, port `11434`). You do not need a separate Ollama install.

>If you want to use Ollama locally, follow Ollama docs and check network connection through docker and `litellm` is correct.
>
> **Or ignore `litellm` and use Ollama support for [Anthropic Messages API](https://docs.ollama.com/api/anthropic-compatibility) and [Claude Code](https://docs.ollama.com/api/anthropic-compatibility#using-with-claude-code)**


```bash
# Pull recommended coding models (run once)
docker exec ai-platform-ollama ollama pull qwen2.5-coder:7b

# For very nerdy experiments:
# 1. Add a custom model definition, see infra/docker/Modelfile.qwen-1.5b-64k (expanded context window in custom Ollama model definition)
docker cp infra/docker/Modelfile.qwen-1.5b-64k ai-platform-ollama:/tmp/Modelfile.qwen-1.5b-64k      
# 2. Load it in Ollama docker
docker exec ai-platform-ollama ollama create qwen-claude-1.5b -f /tmp/Modelfile.qwen-1.5b-64k 
```

>Procedure is similar if running local Ollama
>
>```bash
>ollama create qwen-claude-7b -f infra/docker/Modelfile.qwen-7b-64k 
>```

### Using local models with Claude Code via LiteLLM

LiteLLM acts as an OpenAI-compatible proxy in front of Ollama, translating Anthropic-formatted API calls. Claude Code connects to LiteLLM instead of the Anthropic API.

```bash
# Start LiteLLM (from the ai-tools compose)
make up-ai-tools

# Point Claude Code at local models

export ANTHROPIC_BASE_URL=<http://localhost:4000>
export ANTHROPIC_API_KEY=unused  # LiteLLM does not require this but the SDK checks for it

# Start Claude Code — it will use Ollama via LiteLLM

claude
```

### TODO: Gemini cli integration

[Someone else could experiment and document it!]

## 4. Full Sandboxed Stack (Docker)

`infra/docker-compose.ai-tools.yml` provides a Docker-isolated AI tooling stack: Serena + CBM + Ollama + LiteLLM.

```bash
# Start everything
make up-ai-tools

# Services started

# serena              → localhost:9121  (HTTP/SSE mode, workspace read-only mount)
# codebase-memory-mcp → localhost:9749  (UI Daemon) / headless workers via `exec`
# ollama-tools        → localhost:11435 (local inference, shared model weights)
# litellm             → localhost:4000  (OpenAI-compatible proxy for Ollama)
```

This compose file is separate from `infra/docker-compose.yml` — AI dev tools are not platform services and must not share the application network.

## 5. Quick Reference

> Pre-session check: Run `make up-ai-tools` before any session to ensure Serena and CBM daemons are running and listening.

| Tool | Config / Activation | Endpoint / Notes |
|---|---|---|
| Serena | Defined in ``.claude/settings.json or .mcp.json`` — Docker service (serena). Activate via AI tools compose. | SSE `http://localhost:9121/sse` — Python & TypeScript LSP (targeted symbol lookups) |
| Codebase Memory (CBM) | Defined in ``.claude/settings.json or .mcp.json`` — Docker daemon (codebase-memory-mcp). Activate by setting `NAVIGATION_BACKEND=cbm` or `both`. | UI `http://localhost:9749` (graph UI); headless worker via `infra/scripts/cbm-mcp.sh` (stdio) |
| Context7 | `context7`.claude/settings.json or .mcp.json`` — requires `CONTEXT7_API_KEY` in environment. | Cloud docs service `mcp.context7.com` — stdio (npx) for up-to-date library documentation |
| Ollama / Local Models | Runs in the main AI compose stack (pull models into the Ollama container). | Local inference (Ollama) — use via LiteLLM proxy; example port: 11435 |
| LiteLLM (OpenAI proxy) | Part of AI tools compose. Configure `ANTHROPIC_BASE_URL` to point to the proxy. | OpenAI-compatible proxy that forwards to local models (e.g., `http://localhost:4000`) |
