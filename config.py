import os
from dotenv import load_dotenv

load_dotenv()

# LLM Configuration — OpenAI only
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

LLM_MODEL = os.getenv("LLM_MODEL", "gpt-4o-mini")

# Mem0 Configuration
MEM0_API_KEY = os.getenv("MEM0_API_KEY", None)  # None = use local Mem0
MEM0_USE_LOCAL = MEM0_API_KEY is None

# Experiment Configuration
RESULTS_DIR = os.path.join(os.path.dirname(__file__), "results")
BENCHMARK_SEED = 42

# Agent-Driven Memory Configuration
AGENT_MEMORY_MAX_ENTRIES = 100
AGENT_CONSOLIDATION_THRESHOLD = 20

# Cost tracking
TRACK_COSTS = True
