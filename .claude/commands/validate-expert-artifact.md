---
name: validate-expert-artifact
allowed-tools: Read, Grep, Glob, Task
argument-hint: <file-path> [--thorough]
description: Validate PRD or artifact contents against source expert reports using research skill and exhibit ferret agent
model: sonnet
---

# Expert Artifact Validation

Validate the expert report artifact: $ARGUMENTS

## Purpose

Systematically verify that all claims, figures, citations, and exhibit references in the specified PRD or artifact are accurate and supported by the source expert reports.

## Validation Process

### Step 1: Load and Parse the Artifact

Read the specified file and extract:
- **Numerical claims** (dollar amounts, day counts, percentages)
- **Expert opinions** cited with page/section references
- **Exhibit references** (SOCO xxx, Appendix X, Attachment X, etc.)
- **Quoted text** attributed to expert reports
- **Factual assertions** about project events or timelines

Create a checklist of items requiring verification.

### Step 2: Load Expert Reports Context

Use the `expert-report-research` skill to:
1. Load the expert reports index from `.claude/skills/expert-report-research/references/expert-reports-index.md`
2. Identify which source reports are relevant to this artifact
3. Map the artifact's claims to specific source files

### Step 3: Verify Numerical Claims

For each numerical claim (damages figures, delay days, percentages):

1. Search markdown expert reports using Grep:
   ```
   grep -r "[figure]" expert-reports/markdown/
   ```
2. Read surrounding context to confirm accuracy
3. Flag any discrepancies between artifact and source

### Step 4: Verify Citations and Page References

For each citation (e.g., "Gaudion Main Report, p. 47"):

1. Locate the source file
2. Navigate to the cited page/section
3. Confirm the cited content matches the artifact's characterization
4. Flag any mischaracterizations or incomplete quotations

### Step 5: Deploy Exhibit Ferret for Deep Verification

Use the Task tool to launch the `report-exhibit-ferret` agent for exhibit cross-referencing:

```
Task tool:
  subagent_type: report-exhibit-ferret
  prompt: "Verify the following exhibit references from [artifact name]:
           1. [Exhibit reference 1] - claimed to show [X]
           2. [Exhibit reference 2] - claimed to show [Y]

           For each exhibit:
           - Locate the exhibit in the expert report collection
           - Verify the exhibit actually shows what the artifact claims
           - Note any discrepancies or additional context
           - Flag exhibits that are referenced but not found"
```

### Step 6: Cross-Reference Methodology Claims

For methodology descriptions (e.g., "Gaudion uses windows analysis"):

1. Search source reports for methodology sections
2. Confirm the characterization is accurate and complete
3. Note any nuances omitted from the artifact

### Step 7: Generate Validation Report

Produce a structured validation report:

```markdown
# Validation Report: [Artifact Name]

**Validated:** [Date]
**Source Artifact:** [File path]
**Expert Reports Checked:** [List]

## Summary

| Category | Items Checked | Verified | Discrepancies | Not Found |
|----------|---------------|----------|---------------|-----------|
| Numerical Claims | X | X | X | X |
| Citations | X | X | X | X |
| Exhibit References | X | X | X | X |
| Methodology Claims | X | X | X | X |

**Overall Status:** [VALIDATED / ISSUES FOUND / REQUIRES REVIEW]

## Detailed Findings

### Verified Items
[List of items confirmed accurate with source references]

### Discrepancies Found
[List of items with mismatches, including:
 - What the artifact says
 - What the source actually says
 - Recommended correction]

### Items Not Found
[List of items that could not be verified against source materials]

### Ferret Agent Findings
[Summary of exhibit verification results]

## Recommendations
[Specific corrections or follow-up actions needed]
```

## Quality Standards

- Every numerical figure must trace to a source document
- Quoted text must be verbatim or clearly marked as paraphrased
- Exhibit references must correspond to actual exhibits in the collection
- Methodology characterizations must be fair and complete
- Page/section citations must be accurate

## Output Location

Save the validation report to:
`artifacts/[track]/validation/[artifact-name]-validation.md`

## When to Use

**Pre-Execution (Primary Use Case):**
- After drafting a PRD, **before Phase 1 begins** — Verify all "Key Facts from Reports" are accurate
- Ensures the factual foundation is solid before committing execution time
- Catches errors in figures, page references, or methodology characterizations early

**During Execution:**
- After generating comparison matrices or position summaries
- When updating artifacts with new information

**Pre-Delivery:**
- Before finalizing deliverables for client review
- As quality gate before Phase 4 synthesis

## Notes

- Use `--thorough` flag for comprehensive verification of all claims (slower)
- Without flag, focuses on HIGH/CRITICAL materiality items
- Always verify the "Key Facts from Reports" section of PRDs completely
- Pay special attention to internal inconsistencies flagged in the artifact
