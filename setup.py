"""
Purely Pickles Analytics — Setup Script
========================================
Run ONCE after cloning the repo. This:
1. Extracts zomato_data.zip (if needed)
2. Creates SQLite database with all Zomato CSVs
3. Builds indexes for fast date-based queries
4. Prints a summary so you know the data is ready

Usage:
    python setup.py
"""

import sqlite3
import zipfile
import csv
import os
import sys
from pathlib import Path

# ── Configuration ───────────────────────────────────────────
BASE_DIR = Path(__file__).parent
DATA_DIR = BASE_DIR / "data"
DB_PATH = BASE_DIR / "zomato.db"
ZIP_PATH = DATA_DIR / "zomato_data.zip"

CSV_FILES = {
    "orders": {
        "file": "orders.csv",
        "table": "orders",
        "columns": [
            ("order_date", "TEXT"),
            ("sales_qty", "INTEGER"),
            ("sales_amount", "REAL"),
            ("currency", "TEXT"),
            ("user_id", "INTEGER"),
            ("r_id", "INTEGER"),
        ],
    },
    "restaurants": {
        "file": "restaurant.csv",
        "table": "restaurants",
        "columns": [
            ("id", "INTEGER PRIMARY KEY"),
            ("name", "TEXT"),
            ("city", "TEXT"),
            ("rating", "TEXT"),
            ("rating_count", "TEXT"),
            ("cost", "TEXT"),
            ("cuisine", "TEXT"),
        ],
    },
    "food": {
        "file": "food.csv",
        "table": "food",
        "columns": [
            ("f_id", "TEXT PRIMARY KEY"),
            ("item", "TEXT"),
            ("veg_or_non_veg", "TEXT"),
        ],
    },
    "menu": {
        "file": "menu.csv",
        "table": "menu",
        "columns": [
            ("menu_id", "TEXT PRIMARY KEY"),
            ("r_id", "INTEGER"),
            ("f_id", "TEXT"),
            ("cuisine", "TEXT"),
            ("price", "REAL"),
        ],
    },
    "users": {
        "file": "users.csv",
        "table": "users",
        "columns": [
            ("user_id", "INTEGER PRIMARY KEY"),
            ("name", "TEXT"),
            ("email", "TEXT"),
            ("gender", "TEXT"),
            ("occupation", "TEXT"),
            ("monthly_income", "TEXT"),
            ("education", "TEXT"),
            ("family_size", "TEXT"),
        ],
    },
}


def extract_zip():
    """Extract zomato_data.zip if it exists and CSVs aren't already present."""
    if not ZIP_PATH.exists():
        print(f"⚠️  {ZIP_PATH} not found. If CSVs are already in {DATA_DIR}, skipping.")
        return

    # Check if CSVs already extracted
    already_extracted = all(
        (DATA_DIR / cfg["file"]).exists() for cfg in CSV_FILES.values()
    )
    if already_extracted:
        print("✓ All CSVs already extracted. Skipping unzip.")
        return

    print(f"📦 Extracting {ZIP_PATH}...")
    with zipfile.ZipFile(ZIP_PATH, "r") as zf:
        zf.extractall(DATA_DIR)
    print("✓ Extraction complete.")


def create_database():
    """Create SQLite database and all tables."""
    if DB_PATH.exists():
        DB_PATH.unlink()
        print("🗑️  Removed existing database.")

    conn = sqlite3.connect(str(DB_PATH))
    cur = conn.cursor()

    for cfg in CSV_FILES.values():
        col_defs = ", ".join(f"{name} {dtype}" for name, dtype in cfg["columns"])
        cur.execute(f"CREATE TABLE IF NOT EXISTS {cfg['table']} ({col_defs})")
        print(f"✓ Created table: {cfg['table']}")

    # Indexes for performance
    cur.execute("CREATE INDEX IF NOT EXISTS idx_orders_date ON orders(order_date)")
    cur.execute("CREATE INDEX IF NOT EXISTS idx_orders_rid ON orders(r_id)")
    cur.execute("CREATE INDEX IF NOT EXISTS idx_menu_rid ON menu(r_id)")
    print("✓ Created indexes")

    conn.commit()
    return conn


def load_csvs(conn):
    """Load all CSVs into SQLite."""
    cur = conn.cursor()

    # Track the first column which is a row index (skip it)
    INDEX_COLUMNS = {"orders": 1, "restaurants": 1, "food": 1, "menu": 1, "users": 1}

    # Cleaners: post-processing per table
    # orders.csv has r_id as float (e.g., "567335.0") — strip .0
    def clean_orders(data):
        if len(data) >= 6:
            # r_id is index 5 — strip .0 suffix
            if data[5] and data[5].endswith(".0"):
                data[5] = data[5][:-2]
        return data

    CLEANERS = {"orders": clean_orders}

    for cfg in CSV_FILES.values():
        csv_path = DATA_DIR / cfg["file"]
        if not csv_path.exists():
            print(f"❌ {csv_path} not found! Make sure the data is extracted.")
            continue

        print(f"📥 Loading {cfg['table']} from {cfg['file']}...")
        skip_cols = INDEX_COLUMNS.get(cfg["table"], 0)
        col_names = [c[0] for c in cfg["columns"]]
        placeholders = ", ".join("?" for _ in col_names)

        with open(csv_path, "r", encoding="utf-8") as f:
            reader = csv.reader(f)
            header = next(reader)

            batch = []
            batch_size = 5000
            count = 0

            for row in reader:
                # Skip the first N index columns
                data = row[skip_cols : skip_cols + len(col_names)]

                # Apply table-specific cleaner
                cleaner = CLEANERS.get(cfg["table"])
                if cleaner:
                    data = cleaner(data)

                batch.append(data)
                count += 1

                if len(batch) >= batch_size:
                    cur.executemany(
                        f"INSERT OR REPLACE INTO {cfg['table']} ({', '.join(col_names)}) VALUES ({placeholders})",
                        batch,
                    )
                    batch = []

            # Final batch
            if batch:
                cur.executemany(
                    f"INSERT OR REPLACE INTO {cfg['table']} ({', '.join(col_names)}) VALUES ({placeholders})",
                    batch,
                )

            conn.commit()
            print(f"   ✓ Loaded {count:,} rows into {cfg['table']}")


def verify(conn):
    """Print summary statistics."""
    cur = conn.cursor()
    print("\n" + "=" * 55)
    print("📊 DATABASE SUMMARY")
    print("=" * 55)

    for cfg in CSV_FILES.values():
        cur.execute(f"SELECT COUNT(*) FROM {cfg['table']}")
        count = cur.fetchone()[0]
        print(f"  {cfg['table']:<20} {count:>10,} rows")

    cur.execute(
        "SELECT MIN(order_date), MAX(order_date), COUNT(DISTINCT order_date) FROM orders"
    )
    min_date, max_date, unique_dates = cur.fetchone()
    print(f"\n  📅 Date range:     {min_date} → {max_date}")
    print(f"  📅 Unique dates:   {unique_dates}")

    cur.execute("SELECT COUNT(*) FROM orders")
    total_orders = cur.fetchone()[0]
    print(f"  📦 Total orders:   {total_orders:,}")
    print(f"  📦 Avg/day:        {total_orders // unique_dates}")

    print("\n✅ Database is ready! Run the MCP server to start:")
    print("   cd mcp_server && uv run server.py\n")


def main():
    print("🍋 Purely Pickles Analytics — Setup\n")
    extract_zip()
    conn = create_database()
    load_csvs(conn)
    verify(conn)
    conn.close()


if __name__ == "__main__":
    main()
