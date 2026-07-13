# Siddharth's Mentoring Analysis — July 13, 2026

> Based on the full transcript of AI/ML Training session (1h 30m, Teams meeting)

---

## Mentoring Style Assessment

### What's Working

**First principles all the way down.** Siddharth doesn't let trainees hide behind buzzwords. "MCP" isn't an answer until they can explain what problem it solves. Most mentors would accept "we'll use MCP" and move on. He makes them sit in the discomfort of not knowing.

**"How would YOU do it as a human first?" framing.** The PDF extraction example — "you have eyes, you can click, you can do that. Now automate it." This is the essence of AI engineering: automate what you understand manually.

**Real-world analogies.** The Udupi Hotel billing system, the 3-agent architecture, "you are a data engineer working for Purely Pickles" — all concrete, relatable scenarios.

### What's Costing Energy

**Teaching 3 people with vastly different starting points in the same room.** Ganesh is asking semi-reasonable questions, Dakshinya is on her phone, Himaya is silent. That's a classroom management problem, not a curriculum problem.

**The 30-minute "how do you run a Python script?" ordeal.** That's not a teaching failure — that's a hiring failure. Someone training to be an AI engineer should know what a terminal is.

---

## Key Siddharth Phrases & Methods

- "How will you design this? How many agents? What will be the tool call?"
- "Think how will I do it first. You can upload that to AI, then maybe you can build it for AI."
- "Don't remember the words, remember what it means."
- "It's a simple question — I'm asking a simple question."
- "You don't know the answer? It's okay. Tell the dumbest answer also. Whatever you answer will help me understand how much you understood."
- "Tomorrow I want to see the same thing. How many agents? What is the architecture? What is the purpose?"
- "Guys, guys, guys, it's a simple question. You have an Excel file. Where will you store it?"
- "Your brains are failed, like, or what? Store it in SQL. I thought you will know this."
- "Don't look at your phone, Dakshinya, please."
- "First principles thinking is thinking first principles. Don't think I'm asking you to launch a rocket today."

---

## Individual Trainee Assessment

### Ganesh Krishna — Most Potential, Biggest Gaps

**Strengths:**
- Actually engaged. Tried to answer every question
- Said "API" and "MCP" unprompted — surface awareness
- Understood agent vs LLM: "agents are LLMs with tool calls, bash commands, MCP"
- Knew about OpenPyXL preserving formats — did actual research

**Weaknesses:**
- Couldn't articulate "how many agents" for his own use case (Excel agent)
- Took 30 minutes to say "terminal/bash" for running Python
- Pyspark for a 5-row Excel file — no sense of tool-problem fit
- Architecture thinking is zero. Collecting tools, not designing systems

**Verdict:** Junior exposed to buzzwords but never built anything end-to-end. Knows WHAT tools exist but not WHEN to use them. With structure, could be good.

---

### Dakshinya Nachimuthu — Red Flag

**Strengths:**
- Understood the RAG source-classification use case conceptually
- Knew JSON is how LLMs output tokens

**Weaknesses:**
- **On her phone during the session.** Siddharth had to call her out
- Said MCP's role is "so you don't need to load the data again" — completely wrong
- Couldn't explain what MCP actually does after a 1-hour explanation on Friday
- Memorizing words, not understanding concepts
- Zero retention: Friday's MCP lesson → Monday's blank stare

**Key quote from Siddharth:** "I'll explain to you on Friday. I spent one hour explaining to you. I'm just testing how much you understood."

**Verdict:** Checked out or material is over her head. Either way — red flag.

---

### Himaya Perumal — The Unknown

**Strengths:**
- Siddharth says she's already built ML embeddings — has some technical foundation
- When she did speak: identified "two tool calls: answering + persistence" (vague but directionally correct)
- Siddharth trusts her enough to give her the restaurant analytics use case

**Weaknesses:**
- Barely spoke during the session — hard to evaluate
- No architecture thinking demonstrated
- Siddharth's own assessment: "she probably can't handle building the MCP herself — she'll die"

**Verdict:** Biggest unknown. ML background puts her ahead of the other two technically. 5-day Purely Pickles training will reveal everything.

---

## Ranked Summary

| Rank | Person | Current Level | AI Engineer Potential | Risk |
|---|---|---|---|---|
| 1 | Ganesh | Buzzword-aware, zero architecture | Medium | Tool obsession over problem-solving |
| 2 | Himaya | Built ML, doesn't speak up | Unknown — high ceiling, unproven | Might be lost or might be thinking |
| 3 | Dakshinya | Memorizing, not understanding | Low | Phone usage + 0% retention = red flag |

---

## Evaluation Criteria Framework

### 1. First Principles Breakdown (Weight: 30%)
"Given problem X, how would YOU solve it as a human? List every step."

| Score | What it looks like |
|---|---|
| 0 | "I'll use an LLM" — buzzword first |
| 1 | Lists 1-2 vague steps |
| 2 | Lists 3-4 steps, missing critical pieces |
| 3 | Complete human workflow: open file → read → extract → validate → store |
| 4 | Complete workflow + identifies which steps need automation |

### 2. Tool-Problem Fit (Weight: 20%)
"What tool solves this specific problem, and WHY?"

| Score | What it looks like |
|---|---|
| 0 | Pyspark for a 5-row Excel |
| 1 | Names right category (database, not spreadsheet) |
| 2 | Names right tool (Postgres, not MongoDB) |
| 3 | Can explain WHY |
| 4 | Can compare alternatives and justify choice |

### 3. Architecture Thinking (Weight: 25%)
"Design the system. Components? Connections? Data flow?"

| Score | What it looks like |
|---|---|
| 0 | "One agent does everything" |
| 1 | Multiple components but wrong boundaries |
| 2 | Right components but can't explain handoffs |
| 3 | Clear ownership per component + data flow |
| 4 | Handles edge cases and failure modes |

### 4. Learning Rate (Weight: 15%)
"Same question asked 2 days apart — did the answer improve?"

| Score | What it looks like |
|---|---|
| 0 | Same wrong answer (Dakshinya on MCP) |
| 1 | Slightly better phrasing, same misunderstanding |
| 2 | One misconception corrected |
| 3 | Materially better answer |
| 4 | Can explain it to someone else |

### 5. Communication (Weight: 10%)
"Can they explain their thinking clearly?"

| Score | What it looks like |
|---|---|
| 0 | Silence / "I don't know" with no attempt |
| 1 | Fragments — "API... MCP... tool call" |
| 2 | Complete sentences, logical flow |
| 3 | Can explain to non-technical person |
| 4 | Can teach the concept |

---

## Scorecard Decision Matrix

| Score | Decision |
|---|---|
| 15-20 | Accelerate — AI engineer material |
| 10-14 | Continue training, watch closely |
| 5-9 | Intervention — different approach or role |
| 0-4 | Wrong fit — don't waste time |

---

## The Fundamental Problem

Siddharth is teaching calculus to people who haven't learned algebra. Before another architecture session, each trainee should complete:

1. Build and run a Python script that reads a CSV — without AI help
2. Write a SQL query that joins two tables — in Supabase SQL editor
3. Make an API call to OpenAI/DeepSeek — raw `curl` or `requests`, no LangChain
4. Explain what happens when you type `python script.py` — what is the terminal actually doing?

If they can't do these 4 things, agent architecture is a waste of everyone's time.
