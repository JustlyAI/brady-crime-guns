---
name: implementation-summary
aliases:
  - impl-summary
  - summary
allowed-tools: Bash, Read, Write, Glob, Grep
argument-hint: [feature-name] [--archive]
description: Generate comprehensive implementation summary for features developed in a session
model: sonnet
---

# Implementation Summary Generator

Generate a comprehensive markdown implementation summary for features developed in the current session.

## Parameters

- **feature-name**: Optional short feature identifier (e.g., "model-selection", "eval-tracking")
  - If not provided, auto-detect from git changes and prompt for confirmation
- **--archive**: Optional flag to archive the summary to .docs/archive/ after generation

## Context Analysis

First, analyze the current session work to understand what was implemented:

### 1. Git Analysis

```bash
git status --porcelain
git diff HEAD --stat
git log --oneline -5
git diff HEAD
```

### 2. Branch Context

```bash
git branch --show-current
git log main..HEAD --oneline
```

### 3. Recent Test Runs

Check for test artifacts or output:
```bash
find tests/ -name "test_*.py" -type f 2>/dev/null | head -10
```

## Document Generation

Create a comprehensive markdown document at:
`implementation-summary-{feature}_{YYYY-MM-DD}.md`

### Document Structure

Use this exact structure (based on project examples in .docs/archive/):

```markdown
# {Feature Name} Implementation Summary

## Overview

[1-2 paragraph summary of feature and its purpose in the S-C Workbench litigation AI context]

## Implementation Date

{YYYY-MM-DD}

## Feature Description

[Detailed description covering:
- What the feature does
- Why it was needed
- How it fits into the broader system
- Key capabilities added]

## Files Modified

[For EACH modified file:]

### {N}. {Component Name}

**File**: `path/to/file.py`

**Changes**:
1. [Change 1 with line numbers] (lines XX-YY):
   ```python
   # Code snippet showing the change
   ```

2. [Change 2 with line numbers] (lines XX-YY):
   ```python
   # Code snippet
   ```

**Rationale**: [Why these changes were made, design considerations]

---

## Architecture Decisions

### 1. {Decision Title}

[Explanation of architectural choice]
- **Why**: [Reasoning]
- **Alternatives considered**: [What else was considered]
- **Trade-offs**: [Pros/cons]

### 2. {Decision Title}

[Continue for each major decision]

### Backward Compatibility

[Document compatibility guarantees:]
- ✅ [What remains compatible]
- ⚠️ [Any breaking changes]
- 🔄 [Migration paths]

### Settings Precedence

[If configuration involved, document precedence order]

---

## Testing

### Manual Testing Performed

[Document each test scenario:]

1. **{Test Scenario}**:
   ```bash
   # Commands run
   ```
   **Result**: [What happened]

2. **{Test Scenario}**:
   [Continue...]

### Test Results

[Summary table:]
- ✅ [What passed]
- ✅ [What passed]
- ⚠️ [Any issues found]

### Automated Tests

[If automated tests were written:]
- Location: `tests/test_*.py`
- Coverage: [Areas covered]
- Execution: `pytest tests/test_feature.py`

---

## Usage Examples

### Example 1: {Use Case Title}

```python
# Code example showing usage
```

**Use case**: [When to use this]

### Example 2: {Use Case Title}

```bash
# CLI example
```

**Use case**: [When to use this]

### Example 3: {Use Case Title}

[Continue with executable examples]

---

## Configuration Reference

### Valid Configuration Values

[Document all configuration options:]

```json
{
  "setting_name": "value",
  "description": "What this does"
}
```

### Configuration Location

Primary configuration file:
```
/Users/laurentwiesel/Dev/S-C/s_c_workbench/.maite/settings.local.json
```

[Document any environment variables]

---

## Benefits

### 1. {Benefit Category}

[Concrete benefits:]
- **{Specific benefit}**: [Quantified impact if possible]
- **{Specific benefit}**: [Quantified impact]

### 2. {Benefit Category}

[Continue...]

---

## Edge Cases Handled

### 1. {Edge Case}

**Scenario**: [Description]
**Behavior**: [How it's handled]
**Test**: ✅ [Verification status]

### 2. {Edge Case}

[Continue for all edge cases]

---

## Migration Notes

### For Existing Users

[Document migration requirements:]

**Breaking changes**: [Yes/No]
- [List any breaking changes]

**Upgrade steps**:
1. [Step 1]
2. [Step 2]

### Backward Compatibility

✅ **Maintained**:
- [What still works]

⚠️ **Changed**:
- [What changed and how to adapt]

---

## Future Enhancements

### Potential Additions

1. **{Enhancement Title}**
   ```python
   # Code sketch if relevant
   ```
   **Use case**: [When this would be valuable]

2. **{Enhancement Title}**
   [Continue...]

---

## Related Documentation

[Link to related docs:]
- Project README: `README.md`
- Configuration docs: `.docs/...`
- Agent SDK docs: `.docs/claude-agent/...`
- Cursor rules: `.cursor/rules/...`
- [Any relevant external docs]

---

## Notes

### {Special Consideration}

[Document any special notes, gotchas, or important context]

### Session Metadata

[Document metadata captured:]
- Model used: [claude-sonnet-4-5 or other]
- Session tracking: [How it's tracked]
- [Other relevant metadata]

---

## Conclusion

[2-3 paragraph summary covering:]

**Key Achievements**:
- ✅ [Achievement 1]
- ✅ [Achievement 2]
- ✅ [Achievement 3]

**Production Readiness**: [Assessment]

[Final statement on value delivered and integration with S-C Workbench vision]
```

## Quality Standards

When generating the summary, ensure:

1. **Specific Line Numbers**: Always include actual line numbers from git diff
2. **Executable Code Examples**: All examples must be runnable
3. **Concrete Benefits**: Quantify benefits where possible (performance, cost, time)
4. **Clear Rationale**: Explain *why* not just *what*
5. **Complete Context**: Reference project structure, CLAUDE.md guidelines, SDK patterns
6. **Production Assessment**: Honest evaluation of readiness

## Feature Name Detection

If feature-name not provided:

1. Analyze git changes to identify the main feature
2. Suggest a feature name based on:
   - Modified file patterns
   - Commit messages
   - Scope of changes
3. Prompt user: "Detected feature: '{suggested-name}'. Use this name? [Y/n]"
4. Use confirmed name for filename

## Archive Handling

If `--archive` flag present:

1. Generate summary as usual
2. After generation, ask: "Archive summary to .docs/archive/? [Y/n]"
3. If yes:
   ```bash
   mv implementation-summary-{feature}_{date}.md .docs/archive/
   ```
4. Confirm: "Summary archived to .docs/archive/implementation-summary-{feature}_{date}.md"

## Example Usage

```bash
# With explicit feature name
/implementation-summary model-selection
# Creates: implementation-summary-model-selection_2025-11-04.md

# Auto-detect feature
/implementation-summary
# Prompts: "Detected feature: 'eval-tracking'. Use this name? [Y/n]"

# With archive flag
/impl-summary eval-tracking --archive
# Creates summary, then archives to .docs/archive/

# Using alias
/summary context-greeting
```

## Implementation Notes

- **Reference Pattern Files**: Look at existing summaries in .docs/archive/ for tone and structure
- **Project Context**: Incorporate S-C Workbench litigation focus and SDK patterns from CLAUDE.md
- **Conciseness**: Be comprehensive but concise (per project guidelines)
- **UTF-8 Encoding**: All file operations use encoding="utf-8"
- **Date Format**: Use YYYY-MM-DD consistently

## Success Criteria

A successful implementation summary includes:

- ✅ All files modified with specific line numbers
- ✅ Clear architecture decisions with rationale
- ✅ Executable usage examples
- ✅ Comprehensive testing documentation
- ✅ Edge cases and how they're handled
- ✅ Migration notes and backward compatibility
- ✅ Future enhancement suggestions
- ✅ Production readiness assessment
- ✅ Links to related documentation

The goal is to create a reference document that someone could use 6 months from now to understand exactly what was implemented, why, and how to use it.
