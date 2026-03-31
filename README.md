# AI Governance Framework — MVP

---

## Why this exists

Every team that starts using AI assistants makes the same discovery: the tools are powerful, but the first few months are chaotic. Sessions balloon in cost with no explanation. Different team members get different answers to the same question. Something an AI changed last Tuesday quietly broke something else. There's no record of why a decision was made.

This project is a tested answer to that problem. It's a governance layer — a set of structured rules — that sits between your team and the AI tools you're already using. The AI doesn't get a blank slate every session. It gets a bounded role, a defined scope, and a checklist. You get predictable costs, auditable decisions, and a process you can actually explain to a client or a regulator.

The framework was built on a real FastAPI/PostgreSQL platform, benchmarked against an unstructured baseline, and iterated over multiple development phases. It's open for inspection at every level.

---

## If you're evaluating this for your organisation

- **Cost reduction — per-task**: unstructured AI sessions routinely consume 200,000+ API units on a single task. This framework keeps the same task under 10,000 — up to a 20× reduction, enforced by bounded agent roles and a two-attempt circuit breaker.
- **Cost reduction — session overhead**: auto-loaded governance context was reduced from 60,764 to 32,936 bytes (−46%) by scoping rules so they load only when relevant to the files being changed. Source: [`benchmark/results/optimized-v2.txt`](benchmark/results/optimized-v2.txt).
- **Auditability**: every AI action is tied to a named requirement with acceptance criteria. The output is a reviewable artifact, not a black box. Your security or compliance team can read it.
- **EU AI Act and GDPR compliance controls** (Regulation (EU) 2024/1689 [[Verified — EUR-Lex](https://eur-lex.europa.eu/legal-content/EN/TXT/?uri=CELEX:32024R1689)] and Regulation (EU) 2016/679 [[Verified — EUR-Lex](https://eur-lex.europa.eu/legal-content/EN/TXT/?uri=CELEX:32016R0679)]): your code stays inside your infrastructure; no source code or session data is routed to unapproved third-party services; every autonomous action requires a human checkpoint; append-only audit logs are maintained throughout. Article-by-article control map: [FRAMEWORK_README.md — EU AI Act Compliance Map](docs/FRAMEWORK_README.md#eu-ai-act-compliance-map).
- **Adoption in 30 minutes**: the governance layer is a set of text files with no runtime dependencies. Copy `framework-template/` to your repo, fill in the marked placeholders, and you're running.

Detailed benchmark results: [`benchmark/results/`](benchmark/results/).  
Full compliance map (per article, with evidence pointers): [`docs/FRAMEWORK_README.md`](docs/FRAMEWORK_README.md).

---

## If you're a developer using this repo

Start with [`AI_PLAYBOOK.md`](AI_PLAYBOOK.md) — it explains how to use the AI tools in this specific codebase: which commands to run, how to scope a task, what the agents do, and how to avoid the common failure modes.

For the internals of the governance layer itself — how rules, skills, and commands work, what the agents are responsible for, how the benchmark was run — see [`docs/FRAMEWORK_README.md`](docs/FRAMEWORK_README.md).

---

## Quick start (adopting for a new project)

1. Copy `framework-template/` to your repo root
2. Follow `framework-template/HOW-TO-ADOPT.md` — the 30-minute checklist walks you through every required edit
3. Replace all `# ADAPT` markers in the template files with your project's stack, paths, and team conventions

That's it. No scripts to run, no dependencies to install. The framework is plain text.
