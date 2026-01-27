---
name: sessions
allowed-tools: Bash
description: List recent 10 Maite sessions with fork relationships
---

Execute the following command to retrieve the 10 most recent Maite sessions:

!`python -m src.agents.maite.cli.commands list --limit 10 --show-forks`

After executing the command, present the results to the user as a concise numbered list showing:
- Session ID (first 8 characters)
- Session title
- Cost
- Status
- Creation timestamp

Format example:
1. **abc12345** - "Session title" - $0.0809 - completed - Oct 28, 03:14

The full command output displays:
- Session IDs and creation timestamps
- Matter associations
- Session status (active, completed, error)
- Fork relationships between sessions
- Cost information per session
