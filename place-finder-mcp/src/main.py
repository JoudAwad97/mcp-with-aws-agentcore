"""Container entrypoint for the MCP server (invoked by Dockerfile CMD)."""

import uvicorn

from src.servers.tool_registry import McpServersRegistry

registry = McpServersRegistry()
_inner_app = registry.get_registry().http_app(stateless_http=True)


async def app(scope, receive, send):
    """ASGI app that forwards lifespan and lazily initializes the registry."""
    if scope["type"] == "lifespan":
        await _inner_app(scope, receive, send)
        return
    if not registry._is_initialized:
        await registry.initialize()
    await _inner_app(scope, receive, send)


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
