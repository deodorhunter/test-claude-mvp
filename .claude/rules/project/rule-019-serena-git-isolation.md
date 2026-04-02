# Rule 019 — Serena-Git Isolation (Worktree Safety)

<constraint>
In git worktrees: (1) configure Serena MCP to ignore .git/ paths in settings.json; (2) chain git checkout+merge in single && command; (3) remove stale .git/index.lock before git operations.
</constraint>

<why>
Serena LSP holds .git/index lock during parallel file reads → "Unable to create index.lock" errors during merge operations in worktrees. Recurred 3× (Phase 2d ×1, Phase 3a ×2). Wastes ~15k tokens per debugging loop.
</why>

<pattern>
✅ **Correct (worktree merge):**
```bash
rm -f .git/index.lock
git checkout branch1 && git merge upstream
```

✅ **Correct (Serena settings.json):**
```json
"serena": {
  "ignored_paths": [".git/", "node_modules/", "__pycache__/"]
}
```

❌ **What to avoid:**
```bash
git checkout branch1
git merge upstream  # Risk: index.lock created between commands
```

❌ **Serena with no ignore filter:**
```json
"serena": { }  // LSP scans .git/ → contention during merge
```
</pattern>
