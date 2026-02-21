"""
Observability configuration for the MCP server.

Provides OpenTelemetry-based observability with CloudWatch integration for:
- Distributed tracing across MCP tool and prompt invocations
- Session ID propagation from the calling agent
- Custom span creation for detailed monitoring
- CloudWatch GenAI Observability dashboard integration

This module works with the AWS Distro for OpenTelemetry (ADOT) SDK which
automatically instruments the application to capture telemetry data.

Environment Variables Required:
    AGENT_OBSERVABILITY_ENABLED: Enable observability (default: true)
    OTEL_PYTHON_DISTRO: Set to "aws_distro" for ADOT
    OTEL_PYTHON_CONFIGURATOR: Set to "aws_configurator" for ADOT
    OTEL_EXPORTER_OTLP_PROTOCOL: Set to "http/protobuf"
    OTEL_RESOURCE_ATTRIBUTES: Service name and resource attributes
    OTEL_EXPORTER_OTLP_LOGS_HEADERS: CloudWatch log group configuration

Usage:
    Run with automatic instrumentation:
        opentelemetry-instrument python -m src.main
"""

from __future__ import annotations

from contextlib import contextmanager
from typing import Optional

from loguru import logger

# OpenTelemetry imports — gracefully handle if not installed
try:
    from opentelemetry import baggage, context, trace
    from opentelemetry.context import attach, detach
    from opentelemetry.trace import SpanKind, Status, StatusCode

    OTEL_AVAILABLE = True
except ImportError:
    OTEL_AVAILABLE = False
    trace = None  # type: ignore[assignment]
    baggage = None  # type: ignore[assignment]
    context = None  # type: ignore[assignment]
    attach = None  # type: ignore[assignment]
    detach = None  # type: ignore[assignment]
    SpanKind = None  # type: ignore[assignment]
    Status = None  # type: ignore[assignment]
    StatusCode = None  # type: ignore[assignment]
    logger.warning(
        "OpenTelemetry packages not installed. "
        "Observability features will be disabled."
    )


class ObservabilityManager:
    """
    Manages OpenTelemetry observability for the MCP server.

    Provides utilities for:
    - Session ID propagation via OpenTelemetry baggage
    - Custom span creation for MCP tool/prompt invocations
    - Trace context management
    """

    def __init__(
        self,
        service_name: str = "placefinder-mcp",
        enabled: bool = True,
    ) -> None:
        self.service_name = service_name
        self.enabled = enabled and OTEL_AVAILABLE
        self._tracer = None

        if self.enabled and trace is not None:
            self._tracer = trace.get_tracer(
                instrumenting_module_name=service_name,
                tracer_provider=trace.get_tracer_provider(),
            )
            logger.info(f"Observability initialized for service: {service_name}")
        else:
            logger.info("Observability disabled or OpenTelemetry not available")

    # ------------------------------------------------------------------
    # Session context
    # ------------------------------------------------------------------

    def set_session_id(self, session_id: str) -> Optional[object]:
        """Set session ID in OpenTelemetry baggage for trace correlation."""
        if not self.enabled or baggage is None or attach is None:
            return None

        try:
            ctx = baggage.set_baggage("session.id", session_id)
            token = attach(ctx)
            logger.debug(f"Session ID set in observability context: {session_id}")
            return token
        except Exception as e:
            logger.warning(f"Failed to set session ID in baggage: {e}")
            return None

    def clear_session_context(self, token: object) -> None:
        """Clear the session context from OpenTelemetry baggage."""
        if not self.enabled or token is None or detach is None:
            return

        try:
            detach(token)
            logger.debug("Session context cleared from observability")
        except Exception as e:
            logger.warning(f"Failed to clear session context: {e}")

    @contextmanager
    def session_context(self, session_id: str):
        """Context manager for session-scoped observability."""
        token = self.set_session_id(session_id)
        try:
            yield
        finally:
            self.clear_session_context(token)

    # ------------------------------------------------------------------
    # Span creation
    # ------------------------------------------------------------------

    @contextmanager
    def create_span(
        self,
        name: str,
        kind=None,
        attributes: Optional[dict] = None,
    ):
        """
        Create a custom span for detailed tracing.

        Args:
            name: Span name (e.g. "mcp.tool.search_places").
            kind: SpanKind (defaults to INTERNAL).
            attributes: Custom attributes to attach.
        """
        if not self.enabled or self._tracer is None:
            yield None
            return

        if kind is None and SpanKind is not None:
            kind = SpanKind.INTERNAL

        with self._tracer.start_as_current_span(
            name=name,
            kind=kind,
            attributes=attributes or {},
        ) as span:
            try:
                yield span
            except Exception as e:
                span.set_status(Status(StatusCode.ERROR, str(e)))
                span.record_exception(e)
                raise

    def add_span_attribute(self, key: str, value: str) -> None:
        """Add an attribute to the current span."""
        if not self.enabled or trace is None:
            return

        try:
            current_span = trace.get_current_span()
            if current_span:
                current_span.set_attribute(key, value)
        except Exception as e:
            logger.warning(f"Failed to add span attribute: {e}")

    def add_span_event(
        self,
        name: str,
        attributes: Optional[dict] = None,
    ) -> None:
        """Add an event to the current span."""
        if not self.enabled or trace is None:
            return

        try:
            current_span = trace.get_current_span()
            if current_span:
                current_span.add_event(name, attributes=attributes or {})
        except Exception as e:
            logger.warning(f"Failed to add span event: {e}")

    def record_workflow_step(
        self,
        step_name: str,
        step_type: str,
        duration_ms: Optional[float] = None,
        success: bool = True,
        metadata: Optional[dict] = None,
    ) -> None:
        """Record a workflow step as a span event with standard attributes."""
        attributes: dict = {
            "workflow.step.name": step_name,
            "workflow.step.type": step_type,
            "workflow.step.success": success,
        }

        if duration_ms is not None:
            attributes["workflow.step.duration_ms"] = duration_ms

        if metadata:
            for key, value in metadata.items():
                attributes[f"workflow.step.{key}"] = str(value)

        self.add_span_event(f"workflow.{step_name}", attributes)


# ------------------------------------------------------------------
# Singleton
# ------------------------------------------------------------------

_observability_manager: ObservabilityManager | None = None


def get_observability_manager() -> ObservabilityManager:
    """Return the global ObservabilityManager singleton (lazy-init)."""
    global _observability_manager

    if _observability_manager is None:
        from src.config import settings

        _observability_manager = ObservabilityManager(
            service_name=settings.OTEL_SERVICE_NAME,
            enabled=settings.AGENT_OBSERVABILITY_ENABLED,
        )

    return _observability_manager


def initialize_observability(
    service_name: str = "placefinder-mcp",
    enabled: bool = True,
) -> ObservabilityManager:
    """Initialize the global observability manager at startup."""
    global _observability_manager

    _observability_manager = ObservabilityManager(
        service_name=service_name,
        enabled=enabled,
    )

    return _observability_manager
