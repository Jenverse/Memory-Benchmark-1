#!/usr/bin/env python3
"""
Post-experiment analysis: generates paper-ready figures and detailed analysis.

Usage:
    python analyze_results.py --mem0 results/mem0_metrics_*.json --agent results/agent_metrics_*.json
    python analyze_results.py --results-dir results  # auto-find latest
"""

import argparse
import glob
import json
import os
import sys

import matplotlib.pyplot as plt
import matplotlib
matplotlib.use("Agg")
import numpy as np
import seaborn as sns

from benchmark.data import FAILURE_CATEGORIES
from evaluation.failure_analysis import categorize_failures, build_failure_mode_comparison


def load_latest_metrics(results_dir: str, system: str) -> dict:
    """Load the most recent metrics file for a system."""
    pattern = os.path.join(results_dir, f"{system}_metrics_*.json")
    files = sorted(glob.glob(pattern))
    if not files:
        return None
    with open(files[-1]) as f:
        return json.load(f)


def plot_category_comparison(mem0: dict, agent: dict, output_dir: str):
    """Fig 1: Bar chart comparing accuracy by failure category."""
    categories = FAILURE_CATEGORIES
    cat_labels = [c.replace("_", "\n") for c in categories]

    mem0_acc = [mem0["by_category"].get(c, {}).get("accuracy", 0) for c in categories]
    agent_acc = [agent["by_category"].get(c, {}).get("accuracy", 0) for c in categories]

    x = np.arange(len(categories))
    width = 0.35

    fig, ax = plt.subplots(figsize=(12, 6))
    bars1 = ax.bar(x - width/2, mem0_acc, width, label="Mem0 (External)", color="#e74c3c", alpha=0.8)
    bars2 = ax.bar(x + width/2, agent_acc, width, label="Agent-Driven", color="#3498db", alpha=0.8)

    ax.set_ylabel("Accuracy", fontsize=12)
    ax.set_title("Memory System Accuracy by Failure Category", fontsize=14, fontweight="bold")
    ax.set_xticks(x)
    ax.set_xticklabels(cat_labels, fontsize=9)
    ax.legend(fontsize=11)
    ax.set_ylim(0, 1.1)
    ax.axhline(y=1.0, color="gray", linestyle="--", alpha=0.3)

    # Add value labels on bars
    for bar in bars1:
        height = bar.get_height()
        if height > 0:
            ax.annotate(f"{height:.0%}", xy=(bar.get_x() + bar.get_width() / 2, height),
                       xytext=(0, 3), textcoords="offset points", ha="center", va="bottom", fontsize=8)
    for bar in bars2:
        height = bar.get_height()
        if height > 0:
            ax.annotate(f"{height:.0%}", xy=(bar.get_x() + bar.get_width() / 2, height),
                       xytext=(0, 3), textcoords="offset points", ha="center", va="bottom", fontsize=8)

    plt.tight_layout()
    path = os.path.join(output_dir, "fig1_category_comparison.pdf")
    plt.savefig(path, dpi=300, bbox_inches="tight")
    plt.savefig(path.replace(".pdf", ".png"), dpi=300, bbox_inches="tight")
    plt.close()
    print(f"Saved: {path}")


def plot_failure_modes(mem0: dict, agent: dict, output_dir: str):
    """Fig 2: Failure mode frequency comparison."""
    comparison = build_failure_mode_comparison(mem0, agent)

    modes = sorted(comparison.keys())
    if not modes:
        print("No failure modes to plot.")
        return

    mode_labels = [m.replace("_", "\n") for m in modes]
    mem0_counts = [comparison[m]["mem0_count"] for m in modes]
    agent_counts = [comparison[m]["agent_count"] for m in modes]

    x = np.arange(len(modes))
    width = 0.35

    fig, ax = plt.subplots(figsize=(10, 5))
    ax.bar(x - width/2, mem0_counts, width, label="Mem0 (External)", color="#e74c3c", alpha=0.8)
    ax.bar(x + width/2, agent_counts, width, label="Agent-Driven", color="#3498db", alpha=0.8)

    ax.set_ylabel("Count", fontsize=12)
    ax.set_title("Failure Mode Frequency", fontsize=14, fontweight="bold")
    ax.set_xticks(x)
    ax.set_xticklabels(mode_labels, fontsize=9)
    ax.legend(fontsize=11)

    plt.tight_layout()
    path = os.path.join(output_dir, "fig2_failure_modes.pdf")
    plt.savefig(path, dpi=300, bbox_inches="tight")
    plt.savefig(path.replace(".pdf", ".png"), dpi=300, bbox_inches="tight")
    plt.close()
    print(f"Saved: {path}")


def plot_memory_efficiency(mem0: dict, agent: dict, output_dir: str):
    """Fig 3: Memory efficiency comparison (entries stored, tokens used)."""
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 5))

    # Left: Memory entries
    m0_eff = mem0["memory_efficiency"]
    ag_eff = agent["memory_efficiency"]

    metrics_labels = ["Total\nEntries", "Added", "Updated", "Deleted"]
    m0_vals = [m0_eff["avg_total_entries"], m0_eff["avg_entries_added"],
               m0_eff["avg_entries_updated"], m0_eff["avg_entries_deleted"]]
    ag_vals = [ag_eff["avg_total_entries"], ag_eff["avg_entries_added"],
               ag_eff["avg_entries_updated"], ag_eff["avg_entries_deleted"]]

    x = np.arange(len(metrics_labels))
    width = 0.35
    ax1.bar(x - width/2, m0_vals, width, label="Mem0", color="#e74c3c", alpha=0.8)
    ax1.bar(x + width/2, ag_vals, width, label="Agent-Driven", color="#3498db", alpha=0.8)
    ax1.set_ylabel("Average per User")
    ax1.set_title("Memory Operations", fontweight="bold")
    ax1.set_xticks(x)
    ax1.set_xticklabels(metrics_labels)
    ax1.legend()

    # Right: Token usage (cost proxy)
    token_labels = ["Input\nTokens", "Output\nTokens"]
    m0_tokens = [m0_eff["total_input_tokens"], m0_eff["total_output_tokens"]]
    ag_tokens = [ag_eff["total_input_tokens"], ag_eff["total_output_tokens"]]

    # Add eval costs
    m0_eval = mem0.get("eval_costs", {})
    ag_eval = agent.get("eval_costs", {})

    x2 = np.arange(len(token_labels))
    ax2.bar(x2 - width/2, m0_tokens, width, label="Mem0 (memory ops)", color="#e74c3c", alpha=0.8)
    ax2.bar(x2 + width/2, ag_tokens, width, label="Agent-Driven (memory ops)", color="#3498db", alpha=0.8)
    ax2.set_ylabel("Total Tokens")
    ax2.set_title("LLM Token Usage (Memory Operations Only)", fontweight="bold")
    ax2.set_xticks(x2)
    ax2.set_xticklabels(token_labels)
    ax2.legend()

    plt.tight_layout()
    path = os.path.join(output_dir, "fig3_memory_efficiency.pdf")
    plt.savefig(path, dpi=300, bbox_inches="tight")
    plt.savefig(path.replace(".pdf", ".png"), dpi=300, bbox_inches="tight")
    plt.close()
    print(f"Saved: {path}")


def plot_heatmap(mem0: dict, agent: dict, output_dir: str):
    """Fig 4: Heatmap of per-test results for both systems."""
    m0_tests = {t["test_id"]: t for t in mem0["test_details"]}
    ag_tests = {t["test_id"]: t for t in agent["test_details"]}

    test_ids = sorted(set(list(m0_tests.keys()) + list(ag_tests.keys())))

    rating_map = {"correct": 2, "partially_correct": 1, "incorrect": 0, "error": -1}
    rating_labels = {2: "Correct", 1: "Partial", 0: "Incorrect", -1: "Error"}

    data = []
    labels_y = []
    for tid in test_ids:
        m0_r = rating_map.get(m0_tests.get(tid, {}).get("rating", "error"), -1)
        ag_r = rating_map.get(ag_tests.get(tid, {}).get("rating", "error"), -1)
        cat = m0_tests.get(tid, ag_tests.get(tid, {})).get("category", "?")
        data.append([m0_r, ag_r])
        labels_y.append(f"{tid}\n({cat})")

    data = np.array(data)

    fig, ax = plt.subplots(figsize=(6, max(8, len(test_ids) * 0.5)))
    cmap = sns.color_palette(["#e74c3c", "#f39c12", "#2ecc71"], as_cmap=True)
    sns.heatmap(
        data, ax=ax, cmap=cmap, vmin=0, vmax=2,
        xticklabels=["Mem0", "Agent-Driven"],
        yticklabels=labels_y,
        annot=True, fmt="d",
        cbar_kws={"ticks": [0, 1, 2], "label": "0=Incorrect, 1=Partial, 2=Correct"},
        linewidths=0.5,
    )
    ax.set_title("Per-Test Results Heatmap", fontsize=14, fontweight="bold")

    plt.tight_layout()
    path = os.path.join(output_dir, "fig4_heatmap.pdf")
    plt.savefig(path, dpi=300, bbox_inches="tight")
    plt.savefig(path.replace(".pdf", ".png"), dpi=300, bbox_inches="tight")
    plt.close()
    print(f"Saved: {path}")


def generate_narrative_analysis(mem0: dict, agent: dict) -> str:
    """Generate a narrative analysis for the paper's discussion section."""
    taxonomy = categorize_failures(mem0, agent)

    lines = []
    lines.append("NARRATIVE ANALYSIS FOR PAPER")
    lines.append("=" * 60)
    lines.append("")

    # Overall
    m0_acc = mem0["overall"]["accuracy"]
    ag_acc = agent["overall"]["accuracy"]
    lines.append(f"Overall: Mem0 {m0_acc:.0%} vs Agent-Driven {ag_acc:.0%}")
    lines.append("")

    # Category-level insights
    lines.append("KEY FINDINGS BY CATEGORY:")
    lines.append("-" * 40)

    for cat in FAILURE_CATEGORIES:
        t = taxonomy[cat]
        lines.append(f"\n{cat.upper()}:")
        lines.append(f"  Mem0: {t['mem0_accuracy']:.0%}, Agent: {t['agent_accuracy']:.0%}, Winner: {t['winner']}")

        if cat == "contradiction_update":
            lines.append("  -> This is the most critical differentiator. Does each system")
            lines.append("     correctly UPDATE facts rather than storing duplicates?")
        elif cat == "noise_resistance":
            lines.append("  -> Tests whether the system stores irrelevant information.")
            lines.append("     External systems are expected to over-extract here.")
        elif cat == "implicit_preference":
            lines.append("  -> Can the system identify communication preferences that")
            lines.append("     were demonstrated rather than explicitly stated?")
        elif cat == "temporal_relevance":
            lines.append("  -> Can the system recognize that some information is time-bound")
            lines.append("     and may no longer be current?")
        elif cat == "consolidation":
            lines.append("  -> When facts evolve over time (e.g., improving model results),")
            lines.append("     can the system present a coherent narrative?")
        elif cat == "cross_session":
            lines.append("  -> The hardest category: requires synthesizing information")
            lines.append("     from multiple sessions into a coherent whole.")
        elif cat == "simple_recall":
            lines.append("  -> Baseline capability: both systems should do well here.")

    # Failure modes
    lines.append("\n\nFAILURE MODE ANALYSIS:")
    lines.append("-" * 40)
    fm = build_failure_mode_comparison(mem0, agent)
    for mode, counts in sorted(fm.items(), key=lambda x: -(x[1]["mem0_count"] + x[1]["agent_count"])):
        lines.append(f"  {mode}: Mem0={counts['mem0_count']}, Agent={counts['agent_count']}")

    # Key arguments for the paper
    lines.append("\n\nKEY ARGUMENTS FOR THE PAPER:")
    lines.append("-" * 40)
    lines.append("1. Neither system solves the memory problem completely")
    lines.append("2. External memory (Mem0) likely over-extracts (noise_resistance failures)")
    lines.append("3. Agent-driven memory likely handles contradictions better (contradiction_update)")
    lines.append("4. Agent-driven memory costs more (LLM calls for memory management)")
    lines.append("5. Both likely struggle with temporal relevance (recognizing stale info)")
    lines.append("6. Cross-session synthesis is hard for both")
    lines.append("7. The field needs: hybrid approaches, memory-specific training, formal verification")

    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(description="Analyze MemoryBench results")
    parser.add_argument("--results-dir", default="results")
    parser.add_argument("--mem0", default=None, help="Path to Mem0 metrics JSON")
    parser.add_argument("--agent", default=None, help="Path to Agent metrics JSON")
    parser.add_argument("--output-dir", default="results/figures")
    args = parser.parse_args()

    # Load metrics
    if args.mem0:
        with open(args.mem0) as f:
            mem0_metrics = json.load(f)
    else:
        mem0_metrics = load_latest_metrics(args.results_dir, "mem0")

    if args.agent:
        with open(args.agent) as f:
            agent_metrics = json.load(f)
    else:
        agent_metrics = load_latest_metrics(args.results_dir, "agent")

    if not mem0_metrics or not agent_metrics:
        print("Error: Could not find metrics files. Run the experiment first:")
        print("  python run_experiment.py")
        sys.exit(1)

    os.makedirs(args.output_dir, exist_ok=True)

    print("Generating figures...")
    plot_category_comparison(mem0_metrics, agent_metrics, args.output_dir)
    plot_failure_modes(mem0_metrics, agent_metrics, args.output_dir)
    plot_memory_efficiency(mem0_metrics, agent_metrics, args.output_dir)
    plot_heatmap(mem0_metrics, agent_metrics, args.output_dir)

    print("\nGenerating narrative analysis...")
    narrative = generate_narrative_analysis(mem0_metrics, agent_metrics)
    print(narrative)

    narrative_path = os.path.join(args.output_dir, "narrative_analysis.txt")
    with open(narrative_path, "w") as f:
        f.write(narrative)
    print(f"\nNarrative saved to {narrative_path}")


if __name__ == "__main__":
    main()
