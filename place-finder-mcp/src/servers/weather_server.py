"""
Weather MCP Server.

Self-contained FastMCP instance with Google Weather API tools.
Mounted into the registry via tool_registry.py.
"""

from fastmcp import FastMCP

from src.clients.google_weather_client import GoogleWeatherClient
from src.config import settings
from src.schemas.weather import CurrentWeatherResponse, ForecastResponse
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


@weather_mcp.tool(
    title="Get Current Weather",
    description=(
        "Get real-time weather conditions for any location on Earth. "
        "Returns temperature, humidity, wind, precipitation, UV index, "
        "cloud cover, visibility, and atmospheric pressure. "
        "Use this when the user asks about current weather at a destination."
    ),
    tags={"weather", "current", "conditions", "google"},
    annotations={
        "title": "Get Current Weather",
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": True,
    },
)
async def get_current_weather(
    latitude: float,
    longitude: float,
) -> CurrentWeatherResponse:
    """Get current weather conditions for a location.

    Args:
        latitude: Location latitude (e.g. 48.8566 for Paris).
        longitude: Location longitude (e.g. 2.3522 for Paris).
    """
    client = _get_client()
    data = await client.get_current_conditions(latitude=latitude, longitude=longitude)
    return format_current_weather(data)


@weather_mcp.tool(
    title="Get Weather Forecast",
    description=(
        "Get a multi-day weather forecast for any location on Earth. "
        "Returns daily high/low temperatures, daytime and nighttime conditions, "
        "precipitation probability, wind, UV index, and sunrise/sunset times. "
        "Use this when the user is planning a trip and needs to know future weather."
    ),
    tags={"weather", "forecast", "planning", "google"},
    annotations={
        "title": "Get Weather Forecast",
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": True,
    },
)
async def get_weather_forecast(
    latitude: float,
    longitude: float,
    forecast_days: int = 5,
) -> ForecastResponse:
    """Get daily weather forecast for a location (up to 10 days).

    Args:
        latitude: Location latitude (e.g. 48.8566 for Paris).
        longitude: Location longitude (e.g. 2.3522 for Paris).
        forecast_days: Number of forecast days (1-10, default 5).
    """
    client = _get_client()
    data = await client.get_daily_forecast(
        latitude=latitude,
        longitude=longitude,
        days=min(forecast_days, 10),
    )
    return format_forecast(data)
