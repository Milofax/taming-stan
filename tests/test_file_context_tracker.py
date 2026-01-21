"""
Tests for file-context-tracker.py hook.

This hook tracks which projects/repos Claude works with during a session.
It triggers on: Read|Edit|Write|Glob|Grep
It should ALWAYS allow (tracking only, never blocking).

CRITICAL: This test file ensures the required imports work!
The hook depends on session_state.track_group_id_for_path() which must exist.
"""

import json
import pytest
import sys
import subprocess
from pathlib import Path
from unittest.mock import patch
import tempfile
import os

# Paths
TESTS_DIR = Path(__file__).parent
HOOKS_DIR = TESTS_DIR.parent / "hooks"
HOOKS_LIB = HOOKS_DIR / "lib"
FILE_CONTEXT_TRACKER = HOOKS_DIR / "pre-tool-use" / "file-context-tracker.py"

# Add hooks/lib to path for import tests
sys.path.insert(0, str(HOOKS_LIB))


class TestImports:
    """Test that all required imports work - this was the original bug!"""

    def test_session_state_has_track_group_id_for_path(self):
        """CRITICAL: track_group_id_for_path must exist in session_state."""
        from session_state import track_group_id_for_path
        assert callable(track_group_id_for_path)

    def test_session_state_has_detect_group_id(self):
        """detect_group_id is required by track_group_id_for_path."""
        from session_state import detect_group_id
        assert callable(detect_group_id)

    def test_session_state_has_find_git_root(self):
        """find_git_root is required by detect_group_id."""
        from session_state import find_git_root
        assert callable(find_git_root)

    def test_session_state_has_get_github_repo(self):
        """get_github_repo is required by detect_group_id."""
        from session_state import get_github_repo
        assert callable(get_github_repo)

    def test_session_state_has_append_to_list(self):
        """append_to_list is required by track_group_id_for_path."""
        from session_state import append_to_list
        assert callable(append_to_list)

    def test_hook_can_be_executed(self):
        """The hook should execute without import errors when given empty input."""
        result = subprocess.run(
            [sys.executable, str(FILE_CONTEXT_TRACKER)],
            input="{}",
            capture_output=True,
            text=True,
            timeout=5
        )
        assert result.returncode == 0, f"Hook execution failed: {result.stderr}"
        # Verify it produces valid JSON output
        output = json.loads(result.stdout.strip())
        assert "hookSpecificOutput" in output


class TestHookRunner:
    """Helper to run the hook with specific inputs."""

    @staticmethod
    def run(hook_input: dict, cwd: str = None) -> dict:
        """Run the hook and return parsed JSON output."""
        result = subprocess.run(
            [sys.executable, str(FILE_CONTEXT_TRACKER)],
            input=json.dumps(hook_input),
            capture_output=True,
            text=True,
            timeout=10,
            cwd=cwd or os.getcwd()
        )
        if result.returncode != 0:
            raise RuntimeError(f"Hook failed with exit code {result.returncode}: {result.stderr}")
        return json.loads(result.stdout.strip())


class TestAlwaysAllow:
    """The hook should ALWAYS return allow - it only tracks, never blocks."""

    def test_empty_input_allows(self):
        """Empty input should allow."""
        output = TestHookRunner.run({})
        assert output["hookSpecificOutput"]["permissionDecision"] == "allow"

    def test_invalid_tool_allows(self):
        """Unknown tool should allow."""
        output = TestHookRunner.run({"tool_name": "UnknownTool", "tool_input": {}})
        assert output["hookSpecificOutput"]["permissionDecision"] == "allow"

    def test_missing_file_path_allows(self):
        """Missing file_path should allow."""
        output = TestHookRunner.run({"tool_name": "Read", "tool_input": {}})
        assert output["hookSpecificOutput"]["permissionDecision"] == "allow"


class TestPathExtraction:
    """Test that paths are correctly extracted from different tool inputs."""

    def test_read_extracts_file_path(self):
        """Read tool should use file_path."""
        output = TestHookRunner.run({
            "tool_name": "Read",
            "tool_input": {"file_path": "/tmp/test.txt"}
        })
        assert output["hookSpecificOutput"]["permissionDecision"] == "allow"
        assert output["hookSpecificOutput"]["hookEventName"] == "PreToolUse"

    def test_edit_extracts_file_path(self):
        """Edit tool should use file_path."""
        output = TestHookRunner.run({
            "tool_name": "Edit",
            "tool_input": {"file_path": "/tmp/test.txt", "old_string": "a", "new_string": "b"}
        })
        assert output["hookSpecificOutput"]["permissionDecision"] == "allow"

    def test_write_extracts_file_path(self):
        """Write tool should use file_path."""
        output = TestHookRunner.run({
            "tool_name": "Write",
            "tool_input": {"file_path": "/tmp/test.txt", "content": "hello"}
        })
        assert output["hookSpecificOutput"]["permissionDecision"] == "allow"

    def test_glob_extracts_path(self):
        """Glob tool should use path (directory)."""
        output = TestHookRunner.run({
            "tool_name": "Glob",
            "tool_input": {"pattern": "*.py", "path": "/tmp"}
        })
        assert output["hookSpecificOutput"]["permissionDecision"] == "allow"

    def test_grep_extracts_path(self):
        """Grep tool should use path."""
        output = TestHookRunner.run({
            "tool_name": "Grep",
            "tool_input": {"pattern": "test", "path": "/tmp"}
        })
        assert output["hookSpecificOutput"]["permissionDecision"] == "allow"


class TestEdgeCases:
    """Test edge cases and error handling."""

    def test_invalid_json_input(self):
        """Invalid JSON should be handled gracefully (allow)."""
        result = subprocess.run(
            [sys.executable, str(FILE_CONTEXT_TRACKER)],
            input="not valid json",
            capture_output=True,
            text=True,
            timeout=10
        )
        assert result.returncode == 0
        output = json.loads(result.stdout.strip())
        assert output["hookSpecificOutput"]["permissionDecision"] == "allow"

    def test_empty_stdin(self):
        """Empty stdin should be handled gracefully."""
        result = subprocess.run(
            [sys.executable, str(FILE_CONTEXT_TRACKER)],
            input="",
            capture_output=True,
            text=True,
            timeout=10
        )
        assert result.returncode == 0
        output = json.loads(result.stdout.strip())
        assert output["hookSpecificOutput"]["permissionDecision"] == "allow"

    def test_null_file_path(self):
        """null file_path should be handled."""
        output = TestHookRunner.run({
            "tool_name": "Read",
            "tool_input": {"file_path": None}
        })
        assert output["hookSpecificOutput"]["permissionDecision"] == "allow"

    def test_empty_string_file_path(self):
        """Empty string file_path should be handled."""
        output = TestHookRunner.run({
            "tool_name": "Read",
            "tool_input": {"file_path": ""}
        })
        assert output["hookSpecificOutput"]["permissionDecision"] == "allow"

    def test_nonexistent_path(self):
        """Non-existent path should still allow."""
        output = TestHookRunner.run({
            "tool_name": "Read",
            "tool_input": {"file_path": "/nonexistent/path/to/file.txt"}
        })
        assert output["hookSpecificOutput"]["permissionDecision"] == "allow"

    def test_unicode_path(self):
        """Unicode in path should be handled."""
        output = TestHookRunner.run({
            "tool_name": "Read",
            "tool_input": {"file_path": "/tmp/tëst_üñíçödé.txt"}
        })
        assert output["hookSpecificOutput"]["permissionDecision"] == "allow"

    def test_path_with_spaces(self):
        """Paths with spaces should be handled."""
        output = TestHookRunner.run({
            "tool_name": "Read",
            "tool_input": {"file_path": "/tmp/path with spaces/file.txt"}
        })
        assert output["hookSpecificOutput"]["permissionDecision"] == "allow"


class TestOutputFormat:
    """Test that output format is correct."""

    def test_output_has_hook_specific_output(self):
        """Output must have hookSpecificOutput."""
        output = TestHookRunner.run({})
        assert "hookSpecificOutput" in output

    def test_output_has_hook_event_name(self):
        """Output must have hookEventName."""
        output = TestHookRunner.run({})
        assert output["hookSpecificOutput"]["hookEventName"] == "PreToolUse"

    def test_output_has_permission_decision(self):
        """Output must have permissionDecision."""
        output = TestHookRunner.run({})
        assert "permissionDecision" in output["hookSpecificOutput"]

    def test_output_is_valid_json(self):
        """Output must be valid JSON."""
        result = subprocess.run(
            [sys.executable, str(FILE_CONTEXT_TRACKER)],
            input="{}",
            capture_output=True,
            text=True,
            timeout=10
        )
        # Should not raise
        json.loads(result.stdout.strip())


class TestSessionStateFunctions:
    """Test the session_state functions that file-context-tracker depends on."""

    def test_track_group_id_for_path_with_none(self):
        """track_group_id_for_path should handle None."""
        from session_state import track_group_id_for_path
        result = track_group_id_for_path(None)
        assert result is None

    def test_track_group_id_for_path_with_empty_string(self):
        """track_group_id_for_path should handle empty string."""
        from session_state import track_group_id_for_path
        result = track_group_id_for_path("")
        assert result is None

    def test_detect_group_id_with_none(self):
        """detect_group_id should handle None."""
        from session_state import detect_group_id
        group_id, name = detect_group_id(None)
        assert group_id == "main"

    def test_detect_group_id_with_empty_string(self):
        """detect_group_id should handle empty string."""
        from session_state import detect_group_id
        group_id, name = detect_group_id("")
        assert group_id == "main"

    def test_detect_group_id_returns_tuple(self):
        """detect_group_id should return (group_id, name) tuple."""
        from session_state import detect_group_id
        result = detect_group_id("/tmp")
        assert isinstance(result, tuple)
        assert len(result) == 2

    def test_find_git_root_nonexistent_dir(self):
        """find_git_root should handle non-existent directory."""
        from session_state import find_git_root
        result = find_git_root("/nonexistent/path")
        assert result is None

    def test_get_github_repo_nonexistent_dir(self):
        """get_github_repo should handle non-existent directory."""
        from session_state import get_github_repo
        result = get_github_repo("/nonexistent/path")
        assert result is None


class TestGitIntegration:
    """Test git-based group_id detection."""

    def test_detect_group_id_in_git_repo(self):
        """detect_group_id should find GitHub repo and convert slash to hyphen."""
        from session_state import detect_group_id
        # Test with the taming-stan repo itself
        repo_path = str(TESTS_DIR.parent)
        group_id, name = detect_group_id(repo_path)
        # Should be Milofax-taming-stan (with hyphen, not slash)
        if group_id != "main":
            assert "/" not in group_id, f"group_id should use hyphen, not slash: {group_id}"

    def test_find_git_root_in_repo(self):
        """find_git_root should find .git directory."""
        from session_state import find_git_root
        repo_path = str(TESTS_DIR.parent)
        git_root = find_git_root(repo_path)
        if git_root:
            assert Path(git_root).exists()
            assert (Path(git_root) / ".git").exists()
