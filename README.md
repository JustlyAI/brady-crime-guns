# Brady Gun Center - Crime Gun Supply Chain Analysis

A data analysis toolkit for tracking firearm supply chains linked to crimes by jurisdiction.

## Overview

This project helps identify patterns in crime gun supply chains:
- **Where guns are sold** (FFL/dealer location)
- **Where crimes occur** (recovery location)
- **Interstate trafficking patterns**
- **High-risk dealers** based on multiple indicators

## Quick Start

### Installation

```bash
# Create virtual environment
python -m venv .venv
source .venv/bin/activate  # Linux/Mac
# .venv\Scripts\activate   # Windows

# Install dependencies
pip install -r requirements.txt

# Or install as package (editable mode)
pip install -e .
```

### Run Dashboard

```bash
streamlit run src/brady/dashboard/app.py
```

### Run ETL Pipeline

```bash
# Process DE Gunstat data
python -m brady.etl.process_gunstat

# Or with custom paths
python -m brady.etl.process_gunstat --input data/raw/DE_Gunstat_Final.xlsx
```

## Project Structure

```
BradyProject/
├── src/brady/              # Main package
│   ├── etl/                # ETL pipeline modules
│   │   ├── unified.py      # Multi-source ETL
│   │   ├── process_gunstat.py  # DE Gunstat processor
│   │   └── google_drive.py # Google Drive integration
│   └── dashboard/          # Streamlit dashboard
│       └── app.py
├── data/
│   ├── raw/                # Source files (Excel, CSV)
│   └── processed/          # Normalized output
├── docs/                   # Documentation
├── tests/                  # Test suite
├── pyproject.toml          # Package configuration
├── requirements.txt        # Dependencies
└── CLAUDE.md               # AI assistant context
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

See `docs/` for detailed documentation:
- `project_spec.md` - Full project specification
- `column_inventory.md` - Data dictionary
- `etl_planning.md` - ETL pipeline design
- `etl_readme.md` - ETL usage guide
- `dashboard_readme.md` - Dashboard details

## Development

```bash
# Install dev dependencies
pip install -e ".[dev]"

# Run tests
pytest

# Run linter
ruff check src/

# Type checking
mypy src/
```

## License

For Brady Gun Center internal use.
