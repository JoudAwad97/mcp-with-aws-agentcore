"""
OpenRouteService MCP Server.

Self-contained FastMCP instance with routing and geocoding tools.
Imported into the registry via tool_registry.py.
"""

from fastmcp import FastMCP

from src.clients.open_route_service_client import VALID_PROFILES, OpenRouteServiceClient
from src.config import settings
from src.infrastructure.trace_decorator import traced
from src.schemas.routing import DirectionsResponse, GeocodeResponse
from src.utils.route_formatters import format_directions, format_geocode_results

open_route_service_mcp = FastMCP("open_route_service")

# ---------------------------------------------------------------------------
# Lazy client singleton
# ---------------------------------------------------------------------------

_client: OpenRouteServiceClient | None = None


def _get_client() -> OpenRouteServiceClient:
    global _client
    if _client is None:
        _client = OpenRouteServiceClient(
            api_key=settings.OPEN_ROUTE_SERVICE_API_KEY
        )
    return _client


# ---------------------------------------------------------------------------
# MCP Tools
# ---------------------------------------------------------------------------


@open_route_service_mcp.tool(
    title="Get Directions",
    description=(
        "Compute a route between two points with turn-by-turn navigation instructions. "
        "Returns total distance, duration, and step-by-step directions. "
        "Supports driving, cycling, walking, hiking, and wheelchair profiles. "
        "Use this when the user asks how to get from point A to point B."
    ),
    tags={"routing", "directions", "navigation", "openrouteservice"},
    annotations={
        "title": "Get Directions",
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": True,
    },
)
@traced(span_name="mcp.tool.get_directions", handler_type="tool")
async def get_directions(
    start_longitude: float,
    start_latitude: float,
    end_longitude: float,
    end_latitude: float,
    profile: str = "driving-car",
    units: str = "km",
) -> DirectionsResponse:
    """Get route directions between two points with turn-by-turn instructions.

    Args:
        start_longitude: Starting point longitude (e.g. 2.3522 for Paris).
        start_latitude: Starting point latitude (e.g. 48.8566 for Paris).
        end_longitude: Destination longitude.
        end_latitude: Destination latitude.
        profile: Travel mode — one of: driving-car, driving-hgv, cycling-regular,
                 cycling-mountain, cycling-road, cycling-electric, foot-walking,
                 foot-hiking, wheelchair.
        units: Distance units — 'km' or 'mi' (default 'km').
    """
    if profile not in VALID_PROFILES:
        raise ValueError(
            f"Invalid profile '{profile}'. "
            f"Valid profiles: {', '.join(VALID_PROFILES)}"
        )
    client = _get_client()
    data = await client.get_directions(
        coordinates=[
            [start_longitude, start_latitude],
            [end_longitude, end_latitude],
        ],
        profile=profile,
        units=units,
    )
    return format_directions(data)


@open_route_service_mcp.tool(
    title="Geocode Address",
    description=(
        "Convert an address, place name, or landmark into geographic coordinates. "
        "Use this when you need latitude/longitude for a location the user mentioned "
        "by name, before calling directions, weather, or nearby-search tools."
    ),
    tags={"geocoding", "address", "coordinates", "openrouteservice"},
    annotations={
        "title": "Geocode Address",
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": True,
    },
)
@traced(span_name="mcp.tool.geocode", handler_type="tool")
async def geocode(
    address: str,
    max_results: int = 5,
    country: str = "",
) -> GeocodeResponse:
    """Convert an address or place name to geographic coordinates (forward geocoding).

    Args:
        address: Address or place name to geocode (e.g. "Eiffel Tower, Paris").
        max_results: Maximum number of results to return (1-20, default 5).
        country: Optional ISO 3166-1 country code to restrict results (e.g. "FR", "US").
    """
    client = _get_client()
    data = await client.geocode(
        text=address,
        size=max_results,
        boundary_country=country or None,
    )
    return format_geocode_results(data)
