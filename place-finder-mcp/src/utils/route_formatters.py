"""Formatting helpers for OpenRouteService API responses."""

from src.schemas.routing import (
    DirectionsResponse,
    GeocodedLocation,
    GeocodeResponse,
    Route,
    RouteSegment,
    RouteStep,
)


def format_directions(data: dict) -> DirectionsResponse:
    """Format a directions response into a DirectionsResponse model."""
    raw_routes = data.get("routes", [])

    routes = []
    for route in raw_routes:
        summary = route.get("summary", {})

        segments = []
        for segment in route.get("segments", []):
            steps = []
            for step in segment.get("steps", []):
                instruction = step.get("instruction")
                if instruction:
                    steps.append(RouteStep(
                        instruction=instruction,
                        distance_m=step.get("distance"),
                        duration_s=step.get("duration"),
                    ))

            segments.append(RouteSegment(
                distance_km=round(segment.get("distance", 0) / 1000, 2),
                duration_min=round(segment.get("duration", 0) / 60, 1),
                steps=steps,
            ))

        routes.append(Route(
            distance_km=round(summary.get("distance", 0) / 1000, 2),
            duration_min=round(summary.get("duration", 0) / 60, 1),
            segments=segments,
        ))

    return DirectionsResponse(
        count=len(routes),
        routes=routes,
    )


def format_geocode_results(data: dict) -> GeocodeResponse:
    """Format geocoding results into a GeocodeResponse model."""
    features = data.get("features", [])

    results = []
    for feature in features:
        props = feature.get("properties", {})
        coords = feature.get("geometry", {}).get("coordinates", [])

        results.append(GeocodedLocation(
            name=props.get("name"),
            label=props.get("label"),
            latitude=coords[1] if len(coords) > 1 else None,
            longitude=coords[0] if len(coords) > 0 else None,
            locality=props.get("locality"),
            county=props.get("county"),
            region=props.get("region"),
            country=props.get("country"),
            confidence=props.get("confidence"),
        ))

    return GeocodeResponse(
        count=len(results),
        results=results,
    )
