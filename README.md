# 🍋 Purely Pickles — AI Business Analyst

> **Training project for AI engineers learning agent architectures.**

This repo contains everything you need to build an AI agent that:
1. **Fetches** daily billing data from an MCP server (like a real restaurant billing system)
2. **Extracts & cleans** the CSV data
3. **Stores** it in your own Supabase database (with YOUR schema design)
4. **Answers** business questions like "How did my restaurant perform yesterday?"

---

## Architecture

```
┌─────────────────────────┐     MCP      ┌──────────────────────────────┐
│  MCP Billing Server     │◄────────────│  YOUR LangGraph Agent         │
│  (runs locally)         │   CSV!      │                               │
│                         │             │  Data Engineer → Planner →    │
│  Tools:                 │             │  Business Analyst             │
│  • get_daily_orders()   │             │                     │         │
│  • get_order_date_range │             │                     ▼         │
│  • get_available_dates  │             │           YOUR Supabase DB    │
│  • get_restaurant_info  │             │           (you design it)     │
│  • get_schema_hints     │             └──────────────────────────────┘
└─────────────────────────┘
```

---

## Quick Start

### 1. Clone & Setup
```bash
git clone <this-repo-url>
cd purely-pickles-analytics

# One-time setup: builds SQLite from the Zomato dataset
python setup.py
```

### 2. Start the MCP Server
```bash
cd mcp_server
pip install -r requirements.txt
python server.py
```

The MCP server is now running. It simulates a restaurant billing system that exports daily CSVs.

### 3. Call Your First MCP Tool
Connect to the MCP server (via Claude Desktop or any MCP client) and call:
```
get_daily_orders("2017-10-04")
```

This returns a CSV file — just like a real billing system export.

### 4. Build Your Agent
```bash
cd agent-starter
pip install -r requirements.txt
```

Open `graph.py` — this is your LangGraph skeleton. Fill in the TODOs to build a working 3-agent pipeline.

---

## What's Inside

```
purely-pickles-analytics/
├── setup.py                    # One-time setup: builds SQLite database
├── data/
│   └── zomato_data.zip         # Raw dataset (148MB, 150K orders)
├── mcp_server/
│   ├── server.py               # MCP billing system server
│   └── requirements.txt
├── daily_exports/              # CSVs appear here (like billing exports)
├── agent-starter/
│   ├── graph.py                # LangGraph skeleton — YOUR CODE GOES HERE
│   └── requirements.txt
├── docs/
│   ├── SCHEMA_HINTS.md         # Clues for designing YOUR database
│   └── TRAINING_PLAN.md        # 5-day training plan
└── README.md
```

---

## Database Info

- **Source data:** 150,281 orders across 806 days (2017-2020)
- **Average:** ~186 orders/day
- **Tables:** orders, restaurants, food, menu, users
- **Your DB:** You decide the schema. Use Supabase.

---

## Key Concepts You'll Learn

| Concept | Where you practice it |
|---|---|
| **MCP (Model Context Protocol)** | Connecting to the billing server, calling tools |
| **Schema Design** | Creating your Supabase tables with PKs and FKs |
| **Data Engineering** | CSV extraction, Pandas cleaning, DB insertion |
| **LangGraph** | Building multi-agent orchestration |
| **LLM Prompting** | Generating SQL from natural language |
| **Business Analysis** | Answering real questions from data |

---

## Questions?

Read `docs/SCHEMA_HINTS.md` for schema clues.  
Read `docs/TRAINING_PLAN.md` for the day-by-day plan.  
Ask your instructor when you're stuck.
