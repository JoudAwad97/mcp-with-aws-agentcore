"""
Place Finder MCP Server.

Self-contained FastMCP instance with Google Places tools.
Imported into the registry via import_server().
"""

import httpx
from loguru import logger
from fastmcp import FastMCP

from src.clients.google_places import GooglePlacesClient
from src.config import settings
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


@place_finder_mcp.tool()
async def search_places(
    query: str,
    location: str = "",
    max_results: int = 5,
) -> str:
    """Search for places using a text query.

    Args:
        query: What to search for (e.g. "best pizza in New York").
        location: Optional location bias as "latitude,longitude" (e.g. "40.7128,-74.0060").
        max_results: Maximum number of results to return (1-20, default 5).
    """
    try:
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
    except httpx.HTTPStatusError as e:
        logger.error(f"Google Places API error: {e.response.status_code} - {e.response.text}")
        return f"Error searching places: {e.response.status_code}"
    except Exception as e:
        logger.error(f"Unexpected error in search_places: {e}")
        return f"Error searching places: {e}"


@place_finder_mcp.tool()
async def search_nearby_places(
    latitude: float,
    longitude: float,
    radius_meters: float = 1000.0,
    place_type: str = "",
    max_results: int = 5,
) -> str:
    """Search for places near a specific location.

    Args:
        latitude: Center point latitude (e.g. 48.8566 for Paris).
        longitude: Center point longitude (e.g. 2.3522 for Paris).
        radius_meters: Search radius in meters (default 1000).
        place_type: Optional place type filter (e.g. "restaurant", "hotel", "museum").
        max_results: Maximum number of results to return (1-20, default 5).
    """
    try:
        client = _get_client()
        places = await client.search_nearby(
            latitude=latitude,
            longitude=longitude,
            radius=radius_meters,
            place_type=place_type or None,
            max_results=max_results,
        )
        return format_places(places)
    except httpx.HTTPStatusError as e:
        logger.error(f"Google Places API error: {e.response.status_code} - {e.response.text}")
        return f"Error searching nearby places: {e.response.status_code}"
    except Exception as e:
        logger.error(f"Unexpected error in search_nearby_places: {e}")
        return f"Error searching nearby places: {e}"


@place_finder_mcp.tool()
async def get_place_details(place_id: str) -> str:
    """Get detailed information about a specific place.

    Args:
        place_id: The Google Place ID (obtained from search results).
    """
    try:
        client = _get_client()
        place = await client.get_place_details(place_id=place_id)
        return format_place(place)
    except httpx.HTTPStatusError as e:
        logger.error(f"Google Places API error: {e.response.status_code} - {e.response.text}")
        return f"Error getting place details: {e.response.status_code}"
    except Exception as e:
        logger.error(f"Unexpected error in get_place_details: {e}")
        return f"Error getting place details: {e}"
