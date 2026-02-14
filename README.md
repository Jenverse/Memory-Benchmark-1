# Should Your Agent Manage Its Own Memory?

**An Empirical Study of Persistent Memory Strategies for LLM Agents**

Major AI products — ChatGPT, Claude, Cursor — have each built their own agent-managed memory systems rather than using third-party memory providers. This project empirically investigates whether that design choice is well-founded.

## What We Did

We conducted a controlled empirical study comparing how different persistent memory strategies perform when an LLM agent needs to remember information across conversation sessions.

**The key question**: Should you let your agent manage its own memory, or outsource it to an external provider?

**Why this matters**: Existing benchmarks like [LoCoMo](https://snap-research.github.io/locomo/) test whether an LLM can *recall* information from long conversations where the full history is available. We test a different problem: whether a memory *system* makes correct *curation* decisions — what to persist, update, delete, and consolidate — when prior sessions are no longer in context. This is the practical reality for production agents where you can't keep every past conversation in the context window.

### Evaluation Setup

- **20 synthetic user profiles** across 10 professional domains (data engineering, game dev, clinical research, cybersecurity, etc.)
- **5 conversation sessions per profile** with natural evolution — users change jobs, move cities, update preferences, share irrelevant details
- **57 ground-truth memory tests** across 7 categories:

| Category | Tests | What It Tests |
|----------|-------|---------------|
| Contradiction Update | 18 | User says NYC in Session 1, SF in Session 3 — does the system update? |
| Simple Recall | 8 | Can it remember basic facts from earlier sessions? |
| Implicit Preference | 5 | Does it pick up on communication style preferences? |
| Temporal Relevance | 6 | Does it know "on-call this week" from 3 sessions ago is stale? |
| Consolidation | 6 | Can it track evolving facts (model accuracy improving over time)? |
| Noise Resistance | 6 | Does it filter out "I spilled coffee" as irrelevant? |
| Cross-Session Synthesis | 8 | Can it combine facts from multiple sessions into a coherent answer? |

### The Systems We Compared

All systems used the same LLM (GPT-4o-mini) and embedding model (text-embedding-3-small).

1. **Current Session Only (Baseline)**: No memory of prior sessions. Simulates context window limitations.
2. **Mem0**: Open-source external memory provider. Extracts facts automatically, has built-in deduplication.
3. **Redis Agent Memory Server**: Two-stage external provider (working memory → long-term memory promotion).
4. **Agent-Driven**: The LLM manages its own memory — sees all stored memories, decides what to add/update/delete, periodically consolidates.

Plus **3 ablation variants** of the agent-driven approach to understand which components matter.

## Results

### Overall Accuracy

| System | Accuracy | With Partial Credit |
|--------|----------|-------------------|
| Current Session (Baseline) | 11.1% | 11.7% |
| Redis Agent Memory | 43.9% | 57.0% |
| Mem0 | 63.2% | 73.7% |
| **Agent-Driven** | **73.7%** | **84.2%** |

### Per-Category Breakdown

| Category | Baseline | Redis | Mem0 | Agent |
|----------|----------|-------|------|-------|
| Contradiction Update | 0% | 33% | 83% | **89%** |
| Simple Recall | 0% | 38% | 50% | **75%** |
| Implicit Preference | 0% | **100%** | **100%** | **100%** |
| Temporal Relevance | 17% | 50% | 67% | **83%** |
| Consolidation | 0% | **50%** | 33% | **50%** |
| Noise Resistance | **89%** | 83% | 83% | 83% |
| Cross-Session | 0% | 0% | 13% | **25%** |

### Ablation Study

| Variant | Accuracy | Drop |
|---------|----------|------|
| Agent-Driven (Full) | **73.7%** | — |
| − Memory Visibility | 63.2% | −10.5 pp |
| − Consolidation | 63.2% | −10.5 pp |
| − Update/Delete | 54.4% | −19.3 pp |

No single component explains the full gap. The advantage comes from the combination of custom extraction, memory visibility, explicit update/delete, and consolidation working together.

## Key Takeaways

1. **Agent-managed memory outperforms external providers**, but the gap is incremental (10.5 pp over Mem0), not categorical. External providers work reasonably well for simpler memory challenges.

2. **Mem0 handles contradictions well** (83%) through its built-in deduplication. The narrative that external providers are "blind" to existing memory is oversimplified — Mem0 checks for duplicates after extraction.

3. **Temporal relevance is where agent-managed memory has the clearest advantage.** External providers have no mechanism to proactively expire stale information.

4. **Cross-session synthesis is broken for everyone** (≤25%). This is a fundamental limitation of embedding-based retrieval, not a memory management problem.

5. **Update/delete is the most impactful single capability** (−19.3 pp when removed). A memory system that can only add facts deteriorates over time as contradictions accumulate.

6. **External providers need more study.** Areas like temporal relevance, memory consolidation, and extraction selectivity are underexplored and represent opportunities for improvement.

7. **This evaluation methodology could become a community benchmark.** Our diagnostic approach — multi-session profiles with ground-truth annotations targeting specific memory management challenges — could be scaled with crowdsourced conversations and broader scenario coverage.

## Project Structure

```
├── benchmark/
│   └── data.py              # 20 user profiles, 57 tests
├── memory_systems/
│   ├── agent_driven.py       # Agent-managed memory with full control
│   ├── external_mem0.py      # Mem0 wrapper
│   ├── redis_memory.py       # Redis Agent Memory Server wrapper
│   ├── ablations.py          # No Feedback, No Consolidation, Add Only
│   ├── no_memory.py          # Current session only baseline
│   └── embedder.py           # Shared embedding utilities
├── evaluation/
│   ├── runner.py             # Experiment runner
│   ├── metrics.py            # Scoring and aggregation
│   └── failure_analysis.py   # Failure mode classification
├── run_experiment.py          # Main experiment script
├── generate_figures.py        # Paper figure generation
├── results_v3/               # Raw experiment results (JSON)
└── finalpaper/               # Paper source (LaTeX + figures)
```

## Running Experiments

### Setup

1. **Install dependencies**
```bash
pip install -r requirements.txt
```

2. **Configure environment variables**
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
# Run specific systems
python run_experiment.py --system agent --trials 1
python run_experiment.py --system mem0 --trials 1
python run_experiment.py --system langmem --trials 1

# Run ablations
python run_experiment.py --system ablation_no_feedback --trials 1
python run_experiment.py --system ablation_no_consolidation --trials 1
python run_experiment.py --system ablation_add_only --trials 1
```

## Requirements

- Python 3.10+
- OpenAI API key (uses GPT-4o-mini and text-embedding-3-small)
- For Mem0 experiments: `pip install mem0ai`
- For LangMem experiments: `pip install agent-memory-client`
