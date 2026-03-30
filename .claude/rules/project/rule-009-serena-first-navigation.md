# Rule 009 — Serena-First Navigation

## Constraint
Before reading any file for structure, use Serena: `get_symbols_overview` (~200 tokens) → `find_symbol` (~50 tokens) → targeted `read_file` range. Full `Read`/`cat` ONLY for `<file>` XML injection.

## Why
Full-file reads cost ~2,000 tokens each. Serena overviews give the same structural info at 10% cost.
