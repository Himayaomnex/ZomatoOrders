"""
Purely Pickles — MCP Server
============================
Local MCP server that simulates a restaurant's daily billing system export.

Start it:
    uv run mcp_server/server.py

Connect it to Claude Desktop or any MCP client via:
    {
        "mcpServers": {
            "purely-pickles": {
                "command": "uv",
                "args": ["run", "--directory", "/path/to/purely-pickles-analytics/mcp_server", "server.py"]
            }
        }
    }

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

# Ensure exports directory exists
EXPORTS_DIR.mkdir(exist_ok=True)

# ── MCP Server ──────────────────────────────────────────────
mcp = FastMCP(
    "Purely Pickles Billing System",
    instructions="Daily billing system export for Purely Pickles restaurants. "
    "Returns raw CSV data — just like a real billing system would.",
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


@mcp.tool()
def get_daily_orders(date: str) -> str:
    """
    Get ALL orders for a specific date as a CSV string.
    This is the PRIMARY tool — call this every "day" to get that day's billing data.

    The CSV contains: order_date, sales_qty, sales_amount, currency, user_id, r_id

    Example: get_daily_orders("2018-06-22")

    Returns a raw CSV string. Save it, extract it, clean it — that's YOUR job.
    """
    conn = _get_conn()
    cur = conn.cursor()

    cur.execute(
        """
        SELECT o.order_date, o.sales_qty, o.sales_amount, o.currency,
               o.user_id, o.r_id, r.name as restaurant_name, r.city,
               r.cuisine as restaurant_cuisine
        FROM orders o
        LEFT JOIN restaurants r ON o.r_id = r.id
        WHERE o.order_date = ?
        ORDER BY o.r_id
    """,
        (date,),
    )

    rows = cur.fetchall()
    conn.close()

    if not rows:
        return f"# No orders found for {date}. The day hasn't happened yet, or there were no orders."

    columns = [
        "order_date",
        "sales_qty",
        "sales_amount",
        "currency",
        "user_id",
        "r_id",
        "restaurant_name",
        "city",
        "restaurant_cuisine",
    ]

    csv_data = _rows_to_csv(rows, columns)

    # Also save to daily_exports/ folder (like a real billing system export)
    export_path = EXPORTS_DIR / f"orders_{date}.csv"
    with open(export_path, "w") as f:
        f.write(csv_data)

    return (
        f"# Orders for {date}: {len(rows)} orders\n"
        f"# Saved to: {export_path}\n\n"
        f"{csv_data}"
    )


@mcp.tool()
def get_order_date_range(start_date: str, end_date: str) -> str:
    """
    Get orders for a DATE RANGE. Use this for weekly/monthly reports.
    Returns the same CSV format but across multiple days.

    Example: get_order_date_range("2018-06-01", "2018-06-07")
    """
    conn = _get_conn()
    cur = conn.cursor()

    cur.execute(
        """
        SELECT o.order_date, o.sales_qty, o.sales_amount, o.currency,
               o.user_id, o.r_id, r.name as restaurant_name, r.city,
               r.cuisine as restaurant_cuisine
        FROM orders o
        LEFT JOIN restaurants r ON o.r_id = r.id
        WHERE o.order_date BETWEEN ? AND ?
        ORDER BY o.order_date, o.r_id
    """,
        (start_date, end_date),
    )

    rows = cur.fetchall()
    conn.close()

    if not rows:
        return f"# No orders found between {start_date} and {end_date}."

    columns = [
        "order_date",
        "sales_qty",
        "sales_amount",
        "currency",
        "user_id",
        "r_id",
        "restaurant_name",
        "city",
        "restaurant_cuisine",
    ]

    csv_data = _rows_to_csv(rows, columns)

    export_path = EXPORTS_DIR / f"orders_{start_date}_to_{end_date}.csv"
    with open(export_path, "w") as f:
        f.write(csv_data)

    return (
        f"# Orders {start_date} → {end_date}: {len(rows)} orders\n"
        f"# Saved to: {export_path}\n\n"
        f"{csv_data}"
    )


@mcp.tool()
def get_available_dates() -> str:
    """
    List ALL dates that have order data.
    Use this to know which dates you can query.
    Returns a CSV with: date, order_count
    """
    conn = _get_conn()
    cur = conn.cursor()

    cur.execute(
        """
        SELECT order_date, COUNT(*) as order_count
        FROM orders
        GROUP BY order_date
        ORDER BY order_date
    """
    )

    rows = cur.fetchall()
    conn.close()

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["date", "order_count"])
    for row in rows:
        writer.writerow([row["order_date"], row["order_count"]])

    return (
        f"# Available dates: {len(rows)} days (2017-2020)\n"
        f"# Each date has ~186 orders on average\n\n"
        f"{output.getvalue()}"
    )


@mcp.tool()
def get_restaurant_info(restaurant_id: int) -> str:
    """
    Get detailed info about a specific restaurant.
    Returns: name, city, rating, cuisine, cost.

    Example: get_restaurant_info(567335)
    """
    conn = _get_conn()
    cur = conn.cursor()

    cur.execute(
        """
        SELECT id, name, city, rating, rating_count, cost, cuisine
        FROM restaurants
        WHERE id = ?
    """,
        (restaurant_id,),
    )

    row = cur.fetchone()
    conn.close()

    if not row:
        return f"# Restaurant {restaurant_id} not found."

    return (
        f"Restaurant #{row['id']}: {row['name']}\n"
        f"  City:    {row['city']}\n"
        f"  Rating:  {row['rating']} ({row['rating_count']})\n"
        f"  Cost:    {row['cost']}\n"
        f"  Cuisine: {row['cuisine']}"
    )


@mcp.tool()
def get_schema_hints() -> str:
    """
    Get hints about the data structure.
    This does NOT give you the exact schema — you need to figure that out.
    Use these hints to design YOUR OWN database schema for storing processed data.
    """
    return """
═══════════════════════════════════════════════════════════
SCHEMA HINTS — Purely Pickles Billing System
═══════════════════════════════════════════════════════════

The daily CSV you receive contains these columns:

  order_date          — When the order was placed (YYYY-MM-DD)
  sales_qty           — Number of items in the order
  sales_amount        — Total bill amount (INR)
  currency            — Always "INR"
  user_id             — Which customer placed the order
  r_id                — Which restaurant fulfilled the order
  restaurant_name     — Restaurant name (joined from restaurants table)
  city                — City where the restaurant is located
  restaurant_cuisine  — What type of food (e.g., "North Indian", "Bakery")

There are also SEPARATE data sources available:

  Restaurants:
    - id (links to orders.r_id — this is a FOREIGN KEY)
    - name, city, rating, cost, cuisine

  Food items:
    - f_id (unique food identifier)
    - item name, veg_or_non_veg

  Menu:
    - Links restaurants to food items with prices
    - r_id → restaurants.id, f_id → food.f_id

  Users:
    - user_id (links to orders.user_id — this is a FOREIGN KEY)
    - name, email, gender, occupation, income, education

═══════════════════════════════════════════════════════════
YOUR JOB:
  1. Read these hints
  2. Design YOUR OWN Supabase tables with proper:
     - Primary Keys (PK)
     - Foreign Keys (FK)
     - Column types (TEXT, INTEGER, NUMERIC, DATE)
  3. Write extraction + cleaning code to transform the CSV
     into rows that fit YOUR schema
  4. Store the cleaned data in YOUR Supabase database
  5. Query YOUR database to answer business questions

  Hint: orders.r_id → restaurants.id (FK)
  Hint: orders.user_id → users.user_id (FK)
  Hint: A single order can have multiple items
═══════════════════════════════════════════════════════════
"""


@mcp.tool()
def get_todays_date_sim() -> str:
    """
    Returns the CURRENT simulated date. Call this to know "what day it is."
    The simulation starts at 2017-10-04 and advances one day each time you
    call get_daily_orders() with a new date.

    Think of this as: "What date did the billing system just export?"
    """
    # Check the most recent export file
    exports = sorted(EXPORTS_DIR.glob("orders_*.csv"))
    if not exports:
        return "No orders exported yet. Start with: get_daily_orders('2017-10-04')"

    # Get the latest exported date
    latest = exports[-1].stem.replace("orders_", "")
    return (
        f"Last exported date: {latest}\n"
        f"Next available dates (check get_available_dates() for the full list)\n"
        f"Tip: Call get_daily_orders() with the next date to simulate a new day."
    )


# ── Main ────────────────────────────────────────────────────
if __name__ == "__main__":
    if not DB_PATH.exists():
        print("❌ zomato.db not found!")
        print("   Run setup.py first:  python setup.py")
        exit(1)

    print("🍋 Purely Pickles Billing System — MCP Server")
    print(f"   Database: {DB_PATH}")
    print(f"   Exports:  {EXPORTS_DIR}")
    print(f"   Status:   Ready to serve daily CSVs\n")
    mcp.run()
