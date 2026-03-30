---
id: rule-011
title: "EU AI Act Data Boundary — No Code Exfiltration"
layer: project
phase_discovered: "Architecture Review 2026-03-30"
us_discovered: "Framework Refactor"
trigger: "When any agent or tool integration could transmit code, schema, or session data outside the project directory"
cost_if_ignored: "GDPR/EU AI Act violation — potential regulatory fines, data breach, and loss of enterprise trust"
updated: "2026-03-30"
---

# Rule 011 — EU AI Act Data Boundary

## Constraint

All AI processing must use only the configured providers (Ollama local, Claude API with EU data handling agreement). No code, schema excerpts, session content, or audit logs may be transmitted to third-party notification services (Discord, Slack, Telegram), unreviewed plugin marketplaces, or external session sync services. All phase-gate checkpoints are mandatory — no autonomous mode that bypasses human approval. Session replay files must never be committed to version control or synced externally.

## Context

oh-my-claudecode and similar frameworks offer useful cognitive patterns (critic agent, evidence-driven verification, notepad wisdom) but also include infra-level features that are incompatible with EU AI Act enterprise requirements:

1. **GDPR Art. 46 (Data Transfers)**: Automatic multi-provider routing (Gemini, Codex) transfers proprietary code to non-EEA providers without explicit lawful basis. Each provider requires its own data processing agreement.

2. **EU AI Act Art. 10 (Data Governance)**: Session replay JSONL files and notepad systems capturing code snippets violate storage limitation principles (GDPR Art. 5(1)(e)) if synced externally or included in training datasets.

3. **EU AI Act Art. 12 (Logging)**: High-risk AI systems require tamper-proof logs. Mutable local files (`.omc/state/*.jsonl`) do not satisfy this requirement. Our framework uses append-only PostgreSQL audit tables.

4. **EU AI Act Art. 14 (Human Oversight)**: Autopilot/autonomous modes that run complete lifecycles without human checkpoints violate mandatory oversight requirements for high-risk AI use on private codebases and databases.

5. **Supply Chain Risk (Art. 9 Risk Management)**: Public plugin marketplaces introduce unreviewed code execution — a direct risk management failure for enterprise contexts.

This framework's `.omc/` detection hook, mandatory phase-gate stops, and controlled provider list are compliance controls, not optional features.

## Examples

✅ Correct (compliant patterns):
```python
# Processing stays within configured boundary
providers = ["ollama_local", "claude_api_eu"]  # explicit allowlist
# Phase gate stops require human approval before continuing
# Audit logs: append-only PostgreSQL, never mutable files
# Session notes: local docs/.session-notes.md, gitignored
```

❌ Avoid (non-compliant patterns):
```python
# Auto-routing to uncontrolled providers
route_to_cheapest_provider(query)  # could select Gemini, Codex without consent

# External notification with code context
send_to_slack(webhook_url, f"Completed: {source_code_snippet}")

# Autonomous mode bypassing human checkpoints
autopilot.run(task, skip_checkpoints=True)  # EU AI Act Art. 14 violation
```

## What This Rule Permits from oh-my-claudecode

✅ Pull: critic agent, evidence-driven verification, notepad wisdom (local only), atomic changes philosophy, authoring/review separation — all stateless, local, zero exfiltration risk.

❌ Reject: plugin marketplace, external notifications, `.omc/` session sync, multi-provider auto-routing, autopilot mode without checkpoints.
