#!/usr/bin/env python3
"""
Crime Location Classifier

Classifies crime location for a single record using multiple extraction strategies.
Designed to be called by swarm coordinator or run standalone.

Usage:
    python classify_location.py --record '{"id": 1, "source_dataset": "DE_GUNSTAT", ...}'
    python classify_location.py --db data/brady.db --id 5
    python classify_location.py --db data/brady.db --id 5 --update
"""

import argparse
import json
import re
import sqlite3
import sys
from pathlib import Path
from typing import Optional
from pydantic import BaseModel, Field
from termcolor import cprint


class LocationResult(BaseModel):
    """Result of location classification."""
    record_id: int
    crime_location_state: Optional[str] = Field(None, max_length=2)
    crime_location_city: Optional[str] = None
    crime_location_zip: Optional[str] = None
    crime_location_court: Optional[str] = None
    crime_location_pd: Optional[str] = None
    crime_location_reasoning: str
    confidence: str = Field(..., pattern="^(HIGH|MEDIUM|LOW)$")


# Dataset defaults
DATASET_DEFAULTS = {
    "DE_GUNSTAT": {"state": "DE", "confidence": "HIGH"},
    "PA_TRACE": {"state": "PA", "confidence": "HIGH"},
}

# Federal court patterns
FEDERAL_COURT_PATTERNS = {
    r"D\.\s*Del\.": ("DE", "District of Delaware"),
    r"E\.D\.\s*Pa\.": ("PA", "Eastern District of Pennsylvania"),
    r"W\.D\.\s*Pa\.": ("PA", "Western District of Pennsylvania"),
    r"M\.D\.\s*Pa\.": ("PA", "Middle District of Pennsylvania"),
    r"S\.D\.N\.Y\.": ("NY", "Southern District of New York"),
    r"E\.D\.N\.Y\.": ("NY", "Eastern District of New York"),
    r"D\.N\.J\.": ("NJ", "District of New Jersey"),
}

# Delaware cities
DE_CITIES = ["Wilmington", "Dover", "Newark", "New Castle", "Middletown", "Smyrna", "Milford", "Seaford", "Georgetown"]

# Pennsylvania cities
PA_CITIES = ["Philadelphia", "Pittsburgh", "Harrisburg", "Allentown", "Erie", "Reading", "Scranton", "Bethlehem"]


def extract_from_dataset_default(record: dict) -> Optional[dict]:
    """Extract state from dataset-level defaults."""
    source_dataset = record.get("source_dataset", "")
    if source_dataset in DATASET_DEFAULTS:
        default = DATASET_DEFAULTS[source_dataset]
        return {
            "state": default["state"],
            "confidence": default["confidence"],
            "method": f"Dataset default: {source_dataset} implies {default['state']}"
        }
    return None


def extract_from_case_number(record: dict) -> Optional[dict]:
    """Extract court/state from case number patterns."""
    case_number = record.get("case_number", "") or ""

    # Check federal court patterns
    for pattern, (state, court) in FEDERAL_COURT_PATTERNS.items():
        if re.search(pattern, case_number, re.IGNORECASE):
            return {
                "state": state,
                "court": court,
                "confidence": "MEDIUM",
                "method": f"Parsed court from case number: {court}"
            }

    # Delaware Superior Court format: NN-YY-NNNNN
    if re.match(r"\d{2}-\d{2}-\d+", case_number):
        return {
            "court": "Delaware Superior Court",
            "confidence": "MEDIUM",
            "method": f"Case number format {case_number} matches Delaware Superior Court pattern"
        }

    return None


def extract_from_trafficking_flow(record: dict) -> Optional[dict]:
    """Extract destination state from trafficking flow patterns."""
    case_subject = record.get("case_subject", "") or ""

    # Pattern: "XX-->YY" or "XX, YY --> ZZ"
    flow_pattern = r"([A-Z]{2}(?:,\s*[A-Z]{2})*)\s*(?:-->|->|to)\s*([A-Z]{2})"
    match = re.search(flow_pattern, case_subject)

    if match:
        destination = match.group(2)
        return {
            "state": destination,
            "confidence": "MEDIUM",
            "method": f"Trafficking flow destination: {match.group(0)}"
        }

    return None


def extract_from_narrative(record: dict) -> Optional[dict]:
    """Extract location from narrative text via pattern matching."""
    narrative = record.get("case_summary", "") or ""
    results = {"confidence": "LOW", "methods": []}

    # Look for city mentions
    for city in DE_CITIES:
        if city.lower() in narrative.lower():
            results["city"] = city
            results["state"] = "DE"
            results["methods"].append(f"City '{city}' found in narrative")
            results["confidence"] = "MEDIUM"
            break

    if not results.get("city"):
        for city in PA_CITIES:
            if city.lower() in narrative.lower():
                results["city"] = city
                results["state"] = "PA"
                results["methods"].append(f"City '{city}' found in narrative")
                results["confidence"] = "MEDIUM"
                break

    # Look for police department mentions
    pd_pattern = r"(\w+(?:\s+\w+)?)\s+(?:Police|PD|Police Department)"
    pd_match = re.search(pd_pattern, narrative, re.IGNORECASE)
    if pd_match:
        results["pd"] = pd_match.group(0)
        results["methods"].append(f"Police dept found: {pd_match.group(0)}")

        # Infer city from PD name
        pd_city = pd_match.group(1).strip()
        if not results.get("city") and pd_city.lower() not in ["the", "city", "local"]:
            results["city"] = pd_city
            results["methods"].append(f"City inferred from PD: {pd_city}")

    # Look for street addresses (indicates Wilmington for DE)
    street_pattern = r"(\d+\s+)?([NSEW]\.?\s+)?\d+(?:st|nd|rd|th)?\s+(?:and|&)\s+[NSEW]?\.?\s*\w+\s+(?:Street|St|Avenue|Ave)"
    if re.search(street_pattern, narrative, re.IGNORECASE):
        if results.get("state") == "DE":
            if not results.get("city"):
                results["city"] = "Wilmington"
                results["methods"].append("Street address format typical of Wilmington")

    if results.get("methods"):
        results["method"] = "; ".join(results["methods"])
        return results

    return None


def classify_record(record: dict) -> LocationResult:
    """
    Classify crime location for a single record.
    Uses multiple strategies in priority order.
    """
    record_id = record.get("id", 0)

    cprint(f"[CLASSIFY] Processing record ID {record_id}", "cyan")

    # Collect results from all strategies
    state = None
    city = None
    court = None
    pd = None
    reasoning_parts = []
    confidence = "LOW"

    # Strategy 1: Dataset defaults
    default_result = extract_from_dataset_default(record)
    if default_result:
        state = default_result.get("state")
        confidence = default_result.get("confidence", confidence)
        reasoning_parts.append(default_result.get("method", ""))
        cprint(f"  [DEFAULT] State from dataset: {state}", "green")

    # Strategy 2: Case number parsing
    case_result = extract_from_case_number(record)
    if case_result:
        if not state:
            state = case_result.get("state")
        court = case_result.get("court")
        if case_result.get("confidence") == "HIGH" or not default_result:
            confidence = case_result.get("confidence", confidence)
        reasoning_parts.append(case_result.get("method", ""))
        cprint(f"  [CASE] Court: {court}", "green")

    # Strategy 3: Trafficking flow
    flow_result = extract_from_trafficking_flow(record)
    if flow_result:
        if not state:
            state = flow_result.get("state")
            confidence = flow_result.get("confidence", confidence)
        reasoning_parts.append(flow_result.get("method", ""))
        cprint(f"  [FLOW] Destination: {flow_result.get('state')}", "green")

    # Strategy 4: Narrative extraction
    narrative_result = extract_from_narrative(record)
    if narrative_result:
        if not city:
            city = narrative_result.get("city")
        if not state:
            state = narrative_result.get("state")
            confidence = narrative_result.get("confidence", confidence)
        if narrative_result.get("pd"):
            pd = narrative_result.get("pd")
        if narrative_result.get("method"):
            reasoning_parts.append(narrative_result.get("method"))
        cprint(f"  [NLP] City: {city}, PD: {pd}", "green")

    # Compile reasoning
    reasoning = " | ".join([r for r in reasoning_parts if r])
    if not reasoning:
        reasoning = "No location indicators found in record"
        confidence = "LOW"

    cprint(f"  [RESULT] State={state}, City={city}, Confidence={confidence}", "yellow")

    return LocationResult(
        record_id=record_id,
        crime_location_state=state,
        crime_location_city=city,
        crime_location_zip=None,  # Rarely available
        crime_location_court=court,
        crime_location_pd=pd,
        crime_location_reasoning=reasoning,
        confidence=confidence
    )


def get_record_from_db(db_path: str, record_id: int) -> dict:
    """Fetch a record from SQLite database by ID."""
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM crime_gun_events WHERE id = ?", (record_id,))
    row = cursor.fetchone()
    conn.close()

    if not row:
        raise ValueError(f"Record ID {record_id} not found in database")

    return dict(row)


def update_record_in_db(db_path: str, result: LocationResult) -> bool:
    """Update a record in SQLite database with classification results."""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    cursor.execute("""
        UPDATE crime_gun_events
        SET crime_location_state = ?,
            crime_location_city = ?,
            crime_location_zip = ?,
            crime_location_court = ?,
            crime_location_pd = ?,
            crime_location_reasoning = ?,
            updated_at = CURRENT_TIMESTAMP
        WHERE id = ?
    """, (
        result.crime_location_state,
        result.crime_location_city,
        result.crime_location_zip,
        result.crime_location_court,
        result.crime_location_pd,
        result.crime_location_reasoning,
        result.record_id
    ))

    conn.commit()
    success = cursor.rowcount > 0
    conn.close()

    return success


def main():
    parser = argparse.ArgumentParser(description="Classify crime location for a record")
    parser.add_argument("--record", type=str, help="JSON record to classify")
    parser.add_argument("--db", type=str, help="SQLite database path")
    parser.add_argument("--id", type=int, help="Record ID to classify")
    parser.add_argument("--update", action="store_true", help="Update the database with results")
    parser.add_argument("--output", type=str, help="Output file path (default: stdout)")

    args = parser.parse_args()

    record = None

    if args.record:
        record = json.loads(args.record)
    elif args.db and args.id:
        cprint(f"[DB] Reading record ID {args.id} from {args.db}", "cyan")
        record = get_record_from_db(args.db, args.id)
    else:
        cprint("[ERROR] Must provide --record or --db and --id", "red")
        sys.exit(1)

    result = classify_record(record)
    output = result.model_dump_json(indent=2)

    # Update database if requested
    if args.update and args.db:
        cprint(f"[DB] Updating record ID {result.record_id}...", "yellow")
        if update_record_in_db(args.db, result):
            cprint(f"[DB] Record {result.record_id} updated successfully", "green")
        else:
            cprint(f"[DB] Failed to update record {result.record_id}", "red")

    if args.output:
        with open(args.output, 'w', encoding='utf-8') as f:
            f.write(output)
        cprint(f"[DONE] Result written to {args.output}", "green")
    else:
        print(output)


if __name__ == "__main__":
    main()
