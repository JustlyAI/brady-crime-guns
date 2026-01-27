---
name: deep-depo-coverage
allowed-tools: Read, Write, Bash
argument-hint: <topics.json> <index1> [index2] [index3] ...
description: Assess one deposition topic against all indexes - simple read and compare
model: sonnet
---

# Deep Depo Coverage - Simple Version

Assess ONE topic per run. Read everything, compare, decide, save.

**Arguments:** $ARGUMENTS

## Step 1: Load All Files

Read ALL files provided in arguments into memory. Do NOT use Grep or search tools.

First file = topics JSON (working file with coverage_status fields)
Remaining files = deposition indexes to compare against (any format: JSON, markdown, text)

## Step 2: Find Next Topic

In the topics JSON, find the first topic where `coverage_status` is `null`.

If none found, count results and output completion message, then exit.

## Step 3: Compare and Match

Look at the topic description. Read through the index files. Find matching entries.

## Step 4: Extract and Append Source Data

When you find a match, **append the full source entry data** to the topic.

Analyze the structure of the source file and bring in ALL fields:

**If source is JSON:**
```json
{
  "coverage_status": "COVERED",
  "matched_entries": [
    {
      "source_file": "index1.json",
      "entry_id": "1.5",
      "topic": "...",
      "page_range": "...",
      "factual_testimony": "...",
      "relevance": "...",
      "exhibits": ["..."]
    }
  ]
}
```

**If source is Markdown table:**
```json
{
  "coverage_status": "COVERED",
  "matched_entries": [
    {
      "source_file": "index1.md",
      "No": "1.5",
      "Topic": "...",
      "Page Range": "...",
      "Factual Testimony / Issue": "...",
      "Relevance to Litigation": "...",
      "References": "..."
    }
  ]
}
```

**If source is unstructured text:**
```json
{
  "coverage_status": "COVERED",
  "matched_entries": [
    {
      "source_file": "index1.txt",
      "extracted_text": "...",
      "page_refs": "..."
    }
  ]
}
```

Key principle: **Mirror the source structure.** Whatever fields exist in the source entry, include them all.

## Step 5: Update JSON

Update ONLY that one topic. Add:
- `coverage_status`: COVERED | PARTIAL | NOT_COVERED
- `matched_entries`: array of all matching entries with full source data
- `notes`: brief summary if needed
- `certainty_level`: "99%"
- `attempt_count`: 1

Write the updated JSON back to the same file (first argument).

## Step 6: Report and Exit

```
Topic [id]: [key]
Status: [COVERED/PARTIAL/NOT_COVERED]
Matched: [X entries from Y files]
```

EXIT. One topic per run.

## Completion

When no topics have null status:

```
ALL TOPICS ASSESSED
Total: X
COVERED: X | PARTIAL: X | NOT_COVERED: X
```
