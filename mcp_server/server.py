"""
Purely Pickles — MCP Server
============================
Local MCP server that simulates a restaurant's daily billing system export.

Start it:
    python mcp_server/server.py

Connect it to Claude Desktop or any MCP client.

AUTHENTICATION:
    This MCP requires an API key for all tool calls.
    Set PURELY_PICKLES_API_KEY in your .env file.
    Pass it as the first argument to every tool.

This MCP returns RAW CSV — just like a real billing system would export.
Your job is to extract, clean, and store this data in your own database.
"""

import sqlite3
import csv
import io
import os
from datetime import datetime, timedelta
from pathlib import Path

from mcp.server.fastmcp import FastMCP

# ── Configuration ───────────────────────────────────────────
BASE_DIR = Path(__file__).parent.parent
DB_PATH = BASE_DIR / "zomato.db"
EXPORTS_DIR = BASE_DIR / "daily_exports"
DOTENV_PATH = BASE_DIR / ".env"

# ── Authentication ──────────────────────────────────────────
# Load API key from .env file (if it exists)
if DOTENV_PATH.exists():
    with open(DOTENV_PATH) as f:
        for line in f:
            line = line.strip()
            if line.startswith("PURELY_PICKLES_API_KEY="):
                _key = line.split("=", 1)[1].strip().strip('"').strip("'")
                os.environ["PURELY_PICKLES_API_KEY"] = _key

EXPECTED_API_KEY = os.getenv("PURELY_PICKLES_API_KEY")

if not EXPECTED_API_KEY:
    print("⚠️  WARNING: PURELY_PICKLES_API_KEY not set!")
    print("   Create a .env file with your API key:")
    print("   cp .env.example .env")
    print("   Then add your key: PURELY_PICKLES_API_KEY=pp_live_xxxxx")
    print("   The server will run in training mode (all keys accepted).\n")

def _check_auth(api_key: str) -> bool:
    """Validate the API key. Returns True if valid, False otherwise."""
    expected = os.getenv("PURELY_PICKLES_API_KEY")
    if not expected:
        return True  # No key set — allow all (training mode)
    return api_key == expected

# Ensure exports directory exists
EXPORTS_DIR.mkdir(exist_ok=True)

# ── MCP Server ──────────────────────────────────────────────
mcp = FastMCP(
    "Purely Pickles Billing System",
    instructions="Daily billing system export for Purely Pickles restaurants. "
    "Returns raw CSV data — just like a real billing system would. "
    "Authentication: Pass your API key with every tool call.",
)

def _get_conn():
    """Get a read-only SQLite connection."""
    conn = sqlite3.connect(f"file:{DB_PATH}?mode=ro", uri=True)
    conn.row_factory = sqlite3.Row
    return conn

def _rows_to_csv(rows, columns):
    """Convert SQLite rows to CSV string."""
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(columns)
    for row in rows:
        writer.writerow([row[c] for c in columns])
    return output.getvalue()

# ── TOOLS ───────────────────────────────────────────────────
# ALL tools require an api_key parameter.
# This is how real MCP servers work — you authenticate before accessing data.

@mcp.tool()
def get_daily_orders(api_key: str, date: str) -> str:
    """
    Get ALL orders for a specific date as a CSV string.
    REQUIRED: api_key — Your Purely Pickles API key (.env)
    Example: get_daily_orders(api_key="pp_live_xxxxx", date="2018-06-22")
    Returns a raw CSV string. Save it, extract it, clean it — YOUR job.
    """
    if not _check_auth(api_key):
        return "UNAUTHORIZED: Invalid API key."

    conn = _get_conn()
    cur = conn.cursor()
    cur.execute("""
        SELECT o.order_date, o.sales_qty, o.sales_amount, o.currency,
               o.user_id, o.r_id, r.name as restaurant_name, r.city,
               r.cuisine as restaurant_cuisine
        FROM orders o
        LEFT JOIN restaurants r ON o.r_id = r.id
        WHERE o.order_date = ?
        ORDER BY o.r_id
    """, (date,))
    rows = cur.fetchall()
    conn.close()

    if not rows:
        return f"# No orders found for {date}."

    columns = ["order_date","sales_qty","sales_amount","currency","user_id","r_id","restaurant_name","city","restaurant_cuisine"]
    csv_data = _rows_to_csv(rows, columns)

    export_path = EXPORTS_DIR / f"orders_{date}.csv"
    with open(export_path, "w") as f:
        f.write(csv_data)

    return f"# Orders for {date}: {len(rows)} orders\n# Saved to: {export_path}\n\n{csv_data}"


@mcp.tool()
def get_order_date_range(api_key: str, start_date: str, end_date: str) -> str:
    """
    Get orders for a DATE RANGE. Use for weekly/monthly reports.
    REQUIRED: api_key — Your Purely Pickles API key
    Example: get_order_date_range(api_key="pp_live_xxxxx", start_date="2018-06-01", end_date="2018-06-07")
    """
    if not _check_auth(api_key):
        return "UNAUTHORIZED: Invalid API key."

    conn = _get_conn()
    cur = conn.cursor()
    cur.execute("""
        SELECT o.order_date, o.sales_qty, o.sales_amount, o.currency,
               o.user_id, o.r_id, r.name as restaurant_name, r.city,
               r.cuisine as restaurant_cuisine
        FROM orders o
        LEFT JOIN restaurants r ON o.r_id = r.id
        WHERE o.order_date BETWEEN ? AND ?
        ORDER BY o.order_date, o.r_id
    """, (start_date, end_date))
    rows = cur.fetchall()
    conn.close()

    if not rows:
        return f"# No orders found between {start_date} and {end_date}."

    columns = ["order_date","sales_qty","sales_amount","currency","user_id","r_id","restaurant_name","city","restaurant_cuisine"]
    csv_data = _rows_to_csv(rows, columns)

    export_path = EXPORTS_DIR / f"orders_{start_date}_to_{end_date}.csv"
    with open(export_path, "w") as f:
        f.write(csv_data)

    return f"# Orders {start_date} to {end_date}: {len(rows)} orders\n# Saved to: {export_path}\n\n{csv_data}"


@mcp.tool()
def get_available_dates(api_key: str) -> str:
    """
    List ALL dates that have order data. Returns CSV: date, order_count.
    REQUIRED: api_key — Your Purely Pickles API key
    """
    if not _check_auth(api_key):
        return "UNAUTHORIZED: Invalid API key."

    conn = _get_conn()
    cur = conn.cursor()
    cur.execute("SELECT order_date, COUNT(*) as order_count FROM orders GROUP BY order_date ORDER BY order_date")
    rows = cur.fetchall()
    conn.close()

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["date", "order_count"])
    for row in rows:
        writer.writerow([row["order_date"], row["order_count"]])

    return f"# Available dates: {len(rows)} days (2017-2020)\n# ~186 orders/day\n\n{output.getvalue()}"


@mcp.tool()
def get_restaurant_info(api_key: str, restaurant_id: int) -> str:
    """
    Get details about a specific restaurant.
    REQUIRED: api_key — Your Purely Pickles API key
    Example: get_restaurant_info(api_key="pp_live_xxxxx", restaurant_id=567335)
    """
    if not _check_auth(api_key):
        return "UNAUTHORIZED: Invalid API key."

    conn = _get_conn()
    cur = conn.cursor()
    cur.execute("SELECT id, name, city, rating, rating_count, cost, cuisine FROM restaurants WHERE id = ?", (restaurant_id,))
    row = cur.fetchone()
    conn.close()

    if not row:
        return f"# Restaurant {restaurant_id} not found."

    return f"Restaurant #{row['id']}: {row['name']}\n  City: {row['city']}\n  Rating: {row['rating']} ({row['rating_count']})\n  Cost: {row['cost']}\n  Cuisine: {row['cuisine']}"


@mcp.tool()
def get_schema_hints(api_key: str) -> str:
    """
    Get HINTS about the data structure — not the full schema.
    Use these to design YOUR OWN database.
    REQUIRED: api_key — Your Purely Pickles API key
    """
    if not _check_auth(api_key):
        return "UNAUTHORIZED: Invalid API key."

    return """
SCHEMA HINTS - Purely Pickles Billing System
=============================================

Daily CSV columns:
  order_date          - When the order was placed (YYYY-MM-DD)
  sales_qty           - Number of items in the order
  sales_amount        - Total bill amount (INR)
  currency            - Always "INR"
  user_id             - Which customer placed the order
  r_id                - Which restaurant fulfilled the order
  restaurant_name     - Restaurant name (joined)
  city                - City where the restaurant is located
  restaurant_cuisine  - Type of food

Other data sources (query separately):
  Restaurants: id, name, city, rating, cost, cuisine
  Food: f_id, item_name, veg_or_non_veg
  Menu: menu_id, r_id, f_id, cuisine, price
  Users: user_id, name, email, gender, occupation, income, education

FOREIGN KEY HINTS:
  orders.r_id -> restaurants.id
  orders.user_id -> users.user_id

YOUR JOB: Design YOUR OWN Supabase tables with proper PKs, FKs, and types.
"""


@mcp.tool()
def get_todays_date_sim(api_key: str) -> str:
    """
    Returns the current simulated date.
    REQUIRED: api_key — Your Purely Pickles API key
    """
    if not _check_auth(api_key):
        return "UNAUTHORIZED: Invalid API key."

    exports = sorted(EXPORTS_DIR.glob("orders_*.csv"))
    if not exports:
        return "No orders exported yet. Start with: get_daily_orders(api_key='...', date='2017-10-04')"

    latest = exports[-1].stem.replace("orders_", "")
    return f"Last exported date: {latest}\nTip: Call get_daily_orders() with the next date."


# ── Main ────────────────────────────────────────────────────
if __name__ == "__main__":
    if not DB_PATH.exists():
        print("zomato.db not found!")
        print("Run setup.py first:  python setup.py")
        exit(1)

    print("Purely Pickles Billing System - MCP Server")
    print(f"  Database: {DB_PATH}")
    print(f"  Exports:  {EXPORTS_DIR}")
    print(f"  Auth:     {'ENABLED' if EXPECTED_API_KEY else 'TRAINING MODE (all keys accepted)'}")
    print(f"  Status:   Ready\n")
    mcp.run()
