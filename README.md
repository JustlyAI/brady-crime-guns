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

# Run ETL
uv run python -m brady.etl.process_gunstat

# Run tests
uv run python -m pytest tests/ -v
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
│   │   ├── database.py     # SQLite operations
│   │   └── process_gunstat.py
│   ├── dashboard/app.py    # Streamlit dashboard
│   └── utils.py            # Shared utilities
├── data/
│   ├── raw/                # Source Excel/CSV
│   ├── processed/          # Normalized CSV
│   └── brady.db            # SQLite database
├── tests/                  # Test suite
└── pyproject.toml          # Package config
```

## Data Sources

| Source | Description | Size |
|--------|-------------|------|
| DE Gunstat | Delaware crime gun program | 635 records |
| PA Trace | Pennsylvania ATF trace data | 275MB |
| Crime Gun DB | Court documents, trafficking flows | ~500 records |
| DL2 Letters | Demand Letter 2 dealer list | ~1000 dealers |

## Key Concepts

### Jurisdiction Nexus
The core analysis tracks **WHERE CRIMES OCCURRED** (not where dealers are located) to identify supply chain actors linked to crimes in specific jurisdictions.

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
Guns recovered within 3 years of purchase (< 1095 days) are flagged as "short TTC" indicators of trafficking.

## Dashboard Views

1. **Key Metrics** - Total crime guns, dealers, manufacturers, interstate %
2. **Dealer Risk Ranking** - Color-coded risk table
3. **Manufacturer Analysis** - Pie chart and breakdown
4. **Interstate Trafficking** - Source state flow visualization
5. **Raw Data Explorer** - CSV download with traceability

## Documentation

See `docs/` for detailed specs and data dictionary.

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
3. Set environment variable: `PORT=8501`
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

### GitHub Container Registry

```bash
# Login to GHCR
echo $GITHUB_TOKEN | docker login ghcr.io -u USERNAME --password-stdin

# Build and push
docker build -t ghcr.io/OWNER/brady-dashboard:latest .
docker push ghcr.io/OWNER/brady-dashboard:latest
```

## License

MIT License - see [LICENSE](LICENSE) for details.
