"""
OpenRouteService API HTTP client.

Wraps the core endpoints:
- POST /v2/directions/{profile}   — route between waypoints
- GET  /geocode/search            — forward geocoding
- GET  /geocode/reverse           — reverse geocoding
- POST /v2/isochrones/{profile}   — reachability polygons
- POST /v2/matrix/{profile}       — distance / duration matrix
"""

import httpx
from loguru import logger

BASE_URL = "https://api.openrouteservice.org"

VALID_PROFILES = [
    "driving-car",
    "driving-hgv",
    "cycling-regular",
    "cycling-mountain",
    "cycling-road",
    "cycling-electric",
    "foot-walking",
    "foot-hiking",
    "wheelchair",
]


class OpenRouteServiceClient:
    """Async client for the OpenRouteService API."""

    def __init__(self, api_key: str) -> None:
        if not api_key:
            raise ValueError("OPEN_ROUTE_SERVICE_API_KEY is not set.")
        self._client = httpx.AsyncClient(
            base_url=BASE_URL,
            headers={
                "Authorization": api_key,
                "Content-Type": "application/json",
                "Accept": "application/json, application/geo+json",
            },
            timeout=15.0,
        )

    async def get_directions(
        self,
        coordinates: list[list[float]],
        profile: str = "driving-car",
        language: str = "en",
        units: str = "km",
        geometry: bool = True,
        instructions: bool = True,
    ) -> dict:
        """Get route directions between waypoints.

        Args:
            coordinates: List of [longitude, latitude] pairs.
            profile: Routing profile (e.g. driving-car, foot-walking).
            language: Language for instructions.
            units: Distance units (km or mi).
            geometry: Whether to include route geometry.
            instructions: Whether to include turn-by-turn instructions.
        """
        body = {
            "coordinates": coordinates,
            "language": language,
            "units": units,
            "geometry": geometry,
            "instructions": instructions,
        }

        logger.debug(
            f"Directions: profile={profile}, waypoints={len(coordinates)}"
        )
        response = await self._client.post(
            f"/v2/directions/{profile}/json",
            json=body,
        )
        response.raise_for_status()
        return response.json()

    async def geocode(
        self,
        text: str,
        size: int = 5,
        boundary_country: str | None = None,
    ) -> dict:
        """Forward geocode — convert an address or place name to coordinates.

        Args:
            text: Address or place name to geocode.
            size: Maximum number of results.
            boundary_country: Optional ISO 3166-1 country code to restrict results.
        """
        params: dict = {
            "api_key": self._client.headers["Authorization"],
            "text": text,
            "size": min(size, 20),
        }
        if boundary_country:
            params["boundary.country"] = boundary_country

        logger.debug(f"Geocode: text={text!r}, size={size}")
        response = await self._client.get("/geocode/search", params=params)
        response.raise_for_status()
        return response.json()

    async def reverse_geocode(
        self,
        latitude: float,
        longitude: float,
        size: int = 1,
    ) -> dict:
        """Reverse geocode — convert coordinates to an address.

        Args:
            latitude: Latitude of the point.
            longitude: Longitude of the point.
            size: Number of results to return.
        """
        params = {
            "api_key": self._client.headers["Authorization"],
            "point.lat": latitude,
            "point.lon": longitude,
            "size": size,
        }

        logger.debug(f"Reverse geocode: lat={latitude}, lon={longitude}")
        response = await self._client.get("/geocode/reverse", params=params)
        response.raise_for_status()
        return response.json()

    async def get_isochrones(
        self,
        locations: list[list[float]],
        range_seconds: list[int],
        profile: str = "driving-car",
        range_type: str = "time",
    ) -> dict:
        """Calculate isochrones (reachability areas) from locations.

        Args:
            locations: List of [longitude, latitude] origin points.
            range_seconds: List of range values in seconds (time) or meters (distance).
            profile: Routing profile.
            range_type: 'time' (seconds) or 'distance' (meters).
        """
        body = {
            "locations": locations,
            "range": range_seconds,
            "range_type": range_type,
        }

        logger.debug(
            f"Isochrones: profile={profile}, locations={len(locations)}, "
            f"ranges={range_seconds}"
        )
        response = await self._client.post(
            f"/v2/isochrones/{profile}",
            json=body,
        )
        response.raise_for_status()
        return response.json()

    async def get_matrix(
        self,
        locations: list[list[float]],
        profile: str = "driving-car",
        metrics: list[str] | None = None,
        units: str = "km",
    ) -> dict:
        """Compute a distance/duration matrix between locations.

        Args:
            locations: List of [longitude, latitude] points.
            profile: Routing profile.
            metrics: List of metrics to compute ('distance', 'duration').
            units: Distance units (km or mi).
        """
        body: dict = {
            "locations": locations,
            "metrics": metrics or ["distance", "duration"],
            "units": units,
        }

        logger.debug(
            f"Matrix: profile={profile}, locations={len(locations)}"
        )
        response = await self._client.post(
            f"/v2/matrix/{profile}/json",
            json=body,
        )
        response.raise_for_status()
        return response.json()

    async def close(self) -> None:
        """Close the underlying HTTP client."""
        await self._client.aclose()
