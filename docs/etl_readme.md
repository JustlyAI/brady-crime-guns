# Brady Unified Gun Crime Database - ETL Pipeline

Python ETL scripts to create a unified database from multiple gun crime data sources for Brady Gun Center's jurisdiction nexus analysis.

## Purpose

This pipeline consolidates data from:
1. **Crime Gun Dealer Database** - FFL data with court documents, trafficking flows
2. **Demand Letters Database** - DL2 program participation tracking
3. **PA Gun Tracing Data (CSV)** - ATF trace data (274.9 MB)
4. **PA Gun Tracing Data (XLSX)** - ATF trace data (65.9 MB)

The unified database enables **jurisdiction nexus analysis** to identify:
- Where guns were sold (FFL/dealer location)
- Where crimes occurred (recovery location)
- Interstate trafficking patterns
- Short time-to-crime indicators (<3 years)
- High-risk dealers for potential nuisance actions

## Quick Start

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Download Source Files

**Option A: Manual Download (Recommended)**

Download from Google Drive folder: https://drive.google.com/drive/folders/1ZN7XEq2ols6XEKFsQH6e7rAkKaMv5LNT

Files to download:
- `PA-gunTracingData.csv` (274.9 MB)
- `PA-gunTracingData.xlsx` (65.9 MB)

Download Google Sheets as Excel:
- Crime Gun Dealer DB: https://docs.google.com/spreadsheets/d/1SOUl4Xrv6FLUY_t5bNAzO6xB8pftIYcfY3NUBwutC58
- Demand Letters: https://docs.google.com/spreadsheets/d/1l7iUG1t4sti3LM2HRVc2Yb3CZVBsh-GS0MiG5gITZLk

**Option B: Automated Download**

```bash
python google_drive_downloader.py --credentials path/to/credentials.json
```

### 3. Run ETL Pipeline

```bash
python brady_unified_etl.py \
    --crime-gun crime_gun_dealer_database.xlsx \
    --demand-letters demand_letters_database.xlsx \
    --pa-trace-csv PA-gunTracingData.csv \
    --pa-trace-xlsx PA-gunTracingData.xlsx \
    --output-dir ./output
```

### 4. Output Files

The pipeline creates:
- `brady_unified_database.xlsx` - Excel workbook with:
  - `Unified_Data` - All records in unified schema
  - `Jurisdiction_Summary` - Nexus analysis by state
  - `Dealer_Risk_Summary` - High-risk dealer rankings
- `brady_unified_database.csv` - CSV version for large-scale analysis

## Unified Schema

The unified schema contains 55+ fields organized into categories:

### Jurisdiction-Critical Fields (highlighted)
| Field | Description |
|-------|-------------|
| `ffl_premise_state` | State where gun was sold |
| `ffl_premise_city` | City where gun was sold |
| `recovery_state` | State where crime occurred |
| `recovery_city` | City where crime occurred |
| `source_state` | Same as ffl_premise_state |
| `destination_state` | Same as recovery_state |
| `trafficking_flow` | Format: "XX-->YY" (e.g., "PA-->NY") |
| `is_interstate` | True if source ≠ destination |

### Time-to-Crime Fields
| Field | Description |
|-------|-------------|
| `time_to_crime_days` | Days between purchase and recovery |
| `time_to_crime_category` | Very Short (<1yr), Short (<3yr), Medium (3-5yr), Long (>5yr) |
| `short_ttc_indicator` | True if < 1095 days (3 years) |

### Brady DL2 Program Fields
| Field | Description |
|-------|-------------|
| `in_dl2_program_2021` | In DL2 program 2021 |
| `in_dl2_program_2022` | In DL2 program 2022 |
| `in_dl2_program_2023` | In DL2 program 2023 |
| `in_dl2_program_2024` | In DL2 program 2024 |
| `dl2_letter_type_current` | Current letter type |

## Analysis Outputs

### Jurisdiction Summary
Ranks states by "nexus score" for potential nuisance actions:
- Total crime guns recovered in state
- Interstate trafficking count
- Short TTC count
- Top source states

**Nexus Score Formula:**
```
nexus_score = total_crimes + (interstate * 2) + (short_ttc * 3)
```

### Dealer Risk Summary
Ranks dealers by risk score for prioritization:
- Total crime guns traced to dealer
- Interstate trafficking involvement
- Short TTC patterns
- DL2 program status
- Revoked/charged status

**Risk Score Formula:**
```
risk_score = crime_guns + (interstate * 2) + (short_ttc * 3) + (dl2_2024 * 10) + (revoked * 20) + (charged * 15)
```

## Python API Usage

```python
from brady_unified_etl import run_full_etl, create_jurisdiction_summary

# Run full ETL
unified_df = run_full_etl(
    crime_gun_path='crime_gun_dealer_database.xlsx',
    demand_letters_path='demand_letters_database.xlsx',
    pa_trace_csv_path='PA-gunTracingData.csv',
    pa_trace_xlsx_path='PA-gunTracingData.xlsx',
)

# Analyze specific state
ny_crimes = unified_df[unified_df['recovery_state'] == 'NY']
print(f"Crimes in NY: {len(ny_crimes)}")
print(f"Interstate: {ny_crimes['is_interstate'].sum()}")
print(f"Short TTC: {ny_crimes['short_ttc_indicator'].sum()}")

# Top source states for NY crimes
print(ny_crimes['source_state'].value_counts().head(10))
```

## File Structure

```
brady_etl_python/
├── brady_unified_etl.py      # Main ETL pipeline
├── google_drive_downloader.py # Download helper
├── requirements.txt           # Python dependencies
└── README.md                  # This file
```

## Data Source IDs

| Source | Google ID |
|--------|-----------|
| Crime Gun Dealer DB | `1SOUl4Xrv6FLUY_t5bNAzO6xB8pftIYcfY3NUBwutC58` |
| Demand Letters | `1l7iUG1t4sti3LM2HRVc2Yb3CZVBsh-GS0MiG5gITZLk` |
| PA Trace XLSX | `1RS-BUBBgkGhsa9iBw0F7JZQ0Xv15mKT7` |
| GunData Folder | `1ZN7XEq2ols6XEKFsQH6e7rAkKaMv5LNT` |

## Performance Notes

- PA Trace files are large (65-275 MB)
- Use `--max-rows` flag for testing with subset
- Full ETL takes ~5-10 minutes depending on hardware
- Output Excel file will be 50-100 MB

## License

For Brady Gun Center internal use.
