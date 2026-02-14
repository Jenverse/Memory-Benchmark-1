"""No-memory baseline system.

Stores nothing, retrieves nothing. Represents the lower bound where the
assistant has zero long-term memory between sessions. Every session starts
completely fresh with no knowledge of prior interactions.

Used as a control condition to measure the minimum value that any memory
system must exceed to be considered useful.
"""

from .base import BaseMemorySystem, MemoryEntry, MemoryStats


class NoMemoryBaseline(BaseMemorySystem):
    """Baseline that stores and retrieves nothing.

    This is the "no memory" lower bound. The assistant has no access to
    any information from previous sessions.
    """

    def __init__(self, user_id: str):
        super().__init__(user_id)

    def add_conversation(self, turns: list[dict], session_id: int) -> list[MemoryEntry]:
        """Does nothing. No memories are ever stored.

        Args:
            turns: Ignored.
            session_id: Ignored.

        Returns:
            Empty list (no entries created).
        """
        return []

    def search(self, query: str, top_k: int = 5) -> list[MemoryEntry]:
        """Returns nothing. There are no memories to search.

        Args:
            query: Ignored.
            top_k: Ignored.

        Returns:
            Empty list.
        """
        return []

    def get_all(self) -> list[MemoryEntry]:
        """Returns nothing. There are no memories stored.

        Returns:
            Empty list.
        """
        return []

    def reset(self):
        """Does nothing. There is no state to clear."""
        self.stats = MemoryStats()
