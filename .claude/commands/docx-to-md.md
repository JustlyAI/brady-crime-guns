---
name: docx-to-md
allowed-tools: Read, Bash, Glob
argument-hint: <docx-file(s) | folder>
description: Convert Word documents (.docx) to Markdown using mammoth
model: sonnet
---

# DOCX to Markdown Conversion

Convert Word documents (.docx) to Markdown format using mammoth.

## Arguments

- First argument (required): One or more .docx files or a folder path

## Output Conventions

- **Folder input**: Creates a new folder `<folder-name>-md/` in the same parent directory
  - Example: `/path/to/documents/` -> `/path/to/documents-md/`
- **Single file input**: Output goes next to the .docx file
  - Example: `/path/to/file.docx` -> `/path/to/file.md`
- **Multiple files**: Each output goes next to its source .docx

## Task

Convert Word documents to Markdown format using mammoth. Follow these steps:

1. **Parse Arguments**

   - Identify the source (file(s) or folder) from $ARGUMENTS
   - Validate that the source exists

2. **Determine Output Location**

   - If source is a folder: Create `<folder-name>-md/` in the same parent directory
   - If source is a file: Output goes in the same directory as the .docx

3. **Execute Conversion**

   Use this Python script pattern with `/Users/laurentwiesel/anaconda3/bin/python`:

   **For folder processing:**
   ```python
   import mammoth
   from pathlib import Path

   input_dir = Path('<folder-path>')
   output_dir = input_dir.parent / (input_dir.name + '-md')
   output_dir.mkdir(parents=True, exist_ok=True)

   docx_files = list(input_dir.glob('*.docx')) + list(input_dir.glob('*.DOCX'))

   print(f'Found {len(docx_files)} DOCX files to convert')

   for docx_file in docx_files:
       print(f'Converting: {docx_file.name}')
       with open(docx_file, 'rb') as f:
           result = mammoth.convert_to_markdown(f)
           md_content = result.value

           # Report any conversion messages/warnings
           if result.messages:
               for msg in result.messages:
                   print(f'  Warning: {msg}')

       output_file = output_dir / (docx_file.stem + '.md')
       output_file.write_text(md_content, encoding='utf-8')
       print(f'  Saved to: {output_file}')

   print(f'\nConversion complete! Files saved to: {output_dir}')
   ```

   **For single file:**
   ```python
   import mammoth
   from pathlib import Path

   docx_file = Path('<docx-path>')
   output_file = docx_file.with_suffix('.md')

   print(f'Converting: {docx_file.name}')
   with open(docx_file, 'rb') as f:
       result = mammoth.convert_to_markdown(f)
       md_content = result.value

       if result.messages:
           for msg in result.messages:
               print(f'  Warning: {msg}')

   output_file.write_text(md_content, encoding='utf-8')
   print(f'Saved to: {output_file}')
   ```

4. **Report Results**

   - Show conversion progress and status
   - List output files with their absolute paths
   - Report any warnings from mammoth
   - Display summary (total files converted)

## Important Notes

- Uses `/Users/laurentwiesel/anaconda3/bin/python` which has mammoth installed
- Mammoth preserves semantic structure (headings, lists, bold, italic)
- Images are extracted as base64 by default (can be large)
- Tables are converted to markdown tables
- Always use `encoding='utf-8'` when writing files

## Examples

**Single file conversion:**
```
/docx-to-md document.docx
```
Output: `document.md` (same directory)

**Batch conversion from folder:**
```
/docx-to-md /path/to/documents/
```
Output: `/path/to/documents-md/` folder with all converted files

**Multiple files:**
```
/docx-to-md file1.docx file2.docx file3.docx
```
Output: Each `.md` file next to its source .docx
