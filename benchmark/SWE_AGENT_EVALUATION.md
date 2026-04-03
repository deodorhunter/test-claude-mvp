# SWE-Agent Evaluation: Go/No-Go Recommendation

**Date:** 2026-04-03  
**Evaluator:** QA Engineer  
**Status:** Research Complete  

---

## Executive Summary

**Recommendation: CONDITIONAL GO** — mini-swe-agent is technically feasible for Phase 4 implementation, but requires careful architectural consideration given this project's unique constraints (Claude Code governance framework, not traditional software engineering).

- **mini-swe-agent:** Viable. Simple setup, Claude model support via litellm, extensible Python API, MIT license.
- **SWE-bench-lite:** Not applicable. Designed for code-fix benchmarking; governance frameworks don't match SWE-bench problem domain.
- **Custom minimal harness:** Recommended as Phase 4 implementation path — purpose-built for measuring agent task completion quality within this framework.

---

## Part 1: mini-swe-agent Feasibility

### 1.1 What It Is

mini-swe-agent is a lightweight AI software engineering agent (Princeton & Stanford, 2024–2025) designed to be "100x simpler" than full SWE-agent while maintaining strong empirical performance (>74% on SWE-bench verified benchmark). It comprises ~100 lines of core agent code with minimal dependencies.

**Key positioning:** Described as "a hackable tool" rather than a black box, enabling workflow integration and custom task definition beyond SWE-bench.

### 1.2 Setup Requirements

**Installation:**
- Three methods: `pip install mini-swe-agent`, `uvx mini-swe-agent`, or dev clone + `pip install -e .`
- Runtime dependency: bash only (for sandboxed environments)
- Python requirement: ≥3.10 (this project uses 3.11+, compatible)

**First-run configuration:**
- Interactive setup wizard: `mini` prompts for model selection on first run
- Can skip wizard and reconfigure via: `mini-extra config setup`
- Configuration stored in platform-standard location (XDG on Linux/macOS, platformdirs on Windows)

**Time estimate:** <5 minutes for installation and configuration.

### 1.3 Model Provider Support

mini-swe-agent supports **all LLM providers via litellm** (version ≥1.75.5):

| Provider | Support | Status | Notes |
|---|---|---|---|
| Anthropic (Claude) | ✅ Full | Production | Via `anthropic/claude-sonnet-4-5-...` or `anthropic/claude-haiku-...` |
| OpenAI | ✅ Full | Production | `openai/gpt-4`, `openai/gpt-5`, etc. |
| OpenRouter | ✅ Full | Production | Via openrouter integration |
| Portkey | ✅ Full | Production | Via portkey integration |
| Local (Ollama) | ✅ Full | Production | Via `ollama/model-name` or local endpoint override |
| Azure | ✅ Full | Production | Via Azure OpenAI endpoint |

**Recommendation for this project:** Use `anthropic/claude-sonnet-4-6` (aligned with Task Complexity Matrix for MEDIUM/HIGH tasks). Alternative: `anthropic/claude-haiku-4-5-20251001` for quick iteration. Both supported out-of-the-box.

**Model routing:** litellm abstracts provider differences; no vendor lock-in.

### 1.4 Task Definition Format

**Core API (Python):**
```python
from minisweagent.agents.default import DefaultAgent
from minisweagent.models import get_model
from minisweagent.environments.local import LocalEnvironment

agent = DefaultAgent(
    get_model(input_model_name="anthropic/claude-sonnet-4-5-20250929"),
    LocalEnvironment(),
)
agent.run("Your task description as a string")
```

**CLI (REPL-style):**
```bash
mini                          # Interactive mode (task prompted)
mini -t "Your task here"      # Task via -t flag
mini -m anthropic/claude-sonnet-4-6  # Model override
```

**Task input:** Any natural language string describing the goal. Examples from official docs:
- "Implement a Sudoku solver in python in the `sudoku` folder. Make sure the codebase is modular and well tested with pytest."
- "Please run pytest on the current project, discover failing unittests and help me fix them."
- "Help me document & type my codebase by adding short docstrings and type hints."

**Key insight:** Tasks are free-form natural language — **NOT tied to SWE-bench issue JSON format.** This is the inverse of what the backlog feared. mini-swe-agent can accept arbitrary task definitions.

### 1.5 SWE-bench Coupling (Critical Finding)

**Clarity:** mini-swe-agent is **NOT tightly coupled to SWE-bench.**

- mini-swe-agent provides two helper scripts (`benchmark/` directory) to run against SWE-bench problems — but these are *optional utilities*, not core functionality.
- SWE-bench is a separate, standalone benchmark. mini-swe-agent is one of many compatible implementations.
- The agent runs equally well on custom tasks (as demonstrated in CLI examples above) as on SWE-bench issues.

**Verdict:** mini-swe-agent's flexibility exceeds SWE-bench's narrow scope.

### 1.6 Compatibility with Claude Code Governance Framework

**Assessment:** Moderate to Good compatibility with caveats.

**What works well:**
- **Environment abstraction:** LocalEnvironment interacts with local filesystem + bash — compatible with Docker-mounted code directories.
- **Model routing:** litellm provider abstraction matches this project's per-agent model assignment patterns (Haiku vs. Sonnet).
- **Extensibility:** Python API and "hackable" design allow embedding in Speed 2 workflow (e.g., as a specialist sub-agent task runner).
- **History preservation:** mini-swe-agent maintains complete linear message history, enabling debugging/fine-tuning — aligns with rule-010 (context compression) and logging best practices.
- **License:** MIT — no legal/compliance barriers.

**Constraints and incompatibilities:**

1. **Sandbox/multi-tenancy isolation:** mini-swe-agent executes tasks in a single LocalEnvironment (current working directory + filesystem access). For multi-tenant validation (rule-001: tenant isolation), custom wrapper required:
   - Must inject tenant_id into task prompt → agent must filter all DB queries by tenant_id
   - Must prevent agent from escaping sandbox (reading /etc/passwd, etc.)
   - mini-swe-agent has no built-in tenant awareness

   **Mitigation:** Wrapper script or custom Environment subclass that filters filesystem + injects tenant context. Low complexity.

2. **No built-in benchmark metrics:** mini-swe-agent executes tasks but doesn't natively score task completion:
   - No pass/fail verdict on whether the agent solved the task
   - No cost tracking (tokens, wall-clock time)
   - No regression detection between benchmark runs
   
   **Mitigation:** Custom harness wrapper (benchmark runner). Medium complexity.

3. **Tool set is bash-only:** mini-swe-agent uses `subprocess.run()` for all actions. This means:
   - Can't directly call Python functions (e.g., tenant_id validation helper)
   - Can't introspect internal state (e.g., "what URLs did the agent visit?")
   - Works fine for traditional SWE tasks but less ideal for governance/audit scenarios
   
   **Mitigation:** Task prompt engineering to enforce compliance checks. Low complexity.

4. **No built-in session logging:** mini-swe-agent preserves execution history to global config directory but doesn't serialize to JSON or structured logs (unlike oh-my-claudecode's `.omc/sessions/`). 
   
   **Mitigation:** Wrapper captures stdout/stderr + agent messages. Low complexity.

### 1.7 Maintenance Status & Community

- **Team:** Princeton & Stanford (SWE-bench creators) — credible, academic backing
- **Repository activity:** Active development (Feb–Apr 2025 commits visible in README examples)
- **Version:** v2.0 released; v1 deprecated with migration guide provided
- **Issue response:** Typical GitHub issues resolved within weeks
- **Dependencies:** Well-maintained (litellm, pydantic, openai) — no stale deps

**Verdict:** Low risk of abandonment; reasonable to adopt for Phase 4 work.

---

## Part 2: Alternative Evaluations

### 2.1 SWE-bench-lite

**What it is:** A curated subset (~500 problems) of the full SWE-bench (~2,000 problems), designed for easier evaluation and experimentation.

**Applicable to this project?** **No.** Reasons:

1. **Domain mismatch:** SWE-bench-lite evaluates code-fix capability on real GitHub issues (numpy, scikit-learn, Django, etc.). This project is a Claude Code governance framework — not a traditional software product with code bugs and features.
   
2. **Task structure:** SWE-bench assumes: GitHub repo → issue description → expected patch. This project has:
   - Governance documents, rules, skills, MCP servers
   - Acceptance criteria validated via Speed 2 agents, not code diffs
   - Orchestration workflows, not bug-fix workflows

3. **No adaptation path:** Attempting to reframe governance framework tasks as SWE-bench problems would require:
   - Artificially converting "implement a new rule" → "fix a synthetic bug"
   - Losing domain semantics in the translation
   - Creating synthetic issues that don't reflect real governance work

**Verdict:** SWE-bench-lite is a dead-end for this project.

### 2.2 Custom Minimal Harness

**What it is:** Purpose-built benchmark runner tailored to this project's unique needs.

**Proposed structure:**

```
benchmark/
  swe-agent-runner.py          # minimal task executor + scoring
  tasks/
    task-001-create-rule.json  # example: "Create rule-NNN with AC"
    task-002-refactor-agent.json
    ...
  benchmarks/
    (empty initially — populated by runs)
```

**Core components:**
1. **Task definition format** (JSON):
   ```json
   {
     "id": "task-001",
     "title": "Create new governance rule",
     "description": "Write rule-NNN for...",
     "acceptance_criteria": ["AC-1: file exists", "AC-2: format correct"],
     "expected_files": ["benchmark/tasks/task-001-output.md"],
     "scoring": "pass/fail"
   }
   ```

2. **Executor wrapper** (Python):
   - Initialize mini-swe-agent with Anthropic model
   - Inject task definition
   - Capture output files + agent messages
   - Score against acceptance criteria (file existence, content patterns)
   - Log to JSON: task ID, model, tokens, wall-clock time, verdict, pass/fail per AC

3. **Comparison logic**:
   - Baseline run: store initial results
   - Optimization run: re-run same tasks
   - Diff: regression detection, cost deltas

**Effort estimate:**
- Wrapper script: ~150 lines Python
- Task set: 5–10 real governance framework tasks (hand-curated)
- Scoring logic: ~100 lines (file validation + pattern matching)
- **Total:** ~2–3 days implementation time (MEDIUM complexity)

**Advantages:**
- Tailored to this project's governance domain
- Measures what matters: rule creation quality, agent decision-making, cost per task
- No vendor lock-in (unlike SWE-bench)
- Extensible for Phase 4 (API benchmarks, multi-tenant isolation tests)

**Limitations:**
- Not comparable to SWE-bench (different problem domain)
- Benchmark size is manual (5–10 tasks vs. SWE-bench's 500+)
- Scoring requires hand-coded acceptance criteria (not automated test suites)

**Verdict:** Recommended if organization wants to measure governance framework task quality. Viable Phase 4 US.

---

## Part 3: Assessment Matrix

| Criterion | mini-swe-agent | SWE-bench-lite | Custom Harness |
|---|---|---|---|
| **Applicable to governance framework?** | Moderate | No | Yes |
| **Model support (Claude)?** | ✅ Full (litellm) | ✅ Full | ✅ (depends on wrapper) |
| **Setup effort** | Very Low (~5 min) | Medium (~1–2 hrs) | Low (~30 min) |
| **Custom task support** | ✅ Yes (free-form text) | ❌ No (SWE-bench JSON only) | ✅ Yes (project-specific) |
| **Benchmark size** | N/A (executor only) | 500 problems | 5–10 custom tasks |
| **Scoring/metrics** | Manual or custom | Automatic (patch verification) | Manual or custom |
| **Maintenance burden** | Low (upstream) | Low (upstream) | Medium (in-house) |
| **Comparable to industry benchmarks?** | Only SWE-bench | Yes, but mismatched domain | No |
| **Phase 4 effort estimate** | Implementation dependent | 1–2 weeks to adapt | 2–3 days |

---

## Part 4: Recommendation

### 4.1 Go/No-Go Verdict

**CONDITIONAL GO** on mini-swe-agent as the **executor component** of a Phase 4 task-quality benchmarking system.

**Rationale:**
- mini-swe-agent is production-ready, well-maintained, Claude-compatible, and extensible
- Its strength is simplicity and flexibility — perfect for custom task execution
- BUT it requires a **custom harness wrapper** to provide governance-domain-specific scoring, metrics, and multi-tenant isolation validation

### 4.2 Recommended Path: Hybrid Approach

**Phase 4 US (suggested scope):** "Task-Quality Benchmark: mini-swe-agent + Custom Harness"

1. **Use mini-swe-agent as the executor:**
   - Task input: free-form natural language descriptions
   - Model: `anthropic/claude-sonnet-4-6` (MEDIUM/HIGH complexity)
   - Environment: LocalEnvironment (codebase cloned to temp directory per task)

2. **Wrap with custom harness for governance-specific logic:**
   - Task definition format: JSON with acceptance criteria
   - Scoring engine: file existence, pattern matching, rule format validation
   - Metrics: tokens, wall-clock time, pass/fail per criterion
   - Regression detection: store baseline, detect regressions in follow-up runs
   - Multi-tenant validation: inject tenant context in task prompts (not in agent)

3. **Deliverable:** `benchmark/swe-agent-runner.py` + `benchmark/tasks/` directory with 5–10 curated governance tasks

**Phase 4 Effort Estimate:** MEDIUM (2–3 days)
- Day 1: Implement mini-swe-agent wrapper + basic task executor
- Day 2: Implement scoring logic + JSON logging + baseline run
- Day 3: Curate 5–10 real governance tasks, validate scoring, write documentation

### 4.3 Alternative: No Benchmarking (Cost Avoidance)

If Phase 4 prioritizes API/Frontend work over task-quality measurement:
- **Keep current benchmarks:** measure static context size, framework overhead (already optimized, 42% savings achieved)
- **Defer swe-agent work:** not critical for MVP delivery
- **Cost: 0 tokens** in Phase 4

---

## Part 5: Implementation Constraints & Edge Cases

If mini-swe-agent + custom harness is selected for Phase 4:

### 5.1 Tenant Isolation (rule-001)

mini-swe-agent executes tasks in a single sandbox. For multi-tenant benchmarking:

**Requirement:** Validate that agent filters all DB queries by tenant_id.

**Implementation approach:**
- Task prompt explicitly states: "You are working in Tenant 'test-tenant-A'. Filter all database queries by tenant_id."
- Agent executes queries; custom harness intercepts logs/output to verify tenant filtering
- No agent-level sandboxing needed (tenant validation is a task requirement, not a platform guarantee)

**Risk:** If agent ignores tenant context in prompt, it will leak data. This is a task-design risk, not a mini-swe-agent limitation.

### 5.2 Sandbox Escape (Security)

mini-swe-agent uses `subprocess.run()` without sandboxing. Agent could theoretically:
```bash
rm -rf /  # catastrophic
cat /etc/shadow  # data leak
```

**Mitigation:**
- Run benchmark in isolated Docker container (same approach as CI/CD)
- Mount task codebase as read-only (where possible)
- Use filesystem ACLs or seccomp profiles (advanced, optional)

**Acceptable for Phase 4?** Yes. Benchmarking is non-production. Risk is acceptable if isolated from critical systems.

### 5.3 Cost Explosion (Token Runaway)

If a task is poorly specified, agent may loop indefinitely.

**Mitigation:**
- Implement token budget per task: `max_tokens=50000` as a hard stop
- Implement wall-clock timeout: 5–10 minutes per task
- Log warning if token usage exceeds baseline by >2×

---

## Part 6: Rejected Alternatives & Why

### Excluded: Full SWE-agent

Full SWE-agent (predecessor to mini-swe-agent) is more feature-rich but:
- Significantly more complex (1000+ lines vs. 100 lines)
- Not recommended for new projects (mini-swe-agent is the current best practice)
- Overkill for governance framework task execution
- Higher maintenance burden

**Verdict:** mini-swe-agent is the right choice.

### Excluded: SWE-bench-lite

Already covered in Part 2. Domain mismatch is fatal.

### Excluded: GPT-4 Code Interpreter or GitHub Copilot

These are not benchmarking tools — they're interactive editors. Not applicable for automated evaluation.

---

## Summary Table

| Decision | Status | Details |
|---|---|---|
| Adopt mini-swe-agent? | ✅ YES (as executor) | Production-ready, Claude-compatible, extensible |
| Adopt SWE-bench-lite? | ❌ NO | Domain mismatch (code fixes vs. governance) |
| Build custom harness? | ✅ YES (required) | 2–3 day effort; essential for governance-specific scoring |
| Phase 4 work? | ✅ CONDITIONAL YES | If API/Frontend work doesn't preempt Phase 4 timeline |
| Effort tier | MEDIUM | 2–3 days for full implementation |

---

## References

1. **mini-swe-agent Repository:** https://github.com/SWE-agent/mini-swe-agent
   - README: Quick overview, use cases, model setup
   - Quickstart docs: Installation, example prompts, model configuration
   - Python bindings docs: Programmatic API for custom task runners
   - pyproject.toml: Dependency pinning, version constraints

2. **SWE-bench:** https://github.com/SWE-bench/SWE-bench
   - Benchmark design: GitHub issue → code fix verification
   - SWE-bench-lite: Curated subset documentation

3. **This Project's Current Benchmarks:** `benchmark/README.md`
   - Existing token optimization metrics (42% savings achieved)
   - Integration patterns with oh-my-claudecode

4. **AI Reference:** `docs/AI_REFERENCE.md`
   - Model routing (Task Complexity Matrix)
   - Per-agent model assignment (Haiku vs. Sonnet vs. Opus)

---

**Next Step:** If recommendation approved, create Phase 4 US for "Task-Quality Benchmark: mini-swe-agent + Custom Harness" with detailed acceptance criteria, file layout, and task set.

**Date evaluated:** 2026-04-03  
**Evaluator confidence:** HIGH (research verified against official sources)
