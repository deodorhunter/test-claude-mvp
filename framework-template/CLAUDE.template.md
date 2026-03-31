---
type: human-guide
# ADAPT: update version and stack name
version: "1.0.0"
audience: developers
---

# CLAUDE.md — Global Physics
> These rules are ALWAYS ACTIVE for every agent, every session, no exceptions.

---

## Token Optimization (5 Core Rules)

**Rule 1: NO AUTONOMOUS EXPLORATION**  
Forbidden: `ls`, `find`, `tree`, `glob`, `du` to discover files. Forbidden: reading files not explicitly provided.  
Exception: read at most ONCE for a completely missing critical import dependency.

**Rule 2: SILENCE VERBOSE OUTPUTS**
```bash
pip install -q >/dev/null 2>&1
pytest -q --tb=short
npm install --silent 2>/dev/null
docker build -q .
alembic upgrade head 2>&1 | tail -5
```

**Rule 3: TARGETED EDITING ONLY**  
Use the Edit tool for precise replacements. Never rewrite a file when modifying <30% of its content.

**Rule 4: CIRCUIT BREAKER — MAX 2 DEBUGGING ATTEMPTS**
```
Attempt 1 → ONE targeted fix → re-run
Attempt 2 → ONE targeted fix → re-run
Attempt 3 → STOP. Report: (a) exact error ≤10 lines, (b) what was tried, (c) root cause hypothesis.
```

**Rule 5: BULK READING OVER SERIAL READING**  
Use `cat file1 file2 file3` in one call rather than three sequential reads.

---

## Primary References

| Reference | Purpose |
|---|---|
| `docs/AI_REFERENCE.md` | Stack, ports, make targets, test commands. Read at every Speed 2 session start. |
| `docs/backlog/BACKLOG.md` | Current phase and US status |
| `.claude/agents/orchestrator.md` | Speed 2 workflow, delegation, phase gates |

---

## Active Project Rules

<!-- ADAPT: add your project-specific rules here using @path/to/rule.md imports -->
<!-- Universal rules (no project-specific content): none to import by default -->
<!-- Write your first rule using .claude/rules/TEMPLATE.md, then import it here -->

---

## Hard Rules

1. No self-approval: never mark a US done without running the smoke test
2. No code exfiltration: all AI processing stays within configured providers (local/EU only)
3. No delegation without acceptance criteria
4. Human checkpoints are mandatory at each phase gate — no autonomous advancement
