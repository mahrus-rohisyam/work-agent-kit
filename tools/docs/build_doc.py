# /// script
# requires-python = ">=3.10"
# dependencies = ["python-docx==1.2.0"]
# ///
"""Build a branded Word document from a JSON spec, using the document template named in the theme
(its header, footer, page setup and styles).

  uv run tools/docs/build_doc.py SPEC.json [--out outputs/x.docx] [--theme templates/other.json]

The spec and theme formats are documented in tools/docs/README.md.
"""

import argparse

import docx
from docx.enum.table import WD_CELL_VERTICAL_ALIGNMENT
from docx.enum.text import WD_BREAK
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import RGBColor

from theme import abs_path, color, load_json, load_theme, output_path


class Doc:
    def __init__(self, cfg, theme):
        self.theme, self.map = theme, theme["doc"]
        template = abs_path(cfg.get("template") or self.map["template"])
        if not template.exists():
            raise SystemExit(f"Template not found: {template}")
        self.d = docx.Document(str(template))
        self.style_names = {s.name for s in self.d.styles}
        body = self.d.element.body
        for el in list(body):   # keep only the section settings (page, header, footer)
            if el.tag != qn("w:sectPr"):
                body.remove(el)

    def style(self, key):
        name = self.map["styles"].get(key)
        return name if name in self.style_names else "Normal"

    def rgb(self, name, default):
        return color(self.theme, self.map.get(name), default)

    def list_block(self, items, numbered):
        ps = [self.d.add_paragraph(str(t), style=self.style("number" if numbered else "bullet")) for t in items]
        if numbered and ps:
            self.restart_numbering(ps)

    def restart_numbering(self, paragraphs):
        """Give this list its own numbering instance so it starts at 1."""
        num_id = paragraphs[0].style.element.xpath("./w:pPr/w:numPr/w:numId/@w:val")
        if not num_id:
            return
        numbering = self.d.part.numbering_part.element
        num = numbering.add_num(numbering.num_having_numId(int(num_id[0])).abstractNumId.val)
        num.add_lvlOverride(ilvl=0).add_startOverride(1)
        for p in paragraphs:
            pr = p._p.get_or_add_pPr().get_or_add_numPr()
            pr.get_or_add_ilvl().val = 0
            pr.get_or_add_numId().val = num.numId

    @staticmethod
    def shade(cell, rgb):
        shd = OxmlElement("w:shd")
        for k, v in (("w:val", "clear"), ("w:color", "auto"), ("w:fill", rgb)):
            shd.set(qn(k), v)
        cell._tc.get_or_add_tcPr().append(shd)

    def table(self, rows, header, label_cols, widths):
        nc = max(len(r) for r in rows)
        sec = self.d.sections[-1]
        usable = sec.page_width - sec.left_margin - sec.right_margin
        rel = ((widths or []) + [1] * nc)[:nc]
        col_w = [int(usable * w / sum(rel)) for w in rel]
        t = self.d.add_table(rows=len(rows), cols=nc)
        if "Table Grid" in self.style_names:
            t.style = "Table Grid"
        t.autofit = False
        for c, w in enumerate(col_w):
            t.columns[c].width = w
        for r, cells in enumerate(rows):
            tr_pr = t.rows[r]._tr.get_or_add_trPr()
            tr_pr.append(OxmlElement("w:cantSplit"))
            if header and r == 0:
                tr_pr.append(OxmlElement("w:tblHeader"))   # repeat on every page
            for c, w in enumerate(col_w):
                cell = t.cell(r, c)
                cell.width = w
                is_head, is_label = header and r == 0, (c + 1) in label_cols
                if is_head or is_label:
                    self.shade(cell, self.rgb("headerFill", "primary") if is_head else self.rgb("labelFill", "light"))
                cell.vertical_alignment = WD_CELL_VERTICAL_ALIGNMENT.CENTER
                p = cell.paragraphs[0]
                p.style = self.style("tableHeader" if is_head or is_label else "tableText")
                run = p.add_run(str(cells[c]) if c < len(cells) else "")
                if is_head:
                    run.font.color.rgb = RGBColor.from_string(self.rgb("headerText", "white"))
        self.d.add_paragraph(style=self.style("tableText"))   # space after the table

    def build(self, blocks):
        for n, b in enumerate(blocks, 1):
            kind = b.get("type")
            if kind == "heading":
                self.d.add_paragraph(b["text"], style=self.style(f"heading{min(3, int(b.get('level', 1)))}"))
            elif kind == "paragraph":
                self.d.add_paragraph(b["text"], style=self.style("body"))
            elif kind in ("bullets", "numbered"):
                self.list_block(b["items"], kind == "numbered")
            elif kind == "info":   # key/value grid with shaded label columns
                self.table(b["rows"], False, b.get("labelColumns", [1, 3]), b.get("widths"))
            elif kind == "table":
                self.table([b["header"], *b["rows"]], True, [], b.get("widths"))
            elif kind == "pagebreak":
                self.d.add_paragraph().add_run().add_break(WD_BREAK.PAGE)
            else:
                raise SystemExit(f"Block {n}: unknown type '{kind}'")

    def save(self, out):
        # Word does not refresh FILENAME on open; store the right value now.
        for sec in self.d.sections:
            for part in (sec.header, sec.footer):
                for fld in part._element.iter(qn("w:fldSimple")):
                    if "FILENAME" in fld.get(qn("w:instr"), ""):
                        for t in fld.iter(qn("w:t")):
                            t.text = out.name
        self.d.save(str(out))


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("spec")
    ap.add_argument("--out")
    ap.add_argument("--theme")
    a = ap.parse_args()
    cfg = load_json(a.spec)
    out = output_path(a.out, cfg)
    doc = Doc(cfg, load_theme(a.theme or cfg.get("theme")))
    doc.build(cfg["blocks"])
    doc.save(out)
    print("OUTPUT:", out)
    print("BLOCKS:", len(cfg["blocks"]))


if __name__ == "__main__":
    main()
