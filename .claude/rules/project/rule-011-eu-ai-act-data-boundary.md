# Rule 011 — EU AI Act Data Boundary

## Constraint
AI processing uses only configured providers (Ollama local, Claude API with EU DPA). No code/schema/session data transmitted to third-party services (Discord, Slack, plugin marketplaces, session sync). Phase-gate checkpoints mandatory — no autonomous bypass. Session replay never committed or synced.

## Why
GDPR Art. 46 (data transfers), EU AI Act Art. 14 (human oversight), Art. 9 (supply chain risk). Non-compliance = regulatory exposure.

## Permitted from oh-my-claudecode
Critic agent, evidence-driven verification, notepad wisdom (local only), atomic changes, authoring/review separation.

## Rejected
Plugin marketplace, external notifications, `.omc/` session sync, multi-provider routing, autopilot mode.
