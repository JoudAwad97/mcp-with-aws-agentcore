# Entrypoint for `agentcore dev` (loaded as agentcore:app by Uvicorn)
from src.servers.tool_registry import McpServersRegistry

registry = McpServersRegistry()
_inner_app = registry.get_registry().http_app(stateless_http=True)


async def app(scope, receive, send):
    """ASGI app that forwards lifespan and lazily initializes the registry."""
    if scope["type"] == "lifespan":
        # Forward lifespan to inner app so it initializes its task group
        await _inner_app(scope, receive, send)
        return
    if not registry._is_initialized:
        await registry.initialize()
    await _inner_app(scope, receive, send)
