# Evaluation Methodology

## Overview

This document describes the evaluation strategy, metrics, and scoring criteria used to benchmark memory systems for LLM agents.

---

## Evaluation Strategy

### 1. Dataset Design

**Goal**: Create a diagnostic benchmark that exposes specific failure modes of memory systems.

**Structure**:
- 20 diverse user profiles (engineers, researchers, designers, etc.)
- 5 sessions per profile (4 training + 1 testing)
- 57 total test questions across 7 failure categories

**Why 4 training sessions?**
- Allows for temporal evolution (facts changing over time)
- Enables cross-session memory testing
- Simulates realistic long-term user interactions

---

### 2. Test Categories (Failure Modes)

Each test question is designed to expose a specific failure mode:

#### 1. Simple Recall
- **What it tests**: Basic fact retrieval from earlier sessions
- **Example**: "What framework is Marcus using?" → "PyTorch Geometric"
- **Why it matters**: Fundamental capability of any memory system

#### 2. Contradiction Update
- **What it tests**: Updating facts when they change
- **Example**: User says "I'm in NYC" (Session 1), then "I moved to SF" (Session 3)
- **Why it matters**: Most common failure mode; systems must update, not duplicate

#### 3. Implicit Preference
- **What it tests**: Inferring preferences from behavior
- **Example**: User always asks for visual explanations → prefers visual learning
- **Why it matters**: Users don't always state preferences explicitly

#### 4. Temporal Relevance
- **What it tests**: Recognizing when information becomes outdated
- **Example**: "I'm on-call this week" → "rotation ended" → should not say still on-call
- **Why it matters**: Time-sensitive information must be tracked

#### 5. Consolidation
- **What it tests**: Merging related memories
- **Example**: Model performance mentioned across sessions: 67% → 71% → 73%
- **Why it matters**: Prevents memory fragmentation

#### 6. Noise Resistance
- **What it tests**: Ignoring irrelevant information
- **Example**: "My flight was delayed" in casual chat → should NOT store
- **Why it matters**: Prevents memory pollution

#### 7. Cross-Session
- **What it tests**: Combining facts from multiple sessions
- **Example**: "What has Priya learned?" → Python (S2) + SQL (S3) + pandas (S4)
- **Why it matters**: Real users build knowledge over time

---

### 3. Evaluation Process

#### Phase 1: Memory Building (Sessions 1-4)

For each profile:
1. Feed Session 1 conversation to memory system
2. System extracts and stores memories
3. Repeat for Sessions 2, 3, 4
4. System should update/consolidate memories as needed

#### Phase 2: Testing (Session 5)

For each test question:
1. Retrieve relevant memories from the system
2. Generate answer using retrieved memories
3. Compare to ground truth answer
4. Rate as: Correct, Partially Correct, or Incorrect

---

### 4. Scoring Criteria

#### Rating Scale

**Correct** ✅
- Answer matches ground truth
- All key facts present
- No significant errors

**Partially Correct** ~
- Answer has some correct information
- Missing some key details
- Or has minor inaccuracies

**Incorrect** ❌
- Answer is wrong
- Missing critical information
- Or contradicts ground truth

#### Example Scoring

**Question**: "Where is Sarah based?"
**Ground Truth**: "San Francisco (moved from NYC)"

- ✅ **Correct**: "Sarah is based in San Francisco"
- ~ **Partial**: "Sarah moved recently" (missing location)
- ❌ **Incorrect**: "Sarah is based in New York City" (stale memory)

---

### 5. Metrics

#### Primary Metrics

1. **Accuracy**
   - Formula: `Correct / Total Tests`
   - Example: 33 correct out of 57 tests = 57.9%

2. **Accuracy with Partial Credit**
   - Formula: `(Correct + Partially Correct) / Total Tests`
   - Example: (33 + 9) / 57 = 73.7%

#### Category-Specific Metrics

For each of the 7 failure categories:
- Accuracy per category
- Identifies specific weaknesses

#### Failure Mode Analysis

Track why systems fail:
- **Missing Memory**: Didn't extract/store the fact
- **Stale Memory**: Kept outdated information
- **Noise Retrieved**: Retrieved irrelevant information

---

### 6. Memory Systems Tested

#### Agent-Driven Memory (Baseline)
- **How it works**: Uses Claude to actively reason about memories
- **Process**:
  1. After each conversation, LLM decides what to remember
  2. Before answering, LLM retrieves relevant memories
  3. Two-step active reasoning process

#### LangMem (External System)
- **How it works**: LangChain's memory SDK
- **Process**:
  1. Uses `create_memory_manager()` to extract facts
  2. Stores in semantic memory (facts & preferences)
  3. Passes existing memories to handle updates

#### Mem0 (External System)
- **How it works**: Automatic memory extraction
- **Process**:
  1. Sends conversation to Mem0 API
  2. Mem0 extracts facts automatically
  3. Retrieves memories using semantic search

#### Redis Agent Memory Server (External System)
- **How it works**: Two-stage memory approach
- **Process**:
  1. Stores conversations as "working memory"
  2. LLM extraction pipeline promotes to long-term memory
  3. Semantic retrieval from long-term store

#### Zep (External System)
- **How it works**: Knowledge graph-based memory
- **Process**:
  1. Sends messages to Zep threads
  2. Zep builds knowledge graph automatically
  3. Retrieves facts from user context

---

### 7. Experimental Controls

To ensure fair comparison:

1. **Same LLM for all systems**: GPT-4o-mini
2. **Same test questions**: All systems answer identical questions
3. **Same evaluation criteria**: Human-verified ground truth answers
4. **Same dataset**: All systems trained on same 4 sessions

---

### 8. Limitations

1. **Small dataset**: 20 profiles may not cover all edge cases
2. **Manual evaluation**: Ratings are human-judged (though based on clear criteria)
3. **English only**: All conversations in English
4. **Simulated users**: Not real user data
5. **Single trial**: Each system tested once (no averaging across multiple runs)

---

### 9. Reproducibility

To reproduce results:

```bash
# Run all systems
python run_experiment.py --system agent --trials 1
python run_experiment.py --system mem0 --trials 1
python run_experiment.py --system langmem --trials 1
python run_experiment.py --system zep_memory --trials 1

# Results saved to results/ directory
```

---

## Evaluation Insights

### What Makes a Good Memory System?

Based on our evaluation:

1. **Contradiction handling is critical** (31.6% of tests)
   - Must update facts, not duplicate them
   - Agent-Driven: 100%, Zep: 0%

2. **Active reasoning beats automatic extraction**
   - Agent-Driven: 82.1%
   - Best automatic system: 57.9%

3. **Noise resistance matters**
   - Systems must filter irrelevant information
   - Zep excels here (83.3%)

4. **Temporal awareness is hard**
   - Knowing when information becomes outdated
   - Most systems struggle (0-50%)

---

## Future Work

Potential improvements to the benchmark:

1. **Larger dataset**: 50-100 profiles
2. **Multi-trial evaluation**: Average across 3-5 runs
3. **Real user data**: Test on actual user conversations
4. **Multi-lingual**: Add non-English profiles
5. **Automated scoring**: Use LLM-as-judge for consistency
6. **More failure modes**: Add privacy, personalization, etc.

---

## Conclusion

This evaluation methodology provides a **diagnostic benchmark** that:
- Exposes specific failure modes
- Enables fair comparison across systems
- Identifies strengths and weaknesses
- Guides future memory system development

The key insight: **Active reasoning about what to remember significantly outperforms automatic extraction.**

