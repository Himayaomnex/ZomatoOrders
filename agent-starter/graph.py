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
import re

# Configure UTF-8 encoding for Windows consoles to prevent Unicode print crashes
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')
from datetime import datetime, timedelta
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
from dotenv import load_dotenv

# Load .env file from the ZomatoOrders root folder
project_root = Path(__file__).parent.parent
load_dotenv(project_root / ".env")

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

# Configure LLM API Keys
os.environ["OPENAI_API_KEY"] = os.getenv("OPENAI_API_KEY", "")
os.environ["GEMINI_API_KEY"] = os.getenv("GEMINI_API_KEY", "")
os.environ["GROQ_API_KEY"]   = os.getenv("GROQ_API_KEY", "")

# Load the selected LLM Provider dynamically
# Default is "groq" — fastest (sub-second), no overload issues
LLM_PROVIDER = os.getenv("LLM_PROVIDER", "groq").lower().strip()

# ── Build primary LLM ───────────────────────────────────────────────────────
if LLM_PROVIDER == "gemini":
    from langchain_google_genai import ChatGoogleGenerativeAI
    llm = ChatGoogleGenerativeAI(model="gemini-2.0-flash", temperature=0, max_retries=0)
    print("[LLM] Using Google Gemini (gemini-2.0-flash)")
elif LLM_PROVIDER == "groq":
    from langchain_groq import ChatGroq
    llm = ChatGroq(model="llama-3.1-8b-instant", temperature=0)
    print("[LLM] Using Groq Cloud (llama-3.1-8b-instant) - fastest")
elif LLM_PROVIDER == "ollama":
    from langchain_ollama import ChatOllama
    ollama_model = os.getenv("OLLAMA_MODEL", "gemma2:9b")
    llm = ChatOllama(model=ollama_model, temperature=0)
    print(f"[LLM] Using Local Ollama ({ollama_model})")
else:
    from langchain_openai import ChatOpenAI
    llm = ChatOpenAI(model="gpt-4o", temperature=0)
    print("[LLM] Using OpenAI (gpt-4o)")

# If Gemini/Ollama returns a server-side or connection/rate limit error, fallback to Groq/Gemini
def _llm_invoke_with_fallback(messages):
    """Call primary LLM; fall back to Groq/Gemini on any server-side, rate limit, or connection error."""
    try:
        return llm.invoke(messages)
    except Exception as e:
        err_str = str(e).lower()
        is_fallback_needed = any(x in err_str for x in [
            "503", "429", "unavailable", "overloaded", "rate limit", 
            "quota", "exhausted", "connection refused", "connect call failed", "connectionerror"
        ])
        if "conn" in err_str or "refused" in err_str or "unreachable" in err_str:
            is_fallback_needed = True

        if is_fallback_needed:
            print(f"[LLM] Primary model failed ({e}). Falling back to cloud LLM...")
            groq_key = os.getenv("GROQ_API_KEY", "")
            if groq_key and not groq_key.startswith("PASTE"):
                print("   [LLM Fallback] Using Groq llama-3.1-8b-instant")
                from langchain_groq import ChatGroq
                fallback = ChatGroq(model="llama-3.1-8b-instant", temperature=0)
                return fallback.invoke(messages)
            else:
                print("   [LLM Fallback] Using Gemini gemini-2.0-flash")
                from langchain_google_genai import ChatGoogleGenerativeAI
                fallback = ChatGoogleGenerativeAI(model="gemini-2.0-flash", temperature=0, max_retries=0)
                return fallback.invoke(messages)
        raise  # re-raise non-server errors normally


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
    raw_query_data: Optional[List[Dict[str, Any]]]
    target_dates: Optional[List[str]]


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


import json

def extract_dates_from_question(question: str) -> Dict[str, Any]:
    """
    Analyze the user question to determine which dates to load from the MCP billing system.
    Returns a dict with format:
      {"type": "single"|"multiple"|"range"|"default", "dates": [...], "start_date": "...", "end_date": "..."}
    """
    # Quick static checks first to avoid LLM calls on simple standard prompts
    # 1. Regex check for single date
    single_match = re.findall(r"\d{4}-\d{2}-\d{2}", question)
    if len(single_match) == 1:
        return {"type": "single", "dates": [single_match[0]]}
    elif len(single_match) > 1:
        return {"type": "multiple", "dates": single_match}

    # 2. Check for "yesterday"
    if "yesterday" in question.lower() and not ("compare" in question.lower() or "versus" in question.lower() or "vs" in question.lower()):
        return {"type": "single", "dates": ["2017-10-04"]}

    # Fallback to LLM for complex/relative dates and ranges
    try:
        prompt = f"""You are a date extraction helper. Analyze this user question and extract date information for querying a Zomato orders database.
Assume simulated today is 2017-10-05, so yesterday is 2017-10-04, and the day before is 2017-10-03.
Return a valid, raw JSON object (do not wrap in markdown code blocks, do not include any other text or prose) matching one of these formats:
1. For a single date: {{"type": "single", "dates": ["YYYY-MM-DD"]}}
2. For multiple specific dates: {{"type": "multiple", "dates": ["YYYY-MM-DD", "YYYY-MM-DD", ...]}}
3. For a continuous date range: {{"type": "range", "start_date": "YYYY-MM-DD", "end_date": "YYYY-MM-DD"}}
4. If no date, time range, or comparative period is mentioned at all: {{"type": "default", "dates": ["2017-10-04", "2017-10-05", "2017-10-06"]}}

Question: "{question}"
JSON:"""
        response = _llm_invoke_with_fallback([
            SystemMessage(content="You extract date search parameters into JSON format."),
            HumanMessage(content=prompt)
        ])
        raw_content = get_clean_text_content(response.content).strip()
        
        # Clean markdown if returned
        if raw_content.startswith("```"):
            raw_content = raw_content.strip("`")
            if raw_content.startswith("json"):
                raw_content = raw_content[4:].strip()
                
        data = json.loads(raw_content)
        if "type" in data:
            return data
    except Exception as e:
        print(f"   [Data Engineer] Date LLM parsing failed: {e}")

    # Default fallback: load all 3 main training dates so they are available
    return {"type": "default", "dates": ["2017-10-04", "2017-10-05", "2017-10-06"]}


# In-process cache: tracks all dates currently loaded in Supabase
_LOADED_DATES: set = set()


def load_single_date(date_str: str) -> bool:
    """Fetch, clean, and insert orders for a single date into Supabase. Returns True if successful."""
    # Check cache
    if date_str in _LOADED_DATES:
        return True

    # Check Supabase
    try:
        check = supabase.table("orders").select("id").eq("order_date", date_str).limit(1).execute()
        if check.data:
            _LOADED_DATES.add(date_str)
            return True
    except Exception:
        pass

    print(f"   [Data Engineer] Syncing orders for date: {date_str}")
    sys.path.append(str(project_root / "mcp_server"))
    try:
        from server import get_daily_orders
        csv_data = get_daily_orders(api_key="", date=date_str)
    except Exception as e:
        print(f"   [Data Engineer] Failed to call MCP server for {date_str}: {e}")
        return False

    if csv_data.startswith("UNAUTHORIZED") or csv_data.startswith("# No orders"):
        return True  # Skip insertion, not a failure

    # Clean CSV
    lines = csv_data.splitlines()
    csv_rows = [line for line in lines if not line.startswith("#")]
    csv_cleaned = "\n".join(csv_rows).strip()

    # Load & Clean with Pandas
    try:
        df = pd.read_csv(io.StringIO(csv_cleaned))
        df = df.dropna(subset=['order_date', 'sales_qty', 'sales_amount', 'user_id', 'r_id'])
        df['order_date']   = pd.to_datetime(df['order_date']).dt.date.astype(str)
        df['sales_qty']    = df['sales_qty'].astype(int)
        df['sales_amount'] = df['sales_amount'].astype(float)
        df['currency']     = df['currency'].astype(str).str.strip()
        df['user_id']      = df['user_id'].astype(int)
        df['r_id']         = df['r_id'].astype(int)
        orders_df = df[['order_date', 'sales_qty', 'sales_amount', 'currency', 'user_id', 'r_id']]
        records   = orders_df.to_dict('records')
    except Exception as e:
        print(f"   [Data Engineer] CSV parsing failed for {date_str}: {e}")
        return False

    # Insert into Supabase
    try:
        supabase.table("orders").delete().eq("order_date", date_str).execute()
        if records:
            supabase.table("orders").insert(records).execute()
            print(f"   [Data Engineer] Seeded {len(records)} orders for {date_str} in Supabase.")
        _LOADED_DATES.add(date_str)
        return True
    except Exception as e:
        print(f"   [Data Engineer] Supabase write failed for {date_str}: {e}")
        return False


def load_date_range(start_date: str, end_date: str) -> bool:
    """Fetch, clean, and insert orders for a date range into Supabase in one batch."""
    print(f"   [Data Engineer] Syncing orders for range: {start_date} to {end_date}")
    sys.path.append(str(project_root / "mcp_server"))
    try:
        from server import get_order_date_range
        csv_data = get_order_date_range(api_key="", start_date=start_date, end_date=end_date)
    except Exception as e:
        print(f"   [Data Engineer] Failed to call MCP server range: {e}")
        return False

    if csv_data.startswith("UNAUTHORIZED") or csv_data.startswith("# No orders"):
        return True

    # Clean CSV
    lines = csv_data.splitlines()
    csv_rows = [line for line in lines if not line.startswith("#")]
    csv_cleaned = "\n".join(csv_rows).strip()

    # Load & Clean with Pandas
    try:
        df = pd.read_csv(io.StringIO(csv_cleaned))
        df = df.dropna(subset=['order_date', 'sales_qty', 'sales_amount', 'user_id', 'r_id'])
        df['order_date']   = pd.to_datetime(df['order_date']).dt.date.astype(str)
        df['sales_qty']    = df['sales_qty'].astype(int)
        df['sales_amount'] = df['sales_amount'].astype(float)
        df['currency']     = df['currency'].astype(str).str.strip()
        df['user_id']      = df['user_id'].astype(int)
        df['r_id']         = df['r_id'].astype(int)
        orders_df = df[['order_date', 'sales_qty', 'sales_amount', 'currency', 'user_id', 'r_id']]
        records   = orders_df.to_dict('records')
    except Exception as e:
        print(f"   [Data Engineer] CSV parsing failed for range: {e}")
        return False

    # Insert into Supabase (Clean existing rows in range first)
    try:
        supabase.table("orders").delete().filter("order_date", "gte", start_date).filter("order_date", "lte", end_date).execute()
        if records:
            supabase.table("orders").insert(records).execute()
            print(f"   [Data Engineer] Seeded {len(records)} orders for range {start_date} to {end_date} in Supabase.")
        
        # Add all individual dates in the range to our loaded dates cache
        if not df.empty:
            for d in df['order_date'].unique():
                _LOADED_DATES.add(str(d))
        return True
    except Exception as e:
        print(f"   [Data Engineer] Supabase write failed for range: {e}")
        return False


def data_engineer_node(state: AgentState) -> AgentState:
    """
    DATA ENGINEER — Fetch, extract, clean, store.
    """
    print("\n[Data Engineer] Starting...")
    user_question = state.get("user_question", "")

    # If target_dates is already set (passed from Streamlit UI date filter), use them directly!
    preselected_dates = state.get("target_dates")
    if preselected_dates:
        print(f"   [Data Engineer] Using preselected target dates: {preselected_dates}")
        success = True
        for date_str in preselected_dates:
            if not load_single_date(date_str):
                success = False
        if not success:
            state["error"] = "Data Engineer failed to sync required preselected dates from MCP."
            state["extraction_status"] = "failed"
            return state
        state["extraction_status"] = "done"
        print("[Data Engineer] Complete")
        return state

    # Otherwise, parse target dates from question
    date_info = extract_dates_from_question(user_question)
    print(f"   [Data Engineer] Extraction params: {date_info}")

    success = True
    if date_info["type"] == "range":
        start = date_info["start_date"]
        end = date_info["end_date"]
        success = load_date_range(start, end)
    else:
        # single, multiple, or default list of dates
        for date_str in date_info.get("dates", []):
            if not load_single_date(date_str):
                success = False

    if not success:
        state["error"] = "Data Engineer failed to sync required dates from MCP billing server."
        state["extraction_status"] = "failed"
        return state

    if date_info["type"] == "range":
        state["target_dates"] = [date_info["start_date"], date_info["end_date"]]
    else:
        state["target_dates"] = date_info.get("dates", [])

    state["extraction_status"] = "done"
    print("[Data Engineer] Complete")
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


# Database schema definition for the Planner LLM context
SCHEMA_DESC = """
We have a PostgreSQL database in Supabase with the following tables and schemas:

1. users:
   - user_id (INTEGER, Primary Key)
   - name (TEXT)
   - email (TEXT)
   - gender (TEXT)
   - occupation (TEXT)
   - monthly_income (TEXT)
   - education (TEXT)
   - family_size (TEXT)

2. restaurants:
   - id (INTEGER, Primary Key)
   - name (TEXT)
   - city (TEXT)
   - rating (REAL)
   - rating_count (INTEGER)
   - cost (TEXT)
   - cuisine (TEXT)

3. food:
   - f_id (TEXT, Primary Key)
   - item (TEXT)
   - veg_or_non_veg (TEXT)

4. menu:
   - menu_id (TEXT, Primary Key)
   - r_id (INTEGER, Foreign Key referencing restaurants.id)
   - f_id (TEXT, Foreign Key referencing food.f_id)
   - cuisine (TEXT)
   - price (NUMERIC)

5. orders:
   - id (SERIAL, Primary Key)
   - order_date (DATE)
   - sales_qty (INTEGER)
   - sales_amount (NUMERIC)
   - currency (TEXT)
   - user_id (INTEGER, Foreign Key referencing users.user_id)
   - r_id (INTEGER, Foreign Key referencing restaurants.id)
"""

def get_clean_text_content(content) -> str:
    """Helper to safely extract string text from LLM response content which might be a list or a string."""
    if isinstance(content, list):
        text_parts = []
        for part in content:
            if isinstance(part, str):
                text_parts.append(part)
            elif isinstance(part, dict) and "text" in part:
                text_parts.append(part["text"])
        return "".join(text_parts).strip()
    return str(content).strip()

def extract_sql_from_response(text: str) -> str:
    """Robustly pull the SQL out of an LLM response — handles markdown, plain text, etc."""
    text = text.strip()

    # Case 1: wrapped in ```sql ... ``` or ``` ... ```
    import re as _re
    match = _re.search(r"```(?:sql)?\s*(.*?)```", text, _re.DOTALL | _re.IGNORECASE)
    if match:
        return match.group(1).strip().rstrip(';')

    # Case 2: starts with SELECT / WITH / INSERT / UPDATE — plain SQL
    sql_start = _re.search(r"\b(SELECT|WITH|INSERT|UPDATE|DELETE)\b", text, _re.IGNORECASE)
    if sql_start:
        return text[sql_start.start():].strip().rstrip(';')

    # Case 3: return whatever we have, cleaned
    return text.rstrip(';').strip()


# ═══════════════════════════════════════════════════════════
# TOOLS FOR RESTAURANT INTELLIGENT AGENT (RIA)
# ═══════════════════════════════════════════════════════════

def sql_tool(sql_query: str) -> Dict[str, Any]:
    """
    SQL Tool: Execute raw PostgreSQL queries against Supabase.
    Returns a dict containing either 'data' (list of rows) or 'error' (str).
    """
    print(f"   [SQL Tool] Executing: {sql_query}")
    try:
        response = supabase.rpc("execute_sql", {"sql_query": sql_query}).execute()
        data = response.data
        if isinstance(data, dict) and "error" in data:
            return {"error": data["error"]}
        return {"data": data}
    except Exception as e:
        return {"error": str(e)}


def analytical_tool(data: List[Dict[str, Any]], user_question: str) -> Dict[str, Any]:
    """
    Analytical Tool: Calculates business KPIs like Total Revenue, 
    Average Order Value (AOV), order count, and item frequency distributions.
    """
    print(f"   [Analytical Tool] Computing KPIs for {len(data)} rows...")
    kpis = {
        "row_count": len(data),
        "total_revenue": 0.0,
        "total_qty": 0,
        "average_order_value": 0.0,
        "details": ""
    }
    if not data:
        return kpis

    try:
        df = pd.DataFrame(data)
        
        # Calculate Total Revenue (Convert USD to INR: 1 USD = 83 INR)
        revenue_cols = [c for c in df.columns if any(x in c.lower() for x in ['revenue', 'amount', 'price'])]
        if 'sales_amount' in df.columns:
            kpis["total_revenue"] = float(pd.to_numeric(df['sales_amount'], errors='coerce').fillna(0).sum()) * 83.0
        elif revenue_cols:
            kpis["total_revenue"] = float(pd.to_numeric(df[revenue_cols[0]], errors='coerce').fillna(0).sum()) * 83.0

        # Calculate Total Quantities
        qty_cols = [c for c in df.columns if any(x in c.lower() for x in ['qty', 'quantity', 'count'])]
        if 'sales_qty' in df.columns:
            kpis["total_qty"] = int(pd.to_numeric(df['sales_qty'], errors='coerce').fillna(0).sum())
        elif qty_cols:
            kpis["total_qty"] = int(pd.to_numeric(df[qty_cols[0]], errors='coerce').fillna(0).sum())
        else:
            kpis["total_qty"] = len(df)

        # Calculate AOV
        if kpis["row_count"] > 0:
            kpis["average_order_value"] = kpis["total_revenue"] / kpis["row_count"]

        # Additional analytics
        summary_parts = []
        if 'restaurant_name' in df.columns:
            if 'sales_amount' in df.columns:
                sales_col = pd.to_numeric(df['sales_amount'], errors='coerce').fillna(0) * 83.0
                top_rests = df.assign(cleaned_sales=sales_col).groupby('restaurant_name')['cleaned_sales'].sum().nlargest(3)
                summary_parts.append("Top restaurants by revenue: " + ", ".join([f"{name} (₹{val:,.2f})" for name, val in top_rests.items()]))
            elif revenue_cols:
                sales_col = pd.to_numeric(df[revenue_cols[0]], errors='coerce').fillna(0) * 83.0
                top_rests = df.assign(cleaned_sales=sales_col).groupby('restaurant_name')['cleaned_sales'].sum().nlargest(3)
                summary_parts.append("Top restaurants by revenue: " + ", ".join([f"{name} (₹{val:,.2f})" for name, val in top_rests.items()]))
            else:
                top_rests = df['restaurant_name'].value_counts().nlargest(3)
                summary_parts.append("Top restaurants by order count: " + ", ".join([f"{name} ({val} orders)" for name, val in top_rests.items()]))

        if 'city' in df.columns:
            if 'sales_amount' in df.columns:
                sales_col = pd.to_numeric(df['sales_amount'], errors='coerce').fillna(0) * 83.0
                city_rev = df.assign(cleaned_sales=sales_col).groupby('city')['cleaned_sales'].sum().nlargest(3)
                summary_parts.append("Top cities: " + ", ".join([f"{city} (₹{val:,.2f})" for city, val in city_rev.items()]))
            elif revenue_cols:
                sales_col = pd.to_numeric(df[revenue_cols[0]], errors='coerce').fillna(0) * 83.0
                city_rev = df.assign(cleaned_sales=sales_col).groupby('city')['cleaned_sales'].sum().nlargest(3)
                summary_parts.append("Top cities: " + ", ".join([f"{city} (₹{val:,.2f})" for city, val in city_rev.items()]))
            else:
                city_rev = df['city'].value_counts().nlargest(3)
                summary_parts.append("Top cities by order count: " + ", ".join([f"{city} ({val} orders)" for city, val in city_rev.items()]))

        if 'item' in df.columns:
            if 'sales_qty' in df.columns:
                qty_col = pd.to_numeric(df['sales_qty'], errors='coerce').fillna(0)
                top_items = df.assign(cleaned_qty=qty_col).groupby('item')['cleaned_qty'].sum().nlargest(3)
                summary_parts.append("Top food items: " + ", ".join([f"{item} ({qty} qty)" for item, qty in top_items.items()]))
            elif qty_cols:
                qty_col = pd.to_numeric(df[qty_cols[0]], errors='coerce').fillna(0)
                top_items = df.assign(cleaned_qty=qty_col).groupby('item')['cleaned_qty'].sum().nlargest(3)
                summary_parts.append("Top food items: " + ", ".join([f"{item} ({qty} qty)" for item, qty in top_items.items()]))
            else:
                top_items = df['item'].value_counts().nlargest(3)
                summary_parts.append("Top food items by frequency: " + ", ".join([f"{item} ({qty} orders)" for item, qty in top_items.items()]))
            
        kpis["details"] = " | ".join(summary_parts)
    except Exception as e:
        print(f"   [Analytical Tool] Error during pandas computation: {e}")
        kpis["details"] = f"Calculation partial error: {e}"

    return kpis


def report_tool(kpi_data: Dict[str, Any], raw_data: List[Dict[str, Any]], sql_query: str, user_question: str) -> str:
    """
    Report Tool: Formats a professional Markdown report, including KPI callouts 
    and instructions for exporting data (simulating PDF/Excel outputs).
    """
    print("   [Report Tool] Generating business-friendly report...")
    
    prompt = f"""You are a professional Business Analyst for the platform 'Zomato Orders' (represented by the Restaurant Intelligent Agent - RIA). Format all monetary figures in Indian Rupees (₹) using the conversion rate of 1 USD = 83 INR that has been pre-applied to the database metrics.
The user asked: "{user_question}"

The SQL Tool executed this query: {sql_query}
The Analytical Tool calculated these KPIs:
- Total Rows: {kpi_data['row_count']}
- Total Revenue: ₹{kpi_data['total_revenue']:,.2f}
- Total Quantity Ordered: {kpi_data['total_qty']}
- Average Order Value (AOV): ₹{kpi_data['average_order_value']:,.2f}
- Key Insights: {kpi_data['details']}

Raw rows returned (truncated to first 20):
{json.dumps(raw_data[:20], indent=2)}

Please write a clean, helpful, and natural language business report answering the user's question based on the query results and computed KPIs.
Format it nicely in Markdown. Include KPI cards or bullet points for the main metrics (Revenue, AOV, Qty).
At the end of your report, add a brief section titled "📊 Export Options" explaining that the user can download this report using the two buttons directly below this message window:
1. "Download Report (Markdown)" to download the text.
2. "Export Raw Data (CSV)" to download the dataset for Excel.
Do NOT describe any other non-existent buttons (like a top-right export button, PDF dropdown, or a generic 'Raw Data' button).
"""

    try:
        response = _llm_invoke_with_fallback([
            SystemMessage(content="You are a helpful business analyst assistant."),
            HumanMessage(content=prompt)
        ])
        report_content = get_clean_text_content(response.content)
    except Exception as e:
        print(f"   [Report Tool] LLM generation failed: {e}")
        report_content = f"Failed to generate report text: {e}"
        
    return report_content


# ═══════════════════════════════════════════════════════════
# RESTAURANT INTELLIGENT AGENT (RIA) NODE
# ═══════════════════════════════════════════════════════════

def restaurant_intelligent_agent_node(state: AgentState) -> AgentState:
    """
    RESTAURANT INTELLIGENT AGENT (RIA)
    
    This agent coordinates:
    1. Analyzing user question & Generating the SQL query (Planning)
    2. Calling the SQL Tool to fetch raw rows from Supabase
    3. Calling the Analytical Tool to compute business KPIs (Total Revenue, AOV)
    4. Calling the Report Tool to compile the final narrative report and export guide.
    """
    print("\n[Restaurant Intelligent Agent] Starting execution...")
    user_question = state.get("user_question", "")

    # ── Step 1: SQL Generation ──
    system_prompt = f"""You are a professional SQL database developer.
Your task is to generate a single, valid PostgreSQL query that answers the user's question.

Database Schema:
{SCHEMA_DESC}

Important Rules:
1. Return ONLY the raw SQL query — no explanations, no prose, no markdown fences.
2. Use proper table joins (e.g. JOIN orders ON orders.r_id = restaurants.id).
3. Use exact date strings like '2017-10-04' for date comparisons.
4. Do not reference columns or tables not listed in the schema above.
5. If no date is specified, use '2017-10-04' as the default.
6. DO NOT use dynamic date functions like CURRENT_DATE, CURRENT_TIMESTAMP, NOW(), or dynamic date intervals. Always write exact literal date strings (e.g. '2017-10-04').
7. When selecting fields (e.g. columns from joined tables) alongside aggregate values (SUM, COUNT, etc.), you MUST include a proper GROUP BY clause for all selected non-aggregate fields to prevent PostgreSQL syntax errors.
"""

    extracted_dates = state.get("target_dates", [])
    date_context = f"\nFor context, the Data Ingestion system parsed these target date(s) for the query: {extracted_dates}." if extracted_dates else ""

    sql_query = ""
    for attempt in range(2):
        try:
            response = _llm_invoke_with_fallback([
                SystemMessage(content=system_prompt),
                HumanMessage(content=f"Write the PostgreSQL query to answer: {user_question}{date_context}")
            ])
            raw = get_clean_text_content(response.content)
            sql_query = extract_sql_from_response(raw)
            if sql_query:
                break
            else:
                print(f"   [RIA] Empty SQL on attempt {attempt + 1}, retrying...")
        except Exception as e:
            print(f"   [RIA] SQL generation failed (attempt {attempt + 1}): {e}")
            if attempt == 1:
                state["error"] = f"RIA SQL generation failed: {e}"
                return state

    if not sql_query:
        state["error"] = "RIA could not generate a SQL query after 2 attempts."
        return state

    state["sql_query"] = sql_query
    state["requirements"] = f"Write SQL for: {user_question}"
    print(f"   [RIA] Generated SQL: {sql_query}")

    # ── Step 2: Call SQL Tool ──
    sql_result = sql_tool(sql_query)
    if "error" in sql_result:
        state["error"] = f"SQL Tool error: {sql_result['error']}"
        state["analysis_result"] = "Error executing query"
        state["report"] = f"Failed to retrieve data from database: {sql_result['error']}"
        return state

    raw_data = sql_result["data"]
    print(f"   [RIA] SQL Tool returned {len(raw_data)} rows.")

    # ── Step 3: Call Analytical Tool ──
    kpi_data = analytical_tool(raw_data, user_question)

    # Override KPIs with actual daily totals if target_dates is set
    if extracted_dates:
        date_list = ", ".join([f"'{d}'" for d in extracted_dates])
        totals_query = f"SELECT SUM(sales_amount) AS total_revenue, SUM(sales_qty) AS total_qty, COUNT(id) AS total_orders FROM orders WHERE order_date IN ({date_list})"
        try:
            totals_res = supabase.rpc("execute_sql", {"sql_query": totals_query}).execute()
            totals_data = totals_res.data
            if totals_data and isinstance(totals_data, list) and len(totals_data) > 0:
                row = totals_data[0]
                if row.get("total_revenue") is not None:
                    kpi_data["total_revenue"] = float(row["total_revenue"]) * 83.0
                if row.get("total_qty") is not None:
                    kpi_data["total_qty"] = int(row["total_qty"])
                if row.get("total_orders") is not None:
                    kpi_data["row_count"] = int(row["total_orders"])
                if kpi_data["row_count"] > 0:
                    kpi_data["average_order_value"] = kpi_data["total_revenue"] / kpi_data["row_count"]
        except Exception as e:
            print(f"   [RIA] Failed to fetch overall daily totals for KPIs: {e}")
    
    # ── Step 4: Call Report Tool ──
    report_content = report_tool(kpi_data, raw_data, sql_query, user_question)

    state["analysis_result"] = report_content
    state["report"] = report_content
    state["raw_query_data"] = raw_data

    print("[Restaurant Intelligent Agent] Complete")
    return state


# ═══════════════════════════════════════════════════════════
# ROUTER — Decides which agent runs next
# ═══════════════════════════════════════════════════════════

def router(state: AgentState) -> str:
    """Decide which node to call next based on current state."""
    if state.get("error"):
        return END

    # Data Engineer → Restaurant Intelligent Agent → END
    if state.get("extraction_status") == "pending":
        return "data_engineer"
    if state.get("extraction_status") == "done" and not state.get("analysis_result"):
        return "restaurant_intelligent_agent"
    return END


# ═══════════════════════════════════════════════════════════
# BUILD THE GRAPH
# ═══════════════════════════════════════════════════════════

def build_graph() -> StateGraph:
    """
    Build and compile the LangGraph workflow.
    """
    workflow = StateGraph(AgentState)

    # Add nodes
    workflow.add_node("data_engineer", data_engineer_node)
    workflow.add_node("restaurant_intelligent_agent", restaurant_intelligent_agent_node)

    # Set entry point
    workflow.set_entry_point("data_engineer")

    # Define edges
    workflow.add_edge("data_engineer", "restaurant_intelligent_agent")
    workflow.add_edge("restaurant_intelligent_agent", END)

    # Compile
    memory = MemorySaver()
    graph = workflow.compile(checkpointer=memory)

    return graph


# ═══════════════════════════════════════════════════════════
# MAIN — Run the agent
# ═══════════════════════════════════════════════════════════

def run_agent(question: str, thread_id: str = "day1"):
    """
    Run the full agent pipeline for a single user question.
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
    print(f"Zomato Orders AI Analyst")
    print(f"   Question: {question}")
    print(f"{'='*60}")

    result = graph.invoke(initial_state, config)

    print(f"\n{'='*60}")
    print("FINAL REPORT:")
    print(result.get("report", "No report generated"))
    print(f"{'='*60}")

    return result


if __name__ == "__main__":
    print("Zomato Orders — AI Business Analyst")
    print("   This is a STARTER SKELETON.")
    print("   Fill in the TODOs to make it work!\n")

    # Example: ask a question
    run_agent("How did my restaurant perform yesterday?")
