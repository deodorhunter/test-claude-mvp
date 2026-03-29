---
type: human-guide
version: "1.1.0"
audience: developers
updated: "2026-03-29"
related: [CLAUDE.md, .claude/commands/, .claude/agents/]
---

# AI Developer Playbook
> How to use Claude effectively in this repository.
> For AI governance rules, see `CLAUDE.md`. For command macros, see `.claude/commands/`.

---

## Why This Exists

AI coding assistants can write excellent code — but they can also burn through tokens doing useless work: exploring the entire codebase before touching a file, printing 5,000-line install logs, retrying a broken test 12 times, or rewriting a 300-line file to change 3 lines.

This playbook standardizes how developers in this org interact with Claude so that:
- Token costs stay predictable and low (target: < 10,000 tokens per task)
- Context windows don't get polluted with noise
- Claude's outputs are focused, testable, and reviewable

We call the problem **Agentic Bloat**: the tendency of autonomous AI loops to expand their context window with irrelevant information until they're spending most compute processing their own previous mistakes.

---

## The Two Speeds

### 🐇 Speed 1 — Copilot Mode (you drive)

Use this for: bug fixes, small refactors, config changes, adding a field to a model, quick doc updates.

**The contract:**
- You attach the specific file(s) the change lives in
- Claude reads **only** those files
- Claude makes a targeted edit and shows you what changed
- You review, approve, commit — done

**How to invoke Speed 1:**
Just open a chat, attach the file, and describe the task. Claude will operate in Speed 1 automatically when the request is scoped to specific attached files.

```
✅ Good Speed 1 prompts:
"Fix the KeyError on line 47 of quota_service.py — file attached"
"The health endpoint returns 500 when Redis is down. See main.py"
"Add `updated_at` to the Tenant model — see models.py attached"

❌ Bad Speed 1 prompts (these will trigger Speed 2 or bloat):
"Look through the codebase and find all the places we check quota"
"How does the plugin system work? Explain it"
"Refactor the entire auth layer"
```

**Speed 1 model:** Always Haiku. It's fast, cheap, and sufficient for targeted edits.

---

### 🏗️ Speed 2 — Orchestrator Mode (Claude drives)

Use this for: new features, new abstractions, security work, architectural changes, anything that needs a User Story.

**The contract:**
- You describe the goal at a high level
- Claude plans, creates User Stories, and delegates to specialized sub-agents
- You review and approve each US before Claude executes
- Claude collects results, runs smoke tests, triggers QA validation
- You approve the merge

**How to invoke Speed 2:**
Start a new chat with no files attached. Describe the phase/feature goal. Claude will enter Orchestrator mode automatically and ask for approval before doing anything.

```
✅ Good Speed 2 prompts:
"We're starting Phase 2a. Plan the plugin system according to the spec."
"US-010 is approved. Proceed with delegation."
"Phase Gate 1 is approved. Start Phase 2."

❌ Bad Speed 2 prompts:
"Just implement the plugin manager" (skips planning + approval)
"Do US-010 and US-011 at the same time without showing me a plan"
```

**Speed 2 models:** Dynamic — Claude selects per-US based on the Task Complexity Matrix in `CLAUDE.md`.

---

## The Commands Library

Commands are reusable macro prompts stored in `.claude/commands/`. They tell Claude exactly what to do in common situations, without you having to write the instructions from scratch each time.

To use a command, type it in the chat (Claude Code supports `/command-name` notation):

| Command | What it does | When to use |
|---|---|---|
| `/init-ai-reference` | Scans the repo once and writes `docs/AI_REFERENCE.md` | When setting up this repo for the first time, or after major stack changes |
| `/handoff` | Runs `git diff`, parses it, appends summary to `docs/ARCHITECTURE_STATE.md` | After a US is merged, to keep the state file current |
| `/compress-state` | Summarizes the current chat into `docs/.temp_context.md` and prompts `/clear` | When you've been working in the same session for > 30 min and token usage is climbing |

### How Commands Work

Each `.claude/commands/X.md` file contains a structured prompt that:
1. Tells Claude exactly what tools to use (and in what order)
2. Constrains the output to a specific format
3. Uses append-only file operations where state persistence is needed

You can inspect any command file to see exactly what it will do before running it.

---

## Token Optimization — Why We Care

### The Cost of Agentic Bloat (concrete examples)

| Anti-pattern | Token cost | Equivalent |
|---|---|---|
| Exploring the repo with `find .` before starting | +3,000–8,000 input tokens | Re-reading a 30-page spec every task |
| Unsilenced `npm install` output piped into context | +2,000–5,000 output tokens | 10 extra Claude responses |
| Rewriting a 400-line file to change 2 lines | +1,600 output tokens | Writing 4 new functions from scratch |
| Debugging loop — 8 attempts at a broken test | +20,000 tokens | Full implementation of a medium feature |
| DocWriter reading all raw source files instead of git diff | +6,000–15,000 tokens | Full spec read × 2 |

At scale (40 projects × 10 developers × 5 tasks/day), the difference between disciplined and undisciplined prompting is **tens of millions of tokens per month**.

### The 4 Rules (summary — full details in `CLAUDE.md`)

1. **No Exploration** — Claude works only with files you give it
2. **Quiet Outputs** — All shell commands use silent flags
3. **Targeted Edits** — `Edit` tool or `sed`, never full rewrites
4. **Circuit Breaker** — Max 2 debug attempts, then escalate

---

## Prompt Dos and Don'ts

### ✅ DOs — Reducing Cost and Hallucination

| Do | Why |
|---|---|
| **Attach the specific files** for the task | Eliminates exploration tokens entirely |
| **Give Claude the error message verbatim** | Prevents hallucinated bug theories |
| **Reference exact function/class names** | Prevents Claude searching for the wrong thing |
| **Specify the acceptance criteria** | Claude stops when done, not when bored |
| **Use `/clear` after each major task** | Prevents context cross-contamination between tasks |
| **Use `/compress-state` before a long session** | Keeps the working context lean |
| **Ask for a plan first, code second** | Catches misunderstandings before tokens are spent on wrong code |
| **Tell Claude which test to run** | Prevents it inventing test commands |

### ❌ DON'Ts — Token and Hallucination Traps

| Don't | Why it's bad |
|---|---|
| **"Look at the codebase and…"** | Triggers full exploration — 5,000+ wasted tokens |
| **"Refactor everything to use X"** | Open-ended scope → runaway agent → context overflow |
| **"Try to fix it"** | No acceptance criteria → debugging loop guaranteed |
| **Continuing the same chat for 3+ hours** | Context fills with stale information → quality degrades |
| **Asking Claude to "remember" from a previous session** | Claude has no memory between sessions |
| **"Write tests for the whole module"** | Unbounded scope → 40,000 token QA run |
| **Pasting entire files when only a section is relevant** | Wastes input tokens on irrelevant context |
| **Skipping `/init-ai-reference` on a new repo** | Claude guesses ports, commands, paths → hallucinations |

---

## Context Management Workflow

```
Start of session
    │
    ├─ Speed 1? → Attach specific files → do task → /clear
    │
    └─ Speed 2? → Confirm docs/AI_REFERENCE.md exists
                 → Claude reads BACKLOG.md + workflow.md
                 → Plan + approval
                 → Delegate US (with file injection)
                 → Review result
                 → /handoff
                 → /clear (after phase gate or complex US)
```

**Rule of thumb:** If your chat history is longer than 20 messages, run `/compress-state` and then `/clear`. The next session will pick up from `docs/.temp_context.md`.

---

## Setting Up a New Project from This Template

To port this framework to one of the 40 org projects:

1. Copy `.claude/`, `CLAUDE.md`, and `AI_PLAYBOOK.md` to the new repo
2. Run `/init-ai-reference` to auto-generate `docs/AI_REFERENCE.md` for that repo's stack
3. Create `docs/ARCHITECTURE_STATE.md` with the scaffold from the existing file
4. Create `docs/backlog/BACKLOG.md` with the initial US list
5. Adapt `.claude/agents/*.md` files to match that project's domain (use `TEMPLATE.md` as the base)
6. Done — the rest of the framework operates identically

The only project-specific configuration is `docs/AI_REFERENCE.md` and the agent file domains. Everything else is universal.
