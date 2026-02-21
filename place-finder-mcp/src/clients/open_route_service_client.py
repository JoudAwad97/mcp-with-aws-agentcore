"""
OpenRouteService API HTTP client.

Wraps the core endpoints:
- POST /v2/directions/{profile}   — route between waypoints
- GET  /geocode/search            — forward geocoding
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
            f"/v2/directions/{profile}",
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

    async def close(self) -> None:
        """Close the underlying HTTP client."""
        await self._client.aclose()
