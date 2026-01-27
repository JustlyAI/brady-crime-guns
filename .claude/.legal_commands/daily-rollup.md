---
name: daily-rollup
allowed-tools: Bash, Read, Write
argument-hint: [date] [matter-id]
description: Generate daily session summary for current or specified matter
---

You are tasked with generating a daily rollup summarizing all Maite sessions for a specific matter and date.

## Overview

The daily rollup creates a comprehensive memory artifact that captures:
- All sessions completed on the target date
- Total cost and token usage
- Key research activities and findings
- Important context for future sessions

## Steps

### 1. Determine Parameters

**Date**:
- If provided via `$1`, parse that date
- Otherwise, use today's date

**Matter ID**:
- If provided via `$2`, use that matter ID
- Otherwise, read from `.maite/settings.local.json` (look for `current_matter_id` or similar field)
- If not found, prompt the user

### 2. Create the Rollup

Write and execute a Python script that uses the simplified `DailyRollupService.create_for_matter()` API:

```python
import asyncio
from datetime import datetime
from src.agents.maite.services.rollup_service import DailyRollupService

async def create_rollup(matter_id: str = None, date: datetime = None):
    """
    Create daily rollup using simplified API.

    DailyRollupService.create_for_matter() handles all initialization:
    - Loads Config automatically
    - Creates LocalMemoryHandler
    - Initializes SessionManager (if PostgreSQL mode)
    - Creates MaiteMemoryService
    - Generates and stores rollup
    """
    result = await DailyRollupService.create_for_matter(
        matter_id=matter_id,  # None = uses MATTER_ID from config
        date=date             # None = uses today
    )

    if result:
        print(f"\n✅ Daily Rollup Generated")
        print(f"Date: {result['date']}")
        print(f"Sessions: {result['session_count']}")
        print(f"File: {result['filename']}")
        print(f"\nContent preview:")
        print(result['content'][:500] + "..." if len(result['content']) > 500 else result['content'])
    else:
        print("ℹ️  No sessions found for the specified date")

    return result

# Parse arguments
# $1 = date (optional, format: YYYY-MM-DD)
# $2 = matter_id (optional)

date_arg = "$1" if "$1" else None
matter_id_arg = "$2" if "$2" else None

# Convert date string to datetime if provided
target_date = None
if date_arg and date_arg != "$1":
    target_date = datetime.strptime(date_arg, "%Y-%m-%d")

# Run it
result = asyncio.run(create_rollup(matter_id=matter_id_arg, date=target_date))
```

**Key Improvements**:
- Single line API: `DailyRollupService.create_for_matter()`
- Automatic initialization of all dependencies
- Automatic storage mode detection (PostgreSQL vs JSON)
- Automatic matter ID detection from config
- Automatic date defaulting to today

### 3. Display the Summary

After creating the rollup, show the user:
- Number of sessions included
- Total cost for the day
- Key activities summary
- Where the rollup was saved (in the memory system)

## Example Output

```
Daily Rollup Generated
======================
Date: 2024-10-27
Matter: Smith v. Jones (case-123)

Sessions Processed: 8
Total Cost: $5.67
Total Tokens: 45,234

Key Activities:
- Researched statute of limitations for fraud claims
- Analyzed recent case precedents in 9th Circuit
- Drafted motion to dismiss arguments
- Reviewed discovery documents

Rollup saved to: memory/daily/2024-10-27.md
```

## Notes

- **Simplified API**: `DailyRollupService.create_for_matter()` handles all initialization boilerplate
- **Automatic detection**: Storage mode (PostgreSQL/JSON), matter ID, and date all auto-detected from config
- **Dual mode support**: Works in both PostgreSQL and JSON storage modes
  - PostgreSQL provides richer session data (messages, tool usage)
  - JSON mode provides session metadata (title, cost, status)
- **Memory storage**: Rollups saved to `.maite/memories/matters/{matter_id}/daily/{date}.md`
- **Retroactive**: Can be run for any past date, not just today
- **Clean initialization**: All database connections are properly initialized and closed

## Technical Details

The refactored service eliminates the initialization chain:
- Old: `Config → LocalMemoryHandler → SessionManager → MaiteMemoryService → DailyRollupService`
- New: `DailyRollupService.create_for_matter()` (one line!)

This makes the slash command much more reliable and easier to use.
