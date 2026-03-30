# Rule 005 — No Multiline Python in bash -c

## Constraint
Never embed multi-line Python inside `docker exec ... python3 -c "..."`. Write script to temp file with `Write` tool, execute via `docker exec ... python3 /path/script.py`, then delete.

## Why
Shell quoting + Python indentation inside bash -c breaks reliably. Temp file pattern is quoting-safe and debuggable.

## Pattern
```bash
# Write tool → backend/tests/.temp_qa.py, then:
docker exec -e PYTHONPATH=/app ai-platform-api python3 tests/.temp_qa.py && rm backend/tests/.temp_qa.py
```
