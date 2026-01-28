# Brady Gun Center - Crime Gun Supply Chain Analysis

A data analysis toolkit for tracking firearm supply chains linked to crimes by jurisdiction.

## Overview

This project helps identify patterns in crime gun supply chains:
- **Where guns are sold** (FFL/dealer location)
- **Where crimes occur** (recovery location)
- **Interstate trafficking patterns**
- **High-risk dealers** based on multiple indicators

## Quick Start

```bash
# Install dependencies
uv sync

# Run dashboard
uv run streamlit run src/brady/dashboard/app.py

# Run ETL (all datasets)
uv run python -m brady.etl.process_gunstat        # DE Gunstat (635 records)
uv run python -m brady.etl.process_crime_gun_db   # Crime Gun DB (2,030 records)

# Run tests
uv run pytest tests/ -v
```

### Run with Docker

```bash
# Build and run
docker compose up --build

# Run in background
docker compose up -d

# View logs
docker compose logs -f dashboard
```

Access the dashboard at http://localhost:8501

## Project Structure

```
BradyProject/
├── src/brady/              # Main package
│   ├── etl/                # ETL pipeline
│   │   ├── database.py     # Database operations (SQLite + PostgreSQL)
│   │   ├── process_gunstat.py
│   │   └── process_crime_gun_db.py
│   ├── dashboard/app.py    # Streamlit dashboard
│   └── utils.py            # Shared utilities
├── data/
│   ├── raw/                # Source Excel/CSV files
│   └── brady.db            # SQLite database
├── docs/                   # Documentation
│   └── schema-guide.md     # Database schema reference
├── tests/                  # Test suite
└── pyproject.toml          # Package config
```

## Data Sources

The system processes data from multiple sources into three distinct datasets:

| Dataset | Source File | Records | Description |
|---------|-------------|---------|-------------|
| `DE_GUNSTAT` | DE_Gunstat_Final.xlsx | 635 | Delaware crime gun program data |
| `PA_TRACE` | Crime_Gun_Dealer_DB.xlsx (Philadelphia Trace) | 50 | Pennsylvania ATF trace data |
| `CG_COURT_DOC` | Crime_Gun_Dealer_DB.xlsx (CG court doc FFLs) | 1,980 | Multi-state federal court case records |

### Dataset-Specific State Inference

Each dataset has different rules for determining crime location state:

| Dataset | State Inference Rule |
|---------|---------------------|
| `DE_GUNSTAT` | Assume "DE" (Delaware-specific program) |
| `PA_TRACE` | Assume "PA" (Pennsylvania trace data) |
| `CG_COURT_DOC` | Use `jurisdiction_state` from court/recovery parsing |

## Database

The system supports both SQLite (local development) and PostgreSQL (production).

- **SQLite**: `data/brady.db` (default)
- **PostgreSQL**: Set `DATABASE_URL` environment variable

See [docs/schema-guide.md](docs/schema-guide.md) for the complete schema reference.

### Key Tables

Single unified table: `crime_gun_events`

Key column groups:
- **Source traceability**: `source_dataset`, `source_sheet`, `source_row`
- **Jurisdiction**: `jurisdiction_state`, `jurisdiction_city`, `jurisdiction_method`
- **Crime location**: `crime_location_state`, `crime_location_city`, `crime_location_zip`
- **Dealer info**: `dealer_name`, `dealer_city`, `dealer_state`, `dealer_ffl`
- **Risk indicators**: `in_dl2_program`, `is_top_trace_ffl`, `is_revoked`, `is_charged_or_sued`
- **Trafficking**: `trafficking_origin`, `trafficking_destination`, `is_southwest_border`

## Key Concepts

### Jurisdiction Nexus

The core analysis tracks **WHERE CRIMES OCCURRED** (not where dealers are located) to identify supply chain actors linked to crimes in specific jurisdictions.

Jurisdiction is resolved using a priority chain:
1. Recovery location (direct observation)
2. Court reference (federal court abbreviation)
3. Trafficking destination (flow pattern)
4. Sheet default (Philadelphia=PA)
5. Dealer state (fallback)

### Risk Scoring

Dealers are ranked by a composite risk score:
```
score = crime_guns * 10
      + interstate * 2
      + short_ttc * 3
      + dl2_program * 10
      + revoked * 20
      + charged * 15
```

### Time-to-Crime (TTC)

Guns recovered within 3 years of purchase (< 1095 days) are flagged as "short TTC" indicators of potential trafficking.

## Dashboard Views

1. **Key Metrics** - Total crime guns, dealers, manufacturers, interstate %
2. **Dealer Risk Ranking** - Color-coded risk table
3. **Manufacturer Analysis** - Pie chart and breakdown
4. **Interstate Trafficking** - Source state flow visualization
5. **Raw Data Explorer** - CSV download with traceability

## ETL Pipeline

Both ETL modules follow the same pattern:

1. Load Excel with `pd.read_excel()`
2. Transform rows with parsing functions
3. Delete existing records by `source_dataset`
4. Insert new records with `df.to_sql()`

### Running ETL

```bash
# Process Delaware Gunstat data
uv run python -m brady.etl.process_gunstat

# Process Crime Gun Dealer DB (outputs PA_TRACE and CG_COURT_DOC)
uv run python -m brady.etl.process_crime_gun_db
```

## Testing

```bash
# Run all tests
uv run pytest tests/ -v

# Run specific test file
uv run pytest tests/test_process_crime_gun_db.py -v
```

## Deployment

### Docker Build

```bash
# Build for local platform
docker build -t brady-dashboard .

# Build multi-platform (for deployment)
docker buildx build --platform linux/amd64,linux/arm64 -t brady-dashboard .
```

### Railway

1. Connect your GitHub repository to Railway
2. Railway will auto-detect the Dockerfile
3. Set environment variables:
   - `PORT=8501`
   - `DATABASE_URL` (Railway PostgreSQL addon)
4. Deploy

### Google Cloud Run

```bash
# Build and push to GCR
gcloud builds submit --tag gcr.io/PROJECT_ID/brady-dashboard

# Deploy
gcloud run deploy brady-dashboard \
  --image gcr.io/PROJECT_ID/brady-dashboard \
  --platform managed \
  --allow-unauthenticated \
  --port 8501
```

## Documentation

- [Schema Guide](docs/schema-guide.md) - Database schema reference
- [ETL Planning](docs/etl_planning.md) - ETL architecture decisions
- [Dashboard README](docs/dashboard_readme.md) - Dashboard features

## License

MIT License - see [LICENSE](LICENSE) for details.
