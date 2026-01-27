# Brady Gun Center - Crime Gun Tracing Database
## Project Specification v3

---

## 1. Project Goal

**For any given jurisdiction (state or city), identify all supply chain actors (Tier 1/2/3) linked to firearms involved in crimes or events that occurred IN that jurisdiction.**

The jurisdiction nexus is established by **where the crime/event occurred**, NOT by where the supply chain actors are located.

### Deliverable Objective
Create a **normalized master dataset** from the source spreadsheets that:
1. Maintains **traceability** back to original source records
2. Enables **dashboard/visualization** for jurisdiction-based analysis
3. Answers the question: *"For crimes in [State/City], who are the supply chain actors?"*

---

## 2. The Firearm Supply Chain

```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│     TIER 1      │────▶│     TIER 2      │────▶│     TIER 3      │
│  Manufacturer   │     │   Distributor   │     │     Dealer      │
│   / Importer    │     │   / Wholesaler  │     │   / Retailer    │
│                 │     │                 │     │     (FFL)       │
│ Location: X     │     │ Location: Y     │     │ Location: Z     │
└─────────────────┘     └─────────────────┘     └─────────────────┘
                                                        │
                                                        ▼
                                                ┌─────────────────┐
                                                │  CRIME/EVENT    │
                                                │                 │
                                                │ Location: TARGET│
                                                │ JURISDICTION    │
                                                └─────────────────┘
```

### The Key Insight:

**Jurisdiction nexus = WHERE THE CRIME OCCURRED**

We want to ask: *"For crimes that occurred in Delaware, who were all the Tier 1/2/3 actors in the supply chain?"*

The supply chain actors could be located ANYWHERE. What matters is that the gun ended up being used in a crime in our target jurisdiction.

---

## 3. Source Data Inventory

### 3.1 Crime Gun Dealer Database (Google Sheet)
**Sheets:** CG court doc FFLs, Philadelphia Trace, Rochester Trace, Sheet7, Backdated

| Key Column | What It Contains | Relevance |
|------------|------------------|-----------|
| **R: Location(s) of recovery(ies)** | Explicit recovery location | **JURISDICTION CRITICAL** |
| **S: Info on recoveries** | Narrative with crime context | **JURISDICTION** (NLP) |
| **U: Facts** | Detailed narrative with locations | **JURISDICTION** (NLP) |
| **P: Case subject** | Trafficking flow "state(s) --> destination(s)" | **JURISDICTION** |
| **N: Case** | Case name with court reference | **CASE ENRICHMENT** |
| A-F: FFL info | Dealer name, address, city, state, license | **TIER 3** |
| T: Time-to-crime | Short TTC < 1095 days | TTC indicator |

### 3.2 DE Gunstat: Final (Google Sheet)
**Sheets:** all identified dealers, Copy organized by def, Need trace info, Trace Unsuccessful, cabelas-all, purchaser name comp

| Key Column | What It Contains | Relevance |
|------------|------------------|-----------|
| **Implicit** | All cases are Delaware | **JURISDICTION = DE** |
| **S: Gunstat summary** | Detailed narrative of recovery/arrest | **JURISDICTION** (NLP) |
| **B: Case** | Defendant + Case # (e.g., "30-22-23525") | **CASE ENRICHMENT** |
| **D: Firearm info** | Make, Serial, Purchase date, Purchaser, NIBIN | **TIER 1** (make) |
| A: FFL | Dealer name, City, State, FFL # (combined) | **TIER 3** |
| E: Status | Pending/Resolved | Case status |

### 3.3 Demand Letters (DL2) (Google Sheet)
**Sheets:** Demand letter 2 FFLs, Full Data, FAQs, Per State Analysis

| Key Column | What It Contains | Relevance |
|------------|------------------|-----------|
| **None** | No crime/event data | No jurisdiction data |
| A-F: FFL info | License Name, Trade Name, Address, City, State, ZIP | **TIER 3** |
| G-J: DL2 2021-2024 | Program participation by year | Dealer risk indicator |
| K: Type of Letter | Continuing/Removal/New Participant | DL2 status |

**Note:** This is dealer-only reference data - no crimes/events to analyze.

### 3.4 PA Gun Tracing Data (CSV/XLSX - 275MB)
**Format:** Standard ATF trace data

| Key Column | What It Contains | Relevance |
|------------|------------------|-----------|
| **Recovery City** | City where gun recovered | **JURISDICTION CRITICAL** |
| **Recovery State** | State where gun recovered | **JURISDICTION CRITICAL** |
| **Firearm Make** | Manufacturer name | **TIER 1** |
| FFL Name/City/State/License | Dealer information | **TIER 3** |
| Time-to-Crime | Days from purchase to crime | TTC indicator |
| Purchase Date | Date of original purchase | Trace timing |

---

## 4. Jurisdiction Extraction Methods

### Priority Order for Determining Where Crime Occurred:

| Priority | Method | Source Columns | Notes |
|----------|--------|----------------|-------|
| 1 | Explicit recovery fields | PA Trace: Recovery City/State | Most reliable |
| 2 | Dataset-level default | DE Gunstat → Delaware | Implicit from program |
| 3 | Parse case number | Crime Gun DB: N (Case) | e.g., "D. Del." = DE |
| 4 | Trafficking flow parsing | Crime Gun DB: P (Case subject) | "AK-->CA" format |
| 5 | NLP on narratives | Crime Gun DB: R, S, U; DE Gunstat: S | Extract locations |

### Case Number Enrichment Opportunities:

| Pattern | Example | Jurisdiction |
|---------|---------|--------------|
| Federal district | "1:23-cv-00456" | Parse district code |
| State format | "30-22-23525" | DE format (needs mapping) |
| Court reference | "D. Del.", "E.D. Pa." | Direct extraction |

---

## 5. Normalized Master Table Schema

### Design Principles:
1. **One row = One crime/event** involving a firearm
2. **Source traceability** via metadata columns
3. **Standardized fields** for consistent querying
4. **Dashboard-ready** structure

### Master Table: `crime_gun_events`

| Field | Type | Description | Source |
|-------|------|-------------|--------|
| **IDENTIFIERS** ||||
| `event_id` | VARCHAR | Unique identifier | Generated (UUID) |
| `source_dataset` | VARCHAR | Which dataset: CG_DB, DE_GUNSTAT, PA_TRACE | Metadata |
| `source_sheet` | VARCHAR | Which sheet/tab within dataset | Metadata |
| `source_row` | INT | Row number in original | **TRACEABILITY** |
| **JURISDICTION (WHERE CRIME OCCURRED)** ||||
| `jurisdiction_state` | CHAR(2) | State where crime occurred | Derived |
| `jurisdiction_city` | VARCHAR | City where crime occurred | Derived |
| `jurisdiction_method` | VARCHAR | How determined: EXPLICIT, IMPLICIT, CASE_PARSE, NLP | Metadata |
| `jurisdiction_confidence` | VARCHAR | HIGH, MEDIUM, LOW | Metadata |
| **SUPPLY CHAIN: TIER 1** ||||
| `manufacturer_name` | VARCHAR | Gun manufacturer/importer | Firearm make |
| `manufacturer_name_raw` | VARCHAR | Original value before standardization | **TRACEABILITY** |
| **SUPPLY CHAIN: TIER 3** ||||
| `dealer_name` | VARCHAR | FFL dealer name | Trace/case data |
| `dealer_city` | VARCHAR | Dealer city | Trace/case data |
| `dealer_state` | CHAR(2) | Dealer state | Trace/case data |
| `dealer_ffl` | VARCHAR | FFL license number | Trace/case data |
| **FIREARM** ||||
| `firearm_serial` | VARCHAR | Serial number | Trace data |
| `firearm_make` | VARCHAR | Make (raw) | Trace data |
| `firearm_model` | VARCHAR | Model | Trace data |
| `firearm_caliber` | VARCHAR | Caliber | Trace data |
| `firearm_type` | VARCHAR | Pistol/Rifle/Shotgun/etc. | Trace data |
| **CASE/EVENT** ||||
| `case_number` | VARCHAR | Court case number | Case data |
| `case_court` | VARCHAR | Court name/jurisdiction | Case data |
| `defendant_name` | VARCHAR | Defendant | Case data |
| `case_status` | VARCHAR | Pending/Resolved | Case data |
| `event_date` | DATE | Date of crime/recovery | Various |
| `facts_narrative` | TEXT | Unstructured story/facts | Case data |
| **TIMING** ||||
| `purchase_date` | DATE | When gun was purchased | Trace data |
| `time_to_crime_days` | INT | Days from purchase to crime | Calculated |
| `is_short_ttc` | BOOLEAN | TTC < 1095 days (3 years) | Calculated |
| **TRAFFICKING** ||||
| `is_interstate` | BOOLEAN | Dealer state ≠ jurisdiction state | Calculated |
| `trafficking_flow` | VARCHAR | Format: "XX-->YY" | Derived |
| **DL2 ENRICHMENT** ||||
| `dealer_in_dl2_2024` | BOOLEAN | Dealer in DL2 program 2024 | Joined from DL2 |
| `dealer_is_revoked` | BOOLEAN | FFL revoked | Crime Gun DB |
| `dealer_is_charged` | BOOLEAN | FFL charged/sued | Crime Gun DB |

---

## 6. Source Traceability

### Every record maintains link to original:

```
crime_gun_events record:
├── source_dataset: "DE_GUNSTAT"
├── source_sheet: "all identified dealers"
├── source_row: 42
└── Can regenerate link: Google Sheet URL + gid + row
```

### Traceability Fields:
- `source_dataset`: Which of the 4 datasets
- `source_sheet`: Which sheet/tab within that dataset
- `source_row`: Row number in original spreadsheet
- `*_raw` fields: Original values before standardization

---

## 7. Dashboard/Visualization Requirements

### Primary Views:

#### View 1: Jurisdiction Summary
*"For crimes in [STATE], show me the supply chain"*

| Metric | Aggregation |
|--------|-------------|
| Total crime gun events | COUNT(*) |
| Unique dealers involved | COUNT(DISTINCT dealer_name) |
| Unique manufacturers | COUNT(DISTINCT manufacturer_name) |
| Interstate trafficking % | SUM(is_interstate) / COUNT(*) |
| Short TTC % | SUM(is_short_ttc) / COUNT(*) |
| Top source states | GROUP BY dealer_state |

#### View 2: Dealer Risk Ranking
*"Which dealers are highest risk for [STATE]?"*

| Metric | Weight |
|--------|--------|
| Crime guns traced | 1x |
| Interstate trafficking | 2x |
| Short TTC count | 3x |
| In DL2 program 2024 | +10 |
| Revoked | +20 |
| Charged/Sued | +15 |

#### View 3: Trafficking Flow Map
*"Where are crime guns coming from?"*

| From State | To State | Count | % of Total |
|------------|----------|-------|------------|
| PA | DE | 150 | 45% |
| VA | DE | 80 | 24% |
| ... | ... | ... | ... |

#### View 4: Manufacturer Analysis
*"Which manufacturers' guns end up in [STATE] crimes?"*

| Manufacturer | Crime Guns | % of Total | Avg TTC |
|--------------|------------|------------|---------|
| GLOCK | 200 | 35% | 450 days |
| SMITH & WESSON | 150 | 26% | 380 days |
| ... | ... | ... | ... |

---

## 8. Supply Chain Coverage

| Tier | Data Available? | Source | Notes |
|------|-----------------|--------|-------|
| **Tier 1** (Manufacturer) | PARTIAL | Firearm make field | Needs standardization |
| **Tier 2** (Distributor) | **NO** | N/A | Known gap |
| **Tier 3** (Dealer/FFL) | **YES** | All datasets | Good coverage |

---

## 9. Data Processing Pipeline

### Step 1: Extract
- Load each source dataset
- Preserve original row numbers for traceability

### Step 2: Transform
- Normalize dealer info (name, city, state, FFL)
- Standardize manufacturer names (Tier 1)
- Extract jurisdiction from available fields
- Calculate derived fields (interstate, TTC)

### Step 3: Enrich
- Join DL2 program data to dealers
- Parse case numbers for court jurisdiction
- Run NLP on narrative fields for location extraction

### Step 4: Load
- Create normalized master table
- Create lookup tables (manufacturers, dealers)
- Generate dashboard-ready views

---

## 10. Gaps & Limitations

| Gap | Impact | Mitigation |
|-----|--------|------------|
| **No Tier 2 (distributor) data** | Can't trace full supply chain | Focus on Tier 1 & 3 |
| **Jurisdiction not always explicit** | May miss records | Multi-source extraction + confidence score |
| **Inconsistent manufacturer names** | Hard to aggregate | Standardization lookup table |
| **Large PA Trace file (275MB)** | Processing complexity | Chunk processing |
| **Narrative NLP needed** | Complex extraction | Start with explicit fields first |

---

## 11. Deliverables

1. **Normalized Master Table** (`crime_gun_events`)
   - Excel/CSV export
   - SQLite database option
   - Source traceability maintained

2. **Lookup Tables**
   - `dim_manufacturers` - Standardized manufacturer reference
   - `dim_dealers` - Deduplicated dealer/FFL reference

3. **Dashboard/Visualization**
   - Jurisdiction summary view
   - Dealer risk ranking
   - Trafficking flow visualization
   - Manufacturer analysis

4. **ETL Pipeline** (Python)
   - Repeatable process
   - Handles all 4 source datasets
   - Maintains traceability

---

## 12. Next Steps

1. [x] Create column inventory across all datasets
2. [x] Document jurisdiction-relevant fields
3. [ ] Confirm this spec captures requirements
4. [ ] Build Python ETL with source traceability
5. [ ] Create manufacturer standardization lookup
6. [ ] Process PA Trace data (sample first due to size)
7. [ ] Generate normalized master table
8. [ ] Build dashboard prototype

---

*Version: 3.0*
*Updated: 2025-01-23*
*Key changes:*
- *Added comprehensive column inventory from all datasets*
- *Added source traceability requirements*
- *Defined dashboard/visualization objectives*
- *Clarified normalized master table approach*
