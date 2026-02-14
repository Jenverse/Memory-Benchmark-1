# Memory Systems Evaluation - Overview

## Executive Summary

This document provides a comprehensive overview of our evaluation of **4 different memory systems** for LLM agents using a diagnostic benchmark called **MemoryBench**.

**Key Results:**
- **Agent-Driven Memory**: 82.1% accuracy (89.3% with partial credit) ✅ **Best**
- **LangMem (External)**: 57.9% accuracy (73.7% with partial credit)
- **Mem0 (External)**: 57.1% accuracy (66.1% with partial credit)
- **Redis (External)**: 43.9% accuracy (57.0% with partial credit)
- **Zep (External)**: 10.5% accuracy (14.9% with partial credit) ❌ **Worst**

---

## What We Evaluated

### Memory Systems Tested

1. **Agent-Driven Memory** (Our Baseline)
   - Uses Claude (Anthropic) to actively reason about what to remember
   - Two-step process: decide what to store, then retrieve relevant memories
   - Highest accuracy overall

2. **LangMem** (External Memory System)
   - LangChain's memory SDK
   - Semantic memory extraction (facts & preferences)
   - Good at handling contradictions and implicit preferences

3. **Mem0** (External Memory System)
   - Automatic memory extraction and storage
   - Uses graph-based memory organization
   - Moderate performance

4. **Redis Agent Memory Server** (External Memory System)
   - Two-stage approach: working memory → long-term memory
   - LLM extraction pipeline
   - Moderate performance but struggles with contradictions

5. **Zep** (External Memory System)
   - Knowledge graph-based memory
   - Automatic fact extraction
   - Poor performance due to stale memory issues

---

## Evaluation Dataset

### Structure
- **20 user profiles** (diverse personas: engineers, researchers, designers, etc.)
- **5 sessions per profile** (100 total sessions)
  - **Sessions 1-4**: Training conversations (memory building)
  - **Session 5**: Test questions (memory retrieval)
- **57 total test questions** across all profiles

### Test Categories (7 Failure Modes)

1. **Simple Recall** (8 tests): Basic fact retrieval from earlier sessions
2. **Contradiction Update** (18 tests): Facts that change over time (e.g., user moves cities)
3. **Implicit Preference** (5 tests): Preferences inferred from behavior, never stated directly
4. **Temporal Relevance** (6 tests): Information that becomes outdated
5. **Consolidation** (6 tests): Related memories that should be merged
6. **Noise Resistance** (6 tests): Irrelevant chatter that should NOT be stored
7. **Cross-Session** (8 tests): Requires combining facts from multiple sessions

---

## Evaluation Methodology

### How It Works

1. **Memory Building Phase** (Sessions 1-4)
   - System processes 4 conversations with each user
   - Extracts and stores relevant memories
   - Updates memories when contradictions occur

2. **Testing Phase** (Session 5)
   - Ask specific questions that require memory recall
   - Compare system's answer to ground truth
   - Rate as: Correct, Partially Correct, or Incorrect

3. **Scoring**
   - **Accuracy**: % of correct answers
   - **Accuracy with Partial Credit**: % of correct + partially correct answers

### Example Test Case

**User Profile**: Sarah Chen (Software Engineer)

**Session 1**: Sarah mentions she's based in NYC, uses VS Code
**Session 2**: Sarah talks about processing 2TB Parquet files daily
**Session 3**: Sarah moves to San Francisco, switches to Neovim
**Session 4**: Sarah settles into SF

**Test Question (Session 5)**: "Where is Sarah based?"
- **Correct Answer**: San Francisco
- **Tests**: Contradiction Update (must update from NYC → SF)

---

## Key Findings

### 1. Agent-Driven Memory Wins Overall
- **82.1% accuracy** - significantly better than external systems
- Perfect scores on contradiction updates, implicit preferences, temporal relevance
- Active reasoning about what to remember is more effective than automatic extraction

### 2. External Memory Systems Struggle with Contradictions
- **Zep**: 0% on contradiction updates (keeps stale memories)
- **LangMem**: 66.7% on contradiction updates
- **Mem0**: 70% on contradiction updates

### 3. Zep's Catastrophic Failure
- Only 10.5% overall accuracy
- Main issue: Cannot update contradictory facts
- Example: Kept "NYC" when user moved to "SF"
- Only strength: Noise resistance (83.3%)

### 4. LangMem vs Mem0
- Similar overall performance (~57%)
- LangMem better at: Implicit preferences (80% vs 100%), Noise resistance
- Mem0 better at: Temporal relevance (0% vs 0% - both failed)

---

## Documentation Structure

This evaluation package contains:

1. **EVALUATION_OVERVIEW.md** (this file) - High-level summary
2. **TEST_DATA_STRUCTURE.md** - Detailed breakdown of 20 profiles and sessions
3. **RESULTS_SUMMARY.md** - Complete results with category breakdowns
4. **METHODOLOGY.md** - Detailed evaluation strategy and metrics

---

## For More Details

- See `TEST_DATA_STRUCTURE.md` for examples of all 20 user profiles
- See `RESULTS_SUMMARY.md` for detailed performance breakdowns
- See `METHODOLOGY.md` for evaluation metrics and scoring criteria
- See `benchmark/data.py` for the complete test dataset

---

## Quick Stats

| Metric | Agent-Driven | LangMem | Mem0 | Redis | Zep |
|--------|--------------|---------|------|-------|-----|
| **Overall Accuracy** | 82.1% | 57.9% | 57.1% | 43.9% | 10.5% |
| **w/ Partial Credit** | 89.3% | 73.7% | 66.1% | 57.0% | 14.9% |
| **Best Category** | Contradiction (100%) | Implicit Pref (80%) | Implicit Pref (100%) | Noise (83.3%) | Noise (83.3%) |
| **Worst Category** | Simple Recall (66.7%) | Cross-Session (25%) | Temporal (0%) | Contradiction (33.3%) | Most (0%) |

---

**Conclusion**: Agent-driven memory with active reasoning significantly outperforms automatic memory extraction systems, especially on contradiction updates and temporal relevance.

