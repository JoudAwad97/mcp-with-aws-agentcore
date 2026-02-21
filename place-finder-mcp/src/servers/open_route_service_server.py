"""
OpenRouteService MCP Server.

Self-contained FastMCP instance with routing, geocoding, isochrone, and matrix tools.
Imported into the registry via tool_registry.py.
"""

import httpx
from loguru import logger
from fastmcp import FastMCP

from src.clients.open_route_service_client import OpenRouteServiceClient, VALID_PROFILES
from src.config import settings
from src.utils.route_formatters import (
    format_directions,
    format_geocode_results,
    format_isochrones,
    format_matrix,
)

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


@open_route_service_mcp.tool()
async def get_directions(
    start_longitude: float,
    start_latitude: float,
    end_longitude: float,
    end_latitude: float,
    profile: str = "driving-car",
    units: str = "km",
) -> str:
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
    try:
        if profile not in VALID_PROFILES:
            return (
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
    except httpx.HTTPStatusError as e:
        logger.error(f"ORS API error: {e.response.status_code} - {e.response.text}")
        return f"Error getting directions: {e.response.status_code}"
    except Exception as e:
        logger.error(f"Unexpected error in get_directions: {e}")
        return f"Error getting directions: {e}"


@open_route_service_mcp.tool()
async def get_directions_multi_stop(
    longitudes: list[float],
    latitudes: list[float],
    profile: str = "driving-car",
    units: str = "km",
) -> str:
    """Get route directions through multiple waypoints (multi-stop routing).

    Args:
        longitudes: List of longitudes for each waypoint in order.
        latitudes: List of latitudes for each waypoint in order (same length as longitudes).
        profile: Travel mode — one of: driving-car, driving-hgv, cycling-regular,
                 cycling-mountain, cycling-road, cycling-electric, foot-walking,
                 foot-hiking, wheelchair.
        units: Distance units — 'km' or 'mi' (default 'km').
    """
    try:
        if len(longitudes) != len(latitudes):
            return "Error: longitudes and latitudes must have the same length."
        if len(longitudes) < 2:
            return "Error: at least 2 waypoints are required."
        if profile not in VALID_PROFILES:
            return (
                f"Invalid profile '{profile}'. "
                f"Valid profiles: {', '.join(VALID_PROFILES)}"
            )

        client = _get_client()
        coordinates = [
            [lon, lat] for lon, lat in zip(longitudes, latitudes)
        ]
        data = await client.get_directions(
            coordinates=coordinates,
            profile=profile,
            units=units,
        )
        return format_directions(data)
    except httpx.HTTPStatusError as e:
        logger.error(f"ORS API error: {e.response.status_code} - {e.response.text}")
        return f"Error getting directions: {e.response.status_code}"
    except Exception as e:
        logger.error(f"Unexpected error in get_directions_multi_stop: {e}")
        return f"Error getting directions: {e}"


@open_route_service_mcp.tool()
async def geocode(
    address: str,
    max_results: int = 5,
    country: str = "",
) -> str:
    """Convert an address or place name to geographic coordinates (forward geocoding).

    Args:
        address: Address or place name to geocode (e.g. "Eiffel Tower, Paris").
        max_results: Maximum number of results to return (1-20, default 5).
        country: Optional ISO 3166-1 country code to restrict results (e.g. "FR", "US").
    """
    try:
        client = _get_client()
        data = await client.geocode(
            text=address,
            size=max_results,
            boundary_country=country or None,
        )
        return format_geocode_results(data)
    except httpx.HTTPStatusError as e:
        logger.error(f"ORS API error: {e.response.status_code} - {e.response.text}")
        return f"Error geocoding address: {e.response.status_code}"
    except Exception as e:
        logger.error(f"Unexpected error in geocode: {e}")
        return f"Error geocoding address: {e}"


@open_route_service_mcp.tool()
async def reverse_geocode(
    latitude: float,
    longitude: float,
) -> str:
    """Convert geographic coordinates to a human-readable address (reverse geocoding).

    Args:
        latitude: Latitude of the point (e.g. 48.8566).
        longitude: Longitude of the point (e.g. 2.3522).
    """
    try:
        client = _get_client()
        data = await client.reverse_geocode(
            latitude=latitude,
            longitude=longitude,
        )
        return format_geocode_results(data)
    except httpx.HTTPStatusError as e:
        logger.error(f"ORS API error: {e.response.status_code} - {e.response.text}")
        return f"Error reverse geocoding: {e.response.status_code}"
    except Exception as e:
        logger.error(f"Unexpected error in reverse_geocode: {e}")
        return f"Error reverse geocoding: {e}"


@open_route_service_mcp.tool()
async def get_isochrones(
    longitude: float,
    latitude: float,
    range_minutes: list[int],
    profile: str = "driving-car",
) -> str:
    """Calculate reachable areas (isochrones) from a location within given time limits.

    Useful for answering questions like "What can I reach within 15 minutes by car?"

    Args:
        longitude: Origin point longitude.
        latitude: Origin point latitude.
        range_minutes: List of time limits in minutes (e.g. [5, 10, 15]).
        profile: Travel mode — one of: driving-car, driving-hgv, cycling-regular,
                 cycling-mountain, cycling-road, cycling-electric, foot-walking,
                 foot-hiking, wheelchair.
    """
    try:
        if profile not in VALID_PROFILES:
            return (
                f"Invalid profile '{profile}'. "
                f"Valid profiles: {', '.join(VALID_PROFILES)}"
            )
        client = _get_client()
        range_seconds = [m * 60 for m in range_minutes]
        data = await client.get_isochrones(
            locations=[[longitude, latitude]],
            range_seconds=range_seconds,
            profile=profile,
            range_type="time",
        )
        return format_isochrones(data)
    except httpx.HTTPStatusError as e:
        logger.error(f"ORS API error: {e.response.status_code} - {e.response.text}")
        return f"Error calculating isochrones: {e.response.status_code}"
    except Exception as e:
        logger.error(f"Unexpected error in get_isochrones: {e}")
        return f"Error calculating isochrones: {e}"


@open_route_service_mcp.tool()
async def get_distance_matrix(
    longitudes: list[float],
    latitudes: list[float],
    profile: str = "driving-car",
    units: str = "km",
) -> str:
    """Compute a distance and duration matrix between multiple locations.

    Useful for comparing travel times between several points (e.g. hotels and attractions).

    Args:
        longitudes: List of longitudes for each location.
        latitudes: List of latitudes for each location (same length as longitudes).
        profile: Travel mode — one of: driving-car, driving-hgv, cycling-regular,
                 cycling-mountain, cycling-road, cycling-electric, foot-walking,
                 foot-hiking, wheelchair.
        units: Distance units — 'km' or 'mi' (default 'km').
    """
    try:
        if len(longitudes) != len(latitudes):
            return "Error: longitudes and latitudes must have the same length."
        if len(longitudes) < 2:
            return "Error: at least 2 locations are required."
        if profile not in VALID_PROFILES:
            return (
                f"Invalid profile '{profile}'. "
                f"Valid profiles: {', '.join(VALID_PROFILES)}"
            )

        client = _get_client()
        locations = [
            [lon, lat] for lon, lat in zip(longitudes, latitudes)
        ]
        data = await client.get_matrix(
            locations=locations,
            profile=profile,
            units=units,
        )
        return format_matrix(data)
    except httpx.HTTPStatusError as e:
        logger.error(f"ORS API error: {e.response.status_code} - {e.response.text}")
        return f"Error computing distance matrix: {e.response.status_code}"
    except Exception as e:
        logger.error(f"Unexpected error in get_distance_matrix: {e}")
        return f"Error computing distance matrix: {e}"
