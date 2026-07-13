# Training Plan — Purely Pickles AI Business Analyst

> **Trainee:** Himaya  
> **Role:** AI Engineer / Data Scientist  
> **Timeline:** 5 Days  
> **Goal:** Build a LangGraph agent that answers business questions from daily billing CSV exports

---

## Day 1: Setup & First MCP Call

**Goal:** Get the MCP running, fetch your first day of data.

### Tasks:
1. Clone the repo, run `python setup.py` — this builds the local database
2. Start the MCP server: `cd mcp_server && uv run server.py`
3. Call your first MCP tool and get a CSV:
   ```
   get_daily_orders("2017-10-04")
   ```
4. Look at the CSV in `daily_exports/orders_2017-10-04.csv`
5. Read `docs/SCHEMA_HINTS.md` — start thinking about YOUR schema

### Deliverable:
- [ ] MCP server running
- [ ] First CSV exported successfully
- [ ] Initial schema sketch (pencil & paper is fine)

---

## Day 2: Schema Design & Data Cleaning

**Goal:** Design YOUR Supabase schema. Clean one day of data.

### Tasks:
1. Design your Supabase tables — write the `CREATE TABLE` statements
   - Decide: what tables? what columns? what PKs? what FKs?
   - Use the SCHEMA_HINTS.md clues
2. Create the tables in YOUR Supabase project
3. Write a Python function to clean the CSV:
   - Convert `order_date` from string to actual DATE
   - Convert `sales_amount` to numeric
   - Handle any weird values (negative amounts? missing names?)
4. Insert the cleaned data into YOUR tables

### Deliverable:
- [ ] Supabase schema created (screenshot your tables)
- [ ] Data cleaning script working
- [ ] Day 1 data successfully stored in YOUR database

---

## Day 3: Planner Agent — SQL Generation

**Goal:** Build the Planner agent that writes SQL queries.

### Tasks:
1. Write the Planner node in `agent-starter/graph.py`
2. Give the LLM: your schema + the user's question → generate SQL
3. Test with simple questions:
   - "How many orders did we have on 2017-10-04?"
   - "What was the total revenue on 2017-10-04?"
   - "Which restaurant had the most orders?"

### Deliverable:
- [ ] Planner node implemented
- [ ] LLM correctly generates SQL queries
- [ ] 3 test queries run successfully

---

## Day 4: Business Analyst Agent + Full Pipeline

**Goal:** Complete the full 3-agent pipeline.

### Tasks:
1. Implement the Business Analyst node
2. Run complete pipeline: Data Engineer → Planner → Business Analyst
3. Fetch a SECOND day of data (2017-10-05) and process it
4. Answer comparative questions:
   - "How did today compare to yesterday?"
   - "What's trending up? What's trending down?"

### Deliverable:
- [ ] Full pipeline working end-to-end
- [ ] Two days of data processed
- [ ] Comparative analysis working

---

## Day 5: Testing & Demo

**Goal:** Test with real business questions. Prepare demo.

### Tasks:
1. Fetch a third day (2017-10-06)
2. Test these questions:
   - "Give me a full report on yesterday's performance"
   - "What was my highest-selling cuisine last week?"
   - "Who were my top 5 customers?"
   - "Which city brings the most revenue?"
3. Fix any bugs
4. Prepare a 5-minute demo showing the full pipeline

### Deliverable:
- [ ] 3 days of data processed
- [ ] All test questions answered correctly
- [ ] Working demo ready

---

## Tips

- **Start simple.** Get ONE agent working before adding more.
- **Test each step.** Don't move on until the current step works.
- **Schema is sacred.** Design it once, get it right. The rest follows.
- **The MCP is just a data source.** Your value is in what you BUILD around it.
- **Ask questions.** If you're stuck for more than 30 minutes, ask for help.

---

## Resources

- LangGraph docs: https://langchain-ai.github.io/langgraph/
- Supabase Python client: https://supabase.com/docs/reference/python
- MCP (Model Context Protocol): https://modelcontextprotocol.io
- Pandas cheat sheet: https://pandas.pydata.org/Pandas_Cheat_Sheet.pdf
