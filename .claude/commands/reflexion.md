---
name: reflexion
description: "Phase-gate ritual that extracts 1-3 durable rules from the completed phase's session history and saves them as discrete files in .claude/rules/project/. Run once per phase gate, never per-US. Each saved rule must pass the survival test: would knowing it have prevented at least one circuit-breaker trigger or QA bounce-back?"
version: "1.0.0"
model: claude-haiku-4-5-20251001
destructive: false
output: .claude/rules/project/rule-NNN-*.md  # 0-3 new files per run
speed: 2
trigger: "/reflexion"
parallel_safe: true
cadence: "once per phase gate — NOT after every US"
---

# Command: /reflexion
> Phase-gate ritual: extract durable rules from session history.
> Saves 0–3 rule files to `.claude/rules/project/`.
> **Never run per-US** — only at phase gates. Over-extraction creates rule bloat.
> Invocation: type `/reflexion Phase-N` in the chat.

---

<identity>
Reviews the current session's failures, circuit-breaker triggers, QA bounce-backs, and unexpected blockers, then extracts only the patterns that will genuinely prevent future token waste. Saves them as discrete rule files following the format in `.claude/rules/TEMPLATE.md`.

**Token ROI test (mandatory — enforced below):**
> Each rule saves ~15,000 tokens per avoided debugging loop or ~25,000 tokens per avoided QA bounce-back.
> Each rule costs ~200 tokens per future session it's loaded.
> A rule that is used for 5 sessions before deletion must prevent at least 1 failure in those 5 sessions to break even.
> **If a candidate rule fails this test → discard it.**
</identity>

<workflow>
<step_1>
**Recall Phase Failures (in-context only, no file reads)**

From the conversation history, identify every instance of:
- Circuit breaker triggered (agent hit 2 debugging attempts and stopped)
- QA bounce-back (QA Mode A returned FAIL, US was re-delegated)
- Unexpected blocker (agent stopped because of missing context or wrong assumption)
- Judge FAIL verdict (from `/judge` runs)

List each incident:
`Incident N: [US-NNN] — [agent] — [what failed] — [root cause]`
</step_1>

<step_2>
**Apply the Survival Filter**

For each incident, ask: **"Would a rule have prevented this, and will this type of failure recur?"**

Keep the candidate if:
- The root cause is a repeating pattern (not a one-off typo or env issue)
- The fix is a clear, enforceable constraint (not "be more careful")
- It applies to this project's domain specifically (not already in Part 1 of CLAUDE.md)

Discard the candidate if:
- It's a one-time environment issue (missing env var, wrong Docker tag)
- It's already covered by a CLAUDE.md constraint
- It requires long explanation (>30 lines) — that's a skill, not a rule
- It applies only to the specific US, not to the domain in general
</step_2>

<step_3>
**Check Existing Rules (read ONE file)**

```bash
ls .claude/rules/project/ 2>/dev/null
```

Read the last rule number so you can continue the sequence. Do NOT read all existing rule files.
</step_3>

<step_4>
**Write Rule Files**

For each surviving candidate (maximum 3 per phase gate), write a new file to `.claude/rules/project/` following the format in `.claude/rules/TEMPLATE.md` (minimal frontmatter: id, trigger, updated; XML body: `<constraint>`, `<why>`, `<pattern>`).
</step_4>

<step_5>
**Propose CLAUDE.md Import**

For each saved rule, output the import line the Tech Lead should add to `CLAUDE.md`:

```
Add to CLAUDE.md Part 3:
@.claude/rules/project/rule-NNN-[name].md
```

**Do NOT edit CLAUDE.md yourself.** The Tech Lead decides which rules to activate.
</step_5>

<step_6>
**Promotion Check**

For each new rule, ask: **"Is this pattern universal enough to benefit all 40 org projects?"**

If yes, flag it:
```
⬆️ PROMOTION CANDIDATE: rule-NNN could move to .claude/rules/org/
```
</step_6>

<step_7>
**Report**

```
/reflexion — Phase N Results

Incidents reviewed: N
Rules saved: N (files: rule-NNN-*.md, ...)
Rules discarded: N (reasons: one-time env issue / already covered / etc.)
Promotion candidates: [list or "none"]

CLAUDE.md imports to add:
@.claude/rules/project/rule-NNN-*.md
```
</step_7>
</workflow>

<hard_constraints>
1. Maximum **3 rules per phase gate** — quality over quantity.
2. Never save a rule for a one-time or environment-specific failure.
3. Never save a rule that duplicates Part 1 of `CLAUDE.md`.
4. Never edit `CLAUDE.md` directly — only propose the import lines.
5. Never read existing rule files except for the `ls` to get the next number.
6. If zero incidents meet the survival test → output "0 rules saved — no durable patterns found" and stop.
</hard_constraints>
