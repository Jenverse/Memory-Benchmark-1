"""Failure taxonomy analysis — the core contribution of the paper.

Categorizes failures into a taxonomy that reveals systematic differences
between external (Mem0) and agent-driven memory systems.
"""

from collections import defaultdict
from benchmark.data import FAILURE_CATEGORIES


def categorize_failures(mem0_metrics: dict, agent_metrics: dict) -> dict:
    """Build the comparative failure taxonomy.

    This is the main table in the paper — showing where each system
    succeeds and fails across the 7 failure categories.
    """
    taxonomy = {}

    for cat in FAILURE_CATEGORIES:
        mem0_cat = mem0_metrics["by_category"].get(cat, {})
        agent_cat = agent_metrics["by_category"].get(cat, {})

        taxonomy[cat] = {
            "mem0_accuracy": mem0_cat.get("accuracy", 0),
            "mem0_accuracy_partial": mem0_cat.get("accuracy_with_partial", 0),
            "agent_accuracy": agent_cat.get("accuracy", 0),
            "agent_accuracy_partial": agent_cat.get("accuracy_with_partial", 0),
            "mem0_total": mem0_cat.get("total", 0),
            "agent_total": agent_cat.get("total", 0),
            "winner": _get_winner(mem0_cat, agent_cat),
        }

    return taxonomy


def _get_winner(mem0_cat: dict, agent_cat: dict) -> str:
    """Determine which system performs better on a category."""
    m0 = mem0_cat.get("accuracy_with_partial", 0)
    ag = agent_cat.get("accuracy_with_partial", 0)
    if abs(m0 - ag) < 0.1:
        return "tie"
    return "mem0" if m0 > ag else "agent"


def build_failure_mode_comparison(mem0_metrics: dict, agent_metrics: dict) -> dict:
    """Compare failure modes between the two systems."""
    all_modes = set(
        list(mem0_metrics.get("failure_modes", {}).keys()) +
        list(agent_metrics.get("failure_modes", {}).keys())
    )

    comparison = {}
    for mode in sorted(all_modes):
        comparison[mode] = {
            "mem0_count": mem0_metrics.get("failure_modes", {}).get(mode, 0),
            "agent_count": agent_metrics.get("failure_modes", {}).get(mode, 0),
        }

    return comparison


def generate_paper_tables(mem0_metrics: dict, agent_metrics: dict) -> str:
    """Generate LaTeX-ready tables for the paper."""
    taxonomy = categorize_failures(mem0_metrics, agent_metrics)
    failure_comparison = build_failure_mode_comparison(mem0_metrics, agent_metrics)

    output = []

    # Table 1: Overall Results
    output.append("=" * 70)
    output.append("TABLE 1: Overall Results")
    output.append("=" * 70)
    output.append(f"{'Metric':<30} {'Mem0':>15} {'Agent-Driven':>15}")
    output.append("-" * 70)

    m0_overall = mem0_metrics["overall"]
    ag_overall = agent_metrics["overall"]
    output.append(f"{'Accuracy':<30} {m0_overall['accuracy']:>14.1%} {ag_overall['accuracy']:>14.1%}")
    output.append(f"{'Accuracy (w/ partial)':<30} {m0_overall['accuracy_with_partial']:>14.1%} {ag_overall['accuracy_with_partial']:>14.1%}")
    output.append(f"{'Correct':<30} {m0_overall['correct']:>15} {ag_overall['correct']:>15}")
    output.append(f"{'Partially Correct':<30} {m0_overall['partially_correct']:>15} {ag_overall['partially_correct']:>15}")
    output.append(f"{'Incorrect':<30} {m0_overall['incorrect']:>15} {ag_overall['incorrect']:>15}")

    # Table 2: Category Breakdown (the failure taxonomy)
    output.append("")
    output.append("=" * 80)
    output.append("TABLE 2: Failure Taxonomy — Accuracy by Category")
    output.append("=" * 80)
    output.append(f"{'Category':<25} {'N':>5} {'Mem0':>10} {'Agent':>10} {'Winner':>10}")
    output.append("-" * 80)

    for cat in FAILURE_CATEGORIES:
        t = taxonomy[cat]
        n = t["mem0_total"]
        m0_acc = f"{t['mem0_accuracy']:.0%}" if n > 0 else "N/A"
        ag_acc = f"{t['agent_accuracy']:.0%}" if n > 0 else "N/A"
        winner = t["winner"]
        output.append(f"{cat:<25} {n:>5} {m0_acc:>10} {ag_acc:>10} {winner:>10}")

    # Table 3: Failure Modes
    output.append("")
    output.append("=" * 60)
    output.append("TABLE 3: Failure Mode Frequency")
    output.append("=" * 60)
    output.append(f"{'Failure Mode':<30} {'Mem0':>10} {'Agent':>10}")
    output.append("-" * 60)

    for mode, counts in sorted(failure_comparison.items()):
        output.append(f"{mode:<30} {counts['mem0_count']:>10} {counts['agent_count']:>10}")

    # Table 4: Memory Efficiency
    output.append("")
    output.append("=" * 60)
    output.append("TABLE 4: Memory Efficiency")
    output.append("=" * 60)
    output.append(f"{'Metric':<30} {'Mem0':>12} {'Agent':>12}")
    output.append("-" * 60)

    m0_eff = mem0_metrics["memory_efficiency"]
    ag_eff = agent_metrics["memory_efficiency"]
    output.append(f"{'Avg memories stored':<30} {m0_eff['avg_total_entries']:>11.1f} {ag_eff['avg_total_entries']:>11.1f}")
    output.append(f"{'Avg entries added':<30} {m0_eff['avg_entries_added']:>11.1f} {ag_eff['avg_entries_added']:>11.1f}")
    output.append(f"{'Avg entries updated':<30} {m0_eff['avg_entries_updated']:>11.1f} {ag_eff['avg_entries_updated']:>11.1f}")
    output.append(f"{'Avg entries deleted':<30} {m0_eff['avg_entries_deleted']:>11.1f} {ag_eff['avg_entries_deleted']:>11.1f}")
    output.append(f"{'Avg LLM calls (memory ops)':<30} {m0_eff['avg_llm_calls']:>11.1f} {ag_eff['avg_llm_calls']:>11.1f}")
    output.append(f"{'Total input tokens':<30} {m0_eff['total_input_tokens']:>11,} {ag_eff['total_input_tokens']:>11,}")
    output.append(f"{'Total output tokens':<30} {m0_eff['total_output_tokens']:>11,} {ag_eff['total_output_tokens']:>11,}")

    # Table 5: Per-test comparison
    output.append("")
    output.append("=" * 90)
    output.append("TABLE 5: Head-to-Head Per-Test Comparison")
    output.append("=" * 90)
    output.append(f"{'Test ID':<20} {'Category':<22} {'Mem0':>12} {'Agent':>12} {'Match':>8}")
    output.append("-" * 90)

    m0_tests = {t["test_id"]: t for t in mem0_metrics["test_details"]}
    ag_tests = {t["test_id"]: t for t in agent_metrics["test_details"]}

    for test_id in sorted(set(list(m0_tests.keys()) + list(ag_tests.keys()))):
        m0_rating = m0_tests.get(test_id, {}).get("rating", "N/A")
        ag_rating = ag_tests.get(test_id, {}).get("rating", "N/A")
        cat = m0_tests.get(test_id, ag_tests.get(test_id, {})).get("category", "unknown")
        match = "Y" if m0_rating == ag_rating else "N"
        output.append(f"{test_id:<20} {cat:<22} {m0_rating:>12} {ag_rating:>12} {match:>8}")

    return "\n".join(output)


def generate_latex_tables(mem0_metrics: dict, agent_metrics: dict) -> str:
    """Generate LaTeX table code for the paper."""
    taxonomy = categorize_failures(mem0_metrics, agent_metrics)

    latex = []
    latex.append(r"\begin{table}[t]")
    latex.append(r"\centering")
    latex.append(r"\caption{Failure Taxonomy: Accuracy by Category}")
    latex.append(r"\label{tab:failure_taxonomy}")
    latex.append(r"\begin{tabular}{lcccl}")
    latex.append(r"\toprule")
    latex.append(r"\textbf{Category} & \textbf{N} & \textbf{Mem0} & \textbf{Agent-Driven} & \textbf{Winner} \\")
    latex.append(r"\midrule")

    for cat in FAILURE_CATEGORIES:
        t = taxonomy[cat]
        n = t["mem0_total"]
        cat_display = cat.replace("_", " ").title()
        m0 = f"{t['mem0_accuracy']:.0%}" if n > 0 else "N/A"
        ag = f"{t['agent_accuracy']:.0%}" if n > 0 else "N/A"
        winner = t["winner"].title()
        latex.append(f"{cat_display} & {n} & {m0} & {ag} & {winner} \\\\")

    latex.append(r"\bottomrule")
    latex.append(r"\end{tabular}")
    latex.append(r"\end{table}")

    return "\n".join(latex)
