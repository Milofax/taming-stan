"""
Tests for hooks/pre-tool-use/graphiti-first-guard.py

Tests the PreToolUse hook that enforces "Graphiti First" rule:
External research tools should only be used AFTER searching Graphiti.

Edge cases covered:
- WebSearch/WebFetch blocked without prior Graphiti search
- Firecrawl tools blocked without prior Graphiti search
- Context7 tools blocked without prior Graphiti search
- Non-research tools pass through
- After Graphiti search, research tools are allowed
"""

import json
from pathlib import Path

import pytest
import sys
sys.path.insert(0, str(Path(__file__).parent.parent / "hooks" / "lib"))
sys.path.insert(0, str(Path(__file__).parent))
import session_state as ss
from helpers import make_bridge_input


class TestNonResearchToolsPassThrough:
    """Non-research tools should pass through regardless of Graphiti search status."""

    def test_bash_command_allows(self, graphiti_first_guard_runner, clean_state):
        """Bash commands should always pass."""
        hook_input = {"tool_name": "Bash", "tool_input": {"command": "ls -la"}}
        result = graphiti_first_guard_runner.run(hook_input)
        assert result["hookSpecificOutput"]["permissionDecision"] == "allow"

    def test_read_tool_allows(self, graphiti_first_guard_runner, clean_state):
        """Read tool should always pass."""
        hook_input = {"tool_name": "Read", "tool_input": {"file_path": "/tmp/test.txt"}}
        result = graphiti_first_guard_runner.run(hook_input)
        assert result["hookSpecificOutput"]["permissionDecision"] == "allow"

    def test_edit_tool_allows(self, graphiti_first_guard_runner, clean_state):
        """Edit tool should always pass."""
        hook_input = {
            "tool_name": "Edit",
            "tool_input": {"file_path": "/tmp/test.txt", "old_string": "a", "new_string": "b"}
        }
        result = graphiti_first_guard_runner.run(hook_input)
        assert result["hookSpecificOutput"]["permissionDecision"] == "allow"

    def test_non_research_bridge_tool_allows(self, graphiti_first_guard_runner, clean_state):
        """Non-research MCP tools should pass."""
        hook_input = make_bridge_input("github__create_issue", {"title": "Test"})
        result = graphiti_first_guard_runner.run(hook_input)
        assert result["hookSpecificOutput"]["permissionDecision"] == "allow"


class TestWebSearchBlocked:
    """WebSearch should be blocked without prior Graphiti search."""

    def test_websearch_blocked_without_graphiti(self, graphiti_first_guard_runner, clean_state):
        """WebSearch should be denied if Graphiti not searched."""
        hook_input = {
            "tool_name": "WebSearch",
            "tool_input": {"query": "how to use React hooks"}
        }
        result = graphiti_first_guard_runner.run(hook_input)

        assert result["hookSpecificOutput"]["permissionDecision"] == "deny"
        reason = result["hookSpecificOutput"]["permissionDecisionReason"]
        assert "graphiti_first" in reason.lower() or "search_nodes" in reason.lower()

    def test_websearch_allowed_after_graphiti(self, graphiti_first_guard_runner, clean_state):
        """WebSearch should be allowed if Graphiti was searched."""
        ss.write_state("graphiti_searched", True)

        hook_input = {
            "tool_name": "WebSearch",
            "tool_input": {"query": "how to use React hooks"}
        }
        result = graphiti_first_guard_runner.run(hook_input)

        assert result["hookSpecificOutput"]["permissionDecision"] == "allow"

    def test_websearch_deny_includes_query(self, graphiti_first_guard_runner, clean_state):
        """Deny message should include the query for Graphiti search suggestion."""
        hook_input = {
            "tool_name": "WebSearch",
            "tool_input": {"query": "Claude Code hooks"}
        }
        result = graphiti_first_guard_runner.run(hook_input)

        reason = result["hookSpecificOutput"]["permissionDecisionReason"]
        assert "Claude Code" in reason or "hooks" in reason


class TestWebFetchBlocked:
    """WebFetch should be blocked without prior Graphiti search."""

    def test_webfetch_blocked_without_graphiti(self, graphiti_first_guard_runner, clean_state):
        """WebFetch should be denied if Graphiti not searched."""
        hook_input = {
            "tool_name": "WebFetch",
            "tool_input": {"url": "https://docs.example.com/api"}
        }
        result = graphiti_first_guard_runner.run(hook_input)

        assert result["hookSpecificOutput"]["permissionDecision"] == "deny"

    def test_webfetch_allowed_after_graphiti(self, graphiti_first_guard_runner, clean_state):
        """WebFetch should be allowed if Graphiti was searched."""
        ss.write_state("graphiti_searched", True)

        hook_input = {
            "tool_name": "WebFetch",
            "tool_input": {"url": "https://docs.example.com"}
        }
        result = graphiti_first_guard_runner.run(hook_input)

        assert result["hookSpecificOutput"]["permissionDecision"] == "allow"


class TestFirecrawlBlocked:
    """Firecrawl tools should be blocked without prior Graphiti search."""

    def test_firecrawl_scrape_blocked(self, graphiti_first_guard_runner, clean_state):
        """firecrawl_scrape should be denied if Graphiti not searched."""
        hook_input = make_bridge_input("firecrawl__scrape", {"url": "https://example.com"})
        result = graphiti_first_guard_runner.run(hook_input)

        assert result["hookSpecificOutput"]["permissionDecision"] == "deny"

    def test_firecrawl_search_blocked(self, graphiti_first_guard_runner, clean_state):
        """firecrawl_search should be denied if Graphiti not searched."""
        hook_input = make_bridge_input("firecrawl__search", {"query": "react tutorials"})
        result = graphiti_first_guard_runner.run(hook_input)

        assert result["hookSpecificOutput"]["permissionDecision"] == "deny"

    def test_firecrawl_allowed_after_graphiti(self, graphiti_first_guard_runner, clean_state):
        """Firecrawl should be allowed if Graphiti was searched."""
        ss.write_state("graphiti_searched", True)

        hook_input = make_bridge_input("firecrawl__scrape", {"url": "https://example.com"})
        result = graphiti_first_guard_runner.run(hook_input)

        assert result["hookSpecificOutput"]["permissionDecision"] == "allow"


class TestContext7Blocked:
    """Context7 tools should be blocked without prior Graphiti search."""

    def test_context7_resolve_blocked(self, graphiti_first_guard_runner, clean_state):
        """context7 resolve-library-id should be denied if Graphiti not searched."""
        hook_input = make_bridge_input(
            "context7__resolve-library-id",
            {"libraryName": "react"}
        )
        result = graphiti_first_guard_runner.run(hook_input)

        assert result["hookSpecificOutput"]["permissionDecision"] == "deny"

    def test_context7_query_blocked(self, graphiti_first_guard_runner, clean_state):
        """context7 query-docs should be denied if Graphiti not searched."""
        hook_input = make_bridge_input(
            "context7__query-docs",
            {"context7CompatibleLibraryID": "/vercel/next.js", "topic": "routing"}
        )
        result = graphiti_first_guard_runner.run(hook_input)

        assert result["hookSpecificOutput"]["permissionDecision"] == "deny"

    def test_context7_allowed_after_graphiti(self, graphiti_first_guard_runner, clean_state):
        """Context7 should be allowed if Graphiti was searched."""
        ss.write_state("graphiti_searched", True)

        hook_input = make_bridge_input(
            "context7__resolve-library-id",
            {"libraryName": "react"}
        )
        result = graphiti_first_guard_runner.run(hook_input)

        assert result["hookSpecificOutput"]["permissionDecision"] == "allow"


class TestGraphitiSearchDetection:
    """Test that graphiti_searched flag is properly checked."""

    def test_explicit_false_blocks(self, graphiti_first_guard_runner, clean_state):
        """Explicit False value should block."""
        ss.write_state("graphiti_searched", False)

        hook_input = {"tool_name": "WebSearch", "tool_input": {"query": "test"}}
        result = graphiti_first_guard_runner.run(hook_input)

        assert result["hookSpecificOutput"]["permissionDecision"] == "deny"

    def test_missing_flag_blocks(self, graphiti_first_guard_runner, clean_state):
        """Missing flag should block (default to not searched)."""
        # Don't set graphiti_searched at all
        hook_input = {"tool_name": "WebSearch", "tool_input": {"query": "test"}}
        result = graphiti_first_guard_runner.run(hook_input)

        assert result["hookSpecificOutput"]["permissionDecision"] == "deny"


class TestDenyMessageQuality:
    """Test that deny messages are helpful."""

    def test_deny_message_mentions_zettelkasten(self, graphiti_first_guard_runner, clean_state):
        """Deny message should mention Zettelkasten principle."""
        hook_input = {"tool_name": "WebSearch", "tool_input": {"query": "test query"}}
        result = graphiti_first_guard_runner.run(hook_input)

        reason = result["hookSpecificOutput"]["permissionDecisionReason"]
        assert "zettelkasten" in reason.lower()

    def test_deny_message_suggests_search_nodes(self, graphiti_first_guard_runner, clean_state):
        """Deny message should suggest using search_nodes."""
        hook_input = {"tool_name": "WebSearch", "tool_input": {"query": "react hooks best practices"}}
        result = graphiti_first_guard_runner.run(hook_input)

        reason = result["hookSpecificOutput"]["permissionDecisionReason"]
        assert "search_nodes" in reason

    def test_deny_message_truncates_long_query(self, graphiti_first_guard_runner, clean_state):
        """Long queries should be truncated in deny message."""
        long_query = "a" * 100
        hook_input = {"tool_name": "WebSearch", "tool_input": {"query": long_query}}
        result = graphiti_first_guard_runner.run(hook_input)

        reason = result["hookSpecificOutput"]["permissionDecisionReason"]
        # Query should be truncated to 50 chars
        assert len(reason) < 300


class TestEdgeCases:
    """Edge cases and error handling."""

    def test_invalid_json_allows(self, graphiti_first_guard_runner, clean_state):
        """Invalid JSON should fail safe and allow."""
        import subprocess
        import sys as sys_module

        hook_path = Path(__file__).parent.parent / "hooks" / "pre-tool-use" / "graphiti-first-guard.py"
        result = subprocess.run(
            [sys_module.executable, str(hook_path)],
            input="not valid json",
            capture_output=True,
            text=True,
            timeout=10
        )

        output = json.loads(result.stdout)
        assert output["hookSpecificOutput"]["permissionDecision"] == "allow"

    def test_empty_query_still_blocks(self, graphiti_first_guard_runner, clean_state):
        """Empty query should still trigger block for research tools."""
        hook_input = {"tool_name": "WebSearch", "tool_input": {"query": ""}}
        result = graphiti_first_guard_runner.run(hook_input)

        assert result["hookSpecificOutput"]["permissionDecision"] == "deny"

    def test_hook_registers_itself(self, graphiti_first_guard_runner, clean_state):
        """Hook should register itself."""
        hook_input = {"tool_name": "Bash", "tool_input": {"command": "echo test"}}
        graphiti_first_guard_runner.run(hook_input)

        state = ss.read_state()
        assert state.get("hooks_active", {}).get("graphiti-first") is True

    def test_case_insensitive_firecrawl_detection(self, graphiti_first_guard_runner, clean_state):
        """Firecrawl detection should be case-insensitive."""
        hook_input = make_bridge_input("FIRECRAWL__SEARCH", {"query": "test"})
        result = graphiti_first_guard_runner.run(hook_input)

        assert result["hookSpecificOutput"]["permissionDecision"] == "deny"

    def test_case_insensitive_context7_detection(self, graphiti_first_guard_runner, clean_state):
        """Context7 detection should be case-insensitive."""
        hook_input = make_bridge_input("CONTEXT7__resolve-library-id", {"libraryName": "test"})
        result = graphiti_first_guard_runner.run(hook_input)

        assert result["hookSpecificOutput"]["permissionDecision"] == "deny"
