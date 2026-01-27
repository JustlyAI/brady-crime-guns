# Brady Gun Crime Database - Column Inventory

## Purpose
This document inventories all columns across all datasets to identify which fields are relevant for:
1. **Jurisdiction determination** (where crime/event occurred)
2. **Supply chain actor identification** (Tier 1/2/3)
3. **Case/court enrichment opportunities**

---

## Dataset 1: Crime Gun Dealer Database

### Sheet 1.1: CG court doc FFLs (22 columns)

| Col | Header | Relevance | Notes |
|-----|--------|-----------|-------|
| A | FFL | **TIER 3** | Dealer name |
| B | Address | TIER 3 | Dealer address |
| C | City | TIER 3 | Dealer city |
| D | State | TIER 3 | Dealer state |
| E | (hidden/grouped) | - | - |
| F | License number | TIER 3 | FFL license # |
| G | Which FFL Listing s used | Metadata | Data source |
| H | 2022/2 3/24 DL2 FFL? | TIER 3 | DL2 program flag |
| I | Top trace FFL? | TIER 3 | ATF top trace flag |
| J | Revoked FFL? | TIER 3 | License status |
| K | FFL charged/sued? | TIER 3 | Legal status |
| L | Date Last Checked For Inspection Report | Metadata | - |
| M | Inspection report? | TIER 3 | Compliance |
| N | Case | **CASE** | Case name with court info |
| O | Portfolio Created? | Metadata | - |
| P | Case subject | **JURISDICTION** | Contains trafficking flow "state(s) --> destination(s)", DV indicators, SWB for Mexico |
| Q | Law enforcement recoveries? | JURISDICTION | Recovery indicator |
| R | Location(s) of recovery(ies) | **JURISDICTION CRITICAL** | Where crime/gun recovery occurred |
| S | Info on recoveries, incl any associated crimes | **JURISDICTION CRITICAL** | Narrative with crime details |
| T | Time-to-recovery and/or time-to-crime | TTC | Short TTC = <1095 days (3 years) |
| U | Facts | **JURISDICTION CRITICAL** | Detailed narrative with locations, events |
| V | Notes (Tess) | Notes | - |
| W | Notes | Notes | - |

**Key Jurisdiction Fields:**
- Column R: Location(s) of recovery(ies) - explicit recovery location
- Column S: Info on recoveries - narrative with crime context
- Column U: Facts - detailed narrative with locations
- Column P: Case subject - may contain trafficking flow (e.g., "AK-->CA")
- Column N: Case - court reference that can be parsed for jurisdiction

### Sheet 1.2: Philadelphia Trace (Sparse - ~4 columns with data)
| Col | Header | Relevance | Notes |
|-----|--------|-----------|-------|
| A | FFL | TIER 3 | Dealer name only (Philadelphia area dealers) |
| U | Notes (Tess) | Notes | - |
| V | Notes | Notes | - |

**Note:** This is a simple dealer list with implicit jurisdiction = Philadelphia, PA

### Sheet 1.3: Rochester Trace (Similar structure to Philadelphia)
Implicit jurisdiction = Rochester, NY

### Sheet 1.4: Sheet7 (Unknown - needs review)

### Sheet 1.5: Backdated (Unknown - needs review)

---

## Dataset 2: DE Gunstat: Final

### Sheet 2.1: all identified dealers (Main sheet - ~19+ columns)

| Col | Header | Relevance | Notes |
|-----|--------|-----------|-------|
| A | FFL | **TIER 3** | Combined field: Dealer name, City, State, FFL # (e.g., "Cabela's, Newark, DE, FFL 8-51-01809") |
| B | Case | **CASE** | Defendant name + Case # (e.g., "Aaron Graham, Case # 30-22-23525") |
| C | GunStat Report | CASE | Links to GunStat reports |
| D | Firearm, purchase, NIBIN information | **TIER 1 + FIREARM** | Contains: Make (Taurus, Sig Sauer, S&W, Springfield), Serial #, Purchase date, Purchaser name, NIBIN data |
| E | Pending or resolved? | CASE | Case status |
| ... | (columns F-R need review) | - | May contain additional case/trace details |
| S | Gunstat summary of recovery/arrest | **JURISDICTION CRITICAL** | Detailed narrative of crime/recovery events with locations |

**Key Jurisdiction Fields:**
- Column S: Gunstat summary - contains detailed narratives about where crimes occurred
- Implicit: All cases are Delaware (GunStat program is DE-specific)
- Column B: Case # format may indicate court (e.g., "30-22-23525" needs parsing)

**Key Tier 1 Fields:**
- Column D: Contains firearm make (Taurus, Sig Sauer, S&W, Springfield, etc.)

### Sheet 2.2: Copy of all identified dealers- organized by def
Similar structure, organized by defendant

### Sheet 2.3: Need trace info
Cases needing trace information - incomplete data

### Sheet 2.4: Trace Unsuccessful
Failed traces - may still have dealer/case info

### Sheet 2.5: cabelas – all
Cabela's-specific trace data

### Sheet 2.6: purchaser name comp
Purchaser name comparison data

---

## Dataset 3: Demand Letters (DL2)

### Sheet 3.1: Demand letter 2 FFLs (Main sheet)

| Col | Header | Relevance | Notes |
|-----|--------|-----------|-------|
| A | License Name | **TIER 3** | Official FFL name |
| B | Trade Name | TIER 3 | DBA name |
| C | Address | TIER 3 | Dealer address |
| D | City | TIER 3 | Dealer city |
| E | State | TIER 3 | Dealer state |
| F | ZIP | TIER 3 | ZIP code |
| G | In DL2 Program: 2021 | DL2 | Yes/No |
| H | In DL2 Program: 2022 | DL2 | Yes/No |
| I | In DL2 Program: 2023 | DL2 | Yes/No |
| J | In DL2 Program: 2024 | DL2 | Yes/No |
| K | Type of Letter | DL2 | Continuing/Removal/New Participant |
| L | DL2 dates | DL2 | Letter dates |

**Key Fields:**
- No jurisdiction data (dealer-only, no crime/event data)
- Useful for enriching dealer profiles with DL2 program participation

### Sheet 3.2: Full Data
Extended dealer information

### Sheet 3.3: FAQs
Documentation/reference

### Sheet 3.4: Per State Analysis
State-level DL2 statistics

---

## Dataset 4: PA Gun Tracing Data (CSV/XLSX)

**Note:** File is 275MB/66MB - too large to preview in browser. Based on standard ATF trace data format:

| Col | Header | Relevance | Notes |
|-----|--------|-----------|-------|
| - | FFL Name | **TIER 3** | Dealer name |
| - | FFL City | TIER 3 | Dealer city |
| - | FFL State | TIER 3 | Dealer state |
| - | FFL License # | TIER 3 | FFL number |
| - | Firearm Make | **TIER 1** | Manufacturer |
| - | Firearm Model | FIREARM | Model |
| - | Firearm Serial | FIREARM | Serial # |
| - | Firearm Caliber | FIREARM | Caliber |
| - | Firearm Type | FIREARM | Pistol/Rifle/etc. |
| - | Purchase Date | TRACE | Date of purchase |
| - | Purchaser Name | TRACE | Purchaser (if available) |
| - | Recovery Date | **JURISDICTION** | Date of crime/recovery |
| - | Recovery City | **JURISDICTION CRITICAL** | City where crime occurred |
| - | Recovery State | **JURISDICTION CRITICAL** | State where crime occurred |
| - | Time-to-Crime | TTC | Days from purchase to crime |

**Key Jurisdiction Fields:**
- Recovery City: Where gun was recovered (crime location)
- Recovery State: State of crime/event
- Implicit: "PA" in filename suggests PA recoveries

**Key Tier 1 Fields:**
- Firearm Make: Manufacturer name

---

## Summary: Jurisdiction-Critical Columns

| Dataset | Column | Field Name | Type |
|---------|--------|------------|------|
| Crime Gun DB | R | Location(s) of recovery(ies) | Explicit location |
| Crime Gun DB | S | Info on recoveries | Narrative |
| Crime Gun DB | U | Facts | Narrative |
| Crime Gun DB | P | Case subject | Trafficking flow |
| Crime Gun DB | N | Case | Court reference (enrichment) |
| DE Gunstat | S | Gunstat summary | Narrative |
| DE Gunstat | B | Case | Case # (enrichment) |
| DE Gunstat | - | (Implicit) | All = Delaware |
| PA Trace | - | Recovery City | Explicit |
| PA Trace | - | Recovery State | Explicit |
| Demand Letters | - | (None) | Dealer-only data |

---

## Summary: Supply Chain Columns

### Tier 1 (Manufacturer/Importer)
| Dataset | Column | Notes |
|---------|--------|-------|
| Crime Gun DB | - | Not directly available; may be in firearm descriptions |
| DE Gunstat | D | Firearm make in combined field |
| PA Trace | - | Firearm Make column |

### Tier 2 (Distributor/Wholesaler)
**NO DATA AVAILABLE** - This is a known gap across all datasets.

### Tier 3 (Dealer/FFL)
| Dataset | Columns | Notes |
|---------|---------|-------|
| Crime Gun DB | A-F, H-K | Name, Address, City, State, License #, DL2 flag, Revoked, Charged |
| DE Gunstat | A | Combined: Name, City, State, FFL # |
| Demand Letters | A-L | Full dealer profile + DL2 participation |
| PA Trace | - | FFL Name, City, State, License # |

---

## Enrichment Opportunities

### Case Number Parsing
Case numbers in Crime Gun DB and DE Gunstat may embed court jurisdiction:
- Federal: `1:23-cv-00456` → District court
- DE Gunstat: `30-22-23525` → Needs format analysis
- Can derive state/court from case # patterns

### Narrative NLP Extraction
Columns with narratives (Facts, Summary, Info on recoveries) contain location mentions that can be extracted via NLP:
- Street addresses
- City names
- State names
- Venue references

### Manufacturer Standardization
Firearm "Make" field needs standardization lookup:
- "TAURUS" vs "Taurus" vs "taurus"
- Map to parent company
- Map to HQ location (reference only)

---

## Next Steps

1. [ ] Confirm PA Trace column headers by downloading sample
2. [ ] Review remaining sheets (Sheet7, Backdated, etc.)
3. [ ] Build jurisdiction extraction logic for each source type
4. [ ] Create case number parsing rules
5. [ ] Design NLP pipeline for narrative fields
6. [ ] Build manufacturer standardization lookup

---

*Generated: 2025-01-23*
*Version: 1.0*
