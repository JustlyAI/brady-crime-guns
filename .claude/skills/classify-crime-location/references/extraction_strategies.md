# Location Extraction Strategies

## Priority Order

Use these methods in order of reliability:

| Priority | Method | Confidence | Source |
|----------|--------|------------|--------|
| 1 | Explicit recovery fields | HIGH | Recovery City/State columns |
| 2 | Dataset-level default | HIGH | DE_GUNSTAT → DE, PA_TRACE → PA |
| 3 | Case number parsing | MEDIUM | Court codes in case numbers |
| 4 | Trafficking flow parsing | MEDIUM | "XX-->YY" patterns in case_subject |
| 5 | NLP on narratives | LOW-MEDIUM | Location extraction from text |

---

## Strategy 1: Dataset Defaults

### DE_GUNSTAT Records
- All records default to `crime_location_state = "DE"`
- City often extractable from narrative (Wilmington, Dover, Newark common)
- Court: Delaware courts use format like "30-22-23525"

### PA_TRACE Records
- All records default to `crime_location_state = "PA"`
- Recovery City column contains explicit city
- Recovery State column confirms PA or out-of-state

---

## Strategy 2: Case Number Parsing

### Federal Court Patterns

| Pattern | Example | Court |
|---------|---------|-------|
| `[N]:YY-cv-NNNNN` | "1:23-cv-00456" | District court (N = district) |
| `D. [State]` | "D. Del." | District of Delaware |
| `E.D. [State]` | "E.D. Pa." | Eastern District of Pennsylvania |
| `S.D.N.Y.` | | Southern District of New York |

### State Court Patterns

| State | Pattern | Notes |
|-------|---------|-------|
| DE | "30-22-NNNNN" | Delaware Superior Court format |
| PA | varies | County-based numbering |

---

## Strategy 3: Trafficking Flow Parsing

Parse "Case subject" column for patterns:
- `"AK-->CA"` → Destination = CA
- `"PA, VA --> DE"` → Destination = DE
- `"SWB"` → Southwest Border (Mexico destination)

Regex: `([A-Z]{2}(?:,\s*[A-Z]{2})*)\s*(?:-->|->|to)\s*([A-Z]{2})`

---

## Strategy 4: Narrative NLP Extraction

### Key Columns
- `case_summary`: Detailed narrative of events
- `Facts` (in raw data): Event descriptions

### Location Indicators

**Street Addresses:**
- Pattern: "[Number] [Direction] [Street Name] Street/Avenue/Road"
- Example: "E. 10th and N. Pine Streets"

**City Mentions:**
- Delaware: Wilmington, Dover, Newark, New Castle
- Pennsylvania: Philadelphia, Pittsburgh, Harrisburg

**Police Department Mentions:**
- "Wilmington PD", "Philadelphia Police", "[City] Police Department"
- Extract city from PD name

**Court Mentions:**
- "was bound over to [Court]"
- "charged in [Court]"

### Extraction Prompt Template

```
Analyze this crime gun record and extract location information.

Record:
{record_text}

Extract:
1. crime_location_state: Two-letter state code where crime occurred
2. crime_location_city: City name where crime occurred
3. crime_location_zip: ZIP code if mentioned
4. crime_location_court: Court handling the case
5. crime_location_pd: Police department mentioned
6. reasoning: Brief explanation of how you determined each value

If a value cannot be determined, use null.
Confidence: HIGH if explicit, MEDIUM if inferred, LOW if uncertain.
```

---

## Output Format

Each classifier agent returns JSON:

```json
{
  "source_row": 42,
  "crime_location_state": "DE",
  "crime_location_city": "Wilmington",
  "crime_location_zip": null,
  "crime_location_court": "Delaware Superior Court",
  "crime_location_pd": "Wilmington PD",
  "crime_location_reasoning": "Dataset is DE_GUNSTAT (implicit DE). City extracted from narrative: 'at E. 10th and N. Pine Streets' in Wilmington area. Court inferred from case format 30-23-063056.",
  "confidence": "HIGH"
}
```
