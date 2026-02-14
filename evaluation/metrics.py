"""Compute metrics from experiment results."""

from collections import defaultdict
from benchmark.data import FAILURE_CATEGORIES


def compute_metrics(experiment_results: dict) -> dict:
    """Compute aggregate metrics from experiment results.

    Returns metrics at three levels:
    1. Overall accuracy
    2. Per-category accuracy (the failure taxonomy)
    3. Memory efficiency metrics
    """
    all_tests = []
    all_stats = []

    for profile_result in experiment_results["profile_results"]:
        for test_result in profile_result["test_results"]:
            all_tests.append(test_result)
        if profile_result.get("memory_stats"):
            all_stats.append(profile_result["memory_stats"])

    # 1. Overall accuracy
    total = len(all_tests)
    correct = sum(1 for t in all_tests if t["evaluation"].get("rating") == "correct")
    partial = sum(1 for t in all_tests if t["evaluation"].get("rating") == "partially_correct")
    incorrect = sum(1 for t in all_tests if t["evaluation"].get("rating") == "incorrect")

    overall = {
        "total_tests": total,
        "correct": correct,
        "partially_correct": partial,
        "incorrect": incorrect,
        "accuracy": correct / total if total > 0 else 0,
        "accuracy_with_partial": (correct + 0.5 * partial) / total if total > 0 else 0,
    }

    # 2. Per-category breakdown (the failure taxonomy)
    by_category = {}
    for cat in FAILURE_CATEGORIES:
        cat_tests = [t for t in all_tests if t["category"] == cat]
        if not cat_tests:
            by_category[cat] = {"total": 0, "correct": 0, "accuracy": 0}
            continue
        cat_correct = sum(1 for t in cat_tests if t["evaluation"].get("rating") == "correct")
        cat_partial = sum(1 for t in cat_tests if t["evaluation"].get("rating") == "partially_correct")
        by_category[cat] = {
            "total": len(cat_tests),
            "correct": cat_correct,
            "partially_correct": cat_partial,
            "incorrect": len(cat_tests) - cat_correct - cat_partial,
            "accuracy": cat_correct / len(cat_tests),
            "accuracy_with_partial": (cat_correct + 0.5 * cat_partial) / len(cat_tests),
        }

    # 3. Failure mode analysis
    failure_modes = defaultdict(int)
    for t in all_tests:
        for mode in t["evaluation"].get("failure_modes", []):
            failure_modes[mode] += 1

    # 4. Memory efficiency
    memory_efficiency = {
        "avg_total_entries": 0,
        "avg_entries_added": 0,
        "avg_entries_updated": 0,
        "avg_entries_deleted": 0,
        "avg_llm_calls": 0,
        "total_input_tokens": 0,
        "total_output_tokens": 0,
    }
    if all_stats:
        n = len(all_stats)
        memory_efficiency = {
            "avg_total_entries": sum(s["total_entries"] for s in all_stats) / n,
            "avg_entries_added": sum(s["entries_added"] for s in all_stats) / n,
            "avg_entries_updated": sum(s["entries_updated"] for s in all_stats) / n,
            "avg_entries_deleted": sum(s["entries_deleted"] for s in all_stats) / n,
            "avg_llm_calls": sum(s["llm_calls"] for s in all_stats) / n,
            "total_input_tokens": sum(s["total_input_tokens"] for s in all_stats),
            "total_output_tokens": sum(s["total_output_tokens"] for s in all_stats),
        }

    # 5. Per-test detailed results (for the paper)
    test_details = []
    for t in all_tests:
        test_details.append({
            "test_id": t["test_id"],
            "category": t["category"],
            "rating": t["evaluation"].get("rating", "unknown"),
            "failure_modes": t["evaluation"].get("failure_modes", []),
            "explanation": t["evaluation"].get("explanation", ""),
            "num_memories_retrieved": len(t.get("retrieved_memories", [])),
        })

    return {
        "system_name": experiment_results["system_name"],
        "overall": overall,
        "by_category": by_category,
        "failure_modes": dict(failure_modes),
        "memory_efficiency": memory_efficiency,
        "test_details": test_details,
        "eval_costs": experiment_results.get("eval_costs", {}),
    }
