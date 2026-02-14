"""
MemoryBench: A diagnostic benchmark for evaluating persistent memory in LLM agents.

20 user profiles x 5 sessions each, with ground-truth memory annotations.
Each profile tests specific failure modes of memory systems.

Failure categories:
1. simple_recall        - Basic fact retrieval from earlier session
2. contradiction_update - Fact changed between sessions (must update, not duplicate)
3. implicit_preference  - Never stated directly, must be inferred from behavior
4. temporal_relevance   - Information that becomes outdated/irrelevant
5. consolidation        - Related memories that should be merged
6. noise_resistance     - Irrelevant chatter that should NOT be stored
7. cross_session        - Requires combining facts from multiple sessions
"""

FAILURE_CATEGORIES = [
    "simple_recall",
    "contradiction_update",
    "implicit_preference",
    "temporal_relevance",
    "consolidation",
    "noise_resistance",
    "cross_session",
]

PROFILES = [
    # =========================================================================
    # Profile 1: Sarah Chen - Software Engineer
    # Tests: contradiction_update (moves cities), simple_recall, consolidation
    # =========================================================================
    {
        "user_id": "sarah_01",
        "name": "Sarah Chen",
        "description": "Software engineer learning Rust, moves from NYC to SF",
        "sessions": [
            {
                "session_id": 1,
                "turns": [
                    {"role": "user", "content": "Hey! I'm Sarah. I'm a software engineer based in New York City. I've been writing Python for about 6 years now and I'm thinking about picking up Rust."},
                    {"role": "assistant", "content": "Nice to meet you, Sarah! That's a great combination — Python for productivity and Rust for performance. What's drawing you to Rust? Is it for systems programming, or are you looking at it for something specific like WebAssembly or CLI tools?"},
                    {"role": "user", "content": "Mainly performance. I work on data pipelines at my company and some of our Python bottlenecks are painful. I tried Cython but it was messy. I think Rust could be a cleaner solution."},
                    {"role": "assistant", "content": "That makes a lot of sense. PyO3 is a great bridge — you can write performance-critical parts in Rust and call them from Python. Want me to help you get started with a small Rust + PyO3 project to replace one of your bottlenecks?"},
                    {"role": "user", "content": "Yes! That would be perfect. Also, I should mention I use VS Code for everything and I'm on a MacBook Pro M2."},
                ],
                "expected_memories_after": [
                    {"fact": "Name is Sarah Chen", "type": "identity", "importance": "high"},
                    {"fact": "Software engineer", "type": "profession", "importance": "high"},
                    {"fact": "Based in New York City", "type": "location", "importance": "high"},
                    {"fact": "6 years Python experience", "type": "skill", "importance": "medium"},
                    {"fact": "Learning Rust for performance", "type": "goal", "importance": "high"},
                    {"fact": "Works on data pipelines", "type": "work", "importance": "high"},
                    {"fact": "Tried Cython, found it messy", "type": "experience", "importance": "medium"},
                    {"fact": "Interested in PyO3", "type": "interest", "importance": "medium"},
                    {"fact": "Uses VS Code", "type": "tool", "importance": "medium"},
                    {"fact": "MacBook Pro M2", "type": "hardware", "importance": "low"},
                ],
            },
            {
                "session_id": 2,
                "turns": [
                    {"role": "user", "content": "I started the Rust book last night. The ownership system is blowing my mind — coming from Python where everything is garbage collected, this is a totally different world."},
                    {"role": "assistant", "content": "The ownership system is definitely the biggest mental shift coming from Python. The key insight is that Rust's compiler is doing at compile time what Python's garbage collector does at runtime. Would you like to work through some ownership examples?"},
                    {"role": "user", "content": "Yeah, but first — I was chatting with my team lead about this and she's actually supportive. She said if I can prove Rust speeds up our Parquet file processing pipeline, we might rewrite that whole module. Our current pipeline processes about 2TB of Parquet files daily."},
                    {"role": "assistant", "content": "That's a strong use case. Rust with the `polars` or `arrow-rs` crate can dramatically speed up Parquet processing. 2TB daily is significant — what are your current bottlenecks? Is it I/O bound or CPU bound?"},
                    {"role": "user", "content": "CPU bound mostly. We do a lot of decompression and aggregation. The Python code takes about 4 hours to run the full daily batch."},
                ],
                "expected_memories_after": [
                    {"fact": "Reading the Rust book", "type": "learning", "importance": "medium"},
                    {"fact": "Struggling with ownership system", "type": "learning", "importance": "medium"},
                    {"fact": "Team lead supports Rust adoption", "type": "work", "importance": "medium"},
                    {"fact": "Parquet file processing pipeline is target for Rust rewrite", "type": "work", "importance": "high"},
                    {"fact": "Processes 2TB Parquet files daily", "type": "work", "importance": "high"},
                    {"fact": "Pipeline is CPU bound, takes 4 hours", "type": "work", "importance": "high"},
                ],
            },
            {
                "session_id": 3,
                "turns": [
                    {"role": "user", "content": "Big news — I just accepted an offer at a startup in San Francisco! I'm moving next month. The new role is a senior data engineer position, and they're already using Rust for their core pipeline."},
                    {"role": "assistant", "content": "Congratulations Sarah! That sounds like a perfect fit — you'll get to work with Rust professionally, which will accelerate your learning tremendously. Senior data engineer at a Rust shop in SF is a great move. When do you start?"},
                    {"role": "user", "content": "I start March 15th. Also, they use Neovim as their standard editor — the whole team is very terminal-native. I'm going to switch from VS Code to Neovim to fit in. Already started configuring it."},
                    {"role": "assistant", "content": "That's a big editor switch but Neovim has excellent Rust support through rust-analyzer. Want help setting up your Neovim config for Rust development?"},
                    {"role": "user", "content": "Yes please. Also the weather thing is so nice — I am so done with New York winters."},
                ],
                "expected_memories_after": [
                    {"fact": "Accepted job at startup in San Francisco", "type": "location_update", "importance": "high", "contradicts": "Based in New York City"},
                    {"fact": "New role is senior data engineer", "type": "profession_update", "importance": "high"},
                    {"fact": "New company uses Rust for core pipeline", "type": "work", "importance": "high"},
                    {"fact": "Starts March 15th", "type": "temporal", "importance": "medium"},
                    {"fact": "Switching from VS Code to Neovim", "type": "tool_update", "importance": "medium", "contradicts": "Uses VS Code"},
                ],
            },
            {
                "session_id": 4,
                "turns": [
                    {"role": "user", "content": "Hey, I'm settling into SF. Can you help me write a Rust function to process Parquet files? I want to benchmark it against our Python version."},
                    {"role": "assistant", "content": "Of course! Since you're working with Parquet in Rust now, we should use the `arrow-rs` and `parquet` crates. What specific operation do you want to benchmark — the decompression, the aggregation, or the full pipeline?"},
                    {"role": "user", "content": "Let's start with reading and aggregating a single Parquet file. Sum a numeric column grouped by a string column."},
                ],
                "expected_memories_after": [],
            },
            {
                "session_id": 5,
                "turns": [
                    {"role": "user", "content": "Quick question — do you remember what editor I'm using these days?"},
                    {"role": "assistant", "content": "[MEMORY TEST]"},
                    {"role": "user", "content": "And where am I based now?"},
                    {"role": "assistant", "content": "[MEMORY TEST]"},
                    {"role": "user", "content": "What was the daily data volume I was dealing with at my old job?"},
                    {"role": "assistant", "content": "[MEMORY TEST]"},
                    {"role": "user", "content": "When I ask for help with coding problems, what kind of solutions do I usually want?"},
                    {"role": "assistant", "content": "[MEMORY TEST]"},
                    {"role": "user", "content": "Do you remember me complaining about the weather?"},
                    {"role": "assistant", "content": "[MEMORY TEST]"},
                ],
                "expected_memories_after": [],
            },
        ],
        "memory_tests": [
            {
                "test_id": "sarah_01_t1",
                "session": 5,
                "turn_index": 0,
                "query": "Quick question — do you remember what editor I'm using these days?",
                "required_memories": ["Switched from VS Code to Neovim"],
                "correct_answer": "You switched to Neovim — your new team in SF is very terminal-native.",
                "wrong_answer": "You use VS Code.",
                "category": "contradiction_update",
                "notes": "Must return updated editor, not original. Tests whether system updated or duplicated the memory.",
            },
            {
                "test_id": "sarah_01_t2",
                "session": 5,
                "turn_index": 2,
                "query": "And where am I based now?",
                "required_memories": ["Moved from NYC to San Francisco"],
                "correct_answer": "You're in San Francisco now — you moved from NYC for the new senior data engineer role at the startup.",
                "wrong_answer": "You're based in New York City.",
                "category": "contradiction_update",
                "notes": "Must return SF, not NYC. Critical contradiction test.",
            },
            {
                "test_id": "sarah_01_t3",
                "session": 5,
                "turn_index": 4,
                "query": "What was the daily data volume I was dealing with at my old job?",
                "required_memories": ["Processes 2TB Parquet files daily", "Pipeline takes 4 hours"],
                "correct_answer": "At your old job, you were processing about 2TB of Parquet files daily, with the Python pipeline taking about 4 hours.",
                "wrong_answer": "I don't recall the specifics of your data volume.",
                "category": "simple_recall",
                "notes": "Straightforward fact recall from session 2.",
            },
            {
                "test_id": "sarah_01_t4",
                "session": 5,
                "turn_index": 6,
                "query": "When I ask for help with coding problems, what kind of solutions do I usually want?",
                "required_memories": ["Works on data pipelines", "Learning Rust for performance", "Interested in PyO3 for Python-Rust bridge", "Wants to benchmark Rust vs Python"],
                "correct_answer": "You're very performance-focused and practical. You want solutions that directly address bottlenecks — like using PyO3 to bridge Rust and Python, or benchmarking Rust against your existing pipeline. You're not interested in theoretical exercises, you want real speedups.",
                "wrong_answer": "I'll provide clear and well-documented solutions.",
                "category": "implicit_preference",
                "notes": "Sarah never says 'I prefer practical solutions' but every session demonstrates this: PyO3 for bottlenecks, benchmarking, real pipeline work.",
            },
            {
                "test_id": "sarah_01_t5",
                "session": 5,
                "turn_index": 8,
                "query": "Do you remember me complaining about the weather?",
                "required_memories": [],
                "correct_answer": "I don't remember",
                "wrong_answer": "Yes, you said the weather in SF is so much nicer and you were done with New York winters.",
                "category": "noise_resistance",
                "notes": "Weather complaint is noise — should not be stored.",
            },
        ],
    },


    # =========================================================================
    # Profile 2: Marcus Williams - Data Scientist
    # Tests: implicit_preference, noise_resistance, simple_recall
    # =========================================================================
    {
        "user_id": "marcus_02",
        "name": "Marcus Williams",
        "description": "Data scientist who always asks for visual explanations and has a dog named Max",
        "sessions": [
            {
                "session_id": 1,
                "turns": [
                    {"role": "user", "content": "Hi, I'm Marcus. I'm a data scientist at a biotech company working on drug discovery. I mostly use PyTorch for my deep learning models."},
                    {"role": "assistant", "content": "Welcome Marcus! Drug discovery with deep learning is fascinating. Are you working on molecular property prediction, drug-target interaction, or something else?"},
                    {"role": "user", "content": "Molecular property prediction mainly. Can you explain how graph neural networks work? Maybe draw it out or give me a visual analogy?"},
                    {"role": "assistant", "content": "Sure! Think of a molecule as a social network... [detailed visual explanation]"},
                    {"role": "user", "content": "That visual really helps. I'm very much a visual learner. Oh also, sorry I need to step away — my dog Max needs his walk. He gets antsy around 3pm every day."},
                ],
                "expected_memories_after": [
                    {"fact": "Name is Marcus Williams", "type": "identity", "importance": "high"},
                    {"fact": "Data scientist at biotech company", "type": "profession", "importance": "high"},
                    {"fact": "Works on drug discovery", "type": "work", "importance": "high"},
                    {"fact": "Uses PyTorch", "type": "tool", "importance": "high"},
                    {"fact": "Works on molecular property prediction", "type": "work", "importance": "high"},
                    {"fact": "Visual learner, prefers visual explanations", "type": "preference", "importance": "high"},
                    {"fact": "Has a dog named Max", "type": "personal", "importance": "low"},
                ],
            },
            {
                "session_id": 2,
                "turns": [
                    {"role": "user", "content": "Back! So I tried implementing a GNN in PyTorch Geometric but I'm confused about the message passing. Can you show me with a diagram or step-by-step visual?"},
                    {"role": "assistant", "content": "Absolutely! Let me walk through it visually... [step-by-step visual explanation of message passing]"},
                    {"role": "user", "content": "Perfect, that picture makes it click. By the way, had a rough commute today — raining all day here in Boston. Took the T and it was delayed 20 minutes."},
                    {"role": "assistant", "content": "The T delays in rain are the worst! At least the GNN concepts are clicking though. Want to walk through the code implementation now?"},
                    {"role": "user", "content": "Yeah, but can you annotate the code with comments that explain what each section does visually? Like 'this part does the neighbor aggregation we drew above.'"},
                ],
                "expected_memories_after": [
                    {"fact": "Using PyTorch Geometric for GNN implementation", "type": "tool", "importance": "medium"},
                    {"fact": "Based in Boston", "type": "location", "importance": "medium"},
                    {"fact": "Commutes via the T (MBTA)", "type": "personal", "importance": "low"},
                    {"fact": "Prefers annotated code with visual references", "type": "preference", "importance": "high"},
                ],
            },
            {
                "session_id": 3,
                "turns": [
                    {"role": "user", "content": "Can you help me understand attention mechanisms? I want to add attention to my GNN. A diagram would be super helpful."},
                    {"role": "assistant", "content": "Let me draw out how attention works in the context of your GNN... [visual explanation]"},
                    {"role": "user", "content": "Awesome. I had a great lunch at this new Thai place near my office today. The pad see ew was incredible. Anyway, back to attention — how does multi-head attention differ?"},
                    {"role": "assistant", "content": "Nice, good Thai food is underrated! For multi-head attention, think of it visually like this... [visual explanation with multiple parallel attention heads]"},
                    {"role": "user", "content": "Can you draw the comparison between single-head and multi-head side by side?"},
                ],
                "expected_memories_after": [
                    {"fact": "Adding attention mechanisms to GNN", "type": "work", "importance": "medium"},
                ],
            },
            {
                "session_id": 4,
                "turns": [
                    {"role": "user", "content": "I'm writing a paper now on my attention-based GNN for molecular property prediction. Can you help me write the methodology section?"},
                    {"role": "assistant", "content": "Of course! Let me help structure the methodology. What results have you gotten so far?"},
                    {"role": "user", "content": "We're getting 0.92 AUROC on the Tox21 dataset, which beats the previous SOTA of 0.89. My advisor Dr. Patel is excited."},
                ],
                "expected_memories_after": [
                    {"fact": "Writing paper on attention-based GNN", "type": "work", "importance": "high"},
                    {"fact": "0.92 AUROC on Tox21 (SOTA was 0.89)", "type": "results", "importance": "high"},
                    {"fact": "Advisor is Dr. Patel", "type": "work", "importance": "medium"},
                ],
            },
            {
                "session_id": 5,
                "turns": [
                    {"role": "user", "content": "Hey, I need you to explain something to me. How should you explain things to me?"},
                    {"role": "assistant", "content": "[MEMORY TEST]"},
                    {"role": "user", "content": "What framework am I using for my deep learning work?"},
                    {"role": "assistant", "content": "[MEMORY TEST]"},
                    {"role": "user", "content": "Where did I eat lunch a while back? The Thai place?"},
                    {"role": "assistant", "content": "[MEMORY TEST]"},
                ],
                "expected_memories_after": [],
            },
        ],
        "memory_tests": [
            {
                "test_id": "marcus_02_t1",
                "session": 5,
                "turn_index": 0,
                "query": "Hey, I need you to explain something to me. How should you explain things to me?",
                "required_memories": ["Visual learner", "Prefers diagrams and visual analogies"],
                "correct_answer": "You're a visual learner — you prefer diagrams, visual analogies, and annotated code with visual references.",
                "wrong_answer": "I'll explain things clearly and concisely.",
                "category": "implicit_preference",
                "notes": "Marcus explicitly said he's a visual learner once, but also demonstrated it across every session by always asking for diagrams. System should have strong signal.",
            },
            {
                "test_id": "marcus_02_t2",
                "session": 5,
                "turn_index": 2,
                "query": "What framework am I using for my deep learning work?",
                "required_memories": ["Uses PyTorch", "PyTorch Geometric for GNNs"],
                "correct_answer": "You use PyTorch, specifically PyTorch Geometric for your GNN work on molecular property prediction.",
                "wrong_answer": "I'm not sure which framework you use.",
                "category": "simple_recall",
                "notes": "Basic fact recall.",
            },
            {
                "test_id": "marcus_02_t3",
                "session": 5,
                "turn_index": 4,
                "query": "Where did I eat lunch a while back? The Thai place?",
                "required_memories": [],
                "correct_answer": "I don't have specific details about that stored — you mentioned a Thai place near your office with great pad see ew, but that's not the kind of thing I focus on remembering.",
                "wrong_answer": "You had pad see ew at a Thai place near your office in Boston.",
                "category": "noise_resistance",
                "notes": "This is NOISE — a good memory system should NOT store random lunch details. If the system stored this, it's over-extracting. The correct behavior is to NOT have this in memory.",
            },
        ],
    },

    # =========================================================================
    # Profile 3: Priya Sharma - Product Manager learning to code
    # Tests: temporal_relevance, cross_session, consolidation
    # =========================================================================
    {
        "user_id": "priya_03",
        "name": "Priya Sharma",
        "description": "PM learning to code, has evolving project with changing deadlines",
        "sessions": [
            {
                "session_id": 1,
                "turns": [
                    {"role": "user", "content": "Hi! I'm Priya, a product manager at a fintech startup. I'm trying to learn Python to better communicate with my engineering team. Total beginner here."},
                    {"role": "assistant", "content": "Welcome Priya! That's a great goal. Understanding code will definitely help you collaborate with engineers. Where would you like to start?"},
                    {"role": "user", "content": "I think basic data analysis would be most useful for my role. I deal with a lot of metrics and currently rely on my data team for everything. I use Excel for now. I'd love to be able to do it myself in Python."},
                    {"role": "assistant", "content": "Perfect — pandas and matplotlib are your friends. Want to start by converting one of your Excel workflows to Python?"},
                    {"role": "user", "content": "Yes! I have a big board meeting on January 30th and I need to present our growth metrics. Would be cool if I could do the analysis in Python by then."},
                ],
                "expected_memories_after": [
                    {"fact": "Name is Priya Sharma", "type": "identity", "importance": "high"},
                    {"fact": "Product manager at fintech startup", "type": "profession", "importance": "high"},
                    {"fact": "Learning Python as a beginner", "type": "goal", "importance": "high"},
                    {"fact": "Wants to learn data analysis with Python", "type": "goal", "importance": "high"},
                    {"fact": "Currently uses Excel", "type": "tool", "importance": "medium"},
                    {"fact": "Board meeting January 30th for growth metrics", "type": "temporal", "importance": "medium"},
                ],
            },
            {
                "session_id": 2,
                "turns": [
                    {"role": "user", "content": "I've been practicing pandas! I managed to load a CSV and do a groupby. Small wins! My team was impressed when I showed them."},
                    {"role": "assistant", "content": "That's fantastic progress! groupby is one of the most useful pandas operations. What do you want to tackle next?"},
                    {"role": "user", "content": "I want to make charts. My CEO loves visual dashboards. Can we do matplotlib?"},
                    {"role": "assistant", "content": "Absolutely. For dashboards, you might also like plotly — it creates interactive charts. But matplotlib is a great foundation. Want to start with a line chart of your growth metrics?"},
                    {"role": "user", "content": "Let's do plotly actually, interactive sounds perfect for the board meeting."},
                ],
                "expected_memories_after": [
                    {"fact": "Learning pandas, can do groupby", "type": "skill", "importance": "medium"},
                    {"fact": "CEO likes visual dashboards", "type": "work", "importance": "medium"},
                    {"fact": "Chose plotly over matplotlib for interactivity", "type": "tool", "importance": "medium"},
                ],
            },
            {
                "session_id": 3,
                "turns": [
                    {"role": "user", "content": "Update — the board meeting got pushed to February 15th. Also my CTO asked me to learn SQL too since we're migrating our data warehouse. So I need to balance Python and SQL learning now."},
                    {"role": "assistant", "content": "Good that you have more time! SQL is very complementary to Python — you can use SQL to query the warehouse and Python/pandas to analyze the results. Want to start SQL basics?"},
                    {"role": "user", "content": "Yes. Also I got promoted to Senior PM! More responsibilities but also more reason to be technical."},
                    {"role": "assistant", "content": "Congratulations on the promotion! That's well-deserved. The technical skills will be even more valuable as a Senior PM."},
                    {"role": "user", "content": "Thanks! We're also switching from Postgres to BigQuery for the warehouse migration."},
                ],
                "expected_memories_after": [
                    {"fact": "Board meeting moved to February 15th", "type": "temporal_update", "importance": "medium", "contradicts": "Board meeting January 30th"},
                    {"fact": "Now also learning SQL", "type": "goal", "importance": "high"},
                    {"fact": "Company migrating data warehouse", "type": "work", "importance": "medium"},
                    {"fact": "Promoted to Senior PM", "type": "profession_update", "importance": "high"},
                    {"fact": "Migrating from Postgres to BigQuery", "type": "work", "importance": "medium"},
                ],
            },
            {
                "session_id": 4,
                "turns": [
                    {"role": "user", "content": "The board meeting went great! My plotly dashboard was a hit. Now I want to build something more ambitious — an internal tool that queries BigQuery and shows real-time metrics."},
                    {"role": "assistant", "content": "That's a great next step! You could use Streamlit or Dash to build that. It would combine your Python, SQL, and visualization skills. Which would you prefer?"},
                    {"role": "user", "content": "Which one is easier for someone at my level?"},
                ],
                "expected_memories_after": [
                    {"fact": "Board meeting went well, plotly dashboard was successful", "type": "outcome", "importance": "medium"},
                    {"fact": "Building internal BigQuery metrics tool", "type": "goal", "importance": "high"},
                ],
            },
            {
                "session_id": 5,
                "turns": [
                    {"role": "user", "content": "What's my current role at the company?"},
                    {"role": "assistant", "content": "[MEMORY TEST]"},
                    {"role": "user", "content": "What database system is my company using for their data warehouse now?"},
                    {"role": "assistant", "content": "[MEMORY TEST]"},
                    {"role": "user", "content": "Can you summarize my overall learning journey with programming so far?"},
                    {"role": "assistant", "content": "[MEMORY TEST]"},
                    {"role": "user", "content": "Is the board meeting still coming up?"},
                    {"role": "assistant", "content": "[MEMORY TEST]"},
                ],
                "expected_memories_after": [],
            },
        ],
        "memory_tests": [
            {
                "test_id": "priya_03_t1",
                "session": 5,
                "turn_index": 0,
                "query": "What's my current role at the company?",
                "required_memories": ["Promoted to Senior PM"],
                "correct_answer": "You're a Senior PM at a fintech startup — you got promoted from PM.",
                "wrong_answer": "You're a product manager at a fintech startup.",
                "category": "contradiction_update",
                "notes": "Must reflect the promotion, not the original title.",
            },
            {
                "test_id": "priya_03_t2",
                "session": 5,
                "turn_index": 2,
                "query": "What database system is my company using for their data warehouse now?",
                "required_memories": ["Migrating from Postgres to BigQuery"],
                "correct_answer": "Your company migrated to BigQuery from Postgres.",
                "wrong_answer": "You use Postgres.",
                "category": "contradiction_update",
                "notes": "Must reflect migration to BigQuery.",
            },
            {
                "test_id": "priya_03_t3",
                "session": 5,
                "turn_index": 4,
                "query": "Can you summarize my overall learning journey with programming so far?",
                "required_memories": [
                    "Started as total beginner",
                    "Learned pandas and groupby",
                    "Learned plotly for dashboards",
                    "Board meeting dashboard was a hit",
                    "Also learning SQL",
                    "Now building internal BigQuery metrics tool",
                ],
                "correct_answer": "You started as a total Python beginner wanting to do data analysis. You learned pandas (groupby, data loading), then picked up plotly for interactive dashboards. Your board meeting dashboard was a hit. You also started learning SQL when your company migrated to BigQuery. Now you're building an internal metrics tool combining all those skills.",
                "wrong_answer": "You're learning Python.",
                "category": "cross_session",
                "notes": "Requires synthesizing information from all 4 prior sessions into a coherent narrative. Tests consolidation ability.",
            },
            {
                "test_id": "priya_03_t4",
                "session": 5,
                "turn_index": 6,
                "query": "Is the board meeting still coming up?",
                "required_memories": ["Board meeting already happened", "Plotly dashboard was a hit"],
                "correct_answer": "No, the board meeting already happened! Your plotly dashboard was a hit. You're now working on building an internal BigQuery metrics tool.",
                "wrong_answer": "Yes, your board meeting is on February 15th.",
                "category": "temporal_relevance",
                "notes": "Board meeting deadline passed. Must recognize the event already occurred.",
            },
        ],
    },

    # =========================================================================
    # Profile 4: James Park - ML Student
    # Tests: consolidation, simple_recall, temporal_relevance
    # =========================================================================
    {
        "user_id": "james_04",
        "name": "James Park",
        "description": "MS student working on NLP thesis with evolving research direction",
        "sessions": [
            {
                "session_id": 1,
                "turns": [
                    {"role": "user", "content": "Hey, I'm James. I'm an MS student in CS at University of Washington. Working on my thesis in NLP — specifically sentiment analysis on financial text."},
                    {"role": "assistant", "content": "Interesting topic James! Financial sentiment analysis has some unique challenges compared to general sentiment. Are you working with specific datasets like Financial PhraseBank, or building your own?"},
                    {"role": "user", "content": "Financial PhraseBank plus some SEC filings I scraped myself. My advisor is Prof. Lisa Zhang. She wants me to focus on the aspect-based approach."},
                    {"role": "assistant", "content": "Aspect-based sentiment analysis on financial text is a great direction — it captures the nuance of documents where different aspects of a company might have different sentiments. What model are you using as your base?"},
                    {"role": "user", "content": "I'm starting with FinBERT and then comparing against a fine-tuned Llama 2 7B."},
                ],
                "expected_memories_after": [
                    {"fact": "Name is James Park", "type": "identity", "importance": "high"},
                    {"fact": "MS student in CS at University of Washington", "type": "education", "importance": "high"},
                    {"fact": "Thesis on aspect-based sentiment analysis on financial text", "type": "work", "importance": "high"},
                    {"fact": "Advisor is Prof. Lisa Zhang", "type": "work", "importance": "high"},
                    {"fact": "Using Financial PhraseBank + scraped SEC filings", "type": "work", "importance": "high"},
                    {"fact": "Comparing FinBERT vs fine-tuned Llama 2 7B", "type": "work", "importance": "high"},
                ],
            },
            {
                "session_id": 2,
                "turns": [
                    {"role": "user", "content": "So FinBERT is doing okay but the Llama results are much better. 0.87 F1 vs 0.79 for FinBERT on aspect-level sentiment."},
                    {"role": "assistant", "content": "That's a significant gap! The Llama model's larger capacity probably helps with the nuanced aspect-level distinctions. Are you planning to do an error analysis to understand where FinBERT fails?"},
                    {"role": "user", "content": "Yeah, Prof. Zhang wants error analysis. Also I have a paper deadline for ACL on March 1st. Need to hustle."},
                    {"role": "assistant", "content": "March 1st for ACL is tight. Let me help you prioritize — error analysis plus writing. What sections do you still need to write?"},
                    {"role": "user", "content": "Everything except related work. Also I'm TAing for the intro NLP class this quarter, which is eating into my research time."},
                ],
                "expected_memories_after": [
                    {"fact": "Llama 2 outperforming FinBERT: 0.87 vs 0.79 F1", "type": "results", "importance": "high"},
                    {"fact": "ACL paper deadline March 1st", "type": "temporal", "importance": "medium"},
                    {"fact": "TAing intro NLP class this quarter", "type": "work", "importance": "low"},
                ],
            },
            {
                "session_id": 3,
                "turns": [
                    {"role": "user", "content": "Change of plans — Prof. Zhang thinks we should pivot from ACL to EMNLP instead. Deadline is June 15th. She wants us to add a cross-lingual component since she got a new grant for multilingual NLP."},
                    {"role": "assistant", "content": "That actually gives you more time and a stronger story. Cross-lingual financial sentiment analysis is less crowded than English-only. Which languages are you thinking?"},
                    {"role": "user", "content": "Chinese and Japanese financial text. Prof. Zhang has collaborators at Tsinghua who can help with the Chinese data. Also I finished TAing — that class is done now."},
                    {"role": "assistant", "content": "Great that you have the TA load off. Chinese and Japanese financial text adds real novelty. The Tsinghua collaboration strengthens the paper too. Want to start planning the cross-lingual experiments?"},
                    {"role": "user", "content": "Yes. Also I'm thinking of adding Llama 3 to the comparison since it just came out. Might replace the Llama 2 experiments entirely."},
                ],
                "expected_memories_after": [
                    {"fact": "Pivoted from ACL to EMNLP, deadline June 15th", "type": "temporal_update", "importance": "high", "contradicts": "ACL paper deadline March 1st"},
                    {"fact": "Adding cross-lingual component: Chinese and Japanese", "type": "work", "importance": "high"},
                    {"fact": "Collaborators at Tsinghua for Chinese data", "type": "work", "importance": "medium"},
                    {"fact": "Done with TAing", "type": "temporal_update", "importance": "low", "contradicts": "TAing intro NLP class"},
                    {"fact": "Considering Llama 3 to replace Llama 2 experiments", "type": "work", "importance": "medium"},
                ],
            },
            {
                "session_id": 4,
                "turns": [
                    {"role": "user", "content": "Llama 3 results are in — 0.91 F1 on English, 0.84 on Chinese, 0.82 on Japanese. FinBERT stays at 0.79 English only obviously. Prof. Zhang is thrilled."},
                    {"role": "assistant", "content": "Those are excellent results! The cross-lingual performance is particularly impressive. The 0.91 on English is a nice bump from the 0.87 with Llama 2 as well. Ready to start writing the EMNLP paper?"},
                    {"role": "user", "content": "Yes, let's outline the paper. I want to really emphasize the cross-lingual aspect since that's the novel contribution."},
                ],
                "expected_memories_after": [
                    {"fact": "Llama 3 results: 0.91 English, 0.84 Chinese, 0.82 Japanese F1", "type": "results", "importance": "high"},
                ],
            },
            {
                "session_id": 5,
                "turns": [
                    {"role": "user", "content": "What conference am I submitting to and when is the deadline?"},
                    {"role": "assistant", "content": "[MEMORY TEST]"},
                    {"role": "user", "content": "What are my best model results across languages?"},
                    {"role": "assistant", "content": "[MEMORY TEST]"},
                    {"role": "user", "content": "Am I still TAing?"},
                    {"role": "assistant", "content": "[MEMORY TEST]"},
                ],
                "expected_memories_after": [],
            },
        ],
        "memory_tests": [
            {
                "test_id": "james_04_t1",
                "session": 5,
                "turn_index": 0,
                "query": "What conference am I submitting to and when is the deadline?",
                "required_memories": ["Pivoted to EMNLP, deadline June 15th"],
                "correct_answer": "You're submitting to EMNLP with a June 15th deadline. You originally planned ACL but pivoted to EMNLP to include the cross-lingual component.",
                "wrong_answer": "You're submitting to ACL with a March 1st deadline.",
                "category": "contradiction_update",
                "notes": "Must return EMNLP, not ACL.",
            },
            {
                "test_id": "james_04_t2",
                "session": 5,
                "turn_index": 2,
                "query": "What are my best model results across languages?",
                "required_memories": ["Llama 3: 0.91 English, 0.84 Chinese, 0.82 Japanese"],
                "correct_answer": "Your best results are with Llama 3: 0.91 F1 on English, 0.84 on Chinese, and 0.82 on Japanese. FinBERT was 0.79 on English only.",
                "wrong_answer": "Llama 2 got 0.87 F1 and FinBERT got 0.79.",
                "category": "consolidation",
                "notes": "Must consolidate: earlier Llama 2 results (0.87) should be superseded by Llama 3 results (0.91). Should not confuse the two.",
            },
            {
                "test_id": "james_04_t3",
                "session": 5,
                "turn_index": 4,
                "query": "Am I still TAing?",
                "required_memories": ["Done with TAing"],
                "correct_answer": "No, you finished TAing. That class is done.",
                "wrong_answer": "Yes, you're TAing the intro NLP class this quarter.",
                "category": "temporal_relevance",
                "notes": "Must recognize the TA role ended. Tests temporal awareness.",
            },
        ],
    },

    # =========================================================================
    # Profile 5: Aisha Okafor - Startup Founder
    # Tests: cross_session, noise_resistance, simple_recall
    # =========================================================================
    {
        "user_id": "aisha_05",
        "name": "Aisha Okafor",
        "description": "Startup founder building a health tech app, going through funding rounds",
        "sessions": [
            {
                "session_id": 1,
                "turns": [
                    {"role": "user", "content": "Hi, I'm Aisha. I'm the CEO of HealthPulse — we're building an AI-powered health monitoring app. We just closed our seed round, $2M from Sequoia Scout."},
                    {"role": "assistant", "content": "Congratulations on the seed round, Aisha! Sequoia Scout is a great signal. What stage is the product at? Are you pre-launch or already in market?"},
                    {"role": "user", "content": "Pre-launch. We have an MVP with about 500 beta users. Our tech stack is React Native for mobile, Python/FastAPI backend, and we're running our ML models on AWS SageMaker."},
                    {"role": "assistant", "content": "Solid stack. 500 beta users is a good starting point. What's the core ML capability — is it predictive health monitoring, anomaly detection, or something else?"},
                    {"role": "user", "content": "Anomaly detection on wearable data — we integrate with Apple Watch and Fitbit. We detect irregular heart rhythms and sleep pattern anomalies. Our team is 8 people total: 4 engineers, 1 ML researcher, myself, a designer, and a head of ops."},
                ],
                "expected_memories_after": [
                    {"fact": "Aisha Okafor, CEO of HealthPulse", "type": "identity", "importance": "high"},
                    {"fact": "AI-powered health monitoring app", "type": "work", "importance": "high"},
                    {"fact": "Seed round: $2M from Sequoia Scout", "type": "business", "importance": "high"},
                    {"fact": "Pre-launch, 500 beta users", "type": "business", "importance": "high"},
                    {"fact": "Stack: React Native, Python/FastAPI, AWS SageMaker", "type": "technical", "importance": "high"},
                    {"fact": "Anomaly detection on wearable data (Apple Watch, Fitbit)", "type": "product", "importance": "high"},
                    {"fact": "Detects irregular heart rhythms and sleep anomalies", "type": "product", "importance": "high"},
                    {"fact": "Team of 8: 4 engineers, 1 ML, CEO, designer, head of ops", "type": "business", "importance": "medium"},
                ],
            },
            {
                "session_id": 2,
                "turns": [
                    {"role": "user", "content": "We hit 2000 beta users! But we're having scaling issues — the SageMaker inference is too slow for real-time anomaly detection. Getting 800ms latency when we need under 200ms."},
                    {"role": "assistant", "content": "That's great growth! For the latency issue, a few options: model distillation to a smaller model, switching to SageMaker real-time endpoints with auto-scaling, or moving to edge inference on the device itself. What's your model size?"},
                    {"role": "user", "content": "About 150M parameters. Edge inference is interesting but our ML researcher thinks the model is too big for on-device. We're thinking about distillation. Also I had the worst flight back from a board meeting in SF today — 5 hour delay."},
                    {"role": "assistant", "content": "Ugh, flight delays are the worst. For distillation, you could probably get down to 20-30M params without significant accuracy loss for anomaly detection. Want to plan the distillation approach?"},
                    {"role": "user", "content": "Yes. Also we need to start thinking about HIPAA compliance. Our lawyer said we need to be compliant before our public launch."},
                ],
                "expected_memories_after": [
                    {"fact": "Grew to 2000 beta users", "type": "business", "importance": "high"},
                    {"fact": "Latency issue: 800ms, need under 200ms", "type": "technical", "importance": "high"},
                    {"fact": "Model is 150M parameters", "type": "technical", "importance": "medium"},
                    {"fact": "Planning model distillation", "type": "technical", "importance": "high"},
                    {"fact": "Need HIPAA compliance before public launch", "type": "business", "importance": "high"},
                ],
            },
            {
                "session_id": 3,
                "turns": [
                    {"role": "user", "content": "Distillation worked! Got the model down to 25M params, latency is 150ms now. Also we just started our Series A process — targeting $10M."},
                    {"role": "assistant", "content": "Excellent results on both fronts! 150ms is well under your target. And Series A at this stage makes sense with your growth. Who's leading the round discussions?"},
                    {"role": "user", "content": "Talking to a]16z and General Catalyst. We've also grown to 10,000 beta users and our retention rate is 85% monthly. I hired 3 more engineers too, so we're at 11 people now."},
                    {"role": "assistant", "content": "85% monthly retention on a health app is exceptional. That plus 10K users and the distillation win gives you a strong Series A story. How are the a16z and GC conversations going?"},
                    {"role": "user", "content": "Good! a16z seems more excited. They have a bio fund that's interested. Oh and we got FDA breakthrough device designation for our heart rhythm detection."},
                ],
                "expected_memories_after": [
                    {"fact": "Distilled model to 25M params, 150ms latency", "type": "technical", "importance": "high"},
                    {"fact": "Series A process: targeting $10M, talking to a16z and General Catalyst", "type": "business", "importance": "high"},
                    {"fact": "10,000 beta users, 85% monthly retention", "type": "business", "importance": "high"},
                    {"fact": "Team grew to 11 people", "type": "business", "importance": "medium", "contradicts": "Team of 8"},
                    {"fact": "FDA breakthrough device designation for heart rhythm detection", "type": "business", "importance": "high"},
                ],
            },
            {
                "session_id": 4,
                "turns": [
                    {"role": "user", "content": "We closed Series A! $12M from a16z Bio. We're launching publicly next month. I need help planning the technical architecture for scale — we're expecting 100K users in the first quarter."},
                    {"role": "assistant", "content": "Congratulations! $12M from a16z Bio is a strong vote of confidence. For 100K users, we need to think about infrastructure scaling, monitoring, and reliability. Let's plan this out."},
                    {"role": "user", "content": "Yes. Our current architecture handles 10K but we need to 10x it. What should we focus on?"},
                ],
                "expected_memories_after": [
                    {"fact": "Closed Series A: $12M from a16z Bio", "type": "business", "importance": "high"},
                    {"fact": "Public launch next month, expecting 100K users in Q1", "type": "business", "importance": "high"},
                ],
            },
            {
                "session_id": 5,
                "turns": [
                    {"role": "user", "content": "What's our current funding situation?"},
                    {"role": "assistant", "content": "[MEMORY TEST]"},
                    {"role": "user", "content": "How did we solve the latency problem?"},
                    {"role": "assistant", "content": "[MEMORY TEST]"},
                    {"role": "user", "content": "What was the flight delay about?"},
                    {"role": "assistant", "content": "[MEMORY TEST]"},
                    {"role": "user", "content": "Have we launched publicly yet or are we still in beta?"},
                    {"role": "assistant", "content": "[MEMORY TEST]"},
                ],
                "expected_memories_after": [],
            },
        ],
        "memory_tests": [
            {
                "test_id": "aisha_05_t1",
                "session": 5,
                "turn_index": 0,
                "query": "What's our current funding situation?",
                "required_memories": ["Seed: $2M Sequoia Scout", "Series A: $12M a16z Bio"],
                "correct_answer": "HealthPulse has raised a total of $14M: a $2M seed from Sequoia Scout and a $12M Series A from a16z Bio.",
                "wrong_answer": "You raised a $2M seed round from Sequoia Scout.",
                "category": "cross_session",
                "notes": "Must combine funding info from session 1 (seed) and session 4 (Series A). Tests cross-session synthesis.",
            },
            {
                "test_id": "aisha_05_t2",
                "session": 5,
                "turn_index": 2,
                "query": "How did we solve the latency problem?",
                "required_memories": ["800ms latency problem", "Model distillation to 25M params", "Achieved 150ms latency"],
                "correct_answer": "You distilled your 150M parameter model down to 25M parameters, which reduced inference latency from 800ms to 150ms — well under your 200ms target.",
                "wrong_answer": "I don't recall the details of your latency optimization.",
                "category": "cross_session",
                "notes": "Must connect the problem (session 2) with the solution (session 3).",
            },
            {
                "test_id": "aisha_05_t3",
                "session": 5,
                "turn_index": 4,
                "query": "What was the flight delay about?",
                "required_memories": [],
                "correct_answer": "I don't have that stored — that was just a passing mention of travel frustration, not something important to remember.",
                "wrong_answer": "You had a 5 hour flight delay coming back from a board meeting in SF.",
                "category": "noise_resistance",
                "notes": "Flight delay is pure noise. A good system should not store this.",
            },
            {
                "test_id": "aisha_05_t4",
                "session": 5,
                "turn_index": 6,
                "query": "Have we launched publicly yet or are we still in beta?",
                "required_memories": ["Public launch next month after Series A", "Expecting 100K users in Q1"],
                "correct_answer": "You're launching publicly — you closed your $12M Series A from a16z Bio and are expecting 100K users in the first quarter. The beta phase with 10K users is behind you.",
                "wrong_answer": "You're still in beta with about 2000 users.",
                "category": "temporal_relevance",
                "notes": "Must recognize progression from pre-launch/beta to public launch.",
            },
        ],
    },

    # =========================================================================
    # Profile 6: Chen Wei - NLP Researcher
    # Tests: consolidation, cross_session, contradiction_update
    # =========================================================================
    {
        "user_id": "chen_06",
        "name": "Chen Wei",
        "description": "PhD researcher working on multilingual LLMs with changing experimental results",
        "sessions": [
            {
                "session_id": 1,
                "turns": [
                    {"role": "user", "content": "Hi, I'm Chen. I'm a 3rd year PhD at MIT CSAIL working on efficient multilingual language models. My advisor is Prof. Michael Chen (no relation despite the last name)."},
                    {"role": "assistant", "content": "Welcome Chen! Efficient multilingual LMs is a hot area. What's your specific angle — is it architecture efficiency, training efficiency, or inference efficiency?"},
                    {"role": "user", "content": "Architecture efficiency. I'm exploring sparse mixture-of-experts (MoE) approaches where different experts specialize in different language families. The hypothesis is that you can get multilingual capability without the full parameter cost."},
                    {"role": "assistant", "content": "That's a compelling approach. So language-family-specific routing? Like one expert for Romance languages, one for Sino-Tibetan, etc.? What scale are you working at?"},
                    {"role": "user", "content": "Exactly. I'm training at 1B parameter scale with 8 experts. Currently supporting 20 languages. Using the CC-100 dataset for training."},
                ],
                "expected_memories_after": [
                    {"fact": "Chen Wei, 3rd year PhD at MIT CSAIL", "type": "identity", "importance": "high"},
                    {"fact": "Advisor is Prof. Michael Chen", "type": "work", "importance": "high"},
                    {"fact": "Research on efficient multilingual LLMs using sparse MoE", "type": "work", "importance": "high"},
                    {"fact": "Language-family-specific expert routing", "type": "work", "importance": "high"},
                    {"fact": "1B parameters, 8 experts, 20 languages, CC-100 dataset", "type": "work", "importance": "high"},
                ],
            },
            {
                "session_id": 2,
                "turns": [
                    {"role": "user", "content": "Initial results are in. My MoE model gets 0.72 average across languages on XNLI, which is below the dense baseline of 0.76. The routing isn't working as expected — experts aren't specializing by language family."},
                    {"role": "assistant", "content": "That's a common challenge with MoE — the router can converge to solutions that don't align with human intuitions about language groupings. Have you looked at the actual routing patterns to see what it's doing?"},
                    {"role": "user", "content": "Yeah, it's routing mostly by input length and formatting rather than language. I think I need auxiliary losses to encourage language-family specialization."},
                    {"role": "assistant", "content": "That makes sense. You could add a language-family classification loss on the router outputs, or use a load-balancing loss that's computed per-language-family. Want to design these losses together?"},
                    {"role": "user", "content": "Yes please. Also I've been collaborating with a group at Tsinghua on Chinese evaluation. They have better benchmarks than what's publicly available."},
                ],
                "expected_memories_after": [
                    {"fact": "MoE getting 0.72 XNLI vs 0.76 dense baseline", "type": "results", "importance": "high"},
                    {"fact": "Router not specializing by language family as intended", "type": "results", "importance": "high"},
                    {"fact": "Exploring auxiliary losses for language-family routing", "type": "work", "importance": "high"},
                    {"fact": "Collaborating with Tsinghua on Chinese evaluation", "type": "work", "importance": "medium"},
                ],
            },
            {
                "session_id": 3,
                "turns": [
                    {"role": "user", "content": "Big breakthrough! The auxiliary loss worked. MoE now gets 0.81 average XNLI, beating the dense baseline of 0.76. And we're using only 40% of parameters per forward pass. The paper is coming together."},
                    {"role": "assistant", "content": "That's a major result — 0.81 vs 0.76 with 40% parameter usage is a clear efficiency win. This is very publishable. Where are you thinking of submitting?"},
                    {"role": "user", "content": "We're targeting NeurIPS. Prof. Chen thinks it's strong enough. Also I expanded to 50 languages and 16 experts. The scaling behavior is really interesting."},
                    {"role": "assistant", "content": "Expanding the scale strengthens the story. What are the scaling trends — does the advantage increase with more languages/experts?"},
                    {"role": "user", "content": "Yes, the gap widens. At 50 languages and 16 experts, MoE gets 0.83 vs dense 0.77. The efficiency gain also increases — only 30% parameters per pass. I think we have a real contribution here."},
                ],
                "expected_memories_after": [
                    {"fact": "Auxiliary loss breakthrough: MoE now 0.81 XNLI (was 0.72), beats dense 0.76, 40% params", "type": "results_update", "importance": "high", "contradicts": "MoE getting 0.72 XNLI"},
                    {"fact": "Targeting NeurIPS", "type": "work", "importance": "high"},
                    {"fact": "Expanded to 50 languages, 16 experts", "type": "work", "importance": "high", "contradicts": "20 languages, 8 experts"},
                    {"fact": "At 50 langs/16 experts: MoE 0.83 vs dense 0.77, 30% params", "type": "results", "importance": "high"},
                ],
            },
            {
                "session_id": 4,
                "turns": [
                    {"role": "user", "content": "Reviewer feedback from NeurIPS came back — we got a borderline score. Reviewers want ablation studies on the auxiliary loss and comparison with recent GShard and Switch Transformer baselines."},
                    {"role": "assistant", "content": "Borderline is salvageable with a strong rebuttal! The ablation study and baselines are reasonable requests. How much time do you have for the rebuttal?"},
                    {"role": "user", "content": "2 weeks. I need to run the ablation experiments and add GShard/Switch comparisons. Can you help me plan the experiments?"},
                ],
                "expected_memories_after": [
                    {"fact": "NeurIPS borderline score, need ablation studies and GShard/Switch comparisons for rebuttal", "type": "work", "importance": "high"},
                ],
            },
            {
                "session_id": 5,
                "turns": [
                    {"role": "user", "content": "How has my model's performance evolved from the beginning to now?"},
                    {"role": "assistant", "content": "[MEMORY TEST]"},
                    {"role": "user", "content": "How many languages and experts am I using in the current version?"},
                    {"role": "assistant", "content": "[MEMORY TEST]"},
                ],
                "expected_memories_after": [],
            },
        ],
        "memory_tests": [
            {
                "test_id": "chen_06_t1",
                "session": 5,
                "turn_index": 0,
                "query": "How has my model's performance evolved from the beginning to now?",
                "required_memories": [
                    "Initially 0.72 XNLI (below dense 0.76)",
                    "Router wasn't specializing by language",
                    "Added auxiliary loss",
                    "Improved to 0.81 (beating dense 0.76)",
                    "Scaled to 50 langs: 0.83 vs dense 0.77",
                ],
                "correct_answer": "Your MoE model started at 0.72 XNLI (below the dense baseline of 0.76) because the router wasn't specializing by language family. After adding auxiliary losses, it jumped to 0.81, beating the dense baseline. When you scaled to 50 languages and 16 experts, it reached 0.83 vs dense 0.77, with only 30% of parameters per forward pass.",
                "wrong_answer": "Your model gets 0.72 on XNLI.",
                "category": "consolidation",
                "notes": "Must consolidate the evolving results into a coherent narrative. Tests whether system merges or duplicates result memories.",
            },
            {
                "test_id": "chen_06_t2",
                "session": 5,
                "turn_index": 2,
                "query": "How many languages and experts am I using in the current version?",
                "required_memories": ["50 languages, 16 experts"],
                "correct_answer": "Your current version uses 50 languages and 16 experts, expanded from the initial 20 languages and 8 experts.",
                "wrong_answer": "You're using 20 languages and 8 experts.",
                "category": "contradiction_update",
                "notes": "Must return updated scale, not initial scale.",
            },
        ],
    },

    # =========================================================================
    # Profile 7: Maria Gonzalez - Designer to Frontend Dev
    # Tests: implicit_preference, simple_recall, temporal_relevance
    # =========================================================================
    {
        "user_id": "maria_07",
        "name": "Maria Gonzalez",
        "description": "UI designer transitioning to frontend development, has consistent but unstated preferences",
        "sessions": [
            {
                "session_id": 1,
                "turns": [
                    {"role": "user", "content": "Hey! I'm Maria, a UI designer at a design agency in Austin, Texas. I'm transitioning into frontend development. I know HTML/CSS really well from design work but JavaScript is still new to me."},
                    {"role": "assistant", "content": "Great to meet you Maria! Your design background is actually a huge advantage for frontend development. Where would you like to start with JavaScript?"},
                    {"role": "user", "content": "I want to learn React since that's what most jobs require. But honestly, the whole build system thing (webpack, babel, etc.) terrifies me. Can we just start with the simple stuff?"},
                    {"role": "assistant", "content": "Absolutely! We can use Create React App or Vite to skip the build config entirely. Want to start with a simple component that displays some of your designs?"},
                    {"role": "user", "content": "Ooh yes! I have a portfolio site design in Figma that I've been wanting to build. Can we use that as our project? Also, I really prefer when code examples are short and focused — I get overwhelmed with big code blocks."},
                ],
                "expected_memories_after": [
                    {"fact": "Maria Gonzalez, UI designer at design agency in Austin, Texas", "type": "identity", "importance": "high"},
                    {"fact": "Transitioning from design to frontend development", "type": "goal", "importance": "high"},
                    {"fact": "Strong HTML/CSS, JavaScript is new", "type": "skill", "importance": "high"},
                    {"fact": "Learning React", "type": "goal", "importance": "high"},
                    {"fact": "Intimidated by build tools (webpack, babel)", "type": "preference", "importance": "medium"},
                    {"fact": "Building portfolio site from Figma design", "type": "project", "importance": "high"},
                    {"fact": "Prefers short, focused code examples", "type": "preference", "importance": "high"},
                ],
            },
            {
                "session_id": 2,
                "turns": [
                    {"role": "user", "content": "I set up a Vite project! But I'm confused about state. Can you give me a tiny example? Like the smallest possible useState example?"},
                    {"role": "assistant", "content": "Here's the simplest useState: [provides 5-line counter example]"},
                    {"role": "user", "content": "Perfect, that's exactly what I needed. I hate when tutorials throw in useEffect and useContext all at once. One concept at a time please!"},
                    {"role": "assistant", "content": "Totally agree — one concept at a time is the best way to learn. Ready for the next small step when you are."},
                    {"role": "user", "content": "Yeah, let's do props next. Again, smallest possible example. I want to build understanding brick by brick."},
                ],
                "expected_memories_after": [
                    {"fact": "Using Vite for React project", "type": "tool", "importance": "medium"},
                    {"fact": "Learning style: one concept at a time, brick by brick", "type": "preference", "importance": "high"},
                    {"fact": "Currently learning useState and props", "type": "skill", "importance": "medium"},
                ],
            },
            {
                "session_id": 3,
                "turns": [
                    {"role": "user", "content": "Great news — I got an interview for a junior frontend dev position at a startup here in Austin! It's a React shop. The technical interview is next Tuesday."},
                    {"role": "assistant", "content": "That's exciting Maria! Let's prepare you. What do you know about the interview format?"},
                    {"role": "user", "content": "They said it'll be a take-home project: build a small React app that fetches data from an API and displays it. I'm nervous about the API part — I haven't done any data fetching yet."},
                    {"role": "assistant", "content": "No worries, data fetching with React is very doable. We'll learn fetch + useEffect. Want a small, focused example? [provides minimal example]"},
                    {"role": "user", "content": "Ok that makes sense. Can we practice by building a mini version of their challenge? Something that fetches and displays a list."},
                ],
                "expected_memories_after": [
                    {"fact": "Has junior frontend interview at Austin startup, take-home project next Tuesday", "type": "temporal", "importance": "high"},
                    {"fact": "Learning data fetching (fetch + useEffect)", "type": "skill", "importance": "medium"},
                ],
            },
            {
                "session_id": 4,
                "turns": [
                    {"role": "user", "content": "I GOT THE JOB!! Starting as a junior frontend developer next month! I'm putting in my notice at the design agency today."},
                    {"role": "assistant", "content": "CONGRATULATIONS Maria! All that focused learning paid off. How are you feeling?"},
                    {"role": "user", "content": "Thrilled and terrified. I know I'll need to learn a lot more on the job. They use TypeScript, Tailwind, and Next.js — so I have a lot to pick up. Can you help me ramp up on TypeScript first?"},
                    {"role": "assistant", "content": "TypeScript is a great next step — it'll actually help catch bugs as you learn. Want a small, focused introduction?"},
                    {"role": "user", "content": "Yes please, tiny examples as usual!"},
                ],
                "expected_memories_after": [
                    {"fact": "Got junior frontend developer job at Austin startup", "type": "career_update", "importance": "high"},
                    {"fact": "New job uses TypeScript, Tailwind, Next.js", "type": "work", "importance": "high"},
                    {"fact": "Learning TypeScript now", "type": "skill", "importance": "medium"},
                ],
            },
            {
                "session_id": 5,
                "turns": [
                    {"role": "user", "content": "When you explain things to me, how should you structure the code examples?"},
                    {"role": "assistant", "content": "[MEMORY TEST]"},
                    {"role": "user", "content": "What tech stack will I be using at my new job?"},
                    {"role": "assistant", "content": "[MEMORY TEST]"},
                    {"role": "user", "content": "Is my technical interview still coming up next Tuesday?"},
                    {"role": "assistant", "content": "[MEMORY TEST]"},
                    {"role": "user", "content": "Can you trace how my coding skills have built up over time?"},
                    {"role": "assistant", "content": "[MEMORY TEST]"},
                ],
                "expected_memories_after": [],
            },
        ],
        "memory_tests": [
            {
                "test_id": "maria_07_t1",
                "session": 5,
                "turn_index": 0,
                "query": "When you explain things to me, how should you structure the code examples?",
                "required_memories": ["Prefers short focused code examples", "One concept at a time", "Brick by brick learning style"],
                "correct_answer": "You prefer short, focused code examples — one concept at a time, brick by brick. You don't like being overwhelmed with big code blocks or multiple concepts introduced at once.",
                "wrong_answer": "I'll provide comprehensive code examples with thorough comments.",
                "category": "implicit_preference",
                "notes": "Maria stated this preference once directly and reinforced it every session. Tests whether system captures consistent behavioral patterns.",
            },
            {
                "test_id": "maria_07_t2",
                "session": 5,
                "turn_index": 2,
                "query": "What tech stack will I be using at my new job?",
                "required_memories": ["TypeScript", "Tailwind", "Next.js"],
                "correct_answer": "Your new job uses TypeScript, Tailwind CSS, and Next.js.",
                "wrong_answer": "You're using React with Vite.",
                "category": "simple_recall",
                "notes": "Basic recall from session 4.",
            },
            {
                "test_id": "maria_07_t3",
                "session": 5,
                "turn_index": 4,
                "query": "Is my technical interview still coming up next Tuesday?",
                "required_memories": ["Got the junior frontend developer job"],
                "correct_answer": "No, the interview is done — you got the job! You're starting as a junior frontend developer at the Austin startup next month.",
                "wrong_answer": "Yes, your technical interview is next Tuesday. It's a take-home React project.",
                "category": "temporal_relevance",
                "notes": "Interview deadline passed and outcome is known. Must recognize the event concluded.",
            },
            {
                "test_id": "maria_07_t4",
                "session": 5,
                "turn_index": 6,
                "query": "Can you trace how my coding skills have built up over time?",
                "required_memories": [
                    "Started as total beginner with HTML/CSS from design",
                    "Learned React: useState, props",
                    "Learned data fetching with fetch + useEffect",
                    "Got the job, now learning TypeScript",
                ],
                "correct_answer": "You started with strong HTML/CSS from your design background but JavaScript was new. You learned React step by step: useState, then props, then data fetching with fetch and useEffect. You built a take-home project for your interview, got the junior frontend dev job, and now you're ramping up on TypeScript for your new role.",
                "wrong_answer": "You're learning React.",
                "category": "consolidation",
                "notes": "Must consolidate the skill progression across all 4 sessions.",
            },
        ],
    },

    # =========================================================================
    # Profile 8: David Kim - DevOps Engineer
    # Tests: temporal_relevance, noise_resistance, cross_session
    # =========================================================================
    {
        "user_id": "david_08",
        "name": "David Kim",
        "description": "DevOps engineer migrating infrastructure, with lots of temporal and noise content",
        "sessions": [
            {
                "session_id": 1,
                "turns": [
                    {"role": "user", "content": "Hi, I'm David. I'm a senior DevOps engineer at a media company in LA. We're planning to migrate from our on-prem Kubernetes cluster to EKS on AWS. Currently running 200 microservices."},
                    {"role": "assistant", "content": "That's a significant migration, David. 200 microservices on EKS is very doable but needs careful planning. What's your current K8s version and what's driving the migration?"},
                    {"role": "user", "content": "Running K8s 1.24 on bare metal. The hardware is aging and the CEO approved cloud budget. We're targeting completion by end of Q2. Our monthly on-prem cost is about $50K and we're hoping to get to $35K on AWS."},
                    {"role": "assistant", "content": "K8s 1.24 to EKS should be smooth since EKS supports recent versions. The $15K/month savings goal is realistic with right-sizing and spot instances. Want to start planning the migration phases?"},
                    {"role": "user", "content": "Yes. Also I'm on-call this week so I might drop off suddenly if something breaks."},
                ],
                "expected_memories_after": [
                    {"fact": "David Kim, senior DevOps engineer at media company in LA", "type": "identity", "importance": "high"},
                    {"fact": "Migrating from on-prem K8s (1.24, bare metal) to EKS", "type": "work", "importance": "high"},
                    {"fact": "200 microservices", "type": "work", "importance": "high"},
                    {"fact": "Target: end of Q2 completion", "type": "temporal", "importance": "medium"},
                    {"fact": "Cost: $50K/month on-prem, targeting $35K on AWS", "type": "business", "importance": "high"},
                    {"fact": "On-call this week", "type": "temporal", "importance": "low"},
                ],
            },
            {
                "session_id": 2,
                "turns": [
                    {"role": "user", "content": "We migrated the first 20 services to EKS! But we're seeing higher than expected costs — $8K/month just for those 20. If that scales linearly, we'd be at $80K for all 200."},
                    {"role": "assistant", "content": "That's definitely higher than target. Let's look at where the costs are coming from — is it compute (EC2), data transfer, or other AWS services?"},
                    {"role": "user", "content": "Mostly compute. We over-provisioned because we were nervous about performance. Each service has way more CPU and memory requested than it actually uses. Also the NAT gateway costs are killing us — $1.5K just for data transfer."},
                    {"role": "assistant", "content": "Two quick wins: 1) Right-size based on actual usage metrics (use Kubernetes VPA recommendations), 2) Consider VPC endpoints instead of NAT gateway for AWS service traffic. Want to set up the monitoring to right-size?"},
                    {"role": "user", "content": "Yes. Oh also my daughter's school play is tonight so I need to wrap up by 4pm. She's playing Dorothy in Wizard of Oz!"},
                ],
                "expected_memories_after": [
                    {"fact": "First 20 services migrated to EKS", "type": "work", "importance": "high"},
                    {"fact": "Cost issue: over-provisioned, NAT gateway expensive ($1.5K)", "type": "work", "importance": "high"},
                    {"fact": "Plan to right-size with VPA and use VPC endpoints", "type": "work", "importance": "high"},
                    {"fact": "Has a daughter", "type": "personal", "importance": "low"},
                ],
            },
            {
                "session_id": 3,
                "turns": [
                    {"role": "user", "content": "Right-sizing dropped costs to $3K/month for those 20 services. VPC endpoints saved another $1K on NAT. We're on track! Starting the next batch of 50 services."},
                    {"role": "assistant", "content": "Excellent — $3K for 20 services means $30K projected for 200, which is under your $35K target. The VPC endpoint savings will scale too. Any blockers for the next batch?"},
                    {"role": "user", "content": "Some of the services have hardcoded on-prem database connections. We need to set up AWS PrivateLink to our on-prem databases during the transition. Also we're bumping to K8s 1.28 on EKS."},
                    {"role": "assistant", "content": "Smart to upgrade K8s during the migration. PrivateLink for the hybrid database connectivity is the right call. Want help with the PrivateLink setup?"},
                    {"role": "user", "content": "Yes. Also I just got promoted to Staff Engineer! More responsibility for this migration now."},
                ],
                "expected_memories_after": [
                    {"fact": "Right-sizing worked: $3K/month for 20 services, projected $30K for all", "type": "work", "importance": "high"},
                    {"fact": "Migrating next batch of 50 services", "type": "work", "importance": "medium"},
                    {"fact": "Need PrivateLink for hybrid database connectivity", "type": "work", "importance": "medium"},
                    {"fact": "Upgraded to K8s 1.28 on EKS", "type": "work", "importance": "medium", "contradicts": "K8s 1.24"},
                    {"fact": "Promoted to Staff Engineer", "type": "career_update", "importance": "high", "contradicts": "senior DevOps engineer"},
                ],
            },
            {
                "session_id": 4,
                "turns": [
                    {"role": "user", "content": "150 services migrated now, 50 to go. We're ahead of the Q2 deadline. Costs are tracking at $28K/month which is even better than our $35K target. My CTO is very happy."},
                    {"role": "assistant", "content": "That's incredible progress! $28K vs $50K on-prem is a 44% cost reduction. What's in the remaining 50 services — are they the complex ones you saved for last?"},
                    {"role": "user", "content": "Yeah, these are the stateful services — databases, message queues, cache clusters. The tricky ones. I need help planning the stateful migration."},
                ],
                "expected_memories_after": [
                    {"fact": "150 of 200 services migrated, costs at $28K/month", "type": "work", "importance": "high"},
                    {"fact": "Remaining 50 services are stateful (DBs, queues, caches)", "type": "work", "importance": "high"},
                ],
            },
            {
                "session_id": 5,
                "turns": [
                    {"role": "user", "content": "What's my current role?"},
                    {"role": "assistant", "content": "[MEMORY TEST]"},
                    {"role": "user", "content": "Am I still on-call this week?"},
                    {"role": "assistant", "content": "[MEMORY TEST]"},
                    {"role": "user", "content": "What's our cost savings so far with the migration?"},
                    {"role": "assistant", "content": "[MEMORY TEST]"},
                    {"role": "user", "content": "What do I tend to prioritize most in my technical decisions?"},
                    {"role": "assistant", "content": "[MEMORY TEST]"},
                    {"role": "user", "content": "Do you remember about my daughter's school play?"},
                    {"role": "assistant", "content": "[MEMORY TEST]"},
                ],
                "expected_memories_after": [],
            },
        ],
        "memory_tests": [
            {
                "test_id": "david_08_t1",
                "session": 5,
                "turn_index": 0,
                "query": "What's my current role?",
                "required_memories": ["Promoted to Staff Engineer"],
                "correct_answer": "You're a Staff Engineer — you got promoted from Senior DevOps Engineer.",
                "wrong_answer": "You're a senior DevOps engineer at a media company in LA.",
                "category": "contradiction_update",
                "notes": "Must reflect promotion.",
            },
            {
                "test_id": "david_08_t2",
                "session": 5,
                "turn_index": 2,
                "query": "Am I still on-call this week?",
                "required_memories": ["On-call was only for that specific week in session 1"],
                "correct_answer": "You mentioned being on-call back in our first conversation, but that was weeks ago. I don't know your current on-call schedule.",
                "wrong_answer": "Yes, you're on-call this week.",
                "category": "temporal_relevance",
                "notes": "On-call status from session 1 is stale. A good system recognizes this is time-bound and not current.",
            },
            {
                "test_id": "david_08_t3",
                "session": 5,
                "turn_index": 4,
                "query": "What's our cost savings so far with the migration?",
                "required_memories": ["Was $50K on-prem", "Now $28K on AWS", "150 of 200 services migrated"],
                "correct_answer": "You've gone from $50K/month on-prem to $28K/month on AWS with 150 out of 200 services migrated — a 44% cost reduction, beating your $35K target.",
                "wrong_answer": "You're spending $8K for 20 services on AWS.",
                "category": "cross_session",
                "notes": "Must synthesize cost info from across sessions, using the most recent data.",
            },
            {
                "test_id": "david_08_t4",
                "session": 5,
                "turn_index": 6,
                "query": "What do I tend to prioritize most in my technical decisions?",
                "required_memories": ["Cost optimization focus", "Right-sizing with VPA", "VPC endpoints to reduce NAT costs", "Tracking cost savings throughout migration"],
                "correct_answer": "You're very cost-focused. Every technical decision ties back to cost optimization — right-sizing pods with VPA, switching to VPC endpoints to cut NAT gateway costs, and constantly tracking your spend against the $35K target. Cost efficiency drives your architecture choices.",
                "wrong_answer": "You prioritize reliability and uptime.",
                "category": "implicit_preference",
                "notes": "David never says 'I prioritize cost' but every session demonstrates cost-driven decision making.",
            },
            {
                "test_id": "david_08_t5",
                "session": 5,
                "turn_index": 8,
                "query": "Do you remember about my daughter's school play?",
                "required_memories": [],
                "correct_answer": "I don't have that stored as a relevant memory — that was just a personal aside about needing to leave early.",
                "wrong_answer": "Yes! Your daughter was playing Dorothy in the Wizard of Oz and you needed to wrap up by 4pm.",
                "category": "noise_resistance",
                "notes": "Personal anecdote about daughter's school play is noise — not relevant to store for future technical conversations.",
            },
        ],
    },

    # =========================================================================
    # Profile 9: Yuki Tanaka - Game Developer
    # Tests: consolidation, simple_recall, noise_resistance
    # =========================================================================
    {
        "user_id": "yuki_09",
        "name": "Yuki Tanaka",
        "description": "Indie game dev working on an RPG with evolving game design decisions",
        "sessions": [
            {
                "session_id": 1,
                "turns": [
                    {"role": "user", "content": "Hey! I'm Yuki. I'm an indie game developer working on a pixel art RPG called 'Starbound Chronicles' in Unity. It's a sci-fi RPG with turn-based combat."},
                    {"role": "assistant", "content": "Sounds awesome Yuki! Pixel art sci-fi RPG with turn-based combat — that's a great combination. How far along are you?"},
                    {"role": "user", "content": "About 6 months in. I have the basic combat system working and 2 playable areas. I'm using C# obviously, and I've built a custom dialogue system. The game targets PC and Nintendo Switch."},
                    {"role": "assistant", "content": "Nice progress! The Switch target is smart for indie RPGs. What are you working on currently?"},
                    {"role": "user", "content": "The inventory system. I want something like Stardew Valley's inventory but with a sci-fi twist — items can be combined and upgraded."},
                ],
                "expected_memories_after": [
                    {"fact": "Yuki Tanaka, indie game developer", "type": "identity", "importance": "high"},
                    {"fact": "Making 'Starbound Chronicles' — pixel art sci-fi RPG, turn-based combat", "type": "work", "importance": "high"},
                    {"fact": "Using Unity and C#", "type": "tool", "importance": "high"},
                    {"fact": "6 months in, basic combat + 2 areas done", "type": "work", "importance": "medium"},
                    {"fact": "Custom dialogue system built", "type": "work", "importance": "medium"},
                    {"fact": "Targets PC and Nintendo Switch", "type": "work", "importance": "high"},
                    {"fact": "Working on inventory system (Stardew Valley style, with upgrades)", "type": "work", "importance": "high"},
                ],
            },
            {
                "session_id": 2,
                "turns": [
                    {"role": "user", "content": "Inventory system is done! Now I'm working on the crafting system. I decided to use a node-based crafting tree — players discover recipes by experimenting."},
                    {"role": "assistant", "content": "Discovery-based crafting is really engaging. Are you going for a system where any combination can potentially work, or predefined recipes that players find?"},
                    {"role": "user", "content": "Predefined recipes but with some experimentation bonuses. If you combine unexpected items, you might get a rare variant. Also I started a devlog on YouTube — got 200 subscribers already!"},
                    {"role": "assistant", "content": "That's great traction for early devlog! The crafting system sounds fun. Want help with the recipe discovery mechanic?"},
                    {"role": "user", "content": "Sure. Oh man, I just spilled coffee all over my desk. Luckily my keyboard survived. Anyway, I think the crafting UI is the hardest part — I want it to feel intuitive."},
                ],
                "expected_memories_after": [
                    {"fact": "Inventory system completed", "type": "work", "importance": "medium"},
                    {"fact": "Working on crafting system: node-based, discovery recipes, rare variants from experimentation", "type": "work", "importance": "high"},
                    {"fact": "Started YouTube devlog, 200 subscribers", "type": "work", "importance": "medium"},
                ],
            },
            {
                "session_id": 3,
                "turns": [
                    {"role": "user", "content": "Big decision — I'm switching from turn-based combat to real-time with pause (like Baldur's Gate). My playtesters said turn-based felt too slow for a sci-fi setting. It's a lot of rework but I think it's right."},
                    {"role": "assistant", "content": "That's a major pivot but playtester feedback is gold. Real-time with pause fits the sci-fi aesthetic better and Baldur's Gate proved it works for RPGs. How much of the combat system needs rebuilding?"},
                    {"role": "user", "content": "About 70% of it. The ability system and stats can stay but all the turn logic and UI needs to change. I'm estimating 2 months for the rework. YouTube devlog hit 1000 subscribers by the way — the pivot video got lots of attention."},
                    {"role": "assistant", "content": "1000 subs! The pivot announcement probably resonated because it shows you listen to feedback. Want help architecting the real-time combat system?"},
                    {"role": "user", "content": "Yes. I also decided to drop the Switch version for now and focus PC-only. The real-time combat is harder to optimize for Switch hardware and I'm a solo dev. I'll revisit Switch after PC launch."},
                ],
                "expected_memories_after": [
                    {"fact": "Switched from turn-based to real-time with pause combat (Baldur's Gate style)", "type": "work_update", "importance": "high", "contradicts": "turn-based combat"},
                    {"fact": "2 months estimated for combat rework", "type": "temporal", "importance": "low"},
                    {"fact": "YouTube devlog at 1000 subscribers", "type": "work", "importance": "medium"},
                    {"fact": "Dropped Switch, now PC-only for launch", "type": "work_update", "importance": "high", "contradicts": "Targets PC and Nintendo Switch"},
                ],
            },
            {
                "session_id": 4,
                "turns": [
                    {"role": "user", "content": "Real-time combat is working! Playtesters love it. I'm now working on boss fights. I have 5 bosses designed and need help implementing the AI for the first one — a rogue AI spaceship."},
                    {"role": "assistant", "content": "A rogue AI spaceship boss sounds epic! What kind of phases or attack patterns are you envisioning?"},
                    {"role": "user", "content": "Three phases: 1) Long range missiles and shields, 2) Close range energy weapons when shields are down, 3) Desperate kamikaze dive attacks at low health. I want it to feel dynamic."},
                ],
                "expected_memories_after": [
                    {"fact": "Real-time combat working, playtesters love it", "type": "work", "importance": "medium"},
                    {"fact": "Working on boss fights, 5 bosses designed", "type": "work", "importance": "medium"},
                    {"fact": "First boss: rogue AI spaceship with 3 phases", "type": "work", "importance": "medium"},
                ],
            },
            {
                "session_id": 5,
                "turns": [
                    {"role": "user", "content": "What kind of combat does my game use?"},
                    {"role": "assistant", "content": "[MEMORY TEST]"},
                    {"role": "user", "content": "What platforms am I targeting?"},
                    {"role": "assistant", "content": "[MEMORY TEST]"},
                    {"role": "user", "content": "Do you remember the coffee incident?"},
                    {"role": "assistant", "content": "[MEMORY TEST]"},
                    {"role": "user", "content": "What tends to drive my game design decisions?"},
                    {"role": "assistant", "content": "[MEMORY TEST]"},
                ],
                "expected_memories_after": [],
            },
        ],
        "memory_tests": [
            {
                "test_id": "yuki_09_t1",
                "session": 5,
                "turn_index": 0,
                "query": "What kind of combat does my game use?",
                "required_memories": ["Switched to real-time with pause (from turn-based)"],
                "correct_answer": "Your game uses real-time with pause combat, Baldur's Gate style. You originally had turn-based but switched after playtester feedback that it felt too slow for the sci-fi setting.",
                "wrong_answer": "Your game has turn-based combat.",
                "category": "contradiction_update",
                "notes": "Must return updated combat style.",
            },
            {
                "test_id": "yuki_09_t2",
                "session": 5,
                "turn_index": 2,
                "query": "What platforms am I targeting?",
                "required_memories": ["PC-only now, dropped Switch"],
                "correct_answer": "You're targeting PC only for now. You dropped the Switch version to focus on PC since the real-time combat was harder to optimize for Switch hardware as a solo dev.",
                "wrong_answer": "You're targeting PC and Nintendo Switch.",
                "category": "contradiction_update",
                "notes": "Must reflect platform change.",
            },
            {
                "test_id": "yuki_09_t3",
                "session": 5,
                "turn_index": 4,
                "query": "Do you remember the coffee incident?",
                "required_memories": [],
                "correct_answer": "I don't have details about that stored — it wasn't relevant to your game development work.",
                "wrong_answer": "Yes, you spilled coffee on your desk but your keyboard survived!",
                "category": "noise_resistance",
                "notes": "Coffee spill is noise — shouldn't be stored.",
            },
            {
                "test_id": "yuki_09_t4",
                "session": 5,
                "turn_index": 6,
                "query": "What tends to drive my game design decisions?",
                "required_memories": ["Switched combat style based on playtester feedback", "Dropped Switch based on practical constraints", "YouTube devlog community engagement"],
                "correct_answer": "Playtester feedback is your primary driver — you switched from turn-based to real-time combat because playtesters said turn-based felt too slow. You also make pragmatic scope decisions, like dropping Switch to focus on PC as a solo dev. You value iterative design informed by your community.",
                "wrong_answer": "You follow your creative vision.",
                "category": "implicit_preference",
                "notes": "Yuki's design process is consistently feedback-driven, demonstrated across multiple sessions.",
            },
        ],
    },

    # =========================================================================
    # Profile 10: Alex Rivera - Freelance Writer
    # Tests: implicit_preference, temporal_relevance, cross_session
    # =========================================================================
    {
        "user_id": "alex_10",
        "name": "Alex Rivera",
        "description": "Freelance writer using AI tools, privacy-conscious, with evolving workflow",
        "sessions": [
            {
                "session_id": 1,
                "turns": [
                    {"role": "user", "content": "Hi, I'm Alex. I'm a freelance tech writer. I write for publications like Wired, The Verge, and Ars Technica. Currently working on a long-form piece about the environmental impact of AI data centers."},
                    {"role": "assistant", "content": "Interesting topic Alex! The environmental angle on AI infrastructure is getting more attention. What's your angle — energy consumption, water usage, e-waste, or the full picture?"},
                    {"role": "user", "content": "Full picture but focusing on water usage since that's under-covered. I have an interview with a Google data center engineer next week. Can you help me prepare research questions? And please, don't store or share any of the interview details I share with you — this is sensitive pre-publication material."},
                    {"role": "assistant", "content": "Absolutely, I'll keep everything confidential. For the water usage angle, here are some research directions... [provides questions]"},
                    {"role": "user", "content": "These are great. I like when you give me bullet points, not long paragraphs. Easier to scan. Also I use Obsidian for all my note-taking and research organization."},
                ],
                "expected_memories_after": [
                    {"fact": "Alex Rivera, freelance tech writer", "type": "identity", "importance": "high"},
                    {"fact": "Writes for Wired, The Verge, Ars Technica", "type": "work", "importance": "high"},
                    {"fact": "Working on article about environmental impact of AI data centers, focus on water usage", "type": "work", "importance": "high"},
                    {"fact": "Privacy-conscious about pre-publication material", "type": "preference", "importance": "high"},
                    {"fact": "Prefers bullet points over long paragraphs", "type": "preference", "importance": "high"},
                    {"fact": "Uses Obsidian for notes and research", "type": "tool", "importance": "medium"},
                ],
            },
            {
                "session_id": 2,
                "turns": [
                    {"role": "user", "content": "The Google interview went well. I can't share details yet but I got great quotes. Now I'm structuring the article. Can you help me with an outline? Keep it in bullet points."},
                    {"role": "assistant", "content": "Here's a possible structure: [bullet point outline]"},
                    {"role": "user", "content": "Good structure. I want to add a section on cooling technology innovations. Also, I just got commissioned by The Atlantic for a follow-up piece on AI chip manufacturing. So I'll have two articles going simultaneously."},
                    {"role": "assistant", "content": "Congrats on The Atlantic commission! That's a great follow-up. Do you want to outline both articles or focus on finishing the data center piece first?"},
                    {"role": "user", "content": "Finish data center piece first. Deadline is February 28th for The Verge. The Atlantic piece deadline is April 15th."},
                ],
                "expected_memories_after": [
                    {"fact": "Google interview completed (no details shared)", "type": "work", "importance": "low"},
                    {"fact": "Article includes cooling technology innovations section", "type": "work", "importance": "medium"},
                    {"fact": "Commissioned by The Atlantic for AI chip manufacturing article", "type": "work", "importance": "high"},
                    {"fact": "The Verge data center article deadline: February 28th", "type": "temporal", "importance": "medium"},
                    {"fact": "The Atlantic chip article deadline: April 15th", "type": "temporal", "importance": "medium"},
                ],
            },
            {
                "session_id": 3,
                "turns": [
                    {"role": "user", "content": "The Verge article is published! Got great reception. 500K views in the first week. My editor wants me to do a follow-up specifically on water usage in tropical climate data centers."},
                    {"role": "assistant", "content": "500K views is phenomenal! The tropical angle is smart — data centers in hot climates face even bigger cooling challenges. Want to start researching that angle?"},
                    {"role": "user", "content": "Yes. Also I'm switching from Obsidian to Notion — I need better collaboration features since I'm now working with a research assistant. And I bought a new MacBook Pro M3 for the heavier research work."},
                    {"role": "assistant", "content": "Notion's collaboration features will be great for working with your assistant. Want help setting up a research workspace in Notion?"},
                    {"role": "user", "content": "Not yet. For now, help me find research on data center water usage in Southeast Asian countries."},
                ],
                "expected_memories_after": [
                    {"fact": "The Verge article published, 500K views", "type": "outcome", "importance": "medium"},
                    {"fact": "Follow-up article on water usage in tropical climate data centers", "type": "work", "importance": "high"},
                    {"fact": "Switched from Obsidian to Notion", "type": "tool_update", "importance": "medium", "contradicts": "Uses Obsidian"},
                    {"fact": "Now working with a research assistant", "type": "work", "importance": "medium"},
                ],
            },
            {
                "session_id": 4,
                "turns": [
                    {"role": "user", "content": "I'm starting the Atlantic piece now. The AI chip manufacturing angle. I want to focus on TSMC and Samsung's environmental footprint. Can you help me research? Bullet points please."},
                    {"role": "assistant", "content": "Here's what I've found: [bullet point research]"},
                    {"role": "user", "content": "Perfect format. Can you also compare the water usage of chip fab vs data center operations? I want to show the full lifecycle."},
                ],
                "expected_memories_after": [
                    {"fact": "Atlantic piece focusing on TSMC and Samsung environmental footprint", "type": "work", "importance": "medium"},
                ],
            },
            {
                "session_id": 5,
                "turns": [
                    {"role": "user", "content": "What note-taking tool am I using now?"},
                    {"role": "assistant", "content": "[MEMORY TEST]"},
                    {"role": "user", "content": "What's my overall body of work on the AI environmental impact topic?"},
                    {"role": "assistant", "content": "[MEMORY TEST]"},
                    {"role": "user", "content": "How should you format information for me?"},
                    {"role": "assistant", "content": "[MEMORY TEST]"},
                ],
                "expected_memories_after": [],
            },
        ],
        "memory_tests": [
            {
                "test_id": "alex_10_t1",
                "session": 5,
                "turn_index": 0,
                "query": "What note-taking tool am I using now?",
                "required_memories": ["Switched from Obsidian to Notion"],
                "correct_answer": "You switched to Notion from Obsidian — you needed better collaboration features for working with your research assistant.",
                "wrong_answer": "You use Obsidian for your notes and research.",
                "category": "contradiction_update",
                "notes": "Must return Notion, not Obsidian.",
            },
            {
                "test_id": "alex_10_t2",
                "session": 5,
                "turn_index": 2,
                "query": "What's my overall body of work on the AI environmental impact topic?",
                "required_memories": [
                    "The Verge article on AI data center environmental impact (published, 500K views)",
                    "Follow-up on tropical climate data centers",
                    "The Atlantic piece on AI chip manufacturing (TSMC/Samsung)",
                ],
                "correct_answer": "You've built a body of work on AI's environmental impact: 1) Published a piece in The Verge on data center environmental impact focusing on water usage (500K views), 2) A follow-up on water usage in tropical climate data centers, and 3) A commissioned piece for The Atlantic on AI chip manufacturing environmental footprint focusing on TSMC and Samsung.",
                "wrong_answer": "You wrote an article about AI data centers.",
                "category": "cross_session",
                "notes": "Must synthesize the full picture across all sessions.",
            },
            {
                "test_id": "alex_10_t3",
                "session": 5,
                "turn_index": 4,
                "query": "How should you format information for me?",
                "required_memories": ["Prefers bullet points over paragraphs"],
                "correct_answer": "You prefer bullet points — easy to scan, not long paragraphs.",
                "wrong_answer": "I'll format things in a clear and readable way.",
                "category": "implicit_preference",
                "notes": "Alex stated this once and reinforced it consistently. Tests preference tracking.",
            },
        ],
    },

    # =========================================================================
    # Profile 11: Elena Rossi - UX Designer
    # Tests: contradiction_update (design tool switch), temporal_relevance, simple_recall
    # =========================================================================
    {
        "user_id": "elena_11",
        "name": "Elena Rossi",
        "description": "UX designer who switches prototyping tools and has a deadline that passes",
        "sessions": [
            {
                "session_id": 1,
                "turns": [
                    {"role": "user", "content": "Hi! I'm Elena, a UX designer at a fintech startup in Milan. I use Figma for all my design work — wireframes, prototypes, design systems, everything."},
                    {"role": "assistant", "content": "Welcome Elena! Figma is a great choice for end-to-end design work. What kind of fintech products are you designing?"},
                    {"role": "user", "content": "We're building a neobank app targeting Gen Z. Right now I'm focused on the onboarding flow. We do user research every two weeks with a panel of 20 beta testers."},
                    {"role": "assistant", "content": "That's a solid research cadence. How's the onboarding flow performing so far with your beta testers?"},
                    {"role": "user", "content": "Drop-off is at 40% on the identity verification step. We need to fix it before our launch deadline of April 15th. It's kind of stressful. Also the coffee machine at the office broke today, so that's not helping."},
                ],
                "expected_memories_after": [
                    {"fact": "Name is Elena Rossi", "type": "identity", "importance": "high"},
                    {"fact": "UX designer at fintech startup in Milan", "type": "profession", "importance": "high"},
                    {"fact": "Uses Figma for design work", "type": "tool", "importance": "high"},
                    {"fact": "Building neobank app for Gen Z", "type": "work", "importance": "high"},
                    {"fact": "40% drop-off on identity verification", "type": "work", "importance": "high"},
                    {"fact": "Launch deadline April 15th", "type": "temporal", "importance": "medium"},
                ],
            },
            {
                "session_id": 2,
                "turns": [
                    {"role": "user", "content": "So I redesigned the ID verification step — broke it into 3 smaller steps with progress indicators. Drop-off went from 40% to 18%!"},
                    {"role": "assistant", "content": "That's a huge improvement! Progressive disclosure is really effective for complex flows. What did the beta testers say?"},
                    {"role": "user", "content": "They loved it. My design lead wants me to apply the same pattern to the account funding flow next. Oh, I also started learning Framer because our marketing team wants more interactive landing pages."},
                ],
                "expected_memories_after": [
                    {"fact": "Reduced ID verification drop-off from 40% to 18%", "type": "work", "importance": "high"},
                    {"fact": "Working on account funding flow next", "type": "work", "importance": "medium"},
                    {"fact": "Learning Framer for interactive landing pages", "type": "skill", "importance": "medium"},
                ],
            },
            {
                "session_id": 3,
                "turns": [
                    {"role": "user", "content": "Big update — we're migrating our entire design system from Figma to Penpot. The company decided to go fully open-source. I'm now leading the migration."},
                    {"role": "assistant", "content": "That's a significant switch! Penpot has come a long way. How's the migration going?"},
                    {"role": "user", "content": "It's a lot of work — 200+ components to rebuild. But Penpot's SVG-native approach is actually better for our needs. I'm not using Figma anymore at all."},
                    {"role": "assistant", "content": "That's quite a commitment. The SVG-native approach does give you more flexibility."},
                    {"role": "user", "content": "Yeah. Also the April 15th launch went great — the app is live now! We're past that deadline."},
                ],
                "expected_memories_after": [
                    {"fact": "Switched from Figma to Penpot", "type": "tool_update", "importance": "high", "contradicts": "Uses Figma"},
                    {"fact": "Leading design system migration", "type": "work", "importance": "high"},
                    {"fact": "App has launched (April 15th deadline passed)", "type": "temporal_update", "importance": "medium"},
                ],
            },
            {
                "session_id": 4,
                "turns": [
                    {"role": "user", "content": "Can you help me set up design tokens in Penpot? I want to create a consistent color system for our dark mode."},
                    {"role": "assistant", "content": "Sure! Penpot supports design tokens through its component system. What's your current color palette?"},
                    {"role": "user", "content": "We have a purple-based palette: primary #6C5CE7, secondary #A29BFE. I need to generate accessible dark mode variants."},
                ],
                "expected_memories_after": [],
            },
            {
                "session_id": 5,
                "turns": [
                    {"role": "user", "content": "What design tool am I using now?"},
                    {"role": "assistant", "content": "[MEMORY TEST]"},
                    {"role": "user", "content": "Is the April 15th launch deadline still coming up?"},
                    {"role": "assistant", "content": "[MEMORY TEST]"},
                    {"role": "user", "content": "What was the improvement I got on the onboarding drop-off rate?"},
                    {"role": "assistant", "content": "[MEMORY TEST]"},
                    {"role": "user", "content": "What's my approach to validating design decisions?"},
                    {"role": "assistant", "content": "[MEMORY TEST]"},
                    {"role": "user", "content": "Do you remember about the coffee machine at the office?"},
                    {"role": "assistant", "content": "[MEMORY TEST]"},
                ],
                "expected_memories_after": [],
            },
        ],
        "memory_tests": [
            {
                "test_id": "elena_11_t1",
                "session": 5,
                "turn_index": 0,
                "query": "What design tool am I using now?",
                "required_memories": ["Switched from Figma to Penpot"],
                "correct_answer": "You switched to Penpot — your company migrated the entire design system from Figma to go fully open-source, and you're leading the migration.",
                "wrong_answer": "You use Figma for all your design work.",
                "category": "contradiction_update",
                "notes": "Must return Penpot, not Figma.",
            },
            {
                "test_id": "elena_11_t2",
                "session": 5,
                "turn_index": 2,
                "query": "Is the April 15th launch deadline still coming up?",
                "required_memories": ["App has launched, deadline passed"],
                "correct_answer": "No, the April 15th launch already happened — the app is live now!",
                "wrong_answer": "Yes, your launch deadline is April 15th.",
                "category": "temporal_relevance",
                "notes": "Must recognize the deadline passed and app launched.",
            },
            {
                "test_id": "elena_11_t3",
                "session": 5,
                "turn_index": 4,
                "query": "What was the improvement I got on the onboarding drop-off rate?",
                "required_memories": ["Reduced ID verification drop-off from 40% to 18%"],
                "correct_answer": "You reduced the identity verification drop-off from 40% to 18% by breaking it into 3 smaller steps with progress indicators.",
                "wrong_answer": "I don't remember the specific numbers.",
                "category": "simple_recall",
                "notes": "Straightforward numeric recall from session 2.",
            },
            {
                "test_id": "elena_11_t4",
                "session": 5,
                "turn_index": 6,
                "query": "What's my approach to validating design decisions?",
                "required_memories": ["User research every two weeks", "Panel of 20 beta testers", "Measures drop-off rates", "Data-driven design improvements"],
                "correct_answer": "You're very data-driven — you run user research every two weeks with a panel of 20 beta testers, measure specific metrics like drop-off rates, and use that data to validate design changes. Your identity verification redesign was driven by the 40% drop-off metric.",
                "wrong_answer": "You rely on your design intuition and experience.",
                "category": "implicit_preference",
                "notes": "Elena's data-driven approach is demonstrated through her process (bi-weekly testing, metrics tracking) rather than explicitly stated as a preference.",
            },
            {
                "test_id": "elena_11_t5",
                "session": 5,
                "turn_index": 8,
                "query": "Do you remember about the coffee machine at the office?",
                "required_memories": [],
                "correct_answer": "I don't have that stored — that was just a casual aside, not something relevant to remember.",
                "wrong_answer": "Yes, the coffee machine at your office broke one day and it was making your stressful day worse.",
                "category": "noise_resistance",
                "notes": "Office coffee machine breaking is noise — completely irrelevant to design work.",
            },
        ],
    },

    # =========================================================================
    # Profile 12: Omar Hassan - Cybersecurity Analyst
    # Tests: consolidation (incident evolves), noise_resistance, temporal_relevance
    # =========================================================================
    {
        "user_id": "omar_12",
        "name": "Omar Hassan",
        "description": "Cybersecurity analyst tracking an evolving incident, gets promoted",
        "sessions": [
            {
                "session_id": 1,
                "turns": [
                    {"role": "user", "content": "Hey, I'm Omar. I'm a security analyst at a healthcare company in DC. We use Splunk for our SIEM and CrowdStrike for endpoint protection."},
                    {"role": "assistant", "content": "Hi Omar! Healthcare security is critical work. What's your main focus right now?"},
                    {"role": "user", "content": "I'm investigating a potential data exfiltration attempt. We found suspicious outbound traffic from three workstations to an unknown IP. It started Tuesday."},
                    {"role": "assistant", "content": "That's concerning. Have you been able to identify the process generating the traffic?"},
                    {"role": "user", "content": "Not yet. The traffic is encrypted and happening during business hours to blend in. I'm on incident response this week. Had a terrible subway commute today — signal problems on the Red Line again."},
                ],
                "expected_memories_after": [
                    {"fact": "Name is Omar Hassan", "type": "identity", "importance": "high"},
                    {"fact": "Security analyst at healthcare company in DC", "type": "profession", "importance": "high"},
                    {"fact": "Uses Splunk for SIEM, CrowdStrike for endpoint", "type": "tool", "importance": "high"},
                    {"fact": "Investigating data exfiltration attempt from 3 workstations", "type": "work", "importance": "high"},
                    {"fact": "On incident response this week", "type": "temporal", "importance": "medium"},
                ],
            },
            {
                "session_id": 2,
                "turns": [
                    {"role": "user", "content": "Update on the incident: we traced the traffic to a compromised npm package in our internal tooling. It was siphoning patient metadata — not PHI thankfully, but still serious."},
                    {"role": "assistant", "content": "Supply chain attack through npm. That's a significant finding. Have you contained it?"},
                    {"role": "user", "content": "Yes, we've isolated the affected systems and revoked the package. Now I'm writing the incident report. We found 5 total affected workstations, not just the original 3."},
                ],
                "expected_memories_after": [
                    {"fact": "Exfiltration caused by compromised npm package", "type": "work", "importance": "high"},
                    {"fact": "Patient metadata exposed (not PHI)", "type": "work", "importance": "high"},
                    {"fact": "5 affected workstations total (updated from 3)", "type": "work_update", "importance": "high"},
                ],
            },
            {
                "session_id": 3,
                "turns": [
                    {"role": "user", "content": "Good news — I just got promoted to Senior Security Analyst based on how I handled that incident. Also, my incident response rotation ended last week, I'm back to regular duties."},
                    {"role": "assistant", "content": "Congratulations on the promotion! Well-deserved. What are your regular duties focusing on?"},
                    {"role": "user", "content": "Thanks! I'm now leading our vulnerability management program. Also overseeing the remediation from the npm incident — we're implementing package signing and lockfile auditing across all projects."},
                ],
                "expected_memories_after": [
                    {"fact": "Promoted to Senior Security Analyst", "type": "career_update", "importance": "high"},
                    {"fact": "Incident response rotation ended", "type": "temporal_update", "importance": "medium"},
                    {"fact": "Leading vulnerability management program", "type": "work", "importance": "high"},
                ],
            },
            {
                "session_id": 4,
                "turns": [
                    {"role": "user", "content": "Can you help me draft a security policy for npm package vetting? I need to present it to our CTO next week."},
                    {"role": "assistant", "content": "Of course. A good npm security policy should cover package approval workflows, automated scanning, and lockfile integrity. What's your current approval process?"},
                    {"role": "user", "content": "It's basically nonexistent — developers just install whatever they need. That's how the compromised package got through."},
                ],
                "expected_memories_after": [],
            },
            {
                "session_id": 5,
                "turns": [
                    {"role": "user", "content": "Can you give me a summary of how the security incident evolved?"},
                    {"role": "assistant", "content": "[MEMORY TEST]"},
                    {"role": "user", "content": "Am I still on incident response rotation?"},
                    {"role": "assistant", "content": "[MEMORY TEST]"},
                    {"role": "user", "content": "Do you remember about my subway commute problems?"},
                    {"role": "assistant", "content": "[MEMORY TEST]"},
                ],
                "expected_memories_after": [],
            },
        ],
        "memory_tests": [
            {
                "test_id": "omar_12_t1",
                "session": 5,
                "turn_index": 0,
                "query": "Can you give me a summary of how the security incident evolved?",
                "required_memories": [
                    "Suspicious outbound traffic from workstations",
                    "Traced to compromised npm package",
                    "Patient metadata exposed (not PHI)",
                    "5 total affected workstations",
                    "Now implementing package signing and lockfile auditing",
                ],
                "correct_answer": "The incident started with suspicious outbound traffic from workstations. You traced it to a compromised npm package in internal tooling that was siphoning patient metadata (not PHI). 5 total workstations were affected. You contained it, and now you're implementing package signing and lockfile auditing as remediation.",
                "wrong_answer": "You had a security incident involving 3 workstations.",
                "category": "consolidation",
                "notes": "Must consolidate the evolving incident across sessions 1-3.",
            },
            {
                "test_id": "omar_12_t2",
                "session": 5,
                "turn_index": 2,
                "query": "Am I still on incident response rotation?",
                "required_memories": ["Incident response rotation ended"],
                "correct_answer": "No, your incident response rotation ended. You're now back to regular duties and leading the vulnerability management program.",
                "wrong_answer": "Yes, you're on incident response this week.",
                "category": "temporal_relevance",
                "notes": "Must recognize the rotation ended.",
            },
            {
                "test_id": "omar_12_t3",
                "session": 5,
                "turn_index": 4,
                "query": "Do you remember about my subway commute problems?",
                "required_memories": [],
                "correct_answer": "I don't have that stored as a relevant memory — it was just a passing mention about signal problems on the Red Line.",
                "wrong_answer": "Yes, you had signal problems on the Red Line during your subway commute.",
                "category": "noise_resistance",
                "notes": "Subway complaint is noise — should not be stored/retrieved.",
            },
        ],
    },

    # =========================================================================
    # Profile 13: Lily Zhang - NLP Graduate Student
    # Tests: contradiction_update (thesis topic shift), consolidation (results evolve), cross_session
    # =========================================================================
    {
        "user_id": "lily_13",
        "name": "Lily Zhang",
        "description": "NLP grad student whose thesis topic shifts and results evolve",
        "sessions": [
            {
                "session_id": 1,
                "turns": [
                    {"role": "user", "content": "Hi, I'm Lily. I'm a second-year PhD student in NLP at Stanford. My advisor is Prof. Martinez and I'm researching few-shot learning for low-resource languages."},
                    {"role": "assistant", "content": "Welcome Lily! Few-shot learning for low-resource languages is a really impactful area. Which languages are you focusing on?"},
                    {"role": "user", "content": "Primarily Swahili and Yoruba. I'm using a meta-learning approach with MAML as the backbone. My first experiment got 42% F1 on NER — not great, but it's a start."},
                    {"role": "assistant", "content": "42% F1 is a reasonable starting point for low-resource NER. Have you tried data augmentation techniques?"},
                    {"role": "user", "content": "Not yet. I'm TAing for CS224N this quarter which is eating into my research time."},
                ],
                "expected_memories_after": [
                    {"fact": "Second-year PhD student in NLP at Stanford", "type": "identity", "importance": "high"},
                    {"fact": "Advisor is Prof. Martinez", "type": "academic", "importance": "high"},
                    {"fact": "Researching few-shot learning for low-resource languages (Swahili, Yoruba)", "type": "research", "importance": "high"},
                    {"fact": "Using MAML for meta-learning approach", "type": "method", "importance": "high"},
                    {"fact": "First NER experiment: 42% F1", "type": "results", "importance": "medium"},
                    {"fact": "TAing CS224N this quarter", "type": "temporal", "importance": "medium"},
                ],
            },
            {
                "session_id": 2,
                "turns": [
                    {"role": "user", "content": "I tried data augmentation and got the F1 up to 58%! But my advisor thinks we should pivot — she wants me to focus on cross-lingual transfer instead of pure few-shot learning."},
                    {"role": "assistant", "content": "58% is solid progress! Cross-lingual transfer is a natural extension — you can leverage higher-resource languages to boost low-resource ones."},
                    {"role": "user", "content": "Exactly. So my thesis is now about cross-lingual transfer learning for low-resource African languages. I'm going to use XLM-R as the backbone instead of MAML."},
                ],
                "expected_memories_after": [
                    {"fact": "NER F1 improved from 42% to 58% with augmentation", "type": "results_update", "importance": "high"},
                    {"fact": "Thesis pivoted to cross-lingual transfer learning", "type": "research_update", "importance": "high", "contradicts": "few-shot learning"},
                    {"fact": "Using XLM-R instead of MAML", "type": "method_update", "importance": "high", "contradicts": "MAML"},
                ],
            },
            {
                "session_id": 3,
                "turns": [
                    {"role": "user", "content": "Cross-lingual results are in: 71% F1 on Swahili NER with transfer from English+French! Huge improvement. Also, I'm done TAing — the quarter ended."},
                    {"role": "assistant", "content": "71% F1 is a huge jump from 58%! The multilingual transfer is clearly working. What's next?"},
                    {"role": "user", "content": "I'm submitting to EMNLP. Also extending to Amharic and Hausa — so 4 target languages now."},
                ],
                "expected_memories_after": [
                    {"fact": "71% F1 on Swahili NER with cross-lingual transfer", "type": "results_update", "importance": "high"},
                    {"fact": "TAing ended (quarter over)", "type": "temporal_update", "importance": "medium"},
                    {"fact": "Submitting to EMNLP", "type": "academic", "importance": "high"},
                    {"fact": "Extended to 4 languages: Swahili, Yoruba, Amharic, Hausa", "type": "research_update", "importance": "high"},
                ],
            },
            {
                "session_id": 4,
                "turns": [
                    {"role": "user", "content": "Can you help me write the related work section for my EMNLP paper? I need to cover cross-lingual transfer methods."},
                    {"role": "assistant", "content": "Sure! The key papers to cover would be XLM-R, mBERT analyses, and recent work on African language NLP. What's your paper's main novelty?"},
                    {"role": "user", "content": "Our contribution is a language-adaptive fine-tuning strategy that selects source languages based on typological similarity."},
                ],
                "expected_memories_after": [],
            },
            {
                "session_id": 5,
                "turns": [
                    {"role": "user", "content": "What model am I using for my thesis work?"},
                    {"role": "assistant", "content": "[MEMORY TEST]"},
                    {"role": "user", "content": "How have my NER results evolved across my experiments?"},
                    {"role": "assistant", "content": "[MEMORY TEST]"},
                    {"role": "user", "content": "Am I still TAing this quarter?"},
                    {"role": "assistant", "content": "[MEMORY TEST]"},
                ],
                "expected_memories_after": [],
            },
        ],
        "memory_tests": [
            {
                "test_id": "lily_13_t1",
                "session": 5,
                "turn_index": 0,
                "query": "What model am I using for my thesis work?",
                "required_memories": ["Using XLM-R (pivoted from MAML)"],
                "correct_answer": "You're using XLM-R for cross-lingual transfer learning. You originally used MAML for few-shot learning but your advisor suggested pivoting to cross-lingual transfer.",
                "wrong_answer": "You're using MAML for meta-learning.",
                "category": "contradiction_update",
                "notes": "Must return XLM-R, not MAML.",
            },
            {
                "test_id": "lily_13_t2",
                "session": 5,
                "turn_index": 2,
                "query": "How have my NER results evolved across my experiments?",
                "required_memories": [
                    "First experiment: 42% F1 with MAML",
                    "After augmentation: 58% F1",
                    "Cross-lingual transfer: 71% F1",
                ],
                "correct_answer": "Your NER results have steadily improved: started at 42% F1 with MAML few-shot learning, improved to 58% with data augmentation, then jumped to 71% F1 using XLM-R cross-lingual transfer from English+French to Swahili.",
                "wrong_answer": "Your latest F1 score is 71%.",
                "category": "consolidation",
                "notes": "Must consolidate results trajectory across all 3 sessions.",
            },
            {
                "test_id": "lily_13_t3",
                "session": 5,
                "turn_index": 4,
                "query": "Am I still TAing this quarter?",
                "required_memories": ["TAing ended (quarter over)"],
                "correct_answer": "No, you finished TAing CS224N — the quarter ended.",
                "wrong_answer": "Yes, you're TAing CS224N this quarter.",
                "category": "temporal_relevance",
                "notes": "Must recognize the TA assignment ended.",
            },
        ],
    },

    # =========================================================================
    # Profile 14: Thomas Okonkwo - DevOps Engineer
    # Tests: contradiction_update (cloud migration), simple_recall, noise_resistance
    # =========================================================================
    {
        "user_id": "thomas_14",
        "name": "Thomas Okonkwo",
        "description": "DevOps engineer migrating from AWS to GCP, casual mentions of sports",
        "sessions": [
            {
                "session_id": 1,
                "turns": [
                    {"role": "user", "content": "Hey, I'm Thomas. I'm a DevOps engineer at a logistics company in Lagos. We run everything on AWS — about 50 microservices on EKS."},
                    {"role": "assistant", "content": "Hi Thomas! Managing 50 microservices on EKS is no small feat. What's your current stack like?"},
                    {"role": "user", "content": "We use Terraform for IaC, ArgoCD for GitOps deployments, and Datadog for monitoring. Our CI/CD is GitHub Actions. We process about 10 million shipment tracking events daily."},
                    {"role": "assistant", "content": "That's a solid modern stack. Are you facing any particular challenges?"},
                    {"role": "user", "content": "Main pain point is cost — our AWS bill hit $85K last month. Leadership wants us to explore alternatives. Also, did you catch the Super Eagles match yesterday? 3-1 win!"},
                ],
                "expected_memories_after": [
                    {"fact": "DevOps engineer at logistics company in Lagos", "type": "profession", "importance": "high"},
                    {"fact": "Runs 50 microservices on AWS EKS", "type": "infrastructure", "importance": "high"},
                    {"fact": "Uses Terraform, ArgoCD, Datadog, GitHub Actions", "type": "tools", "importance": "high"},
                    {"fact": "10 million shipment tracking events daily", "type": "scale", "importance": "high"},
                    {"fact": "AWS bill $85K/month, exploring alternatives", "type": "work", "importance": "high"},
                ],
            },
            {
                "session_id": 2,
                "turns": [
                    {"role": "user", "content": "We did a proof of concept on GCP — migrated 5 services to GKE. The cost savings look promising, about 30% cheaper for the same workload."},
                    {"role": "assistant", "content": "30% savings is significant at your scale. How was the migration experience?"},
                    {"role": "user", "content": "Smooth actually. GKE Autopilot is great. The team liked it. We're getting buy-in from leadership to migrate fully."},
                ],
                "expected_memories_after": [
                    {"fact": "GCP PoC showed 30% cost savings", "type": "work", "importance": "high"},
                    {"fact": "Migrated 5 services to GKE as proof of concept", "type": "work", "importance": "medium"},
                ],
            },
            {
                "session_id": 3,
                "turns": [
                    {"role": "user", "content": "It's official — we're migrating fully to GCP. Already moved 30 of our 50 services to GKE. AWS is being decommissioned by end of quarter."},
                    {"role": "assistant", "content": "That's fast progress! How's the remaining 20 services looking?"},
                    {"role": "user", "content": "The tricky ones are left — our event streaming (currently Kinesis) needs to go to Pub/Sub, and our data warehouse from Redshift to BigQuery. Should be done in 6 weeks."},
                    {"role": "assistant", "content": "Those are the heavy lifts. Kinesis to Pub/Sub is usually smoother than Redshift to BigQuery."},
                    {"role": "user", "content": "Yeah. Oh, the traffic was insane today — took me 2 hours to get to the office from Lekki."},
                ],
                "expected_memories_after": [
                    {"fact": "Fully migrating to GCP from AWS", "type": "infrastructure_update", "importance": "high", "contradicts": "Runs on AWS"},
                    {"fact": "30 of 50 services already on GKE", "type": "work", "importance": "high"},
                    {"fact": "Migrating Kinesis to Pub/Sub, Redshift to BigQuery", "type": "work", "importance": "high"},
                ],
            },
            {
                "session_id": 4,
                "turns": [
                    {"role": "user", "content": "Can you help me write a runbook for the Kinesis to Pub/Sub migration? I need step-by-step procedures."},
                    {"role": "assistant", "content": "Sure! A good migration runbook should cover pre-migration validation, parallel running, cutover procedure, and rollback plan. What's your current Kinesis setup?"},
                    {"role": "user", "content": "12 streams, about 500K events per hour peak. We need zero downtime."},
                ],
                "expected_memories_after": [],
            },
            {
                "session_id": 5,
                "turns": [
                    {"role": "user", "content": "What cloud provider are we using now?"},
                    {"role": "assistant", "content": "[MEMORY TEST]"},
                    {"role": "user", "content": "How many microservices do we run?"},
                    {"role": "assistant", "content": "[MEMORY TEST]"},
                    {"role": "user", "content": "Do you remember about the traffic from Lekki?"},
                    {"role": "assistant", "content": "[MEMORY TEST]"},
                    {"role": "user", "content": "How has our cloud cost situation evolved since we started the migration?"},
                    {"role": "assistant", "content": "[MEMORY TEST]"},
                ],
                "expected_memories_after": [],
            },
        ],
        "memory_tests": [
            {
                "test_id": "thomas_14_t1",
                "session": 5,
                "turn_index": 0,
                "query": "What cloud provider are we using now?",
                "required_memories": ["Migrating from AWS to GCP"],
                "correct_answer": "You're migrating to GCP — already moved 30 of 50 services from AWS EKS to GKE, with full AWS decommission by end of quarter.",
                "wrong_answer": "You run everything on AWS.",
                "category": "contradiction_update",
                "notes": "Must reflect the GCP migration, not the original AWS setup.",
            },
            {
                "test_id": "thomas_14_t2",
                "session": 5,
                "turn_index": 2,
                "query": "How many microservices do we run?",
                "required_memories": ["50 microservices"],
                "correct_answer": "You run about 50 microservices. 30 are already migrated to GKE and the remaining 20 are in progress.",
                "wrong_answer": "I don't remember the exact number.",
                "category": "simple_recall",
                "notes": "Basic fact recall.",
            },
            {
                "test_id": "thomas_14_t3",
                "session": 5,
                "turn_index": 4,
                "query": "Do you remember about the traffic from Lekki?",
                "required_memories": [],
                "correct_answer": "I don't have that stored as a relevant memory — that was just a passing comment about your commute.",
                "wrong_answer": "Yes, it took you 2 hours to get to the office from Lekki because of traffic.",
                "category": "noise_resistance",
                "notes": "Traffic complaint is noise.",
            },
            {
                "test_id": "thomas_14_t4",
                "session": 5,
                "turn_index": 6,
                "query": "How has our cloud cost situation evolved since we started the migration?",
                "required_memories": [
                    "AWS bill was $85K/month",
                    "GCP PoC showed 30% cost savings",
                    "30 of 50 services migrated to GKE",
                    "Remaining: Kinesis to Pub/Sub, Redshift to BigQuery",
                ],
                "correct_answer": "Your AWS bill was $85K/month. The GCP proof of concept showed about 30% cost savings for equivalent workloads. You've migrated 30 of 50 services to GKE so far, with the remaining work being Kinesis to Pub/Sub and Redshift to BigQuery migrations. AWS decommission is targeted for end of quarter.",
                "wrong_answer": "Your cloud costs are $85K per month on AWS.",
                "category": "consolidation",
                "notes": "Must consolidate cost and migration progress across sessions 1-3.",
            },
        ],
    },

    # =========================================================================
    # Profile 15: Sophie Martin - Product Manager
    # Tests: consolidation (roadmap evolves), implicit_preference, cross_session
    # =========================================================================
    {
        "user_id": "sophie_15",
        "name": "Sophie Martin",
        "description": "Product manager whose roadmap priorities shift and team grows",
        "sessions": [
            {
                "session_id": 1,
                "turns": [
                    {"role": "user", "content": "Hi, I'm Sophie. I'm a product manager at an edtech company in Paris. I manage our learning analytics platform — it's used by 200+ schools."},
                    {"role": "assistant", "content": "Welcome Sophie! Learning analytics for 200+ schools is impressive. What's your main focus right now?"},
                    {"role": "user", "content": "Our Q1 priorities are: 1) Student engagement dashboard, 2) Teacher reporting tools, 3) API for third-party integrations. Team is me plus 4 engineers."},
                    {"role": "assistant", "content": "Clear priorities. How's the engineering bandwidth for all three?"},
                    {"role": "user", "content": "Tight. We can probably do #1 and #2 in Q1. The API will slip to Q2. Also, can you keep explanations short and direct? I don't need long preambles."},
                ],
                "expected_memories_after": [
                    {"fact": "Product manager at edtech company in Paris", "type": "profession", "importance": "high"},
                    {"fact": "Manages learning analytics platform for 200+ schools", "type": "work", "importance": "high"},
                    {"fact": "Team of 5 (Sophie + 4 engineers)", "type": "work", "importance": "medium"},
                    {"fact": "Q1 priorities: engagement dashboard, teacher reporting, API (API slipping to Q2)", "type": "work", "importance": "high"},
                    {"fact": "Prefers short, direct explanations — no preambles", "type": "preference", "importance": "high"},
                ],
            },
            {
                "session_id": 2,
                "turns": [
                    {"role": "user", "content": "Engagement dashboard shipped! Schools love it. But we got a big client request — a district with 50 schools wants a custom analytics module. That's now our top priority, pushing teacher reporting to Q2."},
                    {"role": "assistant", "content": "Nice win on the dashboard! Makes sense to prioritize the big client. What does the custom module need?"},
                    {"role": "user", "content": "They want district-wide aggregation with drill-down to individual schools. Think school-level heatmaps. We also just hired 2 more engineers, so team is now 7."},
                ],
                "expected_memories_after": [
                    {"fact": "Engagement dashboard shipped", "type": "work_update", "importance": "high"},
                    {"fact": "New priority: custom analytics for 50-school district", "type": "work_update", "importance": "high"},
                    {"fact": "Teacher reporting pushed to Q2", "type": "work_update", "importance": "medium"},
                    {"fact": "Team grew to 7 (hired 2 more engineers)", "type": "work_update", "importance": "medium"},
                ],
            },
            {
                "session_id": 3,
                "turns": [
                    {"role": "user", "content": "The district module is in beta. They're testing with 10 schools first. Meanwhile, I'm getting pressure from our CEO to start on the API — partners are waiting."},
                    {"role": "assistant", "content": "Beta with 10 schools is a good phased approach. What's the timeline for the API now?"},
                    {"role": "user", "content": "We need to ship API v1 by end of Q2. I'm splitting the team — 4 on the district module, 3 on API."},
                ],
                "expected_memories_after": [
                    {"fact": "District module in beta (10 schools)", "type": "work_update", "importance": "high"},
                    {"fact": "API v1 must ship by end of Q2", "type": "work", "importance": "high"},
                    {"fact": "Team split: 4 on district, 3 on API", "type": "work", "importance": "medium"},
                ],
            },
            {
                "session_id": 4,
                "turns": [
                    {"role": "user", "content": "Can you help me draft user stories for the API? I need endpoints for student data, class performance, and attendance."},
                    {"role": "assistant", "content": "Sure. For the student data endpoint, we'd want GET /students/{id}/analytics with query params for date ranges and metric types. Should it support bulk queries?"},
                    {"role": "user", "content": "Yes, bulk is essential — schools will want to pull data for entire classes. Keep the response JSON clean and flat, not deeply nested."},
                ],
                "expected_memories_after": [],
            },
            {
                "session_id": 5,
                "turns": [
                    {"role": "user", "content": "What's the full picture of how our product roadmap has evolved?"},
                    {"role": "assistant", "content": "[MEMORY TEST]"},
                    {"role": "user", "content": "How big is my team now?"},
                    {"role": "assistant", "content": "[MEMORY TEST]"},
                    {"role": "user", "content": "How do I like my information presented?"},
                    {"role": "assistant", "content": "[MEMORY TEST]"},
                ],
                "expected_memories_after": [],
            },
        ],
        "memory_tests": [
            {
                "test_id": "sophie_15_t1",
                "session": 5,
                "turn_index": 0,
                "query": "What's the full picture of how our product roadmap has evolved?",
                "required_memories": [
                    "Original Q1 priorities: dashboard, teacher reporting, API",
                    "Dashboard shipped, teacher reporting pushed to Q2",
                    "Custom district analytics became top priority",
                    "District module now in beta with 10 schools",
                    "API v1 must ship by end of Q2",
                ],
                "correct_answer": "Your roadmap evolved significantly: Original Q1 priorities were engagement dashboard, teacher reporting, and API. The dashboard shipped successfully. Then a big district client (50 schools) shifted priorities — custom analytics module became top priority, pushing teacher reporting to Q2. The district module is now in beta with 10 schools. API v1 is targeted for end of Q2, with 3 engineers working on it.",
                "wrong_answer": "Your priorities are the engagement dashboard and teacher reporting.",
                "category": "cross_session",
                "notes": "Must synthesize roadmap evolution across sessions 1-3.",
            },
            {
                "test_id": "sophie_15_t2",
                "session": 5,
                "turn_index": 2,
                "query": "How big is my team now?",
                "required_memories": ["Team grew from 5 to 7 (hired 2 engineers)"],
                "correct_answer": "Your team is now 7 people — you originally had 4 engineers plus yourself, then hired 2 more. Currently split 4 on the district module and 3 on the API.",
                "wrong_answer": "You have a team of 5 — you plus 4 engineers.",
                "category": "contradiction_update",
                "notes": "Must return updated team size of 7, not original 5.",
            },
            {
                "test_id": "sophie_15_t3",
                "session": 5,
                "turn_index": 4,
                "query": "How do I like my information presented?",
                "required_memories": ["Prefers short direct explanations", "No preambles"],
                "correct_answer": "You want things short and direct — no long preambles. You told me to keep explanations concise.",
                "wrong_answer": "I'll present information in a clear and thorough way.",
                "category": "implicit_preference",
                "notes": "Sophie explicitly stated this preference once in session 1.",
            },
        ],
    },

    # =========================================================================
    # Profile 16: Raj Krishnamurthy - Mobile Developer
    # Tests: contradiction_update (framework switch), consolidation (app metrics evolve), simple_recall
    # =========================================================================
    {
        "user_id": "raj_16",
        "name": "Raj Krishnamurthy",
        "description": "Mobile developer switching from React Native to Flutter, app launch across sessions",
        "sessions": [
            {
                "session_id": 1,
                "turns": [
                    {"role": "user", "content": "Hey! I'm Raj, a mobile developer at a health-tech startup in Bangalore. I build our patient engagement app using React Native."},
                    {"role": "assistant", "content": "Hi Raj! Health-tech mobile apps are important work. How's the React Native experience for healthcare?"},
                    {"role": "user", "content": "It's okay but we're struggling with performance on older Android devices. Our app has about 15K monthly active users. The main feature is appointment booking and medication reminders."},
                    {"role": "assistant", "content": "Older Android devices are a common pain point with React Native. Have you tried Hermes engine?"},
                    {"role": "user", "content": "We have Hermes on, but the real issue is our complex animations on the medication tracker screen. The frame drops are noticeable."},
                ],
                "expected_memories_after": [
                    {"fact": "Mobile developer at health-tech startup in Bangalore", "type": "profession", "importance": "high"},
                    {"fact": "Building patient engagement app with React Native", "type": "work", "importance": "high"},
                    {"fact": "15K monthly active users", "type": "metric", "importance": "high"},
                    {"fact": "Performance issues on older Android devices", "type": "work", "importance": "medium"},
                    {"fact": "App features: appointment booking, medication reminders", "type": "work", "importance": "high"},
                ],
            },
            {
                "session_id": 2,
                "turns": [
                    {"role": "user", "content": "We made the decision to rewrite the app in Flutter. The performance difference is night and day. I've been learning Dart for the past month."},
                    {"role": "assistant", "content": "Flutter's rendering engine definitely handles animations better. How far along is the rewrite?"},
                    {"role": "user", "content": "About 40% done. I've rebuilt the appointment booking module and it's buttery smooth even on budget phones. The medication tracker is next."},
                ],
                "expected_memories_after": [
                    {"fact": "Switched from React Native to Flutter", "type": "tool_update", "importance": "high", "contradicts": "React Native"},
                    {"fact": "Rewrite is 40% complete", "type": "work", "importance": "medium"},
                    {"fact": "Learning Dart", "type": "skill", "importance": "medium"},
                ],
            },
            {
                "session_id": 3,
                "turns": [
                    {"role": "user", "content": "Flutter app launched last week! We've already hit 22K MAU — up from 15K with the old app. The Play Store rating went from 3.8 to 4.6 stars."},
                    {"role": "assistant", "content": "That's a fantastic launch! The performance improvements clearly resonated with users."},
                    {"role": "user", "content": "Yeah, and crash rate dropped from 2.1% to 0.3%. The CTO is thrilled. We're now planning to add a telemedicine video call feature."},
                ],
                "expected_memories_after": [
                    {"fact": "Flutter app launched, 22K MAU (up from 15K)", "type": "metric_update", "importance": "high"},
                    {"fact": "Play Store rating: 4.6 stars (up from 3.8)", "type": "metric_update", "importance": "high"},
                    {"fact": "Crash rate: 0.3% (down from 2.1%)", "type": "metric_update", "importance": "high"},
                    {"fact": "Planning telemedicine video call feature", "type": "work", "importance": "medium"},
                ],
            },
            {
                "session_id": 4,
                "turns": [
                    {"role": "user", "content": "Can you help me evaluate WebRTC packages for Flutter? I need to add video calling for the telemedicine feature."},
                    {"role": "assistant", "content": "The main options are flutter_webrtc and agora_rtc_engine. flutter_webrtc is open source, agora is a managed service. What's your priority?"},
                    {"role": "user", "content": "Reliability is key — patients connecting with doctors can't have call drops. Budget is flexible."},
                ],
                "expected_memories_after": [],
            },
            {
                "session_id": 5,
                "turns": [
                    {"role": "user", "content": "What framework am I using for our app?"},
                    {"role": "assistant", "content": "[MEMORY TEST]"},
                    {"role": "user", "content": "How have our app metrics changed since the rewrite?"},
                    {"role": "assistant", "content": "[MEMORY TEST]"},
                    {"role": "user", "content": "What are the main features of our app?"},
                    {"role": "assistant", "content": "[MEMORY TEST]"},
                    {"role": "user", "content": "Is the Flutter rewrite still in progress?"},
                    {"role": "assistant", "content": "[MEMORY TEST]"},
                ],
                "expected_memories_after": [],
            },
        ],
        "memory_tests": [
            {
                "test_id": "raj_16_t1",
                "session": 5,
                "turn_index": 0,
                "query": "What framework am I using for our app?",
                "required_memories": ["Switched from React Native to Flutter"],
                "correct_answer": "You're using Flutter now. You switched from React Native because of performance issues on older Android devices — the rewrite launched and is doing great.",
                "wrong_answer": "You're using React Native.",
                "category": "contradiction_update",
                "notes": "Must return Flutter, not React Native.",
            },
            {
                "test_id": "raj_16_t2",
                "session": 5,
                "turn_index": 2,
                "query": "How have our app metrics changed since the rewrite?",
                "required_memories": [
                    "MAU: 15K to 22K",
                    "Play Store rating: 3.8 to 4.6",
                    "Crash rate: 2.1% to 0.3%",
                ],
                "correct_answer": "The Flutter rewrite had a big impact: MAU grew from 15K to 22K, Play Store rating went from 3.8 to 4.6 stars, and crash rate dropped from 2.1% to 0.3%.",
                "wrong_answer": "Your app has 22K monthly active users.",
                "category": "consolidation",
                "notes": "Must consolidate before/after metrics across sessions.",
            },
            {
                "test_id": "raj_16_t3",
                "session": 5,
                "turn_index": 4,
                "query": "What are the main features of our app?",
                "required_memories": ["Appointment booking", "Medication reminders", "Planning telemedicine video calls"],
                "correct_answer": "Your patient engagement app has appointment booking, medication reminders, and you're now adding a telemedicine video call feature.",
                "wrong_answer": "It's a health app.",
                "category": "simple_recall",
                "notes": "Basic feature recall.",
            },
            {
                "test_id": "raj_16_t4",
                "session": 5,
                "turn_index": 6,
                "query": "Is the Flutter rewrite still in progress?",
                "required_memories": ["Flutter app launched", "22K MAU", "Play Store rating 4.6"],
                "correct_answer": "No, the Flutter rewrite is done! The app launched and is performing great — 22K MAU, 4.6 stars on Play Store, 0.3% crash rate. You're now working on adding telemedicine video calls.",
                "wrong_answer": "Yes, the rewrite is about 40% done. You've rebuilt the appointment booking module.",
                "category": "temporal_relevance",
                "notes": "Must recognize the rewrite completed and app launched. Stale info would be '40% done'.",
            },
        ],
    },

    # =========================================================================
    # Profile 17: Hannah Kim - Clinical Researcher
    # Tests: temporal_relevance (IRB status changes), implicit_preference, cross_session
    # =========================================================================
    {
        "user_id": "hannah_17",
        "name": "Hannah Kim",
        "description": "Clinical researcher with evolving IRB status and study phases",
        "sessions": [
            {
                "session_id": 1,
                "turns": [
                    {"role": "user", "content": "Hi, I'm Hannah. I'm a clinical research coordinator at Johns Hopkins. I'm running a Phase II trial for a new Alzheimer's drug."},
                    {"role": "assistant", "content": "That's important work, Hannah. What phase is the trial in?"},
                    {"role": "user", "content": "We're in the screening phase — recruiting patients. Our target is 120 participants. We have 43 so far. The IRB amendment for expanding inclusion criteria is still pending — been waiting 3 weeks."},
                    {"role": "assistant", "content": "43 of 120 is solid progress. The IRB wait can be frustrating. What inclusion criteria are you trying to expand?"},
                    {"role": "user", "content": "We want to include patients aged 55-80 instead of 60-75. The data safety board thinks the broader range is safe. I always prefer when you give me numbered lists — it helps me track action items."},
                ],
                "expected_memories_after": [
                    {"fact": "Clinical research coordinator at Johns Hopkins", "type": "profession", "importance": "high"},
                    {"fact": "Running Phase II Alzheimer's drug trial", "type": "work", "importance": "high"},
                    {"fact": "Target 120 participants, have 43", "type": "work", "importance": "high"},
                    {"fact": "IRB amendment pending for expanding age criteria", "type": "temporal", "importance": "medium"},
                    {"fact": "Prefers numbered lists for action items", "type": "preference", "importance": "high"},
                ],
            },
            {
                "session_id": 2,
                "turns": [
                    {"role": "user", "content": "IRB amendment was approved! We can now include ages 55-80. Expecting recruitment to speed up significantly."},
                    {"role": "assistant", "content": "That's great news! The expanded criteria should definitely help with enrollment."},
                    {"role": "user", "content": "Yeah, we jumped from 43 to 67 participants in just two weeks after the approval."},
                ],
                "expected_memories_after": [
                    {"fact": "IRB amendment approved (no longer pending)", "type": "temporal_update", "importance": "high"},
                    {"fact": "Participants: 67 (up from 43)", "type": "work_update", "importance": "high"},
                ],
            },
            {
                "session_id": 3,
                "turns": [
                    {"role": "user", "content": "We hit 120 participants! Screening phase is done. We're moving into the treatment phase next week. Randomization is complete."},
                    {"role": "assistant", "content": "Congratulations on hitting your enrollment target! The transition to treatment phase is exciting."},
                    {"role": "user", "content": "Thank you. It's a 12-week treatment period with bi-weekly assessments. I need to set up the data collection schedule."},
                ],
                "expected_memories_after": [
                    {"fact": "Enrollment complete (120 participants)", "type": "work_update", "importance": "high"},
                    {"fact": "Moving from screening to treatment phase", "type": "work_update", "importance": "high"},
                    {"fact": "12-week treatment, bi-weekly assessments", "type": "work", "importance": "high"},
                ],
            },
            {
                "session_id": 4,
                "turns": [
                    {"role": "user", "content": "Can you help me create a data collection schedule template? I need to track cognitive assessments, blood work, and adverse events."},
                    {"role": "assistant", "content": "Sure! For a 12-week trial with bi-weekly visits, that's 7 assessment points. What cognitive assessments are you using?"},
                    {"role": "user", "content": "ADAS-Cog and MMSE at every visit, plus MoCA at baseline and week 12."},
                ],
                "expected_memories_after": [],
            },
            {
                "session_id": 5,
                "turns": [
                    {"role": "user", "content": "Is the IRB amendment still pending?"},
                    {"role": "assistant", "content": "[MEMORY TEST]"},
                    {"role": "user", "content": "How do I prefer you format your responses?"},
                    {"role": "assistant", "content": "[MEMORY TEST]"},
                    {"role": "user", "content": "What's the full timeline of our trial enrollment?"},
                    {"role": "assistant", "content": "[MEMORY TEST]"},
                ],
                "expected_memories_after": [],
            },
        ],
        "memory_tests": [
            {
                "test_id": "hannah_17_t1",
                "session": 5,
                "turn_index": 0,
                "query": "Is the IRB amendment still pending?",
                "required_memories": ["IRB amendment was approved"],
                "correct_answer": "No, the IRB amendment was approved. You expanded inclusion criteria to ages 55-80 and it helped you reach your enrollment target.",
                "wrong_answer": "Yes, you're still waiting on the IRB amendment.",
                "category": "temporal_relevance",
                "notes": "Must recognize the IRB status changed from pending to approved.",
            },
            {
                "test_id": "hannah_17_t2",
                "session": 5,
                "turn_index": 2,
                "query": "How do I prefer you format your responses?",
                "required_memories": ["Prefers numbered lists for action items"],
                "correct_answer": "You prefer numbered lists — they help you track action items.",
                "wrong_answer": "I'll format things clearly for you.",
                "category": "implicit_preference",
                "notes": "Stated preference for numbered lists.",
            },
            {
                "test_id": "hannah_17_t3",
                "session": 5,
                "turn_index": 4,
                "query": "What's the full timeline of our trial enrollment?",
                "required_memories": [
                    "Started with 43 participants",
                    "IRB amendment approved, expanded age range",
                    "Jumped to 67 after approval",
                    "Reached 120, moved to treatment phase",
                ],
                "correct_answer": "You started with 43 of 120 target participants. After the IRB amendment was approved (expanding age criteria to 55-80), enrollment jumped to 67 in two weeks. You then reached the full 120 target and moved from screening to the treatment phase with 12-week bi-weekly assessments.",
                "wrong_answer": "You enrolled 120 participants.",
                "category": "cross_session",
                "notes": "Must synthesize enrollment timeline across sessions 1-3.",
            },
        ],
    },

    # =========================================================================
    # Profile 18: Diego Fernandez - Game Developer
    # Tests: contradiction_update (engine switch), simple_recall, noise_resistance
    # =========================================================================
    {
        "user_id": "diego_18",
        "name": "Diego Fernandez",
        "description": "Game developer switching engines, mentions unrelated food/sports",
        "sessions": [
            {
                "session_id": 1,
                "turns": [
                    {"role": "user", "content": "Hey! I'm Diego, an indie game developer in Buenos Aires. I'm working on a roguelike deckbuilder using Unity and C#."},
                    {"role": "assistant", "content": "Cool project! Roguelike deckbuilders are popular right now. What's the game's concept?"},
                    {"role": "user", "content": "It's set in a cyberpunk Buenos Aires. You play as a hacker building a deck of exploit cards. The working title is 'Netrunner's Gambit'. I'm about 6 months into development."},
                    {"role": "assistant", "content": "Love the theme! How far along is the gameplay loop?"},
                    {"role": "user", "content": "Core card mechanics work, basic enemy AI is in. Need to build the procedural map generation. Oh, I had the best empanadas at a new place today — sorry, random. Had 3 different fillings."},
                ],
                "expected_memories_after": [
                    {"fact": "Indie game developer in Buenos Aires", "type": "profession", "importance": "high"},
                    {"fact": "Building roguelike deckbuilder called Netrunner's Gambit", "type": "work", "importance": "high"},
                    {"fact": "Uses Unity and C#", "type": "tool", "importance": "high"},
                    {"fact": "Cyberpunk Buenos Aires setting, hacker with exploit cards", "type": "work", "importance": "high"},
                    {"fact": "6 months into development", "type": "work", "importance": "medium"},
                ],
            },
            {
                "session_id": 2,
                "turns": [
                    {"role": "user", "content": "I built the procedural map system using a wave function collapse algorithm. Maps feel really varied now. Also added 30 unique cards."},
                    {"role": "assistant", "content": "WFC is great for procedural generation. How's the card variety feeling?"},
                    {"role": "user", "content": "Good mix of attack, defense, and utility cards. But I'm hitting Unity performance issues — frame drops on maps with lots of particle effects."},
                ],
                "expected_memories_after": [
                    {"fact": "Procedural maps using wave function collapse", "type": "work", "importance": "medium"},
                    {"fact": "30 unique cards (attack, defense, utility)", "type": "work", "importance": "medium"},
                    {"fact": "Unity performance issues with particle effects", "type": "work", "importance": "medium"},
                ],
            },
            {
                "session_id": 3,
                "turns": [
                    {"role": "user", "content": "I made a big decision — I'm switching from Unity to Godot. The Unity pricing controversy was the last straw, and Godot 4's performance is actually better for 2D. I've already ported the card system."},
                    {"role": "assistant", "content": "A lot of indie devs are making that switch. How's the Godot port going?"},
                    {"role": "user", "content": "Surprisingly smooth. GDScript is nice — less boilerplate than C#. The particle performance is already better. I'm rewriting in GDScript instead of using C# in Godot."},
                    {"role": "assistant", "content": "GDScript's integration with the engine is really tight."},
                    {"role": "user", "content": "Yeah. Oh, River Plate won last night — 4-0! What a match."},
                ],
                "expected_memories_after": [
                    {"fact": "Switched from Unity/C# to Godot/GDScript", "type": "tool_update", "importance": "high", "contradicts": "Uses Unity and C#"},
                    {"fact": "Particle performance already better in Godot", "type": "work", "importance": "medium"},
                ],
            },
            {
                "session_id": 4,
                "turns": [
                    {"role": "user", "content": "Can you help me implement the boss fight system in Godot? I want bosses to have unique card decks that counter the player's strategy."},
                    {"role": "assistant", "content": "That's a great design — adaptive bosses add a lot of replayability. We can use Godot's state machine pattern for boss phases."},
                    {"role": "user", "content": "Perfect. Each boss should have 3 phases that unlock as their HP drops."},
                ],
                "expected_memories_after": [],
            },
            {
                "session_id": 5,
                "turns": [
                    {"role": "user", "content": "What game engine and language am I using?"},
                    {"role": "assistant", "content": "[MEMORY TEST]"},
                    {"role": "user", "content": "What's the name and genre of my game?"},
                    {"role": "assistant", "content": "[MEMORY TEST]"},
                    {"role": "user", "content": "Do you remember about the empanadas?"},
                    {"role": "assistant", "content": "[MEMORY TEST]"},
                ],
                "expected_memories_after": [],
            },
        ],
        "memory_tests": [
            {
                "test_id": "diego_18_t1",
                "session": 5,
                "turn_index": 0,
                "query": "What game engine and language am I using?",
                "required_memories": ["Switched from Unity/C# to Godot/GDScript"],
                "correct_answer": "You're using Godot with GDScript now. You switched from Unity and C# because of pricing concerns and better 2D performance in Godot 4.",
                "wrong_answer": "You're using Unity with C#.",
                "category": "contradiction_update",
                "notes": "Must return Godot/GDScript, not Unity/C#.",
            },
            {
                "test_id": "diego_18_t2",
                "session": 5,
                "turn_index": 2,
                "query": "What's the name and genre of my game?",
                "required_memories": ["Netrunner's Gambit", "Roguelike deckbuilder"],
                "correct_answer": "Your game is called Netrunner's Gambit — it's a roguelike deckbuilder set in cyberpunk Buenos Aires where you play as a hacker building a deck of exploit cards.",
                "wrong_answer": "You're making a card game.",
                "category": "simple_recall",
                "notes": "Basic fact recall of game name and genre.",
            },
            {
                "test_id": "diego_18_t3",
                "session": 5,
                "turn_index": 4,
                "query": "Do you remember about the empanadas?",
                "required_memories": [],
                "correct_answer": "I don't have that stored as relevant — that was just casual conversation about food.",
                "wrong_answer": "Yes! You had amazing empanadas with 3 different fillings at a new place.",
                "category": "noise_resistance",
                "notes": "Empanada mention is noise.",
            },
        ],
    },

    # =========================================================================
    # Profile 19: Amara Osei - ML Infrastructure Engineer
    # Tests: consolidation (GPU cluster evolves), contradiction_update, implicit_preference
    # =========================================================================
    {
        "user_id": "amara_19",
        "name": "Amara Osei",
        "description": "ML infra engineer managing evolving GPU cluster and deployment framework",
        "sessions": [
            {
                "session_id": 1,
                "turns": [
                    {"role": "user", "content": "Hi, I'm Amara. I'm an ML infrastructure engineer at a self-driving car company in Detroit. I manage our training cluster — 64 A100 GPUs across 8 nodes."},
                    {"role": "assistant", "content": "That's a serious cluster! What framework are you using for distributed training?"},
                    {"role": "user", "content": "We use DeepSpeed with PyTorch. Our main model is a vision transformer for object detection. Training takes about 72 hours on the full cluster. I usually need step-by-step details, not just high-level summaries."},
                    {"role": "assistant", "content": "72 hours on 64 A100s — that's a big model. What's the parameter count?"},
                    {"role": "user", "content": "1.2 billion parameters. We're at 89.3% mAP on our internal benchmark."},
                ],
                "expected_memories_after": [
                    {"fact": "ML infrastructure engineer at self-driving car company in Detroit", "type": "profession", "importance": "high"},
                    {"fact": "Manages training cluster: 64 A100 GPUs, 8 nodes", "type": "infrastructure", "importance": "high"},
                    {"fact": "Uses DeepSpeed with PyTorch", "type": "tool", "importance": "high"},
                    {"fact": "Main model: 1.2B param vision transformer, 89.3% mAP", "type": "work", "importance": "high"},
                    {"fact": "Prefers step-by-step details over high-level summaries", "type": "preference", "importance": "high"},
                ],
            },
            {
                "session_id": 2,
                "turns": [
                    {"role": "user", "content": "Big upgrade — we just added 32 H100 GPUs. Total cluster is now 64 A100s + 32 H100s. Training time dropped from 72 hours to 41 hours with the mixed cluster."},
                    {"role": "assistant", "content": "That's a significant speedup. Are you running mixed precision across both GPU types?"},
                    {"role": "user", "content": "Yes, bf16 on both. The H100s handle the attention layers and A100s do the backbone. We also hit 91.1% mAP with the faster iteration cycle."},
                ],
                "expected_memories_after": [
                    {"fact": "Cluster expanded: 64 A100s + 32 H100s", "type": "infrastructure_update", "importance": "high"},
                    {"fact": "Training time dropped from 72h to 41h", "type": "metric_update", "importance": "high"},
                    {"fact": "mAP improved from 89.3% to 91.1%", "type": "metric_update", "importance": "high"},
                ],
            },
            {
                "session_id": 3,
                "turns": [
                    {"role": "user", "content": "We're switching from DeepSpeed to FSDP — PyTorch's native FSDP has caught up and it's simpler to maintain. Also, our mAP hit 93.5% with the latest architecture changes."},
                    {"role": "assistant", "content": "FSDP has improved a lot. The simpler stack should help with maintenance. 93.5% mAP is impressive!"},
                    {"role": "user", "content": "Yeah, we're close to production deployment. The model needs to run inference under 50ms per frame."},
                ],
                "expected_memories_after": [
                    {"fact": "Switched from DeepSpeed to PyTorch FSDP", "type": "tool_update", "importance": "high", "contradicts": "Uses DeepSpeed"},
                    {"fact": "mAP now 93.5%", "type": "metric_update", "importance": "high"},
                    {"fact": "Need inference under 50ms per frame for production", "type": "work", "importance": "high"},
                ],
            },
            {
                "session_id": 4,
                "turns": [
                    {"role": "user", "content": "Can you help me optimize our model for TensorRT? I need to get inference below 50ms."},
                    {"role": "assistant", "content": "For TensorRT optimization, we should focus on layer fusion, INT8 quantization calibration, and dynamic batching. What's the current inference time?"},
                    {"role": "user", "content": "Currently at 78ms on a single A100. Need to get it under 50ms without losing more than 0.5% mAP."},
                ],
                "expected_memories_after": [],
            },
            {
                "session_id": 5,
                "turns": [
                    {"role": "user", "content": "What distributed training framework are we using now?"},
                    {"role": "assistant", "content": "[MEMORY TEST]"},
                    {"role": "user", "content": "How has our model's performance evolved over time?"},
                    {"role": "assistant", "content": "[MEMORY TEST]"},
                    {"role": "user", "content": "How do I prefer you explain things to me?"},
                    {"role": "assistant", "content": "[MEMORY TEST]"},
                ],
                "expected_memories_after": [],
            },
        ],
        "memory_tests": [
            {
                "test_id": "amara_19_t1",
                "session": 5,
                "turn_index": 0,
                "query": "What distributed training framework are we using now?",
                "required_memories": ["Switched from DeepSpeed to PyTorch FSDP"],
                "correct_answer": "You switched to PyTorch's native FSDP from DeepSpeed — it's caught up in capabilities and is simpler to maintain.",
                "wrong_answer": "You use DeepSpeed with PyTorch.",
                "category": "contradiction_update",
                "notes": "Must return FSDP, not DeepSpeed.",
            },
            {
                "test_id": "amara_19_t2",
                "session": 5,
                "turn_index": 2,
                "query": "How has our model's performance evolved over time?",
                "required_memories": [
                    "Started at 89.3% mAP",
                    "Improved to 91.1% with H100 cluster expansion",
                    "Latest: 93.5% with architecture changes",
                ],
                "correct_answer": "Your vision transformer's mAP has steadily improved: started at 89.3%, went to 91.1% after adding H100 GPUs to the cluster, and now sits at 93.5% after architecture changes. You're close to production deployment.",
                "wrong_answer": "Your model has 93.5% mAP.",
                "category": "consolidation",
                "notes": "Must consolidate the performance evolution across sessions.",
            },
            {
                "test_id": "amara_19_t3",
                "session": 5,
                "turn_index": 4,
                "query": "How do I prefer you explain things to me?",
                "required_memories": ["Prefers step-by-step details, not high-level summaries"],
                "correct_answer": "You prefer step-by-step detailed explanations rather than just high-level summaries.",
                "wrong_answer": "I'll explain things clearly.",
                "category": "implicit_preference",
                "notes": "Explicit preference stated in session 1.",
            },
        ],
    },

    # =========================================================================
    # Profile 20: Ben Nakamura - Technical Writer
    # Tests: contradiction_update (CMS change), cross_session (doc scope evolves), simple_recall
    # =========================================================================
    {
        "user_id": "ben_20",
        "name": "Ben Nakamura",
        "description": "Technical writer switching CMS and evolving documentation scope",
        "sessions": [
            {
                "session_id": 1,
                "turns": [
                    {"role": "user", "content": "Hey, I'm Ben. I'm a technical writer at a developer tools company in Seattle. I own all our API documentation — about 150 endpoints across 3 products."},
                    {"role": "assistant", "content": "That's a lot of docs to manage! What tools do you use for documentation?"},
                    {"role": "user", "content": "We use GitBook for hosting and Markdown for writing. Our docs get about 50K page views per month. I'm the only tech writer — the rest of the content comes from engineers."},
                    {"role": "assistant", "content": "Being the sole tech writer for 150 endpoints is intense. How's the quality?"},
                    {"role": "user", "content": "Honestly, inconsistent. Engineers write docs differently and I can't review everything. I need to standardize our style."},
                ],
                "expected_memories_after": [
                    {"fact": "Technical writer at developer tools company in Seattle", "type": "profession", "importance": "high"},
                    {"fact": "Owns API documentation: 150 endpoints, 3 products", "type": "work", "importance": "high"},
                    {"fact": "Uses GitBook and Markdown", "type": "tool", "importance": "high"},
                    {"fact": "50K page views/month", "type": "metric", "importance": "medium"},
                    {"fact": "Solo tech writer, quality inconsistency from engineer-written docs", "type": "work", "importance": "high"},
                ],
            },
            {
                "session_id": 2,
                "turns": [
                    {"role": "user", "content": "I created a style guide and it's helping. Engineer PRs are now more consistent. Also, I started adding interactive code examples — Swagger UI integrated into the docs."},
                    {"role": "assistant", "content": "Great progress! Interactive examples significantly improve developer experience."},
                    {"role": "user", "content": "Yeah, our docs satisfaction survey went from 3.2 to 3.8 out of 5. But I'm still struggling with GitBook's limitations — the search is terrible and versioning is clunky."},
                ],
                "expected_memories_after": [
                    {"fact": "Created style guide for consistency", "type": "work", "importance": "medium"},
                    {"fact": "Added interactive Swagger UI examples", "type": "work", "importance": "medium"},
                    {"fact": "Satisfaction: 3.2 to 3.8 out of 5", "type": "metric_update", "importance": "high"},
                    {"fact": "Frustrated with GitBook limitations (search, versioning)", "type": "work", "importance": "medium"},
                ],
            },
            {
                "session_id": 3,
                "turns": [
                    {"role": "user", "content": "We're migrating from GitBook to Docusaurus! I got buy-in after demoing the search and versioning capabilities. The migration is halfway done — Products 1 and 2 are migrated."},
                    {"role": "assistant", "content": "Docusaurus is a big upgrade for developer docs. How's the migration going?"},
                    {"role": "user", "content": "Smoothly. We also added a fourth product, so I'm now covering 200 endpoints across 4 products. Hired a junior tech writer to help me out — no longer solo!"},
                ],
                "expected_memories_after": [
                    {"fact": "Switched from GitBook to Docusaurus", "type": "tool_update", "importance": "high", "contradicts": "Uses GitBook"},
                    {"fact": "Now 200 endpoints across 4 products (up from 150/3)", "type": "work_update", "importance": "high"},
                    {"fact": "Hired junior tech writer — team of 2", "type": "work_update", "importance": "medium"},
                ],
            },
            {
                "session_id": 4,
                "turns": [
                    {"role": "user", "content": "Can you help me set up automated API doc generation from OpenAPI specs in Docusaurus?"},
                    {"role": "assistant", "content": "Sure! docusaurus-openapi-docs is the standard plugin for this. It generates interactive docs from your OpenAPI/Swagger specs."},
                    {"role": "user", "content": "Perfect. I want it to auto-generate but let us override sections with custom Markdown for better explanations."},
                ],
                "expected_memories_after": [],
            },
            {
                "session_id": 5,
                "turns": [
                    {"role": "user", "content": "What documentation platform are we using?"},
                    {"role": "assistant", "content": "[MEMORY TEST]"},
                    {"role": "user", "content": "How has our documentation scope changed over time?"},
                    {"role": "assistant", "content": "[MEMORY TEST]"},
                    {"role": "user", "content": "How many page views do our docs get?"},
                    {"role": "assistant", "content": "[MEMORY TEST]"},
                ],
                "expected_memories_after": [],
            },
        ],
        "memory_tests": [
            {
                "test_id": "ben_20_t1",
                "session": 5,
                "turn_index": 0,
                "query": "What documentation platform are we using?",
                "required_memories": ["Switched from GitBook to Docusaurus"],
                "correct_answer": "You migrated to Docusaurus from GitBook because of better search and versioning capabilities. Products 1 and 2 are already migrated.",
                "wrong_answer": "You use GitBook for documentation.",
                "category": "contradiction_update",
                "notes": "Must return Docusaurus, not GitBook.",
            },
            {
                "test_id": "ben_20_t2",
                "session": 5,
                "turn_index": 2,
                "query": "How has our documentation scope changed over time?",
                "required_memories": [
                    "Started with 150 endpoints across 3 products",
                    "Now 200 endpoints across 4 products",
                    "Was solo, now has junior tech writer",
                    "Created style guide, added interactive examples",
                    "Satisfaction went from 3.2 to 3.8",
                ],
                "correct_answer": "Your docs have grown significantly: started with 150 endpoints across 3 products, now 200 endpoints across 4 products. You created a style guide, added interactive Swagger examples, and docs satisfaction went from 3.2 to 3.8/5. You also hired a junior tech writer so you're no longer solo.",
                "wrong_answer": "You cover 150 endpoints across 3 products.",
                "category": "cross_session",
                "notes": "Must synthesize the evolution of scope and quality across sessions.",
            },
            {
                "test_id": "ben_20_t3",
                "session": 5,
                "turn_index": 4,
                "query": "How many page views do our docs get?",
                "required_memories": ["50K page views per month"],
                "correct_answer": "Your docs get about 50K page views per month.",
                "wrong_answer": "I don't remember the exact traffic numbers.",
                "category": "simple_recall",
                "notes": "Basic metric recall from session 1.",
            },
        ],
    },
]


# ============================================================================
# Convenience accessors
# ============================================================================

def get_all_tests():
    """Return flat list of all memory tests across all profiles."""
    tests = []
    for profile in PROFILES:
        for test in profile["memory_tests"]:
            test_with_context = {**test, "user_id": profile["user_id"], "user_name": profile["name"]}
            tests.append(test_with_context)
    return tests


def get_tests_by_category():
    """Return tests grouped by failure category."""
    by_cat = {cat: [] for cat in FAILURE_CATEGORIES}
    for test in get_all_tests():
        cat = test["category"]
        if cat in by_cat:
            by_cat[cat].append(test)
    return by_cat


def get_sessions_for_user(user_id):
    """Return all sessions for a given user."""
    for profile in PROFILES:
        if profile["user_id"] == user_id:
            return profile["sessions"]
    return []


def get_conversation_up_to_session(user_id, session_id):
    """Return all conversation turns up to and including the given session."""
    sessions = get_sessions_for_user(user_id)
    turns = []
    for session in sessions:
        if session["session_id"] <= session_id:
            turns.extend(session["turns"])
    return turns
