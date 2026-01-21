"""
Tests for hooks/post-tool-use/graphiti-retry-guard.py (3-Strikes Hook)

Tests the PostToolUse hook that tracks consecutive tool failures
and blocks after 3 failures until Graphiti is searched.

Edge cases covered:
- Success resets counter
- Different errors reset counter
- Same error increments counter
- 3rd failure triggers block
- Graphiti search allows retry
- Time window expiration resets counter
- Multiple tools tracked independently
"""

import json
import time
import hashlib
from pathlib import Path

import pytest
import sys
sys.path.insert(0, str(Path(__file__).parent.parent / "hooks" / "lib"))
sys.path.insert(0, str(Path(__file__).parent))
import session_state as ss
from helpers import make_post_tool_use_input


class TestSuccessCase:
    """Test cases when tool succeeds (no error)."""

    def test_success_returns_allow(self, graphiti_retry_guard_runner, clean_state):
        """Successful tool call should return allow."""
        hook_input = make_post_tool_use_input("Bash", tool_result="Success")

        result = graphiti_retry_guard_runner.run(hook_input)

        assert result["hookSpecificOutput"]["permissionDecision"] == "allow"

    def test_success_resets_counter(self, graphiti_retry_guard_runner, clean_state):
        """Success should reset failure counter for that tool."""
        # Set up: 2 failures
        ss.write_state("tool_failures", {
            "Bash": {"count": 2, "last_time": time.time(), "error_key": "abc123"}
        })

        # Success
        hook_input = make_post_tool_use_input("Bash", tool_result="Success")
        graphiti_retry_guard_runner.run(hook_input)

        state = ss.read_state()
        assert "Bash" not in state.get("tool_failures", {})

    def test_success_does_not_affect_other_tools(self, graphiti_retry_guard_runner, clean_state):
        """Success on one tool should not reset counter for other tools."""
        ss.write_state("tool_failures", {
            "Bash": {"count": 2, "last_time": time.time(), "error_key": "abc"},
            "Read": {"count": 1, "last_time": time.time(), "error_key": "xyz"}
        })

        # Bash succeeds
        hook_input = make_post_tool_use_input("Bash", tool_result="Success")
        graphiti_retry_guard_runner.run(hook_input)

        state = ss.read_state()
        assert "Bash" not in state["tool_failures"]
        assert state["tool_failures"]["Read"]["count"] == 1


class TestFailureCounter:
    """Test failure counter increments correctly."""

    def test_first_failure_allows(self, graphiti_retry_guard_runner, clean_state):
        """First failure should still allow."""
        hook_input = make_post_tool_use_input(
            "Bash",
            tool_error="Command not found: xyz"
        )

        result = graphiti_retry_guard_runner.run(hook_input)

        assert result["hookSpecificOutput"]["permissionDecision"] == "allow"

    def test_first_failure_increments_counter(self, graphiti_retry_guard_runner, clean_state):
        """First failure should set counter to 1."""
        hook_input = make_post_tool_use_input(
            "Bash",
            tool_error="Command not found"
        )
        graphiti_retry_guard_runner.run(hook_input)

        state = ss.read_state()
        assert state["tool_failures"]["Bash"]["count"] == 1

    def test_second_failure_allows(self, graphiti_retry_guard_runner, clean_state):
        """Second failure should still allow."""
        error = "Command not found"

        # First failure
        hook_input = make_post_tool_use_input("Bash", tool_error=error)
        graphiti_retry_guard_runner.run(hook_input)

        # Second failure (same error)
        result = graphiti_retry_guard_runner.run(hook_input)

        assert result["hookSpecificOutput"]["permissionDecision"] == "allow"

        state = ss.read_state()
        assert state["tool_failures"]["Bash"]["count"] == 2

    def test_third_failure_denies(self, graphiti_retry_guard_runner, clean_state):
        """Third failure with same error should deny."""
        error = "Permission denied"
        hook_input = make_post_tool_use_input("Bash", tool_error=error)

        # First two failures
        graphiti_retry_guard_runner.run(hook_input)
        graphiti_retry_guard_runner.run(hook_input)

        # Third failure
        result = graphiti_retry_guard_runner.run(hook_input)

        assert result["hookSpecificOutput"]["permissionDecision"] == "deny"
        assert "3-Strikes" in result["hookSpecificOutput"]["permissionDecisionReason"]

    def test_deny_message_contains_search_hint(self, graphiti_retry_guard_runner, clean_state):
        """Deny message should contain search_nodes hint."""
        error = "File not found"
        hook_input = make_post_tool_use_input("Bash", tool_error=error)

        # Trigger 3 failures
        for _ in range(3):
            result = graphiti_retry_guard_runner.run(hook_input)

        reason = result["hookSpecificOutput"]["permissionDecisionReason"]
        assert "search_nodes" in reason
        assert "Zettelkasten" in reason


class TestErrorKeyMatching:
    """Test that error key matching works correctly."""

    def test_different_error_resets_counter(self, graphiti_retry_guard_runner, clean_state):
        """Different error pattern should reset counter."""
        # Two failures with error A
        hook_input_a = make_post_tool_use_input("Bash", tool_error="Error type A")
        graphiti_retry_guard_runner.run(hook_input_a)
        graphiti_retry_guard_runner.run(hook_input_a)

        # One failure with error B
        hook_input_b = make_post_tool_use_input("Bash", tool_error="Error type B")
        result = graphiti_retry_guard_runner.run(hook_input_b)

        # Should allow (counter reset to 1)
        assert result["hookSpecificOutput"]["permissionDecision"] == "allow"

        state = ss.read_state()
        assert state["tool_failures"]["Bash"]["count"] == 1

    def test_same_error_prefix_counts(self, graphiti_retry_guard_runner, clean_state):
        """Errors with same first 50 chars should count together."""
        error_base = "This is a very long error message that exceeds fifty characters "
        error1 = error_base + "with suffix 1"
        error2 = error_base + "with suffix 2"

        hook_input1 = make_post_tool_use_input("Bash", tool_error=error1)
        hook_input2 = make_post_tool_use_input("Bash", tool_error=error2)

        # These should count as same error (first 50 chars match)
        graphiti_retry_guard_runner.run(hook_input1)
        graphiti_retry_guard_runner.run(hook_input2)
        result = graphiti_retry_guard_runner.run(hook_input1)

        assert result["hookSpecificOutput"]["permissionDecision"] == "deny"


class TestTimeWindow:
    """Test 5-minute time window behavior."""

    def test_failure_outside_window_resets(self, graphiti_retry_guard_runner, clean_state):
        """Failures outside 5-minute window should reset counter."""
        error = "Some error"

        # Set up: 2 failures 6 minutes ago
        old_time = time.time() - 360  # 6 minutes ago
        error_key = hashlib.md5(f"Bash:{error[:50]}".encode()).hexdigest()[:12]
        ss.write_state("tool_failures", {
            "Bash": {"count": 2, "last_time": old_time, "error_key": error_key}
        })

        # New failure
        hook_input = make_post_tool_use_input("Bash", tool_error=error)
        result = graphiti_retry_guard_runner.run(hook_input)

        # Should allow (counter reset due to time window)
        assert result["hookSpecificOutput"]["permissionDecision"] == "allow"

        state = ss.read_state()
        assert state["tool_failures"]["Bash"]["count"] == 1

    def test_failure_within_window_continues(self, graphiti_retry_guard_runner, clean_state):
        """Failures within 5-minute window should continue counting."""
        error = "Some error"

        # Set up: 2 failures 2 minutes ago
        recent_time = time.time() - 120  # 2 minutes ago
        error_key = hashlib.md5(f"Bash:{error[:50]}".encode()).hexdigest()[:12]
        ss.write_state("tool_failures", {
            "Bash": {"count": 2, "last_time": recent_time, "error_key": error_key}
        })

        # Third failure
        hook_input = make_post_tool_use_input("Bash", tool_error=error)
        result = graphiti_retry_guard_runner.run(hook_input)

        # Should deny (3rd failure)
        assert result["hookSpecificOutput"]["permissionDecision"] == "deny"


class TestGraphitiSearchBypass:
    """Test that Graphiti search allows retry."""

    def test_search_allows_retry_after_block(self, graphiti_retry_guard_runner, clean_state):
        """If Graphiti was searched, should allow retry even after 3 failures."""
        error = "Error message"
        hook_input = make_post_tool_use_input("Bash", tool_error=error)

        # Trigger 3 failures
        for _ in range(3):
            graphiti_retry_guard_runner.run(hook_input)

        # Mark Graphiti as searched
        ss.write_state("graphiti_searched", True)

        # 4th failure should now allow (searched)
        result = graphiti_retry_guard_runner.run(hook_input)
        assert result["hookSpecificOutput"]["permissionDecision"] == "allow"

    def test_no_search_continues_blocking(self, graphiti_retry_guard_runner, clean_state):
        """Without Graphiti search, should continue blocking."""
        error = "Error message"
        hook_input = make_post_tool_use_input("Bash", tool_error=error)

        # Trigger 4 failures
        for i in range(4):
            result = graphiti_retry_guard_runner.run(hook_input)

        # 4th failure should still deny
        assert result["hookSpecificOutput"]["permissionDecision"] == "deny"

    def test_group_ids_in_deny_message(self, graphiti_retry_guard_runner, clean_state):
        """Deny message should include active group_ids."""
        ss.write_state("active_group_ids", ["project-test", "main"])

        error = "Error"
        hook_input = make_post_tool_use_input("Bash", tool_error=error)

        for _ in range(3):
            result = graphiti_retry_guard_runner.run(hook_input)

        reason = result["hookSpecificOutput"]["permissionDecisionReason"]
        assert "main" in reason
        assert "project-test" in reason


class TestMultipleTools:
    """Test that multiple tools are tracked independently."""

    def test_different_tools_independent_counters(self, graphiti_retry_guard_runner, clean_state):
        """Different tools should have independent failure counters."""
        error = "Error"
        bash_input = make_post_tool_use_input("Bash", tool_error=error)
        read_input = make_post_tool_use_input("Read", tool_error=error)

        # 2 Bash failures
        graphiti_retry_guard_runner.run(bash_input)
        graphiti_retry_guard_runner.run(bash_input)

        # 1 Read failure - should not trigger block
        result = graphiti_retry_guard_runner.run(read_input)
        assert result["hookSpecificOutput"]["permissionDecision"] == "allow"

        # 3rd Bash failure - should trigger block
        result = graphiti_retry_guard_runner.run(bash_input)
        assert result["hookSpecificOutput"]["permissionDecision"] == "deny"

    def test_success_on_one_tool_does_not_reset_others(self, graphiti_retry_guard_runner, clean_state):
        """Success on tool A should not reset counter for tool B."""
        error = "Error"
        bash_input = make_post_tool_use_input("Bash", tool_error=error)
        bash_success = make_post_tool_use_input("Bash", tool_result="OK")
        read_input = make_post_tool_use_input("Read", tool_error=error)

        # 2 Read failures
        graphiti_retry_guard_runner.run(read_input)
        graphiti_retry_guard_runner.run(read_input)

        # Bash succeeds
        graphiti_retry_guard_runner.run(bash_success)

        # Read 3rd failure should still block
        result = graphiti_retry_guard_runner.run(read_input)
        assert result["hookSpecificOutput"]["permissionDecision"] == "deny"


class TestEdgeCases:
    """Edge cases and error handling."""

    def test_invalid_json_input_allows(self, graphiti_retry_guard_runner, clean_state):
        """Invalid JSON input should allow (fail-safe)."""
        import subprocess
        import sys as sys_module

        hook_path = Path(__file__).parent.parent / "hooks" / "post-tool-use" / "graphiti-retry-guard.py"
        result = subprocess.run(
            [sys_module.executable, str(hook_path)],
            input="not valid json",
            capture_output=True,
            text=True,
            timeout=10
        )

        output = json.loads(result.stdout)
        assert output["hookSpecificOutput"]["permissionDecision"] == "allow"

    def test_empty_tool_error_allows(self, graphiti_retry_guard_runner, clean_state):
        """Empty tool_error should be treated as success."""
        hook_input = make_post_tool_use_input("Bash", tool_error="")
        result = graphiti_retry_guard_runner.run(hook_input)
        assert result["hookSpecificOutput"]["permissionDecision"] == "allow"

    def test_none_tool_error_allows(self, graphiti_retry_guard_runner, clean_state):
        """None tool_error should be treated as success."""
        hook_input = {"tool_name": "Bash", "tool_result": "OK"}
        result = graphiti_retry_guard_runner.run(hook_input)
        assert result["hookSpecificOutput"]["permissionDecision"] == "allow"

    def test_very_long_error_truncated_in_message(self, graphiti_retry_guard_runner, clean_state):
        """Very long errors should be truncated in deny message."""
        error = "X" * 100  # Long error
        hook_input = make_post_tool_use_input("Bash", tool_error=error)

        for _ in range(3):
            result = graphiti_retry_guard_runner.run(hook_input)

        reason = result["hookSpecificOutput"]["permissionDecisionReason"]
        assert "..." in reason  # Truncated
        assert len(reason) < 500  # Reasonable length

    def test_hook_registers_itself(self, graphiti_retry_guard_runner, clean_state):
        """Hook should register itself in hooks_active."""
        hook_input = make_post_tool_use_input("Bash", tool_result="OK")
        graphiti_retry_guard_runner.run(hook_input)

        state = ss.read_state()
        assert state.get("hooks_active", {}).get("graphiti-retry") is True
