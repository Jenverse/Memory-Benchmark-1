#!/usr/bin/env python3
"""
Compute inter-rater agreement between human annotations and LLM judge.

After the human fills in annotation_sheet.csv, run this script to compute:
- Raw agreement (% exact match)
- Cohen's kappa (chance-corrected agreement)
- Confusion matrix
- Per-category agreement breakdown

Usage:
    python human_validation/compute_agreement.py
"""

import csv
import sys
from collections import Counter

LABELS = ["correct", "partially_correct", "incorrect"]


def load_annotations(path):
    """Load human ratings from annotation sheet."""
    ratings = {}
    with open(path) as f:
        reader = csv.DictReader(f)
        for row in reader:
            rating = row["your_rating (correct/partially_correct/incorrect)"].strip().lower()
            if rating:
                ratings[int(row["id"])] = rating
    return ratings


def load_answer_key(path):
    """Load LLM judge ratings from answer key."""
    ratings = {}
    categories = {}
    with open(path) as f:
        reader = csv.DictReader(f)
        for row in reader:
            id_ = int(row["id"])
            ratings[id_] = row["llm_judge_rating"].strip().lower()
            categories[id_] = row["category"]
    return ratings, categories


def cohens_kappa(human, judge, labels):
    """Compute Cohen's kappa for inter-rater agreement."""
    n = len(human)
    if n == 0:
        return 0.0

    # Observed agreement
    agree = sum(1 for h, j in zip(human, judge) if h == j)
    po = agree / n

    # Expected agreement (by chance)
    human_counts = Counter(human)
    judge_counts = Counter(judge)
    pe = sum(
        (human_counts.get(label, 0) / n) * (judge_counts.get(label, 0) / n)
        for label in labels
    )

    if pe == 1.0:
        return 1.0
    return (po - pe) / (1 - pe)


def confusion_matrix(human, judge, labels):
    """Build confusion matrix."""
    matrix = {h: {j: 0 for j in labels} for h in labels}
    for h, j in zip(human, judge):
        if h in matrix and j in matrix[h]:
            matrix[h][j] += 1
    return matrix


def main():
    human_ratings = load_annotations("human_validation/annotation_sheet.csv")
    judge_ratings, categories = load_answer_key("human_validation/answer_key.csv")

    if not human_ratings:
        print("No human ratings found in annotation_sheet.csv!")
        print("Fill in the 'your_rating' column first, then re-run.")
        sys.exit(1)

    # Match IDs
    common_ids = sorted(set(human_ratings) & set(judge_ratings))
    human = [human_ratings[i] for i in common_ids]
    judge = [judge_ratings[i] for i in common_ids]
    cats = [categories[i] for i in common_ids]

    n = len(common_ids)
    print(f"Comparing {n} ratings\n")

    # Raw agreement
    agree = sum(1 for h, j in zip(human, judge) if h == j)
    print(f"Raw agreement: {agree}/{n} = {agree/n:.1%}")

    # Cohen's kappa
    kappa = cohens_kappa(human, judge, LABELS)
    print(f"Cohen's kappa: {kappa:.3f}")
    if kappa >= 0.8:
        print("  → Almost perfect agreement")
    elif kappa >= 0.6:
        print("  → Substantial agreement")
    elif kappa >= 0.4:
        print("  → Moderate agreement")
    else:
        print("  → Fair or poor agreement")

    # Confusion matrix
    print(f"\nConfusion matrix (rows=human, cols=judge):")
    cm = confusion_matrix(human, judge, LABELS)
    print(f"{'':20s} {'correct':>10s} {'partial':>10s} {'incorrect':>10s}")
    for label in LABELS:
        row = [cm[label].get(l, 0) for l in LABELS]
        display = label.replace("partially_correct", "partial")
        print(f"{display:20s} {row[0]:10d} {row[1]:10d} {row[2]:10d}")

    # Per-category agreement
    print(f"\nPer-category agreement:")
    cat_groups = {}
    for h, j, c in zip(human, judge, cats):
        cat_groups.setdefault(c, []).append((h, j))

    for cat in sorted(cat_groups):
        pairs = cat_groups[cat]
        cat_agree = sum(1 for h, j in pairs if h == j)
        print(f"  {cat:25s}: {cat_agree}/{len(pairs)} = {cat_agree/len(pairs):.0%}")

    # Disagreement analysis
    print(f"\nDisagreements:")
    for i, h, j in zip(common_ids, human, judge):
        if h != j:
            print(f"  ID {i}: human={h}, judge={j} (category={categories[i]})")

    # LaTeX-ready paragraph
    print(f"\n{'='*60}")
    print(f"LaTeX-ready paragraph for the paper:")
    print(f"{'='*60}")
    print(f"""
To validate our LLM judge, we sampled {n} test evaluations
stratified across systems and categories. A human annotator
independently rated each system response as correct, partially
correct, or incorrect against the ground truth. The LLM judge
achieved {agree/n:.0%} raw agreement with human ratings
(Cohen's $\\kappa = {kappa:.2f}$), indicating
{'substantial' if kappa >= 0.6 else 'moderate'} agreement.
""")


if __name__ == "__main__":
    main()
