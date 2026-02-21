"""
Agent Scope Prompt MCP Server.

Self-contained FastMCP instance with MCP prompts that serve
managed prompt templates from Bedrock Prompt Management.
Variables are substituted at render time from prompt arguments.
Mounted into the registry via tool_registry.py.
"""

from fastmcp import FastMCP

from src.infrastructure.bedrock_prompt_manager import get_prompt_manager
from src.infrastructure.trace_decorator import traced

# Import prompt modules to trigger registration in PROMPT_REGISTRY
import src.prompts.holiday_planner_agent_scope

prompt_mcp = FastMCP("agent_prompts")


# ---------------------------------------------------------------------------
# MCP Prompt
# ---------------------------------------------------------------------------


@prompt_mcp.prompt(
    name="holiday_planner_agent_scope",
    title="Holiday Planner Agent Scope Prompt",
    description=(
        "Comprehensive agent scope prompt that guides the LLM on how to "
        "orchestrate all available tools (places search, nearby search, "
        "place details, current weather, weather forecast, store preference, "
        "search preferences, get directions, geocode address) to deliver "
        "a complete holiday planning experience. "
        "Supports optional variable: user_name."
    ),
    tags={"agent-scope", "orchestration", "holiday-planner"},
)
@traced(span_name="mcp.prompt.holiday_planner_agent_scope", handler_type="prompt")
async def holiday_planner_agent_scope(
    user_name: str = "",
) -> str:
    """Fetch and return the agent scope prompt with variable substitution.

    Args:
        user_name: Optional user name for personalized greeting.
    """
    manager = get_prompt_manager()
    return await manager.render_prompt(
        "holiday_planner_agent_scope",
        user_name=user_name,
    )
