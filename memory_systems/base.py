"""Base interface for all memory systems."""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class MemoryEntry:
    """A single memory entry."""
    id: str
    content: str
    metadata: dict = field(default_factory=dict)
    created_at: Optional[int] = None  # session number when created
    updated_at: Optional[int] = None  # session number when last updated


@dataclass
class MemoryStats:
    """Statistics about memory operations for cost/efficiency analysis."""
    total_entries: int = 0
    entries_added: int = 0
    entries_updated: int = 0
    entries_deleted: int = 0
    llm_calls: int = 0
    total_input_tokens: int = 0
    total_output_tokens: int = 0


class BaseMemorySystem(ABC):
    """Abstract base class for memory systems."""

    def __init__(self, user_id: str):
        self.user_id = user_id
        self.stats = MemoryStats()

    @abstractmethod
    def add_conversation(self, turns: list[dict], session_id: int) -> list[MemoryEntry]:
        """Process a conversation and store relevant memories.

        Args:
            turns: List of {"role": ..., "content": ...} conversation turns.
            session_id: The session number this conversation belongs to.

        Returns:
            List of MemoryEntry objects that were added/updated.
        """
        pass

    @abstractmethod
    def search(self, query: str, top_k: int = 5) -> list[MemoryEntry]:
        """Search memories by semantic relevance.

        Args:
            query: The search query.
            top_k: Maximum number of results.

        Returns:
            List of relevant MemoryEntry objects.
        """
        pass

    @abstractmethod
    def get_all(self) -> list[MemoryEntry]:
        """Return all stored memories for this user."""
        pass

    @abstractmethod
    def reset(self):
        """Clear all memories for this user."""
        pass

    def get_stats(self) -> MemoryStats:
        """Return current statistics."""
        self.stats.total_entries = len(self.get_all())
        return self.stats
