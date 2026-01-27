# Legal Commands Catalog

Custom slash commands for the S-C Workbench project, designed to streamline Maite agent workflows for litigation support.

---

## Overview

These commands eliminate context switching between the interactive Maite CLI and command-line management tools. All commands work with the existing codebase infrastructure without adding new functionality.

**Location:** `.claude/commands/`
**Total Commands:** 4
**Implementation Date:** October 28, 2025

---

## Commands

### 1. `/sessions` - Session Management

**File:** `sessions.md`
**Type:** Bash Wrapper (Path A)
**Impact:** Highest

**Purpose:** List the 10 most recent Maite sessions with fork relationships

**Command:**

```bash
python -m src.agents.maite.cli.commands list --limit 10 --show-forks
```

**Output:**

- Session IDs with timestamps
- Matter associations
- Status (active, completed, error)
- Fork relationships
- Cost per session

**Usage:**

```
You: /sessions
```

**Why It Matters:** Most frequently used operation. Eliminates the need to exit the conversation and run CLI commands separately.

---

### 2. `/maite-cost` - Quick Cost Check

**File:** `maite-cost.md`
**Type:** Agentic + Bash (Path B)
**Impact:** High

**Purpose:** Display cost summary for current or specified matter

**Arguments:** `[matter-id]` (optional)

**Approach:**

1. Auto-loads matter ID from `.maite/settings.local.json` if not provided
2. Executes stats query via CLI
3. Claude interprets and formats results

**Output:**

- Total sessions
- Total cost (USD)
- Average cost per session
- Today's cost
- Cost breakdown by date/session

**Usage:**

```
You: /maite-cost                    # Current matter
You: /maite-cost case-123          # Specific matter
```

**Why It Matters:** Instant billing visibility without interrupting research workflow. Critical for matter budgeting.

---

### 3. `/daily-rollup` - Daily Summary

**File:** `daily-rollup.md`
**Type:** Fully Agentic (Path C)
**Impact:** Medium-High

**Purpose:** Generate comprehensive daily session summary for archival and review

**Arguments:** `[date] [matter-id]` (both optional)

**Approach:**

1. Claude writes Python script using `DailyRollupService.create_for_matter()`
2. Auto-detects storage mode (PostgreSQL/JSON)
3. Auto-loads matter ID from config
4. Generates and stores memory artifact

**Output:**

- Session count for the day
- Total cost and token usage
- Key research activities
- Tools used per session
- Saved to: `.maite/memories/matters/{matter_id}/daily/{date}.md`

**Usage:**

```
You: /daily-rollup                           # Today, current matter
You: /daily-rollup 2025-10-27               # Specific date
You: /daily-rollup 2025-10-27 case-456      # Specific date and matter
```

**Why It Matters:** Natural end-of-day workflow. Creates searchable memory artifacts without manual summarization.

**Technical Note:** Uses refactored `DailyRollupService.create_for_matter()` API (one-line initialization) to avoid complex dependency chain.

---

### 4. `/maite-skills` - Skills Discovery

**File:** `maite-skills.md`
**Type:** Bash Wrapper (Path A)
**Impact:** Medium

**Purpose:** List all available Maite skills with descriptions

**Command:**

```bash
python -m src.agents.maite.cli.commands skills list --verbose
```

**Output:**

- Skill names
- Descriptions
- Capabilities
- Use cases
- Installation status

**Usage:**

```
You: /maite-skills
```

**Why It Matters:** Quick reference for available capabilities without leaving the conversation. Helps users discover what Maite can do.

---

## Implementation Patterns

### Path A: Bash Wrapper

- **Commands:** `/sessions`, `/maite-skills`
- **Pattern:** Direct CLI command execution using `!` prefix
- **Pros:** Simple, reliable, no Python scripting needed
- **Cons:** Limited output formatting

### Path B: Agentic + Bash

- **Commands:** `/maite-cost`
- **Pattern:** Claude executes bash, interprets results, formats output
- **Pros:** Flexible output, can aggregate multiple data sources
- **Cons:** Slightly more complex than pure bash

### Path C: Fully Agentic

- **Commands:** `/daily-rollup`
- **Pattern:** Claude writes and executes Python using project services
- **Pros:** Maximum flexibility, can use full project infrastructure
- **Cons:** Requires clear prompt with initialization examples

---

## Storage Mode Compatibility

All commands work in both storage modes:

- **PostgreSQL Mode:** Full session data (messages, tool usage, rich metadata)
- **JSON Mode:** Session metadata only (title, cost, status, basic info)

PostgreSQL mode provides richer data for rollups and cost analysis.

---

## Related Infrastructure

### Services

- `DailyRollupService` (`src/agents/maite/services/rollup_service.py`)
- `MaiteMemoryService` (`src/agents/maite/services/memory_service.py`)
- `SessionManager` (`src/shared/infrastructure/session_manager.py`)

### CLI Commands

- `python -m src.agents.maite.cli.commands list` - Session listing
- `python -m src.agents.maite.cli.commands stats` - Statistics
- `python -m src.agents.maite.cli.commands skills` - Skills management

### Configuration

- `.maite/settings.local.json` - Matter ID, agent settings
- `.env` - Storage mode, database URL

---

## Maintenance Notes

- All commands use existing CLI infrastructure
- Commands are stateless (no persistent state between invocations)
- Updates to underlying services automatically benefit slash commands
- New CLI commands in `commands.py` can be easily wrapped as slash commands

---

## See Also

- **Plan:** `.plans/custom-command-plan.md` - Original implementation plan
- **Refactor:** `.docs/rollup-service-refactor-report.md` - Daily rollup improvements
- **CLI Docs:** `src/agents/maite/cli/README.md` - Underlying CLI documentation
- **Slash Commands:** `.docs/claude-agent/claude-slash-commands.md` - Format specification
