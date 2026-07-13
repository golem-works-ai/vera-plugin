#!/usr/bin/env bash
# Regression check for issue #32 — ensures no personal references to the real
# Vera Clemens (@vera) are introduced into the codebase.
# Product/system identifiers (vera-plugin, vera:project-profile, vera-runner,
# vera.yml, vera-staging, temporary file prefixes) are expected and allowed.

set -euo pipefail

REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$REPO_ROOT"

ERRORS=0

echo "=== Checking for personal references to @vera / Vera Clemens ==="

# Check tracked files for personal-account references.
# We exclude the .git directory, this script itself, and product names.
# Product names are filtered with grep -v.

# 1. Grep for @vera as a standalone username (not part of a product name)
if grep -rIn '@vera[^a-zA-Z0-9_-]' . --exclude-dir=.git --exclude-dir=node_modules \
    | grep -v 'vera-plugin' \
    | grep -v 'vera-staging' \
    | grep -v 'vera-runner' \
    | grep -v 'vera.yml' \
    | grep -v 'vera:project-profile' \
    | grep -v 'vera_outcome' \
    | grep -v 'vera_exec' \
    | grep -v 'vera_api' \
    | grep -v 'vera-creds' \
    | grep -v 'x-vera' \
    | grep -v 'VERA_' \
    | grep -v 'verify_no_real_vera_refs.sh'; then
    echo "ERROR: Found @vera personal reference(s) above."
    ERRORS=$((ERRORS + 1))
else
    echo "OK: No @vera personal references found."
fi

# 2. Grep for "Vera Clemens" full name
if grep -rIn 'Vera Clemens' . --exclude-dir=.git --exclude-dir=node_modules \
    | grep -v 'verify_no_real_vera_refs.sh'; then
    echo "ERROR: Found 'Vera Clemens' reference(s) above."
    ERRORS=$((ERRORS + 1))
else
    echo "OK: No 'Vera Clemens' references found."
fi

# 3. Grep for vera-clemens username
if grep -rIn 'vera-clemens' . --exclude-dir=.git --exclude-dir=node_modules \
    | grep -v 'verify_no_real_vera_refs.sh'; then
    echo "ERROR: Found 'vera-clemens' reference(s) above."
    ERRORS=$((ERRORS + 1))
else
    echo "OK: No 'vera-clemens' references found."
fi

# 4. Check git history for embedded @vera references in reachable commits,
#    excluding this verification script itself.
if git log --all -S '@vera' --oneline -- . ':(exclude)scripts/verify_no_real_vera_refs.sh' | grep -q .; then
    git log --all -S '@vera' --oneline -- . ':(exclude)scripts/verify_no_real_vera_refs.sh'
    echo "ERROR: Found @vera reference(s) in git history above."
    ERRORS=$((ERRORS + 1))
else
    echo "OK: No @vera references in git history."
fi

if [ "$ERRORS" -gt 0 ]; then
    echo ""
    echo "FAILED: $ERRORS check(s) found personal references."
    exit 1
fi

echo ""
echo "PASSED: No personal references to the real Vera account found."
