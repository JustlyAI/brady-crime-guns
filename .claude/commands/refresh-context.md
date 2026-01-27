---
name: refresh-context
allowed-tools: Bash, Read
argument-hint: [location]
description: Update current context YAML (datetime, day, location, skills, tools)
---

Update the YAML frontmatter in `current_context.md` with current datetime (ISO 8601 with timezone), day, IP-detected location, and auto-discovered skills/tools.

## Steps

1. **Execute Update Script**:
   - If location provided via `$ARGUMENTS`, use it as manual override
   - Otherwise, auto-detect location via IP geolocation

!`python src/shared/scripts/update_context.py $ARGUMENTS`

2. **Verification**:
   - The script will display the updated YAML frontmatter
   - Confirm the current_datetime, day_of_week, and location are correct

## What Gets Updated

**Always:**
- `current_datetime` → Current timestamp in ISO 8601 format with timezone (e.g., `2025-10-28T09:15:30+09:00`)
- `day_of_week` → Current day name (Monday, Tuesday, etc.)
- `location` → Auto-detected via IP geolocation (fallback: "Unknown"), or manual override if provided
- `available-skills` → Auto-discovered list of skills from `.claude/skills/`
- `available-tools` → Auto-discovered list of allowed tools from `.maite/settings.local.json`

## Usage Examples

```bash
# Auto-detect location via IP geolocation
/refresh-context

# Manual location override
/refresh-context London, UK
/refresh-context New York, NY
/refresh-context Paris, France
```

## Notes

- Script execution: ~150ms (with skills/tools discovery) + ~1s (IP geolocation)
- Preserves all markdown body content unchanged
- Updates only YAML frontmatter fields
- Location auto-detected via `https://ipapi.co/json/` (1 second timeout)
- On IP detection failure, sets `location: "Unknown"` (script continues gracefully)
- Skills discovered via `SkillsService`
- Tools loaded from config hierarchy (.maite/settings.local.json → defaults)
- File location: `.maite/memories/current_context.md`
