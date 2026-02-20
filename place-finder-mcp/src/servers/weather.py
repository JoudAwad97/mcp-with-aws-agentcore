"""
Weather MCP Server.

Self-contained FastMCP instance with Google Weather API tools.
Mounted into the registry via tool_registry.py.
"""

import httpx
from loguru import logger
from fastmcp import FastMCP

from src.clients.google_weather import GoogleWeatherClient
from src.config import settings
from src.utils.weather_formatters import format_current_weather, format_forecast

weather_mcp = FastMCP("weather")

# ---------------------------------------------------------------------------
# Lazy client singleton
# ---------------------------------------------------------------------------

_client: GoogleWeatherClient | None = None


def _get_client() -> GoogleWeatherClient:
    global _client
    if _client is None:
        _client = GoogleWeatherClient(api_key=settings.GOOGLE_PLACES_API_KEY)
    return _client


# ---------------------------------------------------------------------------
# MCP Tools
# ---------------------------------------------------------------------------


@weather_mcp.tool()
async def get_current_weather(
    latitude: float,
    longitude: float,
) -> str:
    """Get current weather conditions for a location.

    Args:
        latitude: Location latitude (e.g. 48.8566 for Paris).
        longitude: Location longitude (e.g. 2.3522 for Paris).
    """
    try:
        client = _get_client()
        data = await client.get_current_conditions(latitude=latitude, longitude=longitude)
        return format_current_weather(data)
    except httpx.HTTPStatusError as e:
        logger.error(f"Google Weather API error: {e.response.status_code} - {e.response.text}")
        return f"Error getting current weather: {e.response.status_code}"
    except Exception as e:
        logger.error(f"Unexpected error in get_current_weather: {e}")
        return f"Error getting current weather: {e}"


@weather_mcp.tool()
async def get_weather_forecast(
    latitude: float,
    longitude: float,
    forecast_days: int = 5,
) -> str:
    """Get daily weather forecast for a location (up to 10 days).

    Args:
        latitude: Location latitude (e.g. 48.8566 for Paris).
        longitude: Location longitude (e.g. 2.3522 for Paris).
        forecast_days: Number of forecast days (1-10, default 5).
    """
    try:
        client = _get_client()
        data = await client.get_daily_forecast(
            latitude=latitude,
            longitude=longitude,
            days=min(forecast_days, 10),
        )
        return format_forecast(data)
    except httpx.HTTPStatusError as e:
        logger.error(f"Google Weather API error: {e.response.status_code} - {e.response.text}")
        return f"Error getting weather forecast: {e.response.status_code}"
    except Exception as e:
        logger.error(f"Unexpected error in get_weather_forecast: {e}")
        return f"Error getting weather forecast: {e}"
