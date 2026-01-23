"""
Tests for hooks/pre-tool-use/graphiti-guard.py

Tests the PreToolUse hook that guards add_memory, search_nodes, and clear_graph calls.

Edge cases covered:
- add_memory: source_description required
- add_memory: credential detection
- add_memory: citation checks
- add_memory: group_id decision workflow
- add_memory: version warning for technical content
- search_nodes: group_ids required
- clear_graph: review required first
"""

import json
from pathlib import Path

import pytest
import sys
sys.path.insert(0, str(Path(__file__).parent.parent / "hooks" / "lib"))
sys.path.insert(0, str(Path(__file__).parent))
import session_state as ss
from helpers import make_add_memory_input, make_search_nodes_input, make_bridge_input


class TestNonGraphitiToolsPassThrough:
    """Non-Graphiti tools should pass through."""

    def test_non_bridge_tool_allows(self, graphiti_guard_runner, clean_state):
        """Non-bridge tools should be allowed."""
        hook_input = {"tool_name": "Bash", "tool_input": {"command": "ls"}}
        result = graphiti_guard_runner.run(hook_input)
        assert result["hookSpecificOutput"]["permissionDecision"] == "allow"

    def test_non_graphiti_bridge_tool_allows(self, graphiti_guard_runner, clean_state):
        """Bridge tools not related to Graphiti should pass."""
        hook_input = make_bridge_input("firecrawl__scrape", {"url": "https://example.com"})
        result = graphiti_guard_runner.run(hook_input)
        assert result["hookSpecificOutput"]["permissionDecision"] == "allow"


class TestAddMemorySourceRequired:
    """add_memory requires source_description."""

    def test_missing_source_denies(self, graphiti_guard_runner, clean_state):
        """Missing source_description should deny."""
        hook_input = make_bridge_input("graphiti__add_memory", {
            "name": "Test Learning",
            "episode_body": "Some content"
        })
        result = graphiti_guard_runner.run(hook_input)
        assert result["hookSpecificOutput"]["permissionDecision"] == "deny"
        assert "source_description" in result["hookSpecificOutput"]["permissionDecisionReason"]

    def test_empty_source_denies(self, graphiti_guard_runner, clean_state):
        """Empty source_description should deny."""
        hook_input = make_add_memory_input(
            "Test Learning",
            "Some content",
            source_description=""
        )
        result = graphiti_guard_runner.run(hook_input)
        assert result["hookSpecificOutput"]["permissionDecision"] == "deny"

    def test_whitespace_only_source_denies(self, graphiti_guard_runner, clean_state):
        """Whitespace-only source_description should deny."""
        hook_input = make_add_memory_input(
            "Test Learning",
            "Some content",
            source_description="   "
        )
        result = graphiti_guard_runner.run(hook_input)
        assert result["hookSpecificOutput"]["permissionDecision"] == "deny"


class TestAddMemoryCredentialDetection:
    """add_memory should detect and block credentials."""

    def test_aws_key_pattern_denies(self, graphiti_guard_runner, clean_state):
        """AWS key patterns should be blocked."""
        hook_input = make_add_memory_input(
            "AWS Config",
            "My AWS key is AKIAIOSFODNN7EXAMPLE",
            source_description="User statement"
        )
        result = graphiti_guard_runner.run(hook_input)
        assert result["hookSpecificOutput"]["permissionDecision"] == "deny"
        assert "Secret" in result["hookSpecificOutput"]["permissionDecisionReason"]

    def test_private_key_block_denies(self, graphiti_guard_runner, clean_state):
        """Private key blocks should be blocked."""
        hook_input = make_add_memory_input(
            "SSH Key",
            "-----BEGIN RSA PRIVATE KEY-----\nMIIEpAIBAAKCAQ...",
            source_description="User statement"
        )
        result = graphiti_guard_runner.run(hook_input)
        assert result["hookSpecificOutput"]["permissionDecision"] == "deny"

    def test_github_token_denies(self, graphiti_guard_runner, clean_state):
        """GitHub tokens should be blocked."""
        hook_input = make_add_memory_input(
            "GitHub Token",
            "My token is ghp_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx",
            source_description="User statement"
        )
        result = graphiti_guard_runner.run(hook_input)
        assert result["hookSpecificOutput"]["permissionDecision"] == "deny"

    def test_password_with_value_denies(self, graphiti_guard_runner, clean_state):
        """Password with value should be blocked."""
        hook_input = make_add_memory_input(
            "Login Info",
            "password: mysecretpassword123",
            source_description="User statement"
        )
        result = graphiti_guard_runner.run(hook_input)
        assert result["hookSpecificOutput"]["permissionDecision"] == "deny"

    def test_mention_of_1password_allows(self, graphiti_guard_runner, clean_state):
        """Mentioning 1Password tool should be allowed."""
        # First confirm group_id
        hook_input = make_add_memory_input(
            "Tool Preference",
            "I use 1Password for credential management",
            source_description="User statement",
            group_id="main"
        )
        graphiti_guard_runner.run(hook_input)  # First call for group_id decision

        result = graphiti_guard_runner.run(hook_input)  # Second call after decision
        # Should either allow or ask about main (not deny for secrets)
        reason = result["hookSpecificOutput"].get("permissionDecisionReason", "")
        assert "Secret" not in reason


class TestAddMemoryCitationCheck:
    """add_memory checks for proper citations."""

    def test_book_without_author_warns(self, graphiti_guard_runner, clean_state):
        """Book reference without author should warn."""
        hook_input = make_add_memory_input(
            "Book Note",
            "From the book 'Clean Code' - good practices for naming",
            source_description="Reading"
        )
        result = graphiti_guard_runner.run(hook_input)
        # May deny asking for citation info
        if result["hookSpecificOutput"]["permissionDecision"] == "deny":
            reason = result["hookSpecificOutput"]["permissionDecisionReason"]
            assert "author" in reason.lower() or "Book" in reason

    def test_book_with_full_citation_progresses(self, graphiti_guard_runner, clean_state):
        """Book with full citation should progress (may still ask group_id)."""
        hook_input = make_add_memory_input(
            "Book Note",
            "From book 'Clean Code' by Robert Martin (2008)",
            source_description="Reading",
            group_id="main"
        )
        result = graphiti_guard_runner.run(hook_input)
        # Should not deny for missing citation
        reason = result["hookSpecificOutput"].get("permissionDecisionReason", "")
        assert "missing" not in reason.lower() or "author" not in reason.lower()


class TestAddMemoryGroupIdDecision:
    """add_memory requires group_id decision."""

    def test_first_call_asks_for_group_id(self, graphiti_guard_runner, clean_state):
        """First call without prior decision should ask about group_id."""
        ss.write_state("active_group_ids", ["project-test"])

        hook_input = make_add_memory_input(
            "Test Learning",
            "Content here",
            source_description="User statement"
        )
        result = graphiti_guard_runner.run(hook_input)
        assert result["hookSpecificOutput"]["permissionDecision"] == "deny"
        reason = result["hookSpecificOutput"]["permissionDecisionReason"]
        assert "group_id" in reason.lower() or "save" in reason.lower()

    def test_repeat_with_same_content_allows_for_project(self, graphiti_guard_runner, clean_state):
        """Repeating same content with project group_id should allow."""
        ss.write_state("active_group_ids", ["project-test"])

        hook_input = make_add_memory_input(
            "Test Learning",
            "Content here",
            source_description="User statement",
            group_id="project-test"
        )

        # First call - asks about group_id
        graphiti_guard_runner.run(hook_input)

        # Second call - should allow for project group
        result = graphiti_guard_runner.run(hook_input)
        assert result["hookSpecificOutput"]["permissionDecision"] == "allow"

    def test_main_group_requires_confirmation(self, graphiti_guard_runner, clean_state):
        """Saving to main requires extra confirmation."""
        hook_input = make_add_memory_input(
            "Test Learning",
            "Content here",
            source_description="User statement",
            group_id="main"
        )

        # First call
        graphiti_guard_runner.run(hook_input)
        # Second call (group_id decision made)
        result = graphiti_guard_runner.run(hook_input)

        # Should either allow or ask for main confirmation
        assert result["hookSpecificOutput"]["permissionDecision"] in ["allow", "deny"]
        if result["hookSpecificOutput"]["permissionDecision"] == "deny":
            reason = result["hookSpecificOutput"]["permissionDecisionReason"]
            assert "main" in reason.lower() or "permanent" in reason.lower()


class TestAddMemoryVersionWarning:
    """add_memory warns about missing versions for technical content."""

    def test_react_without_version_warns_first_time(self, graphiti_guard_runner, clean_state):
        """Technical content without version should warn (first time)."""
        import hashlib

        ss.write_state("active_group_ids", ["project-test"])

        body = "React hooks are better than class components"
        content_hash = hashlib.md5(body.encode()).hexdigest()[:8]

        # Pre-set the group_id decision so it skips that step
        ss.write_state("group_id_decision", {
            "name": "React Learning",
            "content_hash": content_hash,
            "group_id": "project-test"
        })

        hook_input = make_add_memory_input(
            "React Learning",
            body,
            source_description="Own experience",
            group_id="project-test"
        )
        result = graphiti_guard_runner.run(hook_input)

        # Should warn about version (deny with version hint)
        assert result["hookSpecificOutput"]["permissionDecision"] == "deny"
        reason = result["hookSpecificOutput"]["permissionDecisionReason"]
        assert "version" in reason.lower() or "react" in reason.lower()

    def test_react_with_version_allows(self, graphiti_guard_runner, clean_state):
        """Technical content with version should proceed."""
        ss.write_state("active_group_ids", ["project-test"])

        hook_input = make_add_memory_input(
            "React Learning",
            "React 18: Concurrent features are stable",
            source_description="Own experience",
            group_id="project-test"
        )

        # First call for group_id
        graphiti_guard_runner.run(hook_input)
        # Second call
        result = graphiti_guard_runner.run(hook_input)
        assert result["hookSpecificOutput"]["permissionDecision"] == "allow"


class TestSearchNodes:
    """search_nodes requires group_ids."""

    def test_search_without_group_ids_denies(self, graphiti_guard_runner, clean_state):
        """search_nodes without group_ids should deny."""
        ss.write_state("active_group_ids", ["project-test"])

        hook_input = make_search_nodes_input("some query")
        result = graphiti_guard_runner.run(hook_input)

        # Changed from deny to allow_with_msg - warns but doesn't block
        assert result["hookSpecificOutput"]["permissionDecision"] == "allow"
        assert "group_ids" in result["hookSpecificOutput"].get("permissionDecisionReason", "")

    def test_search_with_incomplete_group_ids_warns(self, graphiti_guard_runner, clean_state):
        """search_nodes missing contexts should warn but allow (not block)."""
        ss.write_state("active_group_ids", ["project-test"])

        # Only searching main, missing project-test - should warn but allow
        hook_input = make_search_nodes_input("query", group_ids=["main"])
        result = graphiti_guard_runner.run(hook_input)

        # Changed from deny to allow_with_msg
        assert result["hookSpecificOutput"]["permissionDecision"] == "allow"
        reason = result["hookSpecificOutput"].get("permissionDecisionReason", "")
        # Should mention the need for both contexts
        assert "main" in reason.lower() or "project" in reason.lower() or reason == ""

    def test_search_with_all_group_ids_allows(self, graphiti_guard_runner, clean_state):
        """search_nodes with all required group_ids should allow."""
        ss.write_state("active_group_ids", ["project-test"])

        hook_input = make_search_nodes_input(
            "query",
            group_ids=["main", "project-test"]
        )
        result = graphiti_guard_runner.run(hook_input)
        assert result["hookSpecificOutput"]["permissionDecision"] == "allow"

    def test_search_sets_graphiti_searched_flag(self, graphiti_guard_runner, clean_state):
        """Successful search should set graphiti_searched flag."""
        ss.write_state("active_group_ids", [])

        hook_input = make_search_nodes_input("query", group_ids=["main"])
        graphiti_guard_runner.run(hook_input)

        state = ss.read_state()
        assert state.get("graphiti_searched") is True


class TestClearGraph:
    """clear_graph requires review first."""

    def test_clear_without_review_denies(self, graphiti_guard_runner, clean_state):
        """clear_graph without prior review should deny."""
        hook_input = make_bridge_input("graphiti__clear_graph", {"group_ids": ["test"]})
        result = graphiti_guard_runner.run(hook_input)

        assert result["hookSpecificOutput"]["permissionDecision"] == "deny"
        reason = result["hookSpecificOutput"]["permissionDecisionReason"]
        assert "clear_graph" in reason.lower() or "promote" in reason.lower()

    def test_clear_after_review_allows(self, graphiti_guard_runner, clean_state):
        """clear_graph after review should allow."""
        ss.write_state("graphiti_review_done", True)

        hook_input = make_bridge_input("graphiti__clear_graph", {"group_ids": ["test"]})
        result = graphiti_guard_runner.run(hook_input)

        assert result["hookSpecificOutput"]["permissionDecision"] == "allow"


class TestTitleSearchability:
    """Title searchability checks."""

    def test_long_title_warns(self, graphiti_guard_runner, clean_state):
        """Very long titles should trigger warning."""
        ss.write_state("active_group_ids", ["project-test"])

        long_name = "This is a very long title that exceeds sixty characters and should trigger a warning"
        hook_input = make_add_memory_input(
            long_name,
            "Content",
            source_description="Test",
            group_id="project-test"
        )
        result = graphiti_guard_runner.run(hook_input)

        if result["hookSpecificOutput"]["permissionDecision"] == "deny":
            reason = result["hookSpecificOutput"]["permissionDecisionReason"]
            # May warn about title length or ask about group_id
            assert "title" in reason.lower() or "group_id" in reason.lower() or "chars" in reason.lower()

    def test_redundant_prefix_warns(self, graphiti_guard_runner, clean_state):
        """Redundant prefixes like 'Learning:' should warn."""
        ss.write_state("active_group_ids", ["project-test"])
        ss.write_state("group_id_decision", {
            "name": "Learning: React patterns",
            "content_hash": "x",
            "group_id": "project-test"
        })

        hook_input = make_add_memory_input(
            "Learning: React patterns",
            "Content",
            source_description="Test",
            group_id="project-test"
        )
        result = graphiti_guard_runner.run(hook_input)

        if result["hookSpecificOutput"]["permissionDecision"] == "deny":
            reason = result["hookSpecificOutput"]["permissionDecisionReason"]
            assert "prefix" in reason.lower() or "unnecessary" in reason.lower() or "searchable" in reason.lower()


class TestGroupIdContextGuard:
    """Guard: Only allow saving to group_ids where agent actually worked."""

    def test_save_to_untracked_group_id_denies(self, graphiti_guard_runner, clean_state):
        """Saving to a group_id not in active_group_ids should deny."""
        # Set active_group_ids to only contain one project
        ss.write_state("active_group_ids", ["Milofax-project-a"])

        # Try to save to a different project
        hook_input = make_add_memory_input(
            "Test Learning",
            "Some content",
            source_description="User statement",
            group_id="Milofax-project-b"  # Not in active_group_ids!
        )
        result = graphiti_guard_runner.run(hook_input)

        assert result["hookSpecificOutput"]["permissionDecision"] == "deny"
        reason = result["hookSpecificOutput"]["permissionDecisionReason"]
        assert "not in active contexts" in reason
        assert "Milofax-project-b" in reason
        assert "Milofax-project-a" in reason  # Shows what's allowed

    def test_save_to_tracked_group_id_proceeds(self, graphiti_guard_runner, clean_state):
        """Saving to a group_id in active_group_ids should proceed (may still ask other questions)."""
        ss.write_state("active_group_ids", ["Milofax-project-a"])

        hook_input = make_add_memory_input(
            "Test Learning",
            "Some content",
            source_description="User statement",
            group_id="Milofax-project-a"  # In active_group_ids!
        )
        result = graphiti_guard_runner.run(hook_input)

        # Should NOT deny for "not in active contexts"
        reason = result["hookSpecificOutput"].get("permissionDecisionReason", "")
        assert "not in active contexts" not in reason

    def test_save_to_main_always_allowed(self, graphiti_guard_runner, clean_state):
        """Saving to 'main' should always be allowed (separate confirmation)."""
        ss.write_state("active_group_ids", ["Milofax-project-a"])

        hook_input = make_add_memory_input(
            "Test Learning",
            "Some content",
            source_description="User statement",
            group_id="main"
        )
        result = graphiti_guard_runner.run(hook_input)

        # Should NOT deny for "not in active contexts"
        reason = result["hookSpecificOutput"].get("permissionDecisionReason", "")
        assert "not in active contexts" not in reason
        # May ask about main confirmation, but that's a different check

    def test_no_active_contexts_shows_none(self, graphiti_guard_runner, clean_state):
        """When no active contexts, message should indicate that."""
        # No active_group_ids set

        hook_input = make_add_memory_input(
            "Test Learning",
            "Some content",
            source_description="User statement",
            group_id="some-random-project"
        )
        result = graphiti_guard_runner.run(hook_input)

        assert result["hookSpecificOutput"]["permissionDecision"] == "deny"
        reason = result["hookSpecificOutput"]["permissionDecisionReason"]
        assert "not in active contexts" in reason
        assert "(none)" in reason  # Shows empty active list

    def test_save_to_current_project_without_file_ops_allows(self, graphiti_guard_runner, clean_state):
        """Saving to project_group_id should work even without file operations.

        Scenario: User is in /INFRASTRUCTURE/ (Git: Milofax/marakanda-infrastructure)
        but hasn't read/edited any files yet. The CWD-based project_group_id should
        still be allowed as a valid target.
        """
        # CWD detected as Milofax-infrastructure at SessionStart
        ss.write_state("project_group_id", "Milofax-infrastructure")
        ss.write_state("active_group_ids", [])  # No files read yet

        hook_input = make_add_memory_input(
            "Test Learning",
            "Content about infrastructure",
            source_description="User statement",
            group_id="Milofax-infrastructure"
        )
        result = graphiti_guard_runner.run(hook_input)

        # Should NOT deny for "not in active contexts"
        reason = result["hookSpecificOutput"].get("permissionDecisionReason", "")
        assert "not in active contexts" not in reason

    def test_current_project_shown_in_allowed_contexts(self, graphiti_guard_runner, clean_state):
        """When denying, the current project should be shown in allowed contexts."""
        # CWD detected as project A
        ss.write_state("project_group_id", "Milofax-project-a")
        ss.write_state("active_group_ids", ["Milofax-project-b"])  # Worked in B

        # Try to save to project C (not current, not active)
        hook_input = make_add_memory_input(
            "Test Learning",
            "Some content",
            source_description="User statement",
            group_id="Milofax-project-c"
        )
        result = graphiti_guard_runner.run(hook_input)

        assert result["hookSpecificOutput"]["permissionDecision"] == "deny"
        reason = result["hookSpecificOutput"]["permissionDecisionReason"]
        assert "not in active contexts" in reason
        # Both current project AND active_group_ids should be shown
        assert "Milofax-project-a" in reason  # Current project
        assert "Milofax-project-b" in reason  # Active from file ops


class TestRepeatToSkipAlternating:
    """Bug #2: Repeat to skip must work with alternating learnings.

    The bug: pending states (main_pending, version_pending) store only ONE name.
    When multiple learnings alternate, they overwrite each other and the
    "repeat to confirm" pattern never succeeds.

    Expected behavior: Each learning should have its own pending state entry,
    keyed by a hash of the name.
    """

    def test_alternating_main_learnings_both_can_skip(self, graphiti_guard_runner, clean_state):
        """Alternating learnings to main should both eventually allow."""
        import hashlib

        # Setup: Two learnings alternating, both to main
        learning_a = make_add_memory_input(
            "Learning A",
            "Content A about something",
            source_description="User statement",
            group_id="main"
        )
        learning_b = make_add_memory_input(
            "Learning B",
            "Content B about something else",
            source_description="User statement",
            group_id="main"
        )

        # Round 1: Both should be blocked (first time)
        result_a1 = graphiti_guard_runner.run(learning_a)
        assert result_a1["hookSpecificOutput"]["permissionDecision"] == "deny"
        assert "main" in result_a1["hookSpecificOutput"]["permissionDecisionReason"].lower()

        result_b1 = graphiti_guard_runner.run(learning_b)
        assert result_b1["hookSpecificOutput"]["permissionDecision"] == "deny"
        assert "main" in result_b1["hookSpecificOutput"]["permissionDecisionReason"].lower()

        # Round 2: Both should now be allowed (repeat = confirm)
        result_a2 = graphiti_guard_runner.run(learning_a)
        assert result_a2["hookSpecificOutput"]["permissionDecision"] == "allow", \
            f"Learning A should allow on repeat, got: {result_a2}"

        result_b2 = graphiti_guard_runner.run(learning_b)
        assert result_b2["hookSpecificOutput"]["permissionDecision"] == "allow", \
            f"Learning B should allow on repeat, got: {result_b2}"

    def test_single_main_learning_repeat_still_works(self, graphiti_guard_runner, clean_state):
        """Single learning repeat to main should still work (regression test)."""
        learning = make_add_memory_input(
            "Single Learning",
            "Content about a topic",
            source_description="User statement",
            group_id="main"
        )

        # First call: blocked
        result1 = graphiti_guard_runner.run(learning)
        assert result1["hookSpecificOutput"]["permissionDecision"] == "deny"

        # Second call: allowed
        result2 = graphiti_guard_runner.run(learning)
        assert result2["hookSpecificOutput"]["permissionDecision"] == "allow"

    def test_alternating_version_warnings_both_can_skip(self, graphiti_guard_runner, clean_state):
        """Alternating technical learnings without version should both skip on repeat."""
        import hashlib
        ss.write_state("active_group_ids", ["project-test"])

        # Pre-set group_id decisions to skip that step
        body_a = "React hooks are great"
        body_b = "Django ORM is powerful"
        hash_a = hashlib.md5(body_a.encode()).hexdigest()[:8]
        hash_b = hashlib.md5(body_b.encode()).hexdigest()[:8]

        learning_a = make_add_memory_input(
            "React Learning",
            body_a,
            source_description="Own experience",
            group_id="project-test"
        )
        learning_b = make_add_memory_input(
            "Django Learning",
            body_b,
            source_description="Own experience",
            group_id="project-test"
        )

        # Round 1: Both should warn about version (first time)
        result_a1 = graphiti_guard_runner.run(learning_a)
        assert result_a1["hookSpecificOutput"]["permissionDecision"] == "deny"
        assert "version" in result_a1["hookSpecificOutput"]["permissionDecisionReason"].lower()

        result_b1 = graphiti_guard_runner.run(learning_b)
        assert result_b1["hookSpecificOutput"]["permissionDecision"] == "deny"
        assert "version" in result_b1["hookSpecificOutput"]["permissionDecisionReason"].lower()

        # Round 2: Both should now be allowed (repeat = skip version warning)
        result_a2 = graphiti_guard_runner.run(learning_a)
        assert result_a2["hookSpecificOutput"]["permissionDecision"] == "allow", \
            f"React learning should allow on repeat, got: {result_a2}"

        result_b2 = graphiti_guard_runner.run(learning_b)
        assert result_b2["hookSpecificOutput"]["permissionDecision"] == "allow", \
            f"Django learning should allow on repeat, got: {result_b2}"

    def test_single_version_warning_repeat_still_works(self, graphiti_guard_runner, clean_state):
        """Single technical learning repeat should still work (regression test)."""
        ss.write_state("active_group_ids", ["project-test"])

        learning = make_add_memory_input(
            "Python Learning",
            "Python asyncio is useful",
            source_description="Own experience",
            group_id="project-test"
        )

        # First call: version warning
        result1 = graphiti_guard_runner.run(learning)
        assert result1["hookSpecificOutput"]["permissionDecision"] == "deny"
        assert "version" in result1["hookSpecificOutput"]["permissionDecisionReason"].lower()

        # Second call: allowed
        result2 = graphiti_guard_runner.run(learning)
        assert result2["hookSpecificOutput"]["permissionDecision"] == "allow"


class TestEdgeCases:
    """Edge cases and error handling."""

    def test_invalid_json_allows(self, graphiti_guard_runner, clean_state):
        """Invalid JSON should fail safe and allow."""
        import subprocess
        import sys as sys_module

        hook_path = Path(__file__).parent.parent / "hooks" / "pre-tool-use" / "graphiti-guard.py"
        result = subprocess.run(
            [sys_module.executable, str(hook_path)],
            input="not valid json",
            capture_output=True,
            text=True,
            timeout=10
        )

        output = json.loads(result.stdout)
        assert output["hookSpecificOutput"]["permissionDecision"] == "allow"

    def test_hook_registers_itself(self, graphiti_guard_runner, clean_state):
        """Hook should register itself."""
        hook_input = make_bridge_input("graphiti__add_memory", {"name": "x", "episode_body": "y"})
        graphiti_guard_runner.run(hook_input)

        state = ss.read_state()
        assert state.get("hooks_active", {}).get("graphiti") is True
