---
id: rule-009
trigger: "Before reading any file for structure or symbol location"
updated: "2026-03-31"
---

# Rule 009 — Serena-First Navigation

<constraint>
Before reading any file for structure, use Serena: `get_symbols_overview` (~200 tokens) → `find_symbol` (~50 tokens) → targeted `read_file` range. Full `Read`/`cat` ONLY for `<file>` XML injection.
</constraint>

<why>
Full-file reads cost ~2,000 tokens each. Serena overviews give the same structural info at 10% cost.
</why>
