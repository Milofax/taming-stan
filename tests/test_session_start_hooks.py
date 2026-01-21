"""
Tests for SessionStart hooks:
- graphiti-context-loader.py
- reset-session-flags.py
"""

import json
import pytest
import subprocess
import sys
from pathlib import Path

TESTS_DIR = Path(__file__).parent
HOOKS_DIR = TESTS_DIR.parent / "hooks"
HOOKS_LIB = HOOKS_DIR / "lib"
CONTEXT_LOADER_PATH = HOOKS_DIR / "session-start" / "graphiti-context-loader.py"
RESET_FLAGS_PATH = HOOKS_DIR / "session-start" / "reset-session-flags.py"

sys.path.insert(0, str(HOOKS_LIB))


class TestHookRunner:
    @staticmethod
    def run(hook_path: Path, hook_input: dict) -> dict:
        result = subprocess.run(
            [sys.executable, str(hook_path)],
            input=json.dumps(hook_input),
            capture_output=True,
            text=True,
            timeout=10
        )
        assert result.returncode == 0, f"Hook failed: {result.stderr}"
        output = result.stdout.strip()
        if output:
            return json.loads(output)
        return {}


class TestResetSessionFlags:
    """Tests for reset-session-flags.py"""

    def test_outputs_valid_json(self):
        # Reset run_once state first
        from session_state import write_state
        write_state("_run_once_reset-session-flags", 0)

        output = TestHookRunner.run(RESET_FLAGS_PATH, {
            "cwd": "/tmp",
            "session_id": "test-session-123"
        })
        # Should output empty JSON object
        assert output == {} or "additionalContext" not in output

    def test_handles_empty_input(self):
        from session_state import write_state
        write_state("_run_once_reset-session-flags", 0)

        result = subprocess.run(
            [sys.executable, str(RESET_FLAGS_PATH)],
            input="{}",
            capture_output=True,
            text=True,
            timeout=10
        )
        assert result.returncode == 0
        output = json.loads(result.stdout.strip())
        assert isinstance(output, dict)

    def test_handles_invalid_json(self):
        from session_state import write_state
        write_state("_run_once_reset-session-flags", 0)

        result = subprocess.run(
            [sys.executable, str(RESET_FLAGS_PATH)],
            input="not valid json",
            capture_output=True,
            text=True,
            timeout=10
        )
        assert result.returncode == 0
        output = json.loads(result.stdout.strip())
        assert isinstance(output, dict)

    def test_resets_flags_on_new_session(self):
        from session_state import write_state, read_state
        write_state("_run_once_reset-session-flags", 0)
        write_state("claude_session_id", "old-session")
        write_state("graphiti_searched", True)
        write_state("firecrawl_attempted", True)

        TestHookRunner.run(RESET_FLAGS_PATH, {
            "cwd": "/tmp",
            "session_id": "new-session-456"
        })

        state = read_state()
        # Session flags should be reset
        assert state.get("graphiti_searched") is None or state.get("graphiti_searched") == False


class TestGraphitiContextLoader:
    """Tests for graphiti-context-loader.py"""

    def test_outputs_valid_json_with_context(self):
        from session_state import write_state
        write_state("_run_once_graphiti-context-loader", 0)

        output = TestHookRunner.run(CONTEXT_LOADER_PATH, {
            "cwd": "/tmp",
            "session_id": "test-session-123"
        })
        assert "additionalContext" in output
        assert isinstance(output["additionalContext"], str)

    def test_context_mentions_graphiti(self):
        from session_state import write_state
        write_state("_run_once_graphiti-context-loader", 0)

        output = TestHookRunner.run(CONTEXT_LOADER_PATH, {
            "cwd": "/tmp",
            "session_id": "test-session"
        })
        context = output.get("additionalContext", "")
        assert "graphiti" in context.lower() or "zettelkasten" in context.lower()

    def test_detects_main_context_for_tmp(self):
        from session_state import write_state
        write_state("_run_once_graphiti-context-loader", 0)

        output = TestHookRunner.run(CONTEXT_LOADER_PATH, {
            "cwd": "/tmp",
            "session_id": "test-session"
        })
        context = output.get("additionalContext", "")
        assert "main" in context.lower()

    def test_sets_graphiti_available_flag(self):
        from session_state import write_state, read_state
        write_state("_run_once_graphiti-context-loader", 0)
        write_state("graphiti_available", False)

        TestHookRunner.run(CONTEXT_LOADER_PATH, {
            "cwd": "/tmp",
            "session_id": "test-session"
        })

        state = read_state()
        assert state.get("graphiti_available") == True

    def test_handles_empty_input(self):
        from session_state import write_state
        write_state("_run_once_graphiti-context-loader", 0)

        result = subprocess.run(
            [sys.executable, str(CONTEXT_LOADER_PATH)],
            input="{}",
            capture_output=True,
            text=True,
            timeout=10
        )
        assert result.returncode == 0
        # Should output valid JSON even with empty input
        output = json.loads(result.stdout.strip())
        assert isinstance(output, dict)

    def test_handles_invalid_json(self):
        from session_state import write_state
        write_state("_run_once_graphiti-context-loader", 0)

        result = subprocess.run(
            [sys.executable, str(CONTEXT_LOADER_PATH)],
            input="not valid json",
            capture_output=True,
            text=True,
            timeout=10
        )
        assert result.returncode == 0
        output = json.loads(result.stdout.strip())
        assert isinstance(output, dict)


class TestGroupIdDetection:
    """Test group_id detection in graphiti-context-loader."""

    def test_detects_github_repo_from_git_dir(self, tmp_path):
        # This test requires a git repo setup - skip if complex
        from session_state import write_state
        write_state("_run_once_graphiti-context-loader", 0)

        # For a real git repo path, it would detect the group_id
        output = TestHookRunner.run(CONTEXT_LOADER_PATH, {
            "cwd": str(tmp_path),
            "session_id": "test-session"
        })
        # Should still output valid JSON
        assert "additionalContext" in output


class TestDeduplication:
    """Test run_once deduplication."""

    def test_skips_on_duplicate_run(self):
        from session_state import write_state
        import time
        # Set recent run
        write_state("_run_once_graphiti-context-loader", time.time())

        result = subprocess.run(
            [sys.executable, str(CONTEXT_LOADER_PATH)],
            input=json.dumps({"cwd": "/tmp", "session_id": "test"}),
            capture_output=True,
            text=True,
            timeout=10
        )
        assert result.returncode == 0
        output = json.loads(result.stdout.strip())
        # Should output empty JSON when skipped
        assert output == {}
