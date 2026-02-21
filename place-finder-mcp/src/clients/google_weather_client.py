"""
Google Weather API HTTP client.

Wraps the core endpoints:
- GET /v1/currentConditions:lookup   (current weather)
- GET /v1/forecast/days:lookup       (daily forecast)

Uses the same Google API key as the Places API.
"""

import httpx
from loguru import logger

BASE_URL = "https://weather.googleapis.com/v1"


class GoogleWeatherClient:
    """Async client for the Google Weather API."""

    def __init__(self, api_key: str) -> None:
        if not api_key:
            raise ValueError("GOOGLE_PLACES_API_KEY is not set (used for Weather API too).")
        self._api_key = api_key
        self._client = httpx.AsyncClient(timeout=10.0)

    async def get_current_conditions(
        self, latitude: float, longitude: float
    ) -> dict:
        """Get current weather conditions for a location."""
        logger.debug(f"Current conditions: lat={latitude}, lng={longitude}")
        response = await self._client.get(
            f"{BASE_URL}/currentConditions:lookup",
            params={
                "key": self._api_key,
                "location.latitude": latitude,
                "location.longitude": longitude,
            },
        )
        response.raise_for_status()
        return response.json()

    async def get_daily_forecast(
        self,
        latitude: float,
        longitude: float,
        days: int = 5,
    ) -> dict:
        """Get daily weather forecast for a location (up to 10 days)."""
        logger.debug(f"Daily forecast: lat={latitude}, lng={longitude}, days={days}")
        response = await self._client.get(
            f"{BASE_URL}/forecast/days:lookup",
            params={
                "key": self._api_key,
                "location.latitude": latitude,
                "location.longitude": longitude,
                "days": min(days, 10),
            },
        )
        response.raise_for_status()
        return response.json()

    async def close(self) -> None:
        """Close the underlying HTTP client."""
        await self._client.aclose()
