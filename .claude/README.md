# `.claude/` Directory - Shared SDK Features

This directory contains Claude Agent SDK features shared between **two agents** operating in this codebase:

1. **Claude Code** (development agent) - Helps write/debug code
2. **Maite** (litigation agent) - The product being developed

## Two-Layer Configuration Architecture

### The Challenge

**Question:** How can two different agents share `.claude/` without interfering with each other?

**Answer:** Use `setting_sources=["project"]` to load SDK features from `.claude/`, then **explicitly override** agent-specific settings.

### How It Works

**Layer 1: SDK Features (`.claude/` - shared)**
```python
# Both agents use:
setting_sources=["project"]  # Loads from .claude/

# SDK automatically loads:
# - .claude/CLAUDE.md (base system prompt)
# - .claude/agents/* (subagents)
# - .claude/skills/* (skills)
# - .claude/commands/* (slash commands)
# - .claude/settings.json (hooks, if configured)
```

**Layer 2: Agent-Specific Overrides**

**Claude Code:**
- Uses `.claude/CLAUDE.md` as system prompt
- Uses `.claude/settings.local.json` for runtime config

**Maite:**
- **Explicitly overrides** system prompt with `.maite/MAITE.md`
- Uses `.maite/settings.local.json` for runtime config
- Gets all SDK features from `.claude/` automatically

**Key Insight:** Explicit `system_prompt` parameter in `ClaudeAgentOptions` takes precedence over `setting_sources`.

```python
# Maite's configuration
ClaudeAgentOptions(
    setting_sources=["project"],           # ✅ Load SDK features from .claude/
    system_prompt=load(".maite/MAITE.md"), # ✅ Override .claude/CLAUDE.md
    allowed_tools=[...],                   # From .maite/settings.local.json
    permission_mode="bypassPermissions",   # From .maite/settings.local.json
)

# Result: Maite gets .claude/ features + .maite/ identity
```

---

## Directory Structure

```
.claude/
├── README.md                         # This file
├── CLAUDE.md                         # Development context (Claude Code uses)
├── settings.local.json               # Claude Code runtime config
│
├── agents/                           # Subagents (auto-loaded)
│   ├── legal-document-editor.md      # Maite subagent (production)
│   └── dev_claude_sdk_expert.md      # Dev subagent (dev-only)
│
├── skills/                           # Skills (auto-loaded)
│   ├── civil-procedure/              # Maite skill (production)
│   └── dev_claude-agent/             # Dev skill (dev-only)
│
├── commands/                         # Slash commands (auto-loaded)
│   ├── prd.md                        # Shared command
│   ├── cleanup.md                    # Shared command
│   ├── code-review.md                # Dev command
│   └── update_claude_docs.md         # Dev command
│
└── ~dev_commands/                    # Dev-only commands
    ├── aw.md
    ├── debug.md
    └── system-health.md
```

### Naming Conventions

**Development-only content:**
- Prefix agents: `dev_*` (e.g., `dev_claude_sdk_expert.md`)
- Prefix skills: `dev_*` (e.g., `dev_claude-agent/`)
- Dev commands: `~dev_commands/` folder

**Production content (Maite):**
- No prefix (e.g., `legal-document-editor.md`)
- Clear descriptive names (e.g., `civil-procedure/`)

**Shared content:**
- Use descriptive names
- Works for both agents

---

## What This Directory Provides

### 1. Automatic Subagent Loading

**How to add a subagent:**
```bash
# 1. Create agent markdown file
cat > .claude/agents/contract-analyzer.md << 'EOF'
# Contract Analyzer Agent

Specialized agent for contract review and analysis.

## Capabilities
- Contract clause analysis
- Risk identification
- Compliance checking
EOF

# 2. Done! SDK loads it automatically
# No code changes required
```

**Usage:**
- Agent is available immediately to any agent with `setting_sources=["project"]`
- Invoke via agent system (implementation in SDK)

### 2. Automatic Skills Loading

**How to add a skill:**
```bash
# 1. Create skill directory
mkdir -p .claude/skills/evidence-rules

# 2. Add SKILL.md
cat > .claude/skills/evidence-rules/SKILL.md << 'EOF'
# Federal Rules of Evidence Skill

Provides analysis and guidance on Federal Rules of Evidence.

## Capabilities
- Rule interpretation
- Objection strategies
- Evidence admissibility
EOF

# 3. Add reference materials
mkdir .claude/skills/evidence-rules/references/
# Add reference documents...

# 4. Done! SDK loads it automatically
```

**Benefits:**
- ✅ Zero configuration
- ✅ Instant availability
- ✅ No custom loader code
- ✅ Shared across both agents

### 3. Slash Commands

**How to add a command:**
```bash
# 1. Create command markdown file
cat > .claude/commands/cite-check.md << 'EOF'
# Cite Check Command

Verify legal citations for accuracy and proper formatting.

## Usage
/cite-check <citation>

## Implementation
[Command implementation details]
EOF

# 2. Done! Available as /cite-check
```

**Commands automatically available:**
- `/prd` - Generate product requirements document
- `/cleanup` - Clean up code files
- `/code-review` - Review code changes
- `/update_claude_docs` - Update SDK documentation
- Custom commands in `~dev_commands/` for development

### 4. Hooks (Optional)

Configure in `.claude/settings.json`:
```json
{
  "hooks": {
    "PreToolUse": ["validate_legal_ethics"],
    "PostToolUse": ["track_citations"]
  }
}
```

---

## Adding Features (The Easy Way)

### Before `.claude/` Integration

**To add a skill (old way):**
1. Create skill folder in `.maite/skills/`
2. Write custom discovery code in Python
3. Parse SKILL.md manually
4. Integrate with agent initialization
5. Test discovery mechanism
6. Upload to Skills API

**Time:** 2-3 hours of coding

### After `.claude/` Integration

**To add a skill (new way):**
1. Drop skill folder in `.claude/skills/`
2. Done.

**Time:** 1 minute

### Development Velocity Comparison

| Feature      | Before (custom code) | After (.claude/) | Speed Increase |
|--------------|---------------------|------------------|----------------|
| Add skill    | ~2-3 hours          | ~1 minute        | ~100x faster   |
| Add subagent | ~2-3 hours          | ~1 minute        | ~100x faster   |
| Add command  | Not feasible        | ~1 minute        | ∞ faster       |

---

## For Maite: How to Use `.claude/` Features

### Configuration Required

In `.maite/settings.local.json`:
```json
{
  "agent": {
    "setting_sources": ["project"]  // ✅ Enable .claude/ loading
  }
}
```

In `src/agents/maite/agent.py`:
```python
# Load system prompt explicitly (overrides .claude/CLAUDE.md)
system_prompt = self._load_system_prompt()  # Loads .maite/MAITE.md

# Create options
ClaudeAgentOptions(
    setting_sources=["project"],      # Load .claude/ features
    system_prompt=system_prompt,      # Override with Maite prompt
    allowed_tools=[...],              # From .maite/settings.local.json
)
```

### What Maite Gets Automatically

From `.claude/`:
- ✅ All subagents in `agents/` (legal-document-editor, etc.)
- ✅ All skills in `skills/` (civil-procedure, etc.)
- ✅ All slash commands in `commands/`
- ✅ Any configured hooks

While maintaining:
- ✅ Separate system prompt (`.maite/MAITE.md`)
- ✅ Separate runtime config (`.maite/settings.local.json`)
- ✅ Distinct identity and behavior

---

## For Claude Code: Using `.claude/`

### Configuration

Claude Code uses `.claude/` as the standard SDK configuration directory.

In `.claude/settings.local.json`:
```json
{
  "agent": {
    "setting_sources": ["project"]  // Load from .claude/
  }
}
```

### What Claude Code Uses

- ✅ `.claude/CLAUDE.md` - Development context (not overridden)
- ✅ `.claude/agents/dev_*` - Development subagents
- ✅ `.claude/skills/dev_*` - Development skills
- ✅ `.claude/commands/` - All commands (including dev-only)

---

## Distribution Strategy

When packaging Maite for production distribution:

```bash
#!/bin/bash
# scripts/clean_for_distribution.sh

# Remove development-only content
rm -rf .claude/agents/dev_*
rm -rf .claude/skills/dev_*
rm -rf .claude/~dev_commands/
rm -f .claude/commands/code-review.md
rm -f .claude/commands/update_claude_docs.md

# Remove development tools
rm -rf .cursor/
rm -rf .plans/

# Keep only production content
echo "✅ Distribution-ready .claude/ directory"
ls -la .claude/
```

**Result:** Clean `.claude/` with only Maite-relevant content (legal-document-editor, civil-procedure, etc.)

---

## Benefits of This Architecture

### 1. Development Velocity

**Adding features is trivial:**
- Drop folder in `.claude/skills/` → Instant skill
- Drop file in `.claude/agents/` → Instant subagent
- Drop file in `.claude/commands/` → Instant command

**No code changes needed** - SDK handles everything.

### 2. Shared Infrastructure

Both agents benefit from shared resources:
- Legal research skills useful for development documentation
- Code review agents useful for Maite's own development
- Shared commands reduce duplication

### 3. Future-Proof

When Anthropic adds new SDK features:
- ✅ Both agents get them automatically
- ✅ Zero migration work
- ✅ No custom code to update

### 4. Clean Separation

Despite sharing `.claude/`:
- ✅ Each agent has distinct identity (separate system prompts)
- ✅ Each agent has separate runtime config
- ✅ Clear naming conventions prevent confusion

---

## Common Questions

### Q: Won't Claude Code and Maite conflict?

**A:** No. Each agent:
- Uses different system prompts (`.claude/CLAUDE.md` vs `.maite/MAITE.md`)
- Has different runtime configs (`.claude/settings.local.json` vs `.maite/settings.local.json`)
- Interprets shared features through its own context

### Q: Can I use different skills for each agent?

**A:** Yes. Use naming conventions:
- `dev_*` skills → Development only (Claude Code)
- No prefix → Production (Maite) or shared

Both agents see all skills, but naming makes purpose clear.

### Q: What if I want Maite to NOT use `.claude/`?

**A:** Set `setting_sources=[]` in `.maite/settings.local.json`. This disables automatic SDK feature loading, but you lose subagents, skills, commands.

**Not recommended** - you'd need custom code for every SDK feature.

### Q: How does system prompt override work?

**A:** SDK loads `.claude/CLAUDE.md` via `setting_sources`, but explicit `system_prompt` parameter takes precedence:

```python
# This explicit parameter wins
ClaudeAgentOptions(
    setting_sources=["project"],          # Loads .claude/CLAUDE.md
    system_prompt=load(".maite/MAITE.md") # ✅ Overrides it
)
```

Result: Maite uses `.maite/MAITE.md`, not `.claude/CLAUDE.md`.

---

## Technical Details

### Configuration Precedence Chain

**1. Explicit Parameters** (highest priority)
```python
ClaudeAgentOptions(
    system_prompt=custom_prompt,  # ✅ Overrides everything
    allowed_tools=custom_tools,    # ✅ Overrides everything
)
```

**2. Manual Configuration** (medium priority)
```python
config = load_json('.maite/settings.local.json')
# Used for: permission_mode, max_turns, etc.
```

**3. Setting Sources** (lowest priority)
```python
setting_sources=["project"]  # Loads .claude/
# Overridden by: Explicit parameters
```

### SDK Feature Loading

When `setting_sources=["project"]`:
```
SDK loads from .claude/:
├── CLAUDE.md → system_prompt (if not explicitly set)
├── agents/*.md → available subagents
├── skills/*/ → available skills
├── commands/*.md → slash commands
└── settings.json → hooks configuration
```

### Path Resolution

SDK looks for `.claude/` at project root:
```
project_root/
└── .claude/
    ├── CLAUDE.md
    ├── agents/
    ├── skills/
    └── commands/
```

No configuration needed - SDK finds it automatically via `setting_sources=["project"]`.

---

## Related Documentation

- **Main README**: `../README.md` - Project overview
- **Maite Config Guide**: `../.maite/README.md` - Maite-specific configuration
- **Architecture Reports**:
  - `../.docs/checkpoints/Checkpoint-Maite-Settings-Refactor_2025-10-23.md` - Settings refactor
  - `../.docs/checkpoints/Checkpoint-Claude-Integration_2025-10-23.md` - `.claude/` integration (this architecture)

---

**Summary:** `.claude/` is the shared SDK feature directory. Both agents use it via `setting_sources=["project"]` while maintaining separate identities through explicit system prompts and runtime configs. This enables automatic feature loading with zero code changes.
