"""Formatting helpers for OpenRouteService API responses."""


def format_directions(data: dict) -> str:
    """Format a directions response into a readable string."""
    routes = data.get("routes", [])
    if not routes:
        return "No route found."

    parts = []
    for i, route in enumerate(routes, 1):
        summary = route.get("summary", {})
        distance_km = summary.get("distance", 0) / 1000
        duration_min = summary.get("duration", 0) / 60

        lines = [
            f"--- Route {i} ---",
            f"Distance: {distance_km:.1f} km",
            f"Duration: {duration_min:.0f} minutes",
        ]

        segments = route.get("segments", [])
        for seg_idx, segment in enumerate(segments, 1):
            seg_dist = segment.get("distance", 0) / 1000
            seg_dur = segment.get("duration", 0) / 60
            lines.append(f"\nSegment {seg_idx}: {seg_dist:.1f} km, {seg_dur:.0f} min")

            steps = segment.get("steps", [])
            for step in steps:
                instruction = step.get("instruction", "")
                step_dist = step.get("distance", 0)
                step_dur = step.get("duration", 0)
                if instruction:
                    dist_str = (
                        f"{step_dist:.0f} m"
                        if step_dist < 1000
                        else f"{step_dist / 1000:.1f} km"
                    )
                    lines.append(
                        f"  - {instruction} ({dist_str}, {step_dur:.0f}s)"
                    )

        parts.append("\n".join(lines))

    return "\n\n".join(parts)


def format_geocode_results(data: dict) -> str:
    """Format geocoding results into a readable string."""
    features = data.get("features", [])
    if not features:
        return "No results found."

    parts = []
    for i, feature in enumerate(features, 1):
        props = feature.get("properties", {})
        coords = feature.get("geometry", {}).get("coordinates", [])

        name = props.get("name", "Unknown")
        label = props.get("label", "N/A")
        country = props.get("country", "")
        region = props.get("region", "")
        county = props.get("county", "")
        locality = props.get("locality", "")
        confidence = props.get("confidence", "")

        lon = coords[0] if len(coords) > 0 else ""
        lat = coords[1] if len(coords) > 1 else ""

        lines = [
            f"--- Result {i} ---",
            f"Name: {name}",
            f"Label: {label}",
            f"Coordinates: {lat}, {lon}",
        ]
        if locality:
            lines.append(f"Locality: {locality}")
        if county:
            lines.append(f"County: {county}")
        if region:
            lines.append(f"Region: {region}")
        if country:
            lines.append(f"Country: {country}")
        if confidence:
            lines.append(f"Confidence: {confidence}")

        parts.append("\n".join(lines))

    return "\n\n".join(parts)


def format_isochrones(data: dict) -> str:
    """Format isochrone response into a readable string."""
    features = data.get("features", [])
    if not features:
        return "No isochrone data found."

    parts = []
    for i, feature in enumerate(features, 1):
        props = feature.get("properties", {})
        center = props.get("center", [])
        value = props.get("value", 0)
        area = props.get("area", 0)
        group_index = props.get("group_index", "")

        lines = [
            f"--- Isochrone {i} ---",
            f"Range value: {value}",
        ]
        if center:
            lines.append(f"Center: {center[1]}, {center[0]}")
        if area:
            lines.append(f"Area: {area / 1_000_000:.2f} km²")
        if group_index is not None:
            lines.append(f"Group: {group_index}")

        coords = feature.get("geometry", {}).get("coordinates", [])
        if coords:
            outer = coords[0] if coords else []
            lines.append(f"Boundary points: {len(outer)}")

        parts.append("\n".join(lines))

    return "\n\n".join(parts)


def format_matrix(data: dict) -> str:
    """Format a matrix response into a readable string."""
    durations = data.get("durations", [])
    distances = data.get("distances", [])
    sources = data.get("sources", [])
    destinations = data.get("destinations", [])

    if not durations and not distances:
        return "No matrix data found."

    def _loc_label(loc: dict, idx: int) -> str:
        coords = loc.get("location", [])
        if coords:
            return f"Point {idx + 1} ({coords[1]:.4f}, {coords[0]:.4f})"
        return f"Point {idx + 1}"

    src_labels = [_loc_label(s, i) for i, s in enumerate(sources)]
    dst_labels = [_loc_label(d, i) for i, d in enumerate(destinations)]

    lines = [f"Matrix: {len(src_labels)} origins × {len(dst_labels)} destinations", ""]

    if durations:
        lines.append("Duration (minutes):")
        for i, row in enumerate(durations):
            for j, val in enumerate(row):
                if val is not None:
                    lines.append(
                        f"  {src_labels[i]} → {dst_labels[j]}: {val / 60:.1f} min"
                    )
                else:
                    lines.append(
                        f"  {src_labels[i]} → {dst_labels[j]}: unreachable"
                    )

    if distances:
        lines.append("\nDistance (km):")
        for i, row in enumerate(distances):
            for j, val in enumerate(row):
                if val is not None:
                    lines.append(
                        f"  {src_labels[i]} → {dst_labels[j]}: {val / 1000:.1f} km"
                    )
                else:
                    lines.append(
                        f"  {src_labels[i]} → {dst_labels[j]}: unreachable"
                    )

    return "\n".join(lines)
