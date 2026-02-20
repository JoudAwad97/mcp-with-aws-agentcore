"""
User Preferences MCP Server.

Self-contained FastMCP instance with Bedrock AgentCore Memory tools.
Mounted into the registry via tool_registry.py.
"""

from loguru import logger
from fastmcp import FastMCP

from src.clients.agentcore_memory import AgentCoreMemoryClient
from src.config import settings
from src.utils.memory_formatters import (
    format_delete_result,
    format_memory_records,
    format_store_result,
)

user_preferences_mcp = FastMCP("user_preferences")

# ---------------------------------------------------------------------------
# Lazy client singleton
# ---------------------------------------------------------------------------

_client: AgentCoreMemoryClient | None = None


def _get_client() -> AgentCoreMemoryClient:
    global _client
    if _client is None:
        _client = AgentCoreMemoryClient(
            memory_id=settings.AGENTCORE_MEMORY_ID,
            region_name=settings.AWS_REGION,
        )
    return _client


# ---------------------------------------------------------------------------
# MCP Tools
# ---------------------------------------------------------------------------


@user_preferences_mcp.tool()
async def store_user_preference(
    actor_id: str,
    preference_text: str,
) -> str:
    """Store a preference for a user.

    Saves the preference to long-term memory so it can be recalled later
    to personalize recommendations.

    Args:
        actor_id: Unique identifier for the user (e.g. "user-123").
        preference_text: The preference to store (e.g. "I prefer vegetarian restaurants").
    """
    try:
        client = _get_client()
        result = await client.store_preference(
            actor_id=actor_id,
            preference_text=preference_text,
        )
        return format_store_result(result)
    except Exception as e:
        logger.error(f"Error storing preference: {e}")
        return f"Error storing preference: {e}"


@user_preferences_mcp.tool()
async def get_user_preferences(
    actor_id: str,
    query: str,
    max_results: int = 5,
) -> str:
    """Search for a user's stored preferences by semantic query.

    Returns the most relevant preferences matching the query.

    Args:
        actor_id: Unique identifier for the user (e.g. "user-123").
        query: What to search for (e.g. "restaurant preferences", "budget").
        max_results: Maximum number of preferences to return (1-20, default 5).
    """
    try:
        client = _get_client()
        records = await client.search_preferences(
            actor_id=actor_id,
            query=query,
            top_k=max_results,
        )
        return format_memory_records(records)
    except Exception as e:
        logger.error(f"Error searching preferences: {e}")
        return f"Error searching preferences: {e}"


@user_preferences_mcp.tool()
async def list_user_preferences(actor_id: str) -> str:
    """List all stored preferences for a user.

    Returns every preference record stored for the given user.

    Args:
        actor_id: Unique identifier for the user (e.g. "user-123").
    """
    try:
        client = _get_client()
        records = await client.list_preferences(actor_id=actor_id)
        return format_memory_records(records)
    except Exception as e:
        logger.error(f"Error listing preferences: {e}")
        return f"Error listing preferences: {e}"


@user_preferences_mcp.tool()
async def delete_user_preference(
    actor_id: str,
    record_id: str,
) -> str:
    """Delete a specific stored preference.

    Args:
        actor_id: Unique identifier for the user (e.g. "user-123").
        record_id: The ID of the preference record to delete (obtained from list/search results).
    """
    try:
        client = _get_client()
        result = await client.delete_preference(
            actor_id=actor_id,
            record_id=record_id,
        )
        return format_delete_result(result)
    except Exception as e:
        logger.error(f"Error deleting preference: {e}")
        return f"Error deleting preference: {e}"
