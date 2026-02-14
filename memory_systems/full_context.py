"""Full-context baseline memory system.

Stores every conversation transcript verbatim with no extraction, summarization,
or embedding. Retrieval returns all stored transcripts (up to top_k) without
any semantic ranking. This represents the naive "stuff everything into the
context window" upper bound baseline.

No LLM calls are made. No embeddings are computed. This is purely raw storage
and retrieval of complete conversation histories.
"""

import uuid
from .base import BaseMemorySystem, MemoryEntry, MemoryStats


class FullContextBaseline(BaseMemorySystem):
    """Baseline that stores full conversation transcripts verbatim.

    Every session's conversation is stored as a single MemoryEntry containing
    the complete transcript. Search returns all stored transcripts (no semantic
    filtering). This represents the upper bound on information retention at the
    cost of context window space — the assistant sees everything, unprocessed.
    """

    def __init__(self, user_id: str):
        super().__init__(user_id)
        self._memories: dict[str, MemoryEntry] = {}

    def _format_conversation(self, turns: list[dict]) -> str:
        """Format conversation turns into a single text transcript.

        Args:
            turns: List of {"role": ..., "content": ...} conversation turns.

        Returns:
            A plaintext transcript with "User:" / "Assistant:" prefixes.
        """
        lines = []
        for turn in turns:
            role = "User" if turn["role"] == "user" else "Assistant"
            lines.append(f"{role}: {turn['content']}")
        return "\n".join(lines)

    def add_conversation(self, turns: list[dict], session_id: int) -> list[MemoryEntry]:
        """Store the full conversation transcript as a single memory entry.

        No extraction, summarization, or embedding is performed. The entire
        conversation is stored verbatim as one entry.

        Args:
            turns: List of {"role": ..., "content": ...} conversation turns.
            session_id: The session number this conversation belongs to.

        Returns:
            A single-element list containing the stored MemoryEntry.
        """
        if not turns:
            return []

        transcript = self._format_conversation(turns)
        mem_id = str(uuid.uuid4())[:8]

        entry = MemoryEntry(
            id=mem_id,
            content=transcript,
            metadata={
                "session_id": session_id,
                "source": "full_context",
                "num_turns": len(turns),
            },
            created_at=session_id,
            updated_at=session_id,
        )

        self._memories[mem_id] = entry
        self.stats.entries_added += 1
        return [entry]

    def search(self, query: str, top_k: int = 5) -> list[MemoryEntry]:
        """Return all stored transcripts, up to top_k.

        No semantic search is performed. Results are returned in insertion
        order (earliest sessions first), capped at top_k.

        Args:
            query: Ignored (no semantic search).
            top_k: Maximum number of transcripts to return.

        Returns:
            List of MemoryEntry objects (up to top_k).
        """
        all_entries = list(self._memories.values())
        return all_entries[:top_k]

    def get_all(self) -> list[MemoryEntry]:
        """Return all stored conversation transcripts.

        Returns:
            List of all MemoryEntry objects.
        """
        return list(self._memories.values())

    def reset(self):
        """Clear all stored transcripts."""
        self._memories = {}
        self.stats = MemoryStats()
