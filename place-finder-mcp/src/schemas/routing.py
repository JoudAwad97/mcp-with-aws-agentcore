"""Pydantic response models for OpenRouteService tools."""

from pydantic import BaseModel, Field


# --- Directions ---


class RouteStep(BaseModel):
    instruction: str = Field(description="Turn-by-turn instruction text.")
    distance_m: float | None = Field(None, description="Step distance in meters.")
    duration_s: float | None = Field(None, description="Step duration in seconds.")


class RouteSegment(BaseModel):
    distance_km: float = Field(description="Segment distance in kilometres.")
    duration_min: float = Field(description="Segment duration in minutes.")
    steps: list[RouteStep] = Field(description="Turn-by-turn steps within this segment.")


class Route(BaseModel):
    distance_km: float = Field(description="Total route distance in kilometres.")
    duration_min: float = Field(description="Total route duration in minutes.")
    segments: list[RouteSegment] = Field(description="Route segments between waypoints.")


class DirectionsResponse(BaseModel):
    count: int = Field(description="Number of routes returned.")
    routes: list[Route] = Field(description="List of computed routes.")


# --- Geocoding ---


class GeocodedLocation(BaseModel):
    name: str | None = Field(None, description="Place or feature name.")
    label: str | None = Field(None, description="Full human-readable label.")
    latitude: float | None = Field(None, description="Latitude coordinate.")
    longitude: float | None = Field(None, description="Longitude coordinate.")
    locality: str | None = Field(None, description="City or locality name.")
    county: str | None = Field(None, description="County or district.")
    region: str | None = Field(None, description="State or region.")
    country: str | None = Field(None, description="Country name.")
    confidence: float | None = Field(None, description="Geocoding confidence score.")


class GeocodeResponse(BaseModel):
    count: int = Field(description="Number of results returned.")
    results: list[GeocodedLocation] = Field(description="List of geocoded locations.")
