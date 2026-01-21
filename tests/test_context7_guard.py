"""
Tests for context7-guard.py hook.

This hook:
- Checks if Graphiti should be searched before using Context7
- Tracks library lookups for coordination with firecrawl-guard
"""

import json
import pytest
import subprocess
import sys
from pathlib import Path

TESTS_DIR = Path(__file__).parent
HOOKS_DIR = TESTS_DIR.parent / "hooks"
HOOKS_LIB = HOOKS_DIR / "lib"
HOOK_PATH = HOOKS_DIR / "pre-tool-use" / "context7-guard.py"

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


class TestNonContext7ToolsAllowed:
    """Non-Context7 tools should always be allowed."""

    def test_bash_allows(self):
        output = TestHookRunner.run({"tool_name": "Bash", "tool_input": {"command": "ls"}})
        assert output["hookSpecificOutput"]["permissionDecision"] == "allow"

    def test_read_allows(self):
        output = TestHookRunner.run({"tool_name": "Read", "tool_input": {"file_path": "/tmp/test"}})
        assert output["hookSpecificOutput"]["permissionDecision"] == "allow"

    def test_empty_input_allows(self):
        output = TestHookRunner.run({})
        assert output["hookSpecificOutput"]["permissionDecision"] == "allow"

    def test_other_mcp_tool_allows(self):
        output = TestHookRunner.run({
            "tool_name": "mcp__mcp-funnel__bridge_tool_request",
            "tool_input": {"tool": "firecrawl__scrape"}
        })
        assert output["hookSpecificOutput"]["permissionDecision"] == "allow"


class TestContext7WithoutGraphiti:
    """Context7 should be allowed when Graphiti is not available."""

    def test_context7_resolve_allowed_without_graphiti(self):
        from session_state import write_state
        write_state("graphiti_available", False)

        output = TestHookRunner.run({
            "tool_name": "mcp__mcp-funnel__bridge_tool_request",
            "tool_input": {"tool": "context7__resolve_library_id", "arguments": {"libraryName": "react"}}
        })
        assert output["hookSpecificOutput"]["permissionDecision"] == "allow"


class TestContext7WithGraphiti:
    """Context7 should check Graphiti first when available."""

    def test_context7_blocked_when_graphiti_not_searched(self):
        from session_state import write_state
        write_state("graphiti_available", True)
        write_state("graphiti_searched", False)

        output = TestHookRunner.run({
            "tool_name": "mcp__mcp-funnel__bridge_tool_request",
            "tool_input": {"tool": "context7__resolve_library_id", "arguments": {"libraryName": "react"}}
        })
        assert output["hookSpecificOutput"]["permissionDecision"] == "deny"
        assert "graphiti" in output["hookSpecificOutput"]["permissionDecisionReason"].lower()

    def test_context7_allowed_after_graphiti_searched(self):
        from session_state import write_state
        write_state("graphiti_available", True)
        write_state("graphiti_searched", True)

        output = TestHookRunner.run({
            "tool_name": "mcp__mcp-funnel__bridge_tool_request",
            "tool_input": {"tool": "context7__resolve_library_id", "arguments": {"libraryName": "react"}}
        })
        assert output["hookSpecificOutput"]["permissionDecision"] == "allow"


class TestLibraryTracking:
    """Test that library lookups are tracked."""

    def test_library_tracked_on_resolve(self):
        from session_state import write_state, read_state
        write_state("graphiti_available", True)
        write_state("graphiti_searched", True)
        write_state("context7_attempted_for", [])  # Reset

        TestHookRunner.run({
            "tool_name": "mcp__mcp-funnel__bridge_tool_request",
            "tool_input": {"tool": "context7__resolve_library_id", "arguments": {"libraryName": "NextJS"}}
        })

        state = read_state()
        assert "nextjs" in state.get("context7_attempted_for", [])


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

    def test_missing_library_name_still_allows(self):
        from session_state import write_state
        write_state("graphiti_available", True)
        write_state("graphiti_searched", True)

        output = TestHookRunner.run({
            "tool_name": "mcp__mcp-funnel__bridge_tool_request",
            "tool_input": {"tool": "context7__resolve_library_id", "arguments": {}}
        })
        assert output["hookSpecificOutput"]["permissionDecision"] == "allow"
