# Claude Code Commands

This directory contains custom slash commands for the Workbench project.

## Available Commands

| Command | Description |
|---------|-------------|
| `/cleanup` | Post-session cleanup of code, test files, and phase reports |
| `/code-review` | Comprehensive code quality review with security and performance analysis |
| `/comparison-cite-checker` | Citation verification with 99% accuracy target (Ralph Loop compatible) |
| `/deep-depo-coverage` | Deep deposition coverage analysis one topic at a time (Ralph Loop compatible) |
| `/depo-coverage` | Compare deposition prep topics against actual deposition indexes |
| `/depo-coverage-report` | Generate strategic coverage analysis report from assessed topics JSON |
| `/implementation-summary` | Generate detailed markdown summary of implemented features |
| `/pdf-to-md` | Convert PDF files to Markdown using Docling CLI with OCR |
| `/prd` | Create Product Requirements Document with phased implementation plan |
| `/refresh-context` | Update context YAML with datetime, location, and available skills |
| `/understand` | Analyze codebase architecture, patterns, and component relationships |
| `/update_claude_docs` | Align Claude Agent SDK documentation with reference documents |
| `/validate-eval` | Validate infrastructure readiness for LegalBench evaluation |
| `/validate-expert-artifact` | Verify PRD claims against source expert reports |

---

## Command Details

### `/cleanup`
Post-development cleanup. Removes ad hoc test files, phase completion reports, and any bloat added during development. Preserves intentional tests in `tests/` and planned docs in `.docs/`.

### `/code-review [file-path | commit-hash | --full]`
Multi-dimensional code review covering:
- Code quality and anti-patterns
- Security vulnerabilities (OWASP top 10)
- Performance bottlenecks
- Architecture and design
- Test coverage gaps
- Documentation completeness

### `/comparison-cite-checker [--json <citations.json>] [--sources <source-dir>] [--output <path>]`
Ralph Loop compatible citation verification. Processes one citation at a time with exhaustive accuracy checking (99% target, 90% minimum). Features:
- **Flexible schema**: Auto-detects citation structure (legal, expert report, academic, generic)
- **3-attempt safety**: Prevents infinite loops on ambiguous citations
- **Comprehensive checks**: Source existence, location accuracy, content accuracy, context verification
- **Statuses**: ACCURATE, MINOR_ISSUE, INACCURATE, NOT_FOUND
- Use with `/ralph-loop /comparison-cite-checker --completion-promise 'All citations verified'`

### `/deep-depo-coverage [--json <topics.json>] [--index <depo-index.json>] [--output <path>]`
Ralph Loop compatible deposition coverage analysis. Processes one prep topic at a time with exhaustive multi-volume search (99% certainty target, 90% minimum). Features:
- **3-attempt safety**: Prevents infinite loops, flags topics for manual review
- **Format-agnostic**: Auto-converts Excel/CSV/PDF/Word sources using Task tool delegation
- **Checkpoint resumption**: Updates JSON after each topic for interruption/restart
- **Quality tracking**: Certainty levels, attempt counts, search terms documented
- Use with `/ralph-loop /deep-depo-coverage --completion-promise 'All 195 topics assessed'`

### `/depo-coverage [--json <topics.json>] [--indexes <vol1.md> <vol2.md>...] [--output <path>]`
Compare deposition prep topics against actual deposition topic indexes. Assesses all topics in one run:
- **Coverage classification**: COVERED, PARTIAL, NOT_COVERED
- **Gap identification**: Lists uncovered topics by section
- **Emergent topics**: Identifies discussion topics not in prep list
- **Verification**: Ensures all topics assessed with volume/page citations
- Outputs: Updated JSON + markdown coverage report

### `/depo-coverage-report [--json <assessed.json>] [--context <file1> <file2>...] [--output <path>]`
Generates comprehensive strategic coverage analysis report from assessed deposition topics JSON. Produces 20-40 page markdown report with:
- **Coverage statistics**: Overall, by section, by subsection
- **Strategic pattern analysis**: What was prioritized vs avoided, opposing counsel strategy
- **Gap analysis**: Critical gaps by section with prioritization
- **Partial coverage deep dive**: What was covered, what remains, strategic value
- **Emergent topics**: Unplanned discussion areas from deposition (requires context files)
- **Volume progression**: How deposition evolved across volumes
- **Recommendations**: Actionable follow-up for depositions, discovery, case strategy

### `/implementation-summary [feature-name] [--archive]`
Generates comprehensive markdown documentation for completed features. Auto-detects feature name from git changes. Includes file changes with line numbers, architecture decisions, testing documentation, and usage examples. Aliases: `/impl-summary`, `/summary`.

### `/pdf-to-md <pdf-file(s) | folder> [output-folder]`
Converts PDFs to Markdown via Docling CLI. Supports single files, multiple files, or batch processing from folders. Default output: `output/converted_pdf_to_md/`. Includes OCR support for scanned documents.

### `/prd <feature-description>`
Creates a Product Requirements Document in `.plans/<feature-name>.md`. Structured for Claude Code execution with:
- Feature overview and requirements
- Technical architecture (database, API, frontend)
- Implementation phases with specific tasks and verification steps
- File structure impact

### `/refresh-context [location]`
Updates `current_context.md` YAML frontmatter with:
- Current datetime (ISO 8601)
- Day of week
- Location (IP-detected or manual override)
- Available skills and tools

### `/understand [focus-area]`
Deep codebase analysis producing:
- Project architecture and tech stack
- Entry points and module organization
- Dependency mapping (internal and external)
- Pattern recognition (naming, error handling, auth flow)
- Component map with key insights

### `/update_claude_docs <reference-docs...>`
Systematic update of Claude Agent SDK documentation across:
- Root README
- Agent definitions
- Cursor rules
- SDK skills

Enforces SDK 0.1.4+ compliance and valid permission modes.

### `/validate-eval`
Pre-evaluation infrastructure check for LegalBench. Validates:
- Matter directory structure (111111-0002)
- Memory handler functionality
- Memory service integration
- Agent initialization with eval context
- Database connectivity (PostgreSQL)

Exit codes: 0 (ready), 1 (minor issues), 2 (critical issues).

### `/validate-expert-artifact <file-path> [--thorough]`
Cross-references PRD claims against source expert reports:
- Numerical claims verification
- Citation and page reference checks
- Exhibit reference validation (via `report-exhibit-ferret` agent)
- Methodology claim accuracy

Produces structured validation report with discrepancies and recommendations.

---

## Usage

Invoke commands with `/command-name` in Claude Code:

```
/understand src/agents/
/code-review --full
/pdf-to-md documents/brief.pdf
/prd Add user authentication with OAuth2

# Deposition analysis (Ralph Loop)
/ralph-loop /deep-depo-coverage --completion-promise 'All 195 topics assessed' --max-iterations 250
/depo-coverage-report

# Citation verification (Ralph Loop)
/ralph-loop /comparison-cite-checker --completion-promise 'All citations verified' --max-iterations 500
```
