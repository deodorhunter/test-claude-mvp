---
id: rule-015
trigger: "When any agent executes code, installs packages, or runs tests"
updated: "2026-04-01"
---

# Rule 015 — Host Execution Air-Gap

<constraint>
ALL code execution, package installation, and test runs MUST go through `docker exec <container> <cmd>`. Agents are strictly forbidden from running the following natively on the host: `pip`, `pip3`, `python`, `python3`, `node`, `npm`, `npx`, `pytest`, `alembic` (outside of Make targets). No exceptions.
</constraint>

<why>
Native host execution risks reading host credentials (`~/.aws`, `~/.env`, SSH keys), polluting the host Python/Node environment, and bypassing the containerised security boundary — violating EU AI Act Art. 14 (human oversight) and exposing secrets to model context.
</why>

<pattern>
```bash
# ✅ Correct — all execution through docker exec
docker exec -e PYTHONPATH=/app ai-platform-api pytest -q --tb=short tests/

# ✅ Correct — make targets are permitted (they internally docker exec)
make migrate
make test

# ❌ Forbidden — native host execution
pytest tests/
python -m pytest
pip install some-package
alembic upgrade head   # run directly on host
```
</pattern>
