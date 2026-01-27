# Brady Crime Gun Supply Chain Dashboard

## Project Goal

**For any given jurisdiction (state or city), identify all supply chain actors (manufacturers and dealers) linked to firearms involved in crimes that occurred IN that jurisdiction.**

The MVP focuses on **Delaware** using real DE Gunstat data (635 crime gun events).

---

## Quick Start

```bash
# Install dependencies
pip install -r requirements.txt

# Process real data (already done - CSV exists)
python process_real_data.py

# Run dashboard
streamlit run app.py --server.port 8501
```

---

## Current State

### ✅ Completed
1. **Data extraction** - `process_real_data.py` parses the DE Gunstat Excel file
2. **635 real records** processed and saved to `data/crime_gun_events.csv`
3. **Streamlit dashboard** - `app.py` with:
   - State filter (defaults to DE)
   - Key metrics (total events, dealers, manufacturers, interstate %)
   - Dealer risk ranking table with color-coded risk levels
   - Manufacturer pie chart and table
   - Interstate trafficking flow visualization
   - Raw data explorer with CSV download

### 🔧 Needs Work
1. **Browser access** - Streamlit runs but browser extension couldn't connect to localhost
2. **More data sources** - Only DE Gunstat loaded; Crime Gun DB, PA Trace, DL2 not yet integrated
3. **Risk scoring refinement** - Current algorithm is basic
4. **NLP for narratives** - Case summaries have location data that could be extracted

---

## File Inventory

```
brady_dashboard/
├── CLAUDE.md              # This file - project context
├── requirements.txt       # Python dependencies
├── app.py                 # Streamlit dashboard (main app)
├── process_real_data.py   # ETL for DE Gunstat Excel → CSV
├── extract_data.py        # Original sample data generator (deprecated)
└── data/
    └── crime_gun_events.csv   # 635 processed crime gun records
```

### Source Data (in /mnt/uploads/)
- `Copy of DE Gunstat_ Final.xlsx` - **635 rows** of Delaware crime gun data

### Related Docs (in /mnt/outputs/)
- `brady_project_spec.md` - Full project specification (v3)
- `brady_column_inventory.md` - Column mapping across all datasets

---

## Data Schema

### crime_gun_events.csv

| Column | Description | Example |
|--------|-------------|---------|
| `source_dataset` | Data source | DE_GUNSTAT |
| `source_sheet` | Sheet name | all identified dealers |
| `source_row` | Row # for traceability | 42 |
| `jurisdiction_state` | Where crime occurred | DE |
| `jurisdiction_city` | City of crime | Wilmington |
| `dealer_name` | FFL dealer name | Cabela's |
| `dealer_city` | Dealer location | Newark |
| `dealer_state` | Dealer state | DE |
| `dealer_ffl` | FFL license # | 8-51-01809 |
| `manufacturer_name` | Gun manufacturer (Tier 1) | GLOCK |
| `firearm_serial` | Serial number | ABC123 |
| `firearm_caliber` | Caliber | 9mm |
| `defendant_name` | Case defendant | John Smith |
| `case_number` | Case # | 30-23-12345 |
| `case_status` | Resolved/Pending | Resolved |
| `is_interstate` | Dealer state ≠ DE | True/False |
| `has_nibin` | NIBIN match exists | True/False |
| `has_trafficking_indicia` | Trafficking indicators | True/False |

---

## Key Findings from Real Data

### Top Manufacturers (Tier 1)
1. GLOCK - 150 (24%)
2. SMITH & WESSON - 101 (16%)
3. TAURUS - 84 (13%)
4. RUGER - 64 (10%)
5. SPRINGFIELD - 25 (4%)

### Top Dealers (Tier 3)
1. Cabela's (Newark, DE) - 118 guns
2. Starquest Shooters - 82 guns
3. Miller's Gun Center - 68 guns
4. First State Firearms - 40 guns

### Interstate Trafficking
- **34.5%** of crime guns came from out-of-state dealers
- Top source states: PA (74), GA (29), VA (21), SC (15)

---

## Next Steps

### Immediate (MVP Polish)
1. [ ] Fix localhost browser access OR generate static HTML report
2. [ ] Add time-to-crime analysis (TTR column exists)
3. [ ] Improve case status normalization (many variants)

### Short-term
1. [ ] Integrate Crime Gun Dealer Database (Google Sheet)
2. [ ] Integrate PA Trace data (275MB CSV)
3. [ ] Join DL2 dealer data for risk enrichment
4. [ ] Add city-level filtering

### Medium-term
1. [ ] NLP extraction from `case_summary` narratives
2. [ ] Case number parsing for court jurisdiction
3. [ ] Manufacturer standardization lookup table
4. [ ] Export to SQLite for more complex queries

---

## Architecture

```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│  Source Data    │────▶│   ETL Scripts   │────▶│   Dashboard     │
│                 │     │                 │     │                 │
│ • DE Gunstat    │     │ process_real_   │     │ • Streamlit     │
│ • Crime Gun DB  │     │   data.py       │     │ • Plotly charts │
│ • PA Trace      │     │                 │     │ • Data tables   │
│ • DL2 Letters   │     │                 │     │                 │
└─────────────────┘     └─────────────────┘     └─────────────────┘
                                │
                                ▼
                        ┌─────────────────┐
                        │ crime_gun_      │
                        │ events.csv      │
                        │ (normalized)    │
                        └─────────────────┘
```

---

## Key Concept: Jurisdiction Nexus

**Jurisdiction = WHERE THE CRIME OCCURRED**, not where the dealer is located.

For DE Gunstat, all 635 events are Delaware crimes (implicit). For other datasets:
- PA Trace: Has explicit Recovery City/State
- Crime Gun DB: Parse from case references, recovery location columns

---

## Risk Scoring Algorithm

```python
def calculate_dealer_risk_score(dealer_stats):
    score = dealer_stats['crime_count'] * 10

    # Interstate multiplier
    if dealer_stats['interstate_pct'] > 0.5:
        score *= 2.0
    elif dealer_stats['interstate_pct'] > 0.25:
        score *= 1.5

    # Risk flags
    if dealer_stats.get('in_dl2'): score += 25
    if dealer_stats.get('is_revoked'): score += 50
    if dealer_stats.get('is_charged'): score += 35

    return score
```

Risk Levels:
- **HIGH**: score >= 100
- **MEDIUM**: score >= 50
- **LOW**: score < 50

---

## Commands Reference

```bash
# Run dashboard locally
streamlit run app.py

# Reprocess data from Excel
python process_real_data.py

# Check data
head -5 data/crime_gun_events.csv | column -t -s,
```

---

## Contact / Context

This project is for **Brady Gun Center** to analyze crime gun supply chains.
The goal is a dashboard that answers: *"For crimes in Delaware, who are the manufacturers and dealers involved?"*

Primary data source: DE Gunstat program (Delaware DOJ)
