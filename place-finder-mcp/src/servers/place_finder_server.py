"""
Place Finder MCP Server.

Self-contained FastMCP instance with Google Places tools.
Imported into the registry via tool_registry.py.
"""

from fastmcp import FastMCP

from src.clients.google_places_client import GooglePlacesClient
from src.config import settings
from src.infrastructure.trace_decorator import traced
from src.schemas.places import Place, PlaceSearchResponse
from src.utils.formatters import format_place, format_places

place_finder_mcp = FastMCP("place_finder")

# ---------------------------------------------------------------------------
# Lazy client singleton
# ---------------------------------------------------------------------------

_client: GooglePlacesClient | None = None


def _get_client() -> GooglePlacesClient:
    global _client
    if _client is None:
        _client = GooglePlacesClient(api_key=settings.GOOGLE_PLACES_API_KEY)
    return _client


# ---------------------------------------------------------------------------
# MCP Tools
# ---------------------------------------------------------------------------


@place_finder_mcp.tool(
    title="Search Places",
    description=(
        "Search for places worldwide using a free-text query. "
        "Returns names, addresses, ratings, opening hours, and contact details. "
        "Use this when the user wants to find restaurants, hotels, attractions, "
        "or any point of interest by keyword."
    ),
    tags={"places", "search", "google"},
    annotations={
        "title": "Search Places",
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": True,
    },
)
@traced(span_name="mcp.tool.search_places", handler_type="tool")
async def search_places(
    query: str,
    location: str = "",
    max_results: int = 5,
) -> PlaceSearchResponse:
    """Search for places using a text query.

    Args:
        query: What to search for (e.g. "best pizza in New York").
        location: Optional location bias as "latitude,longitude" (e.g. "40.7128,-74.0060").
        max_results: Maximum number of results to return (1-20, default 5).
    """
    client = _get_client()
    location_bias = None
    if location:
        parts = [p.strip() for p in location.split(",")]
        if len(parts) == 2:
            location_bias = {
                "latitude": float(parts[0]),
                "longitude": float(parts[1]),
                "radius": 5000.0,
            }

    places = await client.search_text(
        query=query,
        location_bias=location_bias,
        max_results=max_results,
    )
    return format_places(places)


@place_finder_mcp.tool(
    title="Search Nearby Places",
    description=(
        "Find places within a radius of a specific geographic coordinate. "
        "Useful when the user already has a location (e.g. hotel coordinates) "
        "and wants to discover what is nearby. Supports filtering by place type "
        "such as restaurant, museum, or park."
    ),
    tags={"places", "nearby", "location", "google"},
    annotations={
        "title": "Search Nearby Places",
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": True,
    },
)
@traced(span_name="mcp.tool.search_nearby_places", handler_type="tool")
async def search_nearby_places(
    latitude: float,
    longitude: float,
    radius_meters: float = 1000.0,
    place_type: str = "",
    max_results: int = 5,
) -> PlaceSearchResponse:
    """Search for places near a specific location.

    Args:
        latitude: Center point latitude (e.g. 48.8566 for Paris).
        longitude: Center point longitude (e.g. 2.3522 for Paris).
        radius_meters: Search radius in meters (default 1000).
        place_type: Optional place type filter (e.g. "restaurant", "hotel", "museum").
        max_results: Maximum number of results to return (1-20, default 5).
    """
    client = _get_client()
    places = await client.search_nearby(
        latitude=latitude,
        longitude=longitude,
        radius=radius_meters,
        place_type=place_type or None,
        max_results=max_results,
    )
    return format_places(places)


@place_finder_mcp.tool(
    title="Get Place Details",
    description=(
        "Retrieve detailed information about a specific place using its Google Place ID. "
        "Returns comprehensive data including address, rating, phone, website, "
        "opening hours, and editorial summary. Use this after a search to get "
        "the full details for a place the user is interested in."
    ),
    tags={"places", "details", "google"},
    annotations={
        "title": "Get Place Details",
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": True,
    },
)
@traced(span_name="mcp.tool.get_place_details", handler_type="tool")
async def get_place_details(place_id: str) -> Place:
    """Get detailed information about a specific place.

    Args:
        place_id: The Google Place ID (obtained from search results).
    """
    client = _get_client()
    place = await client.get_place_details(place_id=place_id)
    return format_place(place)
