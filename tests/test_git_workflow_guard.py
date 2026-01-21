"""
Tests for git-workflow-guard.py hook.

This hook enforces:
- Conventional Commits format
- Branch protection (no direct push to main/develop)
- Force push protection
"""

import json
import pytest
import subprocess
import sys
from pathlib import Path

TESTS_DIR = Path(__file__).parent
HOOKS_DIR = TESTS_DIR.parent / "hooks"
HOOKS_LIB = HOOKS_DIR / "lib"
HOOK_PATH = HOOKS_DIR / "pre-tool-use" / "git-workflow-guard.py"

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


class TestNonGitCommandsAllowed:
    """Non-git commands should always be allowed."""

    def test_ls_allows(self):
        output = TestHookRunner.run({"tool_name": "Bash", "tool_input": {"command": "ls -la"}})
        assert output["hookSpecificOutput"]["permissionDecision"] == "allow"

    def test_npm_allows(self):
        output = TestHookRunner.run({"tool_name": "Bash", "tool_input": {"command": "npm install"}})
        assert output["hookSpecificOutput"]["permissionDecision"] == "allow"

    def test_read_tool_allows(self):
        output = TestHookRunner.run({"tool_name": "Read", "tool_input": {"file_path": "/tmp/test"}})
        assert output["hookSpecificOutput"]["permissionDecision"] == "allow"

    def test_empty_input_allows(self):
        output = TestHookRunner.run({})
        assert output["hookSpecificOutput"]["permissionDecision"] == "allow"


class TestConventionalCommitsValid:
    """Valid conventional commit messages should be allowed."""

    def test_feat_commit(self):
        output = TestHookRunner.run({
            "tool_name": "Bash",
            "tool_input": {"command": 'git commit -m "feat: add new feature"'}
        })
        assert output["hookSpecificOutput"]["permissionDecision"] == "allow"

    def test_fix_commit_with_scope(self):
        output = TestHookRunner.run({
            "tool_name": "Bash",
            "tool_input": {"command": 'git commit -m "fix(api): handle null response"'}
        })
        assert output["hookSpecificOutput"]["permissionDecision"] == "allow"

    def test_docs_commit(self):
        output = TestHookRunner.run({
            "tool_name": "Bash",
            "tool_input": {"command": 'git commit -m "docs: update README"'}
        })
        assert output["hookSpecificOutput"]["permissionDecision"] == "allow"

    def test_breaking_change_commit(self):
        output = TestHookRunner.run({
            "tool_name": "Bash",
            "tool_input": {"command": 'git commit -m "feat!: breaking API change"'}
        })
        assert output["hookSpecificOutput"]["permissionDecision"] == "allow"

    def test_chore_commit(self):
        output = TestHookRunner.run({
            "tool_name": "Bash",
            "tool_input": {"command": 'git commit -m "chore: update dependencies"'}
        })
        assert output["hookSpecificOutput"]["permissionDecision"] == "allow"


class TestConventionalCommitsInvalid:
    """Invalid commit messages should be denied."""

    def test_no_type_denied(self):
        output = TestHookRunner.run({
            "tool_name": "Bash",
            "tool_input": {"command": 'git commit -m "add new feature"'}
        })
        assert output["hookSpecificOutput"]["permissionDecision"] == "deny"
        assert "conventional" in output["hookSpecificOutput"]["permissionDecisionReason"].lower()

    def test_invalid_type_denied(self):
        output = TestHookRunner.run({
            "tool_name": "Bash",
            "tool_input": {"command": 'git commit -m "feature: add something"'}
        })
        assert output["hookSpecificOutput"]["permissionDecision"] == "deny"

    def test_missing_colon_space_denied(self):
        output = TestHookRunner.run({
            "tool_name": "Bash",
            "tool_input": {"command": 'git commit -m "feat:add feature"'}
        })
        assert output["hookSpecificOutput"]["permissionDecision"] == "deny"

    def test_wip_denied(self):
        output = TestHookRunner.run({
            "tool_name": "Bash",
            "tool_input": {"command": 'git commit -m "WIP"'}
        })
        assert output["hookSpecificOutput"]["permissionDecision"] == "deny"


class TestHeredocCommitMessage:
    """HEREDOC commit messages should be parsed correctly.

    Note: HEREDOC format is complex to test due to JSON escaping.
    These tests use triple-quoted strings with actual newlines.
    """

    def test_heredoc_valid_commit(self):
        # Triple-quoted string with actual newlines (not escaped \n)
        cmd = """git commit -m "$(cat <<'EOF'
feat: add new feature

This is the body.

Co-Authored-By: Someone <someone@example.com>
EOF
)\""""
        output = TestHookRunner.run({
            "tool_name": "Bash",
            "tool_input": {"command": cmd}
        })
        assert output["hookSpecificOutput"]["permissionDecision"] == "allow"

    def test_heredoc_invalid_commit(self):
        cmd = """git commit -m "$(cat <<'EOF'
WIP: work in progress
EOF
)\""""
        output = TestHookRunner.run({
            "tool_name": "Bash",
            "tool_input": {"command": cmd}
        })
        assert output["hookSpecificOutput"]["permissionDecision"] == "deny"


class TestBranchProtection:
    """Push to protected branches should be blocked."""

    def test_push_to_main_denied(self):
        from session_state import write_state
        write_state("protected_push_confirmed", {})  # Reset

        output = TestHookRunner.run({
            "tool_name": "Bash",
            "tool_input": {"command": "git push origin main"}
        })
        assert output["hookSpecificOutput"]["permissionDecision"] == "deny"
        assert "main" in output["hookSpecificOutput"]["permissionDecisionReason"]

    def test_push_to_develop_denied(self):
        from session_state import write_state
        write_state("protected_push_confirmed", {})

        output = TestHookRunner.run({
            "tool_name": "Bash",
            "tool_input": {"command": "git push origin develop"}
        })
        assert output["hookSpecificOutput"]["permissionDecision"] == "deny"

    def test_push_to_feature_branch_allowed(self):
        output = TestHookRunner.run({
            "tool_name": "Bash",
            "tool_input": {"command": "git push origin feature/my-feature"}
        })
        assert output["hookSpecificOutput"]["permissionDecision"] == "allow"


class TestForcePushProtection:
    """Force push should have extra warning."""

    def test_force_push_denied_with_warning(self):
        from session_state import write_state
        write_state("protected_push_confirmed", {})

        output = TestHookRunner.run({
            "tool_name": "Bash",
            "tool_input": {"command": "git push --force origin main"}
        })
        assert output["hookSpecificOutput"]["permissionDecision"] == "deny"
        assert "force" in output["hookSpecificOutput"]["permissionDecisionReason"].lower()

    def test_force_with_lease_also_blocked(self):
        from session_state import write_state
        write_state("protected_push_confirmed", {})

        output = TestHookRunner.run({
            "tool_name": "Bash",
            "tool_input": {"command": "git push --force-with-lease origin main"}
        })
        assert output["hookSpecificOutput"]["permissionDecision"] == "deny"


class TestRepeatToConfirm:
    """Repeat-to-confirm pattern for protected branches."""

    def test_second_push_allowed_after_confirmation(self):
        from session_state import write_state
        # Simulate first attempt already happened
        write_state("protected_push_confirmed", {"key": "main:normal"})

        output = TestHookRunner.run({
            "tool_name": "Bash",
            "tool_input": {"command": "git push origin main"}
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

    def test_git_status_allows(self):
        output = TestHookRunner.run({
            "tool_name": "Bash",
            "tool_input": {"command": "git status"}
        })
        assert output["hookSpecificOutput"]["permissionDecision"] == "allow"

    def test_git_log_allows(self):
        output = TestHookRunner.run({
            "tool_name": "Bash",
            "tool_input": {"command": "git log --oneline"}
        })
        assert output["hookSpecificOutput"]["permissionDecision"] == "allow"

    def test_git_add_allows(self):
        output = TestHookRunner.run({
            "tool_name": "Bash",
            "tool_input": {"command": "git add ."}
        })
        assert output["hookSpecificOutput"]["permissionDecision"] == "allow"
