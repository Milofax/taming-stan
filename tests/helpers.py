"""
Helper functions for creating hook test inputs.

These are not pytest fixtures, but utility functions that can be imported
into test modules.
"""


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
