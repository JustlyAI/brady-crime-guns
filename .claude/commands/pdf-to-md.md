---
name: pdf-to-md
allowed-tools: Read, Bash, Glob
argument-hint: <pdf-file(s) | folder>
description: Convert PDF files to Markdown using Docling CLI with OCR and table extraction
model: sonnet
---

# PDF to Markdown Conversion (Docling)

Convert PDF documents to Markdown format using the Docling CLI tool. This uses ML-based layout detection for complex documents with tables and figures.

## Arguments

- First argument (required): One or more PDF files or a folder path

## Output Conventions

- **Folder input**: Creates a new folder `<folder-name>-md/` in the same parent directory
  - Example: `/path/to/documents/` -> `/path/to/documents-md/`
- **Single file input**: Output goes next to the PDF file
  - Example: `/path/to/file.pdf` -> `/path/to/file.md`
- **Multiple files**: Each output goes next to its source PDF

## Task

Convert PDF documents to Markdown format using the Docling CLI. Follow these steps:

1. **Parse Arguments**

   - Identify the source (file(s) or folder) from $ARGUMENTS
   - Validate that the source exists

2. **Determine Output Location**

   - If source is a folder: Create `<folder-name>-md/` in the same parent directory
   - If source is a file: Output goes in the same directory as the PDF

3. **Execute Conversion**

   **For Single File:**
   ```bash
   docling '<pdf-file>' --to md --output '<same-directory-as-pdf>' -v
   ```

   **For Batch Processing (Folder):**
   ```bash
   # Create output directory
   mkdir -p '<folder-path>-md'
   docling '<folder-path>' --to md --output '<folder-path>-md' -v
   ```

   **For Multiple Files:**
   - Process each file individually
   - Output each `.md` file next to its source PDF

4. **Report Results**

   - Show conversion progress and status
   - List output files with their absolute paths
   - Report any errors or warnings
   - Display summary statistics (pages converted, tables extracted, etc.)

## Fallback to PyMuPDF

If Docling fails due to dependency issues (e.g., transformers/rt_detr_v2 errors), fall back to PyMuPDF:

```python
# Use /Users/laurentwiesel/anaconda3/bin/python
import pymupdf
from pathlib import Path

# ... conversion code (see /mupdf command for pattern)
```

Or suggest the user run `/mupdf` instead for a simpler, more reliable conversion.

## Important Notes

- Docling provides ML-based layout detection - best for complex documents with tables/figures
- The `docling` CLI is installed via pyenv at `/Users/laurentwiesel/.pyenv/shims/docling`
- Common options:
  - `--to md`: Output Markdown format
  - `-v`: Verbose output
  - `--ocr`: Enable OCR for scanned documents
  - `--no-tables`: Disable table extraction (faster)
- If you encounter `rt_detr_v2` errors, suggest using `/mupdf` instead

## Examples

**Single file conversion:**
```
/pdf-to-md document.pdf
```
Output: `document.md` (same directory as PDF)

**Batch conversion from folder:**
```
/pdf-to-md /path/to/documents/
```
Output: `/path/to/documents-md/` folder with all converted files

**Multiple files:**
```
/pdf-to-md file1.pdf file2.pdf file3.pdf
```
Output: Each `.md` file next to its source PDF

## When to Use Which Command

| Command | Best For | Speed | Dependencies |
|---------|----------|-------|--------------|
| `/mupdf` | Text-heavy docs (briefs, contracts) | Fast | None (PyMuPDF only) |
| `/pdf-to-md` | Complex layouts, tables, figures | Slower | ML models required |
