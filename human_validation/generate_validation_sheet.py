#!/usr/bin/env python3
"""
Generate a human validation spreadsheet for LLM judge agreement analysis.

Samples ~30 test results stratified across systems and categories,
outputs a CSV for human annotation and a script to compute agreement.
"""

import json
import csv
import random
import os

random.seed(42)

# Result files (one per system)
RESULT_FILES = {
    "Agent-Driven": "results_v5_improved/agent_trial1_results_20260213_113821.json",
    "Mem0": "results_v5/mem0_trial1_results_20260213_105458.json",
    "LangMem": "results_v5/langmem_trial1_results_20260213_105500.json",
}

CATEGORIES = [
    "contradiction_update", "temporal_relevance", "noise_resistance",
    "implicit_preference", "simple_recall", "consolidation", "cross_session"
]


def load_results(filepath):
    with open(filepath) as f:
        data = json.load(f)
    results = []
    for profile in data["profile_results"]:
        for test in profile["test_results"]:
            test["user_id"] = profile["user_id"]
            results.append(test)
    return results


def sample_stratified(all_results, n=30):
    """Sample n results stratified by system and category."""
    # Group by (system, category)
    groups = {}
    for system, results in all_results.items():
        for r in results:
            key = (system, r["category"])
            groups.setdefault(key, []).append(r)

    # Calculate how many to sample from each group
    # Target: ~10 per system, spread across categories
    sampled = []
    per_system = n // len(all_results)  # 10 per system

    for system in all_results:
        system_items = []
        for cat in CATEGORIES:
            key = (system, cat)
            if key in groups and groups[key]:
                system_items.extend([(r, system) for r in groups[key]])

        random.shuffle(system_items)
        sampled.extend(system_items[:per_system])

    # If we need more to reach n, sample from remaining
    already = {(s, r["test_id"]) for r, s in sampled}
    remaining = []
    for system, results in all_results.items():
        for r in results:
            if (system, r["test_id"]) not in already:
                remaining.append((r, system))
    random.shuffle(remaining)
    sampled.extend(remaining[:n - len(sampled)])

    return sampled


def main():
    os.makedirs("human_validation", exist_ok=True)

    # Load all results
    all_results = {}
    for system, filepath in RESULT_FILES.items():
        all_results[system] = load_results(filepath)
        print(f"Loaded {len(all_results[system])} results for {system}")

    # Sample
    sampled = sample_stratified(all_results, n=30)
    random.shuffle(sampled)  # Randomize order so rater doesn't see system patterns

    # Write annotation CSV (what the human sees)
    annotation_path = "human_validation/annotation_sheet.csv"
    with open(annotation_path, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow([
            "id", "query", "ground_truth_answer", "system_answer",
            "your_rating (correct/partially_correct/incorrect)",
            "your_notes"
        ])
        for i, (result, system) in enumerate(sampled, 1):
            writer.writerow([
                i,
                result["query"],
                result["correct_answer"],
                result["system_answer"],
                "",  # Human fills this in
                ""   # Human notes
            ])

    # Write answer key (hidden from rater until after annotation)
    key_path = "human_validation/answer_key.csv"
    with open(key_path, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow([
            "id", "test_id", "system", "category",
            "llm_judge_rating", "llm_judge_explanation"
        ])
        for i, (result, system) in enumerate(sampled, 1):
            writer.writerow([
                i,
                result["test_id"],
                system,
                result["category"],
                result["evaluation"]["rating"],
                result["evaluation"]["explanation"]
            ])

    print(f"\nGenerated:")
    print(f"  {annotation_path} — give this to your human rater(s)")
    print(f"  {key_path} — DO NOT show to rater until after they finish")
    print(f"\nSampled {len(sampled)} results across {len(RESULT_FILES)} systems")

    # Print category distribution
    from collections import Counter
    cat_counts = Counter(r["category"] for r, _ in sampled)
    sys_counts = Counter(s for _, s in sampled)
    print(f"\nCategory distribution: {dict(cat_counts)}")
    print(f"System distribution: {dict(sys_counts)}")


if __name__ == "__main__":
    main()
