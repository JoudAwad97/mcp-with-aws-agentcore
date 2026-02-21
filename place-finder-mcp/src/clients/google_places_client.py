"""
Google Places API (New) HTTP client.

Wraps the three core endpoints:
- POST /v1/places:searchText
- POST /v1/places:searchNearby
- GET  /v1/places/{place_id}
"""

import httpx
from loguru import logger

BASE_URL = "https://places.googleapis.com/v1"

SEARCH_FIELD_MASK = ",".join([
    "places.id",
    "places.displayName",
    "places.formattedAddress",
    "places.location",
    "places.rating",
    "places.userRatingCount",
    "places.types",
    "places.regularOpeningHours",
    "places.websiteUri",
    "places.nationalPhoneNumber",
    "places.priceLevel",
    "places.editorialSummary",
])

DETAIL_FIELD_MASK = ",".join([
    "id",
    "displayName",
    "formattedAddress",
    "location",
    "rating",
    "userRatingCount",
    "types",
    "regularOpeningHours",
    "websiteUri",
    "nationalPhoneNumber",
    "priceLevel",
    "editorialSummary",
])


class GooglePlacesClient:
    """Async client for the Google Places API (New)."""

    def __init__(self, api_key: str) -> None:
        if not api_key:
            raise ValueError("GOOGLE_PLACES_API_KEY is not set.")
        self._client = httpx.AsyncClient(
            base_url=BASE_URL,
            headers={
                "X-Goog-Api-Key": api_key,
                "Content-Type": "application/json",
            },
            timeout=10.0,
        )

    async def search_text(
        self,
        query: str,
        location_bias: dict | None = None,
        max_results: int = 5,
    ) -> list[dict]:
        """Text Search — find places matching a free-text query."""
        body: dict = {
            "textQuery": query,
            "pageSize": min(max_results, 20),
        }
        if location_bias:
            body["locationBias"] = {
                "circle": {
                    "center": {
                        "latitude": location_bias["latitude"],
                        "longitude": location_bias["longitude"],
                    },
                    "radius": location_bias.get("radius", 5000.0),
                }
            }

        logger.debug(f"Text search: query={query!r}, max_results={max_results}")
        response = await self._client.post(
            "/places:searchText",
            json=body,
            headers={"X-Goog-FieldMask": SEARCH_FIELD_MASK},
        )
        response.raise_for_status()
        return response.json().get("places", [])

    async def search_nearby(
        self,
        latitude: float,
        longitude: float,
        radius: float,
        place_type: str | None = None,
        max_results: int = 5,
    ) -> list[dict]:
        """Nearby Search — find places within a radius of a point."""
        body: dict = {
            "maxResultCount": min(max_results, 20),
            "locationRestriction": {
                "circle": {
                    "center": {
                        "latitude": latitude,
                        "longitude": longitude,
                    },
                    "radius": radius,
                }
            },
        }
        if place_type:
            body["includedTypes"] = [place_type]

        logger.debug(
            f"Nearby search: lat={latitude}, lng={longitude}, "
            f"radius={radius}, type={place_type}"
        )
        response = await self._client.post(
            "/places:searchNearby",
            json=body,
            headers={"X-Goog-FieldMask": SEARCH_FIELD_MASK},
        )
        response.raise_for_status()
        return response.json().get("places", [])

    async def get_place_details(self, place_id: str) -> dict:
        """Place Details — get detailed info about a specific place."""
        logger.debug(f"Place details: place_id={place_id!r}")
        response = await self._client.get(
            f"/places/{place_id}",
            headers={"X-Goog-FieldMask": DETAIL_FIELD_MASK},
        )
        response.raise_for_status()
        return response.json()

    async def close(self) -> None:
        """Close the underlying HTTP client."""
        await self._client.aclose()
