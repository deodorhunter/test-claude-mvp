#!/bin/bash
# Framework Impact Measurement Script
#
# Usage: bash benchmark/measure-framework-impact.sh
#
# Captures baseline metrics and outputs a YAML template for framework testing.
# Run BEFORE implementing a US with the framework, collect metrics AFTER.
#
# Output: .feedback/baseline-YYYYMMDD.txt and template-filled-[timestamp].yml

set -e

FRAMEWORK_VERSION="3.0"
FRAMEWORK_COMMIT=$(git rev-parse HEAD 2>/dev/null || echo "unknown")
SCRIPT_TIMESTAMP=$(date -Iseconds)
BASELINE_DATE=$(date +%Y%m%d)
CODEBASE_ROOT=$(git rev-parse --show-toplevel 2>/dev/null || pwd)

echo "╔══════════════════════════════════════════════════════════════╗"
echo "║  Framework Impact Measurement — Baseline Capture            ║"
echo "║  Version: $FRAMEWORK_VERSION                                   ║"
echo "║  Commit:  ${FRAMEWORK_COMMIT:0:8}...                                  ║"
echo "╚══════════════════════════════════════════════════════════════╝"
echo ""

# Ensure .feedback directory exists
mkdir -p .feedback

# Capture codebase metrics
echo "📊 Scanning codebase..."

PYTHON_FILES=$(find . -type f -name '*.py' -not -path './.git/*' -not -path './__pycache__/*' 2>/dev/null | wc -l)
PYTHON_LOC=$(find . -type f -name '*.py' -not -path './.git/*' -not -path './__pycache__/*' 2>/dev/null -exec wc -l {} + | awk '{sum+=$1} END {print sum}' 2>/dev/null || echo "0")
TOTAL_FILES=$(find . -type f -not -path './.git/*' -not -path './.*' 2>/dev/null | wc -l)

GIT_COMMITS_30D=$(git log --oneline --since="30 days ago" 2>/dev/null | wc -l || echo "0")
GIT_LAST_5=$(git log --oneline -5 2>/dev/null | sed 's/^/  /' || echo "  (git not available)")

echo "✅ Codebase snapshot:"
echo "   - Python files: $PYTHON_FILES"
echo "   - Python LOC: $PYTHON_LOC"
echo "   - Total files: $TOTAL_FILES"
echo "   - Git commits (last 30 days): $GIT_COMMITS_30D"
echo ""
echo "📝 Recent commits:"
echo "$GIT_LAST_5"
echo ""

# Save baseline metrics
BASELINE_FILE=".feedback/baseline-$BASELINE_DATE.txt"
cat > "$BASELINE_FILE" << EOF
# Baseline Metrics — Captured $(date)
# Framework Version: $FRAMEWORK_VERSION
# Framework Commit: $FRAMEWORK_COMMIT

## Codebase Snapshot
- Python files: $PYTHON_FILES
- Python lines of code: $PYTHON_LOC
- Total files: $TOTAL_FILES
- Git commits (last 30 days): $GIT_COMMITS_30D

## Recent Activity
\`\`\`
$GIT_LAST_5
\`\`\`

## Environment
- Hostname: $(hostname)
- OS: $(uname -s)
- Git branch: $(git rev-parse --abbrev-ref HEAD 2>/dev/null || echo "unknown")
- Timestamp: $(date)

---

## Pre-Framework Metrics (to be filled in manually)

### US-0 or Last Project
- [ ] Tokens consumed: ________
- [ ] Duration (minutes): ________
- [ ] Test pass rate: ________%
- [ ] Bugs found before deployment: ________
- [ ] QA bouncebacks: ________
- [ ] Agent iterations: ________

### Notes
[Add your observations about the pre-framework development cycle]

EOF

echo "✅ Baseline saved to: $BASELINE_FILE"
echo ""

# Generate feedback template
TEMPLATE_FILE=".feedback/template-filled-$(date +%s)-developer.yml"
cat > "$TEMPLATE_FILE" << 'EOF'
# Framework Testing Feedback — Developer
#
# Filled template from measure-framework-impact.sh
# Edit this file, then submit as PR to .feedback/ directory
# See: docs/TESTING_AND_FEEDBACK.md#submitting-feedback

version: "3.0"
tested_commit: ""  # Fill: git rev-parse HEAD
timestamp: ""  # Fill: date -Iseconds

tester:
  role: developer | tech-lead | architect
  experience: first-time | "2-3 sessions" | experienced
  team_size: solo | "2-5" | "5-20" | enterprise
  project_type: web-backend | ml-infrastructure | data-pipeline | plugin-system | other
  codebase_loc: ~0  # rough lines of code

us_tested:
  id_or_name: "US-001 (e.g., from docs/backlog/)" 
  description: "What was implemented"
  complexity: simple | medium | complex
  domain: backend | frontend | infra | security | testing | documentation

metrics:
  tokens_consumed: ~0  # total tokens (Claude API or Ollama)
  baseline_tokens: ~0  # pre-framework (from .feedback/baseline-*.txt)
  duration_minutes: ~0  # wall-clock time
  iterations_before_success: ~0  # agent runs before AC met
  qa_bouncebacks: 0  # failed judge/QA reviews
  rules_triggered:
    - rule-001-tenant-isolation
    # - rule-NNN-name (list any caught)

findings:
  what_worked_excellently:
    - ""
  
  what_was_unclear:
    - ""
  
  what_didnt_fit:
    - ""
  
  suggestions_for_framework:
    - ""

context:
  codebase_sensitivity: low | medium | high
  regulatory_context: ""  # GDPR, SOC2, HIPAA, etc if any
  team_location: ""  # geographic distribution

contact_email: ""  # optional
EOF

echo "✅ Template generated: $TEMPLATE_FILE"
echo ""
echo "╔══════════════════════════════════════════════════════════════╗"
echo "║  Next Steps                                                  ║"
echo "╚══════════════════════════════════════════════════════════════╝"
echo ""
echo "1. Review baseline metrics:"
echo "   cat $BASELINE_FILE"
echo ""
echo "2. Implement 1–3 US with the framework"
echo ""
echo "3. Record metrics (tokens, time, quality):"
echo "   nano $TEMPLATE_FILE"
echo ""
echo "4. Submit feedback as PR:"
echo "   git checkout -b feedback/framework-test-$(date +%Y%m%d)"
echo "   git add $TEMPLATE_FILE"
echo "   git commit -m \"Framework feedback: tested on [project] — [observations]\""
echo "   git push origin feedback/framework-test-$(date +%Y%m%d)"
echo "   # Open PR with label: framework-feedback"
echo ""
echo "📖 For full guide, see: docs/TESTING_AND_FEEDBACK.md"
echo ""
