"""Ablation variants of the Agent-Driven memory system.

These isolate which components of agent-driven memory matter most:
  1. AgentNoFeedback  — extraction prompt has no visibility into current memories
  2. AgentNoConsolidation — consolidation never triggers
  3. AgentAddOnly — only "add" decisions are honored; no update, delete, or consolidation

Each is a minimal subclass that overrides only what is necessary.
"""

import json
import math
import uuid

from .agent_driven import AgentDrivenMemory, MEMORY_EXTRACTION_PROMPT
from .base import MemoryEntry


# ---------------------------------------------------------------------------
# 1. AgentNoFeedback – agent extracts memories WITHOUT seeing existing ones
# ---------------------------------------------------------------------------

class AgentNoFeedback(AgentDrivenMemory):
    """Ablation: the extraction prompt does NOT include current memories.

    The LLM still outputs add/update/delete decisions and we honour them,
    but the prompt replaces the {current_memories} section with a placeholder
    so the model cannot condition on what is already stored.

    This tests: **does seeing existing memories during extraction matter?**
    """

    def add_conversation(self, turns: list[dict], session_id: int) -> list[MemoryEntry]:
        # Build the same prompt but blind the model to existing memories.
        prompt = MEMORY_EXTRACTION_PROMPT.format(
            current_memories="(Memory context not available)",
            session_id=session_id,
            conversation=self._format_conversation(turns),
        )

        raw_response = self._call_llm(prompt)

        try:
            json_str = raw_response
            if "```json" in json_str:
                json_str = json_str.split("```json")[1].split("```")[0]
            elif "```" in json_str:
                json_str = json_str.split("```")[1].split("```")[0]
            decisions = json.loads(json_str.strip())
        except (json.JSONDecodeError, IndexError):
            return []

        entries = []

        # --- adds (identical to parent) ---
        add_items = decisions.get("add", [])
        if add_items:
            add_texts = [item["content"] for item in add_items]
            add_vectors = self.embedder.embed_batch(add_texts)

            for item, vector in zip(add_items, add_vectors):
                mem_id = str(uuid.uuid4())[:8]
                entry = MemoryEntry(
                    id=mem_id,
                    content=item["content"],
                    metadata={
                        "importance": item.get("importance", "medium"),
                        "session_id": session_id,
                        "source": "agent_no_feedback",
                    },
                    created_at=session_id,
                    updated_at=session_id,
                )
                self._memories[mem_id] = entry
                self._vectors[mem_id] = vector
                entries.append(entry)
                self.stats.entries_added += 1

        # --- updates (still honoured, though unlikely to hit valid IDs) ---
        update_items = decisions.get("update", [])
        update_texts = []
        update_ids = []
        for item in update_items:
            old_id = item.get("id", "")
            if old_id in self._memories:
                update_texts.append(item["new_content"])
                update_ids.append((old_id, item))

        if update_texts:
            update_vectors = self.embedder.embed_batch(update_texts)
            for (old_id, item), vector in zip(update_ids, update_vectors):
                self._memories[old_id].content = item["new_content"]
                self._memories[old_id].updated_at = session_id
                self._memories[old_id].metadata["last_update_reason"] = item.get("reason", "")
                self._vectors[old_id] = vector
                entries.append(self._memories[old_id])
                self.stats.entries_updated += 1

        # --- deletes (still honoured, though unlikely to hit valid IDs) ---
        for item in decisions.get("delete", []):
            del_id = item if isinstance(item, str) else item.get("id", "")
            if del_id in self._memories:
                del self._memories[del_id]
                self._vectors.pop(del_id, None)
                self.stats.entries_deleted += 1

        # Consolidation still runs (only the feedback loop is ablated).
        if len(self._memories) > self.consolidation_threshold:
            self._consolidate()

        return entries


# ---------------------------------------------------------------------------
# 2. AgentNoConsolidation – consolidation never fires
# ---------------------------------------------------------------------------

class AgentNoConsolidation(AgentDrivenMemory):
    """Ablation: consolidation is disabled; memories accumulate without merging.

    Everything else is identical to the full agent-driven system: the LLM
    still sees current memories, and add/update/delete decisions are all
    honoured.

    This tests: **does periodic consolidation matter?**
    """

    def __init__(self, user_id: str, openai_api_key: str = None,
                 model: str = "gpt-4o-mini", **kwargs):
        # Set consolidation_threshold to infinity so the check in
        # add_conversation (len > threshold) is never True.
        super().__init__(
            user_id=user_id,
            openai_api_key=openai_api_key,
            model=model,
            consolidation_threshold=math.inf,
        )


# ---------------------------------------------------------------------------
# 3. AgentAddOnly – no update, no delete, no consolidation
# ---------------------------------------------------------------------------

class AgentAddOnly(AgentDrivenMemory):
    """Ablation: only 'add' decisions are processed; update/delete/consolidation are all disabled.

    The LLM still sees current memories (feedback loop is intact) and still
    produces update/delete suggestions, but they are silently ignored.  The
    memory store is append-only.

    This tests: **does the ability to modify existing memories matter?**
    """

    def add_conversation(self, turns: list[dict], session_id: int) -> list[MemoryEntry]:
        prompt = MEMORY_EXTRACTION_PROMPT.format(
            current_memories=self._format_memories(),
            session_id=session_id,
            conversation=self._format_conversation(turns),
        )

        raw_response = self._call_llm(prompt)

        try:
            json_str = raw_response
            if "```json" in json_str:
                json_str = json_str.split("```json")[1].split("```")[0]
            elif "```" in json_str:
                json_str = json_str.split("```")[1].split("```")[0]
            decisions = json.loads(json_str.strip())
        except (json.JSONDecodeError, IndexError):
            return []

        entries = []

        # --- adds only ---
        add_items = decisions.get("add", [])
        if add_items:
            add_texts = [item["content"] for item in add_items]
            add_vectors = self.embedder.embed_batch(add_texts)

            for item, vector in zip(add_items, add_vectors):
                mem_id = str(uuid.uuid4())[:8]
                entry = MemoryEntry(
                    id=mem_id,
                    content=item["content"],
                    metadata={
                        "importance": item.get("importance", "medium"),
                        "session_id": session_id,
                        "source": "agent_add_only",
                    },
                    created_at=session_id,
                    updated_at=session_id,
                )
                self._memories[mem_id] = entry
                self._vectors[mem_id] = vector
                entries.append(entry)
                self.stats.entries_added += 1

        # update decisions — intentionally ignored
        # delete decisions — intentionally ignored
        # consolidation  — intentionally skipped

        return entries
