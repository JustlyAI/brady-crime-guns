---
name: mupdf
allowed-tools: Read, Bash, Glob
argument-hint: <pdf-file(s) | folder>
description: Convert PDF files to Markdown using PyMuPDF (fast, reliable, no ML dependencies)
model: sonnet
---

# PDF to Markdown Conversion (PyMuPDF)

Convert PDF documents to Markdown format using PyMuPDF. This is a fast, reliable converter that works without ML model dependencies.

## Arguments

- First argument (required): One or more PDF files or a folder path

## Output Conventions

- **Folder input**: Creates a new folder `<folder-name>-md/` in the same parent directory
  - Example: `/path/to/documents/` -> `/path/to/documents-md/`
- **Single file input**: Output goes next to the PDF file
  - Example: `/path/to/file.pdf` -> `/path/to/file.md`
- **Multiple files**: Each output goes next to its source PDF

## Task

Convert PDF documents to Markdown format using PyMuPDF. Follow these steps:

1. **Parse Arguments**

   - Identify the source (file(s) or folder) from $ARGUMENTS
   - Validate that the source exists

2. **Determine Output Location**

   - If source is a folder: Create `<folder-name>-md/` in the same parent directory
   - If source is a file: Output goes in the same directory as the PDF

3. **Execute Conversion**

   Use this Python script pattern with `/Users/laurentwiesel/anaconda3/bin/python`:

   ```python
   import pymupdf
   from pathlib import Path

   # For folder processing
   input_dir = Path('<folder-path>')
   output_dir = input_dir.parent / (input_dir.name + '-md')
   output_dir.mkdir(parents=True, exist_ok=True)

   pdf_files = list(input_dir.glob('*.PDF')) + list(input_dir.glob('*.pdf'))

   for pdf_file in pdf_files:
       doc = pymupdf.open(pdf_file)
       md_content = f'# {pdf_file.stem}\n\n'

       for page_num, page in enumerate(doc, 1):
           text = page.get_text()
           md_content += f'## Page {page_num}\n\n{text}\n\n'

       output_file = output_dir / (pdf_file.stem + '.md')
       output_file.write_text(md_content, encoding='utf-8')
       doc.close()
   ```

   For single file:
   ```python
   import pymupdf
   from pathlib import Path

   pdf_file = Path('<pdf-path>')
   output_file = pdf_file.with_suffix('.md')

   doc = pymupdf.open(pdf_file)
   md_content = f'# {pdf_file.stem}\n\n'

   for page_num, page in enumerate(doc, 1):
       text = page.get_text()
       md_content += f'## Page {page_num}\n\n{text}\n\n'

   output_file.write_text(md_content, encoding='utf-8')
   doc.close()
   ```

4. **Report Results**

   - Show conversion progress and status
   - List output files with their absolute paths
   - Report page counts for each file
   - Display summary (total files, total pages)

## Important Notes

- Uses `/Users/laurentwiesel/anaconda3/bin/python` which has pymupdf installed
- Fast and reliable - no ML model dependencies
- Best for text-based PDFs (court filings, briefs, contracts)
- Does not extract tables with structure (use /pdf-to-md for complex layouts)
- Always use `encoding='utf-8'` when writing files

## Examples

**Single file conversion:**
```
/mupdf document.pdf
```
Output: `document.md` (same directory)

**Batch conversion from folder:**
```
/mupdf /path/to/documents/
```
Output: `/path/to/documents-md/` folder with all converted files

**Multiple files:**
```
/mupdf file1.pdf file2.pdf file3.pdf
```
Output: Each `.md` file next to its source PDF
