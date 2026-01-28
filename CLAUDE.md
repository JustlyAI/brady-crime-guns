# Brady Gun Center - Claude Instructions

## Project Overview

Crime gun supply chain analysis for the Brady Center. Tracks firearms linked to crimes by jurisdiction to identify high-risk dealers and trafficking patterns.

**Live Dashboard:** https://brady-dashboard-production.up.railway.app/

## Quick Commands

```bash
# Run ETL pipelines
uv run python -m brady.etl.process_gunstat        # DE Gunstat (635 records)
uv run python -m brady.etl.process_crime_gun_db   # Crime Gun DB (2,030 records)

# Run tests
uv run pytest tests/ -v

# Run dashboard
uv run streamlit run src/brady/dashboard/app.py
```

## Architecture

```
src/brady/
├── etl/
│   ├── database.py            # SQLite schema, migrations, queries
│   ├── process_gunstat.py     # DE Gunstat Excel → SQLite
│   ├── process_crime_gun_db.py # Crime Gun DB Excel → SQLite
│   ├── date_utils.py          # Date parsing utilities
│   └── court_lookup.py        # Court name resolution
├── dashboard/app.py           # Streamlit dashboard
└── utils.py                   # get_project_root()
```

## Database

Supports PostgreSQL (production) and SQLite (local dev). Single table `crime_gun_events`.

- **Production:** PostgreSQL on Railway (set `DATABASE_URL` env var)
- **Local:** SQLite at `data/brady.db`

Key columns:
- `source_dataset`: 'DE_GUNSTAT', 'PA_TRACE', or 'CG_COURT_DOC'
- `jurisdiction_state/city/method`: Where crime occurred
- `dealer_name/city/state/ffl`: FFL info
- `trafficking_origin/destination`: Interstate flow
- `time_to_crime`: Days (integer)

## ETL Patterns

Both ETL modules follow the same pattern:
1. Load Excel with `pd.read_excel()`
2. Transform rows with parsing functions
3. Delete existing records by `source_dataset`
4. Insert new records with `df.to_sql()`

Crime Gun DB uses priority-based jurisdiction resolution:
1. Recovery location (Column R)
2. Court reference (Column N)
3. Trafficking destination (Column P)
4. Sheet default (Philadelphia=PA)
5. Dealer state

## Testing

Tests in `tests/` directory. Run with `uv run pytest tests/ -v`.

Key test files:
- `test_process_crime_gun_db.py` - 51 tests for parsing functions
- `test_process_gunstat.py` - DE Gunstat parsing tests
- `test_date_utils.py` - Date parsing tests

## Data Files

- `data/raw/DE_Gunstat_Final.xlsx` - Delaware crime gun data
- `data/raw/Crime_Gun_Dealer_DB.xlsx` - Court case records (skip Sheet7)
- `data/brady.db` - SQLite database (generated)

## Deployment

Railway deployment with auto-deploy from `main` branch.

```bash
# Check deployment status
railway status

# View logs
railway logs

# Populate Railway database (run locally)
DATABASE_URL="<railway-postgres-url>" uv run python -m brady.etl.process_gunstat
DATABASE_URL="<railway-postgres-url>" uv run python -m brady.etl.process_crime_gun_db
```

Config files: `railway.toml`, `.railwayignore`, `Dockerfile`

## Code Style

- Use `termcolor.cprint()` for console output
- Use `encoding="utf-8"` for file operations
- Use context managers for database connections
- Keep parsing functions pure (no side effects)
