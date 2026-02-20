"""
Bedrock AgentCore Memory client.

Wraps the bedrock_agentcore.memory SDK for long-term memory operations:
- Create memory sessions
- Add conversational turns (store preferences)
- Search long-term memories
- List / delete memory records

The SDK is boto3-based (synchronous), so all calls are wrapped in
asyncio.to_thread() to avoid blocking the ASGI event loop.
"""

import asyncio
import uuid

from loguru import logger

from bedrock_agentcore.memory.session import MemorySessionManager
from bedrock_agentcore.memory.constants import ConversationalMessage, MessageRole


class AgentCoreMemoryClient:
    """Async client for Bedrock AgentCore Long-Term Memory."""

    def __init__(self, memory_id: str, region_name: str) -> None:
        if not memory_id:
            raise ValueError("AGENTCORE_MEMORY_ID is not set.")
        self._memory_id = memory_id
        self._region_name = region_name
        self._manager = MemorySessionManager(
            memory_id=memory_id,
            region_name=region_name,
        )

    async def store_preference(
        self,
        actor_id: str,
        preference_text: str,
    ) -> dict:
        """Store a user preference by adding conversational turns."""
        session_id = f"pref-{uuid.uuid4().hex[:12]}"
        logger.debug(f"Storing preference: actor={actor_id}, session={session_id}")

        def _store():
            session = self._manager.create_memory_session(
                actor_id=actor_id,
                session_id=session_id,
            )
            session.add_turns([
                ConversationalMessage(preference_text, MessageRole.USER),
                ConversationalMessage(
                    f"Preference noted: {preference_text}",
                    MessageRole.ASSISTANT,
                ),
            ])
            return {"actor_id": actor_id, "session_id": session_id, "status": "stored"}

        return await asyncio.to_thread(_store)

    async def search_preferences(
        self,
        actor_id: str,
        query: str,
        top_k: int = 5,
    ) -> list:
        """Semantic search over a user's long-term memory records."""
        namespace = f"/preferences/{actor_id}/"
        logger.debug(f"Searching preferences: actor={actor_id}, query={query!r}")

        def _search():
            session = self._manager.create_memory_session(
                actor_id=actor_id,
                session_id=f"search-{uuid.uuid4().hex[:8]}",
            )
            return session.search_long_term_memories(
                query=query,
                namespace_prefix=namespace,
                top_k=top_k,
            )

        return await asyncio.to_thread(_search)

    async def list_preferences(self, actor_id: str) -> list:
        """List all long-term memory records for a user."""
        namespace = f"/preferences/{actor_id}/"
        logger.debug(f"Listing preferences: actor={actor_id}")

        def _list():
            session = self._manager.create_memory_session(
                actor_id=actor_id,
                session_id=f"list-{uuid.uuid4().hex[:8]}",
            )
            return session.list_long_term_memory_records(
                namespace_prefix=namespace,
            )

        return await asyncio.to_thread(_list)

    async def delete_preference(self, actor_id: str, record_id: str) -> dict:
        """Delete a specific long-term memory record."""
        logger.debug(f"Deleting preference: actor={actor_id}, record={record_id}")

        def _delete():
            session = self._manager.create_memory_session(
                actor_id=actor_id,
                session_id=f"delete-{uuid.uuid4().hex[:8]}",
            )
            session.delete_memory_record(record_id=record_id)
            return {"actor_id": actor_id, "record_id": record_id, "status": "deleted"}

        return await asyncio.to_thread(_delete)

    async def close(self) -> None:
        """No persistent connection to close."""
        pass
