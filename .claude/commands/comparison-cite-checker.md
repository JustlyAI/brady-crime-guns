---
name: comparison-cite-checker
allowed-tools: Read, Write, Bash
argument-hint: <citations.json> <source1> [source2] [source3] ...
description: Citation verification - processes next unverified citation with 99% accuracy target, 90% minimum
model: sonnet
---

# Citation Verification - Simple Version

Verify ONE citation per run. Read everything, compare, decide, save.

**Arguments:** $ARGUMENTS

## Step 1: Load All Files

Read ALL files provided in arguments into memory. Do NOT use Grep or search tools.

First file = citations JSON (working file with verification_status fields)
Remaining files = source materials to verify against (any format: JSON, markdown, text, PDF converted to md)

## Step 2: Find Next Citation

In the citations JSON, find the first citation where `verification_status` is `null`.

If none found, count results and output completion message, then exit.

## Step 3: Verify

Look at the citation's claim/quote and source reference. Read through the source files. Ask yourself:

- Does the source exist?
- Is the location (page, volume, line) correct?
- Does the content match the claim/quote?
- Is the context accurate (not misleading)?

## Step 4: Extract and Append Source Data

When you find the cited content, **append the full source data** to the citation.

Analyze the structure of the source file and bring in ALL relevant fields:

**If source is JSON:**
```json
{
  "verification_status": "ACCURATE",
  "matched_source": {
    "source_file": "deposition.json",
    "volume": "II",
    "page": "88-94",
    "testimony": "...",
    "witness": "...",
    "date": "..."
  }
}
```

**If source is Markdown/Text:**
```json
{
  "verification_status": "ACCURATE",
  "matched_source": {
    "source_file": "report.md",
    "section": "...",
    "page_range": "...",
    "extracted_text": "...",
    "context": "..."
  }
}
```

Key principle: **Mirror the source structure.** Whatever fields exist around the matched content, include them all.

## Step 5: Classify and Update

| Status | Definition |
|--------|-----------|
| ACCURATE | Citation verified as completely accurate |
| MINOR_ISSUE | Trivial error (typo, formatting, off by 1 page) |
| INACCURATE | Substantive error (wrong quote, misattribution, out of context) |
| NOT_FOUND | Source not located in provided files |

Update ONLY that one citation. Add:
- `verification_status`: ACCURATE | MINOR_ISSUE | INACCURATE | NOT_FOUND
- `matched_source`: object with all fields from source (if found)
- `discrepancy`: description of any issues (if applicable)
- `notes`: brief verification summary
- `accuracy_level`: "99%"
- `attempt_count`: 1

Write the updated JSON back to the same file (first argument).

## Step 6: Report and Exit

```
Citation [id]: [reference]
Status: [ACCURATE/MINOR_ISSUE/INACCURATE/NOT_FOUND]
Matched: [source file and location if found]
```

EXIT. One citation per run.

## Completion

When no citations have null status:

```
ALL CITATIONS VERIFIED
Total: X
ACCURATE: X | MINOR_ISSUE: X | INACCURATE: X | NOT_FOUND: X
```
