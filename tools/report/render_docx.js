// Turn report.json (written by build_report.py) into a .docx in the style of the Review 2 report.
// usage: node render_docx.js report.json out.docx
const fs = require('fs');
const path = require('path');
const {
  Document, Packer, Paragraph, TextRun, ImageRun, Table, TableRow, TableCell, WidthType,
  BorderStyle, AlignmentType, HeadingLevel, PageBreak, Footer, PageNumber, TableOfContents,
  LevelFormat, VerticalAlign, ShadingType,
} = require('docx');

const [, , specPath, outPath] = process.argv;
const spec = JSON.parse(fs.readFileSync(specPath, 'utf8'));
const base = path.dirname(specPath);

const FONT = 'Calibri';
const MONO = 'Consolas';
const PAGE_W = 9360; // 6.5 in of text width, in DXA

function runs(r, size) {
  // r: string | [ {text, b, i, code} ... ]
  const list = typeof r === 'string' ? [{ text: r }] : r;
  return list.map(x => new TextRun({
    text: x.text, bold: !!x.b, italics: !!x.i,
    font: x.code ? MONO : FONT,
    size: x.code ? Math.round((size || 22) * 0.86) : size,
  }));
}

const border = { style: BorderStyle.SINGLE, size: 4, color: '000000' };
const borders = { top: border, bottom: border, left: border, right: border };

function cellParas(c, isHeader) {
  const o = typeof c === 'string' ? { text: c } : c;
  const lines = String(o.text).split('\n');
  return lines.map(line => new Paragraph({
    alignment: isHeader ? AlignmentType.CENTER : AlignmentType.LEFT,
    spacing: { before: 0, after: 0 },
    children: [new TextRun({
      text: line, bold: isHeader || !!o.b,
      font: o.code ? MONO : FONT, size: o.code ? 15 : 20,
    })],
  }));
}

function table(b) {
  const widths = b.cols;
  const total = widths.reduce((a, x) => a + x, 0);
  const mk = (cells, header) => new TableRow({
    tableHeader: header,
    cantSplit: !!b.cantSplit,
    children: cells.map((c, i) => new TableCell({
      width: { size: widths[i], type: WidthType.DXA },
      borders,
      margins: { top: 50, bottom: 50, left: 90, right: 90 },
      verticalAlign: VerticalAlign.CENTER,
      shading: header ? { type: ShadingType.CLEAR, color: 'auto', fill: 'F2F2F2' } : undefined,
      children: cellParas(c, header),
    })),
  });
  const rows = [];
  if (b.header) rows.push(mk(b.header, true));
  for (const r of b.rows) rows.push(mk(r, false));
  return new Table({ width: { size: total, type: WidthType.DXA }, columnWidths: widths, rows });
}

function image(b) {
  const data = fs.readFileSync(path.resolve(base, b.path));
  return new Paragraph({
    alignment: AlignmentType.CENTER,
    keepNext: true,
    spacing: { before: 120, after: 60 },
    children: [new ImageRun({
      type: 'png', data,
      transformation: { width: Math.round(b.w_in * 96), height: Math.round(b.h_in * 96) },
    })],
  });
}

const children = [];
for (const b of spec.blocks) {
  switch (b.t) {
    case 'title':
      children.push(new Paragraph({
        alignment: AlignmentType.CENTER,
        spacing: { before: b.before || 0, after: b.after === undefined ? 120 : b.after },
        children: [new TextRun({ text: b.text, bold: !!b.b, size: b.size || 22, font: FONT })],
      }));
      break;
    case 'h1':
      children.push(new Paragraph({ heading: HeadingLevel.HEADING_1, pageBreakBefore: !!b.newPage, children: [new TextRun(b.text)] }));
      break;
    case 'h2':
      children.push(new Paragraph({ heading: HeadingLevel.HEADING_2, children: [new TextRun(b.text)] }));
      break;
    case 'h3':
      children.push(new Paragraph({ heading: HeadingLevel.HEADING_3, keepNext: true, children: [new TextRun(b.text)] }));
      break;
    case 'p':
      children.push(new Paragraph({
        alignment: b.center ? AlignmentType.CENTER : AlignmentType.JUSTIFIED,
        keepNext: !!b.keepNext,
        spacing: { after: 120 },
        children: runs(b.runs || b.text),
      }));
      break;
    case 'code':
      for (const line of b.text.split('\n')) {
        children.push(new Paragraph({
          spacing: { before: 0, after: 0 }, indent: { left: 360 }, keepNext: true,
          children: [new TextRun({ text: line || ' ', font: MONO, size: 17 })],
        }));
      }
      children.push(new Paragraph({ spacing: { after: 60 }, children: [] }));
      break;
    case 'bullets':
      for (const item of b.items) {
        children.push(new Paragraph({ numbering: { reference: 'bullets', level: 0 }, spacing: { after: 60 }, children: runs(item) }));
      }
      break;
    case 'table':
      children.push(table(b));
      children.push(new Paragraph({ spacing: { after: 120 }, children: [] }));
      break;
    case 'img':
      children.push(image(b));
      break;
    case 'caption':
      children.push(new Paragraph({
        alignment: AlignmentType.CENTER, spacing: { before: 0, after: 200 },
        children: [new TextRun({ text: b.text, italics: true, size: 19, font: FONT })],
      }));
      break;
    case 'pagebreak':
      children.push(new Paragraph({ children: [new PageBreak()] }));
      break;
    case 'toc':
      children.push(new TableOfContents('Table of Contents', { hyperlink: true, headingStyleRange: '1-2' }));
      break;
    default:
      throw new Error('unknown block ' + b.t);
  }
}

const doc = new Document({
  creator: spec.author || '',
  title: spec.title || '',
  features: { updateFields: true },
  styles: {
    default: { document: { run: { font: FONT, size: 22, color: '000000' } } },
    paragraphStyles: [
      { id: 'Heading1', name: 'Heading 1', basedOn: 'Normal', next: 'Normal', quickFormat: true,
        run: { size: 32, bold: true, color: '2E74B5', font: FONT }, paragraph: { spacing: { before: 280, after: 140 }, outlineLevel: 0, keepNext: true } },
      { id: 'Heading2', name: 'Heading 2', basedOn: 'Normal', next: 'Normal', quickFormat: true,
        run: { size: 26, bold: true, color: '2E74B5', font: FONT }, paragraph: { spacing: { before: 220, after: 100 }, outlineLevel: 1, keepNext: true } },
      { id: 'Heading3', name: 'Heading 3', basedOn: 'Normal', next: 'Normal', quickFormat: true,
        run: { size: 24, bold: true, color: '1F4D78', font: FONT }, paragraph: { spacing: { before: 180, after: 80 }, outlineLevel: 2, keepNext: true } },
    ],
  },
  numbering: {
    config: [{ reference: 'bullets', levels: [{ level: 0, format: LevelFormat.BULLET, text: '•', alignment: AlignmentType.LEFT,
      style: { paragraph: { indent: { left: 720, hanging: 360 } } } }] }],
  },
  sections: [{
    properties: { page: { size: { width: 12240, height: 15840 }, margin: { top: 1440, right: 1440, bottom: 1440, left: 1440 } } },
    footers: {
      default: new Footer({ children: [new Paragraph({ alignment: AlignmentType.CENTER, children: [new TextRun({ children: [PageNumber.CURRENT], size: 20 })] })] }),
    },
    children,
  }],
});

Packer.toBuffer(doc).then(buf => { fs.writeFileSync(outPath, buf); console.log('wrote', outPath, children.length, 'paragraphs/tables'); });
