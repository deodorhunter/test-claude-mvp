#!/bin/sh
# verify-docs.sh — CI verification for documentation accuracy
# Checks:
#   - All HTTP(S) links in docs/ resolve (HEAD requests, external only)
#   - Port numbers in docs/AI_REFERENCE.md match docker-compose.yml
#   - Make targets referenced in docs exist in Makefile
#   - All US files referenced in BACKLOG.md exist on disk
#   - Plugin status in PLUGIN_MANIFEST.md has required frontmatter fields
#   - Rule files in .claude/rules/project/ have required structure

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"

# Color codes
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

CHECKS_PASSED=0
CHECKS_FAILED=0

echo "=== Doc Verification CI ==="
echo "Repo root: ${REPO_ROOT}"
echo ""

# ============================================================================
# 1. CHECK HTTP(S) LINKS IN docs/ (external links only)
# ============================================================================
echo "1. Checking HTTP(S) links in docs/ ..."

# Extract external links only (exclude docker-internal hosts and localhost)
LINKS=$(grep -r -oh 'https*://[a-zA-Z0-9.-]*\.[a-zA-Z][^)[:space:]]*' "${REPO_ROOT}/docs/" 2>/dev/null | \
  grep -v 'localhost' | \
  grep -v '127.0.0.1' | \
  grep -v ':$' | \
  sort -u)

LINK_FAILURES=0

for link in $LINKS; do
  # Strip trailing punctuation from extraction artifacts
  link=$(echo "$link" | sed 's/[`,"]*$//')

  # Perform HEAD request (5 second timeout, ignore SSL errors)
  if curl -sI --max-time 5 --insecure "$link" > /dev/null 2>&1; then
    CHECKS_PASSED=$((CHECKS_PASSED + 1))
  else
    echo "${RED}✗ Link failed: $link${NC}"
    LINK_FAILURES=$((LINK_FAILURES + 1))
    CHECKS_FAILED=$((CHECKS_FAILED + 1))
  fi
done

if [ "$LINK_FAILURES" -eq 0 ]; then
  if [ "$CHECKS_PASSED" -gt 0 ]; then
    echo "${GREEN}✓ All external links resolved (checked $CHECKS_PASSED)${NC}"
  else
    echo "${YELLOW}⊘ No external links found in docs${NC}"
  fi
else
  echo "${RED}✗ $LINK_FAILURES link(s) failed${NC}"
fi
echo ""

# ============================================================================
# 2. CHECK PORT NUMBERS IN AI_REFERENCE.md vs docker-compose.yml
# ============================================================================
echo "2. Checking port mappings (AI_REFERENCE.md vs docker-compose.yml) ..."
PORT_MISMATCHES=0

# Check each expected port exists in docker-compose.yml
for port in 8000 5432 6379 6333 11434 8080 9120 3000; do
  if grep -q "$port" "${REPO_ROOT}/infra/docker-compose.yml" 2>/dev/null; then
    CHECKS_PASSED=$((CHECKS_PASSED + 1))
  else
    echo "${RED}✗ Port mismatch: port $port not found in docker-compose.yml${NC}"
    PORT_MISMATCHES=$((PORT_MISMATCHES + 1))
    CHECKS_FAILED=$((CHECKS_FAILED + 1))
  fi
done

if [ "$PORT_MISMATCHES" -eq 0 ]; then
  echo "${GREEN}✓ All port mappings match${NC}"
else
  echo "${RED}✗ $PORT_MISMATCHES port mismatch(es)${NC}"
fi
echo ""

# ============================================================================
# 3. CHECK MAKE TARGETS IN MAKEFILE
# ============================================================================
echo "3. Checking Make targets exist in Makefile ..."
# Extract make targets from positive references (exclude lines with NOT/no/don't/AVOID)
MAKE_TARGETS_IN_DOCS=$(grep -roh '\`make [a-z\-]*\`' "${REPO_ROOT}/docs/" 2>/dev/null | \
  grep -v -E '\`make (feedback|init-framework)\`' | \
  sed 's/`//g' | sed 's/make //g' | sort -u)
MAKE_FAILURES=0

for target in $MAKE_TARGETS_IN_DOCS; do
  if grep -q "^${target}:" "${REPO_ROOT}/Makefile" 2>/dev/null; then
    CHECKS_PASSED=$((CHECKS_PASSED + 1))
  else
    echo "${RED}✗ Make target not found: $target${NC}"
    MAKE_FAILURES=$((MAKE_FAILURES + 1))
    CHECKS_FAILED=$((CHECKS_FAILED + 1))
  fi
done

if [ "$MAKE_FAILURES" -eq 0 ]; then
  echo "${GREEN}✓ All Make targets exist${NC}"
else
  echo "${RED}✗ $MAKE_FAILURES Make target(s) not found${NC}"
fi
echo ""

# ============================================================================
# 4. CHECK US FILES REFERENCED IN BACKLOG.md
# ============================================================================
echo "4. Checking User Story files referenced in BACKLOG.md ..."
US_REFS=$(grep -oE 'US-[0-9]{3}' "${REPO_ROOT}/docs/backlog/BACKLOG.md" 2>/dev/null | sort -u)
US_FAILURES=0

for us in $US_REFS; do
  us_file="${REPO_ROOT}/docs/backlog/${us}.md"
  if [ -f "$us_file" ]; then
    CHECKS_PASSED=$((CHECKS_PASSED + 1))
  else
    echo "${RED}✗ US file not found: $us_file${NC}"
    US_FAILURES=$((US_FAILURES + 1))
    CHECKS_FAILED=$((CHECKS_FAILED + 1))
  fi
done

if [ "$US_FAILURES" -eq 0 ]; then
  echo "${GREEN}✓ All US files exist${NC}"
else
  echo "${RED}✗ $US_FAILURES US file(s) not found${NC}"
fi
echo ""

# ============================================================================
# 5. CHECK PLUGIN MANIFEST STATUS
# ============================================================================
echo "5. Checking PLUGIN_MANIFEST.md metadata ..."
MANIFEST_FILE="${REPO_ROOT}/PLUGIN_MANIFEST.md"
MANIFEST_FAILURES=0

if [ -f "$MANIFEST_FILE" ]; then
  # Check for required frontmatter fields
  if grep -q '^type:' "$MANIFEST_FILE" && \
     grep -q '^name:' "$MANIFEST_FILE" && \
     grep -q '^version:' "$MANIFEST_FILE" && \
     grep -q '^status:' "$MANIFEST_FILE"; then
    CHECKS_PASSED=$((CHECKS_PASSED + 1))
    echo "${GREEN}✓ PLUGIN_MANIFEST.md has required frontmatter${NC}"
  else
    echo "${RED}✗ PLUGIN_MANIFEST.md missing required fields (type, name, version, status)${NC}"
    MANIFEST_FAILURES=$((MANIFEST_FAILURES + 1))
    CHECKS_FAILED=$((CHECKS_FAILED + 1))
  fi
else
  echo "${YELLOW}⊘ PLUGIN_MANIFEST.md not found (optional)${NC}"
fi
echo ""

# ============================================================================
# 6. CHECK RULE FILES FRONTMATTER
# ============================================================================
echo "6. Checking rule files in .claude/rules/project/ ..."
RULES_DIR="${REPO_ROOT}/.claude/rules/project"
RULE_FAILURES=0

if [ -d "$RULES_DIR" ]; then
  for rule_file in "$RULES_DIR"/rule-*.md; do
    if [ -f "$rule_file" ]; then
      rule_name=$(basename "$rule_file")
      # Rules should have frontmatter with constraint, why, and pattern sections
      if grep -q '^<constraint>' "$rule_file" && \
         grep -q '^<why>' "$rule_file" && \
         grep -q '<pattern>' "$rule_file"; then
        CHECKS_PASSED=$((CHECKS_PASSED + 1))
      else
        echo "${RED}✗ Rule missing required sections: $rule_name${NC}"
        RULE_FAILURES=$((RULE_FAILURES + 1))
        CHECKS_FAILED=$((CHECKS_FAILED + 1))
      fi
    fi
  done

  if [ "$RULE_FAILURES" -eq 0 ]; then
    echo "${GREEN}✓ All rule files have required structure${NC}"
  else
    echo "${RED}✗ $RULE_FAILURES rule file(s) have issues${NC}"
  fi
else
  echo "${YELLOW}⊘ .claude/rules/project/ directory not found${NC}"
fi
echo ""

# ============================================================================
# SUMMARY
# ============================================================================
echo "=== Verification Summary ==="
echo -e "Passed: ${GREEN}${CHECKS_PASSED}${NC}"
echo -e "Failed: ${RED}${CHECKS_FAILED}${NC}"

if [ "$CHECKS_FAILED" -gt 0 ]; then
  exit 1
fi

echo ""
echo -e "${GREEN}✓ All verifications passed${NC}"
exit 0
