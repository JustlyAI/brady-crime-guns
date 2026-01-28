# Database Schema Guide

This document describes the unified schema for the Brady Gun Center crime gun events database.

## Overview

The database uses a single unified table (`crime_gun_events`) that stores all crime gun records from multiple data sources. The schema supports both SQLite (local development) and PostgreSQL (production deployment).

## Table: `crime_gun_events`

### Source Traceability

Every record maintains full traceability to its original source.

| Column | Type | Description |
|--------|------|-------------|
| `id` | INTEGER | Auto-incrementing primary key |
| `source_dataset` | TEXT | Dataset identifier (see [Datasets](#datasets)) |
| `source_sheet` | TEXT | Original Excel sheet name |
| `source_row` | INTEGER | Original row number in source file |

### Datasets

Three distinct datasets are supported:

| Dataset | Source | Records | State Inference |
|---------|--------|---------|-----------------|
| `DE_GUNSTAT` | DE_Gunstat_Final.xlsx | 635 | Assume "DE" |
| `PA_TRACE` | Crime_Gun_Dealer_DB.xlsx (Philadelphia Trace) | 50 | Assume "PA" |
| `CG_COURT_DOC` | Crime_Gun_Dealer_DB.xlsx (CG court doc FFLs) | 1,980 | Use `jurisdiction_state` |

### Jurisdiction Fields (ETL-Populated)

These fields are populated during ETL processing using a priority-based resolution chain.

| Column | Type | Description |
|--------|------|-------------|
| `jurisdiction_state` | TEXT | 2-letter state code where crime occurred |
| `jurisdiction_city` | TEXT | City name (when available) |
| `jurisdiction_method` | TEXT | How jurisdiction was determined (see below) |
| `jurisdiction_confidence` | TEXT | Confidence level (reserved for future use) |

#### Jurisdiction Methods

| Method | Description | Priority |
|--------|-------------|----------|
| `RECOVERY` | Extracted from recovery location text | 1 (highest) |
| `COURT` | Parsed from federal court abbreviation | 2 |
| `TRAFFICKING` | Derived from trafficking destination | 3 |
| `SHEET_DEFAULT` | Inferred from source sheet (Philadelphia=PA) | 4 |
| `DEALER_STATE` | Fallback to dealer location | 5 (lowest) |
| `UNKNOWN` | Could not determine jurisdiction | - |

### Crime Location Fields (Classifier-Populated)

These fields are populated by classifier agents for enhanced location data.

| Column | Type | Description |
|--------|------|-------------|
| `crime_location_state` | TEXT | Verified state code |
| `crime_location_city` | TEXT | Verified city name |
| `crime_location_zip` | TEXT | ZIP code (when available) |
| `crime_location_court` | TEXT | Court name/jurisdiction |
| `crime_location_pd` | TEXT | Police department |
| `crime_location_reasoning` | TEXT | Explanation of classification logic |

### Dealer Information (Tier 3)

FFL dealer details from source records.

| Column | Type | Description |
|--------|------|-------------|
| `dealer_name` | TEXT | FFL dealer business name |
| `dealer_city` | TEXT | Dealer city |
| `dealer_state` | TEXT | Dealer state (2-letter code) |
| `dealer_ffl` | TEXT | FFL license number |

### Manufacturer Information (Tier 1)

| Column | Type | Description |
|--------|------|-------------|
| `manufacturer_name` | TEXT | Firearm manufacturer name |

### Firearm Details

| Column | Type | Description |
|--------|------|-------------|
| `firearm_serial` | TEXT | Serial number |
| `firearm_caliber` | TEXT | Caliber/gauge |

### Case Information

| Column | Type | Description |
|--------|------|-------------|
| `defendant_name` | TEXT | Defendant name |
| `case_number` | TEXT | Original case number |
| `case_status` | TEXT | Case status |
| `case_name` | TEXT | Full case citation (CG_COURT_DOC) |
| `case_number_clean` | TEXT | Normalized case number |
| `court` | TEXT | Court identifier |

### Purchase Information

| Column | Type | Description |
|--------|------|-------------|
| `purchase_date` | TEXT | Date of firearm purchase |
| `purchaser_name` | TEXT | Original purchaser name |

### Timing Fields

| Column | Type | Description |
|--------|------|-------------|
| `time_to_recovery` | TEXT | Raw time-to-recovery text |
| `ttr_category` | TEXT | TTR category label |
| `sale_date` | TEXT | Computed sale date |
| `crime_date` | TEXT | Computed crime date |
| `time_to_crime` | INTEGER | Days from sale to crime (computed) |

### Risk Indicators

Boolean fields indicating trafficking risk factors. Stored as INTEGER (0/1/NULL).

| Column | Type | Description |
|--------|------|-------------|
| `has_nibin` | INTEGER | NIBIN hit indicator |
| `has_trafficking_indicia` | INTEGER | General trafficking indicators |
| `is_interstate` | INTEGER | Interstate transaction flag |
| `in_dl2_program` | INTEGER | FFL in Demand Letter 2 program |
| `is_top_trace_ffl` | INTEGER | FFL is a top trace dealer |
| `is_revoked` | INTEGER | FFL license revoked |
| `is_charged_or_sued` | INTEGER | FFL charged or sued |

### Trafficking Flow (CG_COURT_DOC only)

| Column | Type | Description |
|--------|------|-------------|
| `trafficking_origin` | TEXT | Origin state code |
| `trafficking_destination` | TEXT | Destination state code or "SWB" |
| `is_southwest_border` | INTEGER | Southwest border trafficking flag |

### Narrative Fields

| Column | Type | Description |
|--------|------|-------------|
| `facts_narrative` | TEXT | Facts from court documents |
| `case_summary` | TEXT | Summary narrative |

### Metadata

| Column | Type | Description |
|--------|------|-------------|
| `created_at` | TIMESTAMP | Record creation timestamp |
| `updated_at` | TIMESTAMP | Last update timestamp |

## Indexes

The following indexes are created for query optimization:

```sql
CREATE INDEX idx_jurisdiction_state ON crime_gun_events(jurisdiction_state);
CREATE INDEX idx_crime_location_state ON crime_gun_events(crime_location_state);
CREATE INDEX idx_dealer_name ON crime_gun_events(dealer_name);
CREATE INDEX idx_manufacturer_name ON crime_gun_events(manufacturer_name);
CREATE INDEX idx_time_to_crime ON crime_gun_events(time_to_crime);
CREATE INDEX idx_court ON crime_gun_events(court);
CREATE INDEX idx_source_dataset ON crime_gun_events(source_dataset);
CREATE INDEX idx_trafficking_destination ON crime_gun_events(trafficking_destination);
```

## Common Queries

### Count records by dataset

```sql
SELECT source_dataset, COUNT(*) as count
FROM crime_gun_events
GROUP BY source_dataset
ORDER BY count DESC;
```

### Dataset and sheet breakdown

```sql
SELECT source_dataset, source_sheet, COUNT(*) as count
FROM crime_gun_events
GROUP BY source_dataset, source_sheet
ORDER BY source_dataset;
```

### Jurisdiction method breakdown

```sql
SELECT jurisdiction_method, COUNT(*) as count,
       ROUND(100.0 * COUNT(*) / (SELECT COUNT(*) FROM crime_gun_events), 1) as pct
FROM crime_gun_events
GROUP BY jurisdiction_method
ORDER BY count DESC;
```

### Dealers by crime gun count

```sql
SELECT dealer_name, dealer_state, COUNT(*) as crime_guns
FROM crime_gun_events
WHERE dealer_name IS NOT NULL
GROUP BY dealer_name, dealer_state
ORDER BY crime_guns DESC
LIMIT 20;
```

### Interstate trafficking analysis

```sql
SELECT trafficking_origin, trafficking_destination, COUNT(*) as flows
FROM crime_gun_events
WHERE trafficking_origin IS NOT NULL
GROUP BY trafficking_origin, trafficking_destination
ORDER BY flows DESC;
```

### Time-to-crime statistics

```sql
SELECT
    source_dataset,
    COUNT(*) as total,
    SUM(CASE WHEN time_to_crime IS NOT NULL THEN 1 ELSE 0 END) as with_ttc,
    AVG(time_to_crime) as avg_ttc,
    MIN(time_to_crime) as min_ttc,
    MAX(time_to_crime) as max_ttc
FROM crime_gun_events
GROUP BY source_dataset;
```

### Risk indicator summary

```sql
SELECT
    SUM(in_dl2_program) as dl2_count,
    SUM(is_top_trace_ffl) as top_trace_count,
    SUM(is_revoked) as revoked_count,
    SUM(is_charged_or_sued) as charged_count
FROM crime_gun_events;
```

## Database Backends

### SQLite (Local Development)

Default location: `data/brady.db`

- Auto-incrementing IDs via `INTEGER PRIMARY KEY AUTOINCREMENT`
- Parameter placeholder: `?`
- Row ID access: `rowid`

### PostgreSQL (Production)

Connection via `DATABASE_URL` environment variable.

- Auto-incrementing IDs via `SERIAL PRIMARY KEY`
- Parameter placeholder: `%s`
- Row ID access: `id`

## Migrations

The database module includes migration functions to add new columns to existing databases:

- `migrate_add_computed_columns()` - Adds timing computed columns
- `migrate_add_crime_gun_db_columns()` - Adds CG_COURT_DOC-specific columns

Migrations are idempotent and safe to run multiple times.

## ETL Process

### Data Flow

```
Excel Files
    │
    ├── DE_Gunstat_Final.xlsx ──────► process_gunstat.py ──► DE_GUNSTAT
    │
    └── Crime_Gun_Dealer_DB.xlsx
            │
            ├── Philadelphia Trace ─► process_crime_gun_db.py ──► PA_TRACE
            │
            └── CG court doc FFLs ──► process_crime_gun_db.py ──► CG_COURT_DOC
                                                │
                                                ▼
                                        crime_gun_events table
```

### Idempotent Loading

ETL processes are idempotent:
1. Delete existing records matching `source_dataset`
2. Insert new records

This allows safe re-running without duplicates.
