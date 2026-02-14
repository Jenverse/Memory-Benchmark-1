# Complete Test Data

## Overview

This folder contains the complete test dataset used for evaluating memory systems.

**Location of Full Test Data**: `../benchmark/data.py`

---

## Dataset Structure

### 20 User Profiles

Each profile contains:
- **User ID**: Unique identifier (e.g., `sarah_01`)
- **Name**: User's full name
- **Description**: Brief summary of the user and what they test
- **5 Sessions**: 4 training sessions + 1 test session

### Session Structure

**Training Sessions (1-4)**:
- Conversation turns between user and assistant
- Expected memories that should be extracted
- Memory types: identity, profession, location, skills, preferences, etc.

**Test Session (5)**:
- 2-3 test questions per profile
- Each question has:
  - Test ID
  - Category (failure mode being tested)
  - Query (the question to ask)
  - Required memories (what the system needs to remember)
  - Ground truth answer

---

## Test Categories (7 Failure Modes)

1. **Simple Recall** (8 tests)
   - Basic fact retrieval from earlier sessions
   - Example: "What framework is Marcus using?" → "PyTorch Geometric"

2. **Contradiction Update** (18 tests)
   - Facts that change over time must be updated
   - Example: User moves from NYC → SF (must update, not duplicate)

3. **Implicit Preference** (5 tests)
   - Preferences inferred from behavior, never stated directly
   - Example: User always asks for visual explanations → prefers visual learning

4. **Temporal Relevance** (6 tests)
   - Information that becomes outdated
   - Example: "I'm on-call this week" → "rotation ended" → should not say still on-call

5. **Consolidation** (6 tests)
   - Related memories should be merged
   - Example: Model performance over time: 67% → 71% → 73%

6. **Noise Resistance** (6 tests)
   - Irrelevant chatter should NOT be stored
   - Example: "My flight was delayed" (not relevant to user's work)

7. **Cross-Session** (8 tests)
   - Combining facts from multiple sessions
   - Example: Session 1: "I use React", Session 3: "I use TypeScript" → "React + TypeScript"

---

## How to Access the Data

### Option 1: Python Import
```python
from benchmark.data import PROFILES

# Access all 20 profiles
for profile in PROFILES:
    print(f"User: {profile['name']}")
    print(f"Sessions: {len(profile['sessions'])}")
    print(f"Test questions: {len(profile['test_questions'])}")
```

### Option 2: Direct File Access
The complete test data is in: `benchmark/data.py`

This is a Python file with the `PROFILES` list containing all 20 user profiles with their sessions and test questions.

---

## Example Profile Structure

```python
{
    "user_id": "sarah_01",
    "name": "Sarah Chen",
    "description": "Software engineer learning Rust, moves from NYC to SF",
    "sessions": [
        {
            "session_id": 1,
            "turns": [
                {"role": "user", "content": "Hey! I'm Sarah..."},
                {"role": "assistant", "content": "Nice to meet you..."}
            ],
            "expected_memories_after": [
                {"fact": "Name is Sarah Chen", "type": "identity"},
                {"fact": "Based in New York City", "type": "location"}
            ]
        },
        # ... sessions 2-4 ...
        {
            "session_id": 5,
            "turns": []  # Test session has no training turns
        }
    ],
    "test_questions": [
        {
            "test_id": "sarah_01_t1",
            "category": "contradiction_update",
            "query": "Quick question — do you remember what editor I'm using these days?",
            "required_memories": ["Switched from VS Code to Neovim"],
            "ground_truth": "You switched from VS Code to Neovim..."
        }
    ]
}
```

---

## Statistics

- **Total Profiles**: 20
- **Total Sessions**: 100 (20 profiles × 5 sessions)
- **Total Test Questions**: 57
- **Test Distribution**:
  - Contradiction Update: 18 tests (31.6%)
  - Cross-Session: 8 tests (14.0%)
  - Simple Recall: 8 tests (14.0%)
  - Consolidation: 6 tests (10.5%)
  - Temporal Relevance: 6 tests (10.5%)
  - Noise Resistance: 6 tests (10.5%)
  - Implicit Preference: 5 tests (8.8%)

---

## All 20 User Profiles

1. **Sarah Chen** (sarah_01) - Software engineer, NYC→SF, VS Code→Neovim
2. **Marcus Williams** (marcus_02) - PhD student, GNN research, visual learner
3. **Priya Sharma** (priya_03) - Product Manager, PM→Senior PM, Postgres→BigQuery
4. **James Park** (james_04) - NLP PhD, EMNLP paper, TAing ended
5. **Aisha Okafor** (aisha_05) - ML Engineer, HealthPulse, Series A funding
6. **Chen Wei** (chen_06) - CV Researcher, object detection, 12 languages
7. **Maria Gonzalez** (maria_07) - Dev Advocate, Next.js stack
8. **David Kim** (david_08) - DevOps, Senior→Staff, on-call rotation ended
9. **Yuki Tanaka** (yuki_09) - Game Dev, turn-based→real-time, Switch→PC
10. **Alex Rivera** (alex_10) - Journalist, Obsidian→Notion, bullet points
11. **Elena Rossi** (elena_11) - UX Designer, Figma→Penpot, app launch
12. **Omar Hassan** (omar_12) - Security Engineer, incident response
13. **Lily Zhang** (lily_13) - Linguistics PhD, mBERT→XLM-R, NER tasks
14. **Thomas Okonkwo** (thomas_14) - Cloud Architect, AWS→GCP, 23 services
15. **Sophie Martin** (sophie_15) - Startup Founder, roadmap planning, team growth
16. **Raj Krishnamurthy** (raj_16) - Mobile Dev, React Native→Flutter
17. **Hannah Kim** (hannah_17) - Clinical Researcher, IRB approval, numbered lists
18. **Diego Fernandez** (diego_18) - Game Dev, Unity→Godot, C#→GDScript
19. **Amara Osei** (amara_19) - AI Researcher, DeepSpeed→FSDP
20. **Ben Nakamura** (ben_20) - Tech Writer, GitBook→Docusaurus, 50K views

---

**For complete details, see**: `../benchmark/data.py`

