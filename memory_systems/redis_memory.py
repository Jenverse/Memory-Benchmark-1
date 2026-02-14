"""Redis Agent Memory Server - external memory system wrapper.

Uses the Redis Agent Memory Server (https://github.com/redis/agent-memory-server)
as a second external memory provider. The server runs as a Docker container and
provides LLM-based memory extraction, embedding, and vector search via Redis.

Key characteristic: Like Mem0, this is an EXTERNAL system — the agent has no
control over what gets extracted. The server's own LLM pipeline decides.
"""

import asyncio
import uuid
import time
from datetime import datetime, timezone

from .base import BaseMemorySystem, MemoryEntry, MemoryStats

# Lazy imports to avoid requiring the SDK when not in use
_client = None


def _get_or_create_client():
    """Lazy singleton client."""
    global _client
    if _client is None:
        from agent_memory_client import MemoryAPIClient
        from agent_memory_client.client import MemoryClientConfig
        config = MemoryClientConfig(base_url="http://localhost:8000")
        _client = MemoryAPIClient(config)
    return _client


def _run_async(coro):
    """Run an async coroutine synchronously."""
    try:
        loop = asyncio.get_event_loop()
        if loop.is_running():
            import concurrent.futures
            with concurrent.futures.ThreadPoolExecutor() as pool:
                future = pool.submit(asyncio.run, coro)
                return future.result()
        else:
            return loop.run_until_complete(coro)
    except RuntimeError:
        return asyncio.run(coro)


class RedisAgentMemory(BaseMemorySystem):
    """Memory system using Redis Agent Memory Server."""

    def __init__(self, user_id: str, namespace: str = "memorybench"):
        super().__init__(user_id)
        self.namespace = namespace
        self.client = _get_or_create_client()
        self._session_counter = 0

    def add_conversation(self, turns: list[dict], session_id: int) -> list[MemoryEntry]:
        """Send conversation to Redis Agent Memory Server for extraction."""
        from agent_memory_client.models import WorkingMemory, MemoryMessage

        self._session_counter += 1
        sess_id = f"{self.user_id}_session_{session_id}"

        # Build messages with timestamps
        messages = []
        for turn in turns:
            messages.append(MemoryMessage(
                role=turn["role"],
                content=turn["content"],
                created_at=datetime.now(timezone.utc),
            ))

        # Put working memory
        wm = WorkingMemory(
            messages=messages,
            session_id=sess_id,
            user_id=self.user_id,
            namespace=self.namespace,
        )

        async def _add():
            await self.client.put_working_memory(
                session_id=sess_id,
                memory=wm,
                user_id=self.user_id,
            )
            # Promote to long-term memory (triggers LLM extraction)
            await self.client.promote_working_memories_to_long_term(
                session_id=sess_id,
            )

        _run_async(_add())
        self.stats.llm_calls += 1  # The server makes its own LLM calls internally

        # Wait briefly for extraction to complete
        time.sleep(2)

        # Return whatever was extracted
        entries = []
        all_mems = self._search_all()
        for m in all_mems:
            entries.append(m)
        self.stats.entries_added = len(all_mems)
        return entries

    def _search_all(self) -> list[MemoryEntry]:
        """Get all memories for this user."""
        async def _search():
            results = await self.client.search_long_term_memory(
                text="*",
                user_id={"eq": self.user_id},
                namespace={"eq": self.namespace},
                limit=100,
            )
            return results.memories

        raw = _run_async(_search())
        entries = []
        for m in raw:
            entries.append(MemoryEntry(
                id=str(m.id) if hasattr(m, 'id') else str(uuid.uuid4())[:8],
                content=m.text,
                metadata={
                    "source": "redis_agent_memory",
                    "topics": getattr(m, 'topics', None) or [],
                    "entities": getattr(m, 'entities', None) or [],
                    "memory_type": str(getattr(m, 'memory_type', 'unknown')),
                },
            ))
        return entries

    def search(self, query: str, top_k: int = 5) -> list[MemoryEntry]:
        """Search memories by semantic relevance."""
        async def _search():
            results = await self.client.search_long_term_memory(
                text=query,
                user_id={"eq": self.user_id},
                namespace={"eq": self.namespace},
                limit=top_k,
            )
            return results.memories

        raw = _run_async(_search())
        entries = []
        for m in raw:
            entries.append(MemoryEntry(
                id=str(m.id) if hasattr(m, 'id') else str(uuid.uuid4())[:8],
                content=m.text,
                metadata={
                    "source": "redis_agent_memory",
                    "topics": getattr(m, 'topics', None) or [],
                    "entities": getattr(m, 'entities', None) or [],
                },
            ))
        return entries

    def get_all(self) -> list[MemoryEntry]:
        """Return all stored memories for this user."""
        return self._search_all()

    def reset(self):
        """Clear all memories for this user."""
        async def _reset():
            try:
                # Get all memory IDs for this user
                results = await self.client.search_long_term_memory(
                    text="*",
                    user_id={"eq": self.user_id},
                    namespace={"eq": self.namespace},
                    limit=500,
                )
                if results.memories:
                    ids = [str(m.id) for m in results.memories if hasattr(m, 'id')]
                    if ids:
                        await self.client.delete_long_term_memories(memory_ids=ids)
            except Exception:
                pass  # May not have any memories yet
            # Also delete working memory sessions
            try:
                sessions = await self.client.list_sessions(
                    user_id=self.user_id,
                    namespace=self.namespace,
                )
                if hasattr(sessions, 'sessions'):
                    for s in sessions.sessions:
                        await self.client.delete_working_memory(session_id=s.session_id)
            except Exception:
                pass

        _run_async(_reset())
        self.stats = MemoryStats()
