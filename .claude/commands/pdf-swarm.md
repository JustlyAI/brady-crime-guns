---
name: pdf-swarm
allowed-tools: Read, Bash, Glob, Task, AskUserQuestion
argument-hint: <folder-path>
description: Convert multiple PDFs to Markdown using parallel subagents for maximum throughput
model: sonnet
---

# PDF Swarm Processor

Convert multiple PDF documents to Markdown using a swarm of parallel subagents. Uses Docling (preferred) with PyMuPDF fallback.

## Arguments

- First argument (required): Folder path containing PDF files

## Output Conventions

- **Folder input**: Creates `<folder-name>-md/` in same parent directory
- Example: `/path/to/documents/` -> `/path/to/documents-md/`

## Workflow

### Step 0: Analyze PDF Type (Required)

Before swarming, sample 1-2 PDFs to detect if they're text-based or scanned:

```bash
/Users/laurentwiesel/anaconda3/bin/python << 'EOF'
import pymupdf
from pathlib import Path

pdf_path = "<first-pdf-in-folder>"
doc = pymupdf.open(pdf_path)
text = doc[0].get_text().strip()
has_text = bool(text) and len(text) > 50

print(f"File: {Path(pdf_path).name}")
print(f"Pages: {len(doc)}")
print(f"Extractable text: {'Yes' if has_text else 'No (scanned/image-based)'}")
if has_text:
    print(f"Sample: {text[:200]}...")
print(f"Recommended mode: {'text' if has_text else 'ocr'}")
doc.close()
EOF
```

**Determine conversion mode:**

| Mode | Detection | Docling Command |
|------|-----------|-----------------|
| `text` | Has extractable text | `docling '<pdf>' --to md --output '<dir>' -v` |
| `ocr` | Scanned/image-based | `docling '<pdf>' --to md --output '<dir>' --force-ocr --image-export-mode placeholder --ocr-engine ocrmac -v` |

**Confirm with user using AskUserQuestion:**
- Present the analysis findings
- Show recommended mode (text or ocr)
- Ask user to confirm before proceeding

### Step 1: Discover PDFs

```bash
find "$ARGUMENTS" -maxdepth 1 \( -name "*.pdf" -o -name "*.PDF" \) | sort
```

Print the count and list of files found.

### Step 2: Create Output Directory

```bash
output_dir="${ARGUMENTS%/}-md"
mkdir -p "$output_dir"
```

### Step 3: Dispatch Converter Swarm

For each PDF, dispatch a Task subagent. **Send ALL Task calls in a SINGLE message for parallel execution.**

**For TEXT mode (standard Docling):**
```
Convert PDF to Markdown using Docling:

INPUT: <absolute-pdf-path>
OUTPUT_DIR: <output-directory>

Run:
docling '<pdf-path>' --to md --output '<output-dir>' -v

If Docling fails, fall back to PyMuPDF:
/Users/laurentwiesel/anaconda3/bin/python /Users/laurentwiesel/Dev/AIF/workbench/.claude/skills/pdf-swarm-processor/scripts/convert_pdf.py '<pdf-path>' '<output-dir>/<filename>.md'

Report: SUCCESS/FAILED, output path, any errors
```

**For OCR mode (scanned PDFs):**
```
Convert scanned PDF to Markdown using Docling with OCR:

INPUT: <absolute-pdf-path>
OUTPUT_DIR: <output-directory>

Run:
docling '<pdf-path>' --to md --output '<output-dir>' --force-ocr --image-export-mode placeholder --ocr-engine ocrmac -v

Report: SUCCESS/FAILED, output path, any errors
```

**Batch size**: Process up to 10 PDFs in parallel per wave.

### Step 4: Dispatch Validator Swarm

After conversions complete, dispatch `md-conversion-validator` agents for each output:

```
Use Task tool with subagent_type="md-conversion-validator"
Prompt: "Validate the markdown conversion quality of: <output-md-path>"
```

Run validators in parallel (single message with multiple Task calls).

### Step 5: Aggregate Results

```markdown
# PDF Swarm Processing Report

## Configuration
- Mode: [text|ocr]
- Converter: Docling [+ PyMuPDF fallback if used]

## Summary
- Total PDFs: [count]
- Successful: [count]
- Failed: [count]

## Results
| File | Mode | Status | Validation |
|------|------|--------|------------|
| ... | text/ocr | ✓/✗ | PASS/FAIL |

## Output Location
<output-directory>

## Issues (if any)
[List any conversion or validation failures]
```

## Conversion Priority

1. **Docling** (preferred) - ML-based layout detection, table extraction, OCR support
2. **PyMuPDF** (fallback) - Fast, reliable, no dependencies, text-only

## Performance Guidelines

- **Wave size**: 10 PDFs per parallel wave
- **Timeouts**: Docling with OCR may take 1-3 minutes per PDF
- **Memory**: Each subagent is independent

## Example

```
/pdf-swarm /path/to/discovery-documents/
```

This will:
1. Analyze sample PDFs to detect text vs scanned
2. Confirm conversion mode with user
3. Find all PDFs in the folder
4. Dispatch parallel Docling converter subagents (waves of 10)
5. Validate each converted file
6. Report results with summary statistics
