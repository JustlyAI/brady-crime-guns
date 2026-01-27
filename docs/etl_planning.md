# Brady Gun Crime Database - Planning Document

## Data Sources Inventory

We have **5 data sources** in the Google Drive folder:

| # | File | Type | Granularity | Key Data |
|---|------|------|-------------|----------|
| 1 | **Crime Gun Dealer Database** | Google Sheet | Dealer + Case | FFLs from court docs, Philadelphia/Rochester traces |
| 2 | **DE Gunstat: Final** | Google Sheet | Case/Trace | Delaware GunStat program cases with NIBIN data |
| 3 | **Demand Letters (DL2)** | Google Sheet | Dealer | DL2 program participation 2021-2024 |
| 4 | **PA-gunTracingData.csv** | CSV (275 MB) | Individual Trace | ATF trace data - PA recoveries |
| 5 | **PA-gunTracingData.xlsx** | Excel (66 MB) | Individual Trace | Same as #4, Excel format |

---

## Data Source Details

### 1. Crime Gun Dealer Database
**Sheets:**
- CG court doc FFLs
- Philadelphia Trace
- Rochester Trace

**Key Fields:**
- FFL name, Address, City, State, License #
- Top Trace status, Revoked, Charged/Sued
- Case name, Case subject (trafficking flow like "Alaska --> California")
- Recovery locations, Time-to-crime

**Granularity:** One row per dealer (with case info embedded)

---

### 2. DE Gunstat: Final (NEW - needs full analysis)
**Sheets:**
- all identified dealers
- Copy of all identified dealers- organized by def
- Need trace info
- Trace Unsuccessful
- cabelas - a... (and possibly more)

**Key Fields:**
- Dealer name + City + State + FFL #
- Case (Defendant name, Case #)
- GunStat Report (links)
- Firearm, purchase, NIBIN information
- Pending or resolved status
- Purchaser name

**Granularity:** One row per **case/trace** (not per dealer)

---

### 3. Demand Letters (DL2)
**Sheets:**
- Demand letter 2 FFLs
- Full Data
- FAQs
- Per State Analysis

**Key Fields:**
- License Name, Trade Name
- Address, City, State, ZIP
- In DL2 Program: 2021, 2022, 2023, 2024 (Yes/No)
- Type of Letter (Continuing, Removal, New Participant)
- DL2 dates

**Granularity:** One row per **dealer**

---

### 4 & 5. PA Gun Tracing Data (CSV & XLSX)
**Key Fields (typical ATF trace format):**
- Dealer/FFL info (name, city, state, license #)
- Firearm details (serial, make, model, caliber, type)
- Purchase date, Purchaser info
- Recovery date, Recovery location (city, state)
- Time-to-crime (days)

**Granularity:** One row per **individual firearm trace**

---

## Proposed Database Schema

### Option A: Star Schema (Recommended)

```
                         ┌──────────────────┐
                         │   dim_dealers    │
                         │  (Master FFL)    │
                         └────────┬─────────┘
                                  │
          ┌───────────────────────┼───────────────────────┐
          │                       │                       │
          ▼                       ▼                       ▼
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│  fact_dl2_      │    │   fact_cases     │    │  fact_traces    │
│  participation  │    │ (court cases)    │    │ (ATF traces)    │
│                 │    │                  │    │                 │
│ - dealer_id     │    │ - dealer_id      │    │ - dealer_id     │
│ - year          │    │ - case_name      │    │ - trace_id      │
│ - in_program    │    │ - case_number    │    │ - firearm_*     │
│ - letter_type   │    │ - defendant      │    │ - purchase_date │
│                 │    │ - status         │    │ - recovery_*    │
│                 │    │ - source (DE/PA) │    │ - ttc_days      │
└─────────────────┘    └──────────────────┘    └─────────────────┘
```

### Table Definitions

#### dim_dealers (Dimension)
| Column | Type | Description |
|--------|------|-------------|
| dealer_id | VARCHAR(12) | Hash of normalized name + state |
| license_name | VARCHAR(255) | Official FFL license name |
| trade_name | VARCHAR(255) | DBA / trade name |
| ffl_number | VARCHAR(20) | FFL license number |
| address | VARCHAR(255) | Premise address |
| city | VARCHAR(100) | City |
| state | CHAR(2) | State (normalized to 2-letter) |
| zip | VARCHAR(10) | ZIP code |
| is_revoked | BOOLEAN | License revoked |
| is_charged | BOOLEAN | Has been charged/sued |
| is_top_trace | BOOLEAN | ATF top trace dealer |
| sources | VARCHAR(255) | Which datasets this dealer appears in |

#### fact_dl2_participation
| Column | Type | Description |
|--------|------|-------------|
| dealer_id | VARCHAR(12) | FK to dim_dealers |
| year | INT | Program year (2021-2024) |
| in_program | BOOLEAN | Was in DL2 program that year |
| letter_type | VARCHAR(50) | Continuing/Removal/New Participant |
| letter_date | DATE | Date of letter |

#### fact_cases
| Column | Type | Description |
|--------|------|-------------|
| case_id | VARCHAR(20) | Unique case identifier |
| dealer_id | VARCHAR(12) | FK to dim_dealers |
| source_dataset | VARCHAR(50) | DE_Gunstat, Crime_Gun_DB, etc. |
| case_number | VARCHAR(50) | Court case number |
| defendant_name | VARCHAR(255) | Defendant |
| case_status | VARCHAR(20) | Pending/Resolved |
| gunstat_report_link | VARCHAR(500) | Link to GunStat report |
| trafficking_flow | VARCHAR(20) | e.g., "AK-->CA" |
| notes | TEXT | Additional case info |

#### fact_traces
| Column | Type | Description |
|--------|------|-------------|
| trace_id | VARCHAR(20) | Unique trace identifier |
| dealer_id | VARCHAR(12) | FK to dim_dealers |
| source_dataset | VARCHAR(50) | PA_Trace_CSV, PA_Trace_XLSX |
| firearm_serial | VARCHAR(50) | Serial number |
| firearm_make | VARCHAR(100) | Manufacturer |
| firearm_model | VARCHAR(100) | Model |
| firearm_caliber | VARCHAR(20) | Caliber |
| firearm_type | VARCHAR(50) | Pistol/Rifle/etc. |
| purchase_date | DATE | Date of purchase |
| purchaser_name | VARCHAR(255) | Purchaser (if available) |
| recovery_date | DATE | Date recovered |
| recovery_city | VARCHAR(100) | City where recovered |
| recovery_state | CHAR(2) | State where recovered |
| time_to_crime_days | INT | Days from purchase to recovery |
| is_short_ttc | BOOLEAN | TTC < 1095 days (3 years) |
| is_interstate | BOOLEAN | Dealer state ≠ recovery state |
| trafficking_flow | VARCHAR(20) | e.g., "PA-->NY" |
| nibin_info | VARCHAR(255) | NIBIN hit information |

---

## Analysis Views to Create

### view_dealer_summary
Pre-joined view for quick analysis:
```sql
SELECT
    d.*,
    COUNT(DISTINCT t.trace_id) as total_traces,
    SUM(t.is_short_ttc) as short_ttc_count,
    SUM(t.is_interstate) as interstate_count,
    AVG(t.time_to_crime_days) as avg_ttc,
    MAX(dl.in_program) as in_dl2_program,
    COUNT(DISTINCT c.case_id) as court_cases
FROM dim_dealers d
LEFT JOIN fact_traces t ON d.dealer_id = t.dealer_id
LEFT JOIN fact_dl2_participation dl ON d.dealer_id = dl.dealer_id AND dl.year = 2024
LEFT JOIN fact_cases c ON d.dealer_id = c.dealer_id
GROUP BY d.dealer_id
```

### view_jurisdiction_nexus
For identifying nuisance action opportunities:
```sql
SELECT
    recovery_state as harm_state,
    d.state as sale_state,
    COUNT(*) as trace_count,
    SUM(is_short_ttc) as short_ttc_count,
    trafficking_flow
FROM fact_traces t
JOIN dim_dealers d ON t.dealer_id = d.dealer_id
WHERE t.is_interstate = TRUE
GROUP BY recovery_state, d.state, trafficking_flow
ORDER BY trace_count DESC
```

---

## Key Questions This Schema Answers

1. **Which dealers in the DL2 program have the most crime gun traces?**
2. **What are the top interstate trafficking corridors?**
3. **Which states have the most crime guns with short time-to-crime?**
4. **Which dealers have both DL2 participation AND court cases?**
5. **What's the average TTC for dealers who've been charged vs. not charged?**

---

## Next Steps

1. ☐ Finish analyzing DE Gunstat sheets (need to see all sheets)
2. ☐ Confirm schema with user
3. ☐ Update Python ETL to create these 4 tables
4. ☐ Create output as either:
   - SQLite database file
   - Excel workbook with multiple sheets
   - CSV files (one per table)
5. ☐ Build analysis views

---

## Open Questions

1. **PA Trace CSV vs XLSX** - Are these the same data? Should we use one or merge both?
2. **DE Gunstat** - Is this Delaware-specific or national? How does it relate to PA trace data?
3. **Dealer matching** - How to match dealers across datasets? FFL# preferred but not always available.
4. **Output format preference** - SQLite? Excel? CSV?
