"""Formatting helpers for Google Weather API responses."""


def _get_temp(temp_obj: dict) -> str:
    """Extract temperature string from a Google Weather temperature object."""
    if not temp_obj:
        return "N/A"
    degrees = temp_obj.get("degrees", "N/A")
    return f"{degrees}"


def _get_wind(wind_obj: dict) -> str:
    """Extract wind string from a Google Weather wind object."""
    if not wind_obj:
        return "N/A"
    speed = wind_obj.get("speed", {})
    speed_val = speed.get("value", "N/A")
    speed_unit = speed.get("unit", "")
    direction = wind_obj.get("direction", {})
    cardinal = direction.get("cardinal", "")
    degrees = direction.get("degrees", "")
    gust = wind_obj.get("gust", {})
    gust_val = gust.get("value", "")

    parts = [f"{speed_val} {speed_unit}".strip()]
    if cardinal:
        parts.append(f"from {cardinal} ({degrees}°)")
    if gust_val:
        parts.append(f"gusts {gust_val} {speed_unit}".strip())
    return ", ".join(parts)


def format_current_weather(data: dict) -> str:
    """Format Google Weather currentConditions response into a readable string."""
    condition = data.get("weatherCondition", {})
    condition_desc = condition.get("description", {}).get("text", "Unknown")
    condition_type = condition.get("type", "")

    temp = _get_temp(data.get("temperature", {}))
    feels_like = _get_temp(data.get("feelsLikeTemperature", {}))
    humidity = data.get("relativeHumidity", "N/A")
    uv_index = data.get("uvIndex", "N/A")
    cloud_cover = data.get("cloudCover", "N/A")
    is_daytime = data.get("isDaytime", True)

    dew_point = _get_temp(data.get("dewPoint", {}))
    visibility = data.get("visibility", {})
    vis_val = visibility.get("value", "N/A")
    vis_unit = visibility.get("unit", "")

    pressure = data.get("airPressure", {})
    pressure_val = pressure.get("meanSeaLevelMillibars", "N/A")

    wind_str = _get_wind(data.get("wind", {}))

    precip = data.get("precipitation", {})
    precip_prob = precip.get("probability", {}).get("percent", 0)
    precip_type = precip.get("type", "NONE")

    current_time = data.get("currentTime", "")
    timezone = data.get("timeZone", {}).get("id", "")

    lines = [
        f"Condition: {condition_desc}" + (f" ({condition_type})" if condition_type else ""),
        f"Temperature: {temp}°C (feels like {feels_like}°C)",
        f"Humidity: {humidity}%",
        f"Dew Point: {dew_point}°C",
        f"Cloud Cover: {cloud_cover}%",
        f"UV Index: {uv_index}",
        f"Wind: {wind_str}",
        f"Precipitation: {precip_type}, probability {precip_prob}%",
        f"Visibility: {vis_val} {vis_unit}".strip(),
        f"Pressure: {pressure_val} mbar",
        f"Time of Day: {'Day' if is_daytime else 'Night'}",
    ]
    if timezone:
        lines.append(f"Timezone: {timezone}")
    if current_time:
        lines.append(f"Observation Time: {current_time}")

    return "\n".join(lines)


def format_forecast(data: dict) -> str:
    """Format Google Weather daily forecast response into a readable string."""
    forecast_days = data.get("forecastDays", [])
    if not forecast_days:
        return "No forecast data available."

    timezone = data.get("timeZone", {}).get("id", "")
    parts = []

    for day in forecast_days:
        display_date = day.get("displayDate", {})
        date_str = f"{display_date.get('year', '')}-{display_date.get('month', ''):02d}-{display_date.get('day', ''):02d}"

        temp_max = _get_temp(day.get("maxTemperature", {}))
        temp_min = _get_temp(day.get("minTemperature", {}))

        daytime = day.get("daytimeForecast", {})
        daytime_condition = daytime.get("weatherCondition", {}).get("description", {}).get("text", "N/A")

        nighttime = day.get("nighttimeForecast", {})
        nighttime_condition = nighttime.get("weatherCondition", {}).get("description", {}).get("text", "N/A")

        humidity = day.get("relativeHumidity", "N/A")
        uv_index = day.get("uvIndex", "N/A")

        precip = day.get("precipitation", {})
        precip_prob = precip.get("probability", {}).get("percent", 0)
        precip_qty = precip.get("qpf", {})
        precip_val = precip_qty.get("value", 0)
        precip_unit = precip_qty.get("unit", "mm")

        wind_str = _get_wind(day.get("wind", {}))

        sun_events = day.get("sunEvents", {})
        sunrise = sun_events.get("sunrise", "N/A")
        sunset = sun_events.get("sunset", "N/A")

        lines = [
            f"--- {date_str} ---",
            f"Day: {daytime_condition} | Night: {nighttime_condition}",
            f"Temperature: {temp_min}°C to {temp_max}°C",
            f"Humidity: {humidity}%",
            f"Precipitation: {precip_val} {precip_unit} (probability {precip_prob}%)",
            f"Wind: {wind_str}",
            f"UV Index: {uv_index}",
            f"Sunrise: {sunrise} | Sunset: {sunset}",
        ]
        parts.append("\n".join(lines))

    header = f"Timezone: {timezone}\n\n" if timezone else ""
    return header + "\n\n".join(parts)
