# Brady Gun Project

Crime gun supply chain analysis dashboard for identifying dealers and manufacturers linked to crimes by jurisdiction.

## Setup

This project uses **uv** for Python package management.

```bash
# Install dependencies
uv sync

# Install in development mode
uv pip install -e .
```

## Project Structure

```
src/brady/           # Main Python package
├── etl/             # ETL pipeline (unified.py, process_gunstat.py)
└── dashboard/       # Streamlit app (app.py)

data/
├── raw/             # Source Excel/CSV files
└── processed/       # Normalized CSV output

docs/                # Documentation (project_spec.md, column_inventory.md)
tests/               # Test suite
```

## Quick Commands

```bash
# Run dashboard
uv run streamlit run src/brady/dashboard/app.py

# Run ETL
uv run python -m brady.etl.process_gunstat

# Run tests
uv run pytest
```

## Key Concept

**Jurisdiction Nexus**: Track WHERE CRIMES OCCURRED to identify supply chain actors. The dashboard shows dealers and manufacturers linked to crimes in a selected state.

## MVP Focus

Currently focused on Delaware (DE) with 635 crime gun events from DE Gunstat data.
