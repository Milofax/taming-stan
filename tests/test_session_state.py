"""
Tests for hooks/lib/session_state.py

Tests the shared session state management used by all hooks.
"""

import json
import hashlib
import time
from pathlib import Path
from unittest.mock import patch

import pytest

# Import module under test
import sys
sys.path.insert(0, str(Path(__file__).parent.parent / "hooks" / "lib"))
import session_state as ss


class TestGetSessionId:
    """Tests for get_session_id() function."""

    def test_returns_string_with_state_prefix(self, mock_cwd):
        """Session ID should start with 'state-'."""
        result = ss.get_session_id()
        assert result.startswith("state-")

    def test_hash_based_on_cwd(self, mock_cwd, temp_state_dir):
        """Session ID hash should be based on cwd."""
        expected_hash = hashlib.md5(str(temp_state_dir).encode()).hexdigest()[:8]
        result = ss.get_session_id()
        assert result == f"state-{expected_hash}"

    def test_different_cwd_gives_different_id(self, temp_state_dir):
        """Different cwds should produce different session IDs."""
        with patch("os.getcwd", return_value="/path/one"):
            id1 = ss.get_session_id()

        with patch("os.getcwd", return_value="/path/two"):
            id2 = ss.get_session_id()

        assert id1 != id2


class TestGetStatePath:
    """Tests for get_state_path() function."""

    def test_returns_path_in_tmp(self, mock_cwd):
        """State file should be in /tmp."""
        result = ss.get_state_path()
        assert str(result).startswith("/tmp/claude-session-")

    def test_path_contains_session_id(self, mock_cwd):
        """State path should contain the session ID."""
        session_id = ss.get_session_id()
        state_path = ss.get_state_path()
        assert session_id in str(state_path)


class TestReadWriteState:
    """Tests for read_state() and write_state() functions."""

    def test_read_empty_state(self, clean_state):
        """Reading non-existent state should return empty dict."""
        result = ss.read_state()
        assert result == {}

    def test_write_and_read_state(self, clean_state):
        """Should be able to write and read back state."""
        ss.write_state("test_key", "test_value")
        result = ss.read_state()
        assert result.get("test_key") == "test_value"

    def test_write_preserves_existing_keys(self, clean_state):
        """Writing a new key should preserve existing keys."""
        ss.write_state("key1", "value1")
        ss.write_state("key2", "value2")

        result = ss.read_state()
        assert result.get("key1") == "value1"
        assert result.get("key2") == "value2"

    def test_write_overwrites_existing_key(self, clean_state):
        """Writing to existing key should overwrite."""
        ss.write_state("key", "old_value")
        ss.write_state("key", "new_value")

        result = ss.read_state()
        assert result.get("key") == "new_value"

    def test_write_complex_values(self, clean_state):
        """Should handle complex values (dict, list)."""
        ss.write_state("dict_key", {"nested": "value"})
        ss.write_state("list_key", [1, 2, 3])

        result = ss.read_state()
        assert result.get("dict_key") == {"nested": "value"}
        assert result.get("list_key") == [1, 2, 3]


class TestRegisterHook:
    """Tests for register_hook() function."""

    def test_register_hook_creates_hooks_active(self, clean_state):
        """Registering a hook should create hooks_active dict."""
        ss.register_hook("test-hook")
        result = ss.read_state()
        assert "hooks_active" in result
        assert result["hooks_active"].get("test-hook") is True

    def test_register_multiple_hooks(self, clean_state):
        """Should be able to register multiple hooks."""
        ss.register_hook("hook1")
        ss.register_hook("hook2")

        result = ss.read_state()
        assert result["hooks_active"].get("hook1") is True
        assert result["hooks_active"].get("hook2") is True


class TestIsHookActive:
    """Tests for is_hook_active() function."""

    def test_inactive_hook(self, clean_state):
        """Non-registered hook should return False."""
        assert ss.is_hook_active("unknown-hook") is False

    def test_active_hook(self, clean_state):
        """Registered hook should return True."""
        ss.register_hook("my-hook")
        assert ss.is_hook_active("my-hook") is True


class TestRunOnce:
    """Tests for run_once() function (deduplication)."""

    def test_first_run_returns_true(self, clean_state):
        """First run should return True."""
        assert ss.run_once("unique-hook") is True

    def test_second_run_within_ttl_returns_false(self, clean_state):
        """Second run within TTL should return False."""
        ss.run_once("test-hook", ttl_seconds=5.0)
        result = ss.run_once("test-hook", ttl_seconds=5.0)
        assert result is False

    def test_run_after_ttl_returns_true(self, clean_state):
        """Run after TTL expires should return True."""
        ss.run_once("test-hook", ttl_seconds=0.1)
        time.sleep(0.15)
        result = ss.run_once("test-hook", ttl_seconds=0.1)
        assert result is True

    def test_different_hooks_independent(self, clean_state):
        """Different hook names should be independent."""
        ss.run_once("hook-a")
        result = ss.run_once("hook-b")
        assert result is True


class TestAppendToList:
    """Tests for append_to_list() function."""

    def test_append_to_new_list(self, clean_state):
        """Should create list if it doesn't exist."""
        ss.append_to_list("my_list", "item1")
        result = ss.read_state()
        assert result.get("my_list") == ["item1"]

    def test_append_to_existing_list(self, clean_state):
        """Should append to existing list."""
        ss.append_to_list("my_list", "item1")
        ss.append_to_list("my_list", "item2")

        result = ss.read_state()
        assert result.get("my_list") == ["item1", "item2"]

    def test_no_duplicates(self, clean_state):
        """Should not add duplicates."""
        ss.append_to_list("my_list", "item1")
        ss.append_to_list("my_list", "item1")

        result = ss.read_state()
        assert result.get("my_list") == ["item1"]


class TestResetSessionFlags:
    """Tests for reset_session_flags() function."""

    def test_resets_all_session_flags(self, clean_state):
        """Should reset all flags defined in SESSION_FLAGS."""
        # Set up flags
        ss.write_state("graphiti_searched", True)
        ss.write_state("firecrawl_attempted", True)
        ss.write_state("other_key", "should_remain")

        ss.reset_session_flags()

        result = ss.read_state()
        assert "graphiti_searched" not in result
        assert "firecrawl_attempted" not in result
        assert result.get("other_key") == "should_remain"


class TestCheckAndUpdateSession:
    """Tests for check_and_update_session() function."""

    def test_new_session_resets_flags(self, clean_state):
        """New session ID should reset flags."""
        ss.write_state("graphiti_searched", True)

        result = ss.check_and_update_session("new-session-123")

        assert result is True
        state = ss.read_state()
        assert "graphiti_searched" not in state
        assert state.get("claude_session_id") == "new-session-123"

    def test_same_session_does_not_reset(self, clean_state):
        """Same session ID should not reset flags."""
        ss.write_state("claude_session_id", "session-abc")
        ss.write_state("graphiti_searched", True)

        result = ss.check_and_update_session("session-abc")

        assert result is False
        state = ss.read_state()
        assert state.get("graphiti_searched") is True
