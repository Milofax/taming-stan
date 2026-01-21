"""
Tests for firecrawl-guard.py hook.

This hook:
- Enforces Graphiti search before WebSearch/WebFetch
- Enforces Firecrawl before WebSearch/WebFetch
- Suggests Context7 for library documentation searches
"""

import json
import pytest
import subprocess
import sys
from pathlib import Path

TESTS_DIR = Path(__file__).parent
HOOKS_DIR = TESTS_DIR.parent / "hooks"
HOOKS_LIB = HOOKS_DIR / "lib"
HOOK_PATH = HOOKS_DIR / "pre-tool-use" / "firecrawl-guard.py"

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


class TestNonWebToolsAllowed:
    """Non-web tools should always be allowed."""

    def test_bash_allows(self):
        output = TestHookRunner.run({"tool_name": "Bash", "tool_input": {"command": "ls"}})
        assert output["hookSpecificOutput"]["permissionDecision"] == "allow"

    def test_read_allows(self):
        output = TestHookRunner.run({"tool_name": "Read", "tool_input": {"file_path": "/tmp/test"}})
        assert output["hookSpecificOutput"]["permissionDecision"] == "allow"

    def test_empty_input_allows(self):
        output = TestHookRunner.run({})
        assert output["hookSpecificOutput"]["permissionDecision"] == "allow"


class TestWebSearchGraphitiFirst:
    """WebSearch should require Graphiti search first."""

    def test_websearch_blocked_without_graphiti(self):
        from session_state import write_state
        write_state("graphiti_available", True)
        write_state("graphiti_searched", False)

        output = TestHookRunner.run({
            "tool_name": "WebSearch",
            "tool_input": {"query": "python tutorial"}
        })
        assert output["hookSpecificOutput"]["permissionDecision"] == "deny"
        assert "graphiti" in output["hookSpecificOutput"]["permissionDecisionReason"].lower()


class TestWebSearchFirecrawlFirst:
    """WebSearch should require Firecrawl attempt first."""

    def test_websearch_blocked_without_firecrawl(self):
        from session_state import write_state
        write_state("graphiti_available", True)
        write_state("graphiti_searched", True)
        write_state("firecrawl_attempted", False)

        output = TestHookRunner.run({
            "tool_name": "WebSearch",
            "tool_input": {"query": "python tutorial"}
        })
        assert output["hookSpecificOutput"]["permissionDecision"] == "deny"
        assert "firecrawl" in output["hookSpecificOutput"]["permissionDecisionReason"].lower()

    def test_websearch_allowed_after_firecrawl(self):
        from session_state import write_state
        write_state("graphiti_available", True)
        write_state("graphiti_searched", True)
        write_state("firecrawl_attempted", True)

        output = TestHookRunner.run({
            "tool_name": "WebSearch",
            "tool_input": {"query": "python tutorial"}
        })
        assert output["hookSpecificOutput"]["permissionDecision"] == "allow"


class TestWebFetch:
    """WebFetch should have same rules as WebSearch."""

    def test_webfetch_blocked_without_graphiti(self):
        from session_state import write_state
        write_state("graphiti_available", True)
        write_state("graphiti_searched", False)

        output = TestHookRunner.run({
            "tool_name": "WebFetch",
            "tool_input": {"url": "https://example.com"}
        })
        assert output["hookSpecificOutput"]["permissionDecision"] == "deny"

    def test_webfetch_allowed_after_all_checks(self):
        from session_state import write_state
        write_state("graphiti_available", True)
        write_state("graphiti_searched", True)
        write_state("firecrawl_attempted", True)

        output = TestHookRunner.run({
            "tool_name": "WebFetch",
            "tool_input": {"url": "https://example.com"}
        })
        assert output["hookSpecificOutput"]["permissionDecision"] == "allow"


class TestFirecrawlViabridge:
    """Firecrawl via MCP bridge should check Graphiti first."""

    def test_firecrawl_blocked_without_graphiti(self):
        from session_state import write_state
        write_state("graphiti_available", True)
        write_state("graphiti_searched", False)

        output = TestHookRunner.run({
            "tool_name": "mcp__mcp-funnel__bridge_tool_request",
            "tool_input": {"tool": "firecrawl__search", "arguments": {"query": "react docs"}}
        })
        assert output["hookSpecificOutput"]["permissionDecision"] == "deny"

    def test_firecrawl_sets_attempted_flag(self):
        from session_state import write_state, read_state
        write_state("graphiti_available", True)
        write_state("graphiti_searched", True)
        write_state("firecrawl_attempted", False)

        TestHookRunner.run({
            "tool_name": "mcp__mcp-funnel__bridge_tool_request",
            "tool_input": {"tool": "firecrawl__scrape", "arguments": {"url": "https://example.com"}}
        })

        state = read_state()
        assert state.get("firecrawl_attempted") == True


class TestContext7Suggestion:
    """Firecrawl should suggest Context7 for library docs."""

    def test_suggests_context7_for_react_docs(self):
        from session_state import write_state, register_hook
        write_state("graphiti_available", True)
        write_state("graphiti_searched", True)
        register_hook("context7")  # Activate Context7 hook
        write_state("context7_attempted_for", [])

        output = TestHookRunner.run({
            "tool_name": "mcp__mcp-funnel__bridge_tool_request",
            "tool_input": {"tool": "firecrawl__search", "arguments": {"query": "react documentation"}}
        })
        assert output["hookSpecificOutput"]["permissionDecision"] == "deny"
        assert "context7" in output["hookSpecificOutput"]["permissionDecisionReason"].lower()

    def test_allows_after_context7_attempted(self):
        from session_state import write_state, register_hook
        write_state("graphiti_available", True)
        write_state("graphiti_searched", True)
        register_hook("context7")
        write_state("context7_attempted_for", ["react"])

        output = TestHookRunner.run({
            "tool_name": "mcp__mcp-funnel__bridge_tool_request",
            "tool_input": {"tool": "firecrawl__search", "arguments": {"query": "react documentation"}}
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

    def test_graphiti_not_available_allows_websearch(self):
        from session_state import write_state
        write_state("graphiti_available", False)
        write_state("firecrawl_attempted", True)

        output = TestHookRunner.run({
            "tool_name": "WebSearch",
            "tool_input": {"query": "test"}
        })
        # When graphiti_available is False, graphiti check is skipped
        # But firecrawl check still applies
        assert output["hookSpecificOutput"]["permissionDecision"] == "allow"
