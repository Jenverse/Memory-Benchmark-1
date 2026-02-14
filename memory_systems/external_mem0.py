"""External memory system using Mem0.

Mem0 is a third-party memory extraction service that automatically
identifies and stores relevant information from conversations.
The key characteristic: the SYSTEM decides what to remember, not the agent.

We configure Mem0 to use the same embedder (text-embedding-3-small)
and gpt-4o-mini for its internal extraction, keeping the comparison fair.
"""

import uuid
from .base import BaseMemorySystem, MemoryEntry, MemoryStats
from .embedder import Embedder


class Mem0Memory(BaseMemorySystem):
    """Memory system backed by Mem0's automatic extraction."""

    def __init__(self, user_id: str, use_local: bool = True, api_key: str = None,
                 openai_api_key: str = None):
        super().__init__(user_id)
        self.use_local = use_local

        if use_local:
            from mem0 import Memory
            # Same LLM and embedder as agent-driven — fair comparison
            config = {
                "llm": {
                    "provider": "openai",
                    "config": {
                        "model": "gpt-4o-mini",
                        "temperature": 0.1,
                    }
                },
                "embedder": {
                    "provider": "openai",
                    "config": {
                        "model": "text-embedding-3-small",
                    }
                },
            }
            self.memory = Memory.from_config(config)
        else:
            from mem0 import MemoryClient
            self.memory = MemoryClient(api_key=api_key)

        self._entry_cache = {}

    def add_conversation(self, turns: list[dict], session_id: int) -> list[MemoryEntry]:
        """Send conversation to Mem0 for automatic memory extraction.

        Mem0 decides what to extract — we have no control over this process.
        This is the core limitation we're studying.
        """
        messages = []
        for turn in turns:
            messages.append({
                "role": turn["role"],
                "content": turn["content"],
            })

        result = self.memory.add(
            messages=messages,
            user_id=self.user_id,
            metadata={"session_id": session_id},
        )

        self.stats.llm_calls += 1

        entries = []
        if isinstance(result, dict) and "results" in result:
            for r in result["results"]:
                entry = MemoryEntry(
                    id=r.get("id", str(uuid.uuid4())),
                    content=r.get("memory", r.get("text", "")),
                    metadata={"session_id": session_id, "source": "mem0", "event": r.get("event", "ADD")},
                    created_at=session_id,
                    updated_at=session_id,
                )
                entries.append(entry)
                self._entry_cache[entry.id] = entry
                if r.get("event") == "ADD":
                    self.stats.entries_added += 1
                elif r.get("event") == "UPDATE":
                    self.stats.entries_updated += 1
                elif r.get("event") == "DELETE":
                    self.stats.entries_deleted += 1

        return entries

    def search(self, query: str, top_k: int = 5) -> list[MemoryEntry]:
        """Search Mem0's stored memories."""
        results = self.memory.search(
            query=query,
            user_id=self.user_id,
            limit=top_k,
        )

        entries = []
        result_list = results if isinstance(results, list) else results.get("results", [])
        for r in result_list:
            entry = MemoryEntry(
                id=r.get("id", str(uuid.uuid4())),
                content=r.get("memory", r.get("text", "")),
                metadata=r.get("metadata", {}),
            )
            entries.append(entry)

        return entries

    def get_all(self) -> list[MemoryEntry]:
        """Get all memories stored by Mem0 for this user."""
        results = self.memory.get_all(user_id=self.user_id)

        entries = []
        result_list = results if isinstance(results, list) else results.get("results", [])
        for r in result_list:
            entry = MemoryEntry(
                id=r.get("id", str(uuid.uuid4())),
                content=r.get("memory", r.get("text", "")),
                metadata=r.get("metadata", {}),
            )
            entries.append(entry)

        return entries

    def reset(self):
        """Clear all Mem0 memories for this user."""
        self.memory.delete_all(user_id=self.user_id)
        self._entry_cache = {}
        self.stats = MemoryStats()
