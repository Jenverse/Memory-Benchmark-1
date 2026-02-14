"""Zep Memory - external memory system wrapper.

Uses Zep (https://www.getzep.com/) as an external memory provider.
Zep provides LLM-based memory extraction, knowledge graph, and semantic search.

Key characteristic: Like Mem0 and Redis, this is an EXTERNAL system — the agent has no
control over what gets extracted. Zep's own pipeline decides what facts to extract.
"""

import uuid
import time
import os
import re
from datetime import datetime, timezone

from .base import BaseMemorySystem, MemoryEntry, MemoryStats

# Lazy imports to avoid requiring the SDK when not in use
_client = None


def _get_or_create_client():
    """Lazy initialization of Zep client."""
    global _client
    if _client is None:
        from zep_cloud.client import Zep
        api_key = os.getenv("ZEP_API_KEY")
        if not api_key:
            raise ValueError("ZEP_API_KEY environment variable not set")
        _client = Zep(api_key=api_key)
    return _client


class ZepMemory(BaseMemorySystem):
    """Memory system using Zep.

    Note: Users must be created in Zep before using this memory system.
    Run setup_zep_users.py first to create all users.
    """

    def __init__(self, user_id: str):
        super().__init__(user_id)
        self.client = _get_or_create_client()
        self._session_counter = 0

    def add_conversation(self, turns: list[dict], session_id: int) -> list[MemoryEntry]:
        """Send conversation to Zep for extraction."""
        from zep_cloud.types import Message

        self._session_counter += 1
        thread_id = f"{self.user_id}_session_{session_id}"

        # Build messages with timestamps
        messages = []
        for turn in turns:
            messages.append(Message(
                created_at=datetime.now(timezone.utc).isoformat(),
                role=turn["role"],
                content=turn["content"],
            ))

        # Try to get the thread first, create if it doesn't exist
        try:
            self.client.thread.get(thread_id=thread_id)
        except Exception:
            # Thread doesn't exist, create it
            try:
                self.client.thread.create(
                    thread_id=thread_id,
                    user_id=self.user_id,
                )
            except Exception as e:
                # If creation fails, it might already exist from another process
                print(f"Warning: Could not create thread {thread_id}: {e}")

        # Add messages to the thread
        self.client.thread.add_messages(
            thread_id=thread_id,
            messages=messages,
        )

        self.stats.llm_calls += 1  # Zep makes its own LLM calls internally

        # Wait briefly for extraction to complete
        time.sleep(2)

        # Return whatever was extracted from this thread
        entries = self._get_thread_context(thread_id)
        self.stats.entries_added = len(entries)
        return entries

    def _get_thread_context(self, thread_id: str) -> list[MemoryEntry]:
        """Get user context from a specific thread."""
        try:
            user_context = self.client.thread.get_user_context(thread_id=thread_id)
            context_text = user_context.context if hasattr(user_context, 'context') else str(user_context)

            # Parse the context block to extract facts
            entries = self._parse_context_block(context_text)
            return entries
        except Exception as e:
            print(f"Warning: Could not get context for thread {thread_id}: {e}")
            return []

    def _parse_context_block(self, context_text: str) -> list[MemoryEntry]:
        """Parse Zep's context block format to extract facts."""
        entries = []

        # Extract facts from the <FACTS> section
        facts_match = re.search(r'<FACTS>(.*?)</FACTS>', context_text, re.DOTALL)
        if facts_match:
            facts_section = facts_match.group(1)
            # Each fact is on a line starting with "  - "
            fact_lines = re.findall(r'  - (.+?)(?:\(.*?\))?$', facts_section, re.MULTILINE)

            for fact in fact_lines:
                fact = fact.strip()
                if fact:
                    entries.append(MemoryEntry(
                        id=str(uuid.uuid4())[:8],
                        content=fact,
                        metadata={"source": "zep"},
                    ))

        return entries

    def _search_all(self) -> list[MemoryEntry]:
        """Get all memories for this user across all threads."""
        # Since we don't have a single "get all facts" API, we'll need to
        # aggregate from all threads for this user
        # For now, return empty - this is mainly used for debugging
        return []

    def search(self, query: str, top_k: int = 5) -> list[MemoryEntry]:
        """Search memories by semantic relevance using graph search."""
        try:
            results = self.client.graph.search(
                user_id=self.user_id,
                query=query,
                limit=top_k,
            )

            entries = []
            if hasattr(results, 'edges') and results.edges:
                for edge in results.edges:
                    # Extract fact information
                    fact = getattr(edge, 'fact', '')
                    if fact:
                        entries.append(MemoryEntry(
                            id=str(uuid.uuid4())[:8],
                            content=fact,
                            metadata={"source": "zep"},
                        ))

            return entries
        except Exception as e:
            print(f"Warning: Graph search failed: {e}")
            return []

    def get_all(self) -> list[MemoryEntry]:
        """Return all stored memories for this user."""
        return self._search_all()

    def reset(self):
        """Clear all memories for this user."""
        # Zep doesn't have a direct "delete all" for a user's graph
        # We would need to delete individual facts or the user
        # For now, we'll just reset our stats
        self.stats = MemoryStats()

