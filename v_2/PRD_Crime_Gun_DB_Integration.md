# Product Requirements Document: Crime Gun Dealer Criminal Database Integration

**Project:** Brady Unified Gun Crime Database
**Version:** 1.0
**Date:** January 27, 2026
**Status:** Draft

---

## 1. Executive Summary

This PRD defines the requirements for integrating the Crime Gun Dealer Criminal Database (`Crime_Gun_Dealer_DB.xlsx`) into the Brady Unified Gun Crime Database ETL pipeline. This dataset contains court case information linking Federal Firearms Licensees (FFLs) to crime guns, with detailed case narratives, recovery locations, and trafficking flow data.

### 1.1 Dataset Overview

| Sheet | Description |
|-------|-------------|
| CG court doc FFLs | Primary sheet: 1,981 rows of FFL-case linkages with detailed court narratives |
| Philadelphia Trace | 54 Philadelphia-area FFLs with time-to-crime data |
| Rochester Trace | Rochester-area FFLs (sparse data) |
| Backdated | Historical records (currently empty) |

**Note:** Sheet7 is excluded per project requirements.

---

## 2. Business Context

### 2.1 Strategic Value

This dataset provides critical court-level evidence linking FFLs to crime guns, enabling Brady to:

- Identify dealers involved in federal and state prosecutions
- Track interstate trafficking patterns from source to destination states
- Document time-to-crime indicators for high-risk dealer identification
- Build comprehensive dealer risk profiles for potential nuisance litigation
- Support jurisdiction nexus analysis for targeted enforcement

### 2.2 Integration with Existing Pipeline

The existing ETL pipeline processes three datasets: DE Gunstat, Demand Letters (DL2), and PA Gun Tracing Data. This fourth dataset adds prosecutorial context missing from trace-only data.

---

## 3. Source Data Specification

### 3.1 CG court doc FFLs (Primary Sheet)

This is the primary data source with 1,981 records and 24 columns.

#### 3.1.1 Column Schema

| Col | Field | Type | Notes |
|-----|-------|------|-------|
| A | FFL | String | Dealer name (Tier 3) |
| B | Address | String | Dealer street address |
| C | City | String | Dealer city |
| D | State | String (2-char) | Dealer state code |
| E | search key | String | Composite key for deduplication |
| F | license number | String | FFL license number |
| H | 2022/23/24 DL2 FFL? | Boolean/String | DL2 program participation flag |
| I | Top trace FFL? | Boolean/String | ATF top trace designation |
| J | Revoked FFL? | Boolean/String | License revocation status |
| K | FFL charged/sued? | Boolean/String | Legal action status |
| N | Case | String | **JURISDICTION** - Case name with court reference |
| P | Case subject | String | Trafficking flow, DV*, SWB indicators |
| R | Location(s) of recovery | String | **JURISDICTION CRITICAL** - Explicit recovery location |
| S | Info on recoveries | Text | Crime narrative with location context |
| T | Time-to-crime | String/Number | Short TTC < 1095 days (3 years) |
| U | Facts | Text (long) | **JURISDICTION CRITICAL** - Detailed case narrative |

#### 3.1.2 Jurisdiction-Critical Fields

Four fields contain jurisdiction data requiring specialized extraction:

1. **Column R (Location(s) of recovery):** Explicit city/state list, often numbered ("1. Woodland, CA\n2. Sacramento, CA")
2. **Column N (Case):** Court reference parsing ("D. Alaska", "E.D. Pa.", "S.D.N.Y.")
3. **Column P (Case subject):** Trafficking flow format ("AK-->CA", "state(s) --> destination(s)")
4. **Column U (Facts):** NLP extraction from detailed narratives

### 3.2 Philadelphia Trace Sheet

Contains 54 records of Philadelphia-area FFLs. Schema is similar to main sheet but with slight column offset (no "Which FFL Listings used" column). Key difference: Column R contains numeric time-to-crime values rather than location text.

**Implicit jurisdiction:** Philadelphia, PA for all records.

### 3.3 Rochester Trace Sheet

Structure mirrors Philadelphia Trace. Currently contains sparse data.

**Implicit jurisdiction:** Rochester, NY.

---

## 4. Data Transformation Requirements

### 4.1 Unified Schema Mapping

Map Crime Gun DB fields to the existing unified schema:

| Source Field | Target Field | Transform |
|--------------|--------------|-----------|
| A: FFL | `ffl_name` | Clean whitespace |
| B: Address | `ffl_premise_street` | Direct |
| C: City | `ffl_premise_city` | Normalize case |
| D: State | `ffl_premise_state` | Validate 2-char |
| F: license number | `ffl_license_number` | Standardize format |
| R: Location(s) of recovery | `recovery_city`, `recovery_state` | Parse multi-location |
| N: Case | `case_name`, `case_court` | Parse court ref |
| P: Case subject | `trafficking_flow`, `case_tags` | Extract patterns |
| T: Time-to-crime | `time_to_crime_days` | Parse to integer |
| U: Facts | `facts_narrative` | Store as text |
| H: DL2 FFL? | `in_dl2_program` | Boolean conversion |
| I: Top trace FFL? | `is_top_trace_ffl` | Boolean conversion |
| J: Revoked FFL? | `is_revoked` | Boolean conversion |
| K: FFL charged/sued? | `is_charged_or_sued` | Boolean conversion |

### 4.2 Jurisdiction Extraction Logic

Implement a multi-stage extraction pipeline with confidence scoring:

#### Priority 1: Explicit Recovery Location (Column R)

Parse patterns like "1. Woodland, CA" or "Sacramento, CA" to extract city and state. Handle multi-location lists by creating separate records or storing as array.

**Confidence:** HIGH

#### Priority 2: Case Court Reference (Column N)

Parse federal district court references:

- "D. Alaska" → AK
- "E.D. Pa." → PA (Eastern District)
- "S.D.N.Y." → NY (Southern District)
- "N.D. Ill." → IL (Northern District)

**Confidence:** MEDIUM-HIGH (indicates prosecution venue, may differ from crime location)

#### Priority 3: Trafficking Flow (Column P)

Extract source and destination from patterns:

- "AK-->CA" → source_state: AK, destination_state: CA
- "state(s) --> destination(s)" notation
- "SWB" indicator for Mexico border trafficking
- "DV*" indicator for domestic violence cases

**Confidence:** MEDIUM

#### Priority 4: NLP on Narratives (Column U)

For records without explicit locations, apply location extraction to Facts narrative. Use spaCy or similar NER to identify GPE (geopolitical entities).

**Confidence:** LOW-MEDIUM (requires validation)

#### Priority 5: Sheet-Level Default

Apply implicit jurisdiction for specialized sheets:

- Philadelphia Trace → Philadelphia, PA
- Rochester Trace → Rochester, NY

**Confidence:** MEDIUM

---

## 5. Technical Implementation

### 5.1 ETL Pipeline Updates

Extend `brady_unified_etl.py` with new extraction module.

#### 5.1.1 New Python Module: `crime_gun_db_extractor.py`

```python
# Module functions
def load_crime_gun_db(xlsx_path: str) -> dict[str, pd.DataFrame]:
    """Load all sheets, skip Sheet7"""

def parse_recovery_locations(text: str) -> list[dict]:
    """Multi-location parser for Column R"""

def parse_case_court(case_text: str) -> dict:
    """Federal court code extractor from Column N"""

def parse_trafficking_flow(subject_text: str) -> dict:
    """Arrow notation parser for Column P"""

def extract_locations_nlp(narrative: str) -> list[str]:
    """spaCy GPE extraction for Column U"""

def transform_to_unified(df: pd.DataFrame) -> pd.DataFrame:
    """Schema mapping function"""
```

#### 5.1.2 Sheet Processing Strategy

| Sheet | Processing |
|-------|------------|
| CG court doc FFLs | Full extraction pipeline with all jurisdiction methods |
| Philadelphia Trace | Apply schema offset (+1 col); set implicit jurisdiction |
| Rochester Trace | Apply schema offset; set implicit jurisdiction |
| Backdated | Skip if empty; process if populated in future |
| Sheet7 | **SKIP** - excluded per requirements |

### 5.2 Data Quality Handling

- Row 2 contains test/placeholder data ("?") - filter out
- Handle multi-line FFL names ("aka" patterns)
- Parse numbered lists in recovery locations
- Handle date parsing errors (e.g., Cell F1232 invalid date serial)
- Validate state codes against standard 2-character list

### 5.3 Source Traceability

Maintain full traceability to source records:

| Field | Value |
|-------|-------|
| `source_dataset` | "CRIME_GUN_DB" |
| `source_sheet` | Sheet name (e.g., "CG court doc FFLs") |
| `source_row` | Original row number (1-indexed) |
| `jurisdiction_method` | EXPLICIT_RECOVERY \| CASE_COURT \| TRAFFICKING_FLOW \| NLP \| IMPLICIT |
| `jurisdiction_confidence` | HIGH \| MEDIUM \| LOW |

---

## 6. Acceptance Criteria

### 6.1 Functional Requirements

- [ ] All 1,981 CG court doc FFLs records processed with no data loss
- [ ] 54 Philadelphia Trace records mapped to unified schema
- [ ] Recovery locations extracted for 80%+ of records with Column R data
- [ ] Court references parsed for all standard federal district patterns
- [ ] Trafficking flows extracted from "XX-->YY" patterns
- [ ] Source traceability maintained for 100% of records

### 6.2 Data Quality Metrics

| Metric | Target | Minimum |
|--------|--------|---------|
| Records with jurisdiction identified | 90% | 75% |
| High-confidence jurisdiction | 60% | 40% |
| Valid FFL state codes | 99% | 95% |
| Trafficking flows extracted | 95% | 85% |

### 6.3 Integration Tests

- [ ] End-to-end pipeline runs without errors
- [ ] Output unified schema matches existing specification
- [ ] Dealer risk scores calculate correctly with new data
- [ ] Jurisdiction summary aggregates include Crime Gun DB records
- [ ] Dashboard visualizations render new dataset

---

## 7. Dependencies and Risks

### 7.1 Dependencies

- `openpyxl` for Excel parsing (already in requirements.txt)
- `spaCy` with `en_core_web_sm` model for NLP extraction (optional)
- Existing unified schema from `brady_unified_etl.py`
- Access to source file (`Crime_Gun_Dealer_DB.xlsx`)

### 7.2 Risks and Mitigations

| Risk | Impact | Mitigation |
|------|--------|------------|
| NLP extraction accuracy | Low-confidence jurisdictions | Prioritize explicit fields; flag NLP results |
| Schema drift in source | Column mapping breaks | Header validation; graceful failure |
| Multi-location records | Record explosion | Store as array; optional expansion |
| Philadelphia/Rochester sparse | Limited value add | Focus on main sheet; monitor updates |

---

## 8. Timeline and Milestones

| Phase | Deliverable | Duration |
|-------|-------------|----------|
| 1 | PRD approval and schema finalization | 1 day |
| 2 | Core extraction module (no NLP) | 2 days |
| 3 | NLP extraction (optional enhancement) | 1 day |
| 4 | Integration testing and validation | 1 day |
| 5 | Dashboard updates and documentation | 1 day |

**Total estimated effort:** 5-6 days

---

## Appendix A: Sample Data Patterns

### A.1 Recovery Location Patterns (Column R)

```
1. Woodland, CA
2. Citrus Heights, CA (Sacramento burb)
```

```
Sacramento, CA
```

```
Vacaville, CA
```

### A.2 Case Reference Patterns (Column N)

```
U.S. v. Pangilinan et. al., D. Alaska, No. 20-cr-92
```

```
U.S. v. Smith, No. 23-cr-17 (D. Alaska)
```

### A.3 Trafficking Flow Patterns (Column P)

```
Eagle River man guilty of trafficking firearms from Alaska to California
```

```
FFL theft (22 guns)
```

Format notation: "AK-->CA", "state(s) --> destination(s)"

Special indicators: "DV*" (domestic violence), "SWB" (Mexico border)

---

## Appendix B: Federal District Court Codes

| Code | District | State |
|------|----------|-------|
| D. Alaska | District of Alaska | AK |
| E.D. Pa. | Eastern District of Pennsylvania | PA |
| W.D. Pa. | Western District of Pennsylvania | PA |
| S.D.N.Y. | Southern District of New York | NY |
| E.D.N.Y. | Eastern District of New York | NY |
| N.D. Ill. | Northern District of Illinois | IL |
| C.D. Cal. | Central District of California | CA |
| N.D. Cal. | Northern District of California | CA |
| S.D. Cal. | Southern District of California | CA |
| E.D. Cal. | Eastern District of California | CA |
| D.D.C. | District of Columbia | DC |

---

*Generated: January 27, 2026*
