---
name: crime-location-classifier
description: Classify crime location data fields (state, city, zip, court, police department) for crime gun records. Use when processing Brady Gun Project CSV files that need crime_location_state, crime_location_city, crime_location_zip, crime_location_court, crime_location_pd, and crime_location_reasoning fields populated. Designed for parallel agent swarm deployment (up to 20 concurrent classifiers).
---

# Crime Location Classifier

Classify WHERE CRIMES OCCURRED for gun trace records in the Brady database.

## Database

SQLite: `data/brady.db`
Table: `crime_gun_events`

## Target Columns

| Column | Format | Example |
|--------|--------|---------|
| `crime_location_state` | 2-letter code | "DE" |
| `crime_location_city` | Proper case | "Wilmington" |
| `crime_location_zip` | 5-digit | "19801" |
| `crime_location_court` | Full name | "Superior Court of Delaware" |
| `crime_location_pd` | Full name | "Wilmington Police Department" |
| `crime_location_reasoning` | Structured | "State: [method]. City: [method]..." |

## Classification Rules

### State
1. Use `jurisdiction_state` if available (HIGH confidence)
2. Parse from case_summary narratives
3. Infer from police department names
4. Dataset defaults: DE_GUNSTAT → DE, PA_TRACE → PA

### City
1. Use `jurisdiction_city` if available
2. Extract from case_summary (street names, neighborhoods)
3. Infer from police department name
4. DE cities: Wilmington, Dover, Newark, New Castle

### ZIP Code
Look up based on city + state:
- Wilmington, DE: 19801-19810
- Dover, DE: 19901-19906
- Newark, DE: 19711-19718
- New Castle, DE: 19720

### Court
- Felonies → Superior Court of Delaware
- Misdemeanors → Court of Common Pleas
- Federal → U.S. District Court for Delaware
- Case number format may indicate court

### Police Department
- Extract from narrative (officer names, "Wilmington PD")
- Infer from city: [City] Police Department
- State highways → Delaware State Police

## Query Unclassified Records

```sql
SELECT id, source_row, jurisdiction_state, jurisdiction_city,
       dealer_name, case_number, case_summary
FROM crime_gun_events
WHERE crime_location_state IS NULL
LIMIT 50
```

## Update Records

```python
from brady.etl.database import update_crime_location

update_crime_location(
    record_id=row_id,
    state="DE",
    city="Wilmington",
    zip_code="19801",
    court="Superior Court of Delaware",
    pd="Wilmington Police Department",
    reasoning="State: From jurisdiction_state. City: Extracted from narrative."
)
```

## Handling Uncertainty

- Use "UNKNOWN" when field cannot be determined
- Document uncertainty in reasoning field
- Flag ambiguous: "REVIEW: Multiple cities mentioned"
- Be conservative: prefer UNKNOWN over guessing

## Batch Processing (for Swarm)

Process records by ID range:

```sql
SELECT id, ... FROM crime_gun_events
WHERE id >= ? AND id < ?
AND crime_location_state IS NULL
```

## References

- `references/schema.md` - SQLite schema details
- `references/extraction_strategies.md` - Detailed extraction methods

## Scripts

- `scripts/classify_location.py` - Standalone classifier with `--db` and `--id` options
