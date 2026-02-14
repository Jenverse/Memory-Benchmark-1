# MemoryBench

**A Diagnostic Benchmark for Persistent Memory in LLM Agents**

This repository contains **MemoryBench**, a diagnostic benchmark for evaluating how well memory systems handle persistent information across conversation sessions when prior context is no longer available.

## Overview

Existing benchmarks like [LoCoMo](https://snap-research.github.io/locomo/) and [LongBench](https://github.com/THUDM/LongBench) test whether LLMs can recall information from long conversations where the full history is available. MemoryBench tests a different problem: whether memory systems make correct **curation decisions** — what to store, update, delete, and consolidate — when prior sessions are no longer in the context window.

This is the practical reality for production agents where you can't keep every past conversation in context.

## Benchmark Design

MemoryBench is designed around three principles:

1. **Multi-session realism**: Each profile spans 5 sessions reflecting natural evolution (job changes, relocations, preference shifts)
2. **Targeted failure modes**: 71 tests across 7 categories that isolate specific memory operations
3. **Controlled comparison**: Same LLM (GPT-4o-mini), same embeddings (text-embedding-3-small), same retrieval setup

### Test Categories

| Category | Tests | What It Tests |
|----------|-------|---------------|
| Contradiction Update | 18 | Does the system update when facts change? (NYC → SF) |
| Temporal Relevance | 10 | Does it recognize time-sensitive information is stale? |
| Implicit Preference | 10 | Does it capture unstated preferences from behavior? |
| Noise Resistance | 9 | Does it filter irrelevant information? |
| Simple Recall | 8 | Can it retrieve basic facts from earlier sessions? |
| Consolidation | 8 | Can it merge related facts across sessions? |
| Cross-Session Synthesis | 8 | Can it combine information from multiple sessions? |

**Total**: 20 user profiles × 5 sessions × 71 tests = 1,420 test instances

## Systems Evaluated

All systems use the same LLM (GPT-4o-mini) and embedding model (text-embedding-3-small) for fair comparison.

### Memory System Paradigms

**Agent-Driven (Agent-Managed)**
- LLM directly controls memory operations (add, update, delete)
- Sees all stored memories during conversation
- Periodically consolidates related memories
- Custom extraction logic per conversation

**External Memory Services**
- **Mem0**: Automated extraction pipeline with deduplication
- **LangMem**: Graph-based memory with entity extraction
- **Zep**: Fact extraction with temporal decay
- **Redis**: Two-stage working/long-term memory

**Baseline**
- **Current Session Only**: No persistent memory (simulates context window limitations)

## Results

**Note**: These results are illustrative, demonstrating the diagnostic value of MemoryBench. Absolute performance varies with prompts, retrieval configurations, and implementation details. The benchmark's contribution is the taxonomy and evaluation protocol for structured analysis.

### Overall Strict Accuracy

| System | Strict Accuracy |
|--------|----------------|
| **Base** (no memory) | 0.0% |
| **Zep** | 29.6% |
| **Redis** | 43.7% |
| **Mem0** | 45.1% |
| **LangMem** | 62.0% |
| **Agent-Driven** | 62.0% |

### Per-Category Performance

Agent-Driven and LangMem achieve identical aggregate scores (62.0%) but show complementary strengths:

**Agent-Driven excels at**:
- Contradiction Update (83.3% vs LangMem 72.2%)
- Temporal Relevance (70.0% vs LangMem 60.0%)

**LangMem excels at**:
- Consolidation (75.0% vs Agent-Driven 50.0%)
- Cross-Session Synthesis (50.0% vs Agent-Driven 37.5%)

**Both struggle with**:
- Noise Resistance (Agent: 55.6%, LangMem: 55.6%)

This demonstrates how MemoryBench's category-level analysis reveals structured differences that aggregate accuracy obscures.

## Key Findings

1. **No single paradigm dominates**: Agent-Driven and LangMem tie at 62.0%, but excel at different operations

2. **Category-level analysis is essential**: Aggregate scores hide complementary strengths and weaknesses

3. **Temporal relevance favors agent control**: Systems with explicit update/delete operations handle time-sensitive information better

4. **Consolidation favors graph-based memory**: LangMem's entity-relationship structure enables better fact merging

5. **Noise resistance is universally challenging**: All systems struggle to filter irrelevant information (≤55.6%)

6. **Evaluation methodology matters**: MemoryBench's diagnostic framework reveals structured differences that end-to-end accuracy obscures

## Repository Structure

```
├── benchmark/
│   └── data.py                    # 20 user profiles, 71 tests across 7 categories
├── memory_systems/
│   ├── agent_driven.py            # Agent-managed memory
│   ├── external_mem0.py           # Mem0 wrapper
│   ├── langmem_memory.py          # LangMem wrapper
│   ├── zep_memory.py              # Zep wrapper
│   ├── redis_memory.py            # Redis wrapper
│   ├── base.py                    # Base memory interface
│   └── embedder.py                # Shared embedding utilities
├── evaluation/
│   ├── runner.py                  # Experiment runner
│   ├── metrics.py                 # Scoring and aggregation
│   └── failure_analysis.py        # Category-level analysis
├── human_validation/
│   ├── annotation_sheet.csv       # Human validation data
│   ├── answer_key.csv             # Ground truth answers
│   └── compute_agreement.py       # Agreement calculation (97.2%)
├── results_v5/                    # Latest experimental results
│   ├── langmem_*.json             # LangMem results (62.0%)
│   ├── mem0_*.json                # Mem0 results (45.1%)
│   └── agent_*.json               # Agent-Driven results
├── results_v5_improved/           # Agent-Driven improved (62.0%)
├── shortpaper/                    # ICLR 2026 workshop submission
│   ├── short_paper.tex            # LaTeX source
│   ├── short_paper.pdf            # Compiled paper (5 pages)
│   ├── references.bib             # Bibliography
│   └── radar_chart.pdf            # Performance visualization
├── docs/                          # Documentation
├── run_experiment.py              # Main experiment script
├── analyze_results.py             # Results analysis
└── validate_llm_judge.py          # LLM-as-a-judge validation
```

## Getting Started

### Installation

1. **Clone the repository**
```bash
git clone https://github.com/Jenverse/Memory-Benchmark-1.git
cd Memory-Benchmark-1
```

2. **Install dependencies**
```bash
pip install -r requirements.txt
```

3. **Configure environment variables**
```bash
# Copy the example environment file
cp .env.example .env

# Edit .env and add your API keys
# Required:
OPENAI_API_KEY=your-openai-api-key-here

# Optional (for specific memory systems):
MEM0_API_KEY=  # Leave empty to use local Mem0
ZEP_API_KEY=   # Only needed for Zep experiments
```

### Running Experiments

```bash
# Run specific memory systems
python run_experiment.py --system agent --trials 1
python run_experiment.py --system mem0 --trials 1
python run_experiment.py --system langmem --trials 1
python run_experiment.py --system zep --trials 1

# Analyze results
python analyze_results.py

# Validate LLM-as-a-judge
python validate_llm_judge.py
```

### Requirements

- Python 3.10+
- OpenAI API key (GPT-4o-mini and text-embedding-3-small)
- Optional: API keys for external memory services (Mem0, Zep)

## Paper

The ICLR 2026 workshop short paper is available in `shortpaper/short_paper.pdf`.

**Citation** (to be added after publication)

## Human Validation

LLM-as-a-judge evaluation was validated against human annotations with **97.2% agreement** (Cohen's κ = 0.94). See `human_validation/` for details.

## License

MIT License - see LICENSE file for details

## Contact

For questions about the benchmark or paper, please open an issue on GitHub.
