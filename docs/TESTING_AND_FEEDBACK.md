# Testing & Feedback — Evaluate This Framework on Your Codebase

> Version 3.0 · For developers, security engineers, legal/DPO teams, and framework maintainers
> **Goal:** Test the framework on your project, measure its impact, try experiments, and share findings to improve the framework.

---

## 1. Getting Started with Framework Testing

### Prerequisites

- Claude Code or Copilot Chat set up (see [`docs/AI_TOOLS_SETUP.md`](AI_TOOLS_SETUP.md))
- A codebase to test on (your own project or the template)
- 30–60 minutes per US for baseline + framework implementation comparison
- Willingness to collect metrics (token count, wall-clock time, bugs caught)

### Baseline Measurement Checklist

Before implementing any US with the framework, capture these metrics **without the framework** to establish a baseline:

**Pre-Framework Baseline (US-0 or last project):**
- [ ] Tokens consumed
- [ ] Wall-clock time from brief to acceptance
- [ ] Test pass rate (% of tests passing)
- [ ] Bugs found during review or deployment
- [ ] Number of security/pattern violations you caught manually
- [ ] Iteration count (how many tries before AC met?)
- [ ] QA bouncebacks (failed reviews)

**Run this now:**
```bash
# Capture codebase context
bash benchmark/measure-framework-impact.sh | tee .feedback/baseline-$(date +%Y%m%d).txt
```

### First Implementation: With Framework

Now implement the same or similar US **with the framework**:
1. Read `docs/AI_REFERENCE.md` and `.claude/agents/orchestrator.md`
2. Assign to appropriate agent (backend-dev, security-engineer, etc.)
3. Run sessions with the framework
4. Capture the same metrics

**Compare:**
- Token delta: (with framework) vs (baseline)
- Time delta
- Quality delta (bugs caught, rule violations prevented)

---

## 2. Measuring Performance — Four Dimensions

The framework impacts your development cycle across:

### Dimension 1: Token Economy (Primary Metric)

**What to measure:**
- Tokens consumed per US (Claude API call cost + Ollama inference tokens)
- Cost reduction: `(baseline - actual) / baseline × 100%`
- Cost by phase (Phase 1 planning, Phase 2 implementation, Phase 3 QA)

**Why it matters:** Token cost is directly comparable across projects of any size. 20% savings on a 10k-token project = 2k tokens; on a 500k-token project = 100k tokens.

**What to record:**
```yaml
metrics:
  tokens_consumed: 45000
  baseline_tokens: 60000
  savings_percent: 25  # (60k - 45k) / 60k = 25%
  cost_by_phase:
    phase_1_planning: 5000
    phase_2_implementation: 35000
    phase_3_qa: 5000
```

### Dimension 2: Quality (Security + Correctness)

**What to measure:**
- Test pass rate (% of tests passing on first run)
- Bugs caught during review (before merge)
- Rule violations detected by framework (e.g., cross-tenant queries caught before deployment)

**Why it matters:** Tokens are cheap; bugs are expensive. Did the framework catch issues you would have missed?

**What to record:**
```yaml
metrics:
  test_pass_rate: "100%"  # or "95% (1 flaky test)"
  bugs_caught_in_review:
    - "Cross-tenant query in quota service (rule-001)"
    - "Missing Alembic migration before model change (rule-002)"
  rules_triggered:
    - rule-001-tenant-isolation
    - rule-009-serena-first-navigation
```

### Dimension 3: Speed (Wall-Clock Time)

**What to measure:**
- Total time from brief to acceptance (including agent iteration)
- Number of iterations before agent's code was accepted
- Time spent debugging vs implementing

**Why it matters:** A 20% token reduction is hollow if implementation takes 3× longer. Does the framework accelerate or decelerate your work?

**What to record:**
```yaml
metrics:
  duration_minutes: 120  # total wall-clock time
  iterations_before_success: 3  # how many agent runs?
  qa_bouncebacks: 1  # failed reviews that required iteration
  breakdown:
    reading_us_and_context: 15  # min
    implementation: 85  # min
    qa_and_revision: 20  # min
```

### Dimension 4: Governance Health

**What to measure:**
- Rules that helped you (prevented bugs, caught patterns)
- Rules that were noisy or unclear
- Quality of the feedback loop (did `/reflexion` produce actionable insights?)

**Why it matters:** A framework is only valuable if its rules are right for your domain. "Too strict" = developers ignore it; "too loose" = bugs slip through.

**What to record:**
```yaml
metrics:
  rules_that_helped:
    - rule-001-tenant-isolation: "Caught real bug"
    - rule-009-serena-navigation: "Saved 8k tokens"
  rules_that_were_noisy:
    - rule-003: "Flagged three false positives"
  feedback_loop_quality: "Good — /reflexion produced 2 actionable insights"
```

---

## 3. What to Try Next — Suggested Experiments

After baseline + one US, try these structured experiments to understand framework trade-offs:

### Experiment 1: Local Ollama vs Cloud Claude
**Question:** How much do local models cost vs cloud?

**Setup:**
- Implement US-A with local Ollama (qwen2.5-coder:7b)
- Implement US-B (similar complexity) with Claude API
- Compare: token consumption, quality, iteration count

**Decision guide:** Local = satisfies GDPR Art. 46 (no transfer), slower inference; Cloud = faster, needs DPA

###Experiment 2: Serena Navigation Adoption
**Question:** Do symbol-first lookups really save tokens?

**Setup:**
- Implement one US with Serena tooling (get_symbols_overview, find_symbol, get_diagnostics)
- Implement similar US without Serena (full file reads)
- Compare: tokens, iteration count, agent clarity

**Metric:** Serena should save 10–15% tokens on symbol-heavy refactors.

### Experiment 3: Custom Domain Rules
**Question:** Can I extend rule-001 (tenant isolation) for my business logic?

**Setup:**
- Identify a pattern in your codebase (e.g., "all database writes require audit logging")
- Write a rule extending rule-001 structure
- Have agents enforce it for one sprint
- Measure: bugs caught, developer friction

### Experiment 4: Multi-Tenant Edge Cases
**Question:** Does the framework catch cross-tenant data leaks?

**Setup:**
- Add a second tenant to your test data
- Implement features that *could* leak data (quota checks, report generation)
- Try to construct a cross-tenant query
- Did the framework + rule-001 prevent it?

### Experiment 5: CI/CD Pre-Flight Hooks
**Question:** Can we automate phase-gate checks in GitHub Actions?

**Setup:**
- Port `.claude/hooks/pre-prompt.sh` checks to GitHub Actions
- Verify AI_REFERENCE.md exists before CI runs
- Scan for `.omc/` directory (EU AI Act compliance check)
- Block merge if checks fail

### Experiment 6: Long-Running Projects (Multi-Phase)
**Question:** Do token costs compound over time, or scale well?

**Setup:**
- Track SESSION_COSTS.md across Phase 1 → 2 → 3
- Measure: total tokens, cost per US, phase-to-phase trends
- Do governance rules take longer to apply or faster?

### Experiment 7: Mixed Speed 1 + Speed 2 Workload
**Question:** How much overhead does the orchestrator add vs ad-hoc fixes?

**Setup:**
- Day 1–3: Speed 1 fixes (quick targeted edits, no US structure)
- Day 4–5: Speed 2 US (full planning, agent delegation, phase gates)
- Compare: cost, friction, iteration count

---

## 4. Submitting Feedback

Feedback is how this framework improves. Every submission — positive, negative, uncertain — helps decide what to fix next.

### For Developers / Technical Teams

**Use template:** [`.feedback/template-developer.yml`](../.feedback/template-developer.yml)

**What to include:**
- Framework version + commit hash you tested against
- One US you implemented (complexity, domain, tokens, time)
- What worked excellently
- What was unclear
- What didn't fit your use case
- Suggestions for improvement

**How to submit:**
```bash
# Copy template, fill it out
cp .feedback/template-developer.yml .feedback/20260331T143000-developer-initials.yml

# Edit with your findings
nano .feedback/20260331T143000-developer-initials.yml

# Create PR
git checkout -b feedback/framework-test-US-001
git add .feedback/20260331T143000-developer-initials.yml
git commit -m "Framework feedback: US-001 (qwen2.5-coder) — token savings confirmed"
git push origin feedback/framework-test-US-001

# Open PR with label: framework-feedback
```

### For Security / Compliance Experts

**Use template:** [`.feedback/template-security.yml`](../.feedback/template-security.yml)

**What to include:**
- Rule enforcement mechanisms (what's enforced, what's advisory)
- Governance gaps you discovered
- EU AI Act / GDPR article-by-article alignment
- Third-party integration risks (Claude DPA, Context7 Upstash, Ollama)
- Supply chain audit (version pinning, image SHAs)

**How to submit:**
```bash
# Confidential or public
# If confidential: → GitHub Discussions (label: security-review)
# If public: → PR as developer feedback
```

### For Legal / DPO / Leadership

**Use template:** [`.feedback/template-legal.yml`](../.feedback/template-legal.yml)

**What to include:**
- EU AI Act article-by-article assessment
- GDPR Art. 46 compliance (local vs cloud vs third-party)
- Liability framework (penalties, mitigations)
- Third-party DPA status (must-have vs nice-to-have)
- Deployment readiness checklist

**How to submit:**
```bash
# Confidential only (contains legal assessment, not for public PR)
# → GitHub Discussions (label: legal-review, restricted to admins)
# OR → Email maintainer directly (do not commit legal analysis to git)
```

---

## 5. FAQ — Testing & Feedback

### Q: When is the framework "working well"?

**A:** Working well across indicators:
- ✅ Token savings > 15% vs baseline (for coding tasks)
- ✅ Quality doesn't drop (test pass rate >= baseline, no new bugs)
- ✅ No rule churn (rules don't flip flop week to week)
- ✅ Dev friction is low (rules feel reasonable, not compliance theater)

### Q: How do I know I'm using the framework correctly?

**A:** Check these:
1. **Rule-001 (tenant isolation)**: Every DB query on tenant-owned data has `.where(Model.tenant_id == tenant_id)`
2. **Targeted edits**: You're not rewriting files to change 3 lines
3. **Circuit breaker**: You stopped after 2 debug attempts, not 10
4. **No autonomous exploration**: You're not running `find`, `glob`, or reading files the framework didn't suggest
5. **Phase gates**: Multi-phase US go through judge → QA → review, not straight to merge

### Q: What counts as a rule vs what belongs in a skill?

**A:** Rule = "any agent could violate this, cost of missing it is high (breach, rule bounce-back)"  
Skill = "only one agent type needs this, only at a specific moment"

**Rule example:** rule-001 (tenant isolation) — any backend agent writing a query could miss the tenant_id filter → breach

**Skill example:** writing-audience.md (how to write for DPOs) — only doc-writer uses this, only in Mode B

### Q: My use case doesn't fit any existing role or rule.

**A:** Start with:
1. Pick the closest existing agent (e.g., `backend-dev` for API work)
2. Write a custom skill extending that agent (see `.claude/skills/TEMPLATE.md`)
3. Run it for one sprint, collect feedback
4. Submit findings + whether the skill became a rule or stays situational

---

## 6. How Feedback Drives Framework Improvements

**Feedback Loop:**

```
User feedback (.feedback/<date>-<type>.yml)
  ↓
Maintainer pattern-match ("3 testers report rule-X too noisy")
  ↓
Run /reflexion to extract durable rules
  ↓
Update rule-0NN or create new skill
  ↓
Document in DEVLOG.md
  ↓
Next framework release includes refinement
```

**Real examples (from this project's testing):**
- Finding: "rule-009 priority unclear" (3 reports) → rewrote with concrete examples
- Finding: "Serena saved 8–12k tokens" (5 reports) → made Serena standard in all agents
- Finding: "Phase gates too heavy for Speed 1" (4 reports) → Speed 1 scoping examples expanded in copilot-instructions and AI_PLAYBOOK.md

---

## Next Steps

1. **Run baseline:** `bash benchmark/measure-framework-impact.sh`
2. **Implement 1 US:** With framework, measure metrics
3. **Try 1 experiment:** Pick one from Section 3
4. **Fill feedback template:** Developer or security or legal (pick one)
5. **Submit PR or Discussion:** Share findings with maintainers

Questions? Open a Discussion or email the maintainers.

Happy testing! 🚀
