# v_2 Implementation Guide

## Quick Start for Claude Code

This folder contains everything needed to implement the Crime Gun Dealer DB integration. Start here.

### Files in this folder

| File | Purpose |
|------|---------|
| `PRD_Crime_Gun_DB_Integration.md` | Full requirements document |
| `crime_gun_db_extractor.py` | Module stub with TODO markers - **implement this** |
| `schema_additions.py` | New unified schema fields to merge |
| `test_fixtures.py` | Test cases for unit tests |
| `requirements_additions.txt` | Dependencies to add |
| `IMPLEMENTATION_GUIDE.md` | This file |

### Data file location

```
data/raw/Crime_Gun_Dealer_DB.xlsx
```

---

## Implementation Order

### Step 1: Review the data

```python
import pandas as pd

xlsx = pd.ExcelFile("data/raw/Crime_Gun_Dealer_DB.xlsx")
print(xlsx.sheet_names)
# ['CG court doc FFLs', 'Philadelphia Trace', 'Rochester Trace', 'Sheet7', 'Backdated']

df = pd.read_excel(xlsx, sheet_name="CG court doc FFLs")
print(df.columns.tolist())
print(df.head())
```

### Step 2: Implement extraction functions

In `crime_gun_db_extractor.py`, implement in this order:

1. `load_crime_gun_db()` - Basic sheet loading
2. `parse_recovery_locations()` - Priority 1 jurisdiction
3. `parse_case_court()` - Priority 2 jurisdiction
4. `parse_trafficking_flow()` - Priority 3 jurisdiction
5. `convert_boolean_field()` - Already partially done
6. `clean_ffl_name()` - String normalization
7. `parse_time_to_crime()` - TTC parsing
8. `determine_jurisdiction()` - Priority chain
9. `transform_to_unified()` - Schema mapping
10. `load_and_transform_crime_gun_db()` - Main entry point

### Step 3: Write tests

Create `tests/test_crime_gun_db_extractor.py` using fixtures from `test_fixtures.py`.

```bash
pytest tests/test_crime_gun_db_extractor.py -v
```

### Step 4: Integrate with main ETL

In `brady_unified_etl.py`:

```python
from v_2.crime_gun_db_extractor import load_and_transform_crime_gun_db

# In main ETL function:
crime_gun_df = load_and_transform_crime_gun_db("data/raw/Crime_Gun_Dealer_DB.xlsx")
unified_df = pd.concat([existing_df, crime_gun_df], ignore_index=True)
```

### Step 5: Update schema

Merge fields from `schema_additions.py` into the unified schema definition.

---

## Key Patterns to Handle

### Recovery Locations (Column R)

```
"1. Woodland, CA\n2. Citrus Heights, CA (Sacramento burb)"
```

Regex hint:
```python
pattern = r"(\d+\.\s*)?([^,]+),\s*([A-Z]{2})"
```

### Case Court References (Column N)

```
"U.S. v. Pangilinan et. al., D. Alaska, No. 20-cr-92"
"U.S. v. Smith (E.D. Pa.)"
```

Use the `COURT_PATTERNS` dict in the extractor module.

### Trafficking Flow (Column P)

```
"AK-->CA"
"state(s) --> destination(s)"
"DV*"
"SWB"
```

Regex hint:
```python
arrow_pattern = r"([A-Z]{2})\s*-+>\s*([A-Z]{2}|SWB)"
```

---

## Validation Checklist

Before marking complete:

- [ ] All 1,981 CG court doc FFLs records load without error
- [ ] 54 Philadelphia Trace records have implicit jurisdiction = PA
- [ ] Sheet7 is skipped
- [ ] Backdated sheet handled (skip if empty)
- [ ] Recovery locations parsed for 80%+ of Column R data
- [ ] Court references parsed for standard federal district patterns
- [ ] Trafficking flows extracted from arrow notation
- [ ] Boolean fields converted correctly
- [ ] Time-to-crime parsed to integer days
- [ ] Source traceability fields populated (source_dataset, source_sheet, source_row)
- [ ] Jurisdiction method and confidence tracked
- [ ] All unit tests pass
- [ ] Integration with main ETL works

---

## Common Pitfalls

1. **Row 2 garbage data** - First data row may contain "?" placeholders. Filter it.

2. **Column offset in trace sheets** - Philadelphia and Rochester sheets are missing one column vs main sheet. Verify headers.

3. **Multi-location records** - Decide: create multiple rows or store as JSON array? PRD suggests array with optional expansion.

4. **Empty Backdated sheet** - Don't error on empty sheet, just return empty DataFrame.

5. **Date parsing errors** - Some cells have invalid Excel date serials. Catch and log.

6. **State code validation** - Validate against `VALID_STATES` set. Log invalid codes.
