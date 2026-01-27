---
name: depo-coverage-report
allowed-tools: Read, Write, Bash
argument-hint: [--json <assessed.json>] [--output <path>]
description: Generate comprehensive coverage analysis report from assessed deposition topics JSON
model: sonnet
---

# Deposition Coverage Report Generator

Generate strategic coverage analysis report from assessed topics JSON.

**Arguments:** $ARGUMENTS

## Defaults

- **JSON:** `.projects/trumpgrp/depo-coverage-analysis/diaz/outputs/Armando_Diaz_Deposition_Topics_Assessed.json`
- **Output:** Same directory, filename `Deposition_Coverage_Report_[Witness]_[YYYY-MM-DD_HHMMSS].md`

## Process

### 1. Load & Validate JSON

Verify all topics have:
- `coverage_status` (COVERED, PARTIAL, NOT_COVERED)
- Volume references for COVERED/PARTIAL
- Certainty levels and search terms

Note incomplete assessments prominently.

### 2. Calculate Statistics

**Overall:** Total, covered, partial, not covered (counts and percentages)

**By Section:** For each major section (II, III, IV...), show coverage breakdown

**Quality Metrics:** Average certainty, topics with 99%+ certainty, multi-volume references

### 3. Analyze Patterns

- **High coverage (>80%):** What was prioritized and why
- **Gaps (<20%):** Systematic avoidances, strategic implications
- **Partial coverage:** What was touched but not exhausted
- **Volume distribution:** How coverage evolved across volumes

### 4. Generate Recommendations

- Priority topics for next session
- Discovery actions triggered (document requests, interrogatories)
- Strategic implications for case theory

## Output Report Structure

```markdown
# Deposition Coverage Analysis Report
**Witness:** [Name]
**Case:** A3 Development v. Suffolk Construction
**Analysis Date:** [Date]
**Volumes Analyzed:** [List]

---

## Executive Summary

[2-3 paragraphs: key findings, coverage rate, major gaps, strategic implications]

**Key Statistics:**
| Status | Count | Percentage |
|--------|-------|------------|
| COVERED | X | X% |
| PARTIAL | X | X% |
| NOT_COVERED | X | X% |

**Critical Findings:**
- [3-5 bullet points]

---

## Coverage by Section

| Section | Total | Covered | Partial | Not Covered | Coverage % |
|---------|-------|---------|---------|-------------|------------|
| II. Preliminary Instructions | X | X | X | X | X% |
| III. General Background | X | X | X | X | X% |
[etc.]

---

## Strategic Analysis

### High-Coverage Areas (>80%)

**[Section Name]** - X% coverage
- Strategic significance
- Key findings/admissions
- Documents referenced

### Coverage Gaps (<20%)

**[Section Name]** - X% coverage
- Why these gaps matter
- Possible reasons for avoidance
- Implications for case strategy

### Volume Progression

- **Volume I:** Primary focus and what was established
- **Volume II:** Strategy shift or topic evolution
- **Volume III:** Conclusion and revisited topics

---

## Detailed Gap Analysis

For each NOT_COVERED topic in sections with significant gaps:

**Topic [Key]:** [Description]
- Search terms used
- Why this matters
- Recommendation

---

## Partial Coverage Items

For PARTIAL topics worth completing:

**Topic [Key]:** [Description]
- What was covered (volume/pages)
- What remains unexplored
- Strategic value of completion

---

## Recommendations

### Next Deposition Session

**Priority 1 (Must Cover):**
1. [Topic] - Why critical, approach, documents needed

**Priority 2 (Should Cover):**
1. [Topic] - Why valuable if time permits

### Discovery Actions

**Document Requests:**
1. [Document] - Justification from testimony

**Interrogatories:**
1. [Question] - Gap it addresses

---

## Appendix: Complete Coverage Matrix

| Key | Topic | Status | Volume(s) | Pages | Certainty |
|-----|-------|--------|-----------|-------|-----------|
| II.1 | Role of court reporter | COVERED | Vol. I | 1-5 | 99% |
[all topics]

---

*Analysis completed: [Timestamp]*
*Source: [JSON path]*
```

## Quality Standards

- **Strategic:** Insights about what coverage patterns mean, not just statistics
- **Actionable:** Specific recommendations with reasoning
- **Evidence-based:** Findings supported by citations
- **Professional:** Suitable for litigation team or client

## Usage

```bash
# Default (Diaz)
/depo-coverage-report

# Custom JSON
/depo-coverage-report --json path/to/assessed.json

# Custom output
/depo-coverage-report --output path/to/report.md
```
