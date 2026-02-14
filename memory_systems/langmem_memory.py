"""External memory system using LangMem.

LangMem is LangChain's memory SDK that provides long-term memory for AI agents.
It supports three memory types:
- Semantic memory: Facts and knowledge (user preferences, facts about users)
- Episodic memory: Past experiences and actions
- Procedural memory: Instructions and rules

For this benchmark, we focus on semantic memory for storing facts from conversations.
"""

import uuid
import os
from .base import BaseMemorySystem, MemoryEntry, MemoryStats


class LangMemMemory(BaseMemorySystem):
    """Memory system backed by LangMem's semantic memory."""

    def __init__(self, user_id: str, openai_api_key: str = None):
        super().__init__(user_id)
        
        # Set OpenAI API key if provided
        if openai_api_key:
            os.environ["OPENAI_API_KEY"] = openai_api_key
        
        from langmem import create_memory_manager
        from langgraph.store.memory import InMemoryStore
        
        # Create memory manager for extracting facts
        self.manager = create_memory_manager(
            "openai:gpt-4o-mini",  # Same LLM as other systems for fair comparison
            instructions="Extract user preferences, facts, and important information from conversations",
            enable_inserts=True,
            enable_updates=True,
        )
        
        # Create in-memory store for storing memories
        # In production, this would be a DB-backed store
        self.store = InMemoryStore()
        
        # Namespace for this user's memories
        self.namespace = (user_id, "memories")
        
        # Cache for tracking entries
        self._entry_cache = {}

        # Cache for LangMem ExtractedMemory objects
        self._langmem_memories = []

    def add_conversation(self, turns: list[dict], session_id: int) -> list[MemoryEntry]:
        """Process conversation and extract memories using LangMem.

        LangMem's memory manager automatically extracts facts and updates
        existing memories when contradictions are found.
        """
        # Format conversation for LangMem
        messages = []
        for turn in turns:
            messages.append({
                "role": turn["role"],
                "content": turn["content"],
            })

        # Extract memories using LangMem manager
        # Pass existing memories from previous invocations
        invoke_params = {"messages": messages}
        if self._langmem_memories:
            invoke_params["existing"] = self._langmem_memories

        result = self.manager.invoke(invoke_params)

        self.stats.llm_calls += 1

        # Store the result for next invocation
        self._langmem_memories = result

        # Process extracted memories
        entries = []
        # Result is a list of ExtractedMemory objects
        memories_list = result if isinstance(result, list) else []

        for memory in memories_list:
            # Extract content from memory object
            if hasattr(memory, 'content'):
                if hasattr(memory.content, 'content'):
                    content = memory.content.content
                else:
                    content = str(memory.content)
            else:
                content = str(memory)

            # Generate or use existing ID
            memory_id = getattr(memory, 'id', str(uuid.uuid4()))

            # Create MemoryEntry
            entry = MemoryEntry(
                id=memory_id,
                content=content,
                metadata={"session_id": session_id, "source": "langmem"},
                created_at=session_id,
                updated_at=session_id,
            )

            # Store in LangMem store
            self.store.put(
                self.namespace,
                memory_id,
                {"text": content, "session_id": session_id}
            )

            # Track in cache
            if memory_id in self._entry_cache:
                self.stats.entries_updated += 1
            else:
                self.stats.entries_added += 1

            self._entry_cache[memory_id] = entry
            entries.append(entry)

        return entries

    def search(self, query: str, top_k: int = 5) -> list[MemoryEntry]:
        """Search memories using LangMem's semantic search."""
        # Use store.search() for semantic search
        results = self.store.search(
            self.namespace,
            query=query,
            limit=top_k
        )
        
        entries = []
        for item in results:
            # item is a StoreValue object with value and metadata
            memory_id = item.key
            content = item.value.get("text", "")
            session_id = item.value.get("session_id", 0)
            
            entry = MemoryEntry(
                id=memory_id,
                content=content,
                metadata={"session_id": session_id, "source": "langmem"},
            )
            entries.append(entry)
        
        return entries

    def get_all(self) -> list[MemoryEntry]:
        """Get all memories stored for this user."""
        return list(self._entry_cache.values())

    def reset(self):
        """Clear all memories for this user."""
        # Clear from store
        for memory_id in list(self._entry_cache.keys()):
            try:
                self.store.delete(self.namespace, memory_id)
            except:
                pass

        # Clear cache and stats
        self._entry_cache = {}
        self._langmem_memories = []
        self.stats = MemoryStats()

