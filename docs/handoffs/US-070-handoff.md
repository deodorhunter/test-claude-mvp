# US-070 Handoff — Accuracy Scoring: Structured /judge Output + Trend Log

**Date:** 2026-04-03 | **Status:** PARTIAL (3/4 components implemented)

## What Was Built

Accuracy tracking infrastructure for /judge command:

1. **`benchmark/report-accuracy.sh`** — New bash script that reads `benchmark/accuracy-log.jsonl` and prints:
   - Per-phase summary table (US count, AC totals, AC pass rate, bouncebacks)
   - Per-agent breakdown table (pass rate, pass/fail status flags)
   - Overall totals (US pass rate, AC pass rate)

2. **`Makefile` target `benchmark-accuracy`** — Added to `.PHONY` list and implemented as:
   ```makefile
   benchmark-accuracy:
       @bash benchmark/report-accuracy.sh
   ```

3. **`benchmark/README.md` — Accuracy Tracking section** — Comprehensive documentation appended:
   - What it tracks (AC pass/fail per US, per-phase trends, per-agent scores)
   - How it's populated (via /judge append-only)
   - JSON line format specification (7 fields: date, us, agent, ac_total, ac_pass, ac_fail, verdict, phase)
   - Sample report output showing phase summary + per-agent breakdown
   - Data location: `benchmark/accuracy-log.jsonl` (gitignored ✓)

4. **`benchmark/accuracy-log.jsonl` gitignore** — Verified already present from US-069

## Missing Component

**`judge.md` accuracy_logging section** — Unable to append due to permission restrictions on Write/Edit/Bash tools. This section instructs the judge command to:
- Count PASS/FAIL/UNCLEAR verdicts
- Extract phase from `docs/backlog/BACKLOG.md`
- Extract agent from US frontmatter
- Append JSON line with format: `{"date":"YYYY-MM-DD","us":"US-NNN","agent":"type","ac_total":N,"ac_pass":N,"ac_fail":N,"verdict":"pass|fail","phase":"Xd"}`

The section is complete and documented in the user story — needs manual addition to judge.md.

## Integration Points

1. **Judge command** → writes to `benchmark/accuracy-log.jsonl` (one line per US run)
2. **Make target** → `make benchmark-accuracy` reads the log and prints formatted output
3. **CI/reporting** → Can be integrated into phase gate reporting via `make benchmark-accuracy`

## File Ownership

| File | Owner | Status |
|---|---|---|
| `benchmark/report-accuracy.sh` | Tech Lead / Doc Writer | Created ✅ |
| `Makefile` (benchmark-accuracy target) | Tech Lead | Updated ✅ |
| `benchmark/README.md` | Tech Lead / Doc Writer | Updated ✅ |
| `.claude/commands/judge.md` | Judge command maintainer | ⚠️ Needs manual update |
| `benchmark/accuracy-log.jsonl` | Judge command (append-only) | Ready (gitignore set) ✅ |

## Residual Risks

| Risk | Severity | Mitigation |
|---|---|---|
| Judge.md not updated | MEDIUM | Must be done manually before /judge can log. Without it, accuracy-log.jsonl stays empty. |
| JSON parsing in report script | LOW | Script uses jq safely with error handling (suppress stderr if jq unavailable). Graceful fallback if file empty. |
| Phase lookup implementation | LOW | Judge needs to extract phase via `grep` on BACKLOG.md — straightforward text search, low complexity. |

## Manual Test Instructions

Assuming judge.md is updated with accuracy_logging section:

```bash
# 1. Create a test US and run /judge on it
cd /Users/martina/personal-projects/test-claude-mvp
/judge US-070

# 2. Verify JSON was appended to accuracy-log.jsonl
tail -1 benchmark/accuracy-log.jsonl
# Expected: {"date":"2026-04-03","us":"US-070","agent":"...","ac_total":N,...}

# 3. Run the accuracy report
make benchmark-accuracy

# Expected output:
# ## Accuracy Report — Phase Summary
# | Phase | US Count | ACs Total | ACs Pass | Pass Rate | Bouncebacks |
# ...
# ## Per-Agent Breakdown
# ...
```

## Automated Tests

The report script includes basic validation:
- Checks if `benchmark/accuracy-log.jsonl` exists and is non-empty
- Uses `jq` safely (exits cleanly if jq not available)
- Graceful error message if log is empty ("Run /judge US-NNN after implementations")

No unit tests added (bash script for reporting only, driven by manual make target).

## Notes

- `benchmark/accuracy-log.jsonl` is already gitignored per US-069
- Report uses standard jq aggregation (group_by phase/agent, sum totals)
- "Bouncebacks" column = entries with verdict="fail" (re-implementation required)
- UNCLEAR AC counts toward ac_total but NOT ac_pass (conservative scoring)
