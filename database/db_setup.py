"""
database/db_setup.py
---------------------
Creates the SQLite database (if it doesn't exist), builds the tables from
schema.sql, and seeds the three catalog tables (internships, projects,
learning_resources) from the CSV files in /data.

Run this once before starting the Flask app:
    python database/db_setup.py

It is safe to re-run: catalog tables are cleared and re-seeded each time,
but the `users` and `recommendation_history` tables are left untouched so
you don't lose profiles you've already created.
"""

import os
import sqlite3
import pandas as pd

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_PATH = os.path.join(BASE_DIR, "database", "database.db")
SCHEMA_PATH = os.path.join(BASE_DIR, "database", "schema.sql")
DATA_DIR = os.path.join(BASE_DIR, "data")

CSV_TO_TABLE = {
    "internships.csv": "internships",
    "projects.csv": "projects",
    "learning_resources.csv": "learning_resources",
}


def get_connection():
    """Return a SQLite connection to the project database."""
    return sqlite3.connect(DB_PATH)


def create_tables(conn):
    """Execute schema.sql to (re)create all tables."""
    with open(SCHEMA_PATH, "r") as f:
        schema_sql = f.read()
    conn.executescript(schema_sql)
    conn.commit()
    print("Tables created (or already existed).")


def seed_catalog_tables(conn):
    """Load CSV datasets into their matching SQLite tables."""
    for csv_file, table_name in CSV_TO_TABLE.items():
        csv_path = os.path.join(DATA_DIR, csv_file)
        df = pd.read_csv(csv_path)

        # Clear existing rows so re-running this script doesn't duplicate data.
        conn.execute(f"DELETE FROM {table_name}")

        df.to_sql(table_name, conn, if_exists="append", index=False)
        print(f"Seeded '{table_name}' with {len(df)} rows from {csv_file}.")

    conn.commit()


def initialize_database():
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = get_connection()
    try:
        create_tables(conn)
        seed_catalog_tables(conn)
    finally:
        conn.close()
    print(f"\nDatabase ready at: {DB_PATH}")


if __name__ == "__main__":
    initialize_database()
