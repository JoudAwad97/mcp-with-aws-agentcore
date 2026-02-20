"""
MCP Tool Registry.

Aggregates all MCP servers into a single FastMCP instance with prefix namespacing.
"""

from loguru import logger
from fastmcp import FastMCP

from src.servers.place_finder import place_finder_mcp
from src.servers.user_preferences import user_preferences_mcp
from src.servers.weather import weather_mcp


class McpServersRegistry:
    def __init__(self) -> None:
        self.registry = FastMCP("tool_registry")
        self._is_initialized = False

    async def initialize(self) -> None:
        """Import all MCP servers into the registry with namespaces."""
        if self._is_initialized:
            return

        logger.info("Initializing MCP tool registry...")

        self.registry.mount(place_finder_mcp, namespace="places")
        self.registry.mount(weather_mcp, namespace="weather")
        self.registry.mount(user_preferences_mcp, namespace="preferences")
        # Future servers:
        # self.registry.mount(events_mcp, namespace="events")

        self._is_initialized = True

        all_tools = await self.registry.list_tools()
        tool_names = [t.name for t in all_tools]
        logger.info(f"Registry initialized with {len(all_tools)} tools: {tool_names}")

    def get_registry(self) -> FastMCP:
        return self.registry
