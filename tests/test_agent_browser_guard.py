"""
Tests for agent-browser-guard.py hook.

This hook blocks browser automation CLIs (playwright, puppeteer, cypress, selenium)
and MCP tools except agent-browser.
"""

import json
import pytest
import subprocess
import sys
from pathlib import Path

TESTS_DIR = Path(__file__).parent
HOOKS_DIR = TESTS_DIR.parent / "hooks"
HOOK_PATH = HOOKS_DIR / "pre-tool-use" / "agent-browser-guard.py"


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

    def test_read_tool_allows(self):
        output = TestHookRunner.run({"tool_name": "Read", "tool_input": {"file_path": "/tmp/test"}})
        assert output["hookSpecificOutput"]["permissionDecision"] == "allow"

    def test_bash_non_browser_command_allows(self):
        output = TestHookRunner.run({"tool_name": "Bash", "tool_input": {"command": "ls -la"}})
        assert output["hookSpecificOutput"]["permissionDecision"] == "allow"

    def test_empty_input_allows(self):
        output = TestHookRunner.run({})
        assert output["hookSpecificOutput"]["permissionDecision"] == "allow"


class TestPlaywrightCLIBlocked:
    """Playwright CLI commands should be blocked."""

    def test_npx_playwright_test(self):
        output = TestHookRunner.run({"tool_name": "Bash", "tool_input": {"command": "npx playwright test"}})
        assert output["hookSpecificOutput"]["permissionDecision"] == "deny"
        assert "playwright" in output["hookSpecificOutput"]["permissionDecisionReason"].lower()

    def test_npm_run_playwright(self):
        output = TestHookRunner.run({"tool_name": "Bash", "tool_input": {"command": "npm run playwright test"}})
        assert output["hookSpecificOutput"]["permissionDecision"] == "deny"

    def test_playwright_install(self):
        output = TestHookRunner.run({"tool_name": "Bash", "tool_input": {"command": "playwright install"}})
        assert output["hookSpecificOutput"]["permissionDecision"] == "deny"

    def test_playwright_codegen(self):
        output = TestHookRunner.run({"tool_name": "Bash", "tool_input": {"command": "playwright codegen https://example.com"}})
        assert output["hookSpecificOutput"]["permissionDecision"] == "deny"


class TestPuppeteerCLIBlocked:
    """Puppeteer CLI commands should be blocked."""

    def test_npx_puppeteer(self):
        output = TestHookRunner.run({"tool_name": "Bash", "tool_input": {"command": "npx puppeteer screenshot https://example.com"}})
        assert output["hookSpecificOutput"]["permissionDecision"] == "deny"
        assert "puppeteer" in output["hookSpecificOutput"]["permissionDecisionReason"].lower()


class TestCypressCLIBlocked:
    """Cypress CLI commands should be blocked."""

    def test_npx_cypress_run(self):
        output = TestHookRunner.run({"tool_name": "Bash", "tool_input": {"command": "npx cypress run"}})
        assert output["hookSpecificOutput"]["permissionDecision"] == "deny"

    def test_cypress_open(self):
        output = TestHookRunner.run({"tool_name": "Bash", "tool_input": {"command": "cypress open"}})
        assert output["hookSpecificOutput"]["permissionDecision"] == "deny"


class TestSeleniumBlocked:
    """Selenium tools should be blocked."""

    def test_selenium_webdriver(self):
        output = TestHookRunner.run({"tool_name": "Bash", "tool_input": {"command": "npm install selenium-webdriver"}})
        assert output["hookSpecificOutput"]["permissionDecision"] == "deny"

    def test_webdriver_manager(self):
        output = TestHookRunner.run({"tool_name": "Bash", "tool_input": {"command": "webdriver-manager start"}})
        assert output["hookSpecificOutput"]["permissionDecision"] == "deny"


class TestPlaywrightMCPBlocked:
    """Playwright MCP tools should be blocked."""

    def test_playwright_mcp_navigate(self):
        output = TestHookRunner.run({
            "tool_name": "mcp__mcp-funnel__bridge_tool_request",
            "tool_input": {"tool": "playwright__navigate", "arguments": {"url": "https://example.com"}}
        })
        assert output["hookSpecificOutput"]["permissionDecision"] == "deny"
        assert "playwright" in output["hookSpecificOutput"]["permissionDecisionReason"].lower()

    def test_playwright_mcp_click(self):
        output = TestHookRunner.run({
            "tool_name": "mcp__mcp-funnel__bridge_tool_request",
            "tool_input": {"tool": "playwright__click", "arguments": {"selector": "#btn"}}
        })
        assert output["hookSpecificOutput"]["permissionDecision"] == "deny"


class TestAgentBrowserAllowed:
    """agent-browser commands should be allowed."""

    def test_agent_browser_open(self):
        # agent-browser CLI is NOT in BLOCKED list, so it should be allowed
        output = TestHookRunner.run({"tool_name": "Bash", "tool_input": {"command": "agent-browser open https://example.com"}})
        # agent-browser is in the BLOCKED list in playwright-guard, but NOT in agent-browser-guard
        # Let's check - actually looking at the code, agent-browser IS blocked in playwright-guard
        # but agent-browser-guard doesn't block it
        assert output["hookSpecificOutput"]["permissionDecision"] == "allow"


class TestOutputFormat:
    """Test output format is correct."""

    def test_has_hook_specific_output(self):
        output = TestHookRunner.run({})
        assert "hookSpecificOutput" in output

    def test_has_hook_event_name(self):
        output = TestHookRunner.run({})
        assert output["hookSpecificOutput"]["hookEventName"] == "PreToolUse"

    def test_deny_has_reason(self):
        output = TestHookRunner.run({"tool_name": "Bash", "tool_input": {"command": "npx playwright test"}})
        assert "permissionDecisionReason" in output["hookSpecificOutput"]


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

    def test_empty_command_allows(self):
        output = TestHookRunner.run({"tool_name": "Bash", "tool_input": {"command": ""}})
        assert output["hookSpecificOutput"]["permissionDecision"] == "allow"

    def test_case_insensitive_blocking(self):
        output = TestHookRunner.run({"tool_name": "Bash", "tool_input": {"command": "NPX PLAYWRIGHT TEST"}})
        assert output["hookSpecificOutput"]["permissionDecision"] == "deny"
