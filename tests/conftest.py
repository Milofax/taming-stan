"""
Shared fixtures for hook tests.

Best practices:
- Each test gets a fresh, isolated state file
- Fixtures mock stdin for hook input
- Fixtures capture stdout for output validation
"""

import json
import os
import sys
import tempfile
from pathlib import Path
from typing import Any
from unittest.mock import patch
import pytest

# Add hooks/lib and tests directory to path for imports
TESTS_DIR = Path(__file__).parent
HOOKS_LIB = TESTS_DIR.parent / "hooks" / "lib"
sys.path.insert(0, str(HOOKS_LIB))
sys.path.insert(0, str(TESTS_DIR))


@pytest.fixture
def temp_state_dir(tmp_path):
    """Create a temporary directory for state files."""
    return tmp_path


@pytest.fixture
def mock_cwd(temp_state_dir):
    """Mock os.getcwd() to return a consistent path for state file isolation."""
    with patch("os.getcwd", return_value=str(temp_state_dir)):
        yield temp_state_dir


@pytest.fixture
def clean_state(mock_cwd, temp_state_dir):
    """
    Ensure a clean state file for each test.
    Returns the path to the state file.
    """
    import hashlib
    cwd_hash = hashlib.md5(str(temp_state_dir).encode()).hexdigest()[:8]
    state_path = Path(f"/tmp/claude-session-state-{cwd_hash}.json")

    # Clean up before test
    if state_path.exists():
        state_path.unlink()
    lock_path = Path(f"{state_path}.lock")
    if lock_path.exists():
        lock_path.unlink()

    yield state_path

    # Clean up after test
    if state_path.exists():
        state_path.unlink()
    if lock_path.exists():
        lock_path.unlink()


@pytest.fixture
def state_with_data(clean_state):
    """
    Factory fixture to create state with specific data.
    Usage: state_with_data({"key": "value"})
    """
    def _create_state(data: dict):
        clean_state.write_text(json.dumps(data, indent=2))
        return clean_state
    return _create_state


class HookRunner:
    """
    Helper class to run hooks with mocked stdin and capture stdout.
    """

    def __init__(self, hook_module_path: Path):
        self.hook_path = hook_module_path
        self.module_name = hook_module_path.stem.replace("-", "_")

    def run(self, hook_input: dict) -> dict:
        """
        Run the hook with given input and return parsed JSON output.

        Args:
            hook_input: Dict to pass as JSON via stdin

        Returns:
            Parsed JSON output from hook
        """
        import subprocess

        result = subprocess.run(
            [sys.executable, str(self.hook_path)],
            input=json.dumps(hook_input),
            capture_output=True,
            text=True,
            timeout=10,
            cwd=os.getcwd()  # Use current (mocked) cwd
        )

        if result.returncode != 0:
            raise RuntimeError(f"Hook failed: {result.stderr}")

        stdout = result.stdout.strip()
        if not stdout:
            return {}

        try:
            return json.loads(stdout)
        except json.JSONDecodeError:
            # Some hooks output plain text (e.g., SessionStart)
            return {"_raw_output": stdout}

    def run_raw(self, hook_input: dict) -> str:
        """Run hook and return raw stdout (for SessionStart hooks)."""
        import subprocess

        result = subprocess.run(
            [sys.executable, str(self.hook_path)],
            input=json.dumps(hook_input),
            capture_output=True,
            text=True,
            timeout=10,
            cwd=os.getcwd()
        )

        return result.stdout


@pytest.fixture
def hook_runner():
    """
    Factory fixture to create a HookRunner for a specific hook.
    Usage: hook_runner(Path("hooks/pre-tool-use/graphiti-guard.py"))
    """
    def _create_runner(hook_path: Path) -> HookRunner:
        return HookRunner(hook_path)
    return _create_runner


# ============================================================================
# Hook-specific fixtures
# ============================================================================

HOOKS_DIR = Path(__file__).parent.parent / "hooks"


@pytest.fixture
def graphiti_retry_guard_runner(hook_runner, mock_cwd):
    """Runner for graphiti-retry-guard.py (PostToolUse)."""
    return hook_runner(HOOKS_DIR / "post-tool-use" / "graphiti-retry-guard.py")


@pytest.fixture
def graphiti_guard_runner(hook_runner, mock_cwd):
    """Runner for graphiti-guard.py (PreToolUse)."""
    return hook_runner(HOOKS_DIR / "pre-tool-use" / "graphiti-guard.py")


@pytest.fixture
def graphiti_first_guard_runner(hook_runner, mock_cwd):
    """Runner for graphiti-first-guard.py (PreToolUse)."""
    return hook_runner(HOOKS_DIR / "pre-tool-use" / "graphiti-first-guard.py")


@pytest.fixture
def session_reminder_runner(hook_runner, mock_cwd):
    """Runner for session-reminder.py (UserPromptSubmit)."""
    return hook_runner(HOOKS_DIR / "user-prompt-submit" / "session-reminder.py")


@pytest.fixture
def context_loader_runner(hook_runner, mock_cwd):
    """Runner for graphiti-context-loader.py (SessionStart)."""
    return hook_runner(HOOKS_DIR / "session-start" / "graphiti-context-loader.py")


# ============================================================================
# Common input factories
# ============================================================================

def make_bridge_input(tool: str, arguments: dict) -> dict:
    """Create standard bridge_tool_request input."""
    return {
        "tool_name": "mcp__mcp-funnel__bridge_tool_request",
        "tool_input": {
            "tool": tool,
            "arguments": arguments
        }
    }


def make_add_memory_input(
    name: str,
    episode_body: str,
    source_description: str = "Test source",
    group_id: str = ""
) -> dict:
    """Create input for add_memory via bridge."""
    args = {
        "name": name,
        "episode_body": episode_body,
        "source_description": source_description,
    }
    if group_id:
        args["group_id"] = group_id
    return make_bridge_input("graphiti__add_memory", args)


def make_search_nodes_input(
    query: str,
    group_ids: list[str] | None = None,
    entity_types: list[str] | None = None
) -> dict:
    """Create input for search_nodes via bridge."""
    args = {"query": query}
    if group_ids:
        args["group_ids"] = group_ids
    if entity_types:
        args["entity_types"] = entity_types
    return make_bridge_input("graphiti__search_nodes", args)


def make_post_tool_use_input(
    tool_name: str,
    tool_result: str = "",
    tool_error: str | None = None
) -> dict:
    """Create PostToolUse hook input."""
    result = {
        "tool_name": tool_name,
        "tool_result": tool_result,
    }
    if tool_error:
        result["tool_error"] = tool_error
    return result
