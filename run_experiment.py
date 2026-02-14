#!/usr/bin/env python3
"""
MemoryBench: Comparing External vs Agent-Driven Memory for LLM Agents

Main experiment runner with multi-trial support and all system variants.

Usage:
    # Run all 7 systems, 3 trials each
    python run_experiment.py --system all --trials 3

    # Run both primary systems (backward compat)
    python run_experiment.py --system both

    # Run a single system
    python run_experiment.py --system agent
    python run_experiment.py --system no_memory

    # Ablation studies
    python run_experiment.py --system ablation_no_feedback

    # Run on subset of profiles
    python run_experiment.py --profiles sarah_01 marcus_02 --model gpt-4o-mini
"""

import argparse
import json
import os
import sys
import time

import numpy as np
from dotenv import load_dotenv

load_dotenv()

from benchmark.data import PROFILES
from evaluation.runner import ExperimentRunner
from evaluation.metrics import compute_metrics
from evaluation.failure_analysis import generate_paper_tables, generate_latex_tables


# ---------------------------------------------------------------------------
# System registry
# ---------------------------------------------------------------------------

ALL_SYSTEM_NAMES = [
    "current_session",
    "mem0",
    "zep_memory",
    "langmem",
    "redis",
    "agent",
    "ablation_no_feedback",
    "ablation_no_consolidation",
    "ablation_add_only",
]

SYSTEM_DISPLAY_NAMES = {
    "current_session": "Current Session Only (Baseline)",
    "mem0": "External Memory (Mem0)",
    "zep_memory": "External Memory (Zep)",
    "langmem": "External Memory (LangMem)",
    "redis": "External Memory (Redis)",
    "agent": "Agent-Driven",
    "ablation_no_feedback": "Ablation: No Feedback",
    "ablation_no_consolidation": "Ablation: No Consolidation",
    "ablation_add_only": "Ablation: Add Only",
}


# ---------------------------------------------------------------------------
# Factory functions
# ---------------------------------------------------------------------------

def create_current_session_system(user_id: str):
    """Baseline: no memory from previous sessions (only current session context)."""
    from memory_systems.no_memory import NoMemoryBaseline
    return NoMemoryBaseline(user_id=user_id)


def create_zep_memory_system(user_id: str):
    """Factory for Zep Memory."""
    from memory_systems.zep_memory import ZepMemory
    return ZepMemory(user_id=user_id)


def create_langmem_system(user_id: str):
    """Factory for LangMem Memory."""
    from memory_systems.langmem_memory import LangMemMemory
    return LangMemMemory(user_id=user_id, openai_api_key=os.getenv("OPENAI_API_KEY"))


def create_mem0_system(user_id: str):
    from memory_systems.external_mem0 import Mem0Memory
    api_key = os.getenv("MEM0_API_KEY")
    return Mem0Memory(user_id=user_id, use_local=(api_key is None), api_key=api_key)


def create_redis_system(user_id: str):
    """Factory for Redis Agent Memory Server."""
    from memory_systems.redis_memory import RedisAgentMemory
    return RedisAgentMemory(user_id=user_id)


def create_agent_system(user_id: str, model: str = None):
    from memory_systems.agent_driven import AgentDrivenMemory
    return AgentDrivenMemory(
        user_id=user_id,
        openai_api_key=os.getenv("OPENAI_API_KEY"),
        model=model or os.getenv("LLM_MODEL", "gpt-4o-mini"),
    )


def create_ablation_no_feedback(user_id: str, model: str = None):
    from memory_systems.ablations import AgentNoFeedback
    return AgentNoFeedback(
        user_id=user_id,
        openai_api_key=os.getenv("OPENAI_API_KEY"),
        model=model or os.getenv("LLM_MODEL", "gpt-4o-mini"),
    )


def create_ablation_no_consolidation(user_id: str, model: str = None):
    from memory_systems.ablations import AgentNoConsolidation
    return AgentNoConsolidation(
        user_id=user_id,
        openai_api_key=os.getenv("OPENAI_API_KEY"),
        model=model or os.getenv("LLM_MODEL", "gpt-4o-mini"),
    )


def create_ablation_add_only(user_id: str, model: str = None):
    from memory_systems.ablations import AgentAddOnly
    return AgentAddOnly(
        user_id=user_id,
        openai_api_key=os.getenv("OPENAI_API_KEY"),
        model=model or os.getenv("LLM_MODEL", "gpt-4o-mini"),
    )


def get_factory(system_name: str, model: str):
    """Return a factory callable(user_id) -> BaseMemorySystem."""
    factories = {
        "current_session": lambda uid: create_current_session_system(uid),
        "mem0": lambda uid: create_mem0_system(uid),
        "zep_memory": lambda uid: create_zep_memory_system(uid),
        "langmem": lambda uid: create_langmem_system(uid),
        "redis": lambda uid: create_redis_system(uid),
        "agent": lambda uid: create_agent_system(uid, model),
        "ablation_no_feedback": lambda uid: create_ablation_no_feedback(uid, model),
        "ablation_no_consolidation": lambda uid: create_ablation_no_consolidation(uid, model),
        "ablation_add_only": lambda uid: create_ablation_add_only(uid, model),
    }
    return factories[system_name]


# ---------------------------------------------------------------------------
# Aggregation: mean +/- std across trials
# ---------------------------------------------------------------------------

def _aggregate_numeric_dict(dicts: list[dict]) -> dict:
    """For a list of dicts with the same keys, compute mean/std for numeric values."""
    if not dicts:
        return {}
    result = {}
    all_keys = set()
    for d in dicts:
        all_keys.update(d.keys())
    n = len(dicts)
    for key in sorted(all_keys):
        values = [d.get(key, 0) for d in dicts]
        if all(isinstance(v, (int, float)) for v in values):
            result[key] = {
                "mean": float(np.mean(values)),
                "std": float(np.std(values, ddof=1)) if n > 1 else 0.0,
            }
        else:
            result[key] = values[0]
    return result


def aggregate_trial_metrics(trial_metrics_list: list[dict]) -> dict:
    """Aggregate metrics from multiple trials into mean +/- std."""
    if not trial_metrics_list:
        return {}
    n = len(trial_metrics_list)

    aggregated = {
        "system_name": trial_metrics_list[0]["system_name"],
        "num_trials": n,
    }

    # Overall
    aggregated["overall"] = _aggregate_numeric_dict(
        [m["overall"] for m in trial_metrics_list]
    )

    # Per-category
    all_categories = set()
    for m in trial_metrics_list:
        all_categories.update(m.get("by_category", {}).keys())
    aggregated["by_category"] = {}
    for cat in sorted(all_categories):
        cat_dicts = [
            m["by_category"].get(cat, {"total": 0, "correct": 0, "accuracy": 0})
            for m in trial_metrics_list
        ]
        aggregated["by_category"][cat] = _aggregate_numeric_dict(cat_dicts)

    # Failure modes
    all_modes = set()
    for m in trial_metrics_list:
        all_modes.update(m.get("failure_modes", {}).keys())
    aggregated["failure_modes"] = {}
    for mode in sorted(all_modes):
        values = [m.get("failure_modes", {}).get(mode, 0) for m in trial_metrics_list]
        aggregated["failure_modes"][mode] = {
            "mean": float(np.mean(values)),
            "std": float(np.std(values, ddof=1)) if n > 1 else 0.0,
        }

    # Memory efficiency
    aggregated["memory_efficiency"] = _aggregate_numeric_dict(
        [m["memory_efficiency"] for m in trial_metrics_list]
    )

    # Eval costs (sum across trials)
    aggregated["eval_costs_total"] = {}
    cost_keys = trial_metrics_list[0].get("eval_costs", {}).keys()
    for k in cost_keys:
        values = [m.get("eval_costs", {}).get(k, 0) for m in trial_metrics_list]
        aggregated["eval_costs_total"][k] = int(sum(values))

    return aggregated


# ---------------------------------------------------------------------------
# Pretty-printing
# ---------------------------------------------------------------------------

def print_aggregated_summary(system_name: str, agg: dict):
    overall = agg.get("overall", {})
    acc = overall.get("accuracy", {})
    acc_p = overall.get("accuracy_with_partial", {})
    if isinstance(acc, dict):
        print(f"\n  {system_name}")
        print(f"    Accuracy:              {acc.get('mean', 0):.1%} +/- {acc.get('std', 0):.1%}")
        print(f"    Accuracy (w/ partial): {acc_p.get('mean', 0):.1%} +/- {acc_p.get('std', 0):.1%}")
    else:
        print(f"\n  {system_name}: Accuracy = {acc:.1%}")


def print_comprehensive_comparison(all_aggregated: dict):
    print("\n" + "=" * 80)
    print("COMPREHENSIVE COMPARISON (mean +/- std across trials)")
    print("=" * 80)

    print(f"\n{'System':<35} {'Accuracy':>20}")
    print("-" * 58)

    for sys_name in ALL_SYSTEM_NAMES:
        if sys_name not in all_aggregated:
            continue
        agg = all_aggregated[sys_name]
        overall = agg.get("overall", {})
        acc = overall.get("accuracy", {})
        display = SYSTEM_DISPLAY_NAMES.get(sys_name, sys_name)
        if isinstance(acc, dict):
            acc_str = f"{acc.get('mean', 0):.1%} +/- {acc.get('std', 0):.1%}"
        else:
            acc_str = f"{acc:.1%}"
        print(f"  {display:<33} {acc_str:>20}")


# ---------------------------------------------------------------------------
# Resolve --system argument
# ---------------------------------------------------------------------------

def resolve_systems(system_arg: str) -> list[str]:
    if system_arg == "all":
        return list(ALL_SYSTEM_NAMES)
    elif system_arg == "both":
        return ["mem0", "agent"]
    else:
        return [system_arg]


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(description="Run MemoryBench experiments")
    parser.add_argument(
        "--system",
        choices=[
            "all", "both", "mem0", "agent",
            "current_session", "zep_memory", "langmem", "redis",
            "ablation_no_feedback", "ablation_no_consolidation", "ablation_add_only",
        ],
        default="both",
        help="Which memory system(s) to run",
    )
    parser.add_argument("--trials", type=int, default=3,
                        help="Number of independent trials per system (default: 3)")
    parser.add_argument("--profiles", nargs="+", default=None,
                        help="Specific profile user_ids to run (default: all)")
    parser.add_argument("--model", default=None,
                        help="LLM model to use (default: gpt-4o-mini)")
    parser.add_argument("--output-dir", default="results",
                        help="Directory for output files")
    args = parser.parse_args()

    # Validate API key
    if not os.getenv("OPENAI_API_KEY"):
        print("Error: OPENAI_API_KEY not set. Create a .env file:")
        print('  echo "OPENAI_API_KEY=sk-..." > .env')
        sys.exit(1)

    # Filter profiles if specified
    profiles = PROFILES
    if args.profiles:
        profiles = [p for p in PROFILES if p["user_id"] in args.profiles]
        if not profiles:
            print(f"Error: No profiles found matching {args.profiles}")
            sys.exit(1)

    model = args.model or "gpt-4o-mini"
    systems_to_run = resolve_systems(args.system)

    print(f"Running MemoryBench with {len(profiles)} profiles")
    print(f"Systems: {', '.join(systems_to_run)}")
    print(f"Trials per system: {args.trials}")
    print(f"Model: {model}")
    print()

    os.makedirs(args.output_dir, exist_ok=True)
    timestamp = time.strftime("%Y%m%d_%H%M%S")

    all_aggregated = {}
    all_single_metrics = {}

    for system_name in systems_to_run:
        display_name = SYSTEM_DISPLAY_NAMES.get(system_name, system_name)
        factory = get_factory(system_name, model)

        print("=" * 60)
        print(f"Running {display_name}  ({args.trials} trial(s))")
        print("=" * 60)

        trial_metrics_list = []

        for trial_idx in range(1, args.trials + 1):
            print(f"\n--- Trial {trial_idx}/{args.trials} ---")

            runner = ExperimentRunner(
                openai_api_key=os.getenv("OPENAI_API_KEY"),
                model=model,
            )

            results = runner.run_full_experiment(
                memory_system_factory=factory,
                system_name=display_name,
                profiles=profiles,
            )

            # Save individual trial results
            trial_path = os.path.join(
                args.output_dir,
                f"{system_name}_trial{trial_idx}_results_{timestamp}.json",
            )
            runner.save_results(results, trial_path)

            # Compute metrics for this trial
            metrics = compute_metrics(results)
            metrics_path = os.path.join(
                args.output_dir,
                f"{system_name}_trial{trial_idx}_metrics_{timestamp}.json",
            )
            with open(metrics_path, "w") as f:
                json.dump(metrics, f, indent=2)

            acc = metrics["overall"]["accuracy"]
            print(f"  Trial {trial_idx} accuracy: {acc:.1%}")
            trial_metrics_list.append(metrics)

        # Aggregate across trials
        aggregated = aggregate_trial_metrics(trial_metrics_list)
        agg_path = os.path.join(
            args.output_dir, f"{system_name}_aggregated_{timestamp}.json",
        )
        with open(agg_path, "w") as f:
            json.dump(aggregated, f, indent=2, default=str)

        print_aggregated_summary(display_name, aggregated)

        all_aggregated[system_name] = aggregated
        all_single_metrics[system_name] = trial_metrics_list[-1]
        print()

    # Final comparison
    if len(all_aggregated) > 1:
        print_comprehensive_comparison(all_aggregated)

        comparison_path = os.path.join(
            args.output_dir, f"comparison_aggregated_{timestamp}.json",
        )
        with open(comparison_path, "w") as f:
            json.dump(all_aggregated, f, indent=2, default=str)
        print(f"\nComparison saved to {comparison_path}")

    # Legacy pairwise tables
    if "mem0" in all_single_metrics and "agent" in all_single_metrics:
        print("\n" + "=" * 60)
        print("PAIRWISE COMPARISON (External vs Agent-Driven, last trial)")
        print("=" * 60)

        tables = generate_paper_tables(
            all_single_metrics["mem0"], all_single_metrics["agent"],
        )
        print(tables)

        tables_path = os.path.join(args.output_dir, f"comparison_tables_{timestamp}.txt")
        with open(tables_path, "w") as f:
            f.write(tables)

        latex = generate_latex_tables(
            all_single_metrics["mem0"], all_single_metrics["agent"],
        )
        latex_path = os.path.join(args.output_dir, f"latex_tables_{timestamp}.tex")
        with open(latex_path, "w") as f:
            f.write(latex)

    print("\nExperiment complete!")


if __name__ == "__main__":
    main()
