"""Agent-Driven memory system — conversationalist design.

The agent IS the conversationalist: it processes each user turn in real time,
producing both a response and memory operations in a single LLM call.
No separate extraction step.

Key characteristic: memory management is woven into the conversation itself,
not bolted on as a post-hoc batch job.
"""

import json
import uuid
from openai import OpenAI
from .base import BaseMemorySystem, MemoryEntry, MemoryStats
from .embedder import Embedder

# ---------------------------------------------------------------------------
# Legacy prompt — still used by ablation variants (imported from ablations.py)
# ---------------------------------------------------------------------------
MEMORY_EXTRACTION_PROMPT = """You are a memory management system for a personal AI assistant. Your job is to analyze a conversation and decide what to STORE, UPDATE, or DELETE in the user's memory profile.

## Current Memories
{current_memories}

## New Conversation (Session {session_id})
{conversation}

## Instructions

Analyze this conversation and output a JSON object with three arrays:

1. "add": New facts/preferences to store (things not already in memory)
2. "update": Existing memories that need modification (with the memory ID and new content)
3. "delete": Memory IDs that are now outdated, wrong, or irrelevant

Guidelines:
- STORE: Important facts about the user (identity, preferences, goals, work, skills, relationships)
- STORE: User preferences for communication style and workflow
- UPDATE: When a fact changes (moved cities, got promoted, switched tools) — replace the old memory, don't add a duplicate
- DELETE: Temporary/time-bound information that's no longer relevant (e.g., "on-call this week" from weeks ago)
- SKIP: Idle chatter, weather complaints, food mentions, travel complaints — unless the user indicates these matter to them
- SKIP: Information that's only relevant to the current conversation and won't matter in future sessions

Be SELECTIVE. A good memory system stores 5-10 important things per session, not every detail.

Output ONLY valid JSON:
{{
    "add": [
        {{"content": "...", "importance": "high|medium|low"}}
    ],
    "update": [
        {{"id": "...", "old_content": "...", "new_content": "...", "reason": "..."}}
    ],
    "delete": [
        {{"id": "...", "reason": "..."}}
    ]
}}"""

# ---------------------------------------------------------------------------
# Conversationalist prompt — single LLM call produces response + memory ops
# ---------------------------------------------------------------------------

CONVERSATION_PROMPT = """You are a personal AI assistant with persistent memory. You remember things about the user across conversations so you can be helpful in future sessions.

## Memory Schema
Each memory has: [id] content (importance: high|medium|low)

## Your Current Memories (retrieved by relevance to this conversation)
{retrieved_memories}

## Conversation So Far (Session {session_id})
{conversation}

## Instructions

1. Respond to the user's latest message naturally and helpfully.
2. Decide what memory operations are needed. Your goal is to build a rich, accurate profile of the user over time.

### What to ADD
Store any fact that would help you be a better assistant in future conversations:
- Identity and role (name, job title, company, location)
- Projects and work details (what they're building, tools used, team size)
- Specific numbers and metrics (performance stats, costs, deadlines, milestones)
- Skills, learning progress, and achievements (what they've learned, results they got)
- Preferences for how they like to interact (brief vs detailed, lists vs prose, visual vs text, examples first vs theory first)
- Goals, plans, and upcoming events (deadlines, launches, interviews)
- Relationships and team context (manager, collaborators, team structure)

### What to UPDATE
When facts change, UPDATE the existing memory with the new state. Always reflect the current reality:
- Status changes: "planning to migrate" → "migrated 30 of 50 services"
- Events that happened: "interview next Tuesday" → "got the job, starting next month"
- Metric improvements: "model accuracy 85%" → "model accuracy 92% after fine-tuning"
- Role changes: "senior engineer" → "promoted to staff engineer"

### What to DELETE
- Facts that are completely superseded by an update
- Temporary information that has expired

### What to SKIP
- Idle chatter, weather, food, travel complaints — unless they indicate a lasting preference
- Technical content the user is asking about (store what they're working on, not the tutorial content itself)

### Examples

Example 1 — User shares project details with numbers:
Conversation: "We finally got our API response time down to 45ms. It was 200ms before we added the Redis cache. The team has grown to 8 engineers now."
Good memory_ops:
  add: "API response time improved from 200ms to 45ms after adding Redis cache" (high)
  add: "Team has grown to 8 engineers" (medium)

Example 2 — User reveals a preference through behavior:
Conversation: "Can you just give me the command? I don't need the explanation."
Good memory_ops:
  add: "User prefers direct answers and commands without lengthy explanations" (high)

Example 3 — A previous fact has changed:
Existing memory: [abc1] User is preparing for a demo on March 5th (high)
Conversation: "The demo went great! Client loved it and we signed the contract."
Good memory_ops:
  update: id=abc1, new_content="Demo on March 5th was successful — client signed the contract" (reason: "event has passed, recording outcome")

Example 4 — User mentions a milestone in a progression:
Existing memory: [def2] User's model achieves 78% accuracy on the validation set (high)
Conversation: "After switching to a larger embedding model, we're at 86% accuracy now."
Good memory_ops:
  update: id=def2, new_content="User's model accuracy improved from 78% to 86% after switching to a larger embedding model" (reason: "metric improved, preserving progression")

Output ONLY valid JSON (no markdown code blocks, no extra text):
{{
    "response": "Your natural response to the user...",
    "memory_ops": {{
        "add": [
            {{"content": "...", "importance": "high|medium|low"}}
        ],
        "update": [
            {{"id": "...", "new_content": "...", "reason": "..."}}
        ],
        "delete": [
            {{"id": "...", "reason": "..."}}
        ]
    }}
}}"""

CONSOLIDATION_PROMPT = """You are a memory consolidation system. Review these memories and merge/clean them up.

## Current Memories
{memories}

## Instructions
Consolidate these memories by:
1. Merging related/overlapping memories into single entries
2. Removing redundant information
3. Ensuring no contradictions exist (keep the most recent version)
4. Keeping the total count manageable (aim for fewer, richer entries)

Output ONLY valid JSON:
{{
    "keep": ["id1", "id2", ...],
    "merge": [
        {{"source_ids": ["id1", "id2"], "merged_content": "..."}}
    ],
    "delete": ["id3", "id4", ...]
}}"""


class AgentDrivenMemory(BaseMemorySystem):
    """Memory system where the LLM agent decides what to remember."""

    def __init__(
        self,
        user_id: str,
        openai_api_key: str = None,
        model: str = "gpt-4o-mini",
        consolidation_threshold: int = 20,
    ):
        super().__init__(user_id)
        self.client = OpenAI(api_key=openai_api_key)
        self.model = model
        self.consolidation_threshold = consolidation_threshold
        self.embedder = Embedder(api_key=openai_api_key)

        # Simple storage: {id: MemoryEntry} and {id: embedding_vector}
        self._memories: dict[str, MemoryEntry] = {}
        self._vectors: dict[str, list[float]] = {}

    def _call_llm(self, prompt: str) -> str:
        response = self.client.chat.completions.create(
            model=self.model,
            max_tokens=2000,
            messages=[{"role": "user", "content": prompt}],
        )
        self.stats.llm_calls += 1
        if response.usage:
            self.stats.total_input_tokens += response.usage.prompt_tokens
            self.stats.total_output_tokens += response.usage.completion_tokens
        return response.choices[0].message.content

    def _format_memories(self) -> str:
        if not self._memories:
            return "(No memories stored yet)"
        lines = []
        for mid, mem in self._memories.items():
            lines.append(f"[{mid}] {mem.content} (importance: {mem.metadata.get('importance', 'unknown')})")
        return "\n".join(lines)

    def _format_conversation(self, turns: list[dict]) -> str:
        lines = []
        for turn in turns:
            role = "User" if turn["role"] == "user" else "Assistant"
            lines.append(f"{role}: {turn['content']}")
        return "\n".join(lines)

    def _parse_json_response(self, raw_response: str) -> dict | None:
        """Extract and parse JSON from an LLM response."""
        try:
            json_str = raw_response
            if "```json" in json_str:
                json_str = json_str.split("```json")[1].split("```")[0]
            elif "```" in json_str:
                json_str = json_str.split("```")[1].split("```")[0]
            return json.loads(json_str.strip())
        except (json.JSONDecodeError, IndexError):
            return None

    def _retrieve_by_text(self, text: str, top_k: int = 5) -> dict[str, MemoryEntry]:
        """Embed a text string and retrieve the most relevant memories."""
        if not self._memories:
            return {}
        results = self.embedder.search(text, self._vectors, top_k=top_k)
        return {mid: self._memories[mid] for mid, _score in results if mid in self._memories}

    def _format_retrieved_memories(self, retrieved: dict[str, MemoryEntry]) -> str:
        """Format retrieved memories for the conversation prompt."""
        if not retrieved:
            return "(No memories stored yet)"
        lines = []
        for mid, mem in retrieved.items():
            lines.append(f"[{mid}] {mem.content} (importance: {mem.metadata.get('importance', 'unknown')})")
        return "\n".join(lines)

    def _process_memory_ops(self, ops: dict, session_id: int) -> list[MemoryEntry]:
        """Process add/update/delete memory operations from a single LLM call."""
        entries = []

        # Batch embed all new additions
        add_items = ops.get("add", [])
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
                        "source": "agent_driven",
                    },
                    created_at=session_id,
                    updated_at=session_id,
                )
                self._memories[mem_id] = entry
                self._vectors[mem_id] = vector
                entries.append(entry)
                self.stats.entries_added += 1

        # Process updates
        update_items = ops.get("update", [])
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

        # Process deletions
        for item in ops.get("delete", []):
            del_id = item if isinstance(item, str) else item.get("id", "")
            if del_id in self._memories:
                del self._memories[del_id]
                self._vectors.pop(del_id, None)
                self.stats.entries_deleted += 1

        return entries

    def add_conversation(self, turns: list[dict], session_id: int) -> list[MemoryEntry]:
        """Process a conversation turn-by-turn, like a real conversationalist.

        For each user turn:
        1. Embed the user message → retrieve relevant memories
        2. One LLM call: conversation so far + memories → response + memory_ops
        3. Process memory_ops immediately (so later turns benefit)
        """
        all_entries = []
        conversation_so_far = []

        for turn in turns:
            conversation_so_far.append(turn)

            # Only process on user turns (assistant turns are the agent's own responses)
            if turn["role"] != "user":
                continue

            # 1. Retrieve memories relevant to this user message
            retrieved = self._retrieve_by_text(turn["content"], top_k=5)

            # 2. Single LLM call: conversation + memories → response + memory_ops
            prompt = CONVERSATION_PROMPT.format(
                retrieved_memories=self._format_retrieved_memories(retrieved),
                session_id=session_id,
                conversation=self._format_conversation(conversation_so_far),
            )
            raw_response = self._call_llm(prompt)
            parsed = self._parse_json_response(raw_response)

            if parsed is None:
                print(f"Warning: Failed to parse response for {self.user_id} session {session_id}")
                print(f"Raw response: {raw_response[:500]}")
                continue

            # 3. Process memory operations immediately
            memory_ops = parsed.get("memory_ops", {})
            if not isinstance(memory_ops, dict):
                memory_ops = {}
            entries = self._process_memory_ops(memory_ops, session_id)
            all_entries.extend(entries)

        # Consolidate if needed (after all turns processed)
        if len(self._memories) > self.consolidation_threshold:
            self._consolidate()

        return all_entries

    def _consolidate(self):
        prompt = CONSOLIDATION_PROMPT.format(memories=self._format_memories())
        raw_response = self._call_llm(prompt)

        try:
            json_str = raw_response
            if "```json" in json_str:
                json_str = json_str.split("```json")[1].split("```")[0]
            elif "```" in json_str:
                json_str = json_str.split("```")[1].split("```")[0]
            decisions = json.loads(json_str.strip())
        except (json.JSONDecodeError, IndexError):
            return

        # Process merges
        merge_texts = []
        merge_sources = []
        for merge in decisions.get("merge", []):
            source_ids = merge.get("source_ids", [])
            merged_content = merge.get("merged_content", "")
            if source_ids and merged_content:
                merge_texts.append(merged_content)
                merge_sources.append((source_ids, merged_content))

        if merge_texts:
            merge_vectors = self.embedder.embed_batch(merge_texts)
            for (source_ids, merged_content), vector in zip(merge_sources, merge_vectors):
                for sid in source_ids:
                    self._memories.pop(sid, None)
                    self._vectors.pop(sid, None)

                new_id = str(uuid.uuid4())[:8]
                self._memories[new_id] = MemoryEntry(
                    id=new_id, content=merged_content,
                    metadata={"importance": "high", "source": "consolidation"},
                )
                self._vectors[new_id] = vector

        for del_id in decisions.get("delete", []):
            self._memories.pop(del_id, None)
            self._vectors.pop(del_id, None)

    def search(self, query: str, top_k: int = 5) -> list[MemoryEntry]:
        if not self._memories:
            return []
        results = self.embedder.search(query, self._vectors, top_k=top_k)
        return [self._memories[mid] for mid, _ in results if mid in self._memories]

    def get_all(self) -> list[MemoryEntry]:
        return list(self._memories.values())

    def reset(self):
        self._memories = {}
        self._vectors = {}
        self.stats = MemoryStats()
