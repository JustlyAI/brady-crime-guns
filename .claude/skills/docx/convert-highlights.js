const fs = require('fs');
const { Document, Packer, Paragraph, TextRun, Table, TableRow, TableCell,
        HeadingLevel, AlignmentType, BorderStyle, WidthType, ShadingType,
        VerticalAlign, LevelFormat } = require('docx');

const inputPath = '/Users/laurentwiesel/Dev/LIT/workbench/output/deposition_eval/highlights.md';
const outputPath = '/Users/laurentwiesel/Dev/LIT/workbench/output/deposition_eval/highlights.docx';

const content = fs.readFileSync(inputPath, 'utf-8');
const lines = content.split('\n');

const tableBorder = { style: BorderStyle.SINGLE, size: 1, color: "CCCCCC" };
const cellBorders = { top: tableBorder, bottom: tableBorder, left: tableBorder, right: tableBorder };

const children = [];
let bulletListCounter = 0;

// Numbering config for bullet lists
const numberingConfig = [];

for (let i = 0; i < lines.length; i++) {
  const line = lines[i];

  // Skip empty lines
  if (!line.trim()) {
    children.push(new Paragraph({ children: [new TextRun("")] }));
    continue;
  }

  // Main title (# )
  if (line.startsWith('# ')) {
    children.push(new Paragraph({
      heading: HeadingLevel.TITLE,
      children: [new TextRun(line.substring(2))]
    }));
    continue;
  }

  // H2 (## )
  if (line.startsWith('## ')) {
    children.push(new Paragraph({
      heading: HeadingLevel.HEADING_1,
      children: [new TextRun(line.substring(3))]
    }));
    continue;
  }

  // H3 (### )
  if (line.startsWith('### ')) {
    children.push(new Paragraph({
      heading: HeadingLevel.HEADING_2,
      children: [new TextRun(line.substring(4))]
    }));
    continue;
  }

  // Bold line starting with **
  if (line.startsWith('**') && line.endsWith('**')) {
    const text = line.substring(2, line.length - 2);
    children.push(new Paragraph({
      children: [new TextRun({ text: text, bold: true })]
    }));
    continue;
  }

  // Bullet points (starts with "- ")
  if (line.startsWith('- ')) {
    const listRef = `bullet-list-${bulletListCounter}`;

    // Add numbering config if not exists
    if (!numberingConfig.find(c => c.reference === listRef)) {
      numberingConfig.push({
        reference: listRef,
        levels: [{
          level: 0,
          format: LevelFormat.BULLET,
          text: "•",
          alignment: AlignmentType.LEFT,
          style: { paragraph: { indent: { left: 720, hanging: 360 } } }
        }]
      });
    }

    children.push(new Paragraph({
      numbering: { reference: listRef, level: 0 },
      children: [new TextRun(line.substring(2))]
    }));
    continue;
  }

  // Block quote (starts with "> ")
  if (line.startsWith('> ')) {
    const quoteText = line.substring(2);
    // Parse the Python dict format
    try {
      const quoteMatch = quoteText.match(/'quote':\s*'([^']+)',\s*'citation':\s*'([^']+)',\s*'significance':\s*"([^"]+)"/);
      if (quoteMatch) {
        children.push(new Paragraph({
          indent: { left: 720 },
          children: [
            new TextRun({ text: '"' + quoteMatch[1] + '"', italics: true }),
            new TextRun({ text: ' — ' + quoteMatch[2], bold: true })
          ]
        }));
        children.push(new Paragraph({
          indent: { left: 720 },
          children: [new TextRun({ text: quoteMatch[3], size: 20 })]
        }));
      } else {
        children.push(new Paragraph({
          indent: { left: 720 },
          children: [new TextRun({ text: quoteText, italics: true })]
        }));
      }
    } catch {
      children.push(new Paragraph({
        indent: { left: 720 },
        children: [new TextRun({ text: quoteText, italics: true })]
      }));
    }
    continue;
  }

  // Horizontal rule (---)
  if (line === '---') {
    children.push(new Paragraph({
      border: { bottom: { style: BorderStyle.SINGLE, size: 6, color: "CCCCCC" } },
      children: [new TextRun("")]
    }));
    continue;
  }

  // Table detection
  if (line.startsWith('|') && line.endsWith('|')) {
    // Collect table rows
    const tableLines = [line];
    let j = i + 1;
    while (j < lines.length && lines[j].startsWith('|') && lines[j].endsWith('|')) {
      tableLines.push(lines[j]);
      j++;
    }
    i = j - 1; // Skip processed lines

    // Parse table
    const tableRows = tableLines
      .filter(tl => !tl.includes('---')) // Skip separator
      .map(tl => tl.split('|').map(cell => cell.trim()).filter(cell => cell));

    if (tableRows.length > 0) {
      const numCols = tableRows[0].length;
      const colWidth = Math.floor(9360 / numCols);

      const rows = tableRows.map((row, rowIdx) => {
        const cells = row.map(cell => new TableCell({
          borders: cellBorders,
          width: { size: colWidth, type: WidthType.DXA },
          shading: rowIdx === 0 ? { fill: "D5E8F0", type: ShadingType.CLEAR } : undefined,
          verticalAlign: VerticalAlign.CENTER,
          children: [new Paragraph({
            alignment: rowIdx === 0 ? AlignmentType.CENTER : AlignmentType.LEFT,
            children: [new TextRun({ text: cell, bold: rowIdx === 0, size: rowIdx === 0 ? 22 : 20 })]
          })]
        }));

        return new TableRow({
          tableHeader: rowIdx === 0,
          children: cells
        });
      });

      children.push(new Table({
        columnWidths: Array(numCols).fill(colWidth),
        margins: { top: 100, bottom: 100, left: 180, right: 180 },
        rows: rows
      }));
    }
    continue;
  }

  // Regular paragraph
  children.push(new Paragraph({
    children: [new TextRun(line)]
  }));
}

// Increment bullet list counter when switching contexts
const finalChildren = [];
let prevWasBullet = false;
for (const child of children) {
  if (child.numbering) {
    if (!prevWasBullet) {
      bulletListCounter++;
    }
    prevWasBullet = true;
  } else {
    prevWasBullet = false;
  }
  finalChildren.push(child);
}

const doc = new Document({
  styles: {
    default: {
      document: { run: { font: "Arial", size: 22 } }
    },
    paragraphStyles: [
      {
        id: "Title",
        name: "Title",
        basedOn: "Normal",
        run: { size: 56, bold: true, color: "000000", font: "Arial" },
        paragraph: { spacing: { before: 240, after: 120 }, alignment: AlignmentType.CENTER }
      },
      {
        id: "Heading1",
        name: "Heading 1",
        basedOn: "Normal",
        next: "Normal",
        quickFormat: true,
        run: { size: 32, bold: true, color: "000000", font: "Arial" },
        paragraph: { spacing: { before: 240, after: 240 }, outlineLevel: 0 }
      },
      {
        id: "Heading2",
        name: "Heading 2",
        basedOn: "Normal",
        next: "Normal",
        quickFormat: true,
        run: { size: 28, bold: true, color: "000000", font: "Arial" },
        paragraph: { spacing: { before: 180, after: 180 }, outlineLevel: 1 }
      }
    ]
  },
  numbering: {
    config: numberingConfig
  },
  sections: [{
    properties: {
      page: {
        margin: { top: 1440, right: 1440, bottom: 1440, left: 1440 }
      }
    },
    children: finalChildren
  }]
});

Packer.toBuffer(doc).then(buffer => {
  fs.writeFileSync(outputPath, buffer);
  console.log(`Document saved to: ${outputPath}`);
});
