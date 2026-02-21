"""
Trace decorator for MCP tool and prompt handlers.

Provides a @traced decorator that wraps any async MCP handler with an
OpenTelemetry span. Automatically captures:
- Span name (e.g. "mcp.tool.search_places", "mcp.prompt.holiday_planner")
- Handler type (tool / prompt)
- Function arguments as span attributes
- Duration and success/failure status
- Exception details on errors

Usage:
    @mcp.tool(...)
    @traced(span_name="mcp.tool.search_places", handler_type="tool")
    async def search_places(query: str, ...) -> PlaceSearchResponse:
        ...
"""

from __future__ import annotations

import functools
import inspect
import time
from typing import Any, Callable

from loguru import logger

from src.infrastructure.observability import get_observability_manager


def traced(
    span_name: str,
    handler_type: str = "tool",
) -> Callable:
    """
    Decorator that wraps an async MCP handler with an OpenTelemetry span.

    Args:
        span_name: The span name (e.g. "mcp.tool.search_places").
        handler_type: Either "tool" or "prompt".
    """

    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        async def wrapper(*args: Any, **kwargs: Any) -> Any:
            observability = get_observability_manager()

            # Build span attributes from function arguments
            sig = inspect.signature(func)
            bound = sig.bind(*args, **kwargs)
            bound.apply_defaults()

            span_attributes: dict[str, Any] = {
                "mcp.handler.type": handler_type,
                "mcp.handler.name": func.__name__,
            }

            # Add function arguments as span attributes (stringify for safety)
            for param_name, param_value in bound.arguments.items():
                attr_key = f"mcp.{handler_type}.param.{param_name}"
                span_attributes[attr_key] = str(param_value)

            start_time = time.monotonic()

            with observability.create_span(
                name=span_name,
                attributes=span_attributes,
            ) as span:
                try:
                    result = await func(*args, **kwargs)

                    duration_ms = (time.monotonic() - start_time) * 1000

                    observability.record_workflow_step(
                        step_name=func.__name__,
                        step_type=handler_type,
                        duration_ms=round(duration_ms, 2),
                        success=True,
                    )

                    logger.debug(
                        f"[trace] {span_name} completed in {duration_ms:.1f}ms"
                    )

                    return result

                except Exception as e:
                    duration_ms = (time.monotonic() - start_time) * 1000

                    observability.record_workflow_step(
                        step_name=func.__name__,
                        step_type=handler_type,
                        duration_ms=round(duration_ms, 2),
                        success=False,
                        metadata={"error": str(e)},
                    )

                    logger.error(
                        f"[trace] {span_name} failed after {duration_ms:.1f}ms: {e}"
                    )

                    raise

        return wrapper

    return decorator
