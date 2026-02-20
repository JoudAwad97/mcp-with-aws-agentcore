"""Formatting helpers for Google Places API responses."""


def format_place(place: dict) -> str:
    """Format a single place dict into a readable string."""
    name = place.get("displayName", {}).get("text", "Unknown")
    address = place.get("formattedAddress", "N/A")
    location = place.get("location", {})
    lat = location.get("latitude", "")
    lng = location.get("longitude", "")
    rating = place.get("rating", "N/A")
    rating_count = place.get("userRatingCount", 0)
    phone = place.get("nationalPhoneNumber", "N/A")
    website = place.get("websiteUri", "N/A")
    price = place.get("priceLevel", "N/A")
    types = ", ".join(place.get("types", []))
    summary = place.get("editorialSummary", {}).get("text", "")
    place_id = place.get("id", "")

    hours_obj = place.get("regularOpeningHours", {})
    hours_text = "; ".join(hours_obj.get("weekdayDescriptions", []))

    lines = [
        f"Name: {name}",
        f"Address: {address}",
        f"Location: {lat}, {lng}",
        f"Rating: {rating} ({rating_count} reviews)",
        f"Phone: {phone}",
        f"Website: {website}",
        f"Price Level: {price}",
        f"Types: {types}",
    ]
    if summary:
        lines.append(f"Summary: {summary}")
    if hours_text:
        lines.append(f"Hours: {hours_text}")
    if place_id:
        lines.append(f"Place ID: {place_id}")

    return "\n".join(lines)


def format_places(places: list[dict]) -> str:
    """Format a list of places into a numbered result string."""
    if not places:
        return "No places found."
    parts = []
    for i, place in enumerate(places, 1):
        parts.append(f"--- Result {i} ---\n{format_place(place)}")
    return "\n\n".join(parts)
