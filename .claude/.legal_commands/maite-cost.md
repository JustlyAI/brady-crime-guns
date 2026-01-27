---
name: maite-cost
allowed-tools: Bash, Read
argument-hint: [matter-id]
description: Show cost summary for current or specified matter
---

You are tasked with displaying a cost summary for Maite sessions.

## Steps

1. **Determine Matter ID**:
   - If the user provides a matter ID via `$ARGUMENTS`, use that
   - Otherwise, try to load the current matter_id from `.maite/settings.local.json`
   - If no matter ID is found, prompt the user to provide one

2. **Query Session Costs**:
   - Use the Bash tool to run: `python -m src.agents.maite.cli.commands stats --matter <matter-id>`
   - This will query the SessionManager and display:
     - Total number of sessions
     - Total cost across all sessions
     - Average cost per session
     - Today's cost
     - Cost breakdown by status (if available)

3. **Display Results**:
   - Present the cost information in a clear, formatted table
   - Highlight any unusually high costs or anomalies
   - Include the date range of the sessions analyzed

## Example Output Format

```
Cost Summary for Matter: [matter-id]
=====================================
Total Sessions: 42
Total Cost: $15.67
Average Cost/Session: $0.37
Today's Cost: $2.45

Sessions by Status:
- Completed: 38 ($14.23)
- Active: 2 ($0.89)
- Error: 2 ($0.55)
```

## Notes

- Requires PostgreSQL mode (SESSION_STORAGE_MODE=postgres)
- Costs are based on token usage tracked in the session metadata
