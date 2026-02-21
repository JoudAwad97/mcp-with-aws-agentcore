"""
User Preferences MCP Server.

Self-contained FastMCP instance with Bedrock AgentCore Memory tools.
Mounted into the registry via tool_registry.py.
"""

from fastmcp import FastMCP

from src.clients.agentcore_memory_client import AgentCoreMemoryClient
from src.config import settings
from src.infrastructure.trace_decorator import traced
from src.schemas.preferences import (
    PreferenceListResponse,
    StorePreferenceResponse,
)
from src.utils.memory_formatters import (
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


@user_preferences_mcp.tool(
    title="Store User Preference",
    description=(
        "Save a user preference to long-term memory for future personalization. "
        "Store travel preferences, dietary restrictions, budget ranges, "
        "accommodation styles, or any other preference the user shares. "
        "These are persisted and can be recalled later to tailor recommendations."
    ),
    tags={"preferences", "memory", "store", "personalization"},
    annotations={
        "title": "Store User Preference",
        "readOnlyHint": False,
        "destructiveHint": False,
        "idempotentHint": False,
        "openWorldHint": False,
    },
)
@traced(span_name="mcp.tool.store_user_preference", handler_type="tool")
async def store_user_preference(
    actor_id: str,
    preference_text: str,
) -> StorePreferenceResponse:
    """Store a preference for a user.

    Saves the preference to long-term memory so it can be recalled later
    to personalize recommendations.

    Args:
        actor_id: Unique identifier for the user (e.g. "user-123").
        preference_text: The preference to store (e.g. "I prefer vegetarian restaurants").
    """
    client = _get_client()
    result = await client.store_preference(
        actor_id=actor_id,
        preference_text=preference_text,
    )
    return format_store_result(result)


@user_preferences_mcp.tool(
    title="Search User Preferences",
    description=(
        "Semantically search a user's stored preferences by topic. "
        "Use this to recall what the user likes or dislikes before making "
        "recommendations. For example, search for 'food' to find dietary "
        "preferences, or 'budget' to find spending limits."
    ),
    tags={"preferences", "memory", "search", "personalization"},
    annotations={
        "title": "Search User Preferences",
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": False,
    },
)
@traced(span_name="mcp.tool.get_user_preferences", handler_type="tool")
async def get_user_preferences(
    actor_id: str,
    query: str,
    max_results: int = 5,
) -> PreferenceListResponse:
    """Search for a user's stored preferences by semantic query.

    Returns the most relevant preferences matching the query.

    Args:
        actor_id: Unique identifier for the user (e.g. "user-123").
        query: What to search for (e.g. "restaurant preferences", "budget").
        max_results: Maximum number of preferences to return (1-20, default 5).
    """
    client = _get_client()
    records = await client.search_preferences(
        actor_id=actor_id,
        query=query,
        top_k=max_results,
    )
    return format_memory_records(records)
