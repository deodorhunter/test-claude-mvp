---
id: rule-013
paths: "infra/**, infra/docker/**"
trigger: "When any agent writes or modifies a Dockerfile"
updated: "2026-03-31"
---

# Rule 013 — Docker COPY No Shell Operators

<constraint>
COPY instructions in a Dockerfile must never include shell operators (||, &&, 2>/dev/null, || true); use RUN cp for any conditional file operation.
</constraint>

<why>
COPY is a DAG layer instruction, not a shell command — shell operators are passed literally to the layer processor and silently break the build (incident: Phase 2d, Dockerfile.plone-mcp).
</why>

<pattern>
```
✅ RUN cp src/optional-file dest/ 2>/dev/null || true
❌ COPY src/optional-file dest/ 2>/dev/null || true
```
</pattern>
