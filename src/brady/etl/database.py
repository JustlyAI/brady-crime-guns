#!/usr/bin/env python3
"""
Brady Gun Center - Database Module
Supports PostgreSQL (Railway) and SQLite (local development)

Uses DATABASE_URL environment variable for PostgreSQL connection.
Falls back to SQLite when DATABASE_URL is not set.
"""

import os
import sqlite3
from contextlib import contextmanager
from pathlib import Path
from typing import Literal, Optional, Union

import pandas as pd
from termcolor import cprint

from brady.utils import get_project_root

# Type alias for database connections
try:
    import psycopg2.extensions
    Connection = Union[sqlite3.Connection, psycopg2.extensions.connection]
except ImportError:
    Connection = sqlite3.Connection  # type: ignore


def get_database_url() -> Optional[str]:
    """Get DATABASE_URL from environment. Returns None for SQLite fallback."""
    return os.environ.get("DATABASE_URL")


def is_postgres() -> bool:
    """Check if we're using PostgreSQL (DATABASE_URL is set)."""
    url = get_database_url()
    return url is not None and url.startswith(("postgres://", "postgresql://"))


def get_db_path() -> Path:
    """Get the SQLite database path (for local development)."""
    return get_project_root() / "data" / "brady.db"


# PostgreSQL schema
SCHEMA_POSTGRES = """
CREATE TABLE IF NOT EXISTS crime_gun_events (
    id SERIAL PRIMARY KEY,

    -- Source traceability
    source_dataset TEXT,
    source_sheet TEXT,
    source_row INTEGER,

    -- Existing jurisdiction fields (from ETL)
    jurisdiction_state TEXT,
    jurisdiction_city TEXT,
    jurisdiction_method TEXT,
    jurisdiction_confidence TEXT,

    -- Crime location fields (populated by classifier agents)
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
    sale_date TEXT,
    crime_date TEXT,
    time_to_crime INTEGER,
    court TEXT,
    case_number_clean TEXT,

    -- Risk indicators
    has_nibin INTEGER DEFAULT 0,
    has_trafficking_indicia INTEGER DEFAULT 0,
    is_interstate INTEGER DEFAULT 0,

    -- Crime Gun DB specific fields
    in_dl2_program INTEGER,
    is_top_trace_ffl INTEGER,
    is_revoked INTEGER,
    is_charged_or_sued INTEGER,
    case_name TEXT,
    trafficking_origin TEXT,
    trafficking_destination TEXT,
    is_southwest_border INTEGER,
    facts_narrative TEXT,

    -- Narrative
    case_summary TEXT,

    -- Metadata
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Indexes for common queries
CREATE INDEX IF NOT EXISTS idx_jurisdiction_state ON crime_gun_events(jurisdiction_state);
CREATE INDEX IF NOT EXISTS idx_crime_location_state ON crime_gun_events(crime_location_state);
CREATE INDEX IF NOT EXISTS idx_dealer_name ON crime_gun_events(dealer_name);
CREATE INDEX IF NOT EXISTS idx_manufacturer_name ON crime_gun_events(manufacturer_name);
CREATE INDEX IF NOT EXISTS idx_time_to_crime ON crime_gun_events(time_to_crime);
CREATE INDEX IF NOT EXISTS idx_court ON crime_gun_events(court);
CREATE INDEX IF NOT EXISTS idx_source_dataset ON crime_gun_events(source_dataset);
CREATE INDEX IF NOT EXISTS idx_trafficking_destination ON crime_gun_events(trafficking_destination);
"""

# SQLite schema (uses AUTOINCREMENT)
SCHEMA_SQLITE = """
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

    -- Crime location fields (populated by classifier agents)
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
    sale_date TEXT,
    crime_date TEXT,
    time_to_crime INTEGER,
    court TEXT,
    case_number_clean TEXT,

    -- Risk indicators
    has_nibin INTEGER DEFAULT 0,
    has_trafficking_indicia INTEGER DEFAULT 0,
    is_interstate INTEGER DEFAULT 0,

    -- Crime Gun DB specific fields
    in_dl2_program INTEGER,
    is_top_trace_ffl INTEGER,
    is_revoked INTEGER,
    is_charged_or_sued INTEGER,
    case_name TEXT,
    trafficking_origin TEXT,
    trafficking_destination TEXT,
    is_southwest_border INTEGER,
    facts_narrative TEXT,

    -- Narrative
    case_summary TEXT,

    -- Metadata
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Indexes for common queries
CREATE INDEX IF NOT EXISTS idx_jurisdiction_state ON crime_gun_events(jurisdiction_state);
CREATE INDEX IF NOT EXISTS idx_crime_location_state ON crime_gun_events(crime_location_state);
CREATE INDEX IF NOT EXISTS idx_dealer_name ON crime_gun_events(dealer_name);
CREATE INDEX IF NOT EXISTS idx_manufacturer_name ON crime_gun_events(manufacturer_name);
CREATE INDEX IF NOT EXISTS idx_time_to_crime ON crime_gun_events(time_to_crime);
CREATE INDEX IF NOT EXISTS idx_court ON crime_gun_events(court);
CREATE INDEX IF NOT EXISTS idx_source_dataset ON crime_gun_events(source_dataset);
CREATE INDEX IF NOT EXISTS idx_trafficking_destination ON crime_gun_events(trafficking_destination);
"""


# Crime Gun DB specific columns for migrations
CRIME_GUN_DB_COLUMNS = [
    ('in_dl2_program', 'INTEGER'),
    ('is_top_trace_ffl', 'INTEGER'),
    ('is_revoked', 'INTEGER'),
    ('is_charged_or_sued', 'INTEGER'),
    ('case_name', 'TEXT'),
    ('trafficking_origin', 'TEXT'),
    ('trafficking_destination', 'TEXT'),
    ('is_southwest_border', 'INTEGER'),
    ('facts_narrative', 'TEXT'),
]


def _get_postgres_connection():
    """Get a PostgreSQL connection using DATABASE_URL."""
    import psycopg2

    url = get_database_url()
    if not url:
        raise ValueError("DATABASE_URL not set")

    cprint(f"Connecting to PostgreSQL...", "cyan")
    conn = psycopg2.connect(url)
    return conn


def _get_sqlite_connection(db_path: Optional[Path] = None) -> sqlite3.Connection:
    """Get a SQLite connection."""
    if db_path is None:
        db_path = get_db_path()

    return sqlite3.connect(str(db_path))


@contextmanager
def get_connection(db_path: Optional[Path] = None):
    """
    Get a database connection (PostgreSQL or SQLite).

    Uses DATABASE_URL if set, otherwise falls back to SQLite.
    Returns a context manager that handles connection cleanup.

    Usage:
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM crime_gun_events")
    """
    if is_postgres():
        conn = _get_postgres_connection()
        try:
            yield conn
        finally:
            conn.close()
    else:
        if db_path is None:
            db_path = get_db_path()
        conn = sqlite3.connect(str(db_path))
        try:
            yield conn
        finally:
            conn.close()


def get_placeholder() -> str:
    """Get the parameter placeholder for the current database."""
    return "%s" if is_postgres() else "?"


def init_db(db_path: Optional[Path] = None) -> Connection:
    """Initialize the database with schema."""
    if is_postgres():
        cprint("Initializing PostgreSQL database...", "cyan")
        conn = _get_postgres_connection()
        cursor = conn.cursor()

        # Execute schema (PostgreSQL version)
        cursor.execute(SCHEMA_POSTGRES)
        conn.commit()

        cprint("PostgreSQL database schema created successfully", "green")
        return conn
    else:
        if db_path is None:
            db_path = get_db_path()

        db_path.parent.mkdir(parents=True, exist_ok=True)
        cprint(f"Initializing SQLite database at {db_path}", "cyan")

        conn = sqlite3.connect(str(db_path))
        conn.executescript(SCHEMA_SQLITE)
        conn.commit()

        cprint("SQLite database schema created successfully", "green")
        return conn


def _get_existing_columns(conn: Connection, table_name: str = "crime_gun_events") -> set:
    """Get set of existing column names in a table."""
    if is_postgres():
        cursor = conn.cursor()
        cursor.execute("""
            SELECT column_name
            FROM information_schema.columns
            WHERE table_name = %s
        """, (table_name,))
        return {row[0] for row in cursor.fetchall()}
    else:
        cursor = conn.cursor()
        cursor.execute(f"PRAGMA table_info({table_name})")
        return {row[1] for row in cursor.fetchall()}


def migrate_add_computed_columns(db_path: Optional[Path] = None) -> bool:
    """
    Add computed columns to existing database if they don't exist.

    Returns:
        True if migration was needed/performed, False if columns already exist
    """
    if is_postgres():
        conn = _get_postgres_connection()
    else:
        if db_path is None:
            db_path = get_db_path()
        if not db_path.exists():
            return False
        conn = sqlite3.connect(str(db_path))

    columns = _get_existing_columns(conn, "crime_gun_events")
    new_columns = ['sale_date', 'crime_date', 'time_to_crime', 'court', 'case_number_clean']
    missing = [col for col in new_columns if col not in columns]

    if not missing:
        cprint("Computed columns already exist in database", "green")
        conn.close()
        return False

    cprint(f"Adding missing columns: {missing}", "yellow")
    cursor = conn.cursor()

    for col in missing:
        col_type = 'INTEGER' if col == 'time_to_crime' else 'TEXT'
        try:
            cursor.execute(f"ALTER TABLE crime_gun_events ADD COLUMN {col} {col_type}")
            cprint(f"  Added column: {col}", "green")
        except Exception as e:
            if "duplicate column" not in str(e).lower() and "already exists" not in str(e).lower():
                cprint(f"  Warning: Could not add column {col}: {e}", "yellow")

    conn.commit()
    conn.close()
    cprint("Migration complete", "green")
    return True


def migrate_add_crime_gun_db_columns(db_path: Optional[Path] = None) -> bool:
    """
    Add Crime Gun DB specific columns to existing database if they don't exist.

    Returns:
        True if migration was needed/performed, False if columns already exist
    """
    if is_postgres():
        conn = _get_postgres_connection()
    else:
        if db_path is None:
            db_path = get_db_path()
        if not db_path.exists():
            return False
        conn = sqlite3.connect(str(db_path))

    existing_columns = _get_existing_columns(conn, "crime_gun_events")
    missing = [(col, col_type) for col, col_type in CRIME_GUN_DB_COLUMNS
               if col not in existing_columns]

    if not missing:
        cprint("Crime Gun DB columns already exist in database", "green")
        conn.close()
        return False

    cprint(f"Adding Crime Gun DB columns: {[c[0] for c in missing]}", "yellow")
    cursor = conn.cursor()

    for col, col_type in missing:
        try:
            cursor.execute(f"ALTER TABLE crime_gun_events ADD COLUMN {col} {col_type}")
            cprint(f"  Added column: {col}", "green")
        except Exception as e:
            if "duplicate column" not in str(e).lower() and "already exists" not in str(e).lower():
                cprint(f"  Warning: Could not add column {col}: {e}", "yellow")

    conn.commit()
    conn.close()
    cprint("Crime Gun DB migration complete", "green")
    return True


def load_df_to_db(df: pd.DataFrame, table_name: str = "crime_gun_events",
                  db_path: Optional[Path] = None,
                  if_exists: Literal["fail", "replace", "append"] = "replace") -> int:
    """
    Load a DataFrame into the database.

    Args:
        df: DataFrame to load
        table_name: Target table name
        db_path: Optional database path (SQLite only)
        if_exists: 'replace', 'append', or 'fail'

    Returns:
        Number of rows inserted
    """
    # Add missing columns to DataFrame
    new_columns = [
        'crime_location_state', 'crime_location_city', 'crime_location_zip',
        'crime_location_court', 'crime_location_pd', 'crime_location_reasoning',
        'sale_date', 'crime_date', 'time_to_crime', 'court', 'case_number_clean',
        'in_dl2_program', 'is_top_trace_ffl', 'is_revoked', 'is_charged_or_sued',
        'case_name', 'trafficking_origin', 'trafficking_destination',
        'is_southwest_border', 'facts_narrative',
    ]

    for col in new_columns:
        if col not in df.columns:
            df[col] = None

    # Convert boolean columns to integers
    bool_cols = [
        'has_nibin', 'has_trafficking_indicia', 'is_interstate',
        'in_dl2_program', 'is_top_trace_ffl', 'is_revoked',
        'is_charged_or_sued', 'is_southwest_border'
    ]
    for col in bool_cols:
        if col in df.columns:
            df[col] = df[col].apply(lambda x: int(x) if pd.notna(x) and x is not None else None)

    cprint(f"Loading {len(df)} records to {table_name}...", "yellow")

    if is_postgres():
        from sqlalchemy import create_engine

        url = get_database_url()
        if url is None:
            raise ValueError("DATABASE_URL not set")
        # SQLAlchemy needs postgresql:// not postgres://
        if url.startswith("postgres://"):
            url = url.replace("postgres://", "postgresql://", 1)

        engine = create_engine(url)
        df.to_sql(table_name, engine, if_exists=if_exists, index=False)
        engine.dispose()
    else:
        if db_path is None:
            db_path = get_db_path()

        if not db_path.exists():
            init_db(db_path)

        conn = sqlite3.connect(str(db_path))
        df.to_sql(table_name, conn, if_exists=if_exists, index=False)
        conn.commit()
        conn.close()

    cprint(f"Loaded {len(df)} records to database", "green")
    return len(df)


def query_db(sql: str, db_path: Optional[Path] = None, params: Optional[tuple] = None) -> pd.DataFrame:
    """Execute a SQL query and return results as DataFrame."""
    if is_postgres():
        from sqlalchemy import create_engine
        from sqlalchemy import text

        url = get_database_url()
        if url is None:
            raise ValueError("DATABASE_URL not set")
        # SQLAlchemy needs postgresql:// not postgres://
        if url.startswith("postgres://"):
            url = url.replace("postgres://", "postgresql://", 1)

        engine = create_engine(url)
        if params:
            result = pd.read_sql_query(text(sql), engine, params=dict(enumerate(params)))
        else:
            result = pd.read_sql_query(sql, engine)
        engine.dispose()
        return result
    else:
        if db_path is None:
            db_path = get_db_path()

        with sqlite3.connect(str(db_path)) as conn:
            if params:
                return pd.read_sql_query(sql, conn, params=list(params))
            return pd.read_sql_query(sql, conn)


def get_all_events(db_path: Optional[Path] = None) -> pd.DataFrame:
    """Get all crime gun events from the database."""
    return query_db("SELECT * FROM crime_gun_events", db_path)


def get_events_by_state(state: str, db_path: Optional[Path] = None) -> pd.DataFrame:
    """Get crime gun events for a specific jurisdiction state."""
    placeholder = get_placeholder()
    sql = f"SELECT * FROM crime_gun_events WHERE jurisdiction_state = {placeholder}"
    return query_db(sql, db_path, params=(state,))


def get_summary_stats(db_path: Optional[Path] = None) -> dict:
    """Get summary statistics from the database."""
    with get_connection(db_path) as conn:
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
        result = cursor.fetchone()[0]
        stats['interstate_count'] = int(result) if result else 0

        # Crime location coverage
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
        record_id: Database row ID (rowid for SQLite, id for PostgreSQL)
    """
    placeholder = get_placeholder()

    # Use 'id' for PostgreSQL, 'rowid' for SQLite
    id_column = "id" if is_postgres() else "rowid"

    with get_connection(db_path) as conn:
        cursor = conn.cursor()

        sql = f"""
            UPDATE crime_gun_events
            SET crime_location_state = {placeholder},
                crime_location_city = {placeholder},
                crime_location_zip = {placeholder},
                crime_location_court = {placeholder},
                crime_location_pd = {placeholder},
                crime_location_reasoning = {placeholder}
            WHERE {id_column} = {placeholder}
        """

        cursor.execute(sql, (state, city, zip_code, court, pd, reasoning, record_id))
        conn.commit()
        return cursor.rowcount > 0


def delete_by_source_dataset(datasets: list[str], db_path: Optional[Path] = None) -> int:
    """
    Delete records by source_dataset values.

    Args:
        datasets: List of source_dataset values to delete
        db_path: Optional database path (SQLite only)

    Returns:
        Number of rows deleted
    """
    if not datasets:
        return 0

    placeholder = get_placeholder()
    placeholders = ", ".join([placeholder] * len(datasets))
    sql = f"DELETE FROM crime_gun_events WHERE source_dataset IN ({placeholders})"

    with get_connection(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute(sql, tuple(datasets))
        deleted = cursor.rowcount
        conn.commit()
        return deleted


def count_by_source_dataset(datasets: list[str], db_path: Optional[Path] = None) -> int:
    """
    Count records by source_dataset values.

    Args:
        datasets: List of source_dataset values to count
        db_path: Optional database path (SQLite only)

    Returns:
        Number of matching rows
    """
    if not datasets:
        return 0

    placeholder = get_placeholder()
    placeholders = ", ".join([placeholder] * len(datasets))
    sql = f"SELECT COUNT(*) FROM crime_gun_events WHERE source_dataset IN ({placeholders})"

    with get_connection(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute(sql, tuple(datasets))
        return cursor.fetchone()[0]


if __name__ == "__main__":
    cprint("=" * 60, "cyan")
    cprint("TESTING DATABASE MODULE", "cyan", attrs=["bold"])
    cprint("=" * 60, "cyan")

    if is_postgres():
        cprint("Using PostgreSQL (DATABASE_URL is set)", "green")
    else:
        cprint("Using SQLite (local development)", "yellow")

    conn = init_db()

    # Check if table exists
    if is_postgres():
        cursor = conn.cursor()
        cursor.execute("""
            SELECT EXISTS (
                SELECT FROM information_schema.tables
                WHERE table_name = 'crime_gun_events'
            )
        """)
        exists = cursor.fetchone()[0]
    else:
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='crime_gun_events'")
        exists = cursor.fetchone() is not None

    if exists:
        cprint("Table 'crime_gun_events' created successfully", "green")
    else:
        cprint("Table creation failed", "red")

    conn.close()

    if not is_postgres():
        cprint(f"\nDatabase location: {get_db_path()}", "yellow")
