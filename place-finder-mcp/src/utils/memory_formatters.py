"""Formatting helpers for AgentCore Memory responses."""


def format_memory_record(record: dict) -> str:
    """Format a single memory record into a readable string."""
    record_id = record.get("id", record.get("recordId", "N/A"))
    content = record.get("content", record.get("memory", "N/A"))
    namespace = record.get("namespace", "N/A")
    created_at = record.get("createdAt", record.get("created_at", "N/A"))
    score = record.get("score", None)

    lines = [
        f"Record ID: {record_id}",
        f"Content: {content}",
        f"Namespace: {namespace}",
        f"Created: {created_at}",
    ]
    if score is not None:
        lines.append(f"Relevance Score: {score}")

    return "\n".join(lines)


def format_memory_records(records: list) -> str:
    """Format a list of memory records into a numbered result string."""
    if not records:
        return "No preferences found."
    parts = []
    for i, record in enumerate(records, 1):
        rec = record if isinstance(record, dict) else {"content": str(record)}
        parts.append(f"--- Preference {i} ---\n{format_memory_record(rec)}")
    return "\n\n".join(parts)


def format_store_result(result: dict) -> str:
    """Format the result of storing a preference."""
    actor_id = result.get("actor_id", "N/A")
    session_id = result.get("session_id", "N/A")
    status = result.get("status", "N/A")
    return (
        f"Preference stored successfully.\n"
        f"Actor: {actor_id}\n"
        f"Session: {session_id}\n"
        f"Status: {status}"
    )


def format_delete_result(result: dict) -> str:
    """Format the result of deleting a preference."""
    actor_id = result.get("actor_id", "N/A")
    record_id = result.get("record_id", "N/A")
    status = result.get("status", "N/A")
    return (
        f"Preference deleted.\n"
        f"Actor: {actor_id}\n"
        f"Record ID: {record_id}\n"
        f"Status: {status}"
    )
