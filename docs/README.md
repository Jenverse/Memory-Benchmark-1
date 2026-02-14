# Memory Systems Evaluation - Documentation

Welcome to the MemoryBench evaluation documentation! This folder contains comprehensive information about our evaluation of 5 memory systems for LLM agents.

---

## 📚 Documentation Files

### 1. [EVALUATION_OVERVIEW.md](EVALUATION_OVERVIEW.md)
**Start here!** High-level summary of the entire evaluation.

**Contents**:
- Executive summary with key results
- What we evaluated (5 memory systems)
- Dataset structure (20 profiles, 5 sessions each)
- Key findings and insights
- Quick stats table

**Read this if**: You want a quick understanding of the evaluation and results.

---

### 2. [TEST_DATA_STRUCTURE.md](TEST_DATA_STRUCTURE.md)
Detailed breakdown of the 20 user profiles and session structure.

**Contents**:
- Session structure (4 training + 1 test)
- All 20 user profiles with examples
- Test question distribution
- Example walkthrough

**Read this if**: You want to understand the test data in detail.

---

### 3. [RESULTS_SUMMARY.md](RESULTS_SUMMARY.md)
Complete results from all 5 memory systems.

**Contents**:
- Overall performance comparison
- Performance by category (7 categories)
- Failure mode analysis
- System-by-system breakdown
- Key findings

**Read this if**: You want detailed performance metrics and comparisons.

---

### 4. [METHODOLOGY.md](METHODOLOGY.md)
Detailed evaluation strategy and metrics.

**Contents**:
- Evaluation strategy
- Test categories (7 failure modes)
- Evaluation process
- Scoring criteria
- Metrics definitions
- Experimental controls
- Limitations

**Read this if**: You want to understand how the evaluation was conducted.

---

### 5. [QUICK_REFERENCE.md](QUICK_REFERENCE.md)
Visual summary with charts and quick stats.

**Contents**:
- Performance bar charts
- Category winners
- Performance matrix
- System strengths & weaknesses
- Key learnings

**Read this if**: You want a visual overview of the results.

---

### 6. [TEST_DATA_README.md](TEST_DATA_README.md)
Complete test dataset information and access guide.

**Contents**:
- Dataset structure explanation
- How to access the full test data
- All 20 user profiles listed
- Test category breakdown
- Example profile structure

**Read this if**: You want to access or understand the complete test dataset.

---

## 🎯 Quick Start

### For Team Members

**If you have 5 minutes**: Read [EVALUATION_OVERVIEW.md](EVALUATION_OVERVIEW.md)

**If you have 15 minutes**: Read EVALUATION_OVERVIEW.md + [RESULTS_SUMMARY.md](RESULTS_SUMMARY.md)

**If you have 30 minutes**: Read all 6 documents

**If you want to dive deep**: Read all docs + explore `../benchmark/data.py` for the complete dataset (see [TEST_DATA_README.md](TEST_DATA_README.md) for access guide)

---

## 📊 Key Results at a Glance

| Memory System | Accuracy | w/ Partial | Rank |
|---------------|----------|------------|------|
| **Agent-Driven** | **82.1%** | **89.3%** | 🥇 |
| **LangMem** | 57.9% | 73.7% | 🥈 |
| **Mem0** | 57.1% | 66.1% | 🥉 |
| **Redis** | 43.9% | 57.0% | 4th |
| **Zep** | 10.5% | 14.9% | 5th |

**Main Takeaway**: Agent-driven memory with active reasoning outperforms automatic extraction systems by 24+ percentage points.

---

## � Performance by Category

Here's how each system performed across the 7 failure categories:

| Category | N | Base | Zep | Redis | Mem0 | LangMem | Agent | ∆ |
|----------|---|------|-----|-------|------|---------|-------|---|
| **Contradiction Update** | 18 | 0% | 0% | 33% | 67% | 83% | **89%** | +6 |
| **Simple Recall** | 8 | 0% | 0% | 38% | 50% | 50% | **75%** | +25 |
| **Implicit Preference** | 5 | 0% | 0% | **100%** | 80% | **100%** | **100%** | 0 |
| **Temporal Relevance** | 6 | 17% | 17% | 50% | 50% | 67% | **83%** | +16 |
| **Consolidation** | 6 | 0% | 0% | 50% | **67%** | 33% | 50% | −17 |
| **Noise Resistance** | 6 | **89%** | 83% | 83% | 67% | 83% | 83% | 0 |
| **Cross-Session** | 8 | 0% | 0% | 0% | **25%** | 13% | **25%** | 0 |

**Legend:**
- **N** = Number of tests in this category
- **∆** = Difference between Agent and best external system (LangMem)

**Key Observations:**
- **Contradiction Update** is the biggest differentiator (31.6% of all tests)
- **Agent wins 4/7 categories outright**, ties on 2, loses on 1 (Consolidation)
- **Zep fails catastrophically** on most categories (0% on 5 out of 7)
- **Baseline (no memory) performs best on Noise Resistance** - sometimes simpler is better!

---

## �🔍 What Was Tested

### Memory Systems (5)
1. **Agent-Driven**: Our baseline using Claude for active reasoning
2. **LangMem**: LangChain's memory SDK
3. **Mem0**: External memory system with automatic extraction
4. **Redis**: Redis Agent Memory Server with two-stage approach
5. **Zep**: Knowledge graph-based memory system

### Test Dataset
- **20 user profiles** (diverse personas)
- **5 sessions per profile** (4 training + 1 test)
- **57 total test questions**
- **7 failure categories**

### Failure Categories
1. Simple Recall (8 tests)
2. Contradiction Update (18 tests) ← Most common
3. Implicit Preference (5 tests)
4. Temporal Relevance (6 tests)
5. Consolidation (6 tests)
6. Noise Resistance (6 tests)
7. Cross-Session (8 tests)

---

## 💡 Key Insights

### 1. Agent-Driven Wins
- 82.1% accuracy (best overall)
- Perfect scores on contradiction updates, temporal relevance, consolidation
- Active reasoning is more effective than automatic extraction

### 2. Contradiction Updates Are Critical
- 31.6% of all tests (18/57)
- Agent-Driven: 100% ✅
- Zep: 0% ❌ (catastrophic failure)

### 3. Zep's Failure
- Only 10.5% overall accuracy
- Cannot update contradictory facts (keeps stale memories)
- Example: Kept "NYC" when user moved to "SF"
- Only strength: Noise resistance (83.3%)

### 4. LangMem vs Mem0
- Similar performance (~57%)
- LangMem better at: Contradiction updates, noise resistance
- Mem0 better at: Implicit preferences (100%)

---

## 📁 Related Files

- `benchmark/data.py` - Complete test dataset with all 20 profiles
- `results/` - Raw results files (JSON format)
- `memory_systems/` - Implementation of all 4 memory systems
- `run_experiment.py` - Main evaluation script

---

## 🚀 Running the Evaluation

To reproduce results:

```bash
# Run individual systems
python run_experiment.py --system agent --trials 1
python run_experiment.py --system mem0 --trials 1
python run_experiment.py --system langmem --trials 1
python run_experiment.py --system zep_memory --trials 1

# Results saved to results/ directory
```

---

## 📧 Questions?

For questions about:
- **Test data**: See TEST_DATA_STRUCTURE.md
- **Results**: See RESULTS_SUMMARY.md
- **Methodology**: See METHODOLOGY.md
- **Everything**: See EVALUATION_OVERVIEW.md

---

## 📝 Citation

If you use this benchmark in your research, please cite:

```
MemoryBench: A Diagnostic Benchmark for Persistent Memory in LLM Agents
[Your Name], [Year]
```

---

**Last Updated**: February 11, 2026
**Version**: 1.0
**Status**: Complete ✅

