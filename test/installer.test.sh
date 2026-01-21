#!/bin/bash
# Test script for taming-stan installer
# Tests hierarchy scenarios

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Test directories - use temp directory for isolation
TEST_BASE="$(cd "$(mktemp -d)" && pwd -P)"
TEST_HOME="$TEST_BASE/test-home"
TEST_PROJECT="$TEST_BASE/test-home/projects/myapp"
TEST_EXTERNAL="$TEST_BASE/external-volume/project"

# Installer path is relative to this script
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd -P)"
INSTALLER_PATH="$(cd "$SCRIPT_DIR/.." && pwd -P)"

# Counters
PASSED=0
FAILED=0

log() {
    echo -e "${YELLOW}[TEST]${NC} $1"
}

pass() {
    echo -e "${GREEN}[PASS]${NC} $1"
    PASSED=$((PASSED + 1))
}

fail() {
    echo -e "${RED}[FAIL]${NC} $1"
    FAILED=$((FAILED + 1))
}

cleanup() {
    log "Cleaning up test directories..."
    rm -rf "$TEST_BASE"
}

trap cleanup EXIT

setup() {
    rm -rf "$TEST_HOME"
    rm -rf "$TEST_BASE/external-volume"
    log "Creating test directories..."
    mkdir -p "$TEST_HOME"
    mkdir -p "$TEST_PROJECT"
    mkdir -p "$TEST_EXTERNAL"
    export HOME="$TEST_HOME"
}

check_hooks_exist() {
    local dir="$1"
    local hooks_dir="$dir/.claude/hooks/taming-stan"
    if [ -d "$hooks_dir" ] && [ "$(ls -A "$hooks_dir" 2>/dev/null | grep -v __pycache__ | head -1)" ]; then
        return 0
    fi
    return 1
}

check_rules_exist() {
    local dir="$1"
    local rules_dir="$dir/.claude/rules/taming-stan"
    if [ -d "$rules_dir" ] && [ "$(ls -A "$rules_dir" 2>/dev/null)" ]; then
        return 0
    fi
    return 1
}

count_hooks() {
    local dir="$1"
    local hooks_dir="$dir/.claude/hooks/taming-stan"
    if [ -d "$hooks_dir" ]; then
        find "$hooks_dir" -name "*.py" ! -path "*/__pycache__/*" ! -path "*/lib/*" | wc -l | tr -d ' '
    else
        echo "0"
    fi
}

check_posttooluse_hook() {
    local dir="$1"
    local hook_file="$dir/.claude/hooks/taming-stan/post-tool-use/graphiti-retry-guard.py"
    if [ -f "$hook_file" ]; then
        return 0
    fi
    return 1
}

check_posttooluse_settings() {
    local dir="$1"
    local settings_file="$dir/.claude/settings.json"
    if [ -f "$settings_file" ] && grep -q '"PostToolUse"' "$settings_file" 2>/dev/null; then
        return 0
    fi
    return 1
}

# ============================================
# TEST 1: Fresh install in HOME (--all flag)
# ============================================
test_fresh_install_home() {
    log "TEST 1: Fresh install in HOME (--all flag)"
    setup

    cd "$TEST_HOME"
    node "$INSTALLER_PATH/bin/cli.js" install --all 2>&1 || true

    if check_hooks_exist "$TEST_HOME"; then
        pass "Hooks installed in HOME"
    else
        fail "Hooks NOT installed in HOME"
    fi

    if check_rules_exist "$TEST_HOME"; then
        pass "Rules installed in HOME"
    else
        fail "Rules NOT installed in HOME"
    fi

    # Check core lib exists
    if [ -f "$TEST_HOME/.claude/hooks/taming-stan/lib/session_state.py" ]; then
        pass "Core lib (session_state.py) installed"
    else
        fail "Core lib (session_state.py) NOT installed"
    fi

    # Check PostToolUse hook exists
    if check_posttooluse_hook "$TEST_HOME"; then
        pass "PostToolUse hook (graphiti-retry-guard.py) installed"
    else
        fail "PostToolUse hook NOT installed"
    fi

    # Check PostToolUse in settings.json
    if check_posttooluse_settings "$TEST_HOME"; then
        pass "PostToolUse configured in settings.json"
    else
        fail "PostToolUse NOT in settings.json"
    fi
}

# ============================================
# TEST 2: Fresh install in Project (no HOME hooks)
# ============================================
test_fresh_install_project() {
    log "TEST 2: Fresh install in Project (no HOME hooks)"
    setup

    cd "$TEST_PROJECT"
    node "$INSTALLER_PATH/bin/cli.js" install --all 2>&1 || true

    if check_hooks_exist "$TEST_PROJECT"; then
        pass "Hooks installed in Project"
    else
        fail "Hooks NOT installed in Project"
    fi

    if check_rules_exist "$TEST_PROJECT"; then
        pass "Rules installed in Project"
    else
        fail "Rules NOT installed in Project"
    fi

    # Check HOME is clean
    if ! check_hooks_exist "$TEST_HOME"; then
        pass "HOME has no hooks (correct)"
    else
        fail "HOME has hooks (should be empty)"
    fi
}

# ============================================
# TEST 3: Install in Project when HOME has hooks
# ============================================
test_install_project_with_home_hooks() {
    log "TEST 3: Install in Project when HOME has hooks"
    setup

    # First install in HOME
    cd "$TEST_HOME"
    node "$INSTALLER_PATH/bin/cli.js" install --all 2>&1 || true

    # Then install in Project
    cd "$TEST_PROJECT"
    node "$INSTALLER_PATH/bin/cli.js" install --all 2>&1 || true

    # Project should have rules but NO hooks (inherited from HOME)
    if check_rules_exist "$TEST_PROJECT"; then
        pass "Rules installed in Project"
    else
        fail "Rules NOT installed in Project"
    fi

    # Check project does NOT have hooks (inherited from HOME)
    local project_hook_count=$(count_hooks "$TEST_PROJECT")
    if [ "$project_hook_count" -eq "0" ]; then
        pass "Project has no local hooks (inherited from HOME) - count: $project_hook_count"
    else
        fail "Project has local hooks but should inherit - count: $project_hook_count"
    fi
}

# ============================================
# TEST 4: Install in HOME when Project has hooks (migration up)
# ============================================
test_hook_migration_up() {
    log "TEST 4: Install in HOME when Project has hooks (migration up)"
    setup

    # First install in Project
    cd "$TEST_PROJECT"
    node "$INSTALLER_PATH/bin/cli.js" install --all 2>&1 || true

    local project_hooks_before=$(count_hooks "$TEST_PROJECT")
    log "Project hooks before HOME install: $project_hooks_before"

    # Then install in HOME
    cd "$TEST_HOME"
    node "$INSTALLER_PATH/bin/cli.js" install --all 2>&1 || true

    # HOME should have hooks
    if check_hooks_exist "$TEST_HOME"; then
        pass "Hooks installed in HOME"
    else
        fail "Hooks NOT installed in HOME"
    fi

    # Project rules should still exist
    if check_rules_exist "$TEST_PROJECT"; then
        pass "Project rules still exist after migration"
    else
        fail "Project rules removed (should remain)"
    fi
}

# ============================================
# TEST 5: Uninstall in Project (simple cleanup)
# ============================================
test_uninstall_project() {
    log "TEST 5: Uninstall in Project (simple cleanup)"
    setup

    # Install in Project
    cd "$TEST_PROJECT"
    node "$INSTALLER_PATH/bin/cli.js" install --all 2>&1 || true

    # Uninstall
    node "$INSTALLER_PATH/bin/cli.js" uninstall 2>&1 || true

    # Everything should be clean
    if ! check_hooks_exist "$TEST_PROJECT"; then
        pass "Hooks removed from Project"
    else
        fail "Hooks still exist in Project"
    fi

    if ! check_rules_exist "$TEST_PROJECT"; then
        pass "Rules removed from Project"
    else
        fail "Rules still exist in Project"
    fi
}

# ============================================
# TEST 6: Reinstall (idempotent)
# ============================================
test_reinstall() {
    log "TEST 6: Reinstall (idempotent)"
    setup

    cd "$TEST_PROJECT"

    # First install
    node "$INSTALLER_PATH/bin/cli.js" install --all 2>&1 || true
    local hooks_before=$(count_hooks "$TEST_PROJECT")

    # Second install
    node "$INSTALLER_PATH/bin/cli.js" install --all 2>&1 || true
    local hooks_after=$(count_hooks "$TEST_PROJECT")

    if [ "$hooks_before" -eq "$hooks_after" ]; then
        pass "Hook count unchanged after reinstall ($hooks_after)"
    else
        fail "Hook count changed: $hooks_before -> $hooks_after"
    fi
}

# ============================================
# TEST 7: External project (outside HOME) registers in registry
# ============================================
test_external_project_registers() {
    log "TEST 7: External project (outside HOME) registers in registry"
    setup

    local registry_file="$TEST_HOME/.claude/taming-stan-installation-registry.json"

    # Install in external project (outside HOME hierarchy)
    cd "$TEST_EXTERNAL"
    node "$INSTALLER_PATH/bin/cli.js" install --all 2>&1 || true

    # Check registry file exists
    if [ -f "$registry_file" ]; then
        pass "Registry file created"
    else
        fail "Registry file NOT created"
    fi

    # Check registry contains the external project
    if grep -q "$TEST_EXTERNAL" "$registry_file" 2>/dev/null; then
        pass "External project registered in registry"
    else
        fail "External project NOT in registry"
    fi

    # Verify external project has hooks and rules
    if check_hooks_exist "$TEST_EXTERNAL"; then
        pass "External project has hooks"
    else
        fail "External project missing hooks"
    fi

    if check_rules_exist "$TEST_EXTERNAL"; then
        pass "External project has rules"
    else
        fail "External project missing rules"
    fi
}

# ============================================
# TEST 8: Uninstall removes project from registry
# ============================================
test_uninstall_removes_from_registry() {
    log "TEST 8: Uninstall removes project from registry"
    setup

    local registry_file="$TEST_HOME/.claude/taming-stan-installation-registry.json"

    # Install in external project
    cd "$TEST_EXTERNAL"
    node "$INSTALLER_PATH/bin/cli.js" install --all 2>&1 || true

    # Verify it's in registry
    if grep -q "$TEST_EXTERNAL" "$registry_file" 2>/dev/null; then
        pass "External project in registry before uninstall"
    else
        fail "External project NOT in registry"
    fi

    # Uninstall
    node "$INSTALLER_PATH/bin/cli.js" uninstall 2>&1 || true

    # Verify it's removed from registry
    if grep -q "$TEST_EXTERNAL" "$registry_file" 2>/dev/null; then
        fail "External project still in registry after uninstall"
    else
        pass "External project removed from registry after uninstall"
    fi
}

# ============================================
# TEST 9: HOME itself is NOT registered in registry
# ============================================
test_home_not_registered() {
    log "TEST 9: HOME itself is NOT registered in registry"
    setup

    local registry_file="$TEST_HOME/.claude/taming-stan-installation-registry.json"

    # Install in HOME
    cd "$TEST_HOME"
    node "$INSTALLER_PATH/bin/cli.js" install --all 2>&1 || true

    # Registry should NOT contain HOME path
    if [ -f "$registry_file" ]; then
        if grep -q "\"$TEST_HOME\"" "$registry_file" 2>/dev/null; then
            fail "HOME is in registry (should not be)"
        else
            pass "HOME is NOT in registry (correct)"
        fi
    else
        pass "Registry file not created when only HOME installed (correct)"
    fi
}

# ============================================
# TEST 10: PostToolUse hook 3-Strikes behavior
# ============================================
test_posttooluse_3strikes() {
    log "TEST 10: PostToolUse hook 3-Strikes behavior"
    setup

    cd "$TEST_HOME"
    node "$INSTALLER_PATH/bin/cli.js" install --all 2>&1 || true

    local hook_path="$TEST_HOME/.claude/hooks/taming-stan/post-tool-use/graphiti-retry-guard.py"

    # Verify hook exists
    if [ ! -f "$hook_path" ]; then
        fail "PostToolUse hook not found at $hook_path"
        return
    fi

    # Test 1: Success case (no error) should allow
    local result=$(echo '{"tool_name": "Bash", "tool_error": null}' | python3 "$hook_path" 2>/dev/null)
    if echo "$result" | grep -q '"permissionDecision": "allow"'; then
        pass "Success case returns allow"
    else
        fail "Success case should return allow"
    fi

    # Test 2: First failure should allow
    result=$(echo '{"tool_name": "Bash", "tool_error": "Permission denied"}' | python3 "$hook_path" 2>/dev/null)
    if echo "$result" | grep -q '"permissionDecision": "allow"'; then
        pass "First failure returns allow"
    else
        fail "First failure should return allow"
    fi

    # Test 3: Second failure should allow
    result=$(echo '{"tool_name": "Bash", "tool_error": "Permission denied"}' | python3 "$hook_path" 2>/dev/null)
    if echo "$result" | grep -q '"permissionDecision": "allow"'; then
        pass "Second failure returns allow"
    else
        fail "Second failure should return allow"
    fi

    # Test 4: Third failure should DENY (3-strikes)
    result=$(echo '{"tool_name": "Bash", "tool_error": "Permission denied"}' | python3 "$hook_path" 2>/dev/null)
    if echo "$result" | grep -q '"permissionDecision": "deny"'; then
        pass "Third failure returns deny (3-strikes)"
    else
        fail "Third failure should return deny (3-strikes triggered)"
    fi

    # Test 5: Verify deny message contains search_nodes hint
    if echo "$result" | grep -q 'search_nodes'; then
        pass "Deny message contains search_nodes hint"
    else
        fail "Deny message should contain search_nodes hint"
    fi
}

# ============================================
# TEST 11: Service selection with specific services
# ============================================
test_specific_services() {
    log "TEST 11: Service selection with specific services"
    setup

    cd "$TEST_PROJECT"
    node "$INSTALLER_PATH/bin/cli.js" install graphiti,stanflux 2>&1 || true

    # Check graphiti rule exists
    if [ -f "$TEST_PROJECT/.claude/rules/taming-stan/graphiti.md" ]; then
        pass "Graphiti rule installed"
    else
        fail "Graphiti rule NOT installed"
    fi

    # Check stanflux rule exists
    if [ -f "$TEST_PROJECT/.claude/rules/taming-stan/stanflux.md" ]; then
        pass "STANFLUX rule installed"
    else
        fail "STANFLUX rule NOT installed"
    fi

    # Check firecrawl NOT installed
    if [ ! -f "$TEST_PROJECT/.claude/rules/taming-stan/mcp-configurations/firecrawl.md" ]; then
        pass "Firecrawl rule NOT installed (correct)"
    else
        fail "Firecrawl rule installed (should not be)"
    fi
}

# ============================================
# RUN ALL TESTS
# ============================================
echo ""
echo "========================================"
echo "  taming-stan Installer Tests"
echo "========================================"
echo ""

test_fresh_install_home
echo ""

test_fresh_install_project
echo ""

test_install_project_with_home_hooks
echo ""

test_hook_migration_up
echo ""

test_uninstall_project
echo ""

test_reinstall
echo ""

test_external_project_registers
echo ""

test_uninstall_removes_from_registry
echo ""

test_home_not_registered
echo ""

test_posttooluse_3strikes
echo ""

test_specific_services
echo ""

# Summary
echo ""
echo "========================================"
echo "  Test Results"
echo "========================================"
echo -e "${GREEN}Passed: $PASSED${NC}"
echo -e "${RED}Failed: $FAILED${NC}"
echo ""

if [ $FAILED -eq 0 ]; then
    echo -e "${GREEN}All tests passed!${NC}"
    exit 0
else
    echo -e "${RED}Some tests failed!${NC}"
    exit 1
fi
