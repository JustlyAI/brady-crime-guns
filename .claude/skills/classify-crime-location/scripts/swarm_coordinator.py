#!/usr/bin/env python3
"""
Crime Location Classifier Swarm Coordinator

Coordinates parallel deployment of classifier agents to process CSV records.
Dispatches up to 20 agents concurrently using Task tool pattern.

Usage:
    python swarm_coordinator.py --input data/processed/crime_gun_events.csv --output results.csv
    python swarm_coordinator.py --input data.csv --batch-size 20 --skip-existing
"""

import argparse
import csv
import json
import os
import sys
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field
from termcolor import cprint


class SwarmConfig(BaseModel):
    """Configuration for swarm processing."""
    input_file: str
    output_file: str
    batch_size: int = Field(default=20, ge=1, le=20)
    skip_existing: bool = True
    start_row: Optional[int] = None
    end_row: Optional[int] = None


class BatchResult(BaseModel):
    """Results from a batch of classifications."""
    batch_id: int
    records_processed: int
    records_skipped: int
    records_failed: int
    results: list


def load_csv_records(config: SwarmConfig) -> list[dict]:
    """Load records from CSV file that need classification."""
    records = []

    cprint(f"[LOAD] Reading {config.input_file}", "cyan")

    with open(config.input_file, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        headers = reader.fieldnames

        for i, row in enumerate(reader, start=2):  # Row 2 is first data row after header
            row["_source_row"] = i

            # Apply row range filter
            if config.start_row and i < config.start_row:
                continue
            if config.end_row and i > config.end_row:
                continue

            # Skip if already has location data (if skip_existing enabled)
            if config.skip_existing:
                existing_state = row.get("jurisdiction_state") or row.get("crime_location_state")
                if existing_state and existing_state.strip():
                    continue

            records.append(row)

    cprint(f"[LOAD] Found {len(records)} records needing classification", "green")
    return records, headers


def create_batches(records: list[dict], batch_size: int) -> list[list[dict]]:
    """Split records into batches for parallel processing."""
    batches = []
    for i in range(0, len(records), batch_size):
        batches.append(records[i:i + batch_size])

    cprint(f"[BATCH] Created {len(batches)} batches of up to {batch_size} records", "cyan")
    return batches


def generate_agent_prompt(record: dict) -> str:
    """Generate prompt for a single classifier agent."""
    # Clean record for prompt - remove very long fields
    clean_record = {k: v for k, v in record.items() if k != "_source_row"}
    summary = clean_record.get("case_summary", "")
    if len(summary) > 2000:
        clean_record["case_summary"] = summary[:2000] + "... [truncated]"

    return f"""Classify the crime location for this record.

**Record Data:**
```json
{json.dumps(clean_record, indent=2, default=str)}
```

**Instructions:**
1. Determine WHERE THE CRIME OCCURRED (not dealer location)
2. Use these strategies in priority order:
   - Dataset defaults: DE_GUNSTAT → Delaware, PA_TRACE → Pennsylvania
   - Case number parsing: Look for court codes like "D. Del.", "E.D. Pa."
   - Trafficking flows: Parse "XX-->YY" patterns for destination
   - Narrative extraction: Find city names, police departments, street addresses

3. Return JSON with these fields:
   - crime_location_state: Two-letter state code (e.g., "DE")
   - crime_location_city: City name if determinable
   - crime_location_zip: ZIP code if mentioned (usually null)
   - crime_location_court: Court name if identifiable
   - crime_location_pd: Police department if mentioned
   - crime_location_reasoning: Explain how you determined each value
   - confidence: "HIGH", "MEDIUM", or "LOW"

**Source Row:** {record.get("_source_row", "unknown")}
"""


def generate_batch_dispatch_code(batch: list[dict], batch_id: int) -> str:
    """Generate Task tool calls for a batch of records."""
    prompts = []
    for record in batch:
        prompt = generate_agent_prompt(record)
        prompts.append({
            "source_row": record.get("_source_row"),
            "prompt": prompt
        })

    return f"""
## Batch {batch_id}: {len(batch)} Records

Deploy {len(batch)} crime-location-classifier agents in parallel using Task tool.

**Agent Prompts:**

{json.dumps(prompts, indent=2)}

For each record, create a Task tool call with:
- subagent_type: "crime-location-classifier"
- description: "Classify crime location row {{source_row}}"
- prompt: The prompt from above
- model: "haiku" (fast, cost-effective)

IMPORTANT: Send ALL {len(batch)} Task calls in a SINGLE message to run in parallel.
"""


def write_results(config: SwarmConfig, headers: list, original_records: dict, results: list[dict]):
    """Write classification results back to CSV."""
    # Add new columns if not present
    new_columns = [
        "crime_location_state",
        "crime_location_city",
        "crime_location_zip",
        "crime_location_court",
        "crime_location_pd",
        "crime_location_reasoning"
    ]

    output_headers = list(headers)
    for col in new_columns:
        if col not in output_headers:
            output_headers.append(col)

    # Merge results into original records
    results_by_row = {r.get("source_row"): r for r in results}

    cprint(f"[WRITE] Writing results to {config.output_file}", "cyan")

    with open(config.output_file, 'w', encoding='utf-8', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=output_headers)
        writer.writeheader()

        for row_num, record in original_records.items():
            if row_num in results_by_row:
                result = results_by_row[row_num]
                for col in new_columns:
                    record[col] = result.get(col, "")
            writer.writerow({k: record.get(k, "") for k in output_headers})

    cprint(f"[WRITE] Done - {len(results)} records updated", "green")


def print_summary(total: int, processed: int, skipped: int, failed: int):
    """Print processing summary."""
    print("\n" + "=" * 50)
    cprint("SWARM PROCESSING SUMMARY", "yellow", attrs=["bold"])
    print("=" * 50)
    print(f"Total records:     {total}")
    print(f"Processed:         {processed}")
    print(f"Skipped (existing): {skipped}")
    print(f"Failed:            {failed}")
    print(f"Success rate:      {(processed / max(processed + failed, 1)) * 100:.1f}%")
    print("=" * 50 + "\n")


def main():
    parser = argparse.ArgumentParser(description="Coordinate crime location classifier swarm")
    parser.add_argument("--input", required=True, help="Input CSV file path")
    parser.add_argument("--output", required=True, help="Output CSV file path")
    parser.add_argument("--batch-size", type=int, default=20, help="Records per batch (max 20)")
    parser.add_argument("--skip-existing", action="store_true", default=True, help="Skip records with existing data")
    parser.add_argument("--start-row", type=int, help="Start from this row number")
    parser.add_argument("--end-row", type=int, help="End at this row number")
    parser.add_argument("--dry-run", action="store_true", help="Print batch prompts without executing")

    args = parser.parse_args()

    config = SwarmConfig(
        input_file=args.input,
        output_file=args.output,
        batch_size=min(args.batch_size, 20),
        skip_existing=args.skip_existing,
        start_row=args.start_row,
        end_row=args.end_row
    )

    # Load records
    records, headers = load_csv_records(config)

    if not records:
        cprint("[DONE] No records need classification", "yellow")
        return

    # Create batches
    batches = create_batches(records, config.batch_size)

    if args.dry_run:
        cprint("[DRY RUN] Printing batch prompts:", "yellow")
        for i, batch in enumerate(batches):
            print(generate_batch_dispatch_code(batch, i + 1))
        return

    # Print dispatch instructions for Claude
    cprint("\n" + "=" * 60, "cyan")
    cprint("SWARM DISPATCH INSTRUCTIONS", "yellow", attrs=["bold"])
    cprint("=" * 60, "cyan")
    print(f"""
Total records to process: {len(records)}
Batches: {len(batches)} (up to {config.batch_size} records each)

To process, dispatch agents batch by batch using the Task tool.
Each batch runs up to {config.batch_size} agents in parallel.

After all batches complete, aggregate results and update the CSV.
""")

    for i, batch in enumerate(batches):
        print(f"\n--- Batch {i + 1}/{len(batches)} ---")
        print(f"Records: {[r.get('_source_row') for r in batch]}")

        if i == 0:
            # Show full example for first batch
            print(generate_batch_dispatch_code(batch, i + 1))


if __name__ == "__main__":
    main()
