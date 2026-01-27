---
name: depo-coverage
allowed-tools: Read, Grep, Glob, Write, Bash
argument-hint: [--json <topics.json>] [--indexes <vol1.md> <vol2.md>...] [--output <path>]
description: Compare deposition prep topics against actual deposition topic indexes to identify coverage gaps
model: sonnet
---

# Deposition Coverage Analysis

Analyze deposition coverage by comparing prep topics (from JSON) against actual deposition topic indexes.

**Arguments:** $ARGUMENTS

## Purpose

Systematically compare what was planned to be covered in a deposition against what was actually discussed across one or more deposition volumes. Uses a structured JSON file to track 1:1 coverage of every prep topic.

## Input Requirements

### Prep Topics JSON (Primary Source)

A JSON file containing all prep topics with the structure:
```json
{
  "metadata": {
    "source": "...",
    "witness": "Armando Diaz",
    "total_topics": 202,
    "generated_date": "..."
  },
  "topics": [
    {
      "id": 1,
      "key": "II.1",
      "section": "II. Preliminary Instructions",
      "subsection": "",
      "topic_num": 1,
      "description": "Role of the court reporter...",
      "coverage_status": null,
      "volume_refs": [],
      "notes": ""
    }
  ]
}
```

### Depo Index Files

One or more markdown files containing topic indexes from actual depositions.

### Default Files (Armando Diaz)

If no arguments provided, use these defaults:
- **Prep Topics JSON:** `/Users/laurentwiesel/Dev/AIF/workbench/Armando_Diaz_Deposition_Topics.json`
- **Volume 1:** `/Users/laurentwiesel/Dev/AIF/workbench/Diaz-Volume1-TopicIndex.md`
- **Volume 2:** `/Users/laurentwiesel/Dev/AIF/workbench/Diaz-Volume2-TopicIndex.md`
- **Volume 3:** `/Users/laurentwiesel/Dev/AIF/workbench/Diaz-Volume3-TopicIndex.md`

## Execution Process

### Step 1: Load Prep Topics JSON

Read the JSON file and get the full list of topics with keys (e.g., II.1, III.A.2, VIII.C.4).

**Total Topics:** 195 (verify against metadata.total_topics)

### Step 2: Load Deposition Topic Indexes

For each deposition volume index file:
- Extract all topics discussed with page/line references
- Note the topic ID (e.g., 1.1, 1.2 in Volume I)
- Preserve the page citation format exactly

### Step 3: Assess Coverage for Each Topic

For EACH of the 202 topics in the JSON, determine:

| Status | Definition |
|--------|------------|
| **COVERED** | Topic clearly addressed with substantive testimony |
| **PARTIAL** | Topic touched upon but not fully explored |
| **NOT_COVERED** | No evidence topic was discussed |

Update the JSON object for each topic:
```json
{
  "coverage_status": "COVERED",
  "volume_refs": ["Vol. I pp. 40-55", "Vol. II pp. 133-135"],
  "notes": "Discussed education, FIU degrees, Primavera courses"
}
```

### Step 4: Write Updated JSON

Save the updated JSON with all coverage assessments to:
- `[witness-name]-depo-topics-assessed.json`

### Step 5: Identify Emergent Topics

Scan deposition indexes for topics NOT matching any of the 202 prep topics.

### Step 6: Generate Coverage Report

Create markdown report from the assessed JSON.

## Required Output Files

### 1. Updated JSON (Primary Artifact)

`Armando_Diaz_Deposition_Topics_Assessed.json`

### 2. Coverage Report (Markdown)

```markdown
# Deposition Coverage Analysis: [Witness Name]

**Analysis Date:** [Date]
**Prep Topics Source:** [JSON file path]
**Deposition Volumes Analyzed:** [List with dates]

## Executive Summary

- **Total Prep Topics:** 202
- **Fully Covered:** [X] ([%])
- **Partially Covered:** [X] ([%])
- **Not Yet Covered:** [X] ([%])
- **Emergent Topics:** [X]

## Coverage Matrix

| Key | Section | Subsection | Topic | Status | Volume(s) | Page Refs | Notes |
|-----|---------|------------|-------|--------|-----------|-----------|-------|
| II.1 | II. Preliminary... | — | Role of court reporter... | COVERED | Vol. I | pp. 1-5 | — |
| III.A.1 | III. General... | A. Personal | Identity and prior... | COVERED | Vol. I | pp. 40-55 | AAF litigation |

## Topics NOT YET Covered (by Section)

### Section XI. Settlement Agreement (0/13 covered)
- XI.A.1: Diaz's awareness of and involvement...
- XI.A.2: Reading and understanding of key...
- XI.B.1: Requirement to provide an updated schedule...
[etc.]

### Section XIII. Post-Settlement Agreement Scheduling (0/11 covered)
[etc.]

## Partially Covered Topics (Follow-up Needed)

| Key | Topic | What Was Covered | What Remains |
|-----|-------|------------------|--------------|

## Emergent Topics (Not in Prep)

| Topic | Volume | Pages | Significance |
|-------|--------|-------|--------------|

## Recommendations

### For Next Deposition Session
1. [Specific recommendation with topic keys]

### Document Requests Triggered
- [Documents referenced]

## Verification

- [ ] All 202 topics assessed
- [ ] JSON file updated and saved
- [ ] Percentages sum to 100%
- [ ] All COVERED/PARTIAL have citations
```

## Output Locations

- **Assessed JSON:** `./Armando_Diaz_Deposition_Topics_Assessed.json`
- **Coverage Report:** `./Armando-Diaz-depo-coverage-analysis.md`

## Completion Criteria

The analysis is complete when:

1. **All 202 topics assessed** - Every topic in JSON has a coverage_status
2. **JSON updated and saved** - Assessed JSON written to file
3. **Citations provided** - Each COVERED/PARTIAL has volume_refs populated
4. **Gaps listed by section** - NOT_COVERED items grouped by section
5. **Emergent topics captured** - Topics in indexes not in prep list
6. **Report saved** - Markdown file written

## Verification Checklist

Before marking complete, confirm:

- [ ] JSON topics count = 202
- [ ] All 202 topics have non-null coverage_status
- [ ] COVERED + PARTIAL + NOT_COVERED = 202
- [ ] Page references use consistent format (pp. X-Y)
- [ ] Updated JSON saved to file
- [ ] Markdown report saved to file

## Usage Examples

```bash
# Default Diaz analysis (uses JSON)
/depo-coverage

# Custom JSON file
/depo-coverage --json Smith_Topics.json --indexes smith-vol1.md smith-vol2.md

# With custom output
/depo-coverage --output reports/diaz-coverage.md
```

## Regenerating the JSON from xlsx

If the JSON needs to be recreated from the source xlsx:

```bash
python3 << 'EOF'
import pandas as pd
import json
import re

df = pd.read_excel('Armando_Diaz_Deposition_Topics.xlsx', sheet_name='Deposition Topics')
topics = []
topic_id = 0

for _, row in df.iterrows():
    topic_id += 1
    section = row['Section'] if pd.notna(row['Section']) else ""
    subsection = row['Subsection'] if pd.notna(row['Subsection']) else ""
    topic_num = int(row['Topic #']) if pd.notna(row['Topic #']) else None
    description = row['Topic Description'] if pd.notna(row['Topic Description']) else ""

    section_match = re.match(r'^([IVX]+)\.', section)
    section_code = section_match.group(1) if section_match else ""

    subsection_match = re.match(r'^([A-Z])\.', subsection) if subsection else None
    subsection_code = subsection_match.group(1) if subsection_match else ""

    if subsection_code and topic_num:
        key = f"{section_code}.{subsection_code}.{topic_num}"
    elif topic_num:
        key = f"{section_code}.{topic_num}"
    else:
        key = f"{section_code}"

    topics.append({
        "id": topic_id,
        "key": key,
        "section": section,
        "subsection": subsection,
        "topic_num": topic_num,
        "description": description,
        "coverage_status": None,
        "volume_refs": [],
        "notes": ""
    })

output = {
    "metadata": {
        "source": "Armando_Diaz_Deposition_Topics.xlsx",
        "witness": "Armando Diaz",
        "total_topics": len(topics),
        "generated_date": "2026-01-15"
    },
    "topics": topics
}

with open('Armando_Diaz_Deposition_Topics.json', 'w', encoding='utf-8') as f:
    json.dump(output, f, indent=2, ensure_ascii=False)
print(f"Created JSON with {len(topics)} topics")
EOF
```
