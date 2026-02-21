"""Formatting helpers for AgentCore Memory responses."""

from src.schemas.preferences import (
    PreferenceListResponse,
    PreferenceRecord,
    StorePreferenceResponse,
)


def format_memory_record(record: dict) -> PreferenceRecord:
    """Format a single memory record into a PreferenceRecord model."""
    return PreferenceRecord(
        record_id=record.get("id", record.get("recordId")),
        content=record.get("content", record.get("memory")),
        namespace=record.get("namespace"),
        created_at=record.get("createdAt", record.get("created_at")),
        relevance_score=record.get("score"),
    )


def format_memory_records(records: list) -> PreferenceListResponse:
    """Format a list of memory records into a PreferenceListResponse model."""
    formatted = []
    for record in records:
        rec = record if isinstance(record, dict) else {"content": str(record)}
        formatted.append(format_memory_record(rec))

    return PreferenceListResponse(
        count=len(formatted),
        preferences=formatted,
    )


def format_store_result(result: dict) -> StorePreferenceResponse:
    """Format the result of storing a preference."""
    return StorePreferenceResponse(
        status=result.get("status", "stored"),
        actor_id=result.get("actor_id"),
        session_id=result.get("session_id"),
    )
