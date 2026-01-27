---
name: validate-eval
allowed-tools: Bash, Read
description: Validate that the s_c_workbench infrastructure is ready for LegalBench evaluation
---

Run comprehensive validation checks to ensure the s_c_workbench infrastructure is ready for LegalBench evaluation.

## What This Command Does

Executes the validation script that performs 5 critical checks:

1. **Matter Directory Structure** - Verifies Matter 111111-0002 directory and required files exist
2. **Memory Handler Functionality** - Tests that memory handler can load eval matter context
3. **Memory Service Integration** - Validates memory service can integrate matter files
4. **Agent Initialization** - Confirms Maite agent can initialize with eval matter context
5. **Database Connectivity** - Tests PostgreSQL connection (if enabled)

## Execution

!`python src/shared/scripts/validate_eval_readiness.py`

## Expected Output

The script displays colored validation results:

```
🔍 LEGALBENCH EVALUATION READINESS VALIDATION

CHECK 1: Matter 111111-0002 Directory Structure
  ✓ Matter directory exists: .maite/memories/matters/111111-0002
  ✓ context.md exists (2156 bytes)
  ✓ strategy.md exists (3421 bytes)
  ✓ timeline.md exists (1234 bytes)

CHECK 2: Memory Handler Functionality
  ✓ LocalMemoryHandler imported successfully
  ✓ Matter context.md readable via memory handler

CHECK 3: Memory Service Matter Loading
  ✓ MaiteMemoryService initialized
  ✓ Matter context loaded successfully
  ✓ All three matter files present in context

CHECK 4: Maite Agent Initialization with Eval Matter
  ✓ MaiteAgent instantiated with matter_id=111111-0002
  ✓ Agent memory initialized
  ✓ Matter context loaded into agent
  ✓ Current context loaded into agent
  ✓ System prompt includes eval matter context

CHECK 5: Database Connectivity (PostgreSQL)
  ✓ PostgreSQL connection successful
    Existing eval sessions: 3

📊 VALIDATION SUMMARY

Total Checks: 15
Passed: 15
Failed: 0
Success Rate: 100.0%

✅ ALL CHECKS PASSED - SYSTEM IS EVAL-READY!
```

## Exit Codes

- **0** - All checks passed, system is eval-ready
- **1** - Minor issues detected (1-2 failures), mostly ready
- **2** - Critical issues detected (3+ failures), not ready

## Usage

```bash
# Run validation checks
/validate-eval
```

## What Gets Validated

**Matter Structure:**
- `.maite/memories/matters/111111-0002/` directory exists
- Required files: `context.md`, `strategy.md`, `timeline.md`

**Memory System:**
- LocalMemoryHandler can load matter files
- MaiteMemoryService integrates all context files
- Matter content includes "LegalBench Evaluation" marker

**Agent Integration:**
- MaiteAgent initializes with `matter_id="111111-0002"`
- Matter context loads into agent memory
- System prompt includes eval context

**Database (Optional):**
- PostgreSQL connection works (if `SESSION_STORAGE_MODE=postgres`)
- Can query existing eval sessions

## When to Use

Run this command:
- Before starting LegalBench evaluation
- After infrastructure changes to memory or agent systems
- To verify eval matter setup after cloning repository
- When troubleshooting eval integration issues

## Next Steps After Validation

If all checks pass:
1. Review `.docs/EVAL-INTEGRATION-QUICK-START.md` for integration guide
2. Implement eval wrapper in LegalBench codebase
3. Run quick smoke test (5 tasks × 5 samples)
4. Analyze results in PostgreSQL

## Notes

- Script execution time: ~2-3 seconds
- Requires virtual environment activated with all dependencies
- Does not modify any files or data
- Safe to run multiple times
- Database check skipped if PostgreSQL not enabled
