# US-070 Manual Update Instructions

## Required Edit: `.claude/commands/judge.md`

**Location:** Append after line 55 (after `</output_format>` closing tag)

**Content to append:**

```xml
<accuracy_logging>
After printing the verdict table, append one JSON line per US evaluated to `benchmark/accuracy-log.jsonl` using bash.
Count PASS verdicts as ac_pass, FAIL as ac_fail, UNCLEAR counts toward ac_total but not ac_pass or ac_fail.

Determine the current phase from `docs/backlog/BACKLOG.md` (grep for the US number to find which phase section it appears in).
Determine the agent from the US file `docs/backlog/US-NNN.md` frontmatter **Agent:** field.

Command to append (run once per US evaluated):
```bash
echo '{"date":"'"$(date +%Y-%m-%d)"'","us":"US-NNN","agent":"agent-type","ac_total":N,"ac_pass":N,"ac_fail":N,"verdict":"pass|fail","phase":"Xd"}' >> benchmark/accuracy-log.jsonl
```

Rules:
- verdict is "pass" if Overall=PASS, "fail" if Overall=FAIL
- append-only — never overwrite or delete entries
- if benchmark/accuracy-log.jsonl does not exist, bash >> creates it automatically
- skip logging if US number cannot be determined from arguments
</accuracy_logging>
```

## Why This Is Needed

The `/judge` command needs to log its verdicts to `benchmark/accuracy-log.jsonl` so that `make benchmark-accuracy` can generate accuracy reports. Without this section:

1. Judge runs but produces no log entries
2. Accuracy log stays empty
3. `make benchmark-accuracy` shows "Accuracy log not found or empty"

## What The Judge Command Should Do With This Section

After printing its verdict table (existing behavior), the judge command implementation should:

1. Parse the US number from arguments (`/judge US-NNN`)
2. Count PASS/FAIL/UNCLEAR from the verdict table
3. Lookup the current phase by grepping `docs/backlog/BACKLOG.md` for the US number
4. Lookup the agent type from the US frontmatter `docs/backlog/US-NNN.md`
5. Execute the append command with actual values filled in
6. Result: One JSON line appended to `benchmark/accuracy-log.jsonl`

## Test Verification (After Update)

```bash
# After updating judge.md with this section:
cd /Users/martina/personal-projects/test-claude-mvp

# Run the judge on any US (example: US-070)
/judge US-070

# Verify JSON was appended
tail -1 benchmark/accuracy-log.jsonl
# Should output a valid JSON object like:
# {"date":"2026-04-03","us":"US-070","agent":"backend-dev","ac_total":5,"ac_pass":5,"ac_fail":0,"verdict":"pass","phase":"3d"}

# Run the accuracy report
make benchmark-accuracy

# Should now show per-phase and per-agent accuracy tables
```

## JSON Format Reference

Each line in `benchmark/accuracy-log.jsonl` must be a valid JSON object with these fields:

| Field | Type | Example | Notes |
|---|---|---|---|
| `date` | string | `"2026-04-03"` | YYYY-MM-DD format |
| `us` | string | `"US-070"` | User Story identifier |
| `agent` | string | `"backend-dev"` | Agent type from US frontmatter |
| `ac_total` | number | `5` | Total AC count for the US |
| `ac_pass` | number | `5` | PASS verdicts (UNCLEAR does NOT count) |
| `ac_fail` | number | `0` | FAIL verdicts |
| `verdict` | string | `"pass"` or `"fail"` | "pass" if Overall=PASS, "fail" if Overall=FAIL |
| `phase` | string | `"3d"` | Phase ID from BACKLOG.md |

**Scoring rules:**
- UNCLEAR AC counts toward `ac_total` but NOT toward `ac_pass` (conservative)
- verdict is "pass" only if Overall is PASS (all AC met or UNCLEAR)
- verdict is "fail" if Overall is FAIL (one or more AC explicitly failed)
