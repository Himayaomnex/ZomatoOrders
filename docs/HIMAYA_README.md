# 👋 Himaya — Welcome to Purely Pickles Analytics

> **Your mission:** Build an AI Business Analyst agent using LangGraph, MCP, and Supabase.

This repo simulates a real restaurant billing system. Every day, it exports a CSV file with all orders from that day. Your job is to build an agent that fetches this data, cleans it, stores it in YOUR own Supabase database, and answers business questions.

---

## 🗺️ The Big Picture

```
┌─────────────────────────┐              ┌─────────────────────────────┐
│  Billing System (MCP)   │              │  YOUR LangGraph Agent        │
│                         │   CSV via    │                              │
│  You don't see the      │◄─────────────│  Data Engineer               │
│  database. You only     │   MCP tools  │    → Calls MCP, gets CSV     │
│  get CSVs through MCP.  │              │    → Extracts & cleans data  │
│                         │              │    → Stores in YOUR Supabase │
│  (built by your         │              │                              │
│   instructor)           │              │  Planner                     │
│                         │              │    → Understands user intent  │
└─────────────────────────┘              │    → Writes SQL queries      │
                                         │                              │
                                         │  Business Analyst            │
                                         │    → Runs queries             │
                                         │    → Answers in English       │
                                         └─────────────────────────────┘
                                                    │
                                                    ▼
                                          YOUR Supabase Database
                                          (you design the schema!)
```

---

## 🚀 Quick Start

### Step 1: Clone & Setup

```bash
git clone <this-repo-url>
cd purely-pickles-analytics

# One-time setup: this builds the local database
python setup.py
```

Expected output:
```
✅ Database is ready!
   orders:      150,281 rows
   restaurants: 148,541 rows
   ...
   Date range: 2017-10-04 → 2020-06-26 (806 days)
```

### Step 2: Set Your API Key

```bash
cp .env.example .env
```

Edit `.env` and set your API key:
```
PURELY_PICKLES_API_KEY=pp_live_YOUR_KEY_HERE
```

> **Without a key:** The server runs in "training mode" — any key works.  
> **With a key:** Only YOUR key works. This is how real MCP servers authenticate.

### Step 3: Start the MCP Server

```bash
cd mcp_server
pip install -r requirements.txt
python server.py
```

You should see:
```
🍋 Purely Pickles Billing System — MCP Server
   Database: ../zomato.db
   Exports:  ../daily_exports/
   Status:   Ready to serve daily CSVs
```

### Step 4: Call Your First Tool

Connect to the MCP server from your LangGraph agent or any MCP client. Your first call:

```
get_daily_orders(api_key="pp_live_YOUR_KEY", date="2017-10-04")
```

This returns a CSV string with 27 orders from the first day. The CSV is also saved to `daily_exports/orders_2017-10-04.csv`.

---

## 🔧 Available MCP Tools

| Tool | What it does |
|---|---|
| `get_daily_orders(api_key, date)` | **Main tool.** Returns today's orders as CSV. Saves to `daily_exports/`. |
| `get_order_date_range(api_key, start, end)` | Returns orders for a date range. Use for weekly reports. |
| `get_available_dates(api_key)` | Lists all 806 dates that have data. |
| `get_restaurant_info(api_key, id)` | Details about a specific restaurant. |
| `get_schema_hints(api_key)` | Clues about what columns exist. Read this before designing YOUR DB. |
| `get_todays_date_sim(api_key)` | What "day" is it in the simulation? |

> **All tools require `api_key` as the FIRST parameter.** This is how real MCP authentication works.

---

## 📅 The "Daily Data" Concept

The billing system has 806 days of data (2017-2018). But you can't see the future.

- **Day 1:** Call `get_daily_orders(date="2017-10-04")` → 27 orders
- **Day 2:** Call `get_daily_orders(date="2017-10-05")` → 95 orders
- **Day 3:** Call `get_daily_orders(date="2017-10-06")` → 147 orders

Each day you only get THAT day's CSV. Yesterday's data is already in YOUR database. Tomorrow's data hasn't happened yet.

If you ask for a date that doesn't exist: `get_daily_orders(date="2025-01-01")` → `"No orders found — the day hasn't happened yet."`

---

## 📊 Your Deliverables

### Day 1-2: Schema Design
Read `docs/SCHEMA_HINTS.md`. Design YOUR Supabase tables. Write the `CREATE TABLE` statements. Think about:
- What tables do I need?
- What are the Primary Keys?
- What are the Foreign Keys? (Hint: `orders.r_id → restaurants.id`)
- What column types should I use?

### Day 3: Data Engineer Agent
In `agent-starter/graph.py`, implement the `data_engineer_node`:
1. Call the MCP to get today's CSV
2. Parse the CSV with Pandas
3. Clean the data (handle weird values)
4. Store it in YOUR Supabase tables

### Day 4: Planner Agent
Implement the `planner_node`:
1. Understand what the user is asking ("How were my sales yesterday?")
2. Look at your schema
3. Generate an SQL query using the LLM

### Day 5: Business Analyst Agent + Full Pipeline
Implement the `business_analyst_node`:
1. Run the SQL query against YOUR Supabase
2. Feed results + user question to LLM
3. Return a clear, human-readable answer

---

## 📁 Files You'll Work With

| File | What it is | Your job |
|---|---|---|
| `agent-starter/graph.py` | LangGraph skeleton | Fill in the TODOs |
| `docs/SCHEMA_HINTS.md` | Clues about the data | Design YOUR schema |
| `docs/TRAINING_PLAN.md` | 5-day plan | Follow it |
| `daily_exports/` | CSVs appear here | Read them |

| File | What it is | DON'T TOUCH |
|---|---|---|
| `mcp_server/server.py` | The MCP billing server | Built by instructor |
| `setup.py` | Database builder | Run once, then ignore |
| `data/zomato_data.zip` | Raw dataset | Never touch this |

---

## 🆘 When You're Stuck

1. **Can't call the MCP?** Is the server running? Did you set your API key in `.env`?
2. **Schema design?** Read `docs/SCHEMA_HINTS.md` again. Start simple — 2 tables is enough.
3. **LangGraph not working?** Test each node separately before connecting them.
4. **SQL query wrong?** Test it in Supabase SQL editor first, then put it in your code.
5. **Still stuck after 30 minutes?** Ask your instructor. That's what they're there for.

---

## 🎯 Key Concepts You're Learning

- **MCP (Model Context Protocol):** How AI agents discover and authenticate to external tools
- **Schema Design:** Primary keys, foreign keys, normalization
- **Data Engineering:** CSV parsing, Pandas cleaning, database insertion
- **LangGraph:** Multi-agent orchestration with state management
- **LLM Prompting:** Generating SQL from natural language
- **Business Intelligence:** Turning raw data into actionable answers

---

## 🔑 API Key Reference

Your API key is stored in `.env`:
```
PURELY_PICKLES_API_KEY=pp_live_YOUR_KEY
```

When running in production (key set): ❌ Wrong key → blocked  
When running in training mode (no key): ✅ Any key works

For your LangGraph agent, load the key from `.env`:
```python
import os
from dotenv import load_dotenv
load_dotenv()
api_key = os.getenv("PURELY_PICKLES_API_KEY")
```

---

Good luck! Build something awesome. 🍋
