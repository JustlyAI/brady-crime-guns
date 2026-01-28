#!/usr/bin/env python3
"""
Brady Gun Center - SQLite Database Module
MVP Version - Delaware Focus

Lightweight SQLite implementation for crime gun data storage.
"""

import sqlite3
import pandas as pd
from pathlib import Path
from typing import Literal, Optional
from termcolor import cprint

from brady.utils import get_project_root


def get_db_path() -> Path:
    """Get the SQLite database path."""
    return get_project_root() / "data" / "brady.db"


# Schema definition with new crime location columns
SCHEMA = """
CREATE TABLE IF NOT EXISTS crime_gun_events (
    id INTEGER PRIMARY KEY AUTOINCREMENT,

    -- Source traceability
    source_dataset TEXT,
    source_sheet TEXT,
    source_row INTEGER,

    -- Existing jurisdiction fields (from ETL)
    jurisdiction_state TEXT,
    jurisdiction_city TEXT,
    jurisdiction_method TEXT,
    jurisdiction_confidence TEXT,

    -- NEW: Crime location fields (to be populated by classifier agents)
    crime_location_state TEXT,
    crime_location_city TEXT,
    crime_location_zip TEXT,
    crime_location_court TEXT,
    crime_location_pd TEXT,
    crime_location_reasoning TEXT,

    -- Dealer (Tier 3)
    dealer_name TEXT,
    dealer_city TEXT,
    dealer_state TEXT,
    dealer_ffl TEXT,

    -- Manufacturer (Tier 1)
    manufacturer_name TEXT,

    -- Firearm details
    firearm_serial TEXT,
    firearm_caliber TEXT,

    -- Case info
    defendant_name TEXT,
    case_number TEXT,
    case_status TEXT,

    -- Purchase info
    purchase_date TEXT,
    purchaser_name TEXT,

    -- Timing (raw)
    time_to_recovery TEXT,
    ttr_category TEXT,

    -- Timing (computed)
    sale_date TEXT,           -- YYYY-MM-DD (normalized from purchase_date)
    crime_date TEXT,          -- YYYY-MM-DD (sale_date + time_to_recovery)
    time_to_crime INTEGER,    -- Days as integer
    court TEXT,               -- Full court name from lookup
    case_number_clean TEXT,   -- Normalized case number format

    -- Risk indicators
    has_nibin INTEGER DEFAULT 0,
    has_trafficking_indicia INTEGER DEFAULT 0,
    is_interstate INTEGER DEFAULT 0,

    -- Narrative
    case_summary TEXT,

    -- Metadata
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Index for common queries
CREATE INDEX IF NOT EXISTS idx_jurisdiction_state ON crime_gun_events(jurisdiction_state);
CREATE INDEX IF NOT EXISTS idx_crime_location_state ON crime_gun_events(crime_location_state);
CREATE INDEX IF NOT EXISTS idx_dealer_name ON crime_gun_events(dealer_name);
CREATE INDEX IF NOT EXISTS idx_manufacturer_name ON crime_gun_events(manufacturer_name);
CREATE INDEX IF NOT EXISTS idx_time_to_crime ON crime_gun_events(time_to_crime);
CREATE INDEX IF NOT EXISTS idx_court ON crime_gun_events(court);
"""


# Migration for adding computed columns to existing database
MIGRATION_COMPUTED_COLUMNS = """
-- Add computed timing columns if they don't exist
ALTER TABLE crime_gun_events ADD COLUMN sale_date TEXT;
ALTER TABLE crime_gun_events ADD COLUMN crime_date TEXT;
ALTER TABLE crime_gun_events ADD COLUMN time_to_crime INTEGER;
ALTER TABLE crime_gun_events ADD COLUMN court TEXT;
ALTER TABLE crime_gun_events ADD COLUMN case_number_clean TEXT;
"""


def init_db(db_path: Optional[Path] = None) -> sqlite3.Connection:
    """Initialize the SQLite database with schema."""
    if db_path is None:
        db_path = get_db_path()

    db_path.parent.mkdir(parents=True, exist_ok=True)

    cprint(f"Initializing database at {db_path}", "cyan")

    conn = sqlite3.connect(str(db_path))
    conn.executescript(SCHEMA)
    conn.commit()

    cprint("Database schema created successfully", "green")
    return conn


def get_connection(db_path: Optional[Path] = None) -> sqlite3.Connection:
    """Get a connection to the database."""
    if db_path is None:
        db_path = get_db_path()

    if not db_path.exists():
        return init_db(db_path)

    return sqlite3.connect(str(db_path))


def migrate_add_computed_columns(db_path: Optional[Path] = None) -> bool:
    """
    Add computed columns to existing database if they don't exist.

    Returns:
        True if migration was needed/performed, False if columns already exist
    """
    if db_path is None:
        db_path = get_db_path()

    if not db_path.exists():
        return False

    conn = sqlite3.connect(str(db_path))
    cursor = conn.cursor()

    # Check if columns already exist
    cursor.execute("PRAGMA table_info(crime_gun_events)")
    columns = {row[1] for row in cursor.fetchall()}

    new_columns = ['sale_date', 'crime_date', 'time_to_crime', 'court', 'case_number_clean']
    missing = [col for col in new_columns if col not in columns]

    if not missing:
        cprint("Computed columns already exist in database", "green")
        conn.close()
        return False

    cprint(f"Adding missing columns: {missing}", "yellow")

    for col in missing:
        if col == 'time_to_crime':
            col_type = 'INTEGER'
        else:
            col_type = 'TEXT'

        try:
            cursor.execute(f"ALTER TABLE crime_gun_events ADD COLUMN {col} {col_type}")
            cprint(f"  Added column: {col}", "green")
        except sqlite3.OperationalError as e:
            if "duplicate column name" not in str(e).lower():
                cprint(f"  Warning: Could not add column {col}: {e}", "yellow")

    conn.commit()
    conn.close()

    cprint("Migration complete", "green")
    return True


def load_df_to_db(df: pd.DataFrame, table_name: str = "crime_gun_events",
                  db_path: Optional[Path] = None,
                  if_exists: Literal["fail", "replace", "append"] = "replace") -> int:
    """
    Load a DataFrame into the SQLite database.

    Args:
        df: DataFrame to load
        table_name: Target table name
        db_path: Optional database path
        if_exists: 'replace', 'append', or 'fail'

    Returns:
        Number of rows inserted
    """
    if db_path is None:
        db_path = get_db_path()

    # Ensure database exists
    if not db_path.exists():
        init_db(db_path)

    conn = sqlite3.connect(str(db_path))

    # Add new columns if they don't exist in the DataFrame
    new_columns = [
        'crime_location_state',
        'crime_location_city',
        'crime_location_zip',
        'crime_location_court',
        'crime_location_pd',
        'crime_location_reasoning',
        # Computed timing columns
        'sale_date',
        'crime_date',
        'time_to_crime',
        'court',
        'case_number_clean',
    ]

    for col in new_columns:
        if col not in df.columns:
            df[col] = None

    # Convert boolean columns to integers for SQLite
    bool_cols = ['has_nibin', 'has_trafficking_indicia', 'is_interstate']
    for col in bool_cols:
        if col in df.columns:
            df[col] = df[col].astype(int)

    cprint(f"Loading {len(df)} records to {table_name}...", "yellow")

    df.to_sql(table_name, conn, if_exists=if_exists, index=False)

    conn.commit()
    conn.close()

    cprint(f"Loaded {len(df)} records to database", "green")
    return len(df)


def query_db(sql: str, db_path: Optional[Path] = None) -> pd.DataFrame:
    """Execute a SQL query and return results as DataFrame."""
    if db_path is None:
        db_path = get_db_path()

    with sqlite3.connect(str(db_path)) as conn:
        return pd.read_sql_query(sql, conn)


def get_all_events(db_path: Optional[Path] = None) -> pd.DataFrame:
    """Get all crime gun events from the database."""
    return query_db("SELECT * FROM crime_gun_events", db_path)


def get_events_by_state(state: str, db_path: Optional[Path] = None) -> pd.DataFrame:
    """Get crime gun events for a specific jurisdiction state."""
    if db_path is None:
        db_path = get_db_path()
    with sqlite3.connect(str(db_path)) as conn:
        return pd.read_sql_query(
            "SELECT * FROM crime_gun_events WHERE jurisdiction_state = ?",
            conn,
            params=[state]
        )


def get_summary_stats(db_path: Optional[Path] = None) -> dict:
    """Get summary statistics from the database."""
    if db_path is None:
        db_path = get_db_path()

    with sqlite3.connect(str(db_path)) as conn:
        cursor = conn.cursor()

        stats = {}

        # Total records
        cursor.execute("SELECT COUNT(*) FROM crime_gun_events")
        stats['total_records'] = cursor.fetchone()[0]

        # Unique dealers
        cursor.execute("SELECT COUNT(DISTINCT dealer_name) FROM crime_gun_events")
        stats['unique_dealers'] = cursor.fetchone()[0]

        # Unique manufacturers
        cursor.execute("SELECT COUNT(DISTINCT manufacturer_name) FROM crime_gun_events WHERE manufacturer_name IS NOT NULL")
        stats['unique_manufacturers'] = cursor.fetchone()[0]

        # Interstate count
        cursor.execute("SELECT SUM(is_interstate) FROM crime_gun_events")
        stats['interstate_count'] = cursor.fetchone()[0] or 0

        # Crime location coverage (new columns populated)
        cursor.execute("SELECT COUNT(*) FROM crime_gun_events WHERE crime_location_state IS NOT NULL")
        stats['crime_location_populated'] = cursor.fetchone()[0]

        return stats


def update_crime_location(record_id: int, state: str, city: str, zip_code: str,
                          court: str, pd: str, reasoning: str,
                          db_path: Optional[Path] = None) -> bool:
    """
    Update crime location fields for a specific record.
    Used by classifier agents to populate location data.

    Args:
        record_id: SQLite rowid of the record to update
    """
    if db_path is None:
        db_path = get_db_path()

    with sqlite3.connect(str(db_path)) as conn:
        cursor = conn.cursor()

        cursor.execute("""
            UPDATE crime_gun_events
            SET crime_location_state = ?,
                crime_location_city = ?,
                crime_location_zip = ?,
                crime_location_court = ?,
                crime_location_pd = ?,
                crime_location_reasoning = ?
            WHERE rowid = ?
        """, (state, city, zip_code, court, pd, reasoning, record_id))

        conn.commit()
        return cursor.rowcount > 0


if __name__ == "__main__":
    # Test database initialization
    cprint("=" * 60, "cyan")
    cprint("TESTING SQLITE DATABASE MODULE", "cyan", attrs=["bold"])
    cprint("=" * 60, "cyan")

    conn = init_db()

    # Check if table exists
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='crime_gun_events'")
    result = cursor.fetchone()

    if result:
        cprint("✅ Table 'crime_gun_events' created successfully", "green")
    else:
        cprint("❌ Table creation failed", "red")

    conn.close()

    cprint(f"\nDatabase location: {get_db_path()}", "yellow")
