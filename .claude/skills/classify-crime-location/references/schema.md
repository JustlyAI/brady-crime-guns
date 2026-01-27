# Crime Location Classification Schema

## Data Source

Primary: SQLite database at `data/brady.db`
Table: `crime_gun_events`

## Target Output Fields

| Field | Type | Description | Example |
|-------|------|-------------|---------|
| `crime_location_state` | TEXT | State where crime occurred | "DE", "PA" |
| `crime_location_city` | TEXT | City where crime occurred | "Wilmington", "Philadelphia" |
| `crime_location_zip` | TEXT | ZIP code of crime location | "19801" |
| `crime_location_court` | TEXT | Court handling the case | "D. Del.", "E.D. Pa." |
| `crime_location_pd` | TEXT | Police department involved | "Wilmington PD", "Philadelphia PD" |
| `crime_location_reasoning` | TEXT | Explanation of how location was determined | "Dataset DE_GUNSTAT implies DE. City extracted from narrative." |

## SQLite Table Schema

```sql
CREATE TABLE crime_gun_events (
    id INTEGER PRIMARY KEY AUTOINCREMENT,

    -- Source traceability
    source_dataset TEXT,
    source_sheet TEXT,
    source_row INTEGER,

    -- Existing jurisdiction (from ETL)
    jurisdiction_state TEXT,
    jurisdiction_city TEXT,

    -- Crime location (populated by classifier)
    crime_location_state TEXT,
    crime_location_city TEXT,
    crime_location_zip TEXT,
    crime_location_court TEXT,
    crime_location_pd TEXT,
    crime_location_reasoning TEXT,

    -- Case/dealer info
    dealer_name TEXT,
    case_number TEXT,
    case_summary TEXT,
    ...
);
```

## Query Records Needing Classification

```sql
SELECT id, source_dataset, source_row, case_number, case_summary, dealer_state
FROM crime_gun_events
WHERE crime_location_state IS NULL
```

## Update Function

Use `brady.etl.database.update_crime_location()`:

```python
from brady.etl.database import update_crime_location

update_crime_location(
    record_id=42,
    state="DE",
    city="Wilmington",
    zip_code=None,
    court="Delaware Superior Court",
    pd="Wilmington PD",
    reasoning="Dataset DE_GUNSTAT implies DE..."
)
```

## Confidence Levels

- **HIGH**: Explicit location fields or dataset-level defaults
- **MEDIUM**: Parsed from case numbers or trafficking flows
- **LOW**: Extracted via NLP from narrative text

## Dataset-Specific Defaults

| Dataset | Default State | Notes |
|---------|---------------|-------|
| DE_GUNSTAT | DE | All Delaware GunStat program records |
| PA_TRACE | PA | Pennsylvania trace data |
| CG_DB | (varies) | Must extract from narratives/case info |
