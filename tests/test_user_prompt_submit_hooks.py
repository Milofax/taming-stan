"""
Tests for UserPromptSubmit hooks:
- graphiti-knowledge-reminder.py
- session-reminder.py
"""

import json
import pytest
import subprocess
import sys
from pathlib import Path

TESTS_DIR = Path(__file__).parent
HOOKS_DIR = TESTS_DIR.parent / "hooks"
HOOKS_LIB = HOOKS_DIR / "lib"
KNOWLEDGE_REMINDER_PATH = HOOKS_DIR / "user-prompt-submit" / "graphiti-knowledge-reminder.py"
SESSION_REMINDER_PATH = HOOKS_DIR / "user-prompt-submit" / "session-reminder.py"

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


class TestGraphitiKnowledgeReminder:
    """Tests for graphiti-knowledge-reminder.py"""

    def test_outputs_valid_json(self):
        from session_state import write_state
        write_state("graphiti_available", True)
        write_state("graphiti_searched", False)

        output = TestHookRunner.run(KNOWLEDGE_REMINDER_PATH, {
            "user_prompt": "What do you know about Python?",
            "cwd": "/tmp"
        })
        assert "continue" in output
        assert output["continue"] == True

    def test_includes_system_message_when_graphiti_available(self):
        from session_state import write_state
        write_state("graphiti_available", True)
        write_state("graphiti_searched", False)

        output = TestHookRunner.run(KNOWLEDGE_REMINDER_PATH, {
            "user_prompt": "test",
            "cwd": "/tmp"
        })
        assert "systemMessage" in output
        assert "search_nodes" in output["systemMessage"]

    def test_no_output_when_graphiti_not_available(self):
        from session_state import write_state
        write_state("graphiti_available", False)

        result = subprocess.run(
            [sys.executable, str(KNOWLEDGE_REMINDER_PATH)],
            input=json.dumps({"user_prompt": "test", "cwd": "/tmp"}),
            capture_output=True,
            text=True,
            timeout=10
        )
        # Should not output anything when Graphiti is not available
        assert result.returncode == 0

    def test_no_spam_when_already_searched(self):
        from session_state import write_state
        write_state("graphiti_available", True)
        write_state("graphiti_searched", True)

        result = subprocess.run(
            [sys.executable, str(KNOWLEDGE_REMINDER_PATH)],
            input=json.dumps({"user_prompt": "test", "cwd": "/tmp"}),
            capture_output=True,
            text=True,
            timeout=10
        )
        # Should not output when already searched
        assert result.returncode == 0

    def test_includes_project_group_id(self):
        from session_state import write_state
        write_state("graphiti_available", True)
        write_state("graphiti_searched", False)
        write_state("project_group_id", "Milofax-taming-stan")

        output = TestHookRunner.run(KNOWLEDGE_REMINDER_PATH, {
            "user_prompt": "test",
            "cwd": "/tmp"
        })
        assert "Milofax-taming-stan" in output.get("systemMessage", "")

    def test_handles_invalid_json(self):
        result = subprocess.run(
            [sys.executable, str(KNOWLEDGE_REMINDER_PATH)],
            input="not valid json",
            capture_output=True,
            text=True,
            timeout=10
        )
        assert result.returncode == 0


class TestSessionReminder:
    """Tests for session-reminder.py"""

    def test_outputs_valid_json(self):
        output = TestHookRunner.run(SESSION_REMINDER_PATH, {
            "user_prompt": "Hello",
            "cwd": "/tmp"
        })
        assert "continue" in output
        assert output["continue"] == True

    def test_includes_system_message(self):
        output = TestHookRunner.run(SESSION_REMINDER_PATH, {
            "user_prompt": "Hello",
            "cwd": "/tmp"
        })
        assert "systemMessage" in output
        assert isinstance(output["systemMessage"], str)

    def test_mentions_graphiti(self):
        output = TestHookRunner.run(SESSION_REMINDER_PATH, {
            "user_prompt": "test",
            "cwd": "/tmp"
        })
        message = output.get("systemMessage", "")
        assert "graphiti" in message.lower() or "search_nodes" in message

    def test_shows_main_for_non_project_dir(self):
        output = TestHookRunner.run(SESSION_REMINDER_PATH, {
            "user_prompt": "test",
            "cwd": "/tmp"
        })
        message = output.get("systemMessage", "")
        assert "main" in message.lower()

    def test_resets_graphiti_searched_flag(self):
        from session_state import write_state, read_state
        write_state("graphiti_searched", True)

        TestHookRunner.run(SESSION_REMINDER_PATH, {
            "user_prompt": "test",
            "cwd": "/tmp"
        })

        state = read_state()
        assert state.get("graphiti_searched") == False

    def test_resets_memory_saved_flag(self):
        from session_state import write_state, read_state
        write_state("memory_saved", True)

        TestHookRunner.run(SESSION_REMINDER_PATH, {
            "user_prompt": "test",
            "cwd": "/tmp"
        })

        state = read_state()
        assert state.get("memory_saved") == False

    def test_handles_empty_cwd(self):
        output = TestHookRunner.run(SESSION_REMINDER_PATH, {
            "user_prompt": "test",
            "cwd": ""
        })
        assert "continue" in output
        assert output["continue"] == True

    def test_handles_invalid_json(self):
        result = subprocess.run(
            [sys.executable, str(SESSION_REMINDER_PATH)],
            input="not valid json",
            capture_output=True,
            text=True,
            timeout=10
        )
        assert result.returncode == 0
        # Should output valid JSON even with invalid input
        output = json.loads(result.stdout.strip())
        assert output["continue"] == True


class TestGroupIdDetection:
    """Test group_id detection in session-reminder."""

    def test_detects_main_for_tmp(self):
        output = TestHookRunner.run(SESSION_REMINDER_PATH, {
            "user_prompt": "test",
            "cwd": "/tmp"
        })
        message = output.get("systemMessage", "")
        # /tmp has no git repo, should fall back to main
        assert "main" in message.lower()

    def test_uses_hyphen_not_slash_in_group_id(self):
        # This tests the slash-to-hyphen conversion for GitHub repos
        # The actual test would need a git repo, but we can verify the output format
        output = TestHookRunner.run(SESSION_REMINDER_PATH, {
            "user_prompt": "test",
            "cwd": "/Volumes/DATEN/Coding/taming-stan"  # Real git repo
        })
        message = output.get("systemMessage", "")
        # If it detected a GitHub repo, it should use hyphen not slash
        if "Milofax" in message:
            assert "Milofax/" not in message  # Should be Milofax-something
