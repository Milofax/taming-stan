"""
Tests for playwright-guard.py hook.

This hook:
- Blocks CLI tools (playwright, puppeteer, cypress, selenium, agent-browser)
- Enforces headless:true as default, requiring user confirmation for headless:false
"""

import json
import pytest
import subprocess
import sys
from pathlib import Path

TESTS_DIR = Path(__file__).parent
HOOKS_DIR = TESTS_DIR.parent / "hooks"
HOOKS_LIB = HOOKS_DIR / "lib"
HOOK_PATH = HOOKS_DIR / "pre-tool-use" / "playwright-guard.py"

sys.path.insert(0, str(HOOKS_LIB))


class TestHookRunner:
    @staticmethod
    def run(hook_input: dict) -> dict:
        result = subprocess.run(
            [sys.executable, str(HOOK_PATH)],
            input=json.dumps(hook_input),
            capture_output=True,
            text=True,
            timeout=10
        )
        assert result.returncode == 0, f"Hook failed: {result.stderr}"
        return json.loads(result.stdout.strip())


class TestNonBrowserToolsAllowed:
    """Non-browser tools should always be allowed."""

    def test_bash_ls_allows(self):
        output = TestHookRunner.run({"tool_name": "Bash", "tool_input": {"command": "ls -la"}})
        assert output["hookSpecificOutput"]["permissionDecision"] == "allow"

    def test_read_allows(self):
        output = TestHookRunner.run({"tool_name": "Read", "tool_input": {"file_path": "/tmp/test"}})
        assert output["hookSpecificOutput"]["permissionDecision"] == "allow"

    def test_empty_input_allows(self):
        output = TestHookRunner.run({})
        assert output["hookSpecificOutput"]["permissionDecision"] == "allow"


class TestBrowserCLIBlocked:
    """Browser automation CLIs should be blocked."""

    def test_playwright_cli_blocked(self):
        output = TestHookRunner.run({
            "tool_name": "Bash",
            "tool_input": {"command": "npx playwright test"}
        })
        assert output["hookSpecificOutput"]["permissionDecision"] == "deny"
        assert "playwright" in output["hookSpecificOutput"]["permissionDecisionReason"].lower()

    def test_puppeteer_cli_blocked(self):
        output = TestHookRunner.run({
            "tool_name": "Bash",
            "tool_input": {"command": "npx puppeteer pdf https://example.com"}
        })
        assert output["hookSpecificOutput"]["permissionDecision"] == "deny"

    def test_cypress_cli_blocked(self):
        output = TestHookRunner.run({
            "tool_name": "Bash",
            "tool_input": {"command": "cypress run"}
        })
        assert output["hookSpecificOutput"]["permissionDecision"] == "deny"

    def test_agent_browser_cli_blocked(self):
        output = TestHookRunner.run({
            "tool_name": "Bash",
            "tool_input": {"command": "agent-browser open https://example.com"}
        })
        assert output["hookSpecificOutput"]["permissionDecision"] == "deny"


class TestPlaywrightMCPHeadless:
    """Playwright MCP should enforce headless:true by default."""

    def test_headless_true_allowed(self):
        output = TestHookRunner.run({
            "tool_name": "mcp__mcp-funnel__bridge_tool_request",
            "tool_input": {
                "tool": "playwright__navigate",
                "arguments": {"url": "https://example.com", "headless": True}
            }
        })
        assert output["hookSpecificOutput"]["permissionDecision"] == "allow"

    def test_headless_false_denied_first_time(self):
        from session_state import write_state
        write_state("headless_user_requested", False)

        output = TestHookRunner.run({
            "tool_name": "mcp__mcp-funnel__bridge_tool_request",
            "tool_input": {
                "tool": "playwright__navigate",
                "arguments": {"url": "https://example.com", "headless": False}
            }
        })
        assert output["hookSpecificOutput"]["permissionDecision"] == "deny"
        assert "headless" in output["hookSpecificOutput"]["permissionDecisionReason"].lower()

    def test_headless_false_allowed_after_confirmation(self):
        from session_state import write_state
        write_state("headless_user_requested", True)

        output = TestHookRunner.run({
            "tool_name": "mcp__mcp-funnel__bridge_tool_request",
            "tool_input": {
                "tool": "playwright__navigate",
                "arguments": {"url": "https://example.com", "headless": False}
            }
        })
        assert output["hookSpecificOutput"]["permissionDecision"] == "allow"

    def test_no_headless_arg_allowed(self):
        output = TestHookRunner.run({
            "tool_name": "mcp__mcp-funnel__bridge_tool_request",
            "tool_input": {
                "tool": "playwright__navigate",
                "arguments": {"url": "https://example.com"}
            }
        })
        assert output["hookSpecificOutput"]["permissionDecision"] == "allow"


class TestOutputFormat:
    """Test output format."""

    def test_has_hook_specific_output(self):
        output = TestHookRunner.run({})
        assert "hookSpecificOutput" in output

    def test_has_hook_event_name(self):
        output = TestHookRunner.run({})
        assert output["hookSpecificOutput"]["hookEventName"] == "PreToolUse"


class TestEdgeCases:
    """Test edge cases."""

    def test_invalid_json_allows(self):
        result = subprocess.run(
            [sys.executable, str(HOOK_PATH)],
            input="not valid json",
            capture_output=True,
            text=True,
            timeout=10
        )
        assert result.returncode == 0
        output = json.loads(result.stdout.strip())
        assert output["hookSpecificOutput"]["permissionDecision"] == "allow"

    def test_case_insensitive_blocking(self):
        output = TestHookRunner.run({
            "tool_name": "Bash",
            "tool_input": {"command": "NPX PLAYWRIGHT TEST"}
        })
        assert output["hookSpecificOutput"]["permissionDecision"] == "deny"

    def test_other_mcp_tool_allowed(self):
        output = TestHookRunner.run({
            "tool_name": "mcp__mcp-funnel__bridge_tool_request",
            "tool_input": {"tool": "firecrawl__scrape", "arguments": {"url": "https://example.com"}}
        })
        assert output["hookSpecificOutput"]["permissionDecision"] == "allow"
