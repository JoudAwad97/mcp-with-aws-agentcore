"""Formatting helpers for Google Weather API responses."""

from src.schemas.weather import (
    CurrentWeatherResponse,
    ForecastDay,
    ForecastPrecipitation,
    ForecastResponse,
    Precipitation,
    Visibility,
    Wind,
)


def _extract_temp(temp_obj: dict) -> float | None:
    """Extract temperature value from a Google Weather temperature object."""
    if not temp_obj:
        return None
    return temp_obj.get("degrees")


def _extract_wind(wind_obj: dict) -> Wind | None:
    """Extract wind data from a Google Weather wind object."""
    if not wind_obj:
        return None
    speed = wind_obj.get("speed", {})
    direction = wind_obj.get("direction", {})
    gust = wind_obj.get("gust", {})

    return Wind(
        speed_value=speed.get("value"),
        speed_unit=speed.get("unit"),
        direction_cardinal=direction.get("cardinal"),
        direction_degrees=direction.get("degrees"),
        gust_value=gust.get("value"),
    )


def format_current_weather(data: dict) -> CurrentWeatherResponse:
    """Format Google Weather currentConditions into a CurrentWeatherResponse model."""
    condition = data.get("weatherCondition", {})
    visibility = data.get("visibility", {})
    pressure = data.get("airPressure", {})
    precip = data.get("precipitation", {})

    return CurrentWeatherResponse(
        condition=condition.get("description", {}).get("text"),
        condition_type=condition.get("type"),
        temperature_c=_extract_temp(data.get("temperature", {})),
        feels_like_c=_extract_temp(data.get("feelsLikeTemperature", {})),
        humidity_percent=data.get("relativeHumidity"),
        dew_point_c=_extract_temp(data.get("dewPoint", {})),
        cloud_cover_percent=data.get("cloudCover"),
        uv_index=data.get("uvIndex"),
        wind=_extract_wind(data.get("wind", {})),
        precipitation=Precipitation(
            type=precip.get("type"),
            probability_percent=precip.get("probability", {}).get("percent"),
        ),
        visibility=Visibility(
            value=visibility.get("value"),
            unit=visibility.get("unit"),
        ),
        pressure_mbar=pressure.get("meanSeaLevelMillibars"),
        is_daytime=data.get("isDaytime"),
        timezone=data.get("timeZone", {}).get("id"),
        observation_time=data.get("currentTime"),
    )


def format_forecast(data: dict) -> ForecastResponse:
    """Format Google Weather daily forecast into a ForecastResponse model."""
    forecast_days = data.get("forecastDays", [])

    days = []
    for day in forecast_days:
        display_date = day.get("displayDate", {})
        daytime = day.get("daytimeForecast", {})
        nighttime = day.get("nighttimeForecast", {})
        precip = day.get("precipitation", {})
        precip_qty = precip.get("qpf", {})
        sun_events = day.get("sunEvents", {})

        days.append(ForecastDay(
            date=(
                f"{display_date.get('year', '')}-"
                f"{display_date.get('month', 0):02d}-"
                f"{display_date.get('day', 0):02d}"
            ),
            max_temperature_c=_extract_temp(day.get("maxTemperature", {})),
            min_temperature_c=_extract_temp(day.get("minTemperature", {})),
            daytime_condition=(
                daytime.get("weatherCondition", {})
                .get("description", {})
                .get("text")
            ),
            nighttime_condition=(
                nighttime.get("weatherCondition", {})
                .get("description", {})
                .get("text")
            ),
            humidity_percent=day.get("relativeHumidity"),
            uv_index=day.get("uvIndex"),
            precipitation=ForecastPrecipitation(
                probability_percent=precip.get("probability", {}).get("percent"),
                amount=precip_qty.get("value"),
                unit=precip_qty.get("unit"),
            ),
            wind=_extract_wind(day.get("wind", {})),
            sunrise=sun_events.get("sunrise"),
            sunset=sun_events.get("sunset"),
        ))

    return ForecastResponse(
        timezone=data.get("timeZone", {}).get("id"),
        days=days,
    )
