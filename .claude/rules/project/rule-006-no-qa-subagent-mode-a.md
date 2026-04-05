<metadata>
  id: rule-006
  updated: "2026-04-03"
</metadata>

# Rule 006 — No QA Sub-Agent for Mode A Validation

<constraint>
NEVER spawn a QA Engineer sub-agent for Mode A validation. Run tests directly using Write tool + docker exec pattern. Max 2 attempts (Rule 4).
</constraint>

<why>
QA sub-agents cannot access Bash/docker exec in sub-agent context — they silently fail or produce unverifiable output, requiring a full re-run by the Tech Lead anyway.
</why>

<pattern>
```
✅ Write test to backend/tests/.temp_qa_us_NNN.py → docker exec -e PYTHONPATH=/app api python3 tests/.temp_qa_us_NNN.py
❌ Agent(subagent_type="qa-engineer", prompt="validate US-NNN acceptance criteria")
```
</pattern>
