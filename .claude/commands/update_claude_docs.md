---
name: update-claude-docs
allowed-tools: Read, Write, Edit, Grep, Glob, Task
argument-hint: <reference-docs...>
description: Systematically update all Claude-related documentation to align with reference documents
model: sonnet
---

# Update Claude Documentation

Systematically update all Claude Agent SDK documentation across the project to align with reference documents: $ARGUMENTS

## Documentation Targets

This command updates:

1. **Root README** - `README.md`
2. **Claude Agent Expert** - `.claude/agents/claude-agent-expert.md`
3. **Cursor Rules** - `.cursor/rules/*.mdc` (all claude/skills related)
4. **Claude Agent SDK Skill** - `.claude/~skills/claude-agent-sdk/**`

## Current State

- SDK Version: !grep -r "0\.1\.4" README.md | head -1 || echo "SDK version check"
- Permission Modes: !grep -r "permission_mode" .cursor/rules/\*.mdc | grep -v "^Binary" | head -5
- Skills Status: !ls -la .claude/~skills/claude-agent-sdk/

## Task Workflow

### 1. Read Reference Documents

Read all provided reference documents:

- Extract SDK version requirements
- Identify permission mode specifications (SDK v2.0+)
- Note code execution patterns (SDK 0.1.4+)
- Capture Skills V2.0 API patterns
- Document architecture decisions

### 2. Create Todo List

Track systematic updates:

```
- Analyze reference documents
- Update README.md
- Update .docs/ARCHITECTURE.md
- Update .claude/agents/claude-agent-expert.md
- Update .cursor/rules/claude-agent.mdc
- Update .cursor/rules/claude-agent-tools.mdc
- Update .cursor/rules/skills-claude-agent.mdc
- Update .cursor/rules/memory-claude-agent.mdc
- Update .claude/.dev_skills/claude-agent/SKILL.md
- Update .claude/.dev_skills/claude-agent/references/*.md
- Update .claude/.dev_skills/claude-agent/scripts/*.py
- Verify consistency across all files
```

### 3. Invoke Claude Agent Expert

For each documentation area, use `Task` tool with `@agent-claude-agent-expert`:

**Update Prompt Template:**

```
Update [TARGET] to align with [REFERENCE DOCS]

Requirements:
- SDK 0.1.4+ compliance (code execution fully integrated, no beta headers)
- SDK v2.0+ permission modes ONLY (acceptEdits, bypassPermissions, default, plan)
- INVALID: "manual" and "acceptAll" (must be removed/flagged)
- Skills V2.0 API patterns (upload to Anthropic)
- No bloat - stay focused and concise
- Zero outdated information

Quality: 100% accuracy, consistency, completeness
```

### 4. Critical SDK 0.1.4+ Requirements

Ensure all documentation reflects:

**Permission Modes (SDK v0.1.4+):**

```python
#  VALID
"acceptEdits"       # Production recommended
"bypassPermissions" # Development only
"default"           # Standard behavior
"plan"              # Planning mode

# L INVALID (Runtime errors)
"manual"    # Does NOT exist in SDK v2.0+
"acceptAll" # Does NOT exist in SDK v2.0+
```

**Code Execution (SDK 0.1.4+):**

```python
#  CORRECT
ClaudeAgentOptions(
    allowed_tools=["Read", "Write", "code_execution_20250825"]
    # No beta headers - causes --betas error
)

# L WRONG
extra_args={"betas": ["code-execution-2025-08-25"]}  # Don't do this
```

**Skills (V2.0 API):**

- Upload to Anthropic API (one-time)
- Zero per-session token cost
- No local file injection

### 5. Quality Standards

Every update must have:

-  SDK 0.1.4+ compliance verified
-  No deprecated patterns
-  Executable code examples
-  Consistent terminology
-  Explicit warnings for common errors

### 6. Verification

After all updates:

- Cross-file consistency check
- Pattern validation
- Code example verification
- Terminology alignment

### 7. Generate Report

Provide comprehensive update summary:

```markdown
## Documentation Update Report

### Files Updated

[List with line counts and key changes]

### Critical Fixes

- SDK compliance issues corrected
- Permission mode corrections
- Deprecated pattern removals

### Quality Metrics

- Accuracy: [100%]
- Consistency: [100%]
- Completeness: [100%]

### Git Status

!git status --porcelain
```

## Important Notes

- Use `@agent-claude-agent-expert` for complex multi-file updates
- Update systematically - don't skip verification steps
- Mark todos as completed after each file update
- Test code examples where possible
- Review git diff before committing

## Success Criteria

- All documentation targets updated
- Zero outdated SDK patterns remain
- Cross-file consistency verified
- Comprehensive report generated
- All todos marked complete

To be clear: Avoid document bloat and only update the files and parts that are directly related to the reference documents.
