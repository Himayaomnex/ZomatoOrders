"""
Purely Pickles — LangGraph Agent (STARTER)
===========================================
This is a SKELETON for your AI Business Analyst agent.
Fill in the TODOs to build a working system.

Architecture:
  Data Engineer → Planner → Business Analyst
       │              │              │
   Fetches CSV    Reads intent   Answers user
   from MCP       Writes SQL     questions
   Cleans data    via schema     in natural
   Stores in DB                  language

You will use:
  - MCP client (to call the Purely Pickles billing system)
  - LangGraph (to orchestrate the agents)
  - Supabase (YOUR database — you design the schema)
  - Pandas (for CSV cleaning and extraction)
"""

import os
import sys
from typing import TypedDict, List, Dict, Any, Optional
from pathlib import Path

# LangGraph imports
from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver

# LangChain (for LLM calls)
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage

# Data tools (you'll use these)
import pandas as pd
import io
import csv

# Supabase (YOUR database)
from supabase import create_client

# ═══════════════════════════════════════════════════════════
# TODO #1: ADD YOUR SUPABASE CREDENTIALS
# ═══════════════════════════════════════════════════════════
SUPABASE_URL = "YOUR_SUPABASE_URL"  # ← FILL THIS IN
SUPABASE_KEY = "YOUR_SUPABASE_KEY"  # ← FILL THIS IN
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

# ═══════════════════════════════════════════════════════════
# TODO #2: ADD YOUR OPENAI / DEEPSEEK API KEY
# ═══════════════════════════════════════════════════════════
os.environ["OPENAI_API_KEY"] = "YOUR_API_KEY"  # ← FILL THIS IN

# You can swap this for DeepSeek if you prefer
llm = ChatOpenAI(model="gpt-4o", temperature=0)

# ═══════════════════════════════════════════════════════════
# STATE — Shared state between all agents
# ═══════════════════════════════════════════════════════════


class AgentState(TypedDict):
    """Shared state that flows through the agent graph."""

    # User input
    user_question: str  # e.g. "How did my restaurant perform yesterday?"

    # Data Engineer outputs
    csv_data: Optional[str]  # Raw CSV from MCP
    cleaned_data: Optional[str]  # Cleaned CSV / JSON
    extraction_status: str  # "pending" | "done" | "failed"

    # Planner outputs
    sql_query: Optional[str]  # SQL query to run against YOUR DB
    requirements: Optional[str]  # What the user actually wants

    # Business Analyst outputs
    analysis_result: Optional[str]  # Final answer to the user
    report: Optional[str]  # Formatted report

    # Errors
    error: Optional[str]


# ═══════════════════════════════════════════════════════════
# AGENT 1: DATA ENGINEER
# ═══════════════════════════════════════════════════════════
#
# This agent should:
# 1. Call the MCP billing system to get today's CSV
# 2. Extract and clean the data
# 3. Store it in YOUR Supabase database
#
# TODO #3: Implement the Data Engineer agent
# ═══════════════════════════════════════════════════════════


def data_engineer_node(state: AgentState) -> AgentState:
    """
    DATA ENGINEER — Fetch, extract, clean, store.

    This agent is responsible for:
    1. Calling the MCP to get the daily CSV
    2. Cleaning the data (handle missing values, fix types)
    3. Storing cleaned data in YOUR Supabase database

    HINT: You'll need to call the MCP tool get_daily_orders(date)
    You can do this via bash command, Python subprocess, or MCP client library.
    """
    print("\n🔧 [Data Engineer] Starting...")

    # ── Step 1: Call the MCP ──
    # TODO: Use subprocess or mcp client to call get_daily_orders()
    # The MCP server is running locally — ask your instructor for the connection details
    #
    # PSEUDOCODE:
    #   csv_data = call_mcp_tool("get_daily_orders", {"date": "2017-10-04"})
    #   state["csv_data"] = csv_data
    #
    # For now, this is a placeholder:

    state["csv_data"] = None  # ← REPLACE with actual MCP call
    state["extraction_status"] = "pending"

    print("   [ ] MCP call — TODO: implement MCP client connection")
    print("   [ ] Data cleaning — TODO: implement Pandas cleaning")
    print("   [ ] Supabase storage — TODO: implement DB insert")

    # ── Step 2: Clean the data ──
    # TODO: Use Pandas to:
    #   - Parse the CSV string into a DataFrame
    #   - Check for missing values
    #   - Convert data types (date → DATE, amount → NUMERIC)
    #   - Validate foreign keys (do user_ids and r_ids exist?)

    # ── Step 3: Store in YOUR Supabase ──
    # TODO: Insert cleaned data into YOUR tables
    # HINT: You designed the schema — you know the tables and columns!

    state["extraction_status"] = "done"
    print("🔧 [Data Engineer] Complete")
    return state


# ═══════════════════════════════════════════════════════════
# AGENT 2: PLANNER
# ═══════════════════════════════════════════════════════════
#
# This agent should:
# 1. Understand what the user is asking
# 2. Look at YOUR database schema
# 3. Write an SQL query to get the answer
#
# TODO #4: Implement the Planner agent
# ═══════════════════════════════════════════════════════════


def planner_node(state: AgentState) -> AgentState:
    """
    PLANNER — Understand intent, write SQL query.

    This agent is the "brain" that:
    1. Takes the user's natural language question
    2. Breaks it down into concrete data requirements
    3. Looks at YOUR Supabase schema
    4. Writes the correct SQL query to answer the question

    The LLM should help you here — give it the schema + user question,
    and ask it to generate the SQL.
    """
    print("\n🧠 [Planner] Starting...")

    user_question = state.get("user_question", "")

    # ── Step 1: Understand user intent ──
    # TODO: Use the LLM to break down the question
    #
    # EXAMPLES:
    #   "How were my sales yesterday?" →
    #       → SUM(sales_amount) WHERE order_date = 'yesterday'
    #
    #   "What was my top-selling cuisine last week?" →
    #       → GROUP BY cuisine, ORDER BY SUM(sales_amount) DESC

    requirements = f"User asked: {user_question}"  # ← REPLACE with LLM breakdown
    state["requirements"] = requirements

    # ── Step 2: Read YOUR schema ──
    # TODO: Query Supabase to get your table schemas
    # Or: use the schema you already know (since YOU designed it!)
    #
    # PSEUDOCODE:
    #   schema = supabase.rpc("get_schema").execute()
    #   or just hardcode your schema since you designed it

    # ── Step 3: Generate SQL query ──
    # TODO: Feed [schema + user question] to the LLM
    # Ask it to generate a valid SQL query
    #
    # PSEUDOCODE:
    #   prompt = f"Schema: {schema}\nQuestion: {user_question}\nWrite SQL:"
    #   response = llm.invoke(prompt)
    #   sql_query = extract_sql_from_response(response)

    state["sql_query"] = None  # ← REPLACE with generated SQL
    print(f"   [ ] User intent: {user_question}")
    print(f"   [ ] SQL query: TODO — implement LLM-based SQL generation")

    print("🧠 [Planner] Complete")
    return state


# ═══════════════════════════════════════════════════════════
# AGENT 3: BUSINESS ANALYST
# ═══════════════════════════════════════════════════════════
#
# This agent should:
# 1. Execute the SQL query against YOUR database
# 2. Interpret the results
# 3. Give a natural language answer to the user
#
# TODO #5: Implement the Business Analyst agent
# ═══════════════════════════════════════════════════════════


def business_analyst_node(state: AgentState) -> AgentState:
    """
    BUSINESS ANALYST — Execute query, analyze results, answer user.

    This agent:
    1. Runs the SQL query from the Planner against YOUR Supabase
    2. Takes the raw results + user question
    3. Uses the LLM to write a natural language answer
    4. Provides insights, not just raw numbers
    """
    print("\n📊 [Business Analyst] Starting...")

    sql_query = state.get("sql_query")
    user_question = state.get("user_question", "")

    # ── Step 1: Execute the SQL query ──
    # TODO: Run the query against YOUR Supabase
    #
    # PSEUDOCODE:
    #   result = supabase.rpc("execute_sql", {"query": sql_query}).execute()
    #   data = result.data

    query_results = None  # ← REPLACE with actual query results

    # ── Step 2: Analyze and answer ──
    # TODO: Feed [user question + query results] to the LLM
    # Ask it to produce a clear, human-readable answer
    #
    # PSEUDOCODE:
    #   prompt = f"Question: {user_question}\nData: {query_results}\nAnswer:"
    #   response = llm.invoke(prompt)

    state["analysis_result"] = "TODO: Implement Business Analyst"
    state["report"] = "TODO: Generate natural language report"

    print(f"   [ ] Query executed: {sql_query}")
    print(f"   [ ] Analysis: TODO — implement LLM-based answer generation")

    print("📊 [Business Analyst] Complete")
    return state


# ═══════════════════════════════════════════════════════════
# ROUTER — Decides which agent runs next
# ═══════════════════════════════════════════════════════════


def router(state: AgentState) -> str:
    """Decide which node to call next based on current state."""
    if state.get("error"):
        return END

    # Data Engineer → Planner → Business Analyst → END
    if state.get("extraction_status") == "pending":
        return "data_engineer"
    if state.get("extraction_status") == "done" and not state.get("sql_query"):
        return "planner"
    if state.get("sql_query") and not state.get("analysis_result"):
        return "business_analyst"
    return END


# ═══════════════════════════════════════════════════════════
# BUILD THE GRAPH
# ═══════════════════════════════════════════════════════════


def build_graph() -> StateGraph:
    """
    Build and compile the LangGraph workflow.

    Flow: Data Engineer → Planner → Business Analyst → END
    """
    workflow = StateGraph(AgentState)

    # Add nodes
    workflow.add_node("data_engineer", data_engineer_node)
    workflow.add_node("planner", planner_node)
    workflow.add_node("business_analyst", business_analyst_node)

    # Set entry point
    workflow.set_entry_point("data_engineer")

    # Define edges
    workflow.add_edge("data_engineer", "planner")
    workflow.add_edge("planner", "business_analyst")
    workflow.add_edge("business_analyst", END)

    # Compile (with memory so it can remember past days)
    memory = MemorySaver()
    graph = workflow.compile(checkpointer=memory)

    return graph


# ═══════════════════════════════════════════════════════════
# MAIN — Run the agent
# ═══════════════════════════════════════════════════════════


def run_agent(question: str, thread_id: str = "day1"):
    """
    Run the full agent pipeline for a single user question.

    Args:
        question: e.g. "How did my restaurant perform yesterday?"
        thread_id: Unique ID for this conversation (so the agent remembers past days)

    TODO #6: Call this from a loop or a simple CLI
    """
    graph = build_graph()

    initial_state: AgentState = {
        "user_question": question,
        "csv_data": None,
        "cleaned_data": None,
        "extraction_status": "pending",
        "sql_query": None,
        "requirements": None,
        "analysis_result": None,
        "report": None,
        "error": None,
    }

    config = {"configurable": {"thread_id": thread_id}}

    print(f"\n{'='*60}")
    print(f"🍋 Purely Pickles AI Analyst")
    print(f"   Question: {question}")
    print(f"{'='*60}")

    result = graph.invoke(initial_state, config)

    print(f"\n{'='*60}")
    print("📋 FINAL REPORT:")
    print(result.get("report", "No report generated"))
    print(f"{'='*60}")

    return result


# ═══════════════════════════════════════════════════════════
# RUN IT
# ═══════════════════════════════════════════════════════════

if __name__ == "__main__":
    print("🍋 Purely Pickles — AI Business Analyst")
    print("   This is a STARTER SKELETON.")
    print("   Fill in the TODOs to make it work!\n")

    # Example: ask a question
    run_agent("How did my restaurant perform yesterday?")
