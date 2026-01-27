# Agent Skills Guide - October 2025

**Last Updated:** 2025-10-24
**Status:** Current (reflects October 16, 2025 Skills announcement)

---

## What Are Agent Skills?

Agent Skills are **local filesystem directories** that extend Claude's capabilities with specialized knowledge, reference materials, and executable scripts. Skills are stored in `.claude/skills/` and automatically discovered by the Claude Agent SDK.

**Key Points:**
- ✅ Skills are local directories (not cloud-based)
- ✅ Discovered automatically via `setting_sources=["project"]`
- ✅ Autonomously invoked by Claude based on context
- ✅ No upload, no API key, no configuration needed
- ✅ Shared via Git (version controlled with code)

---

## How Skills Work

### Progressive Loading (3 Tiers)

**Tier 1: Metadata (Startup)**
- Claude scans `.claude/skills/` at startup
- Reads YAML frontmatter (name + description) from each `SKILL.md`
- Loads ~100 tokens per skill
- Enables Claude to know what skills are available

**Tier 2: Instructions (When Relevant)**
- User asks question matching skill description
- Claude reads full `SKILL.md` content (~2-5k tokens)
- Loads skill instructions and guidance
- Claude can now use skill expertise

**Tier 3: Resources (On Demand)**
- Reference files loaded only when needed (0 tokens until read)
- Scripts executed only when needed (0 tokens for code)
- Minimizes token usage through lazy loading

### Example Flow

```
User: "What's the deadline for responding to a motion in federal court?"

1. Startup (Tier 1):
   - Claude loaded civil-procedure skill metadata
   - Knows skill exists for procedural questions

2. Activation (Tier 2):
   - Claude recognizes question matches civil-procedure skill
   - Uses Bash tool to read .claude/skills/civil-procedure/SKILL.md
   - Loads skill instructions

3. Resource Loading (Tier 3):
   - Claude reads references/frcp_rules.md for Rule 12(a)
   - May execute scripts/deadline_calculator.py if needed

4. Response:
   - Cites FRCP 12(a) with full rule text
   - Provides deadline calculation
   - Includes relevant procedural guidance
```

---

## Skill Structure

### Required Structure

```
.claude/skills/
└── your-skill-name/
    ├── SKILL.md           # Required: Entry point with YAML frontmatter
    ├── references/        # Optional: Reference documents
    │   ├── doc1.md
    │   └── doc2.md
    └── scripts/           # Optional: Executable utilities
        └── helper.py
```

### SKILL.md Format

```markdown
---
name: your-skill-name              # Required: lowercase-with-hyphens, 1-64 chars
description: Brief description     # Required: 1-1024 chars, concise summary
license: MIT                       # Optional
allowed-tools: ["Bash", "Read"]   # Optional: Pre-approved tools (Claude Code)
metadata:                          # Optional: Custom key-value pairs
  version: "1.0.0"
  author: "Your Name"
---

# Skill Name

## Purpose

Clear explanation of what this skill does and when to use it.

## Instructions

Detailed instructions for Claude on how to use this skill:
- When to invoke this skill
- How to use reference materials
- How to execute scripts
- How to provide responses

## Reference Materials

Reference documents are in the `references/` directory:
- `references/rules.md` - Complete rule text
- `references/examples.md` - Example cases

## Scripts

Executable utilities in the `scripts/` directory:
- `scripts/calculator.py` - Calculate deadlines

Usage: `python scripts/calculator.py --date "YYYY-MM-DD"`

## Examples

### Example 1: [Scenario]

**User Question:** "Sample question?"

**Response Approach:**
1. Read relevant reference material
2. Execute calculation script if needed
3. Provide answer with citations

### Example 2: [Another Scenario]

...
```

---

## Creating a New Skill

### Step 1: Create Directory Structure

```bash
cd /Users/laurentwiesel/Dev/S-C/s_c_workbench/.claude/skills
mkdir my-new-skill
cd my-new-skill
```

### Step 2: Create SKILL.md

```bash
cat > SKILL.md << 'EOF'
---
name: my-new-skill
description: Expert guidance on [domain] with [specific capabilities]
---

# My New Skill

## Purpose

This skill provides...

## Instructions

When asked about [domain]:
1. Read relevant references
2. Apply domain expertise
3. Provide detailed guidance with citations

## Reference Materials

- `references/core_rules.md` - Primary reference
- `references/examples.md` - Example scenarios

EOF
```

### Step 3: Add References (Optional)

```bash
mkdir references
cat > references/core_rules.md << 'EOF'
# Core Rules

[Your reference content here]
EOF
```

### Step 4: Add Scripts (Optional)

```bash
mkdir scripts
cat > scripts/helper.py << 'EOF'
#!/usr/bin/env python3
"""Helper script for skill."""

def main():
    # Your script logic here
    pass

if __name__ == "__main__":
    main()
EOF

chmod +x scripts/helper.py
```

### Step 5: Test Your Skill

```bash
# Validate structure
python -m src.agents.maite.cli.commands skills validate

# List all skills (should include your new skill)
python -m src.agents.maite.cli.commands skills list

# Show skill details
python -m src.agents.maite.cli.commands skills show my-new-skill
```

### Step 6: Use Your Skill

```bash
# Start Maite (skills loaded automatically)
python src/agents/maite/cli/cli.py

# Ask questions that should trigger your skill
You: "Question matching your skill description..."
```

**That's it!** No upload, no API key, no configuration needed.

---

## Existing Skills

### civil-procedure (Custom)

**Location:** `.claude/skills/civil-procedure/`

**Purpose:** Expert guidance on federal civil procedure rules and litigation deadlines

**Structure:**
- `SKILL.md` - Main entry point
- `references/frcp_rules.md` - Complete FRCP text
- `references/frap_rules.md` - Federal Rules of Appellate Procedure
- `references/supreme_court_rules.md` - Supreme Court Rules
- `scripts/deadline_calculator.py` - Deadline calculations

**Usage:**
```
You: "What is the deadline for responding to a motion?"
Maite: [Autonomously invokes civil-procedure skill]
       [Cites FRCP 12(a) with full rule text]
       [Provides deadline calculation]
```

### Built-In Skills (docx, xlsx, pdf, pptx)

**Location:** `.claude/skills/{docx,xlsx,pdf,pptx}/`

**Purpose:** Document generation capabilities (local copies of Anthropic skills)

**Structure:**
- Each has `SKILL.md` with generation instructions

**Usage:**
- May be invoked autonomously when document generation needed
- Provide guidance on document structure and formatting
- Work with code_execution tool for generation

---

## How Configuration Works

### Required Configuration

Skills are enabled by the `setting_sources` parameter in `ClaudeAgentOptions`:

```python
# src/agents/maite/agent.py
ClaudeAgentOptions(
    setting_sources=["project"],  # ✅ Enables .claude/ directory scanning
    cwd="/path/to/project",       # Project root
    allowed_tools=[...],          # Must include Read, Write, Bash for skills
)
```

### Configuration Files

**Agent Configuration:** `.maite/settings.local.json`
```json
{
  "agent": {
    "setting_sources": ["project"],  // ✅ Required for skills
    ...
  }
}
```

**What This Does:**
- `setting_sources=["project"]` tells SDK to scan `.claude/` directory
- SDK discovers skills in `.claude/skills/`
- Skills automatically available to Claude
- No additional configuration needed

**What You DON'T Need:**
- ❌ No API key for skills (skills are local)
- ❌ No upload commands
- ❌ No beta headers (SDK handles automatically)
- ❌ No `--enable-skills` flags

---

## CLI Commands

### Local Discovery Commands

```bash
# List all skills in .claude/skills/
python -m src.agents.maite.cli.commands skills list

# Show details for specific skill
python -m src.agents.maite.cli.commands skills show <skill-name>

# Validate skill structure
python -m src.agents.maite.cli.commands skills validate
```

**Example Output:**

```bash
$ python -m src.agents.maite.cli.commands skills list

Available Skills:
  1. civil-procedure - Expert guidance on federal civil procedure
  2. docx - Create Word documents
  3. xlsx - Create spreadsheets
  4. pdf - Create PDF documents
  5. pptx - Create presentations

$ python -m src.agents.maite.cli.commands skills show civil-procedure

Skill: civil-procedure
Description: Expert guidance on federal civil procedure rules...
Structure:
  - SKILL.md (entry point)
  - references/frcp_rules.md (147 KB)
  - references/frap_rules.md (82 KB)
  - references/supreme_court_rules.md (41 KB)
  - scripts/deadline_calculator.py (executable)
```

---

## Sharing Skills

### Via Git (Recommended)

Skills are version controlled with your project:

```bash
# Create new skill
mkdir .claude/skills/new-skill
# ... create SKILL.md, references, scripts ...

# Commit to Git
git add .claude/skills/new-skill
git commit -m "Add new-skill for [purpose]"
git push

# Team members get skill automatically
git pull
# Skills now available in their environment
```

### Via File Copy

```bash
# Copy skill between projects
cp -r /path/to/project/.claude/skills/skill-name \
      /path/to/other-project/.claude/skills/
```

### Via GitHub/Package

```bash
# Clone skill repository
git clone https://github.com/org/skills-repo.git

# Copy desired skills
cp -r skills-repo/civil-procedure .claude/skills/
```

---

## Best Practices

### Skill Descriptions

**DO:**
- ✅ Be specific and concise (under 1024 chars)
- ✅ Describe WHEN to use the skill
- ✅ Mention key capabilities
- ✅ Use keywords Claude will recognize

**DON'T:**
- ❌ Don't be too generic ("legal skill")
- ❌ Don't exceed 1024 characters
- ❌ Don't duplicate other skill descriptions

**Example:**
```yaml
# ✅ GOOD
description: Expert guidance on federal civil procedure rules and litigation deadlines. Answers procedural questions using FRCP, FRAP, and Supreme Court Rules with precise citations and full rule text. Specializes in deadline calculations, service requirements, pleadings standards, discovery procedures, motion practice, and appellate procedures.

# ❌ BAD
description: Legal skill for procedure stuff.
```

### Skill Names

**DO:**
- ✅ Use lowercase-with-hyphens
- ✅ Be descriptive: `contract-analysis`, not `contracts`
- ✅ Keep under 64 characters

**DON'T:**
- ❌ Don't use spaces or underscores
- ❌ Don't use generic names: ~~`legal-skill`~~
- ❌ Don't use camelCase or PascalCase

### Reference Materials

**DO:**
- ✅ Include comprehensive reference documents
- ✅ Use clear filenames: `frcp_rules.md`, not `rules.md`
- ✅ Keep references in `references/` directory
- ✅ Reference files don't cost tokens until read

**DON'T:**
- ❌ Don't put everything in SKILL.md (use references/)
- ❌ Don't exceed reasonable file sizes (keep under 1MB per file)
- ❌ Don't include binary files (use markdown, text, code)

### Scripts

**DO:**
- ✅ Make scripts executable: `chmod +x scripts/script.py`
- ✅ Include shebang: `#!/usr/bin/env python3`
- ✅ Document script usage in SKILL.md
- ✅ Scripts cost zero tokens until executed

**DON'T:**
- ❌ Don't require external dependencies without documentation
- ❌ Don't hard-code paths or credentials
- ❌ Don't create scripts that require user input

### Token Optimization

**DO:**
- ✅ Use progressive loading (references loaded on demand)
- ✅ Keep SKILL.md concise (Claude reads this first)
- ✅ Put detailed content in references/
- ✅ Scripts cost zero tokens (only output costs)

**DON'T:**
- ❌ Don't put everything in SKILL.md
- ❌ Don't duplicate content across skills
- ❌ Don't load unnecessary references

---

## Troubleshooting

### Skills Not Working

**Symptom:** Claude doesn't invoke your skill

**Possible Causes:**
1. `setting_sources` not set to `["project"]`
2. Skill description not specific enough
3. SKILL.md missing or malformed
4. Skill name doesn't match directory name

**Debug Steps:**
```bash
# 1. Verify configuration
# Check .maite/settings.local.json has "setting_sources": ["project"]

# 2. Validate skill structure
python -m src.agents.maite.cli.commands skills validate

# 3. Check skill is discovered
python -m src.agents.maite.cli.commands skills list

# 4. Verify SKILL.md frontmatter
cat .claude/skills/your-skill/SKILL.md
# Check YAML frontmatter has name and description

# 5. Check SDK version
pip show claude-agent-sdk
# Should be >= 0.1.4
```

### Skill Not Discovered

**Symptom:** `skills list` doesn't show your skill

**Possible Causes:**
1. Missing SKILL.md file
2. Malformed YAML frontmatter
3. Skill in wrong directory

**Solution:**
```bash
# Verify structure
ls -la .claude/skills/your-skill/
# Should show SKILL.md

# Verify frontmatter
head -10 .claude/skills/your-skill/SKILL.md
# Should show:
# ---
# name: your-skill
# description: ...
# ---
```

### Permission Errors

**Symptom:** Can't read skill files or execute scripts

**Solution:**
```bash
# Fix permissions
chmod -R 755 .claude/skills/
chmod +x .claude/skills/*/scripts/*.py
```

---

## FAQ

**Q: Do I need an API key to use skills?**
A: No. Skills are local filesystem-based. You only need an API key for the Claude API itself (for running Maite), not for skills.

**Q: How do I upload skills?**
A: You don't. Skills are local directories that you create, edit, and share via Git or file copying.

**Q: Can I share skills with my team?**
A: Yes, via Git. Skills in `.claude/skills/` are version controlled with your project.

**Q: Do skills work with Claude Code?**
A: Yes, if Claude Code has `setting_sources=["project"]` configured.

**Q: Can I delete or update skills?**
A: Yes, just edit or delete the directory. Changes take effect on next agent restart.

**Q: Are skills stored on Anthropic servers?**
A: No. Skills are 100% local filesystem-based. Anthropic doesn't store your skills.

**Q: Do skills consume tokens?**
A: Yes, but efficiently:
- Tier 1 (metadata): ~100 tokens per skill at startup
- Tier 2 (instructions): ~2-5k tokens when skill invoked
- Tier 3 (resources): Only when actually read (on demand)

**Q: Can skills execute code?**
A: Yes, if the agent has Bash or code_execution tools enabled. Scripts in `scripts/` can be executed.

**Q: What languages can I use for scripts?**
A: Any language the agent can execute: Python, JavaScript, shell scripts, etc.

**Q: Can I use skills from other projects?**
A: Yes, copy the skill directory or add it as a Git submodule.

---

## Resources

### Official Documentation
- **Skills Announcement:** https://www.anthropic.com/news/skills (Oct 16, 2025)
- **Engineering Deep Dive:** https://www.anthropic.com/engineering/equipping-agents-for-the-real-world-with-agent-skills
- **Claude Docs:** https://docs.claude.com/en/docs/claude-code/skills
- **Agent SDK:** https://github.com/anthropics/claude-agent-sdk-python

### Project Documentation
- **Definitive Guide:** `.docs/guides/SKILLS-GUIDE-OCTOBER-2025.md`
- **Implementation PRD:** `/Users/laurentwiesel/Dev/S-C/s_c_workbench/SKILLS-COMPLETE-IMPLEMENTATION-PRD.md`

### Examples
- **civil-procedure:** `.claude/skills/civil-procedure/` - Custom legal skill
- **Built-in skills:** `.claude/skills/{docx,xlsx,pdf,pptx}/` - Document generation

---

## Summary

Agent Skills are **local filesystem directories** that extend Claude's capabilities:

1. **Create** skills in `.claude/skills/` (directory + SKILL.md)
2. **Configure** `setting_sources=["project"]` (already done for Maite)
3. **Use** automatically - Claude invokes skills based on context
4. **Share** via Git (version control with code)

**No upload, no API key, no configuration beyond `setting_sources`.**

---

**Last Updated:** 2025-10-24
**Version:** 2.0 (reflects October 2025 architecture)
