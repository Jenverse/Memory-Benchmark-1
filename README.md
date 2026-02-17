# Memory System Evaluation Guide

**A Practical Guide for Evaluating Memory Systems in LLM Agents**

This repository provides a comprehensive evaluation framework for comparing different memory systems used in LLM agents. It's designed to help our data science and engineering team understand how various memory solutions perform and make informed decisions about which system to use for production applications.

## Why Evaluate Memory Systems?

In production LLM agents, you can't keep every past conversation in the context window. You need a **memory system** that can:
- Store important information from past conversations
- Update facts when they change (e.g., user moves from NYC to SF)
- Delete outdated or irrelevant information
- Retrieve the right information when needed
- Consolidate related facts across multiple sessions

**The challenge**: Different memory systems handle these operations differently. This evaluation framework helps you understand which system works best for your use case.

## What We're Comparing

We evaluated **4 different memory systems** to understand their strengths and weaknesses:

### 1. **Agent-Driven Memory** (Agent-Managed)
- The LLM directly controls what to store, update, and delete
- Sees all stored memories during conversations
- Periodically consolidates related information
- **Pros**: Full control over memory operations
- **Cons**: Requires careful prompt engineering

### 2. **Mem0** (External Memory Service)
- Automated extraction pipeline with deduplication
- Handles memory operations automatically
- **Pros**: Easy to integrate, no manual memory management
- **Cons**: Less control over what gets stored

### 3. **LangMem** (Graph-Based Memory)
- Graph-based memory with entity extraction
- Automatically builds knowledge graphs from conversations
- **Pros**: Good at consolidating related facts
- **Cons**: More complex setup

### 4. **Redis Agent Memory Server** (External Memory Service)
- Redis-based memory server with LLM extraction
- Vector search and semantic retrieval
- **Pros**: Scalable, production-ready infrastructure
- **Cons**: Performance depends on extraction quality

### 5. **Baseline** (No Memory)
- Only uses current session context
- Simulates what happens without persistent memory
- **Result**: 0.0% accuracy (can't answer questions about past sessions)

## How We Evaluate

Our evaluation uses **71 tests across 7 categories** that test different memory operations:

| Category | Tests | What It Tests | Why It Matters |
|----------|-------|---------------|----------------|
| **Contradiction Update** | 18 | Does the system update when facts change? | User moves from NYC to SF, changes jobs, etc. |
| **Temporal Relevance** | 10 | Does it recognize stale information? | "Current project" from 6 months ago is outdated |
| **Implicit Preference** | 10 | Does it capture unstated preferences? | User always picks vegetarian options |
| **Noise Resistance** | 9 | Does it filter irrelevant information? | Ignores random chitchat, focuses on important facts |
| **Simple Recall** | 8 | Can it retrieve basic facts? | User's name, location, job title |
| **Consolidation** | 8 | Can it merge related facts? | Combines info from multiple sessions |
| **Cross-Session Synthesis** | 8 | Can it connect information across sessions? | Links preferences to behavior patterns |

**Test Dataset**: 20 diverse user profiles × 5 sessions each = 100 conversation sessions

**Fair Comparison**: All systems use the same LLM (GPT-4o-mini) and embedding model (text-embedding-3-small)

## Results: How Do They Compare?

### Overall Performance

| System | Accuracy | Rank | Type |
|--------|----------|------|------|
| **Agent-Driven** | 62.0% | 🥇 1st | Agent-Managed |
| **LangMem** | 62.0% | 🥇 1st | Graph-Based |
| **Mem0** | 45.1% | 🥉 3rd | External Service |
| **Redis** | *Evaluating...* | TBD | External Service |
| **Base** (no memory) | 0.0% | - | Baseline |

> **Note**: Redis evaluation is currently running. Results will be updated once complete.

### Key Insights

#### 🏆 **Top Performers: Agent-Driven & LangMem (62.0%)**
Both achieve the same overall score but excel at **different operations**:

**Agent-Driven is better at:**
- ✅ **Contradiction Update**: 83.3% (vs LangMem 72.2%)
  - *Why*: Direct control over update/delete operations
  - *Example*: User moves from NYC to SF → system updates location
- ✅ **Temporal Relevance**: 70.0% (vs LangMem 60.0%)
  - *Why*: Can explicitly mark information as outdated
  - *Example*: "Current project" from 6 months ago gets deleted

**LangMem is better at:**
- ✅ **Consolidation**: 75.0% (vs Agent-Driven 50.0%)
  - *Why*: Graph structure naturally merges related facts
  - *Example*: Combines "likes coffee" + "visits Starbucks" → "prefers Starbucks coffee"
- ✅ **Cross-Session Synthesis**: 50.0% (vs Agent-Driven 37.5%)
  - *Why*: Entity relationships enable better connections
  - *Example*: Links work preferences to personal interests

**Both struggle with:**
- ⚠️ **Noise Resistance**: 55.6% for both
  - *Challenge*: Hard to distinguish important facts from casual chitchat

#### 📊 **Mem0 Performance (45.1%)**
- **Strengths**: Easy to integrate, automated extraction
- **Weaknesses**: Less control over what gets stored and updated
- **Best for**: Quick prototypes, simple use cases

#### 🔄 **Redis Performance (TBD)**
- **Status**: Currently evaluating on all 71 tests
- **Expected**: Results will show how Redis compares to other external memory services
- **Focus**: Production scalability vs. accuracy trade-offs

### Performance by Category

| Category | Agent-Driven | LangMem | Mem0 | Redis | Winner |
|----------|--------------|---------|------|-------|--------|
| Contradiction Update | 83.3% | 72.2% | ~45% | *TBD* | Agent-Driven |
| Temporal Relevance | 70.0% | 60.0% | ~40% | *TBD* | Agent-Driven |
| Consolidation | 50.0% | 75.0% | ~35% | *TBD* | LangMem |
| Cross-Session Synthesis | 37.5% | 50.0% | ~30% | *TBD* | LangMem |
| Implicit Preference | ~60% | ~60% | ~50% | *TBD* | Tie |
| Noise Resistance | 55.6% | 55.6% | ~45% | *TBD* | Tie |
| Simple Recall | ~65% | ~65% | ~50% | *TBD* | Tie |

## What This Means for You

### When to Use Each System

**Choose Agent-Driven if:**
- ✅ You need precise control over memory operations
- ✅ Your use case involves frequently changing information (locations, jobs, preferences)
- ✅ You can invest time in prompt engineering
- ✅ Temporal relevance is critical (e.g., project management, customer support)

**Choose LangMem if:**
- ✅ You need to consolidate information across many sessions
- ✅ Your use case involves complex relationships between entities
- ✅ You want automatic knowledge graph construction
- ✅ Cross-session synthesis is important (e.g., research assistants, knowledge bases)

**Choose Mem0 if:**
- ✅ You want quick integration with minimal setup
- ✅ Your use case is relatively simple (basic fact storage and retrieval)
- ✅ You prefer automated memory management
- ✅ Accuracy trade-offs are acceptable for ease of use

**Choose Redis if:**
- ✅ You need production-scale infrastructure
- ✅ You want vector search and semantic retrieval
- ✅ Scalability is a priority
- ✅ *Results pending - will update with specific recommendations*

### Trade-offs to Consider

1. **Control vs. Automation**
   - Agent-Driven: High control, requires more engineering
   - External services (Mem0, Redis): Low control, easier integration

2. **Accuracy vs. Ease of Use**
   - Agent-Driven & LangMem: Higher accuracy, more complex setup
   - Mem0: Lower accuracy, simpler integration

3. **Specialization vs. General Performance**
   - No single system is best at everything
   - Choose based on your specific use case requirements

## How to Run Your Own Evaluation

### Quick Start (5 minutes)

1. **Clone the repository**
```bash
git clone https://github.com/Jenverse/Memory-Benchmark-1.git
cd Memory-Benchmark-1
```

2. **Install dependencies**
```bash
pip install -r requirements.txt
```

3. **Set up your API keys**
```bash
# Copy the example environment file
cp .env.example .env

# Edit .env and add your OpenAI API key
# Required:
OPENAI_API_KEY=your-openai-api-key-here

# Optional (for specific memory systems):
MEM0_API_KEY=  # Leave empty to use local Mem0
```

4. **Run an evaluation**
```bash
# Evaluate Agent-Driven memory
python run_experiment.py --system agent --trials 1

# Evaluate Mem0
python run_experiment.py --system mem0 --trials 1

# Evaluate LangMem
python run_experiment.py --system langmem --trials 1

# Evaluate Redis
python run_experiment.py --system redis --trials 1
```

5. **Analyze results**
```bash
# View detailed results
python analyze_results.py
```

### What Gets Evaluated

Each evaluation runs through:
- **20 user profiles** (diverse personas: software engineers, teachers, consultants, etc.)
- **5 sessions per profile** (4 training sessions + 1 test session)
- **71 test questions** across 7 categories
- **Automated scoring** using LLM-as-a-judge (validated at 97.2% agreement with humans)

**Expected runtime**: 30-60 minutes per system (depending on API speed)

### Understanding the Results

After running an evaluation, you'll get:

1. **Overall accuracy** - How many questions the system answered correctly
2. **Per-category breakdown** - Which memory operations the system excels at
3. **Detailed logs** - Individual test results for debugging

Results are saved in `results_v5/` as JSON files.

## Repository Structure

```
├── benchmark/
│   └── data.py                    # 20 user profiles, 71 test questions
├── memory_systems/
│   ├── agent_driven.py            # Agent-managed memory implementation
│   ├── external_mem0.py           # Mem0 wrapper
│   ├── langmem_memory.py          # LangMem wrapper
│   ├── redis_memory.py            # Redis Agent Memory Server wrapper
│   └── base.py                    # Base memory interface
├── evaluation/
│   ├── runner.py                  # Experiment runner
│   ├── metrics.py                 # Scoring and aggregation
│   └── failure_analysis.py        # Category-level analysis
├── results_v5/                    # Latest experimental results
│   ├── agent_*.json               # Agent-Driven results (62.0%)
│   ├── langmem_*.json             # LangMem results (62.0%)
│   ├── mem0_*.json                # Mem0 results (45.1%)
│   └── redis_*.json               # Redis results (pending)
├── run_experiment.py              # Main experiment script
├── analyze_results.py             # Results analysis tool
└── .env.example                   # Environment variable template
```

## Evaluation Methodology

### How We Score

- **Correct**: System provides accurate, complete answer
- **Partially Correct**: System provides some relevant information but misses key details
- **Incorrect**: System provides wrong information or can't answer

### Validation

Our LLM-as-a-judge evaluation was validated against human annotations:
- **97.2% agreement** with human evaluators
- **Cohen's κ = 0.94** (near-perfect agreement)
- See `human_validation/` for details

### Fair Comparison

All systems use:
- Same LLM: GPT-4o-mini
- Same embeddings: text-embedding-3-small
- Same retrieval setup
- Same test questions

This ensures differences in performance reflect the memory system, not other variables.

## Requirements

- **Python 3.10+**
- **OpenAI API key** (for GPT-4o-mini and text-embedding-3-small)
- **Optional**: Mem0 API key (leave empty to use local Mem0)
- **Optional**: Redis server (for Redis memory system)

## Questions?

For questions about running evaluations or interpreting results, please:
- Open an issue on GitHub
- Check the `docs/` folder for additional documentation
- Review the code in `benchmark/data.py` to see the test questions

## License

MIT License - see LICENSE file for details
