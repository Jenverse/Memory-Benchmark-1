"""Experiment runner: feeds benchmark data through each memory system and evaluates."""

import json
import os
import time
from openai import OpenAI
from benchmark.data import PROFILES, get_all_tests
from memory_systems.base import BaseMemorySystem


ANSWER_EVALUATION_PROMPT = """You are evaluating whether a memory-assisted AI answer is correct.

## Test Question
{query}

## Ground Truth Answer
{correct_answer}

## Required Memories
{required_memories}

## What the System Retrieved from Memory
{retrieved_memories}

## System's Answer
{system_answer}

## Evaluation Criteria
1. Did the system retrieve the RIGHT memories? (not outdated/contradicted versions)
2. Is the answer factually correct based on ground truth?
3. Does it use the most up-to-date information?

Rate as:
- "correct": Answer is factually correct and uses current information
- "partially_correct": Has some right info but missing key details or includes stale info
- "incorrect": Wrong answer, uses outdated info, or completely missing

Also note specific failure modes:
- "stale_memory": Retrieved an outdated version of a fact that was updated
- "missing_memory": Failed to retrieve a needed memory
- "noise_retrieved": Retrieved irrelevant memories
- "hallucinated_memory": Answer includes information never in any conversation
- "contradiction_unresolved": Both old and new versions of a fact exist

Output ONLY valid JSON:
{{
    "rating": "correct|partially_correct|incorrect",
    "failure_modes": ["mode1", "mode2"],
    "explanation": "Brief explanation"
}}"""

ANSWER_GENERATION_PROMPT = """You are an AI assistant with access to stored memories about the user.

## Retrieved Memories
{memories}

## User's Question
{query}

Answer the user's question using ONLY the information from your retrieved memories. If you don't have relevant memories, say so honestly. Be concise."""


class ExperimentRunner:
    """Runs the full experiment: feeds conversations, tests memory, evaluates."""

    def __init__(self, openai_api_key: str = None, model: str = "gpt-4o-mini"):
        self.client = OpenAI(api_key=openai_api_key)
        self.model = model
        self.eval_llm_calls = 0
        self.eval_input_tokens = 0
        self.eval_output_tokens = 0

    def _call_llm(self, prompt: str) -> str:
        response = self.client.chat.completions.create(
            model=self.model,
            max_tokens=1000,
            messages=[{"role": "user", "content": prompt}],
        )
        self.eval_llm_calls += 1
        if response.usage:
            self.eval_input_tokens += response.usage.prompt_tokens
            self.eval_output_tokens += response.usage.completion_tokens
        return response.choices[0].message.content

    def run_single_profile(self, profile: dict, memory_system: BaseMemorySystem) -> dict:
        """Run one user profile through a memory system and evaluate.

        Steps:
        1. Feed sessions 1-4 into the memory system
        2. For each test question (in session 5), search memory and generate an answer
        3. Evaluate the answer against ground truth
        """
        user_id = profile["user_id"]
        results = {
            "user_id": user_id,
            "user_name": profile["name"],
            "memory_system": memory_system.__class__.__name__,
            "test_results": [],
            "all_memories_after": [],
            "memory_stats": None,
        }

        # Step 1: Feed sessions 1-4 into memory
        for session in profile["sessions"]:
            if session["session_id"] >= 5:  # Session 5 is test-only
                continue
            # Filter out [MEMORY TEST] placeholder responses
            real_turns = [t for t in session["turns"] if "[MEMORY TEST]" not in t.get("content", "")]
            if real_turns:
                memory_system.add_conversation(real_turns, session["session_id"])

        # Step 2: Get all stored memories (for analysis)
        all_memories = memory_system.get_all()
        results["all_memories_after"] = [
            {"id": m.id, "content": m.content, "metadata": m.metadata}
            for m in all_memories
        ]

        # Step 3: For each test, search memory and evaluate
        for test in profile["memory_tests"]:
            test_result = self._run_single_test(test, memory_system)
            results["test_results"].append(test_result)

        # Step 4: Capture stats
        stats = memory_system.get_stats()
        results["memory_stats"] = {
            "total_entries": stats.total_entries,
            "entries_added": stats.entries_added,
            "entries_updated": stats.entries_updated,
            "entries_deleted": stats.entries_deleted,
            "llm_calls": stats.llm_calls,
            "total_input_tokens": stats.total_input_tokens,
            "total_output_tokens": stats.total_output_tokens,
        }

        return results

    def _run_single_test(self, test: dict, memory_system: BaseMemorySystem) -> dict:
        """Run a single memory test: retrieve, generate answer, evaluate."""
        query = test["query"]

        # Retrieve memories
        retrieved = memory_system.search(query, top_k=5)
        retrieved_text = "\n".join([f"- {m.content}" for m in retrieved]) if retrieved else "(No memories found)"

        # Generate answer using retrieved memories
        answer_prompt = ANSWER_GENERATION_PROMPT.format(
            memories=retrieved_text,
            query=query,
        )
        system_answer = self._call_llm(answer_prompt)

        # Evaluate answer
        eval_prompt = ANSWER_EVALUATION_PROMPT.format(
            query=query,
            correct_answer=test["correct_answer"],
            required_memories="\n".join(f"- {m}" for m in test["required_memories"]),
            retrieved_memories=retrieved_text,
            system_answer=system_answer,
        )
        eval_response = self._call_llm(eval_prompt)

        # Parse evaluation
        try:
            json_str = eval_response
            if "```json" in json_str:
                json_str = json_str.split("```json")[1].split("```")[0]
            elif "```" in json_str:
                json_str = json_str.split("```")[1].split("```")[0]
            evaluation = json.loads(json_str.strip())
        except (json.JSONDecodeError, IndexError):
            evaluation = {
                "rating": "error",
                "failure_modes": ["parse_error"],
                "explanation": f"Failed to parse evaluation: {eval_response[:200]}",
            }

        return {
            "test_id": test["test_id"],
            "category": test["category"],
            "query": query,
            "required_memories": test["required_memories"],
            "retrieved_memories": [m.content for m in retrieved],
            "system_answer": system_answer,
            "correct_answer": test["correct_answer"],
            "evaluation": evaluation,
            "notes": test.get("notes", ""),
        }

    def run_full_experiment(
        self,
        memory_system_factory,
        system_name: str,
        profiles: list[dict] = None,
    ) -> dict:
        """Run the full experiment across all profiles.

        Args:
            memory_system_factory: Callable(user_id) -> BaseMemorySystem
            system_name: Name of the memory system for reporting
            profiles: List of profile dicts (defaults to all PROFILES)
        """
        if profiles is None:
            profiles = PROFILES

        experiment_results = {
            "system_name": system_name,
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
            "num_profiles": len(profiles),
            "profile_results": [],
            "eval_costs": {
                "llm_calls": 0,
                "input_tokens": 0,
                "output_tokens": 0,
            },
        }

        for i, profile in enumerate(profiles):
            print(f"  [{i+1}/{len(profiles)}] Running profile: {profile['name']} ({profile['user_id']})")

            # Create fresh memory system for each user
            memory_system = memory_system_factory(profile["user_id"])

            profile_result = self.run_single_profile(profile, memory_system)
            experiment_results["profile_results"].append(profile_result)

            # Print quick summary
            for tr in profile_result["test_results"]:
                rating = tr["evaluation"].get("rating", "unknown")
                symbol = {"correct": "+", "partially_correct": "~", "incorrect": "-"}.get(rating, "?")
                print(f"    [{symbol}] {tr['test_id']}: {rating} ({tr['category']})")

        # Record eval costs
        experiment_results["eval_costs"] = {
            "llm_calls": self.eval_llm_calls,
            "input_tokens": self.eval_input_tokens,
            "output_tokens": self.eval_output_tokens,
        }

        return experiment_results

    def save_results(self, results: dict, filepath: str):
        """Save experiment results to JSON."""
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        with open(filepath, "w") as f:
            json.dump(results, f, indent=2, default=str)
        print(f"Results saved to {filepath}")
