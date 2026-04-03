← [Back to DEVLOG index](../DEVLOG.md)

## Entry 17 — YAML Frontmatter Schema Compliance — 2026-04-03

**Trigger**: Claude Code rule and skill files had non-standard YAML frontmatter keys that Claude Code's schema does not recognise (`id`, `updated`, `version`, `type`, `trigger`). The risk: unrecognised keys are silently ignored at load time, meaning rule triggers embedded in custom keys were never evaluated.

**Migration applied** (14 rule files, 6 skill files):

*Rule files* — allowed keys: `description`, `paths`. Every rule had custom `id` and `updated` keys at frontmatter level. These were stripped from the YAML and injected as a `<metadata>` XML block at the top of the Markdown body, preserving the information without confusing the schema parser. Rules without a `paths` key received `paths: "**"`. Rule-013 had `paths` as a comma-separated string (`"infra/**, infra/docker/**"`) — normalised to a proper YAML list. Rule-019 had no frontmatter at all — a compliant `description` + `paths` header was synthesised from the rule title.

*Skill files* — allowed keys: `name`, `description`, `argument-hint`, `compatibility`, `disable-model-invocation`, `license`, `metadata`, `user-invocable`. The custom keys `version`, `type`, `trigger`, and `updated` were moved into a nested `metadata:` dictionary, keeping them accessible to any tooling that reads the body block while not polluting the schema-validated top level.

**Files modified**:
- `.claude/rules/project/rule-001-tenant-isolation.md`
- `.claude/rules/project/rule-002-migration-before-model.md`
- `.claude/rules/project/rule-004-ai-reference-check-every-session.md`
- `.claude/rules/project/rule-005-docwriter-no-multiline-bash.md`
- `.claude/rules/project/rule-007-phase-gate-proceed-means-gate-steps.md`
- `.claude/rules/project/rule-008-pre-edit-read-docker-baked-files.md`
- `.claude/rules/project/rule-009-serena-first-navigation.md`
- `.claude/rules/project/rule-011-eu-ai-act-data-boundary.md`
- `.claude/rules/project/rule-012-mcp-trust-boundary.md`
- `.claude/rules/project/rule-013-docker-copy-no-shell-ops.md` *(paths string → list)*
- `.claude/rules/project/rule-014-registry-enforcement-opt-in.md`
- `.claude/rules/project/rule-018-backlog-refinement.md`
- `.claude/rules/project/rule-019-serena-git-isolation.md` *(no frontmatter → added)*
- `.claude/rules/TEMPLATE.md`
- `.claude/skills/TEMPLATE.md`
- `.claude/skills/speed2-workflow.md`
- `.claude/skills/ralplan-deliberation.md`
- `.claude/skills/writing-audience.md`
- `.claude/skills/speed2-delegation/SKILL.md`
- `.claude/skills/backlog-refinement/SKILL.md`

**Lesson**: Schema-invisible metadata is invisible governance. If the runtime can't see the trigger, the rule doesn't fire. Custom keys belong in the body, not the header.
