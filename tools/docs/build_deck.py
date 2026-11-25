# /// script
# requires-python = ">=3.10"
# dependencies = ["python-pptx==1.0.2"]
# ///
"""Build a branded PowerPoint deck from a JSON spec, using the deck template named in the theme.

  uv run tools/docs/build_deck.py SPEC.json [--out documents/x.pptx] [--theme templates/other.json]

The spec and theme formats are documented in tools/docs/README.md.
"""

import argparse
import math

from pptx import Presentation
from pptx.dml.color import RGBColor
from pptx.enum.shapes import MSO_SHAPE
from pptx.enum.text import MSO_ANCHOR, PP_ALIGN
from pptx.oxml import parse_xml
from pptx.oxml.ns import qn
from pptx.util import Emu, Pt

from theme import abs_path, color, load_json, load_theme, output_path

NOTE_H = 48
COLUMN_GAP = 25
BULLET = '<a:buChar xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main" char="&#8226;"/>'


def as_list(v):
    return [] if v is None else v if isinstance(v, list) else [v]


class Deck:
    def __init__(self, cfg, theme):
        self.theme, self.map = theme, theme["deck"]
        template = abs_path(cfg.get("template") or self.map["template"])
        if not template.exists():
            raise SystemExit(f"Template not found: {template}")
        self.prs = Presentation(str(template))
        ids = self.prs.slides._sldIdLst
        for sld in list(ids):   # start from an empty deck, keep the layouts
            self.prs.part.drop_rel(sld.rId)
            ids.remove(sld)
        b = self.map["body"]
        self.left, self.top, self.width, self.bottom = b["left"], b["top"], b["width"], b["bottom"]
        self.note_top = self.bottom - NOTE_H
        self.warnings = []
        self.n = 0
        self.slide = None

    # ---- helpers ----
    def rgb(self, name, default=None):
        return RGBColor.from_string(color(self.theme, name, default))

    def warn(self, text):
        self.warnings.append(f"Slide {self.n}: {text}")

    def new(self, kind):
        want = self.map[kind]["layout"]
        layouts = list(self.prs.slide_layouts)
        layout = layouts[want] if isinstance(want, int) else next((x for x in layouts if x.name == want), None)
        if layout is None:
            raise SystemExit(f"Layout '{want}' not in the template. Layouts: {', '.join(x.name for x in layouts)}")
        self.slide = self.prs.slides.add_slide(layout)

    def fill_placeholders(self, kind, **texts):
        """Set the mapped placeholders and remove the rest (empty ones show their prompt text)."""
        m = self.map[kind]
        wanted = {m[k]: t for k, t in texts.items() if k in m and t}
        for ph in list(self.slide.placeholders):
            text = wanted.pop(ph.placeholder_format.idx, None)
            if text is None:
                ph._element.getparent().remove(ph._element)
            else:
                ph.text_frame.text = text
        if wanted:
            raise SystemExit(f"Slide {self.n}: the '{kind}' layout has no placeholder {list(wanted)}; fix the theme's deck map")

    def content(self, title):
        self.new("content")
        self.fill_placeholders("content", title=title)
        ph = next(x for x in self.slide.placeholders if x.placeholder_format.idx == self.map["content"]["title"])
        if len(title) * 14 > Emu(ph.width).pt:
            self.warn(f"title '{title}' may not fit on one line; shorten it")

    def body_bottom(self, sl):
        return self.note_top - 10 if sl.get("note") else self.bottom

    def check(self, name, paragraphs, width, height):
        """Rough text height (no font metrics): flags boxes that probably overflow."""
        need = 0
        for text, size, after in paragraphs:
            chars = max(1, int(width / (size * 0.5)))
            need += max(1, math.ceil(len(text) / chars)) * size * 1.2 + after
        if need > height + 4:
            self.warn(f"text in '{name}' probably overflows ({need:.0f}pt > {height:.0f}pt). Cut words, lower 'size', or split the slide")

    def text_box(self, left, top, width, height, name):
        box = self.slide.shapes.add_textbox(Pt(left), Pt(top), Pt(width), Pt(height))
        box.name = name
        tf = box.text_frame
        tf.word_wrap = True
        tf.margin_left = tf.margin_right = 0
        return tf

    def write(self, tf, i, parts, after=0, align=PP_ALIGN.LEFT):
        """Paragraph i of tf from runs [(text, size, bold, color)]."""
        p = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
        p.alignment = align
        p.space_after = Pt(after)
        for text, size, bold, rgb in parts:
            r = p.add_run()
            r.text, r.font.size, r.font.bold = str(text), Pt(size), bold
            r.font.color.rgb = rgb
        return p

    def column_items(self, col):
        """[(text, kind, color name or None)]; kind: b bullet, p plain, h heading."""
        items = []
        if col.get("heading"):
            items.append((col["heading"], "h", col.get("color") or "accent"))
        for it in as_list(col.get("items")):
            if isinstance(it, str):
                items.append((it, "b", None))
            else:
                items.append((it["text"], {"plain": "p", "heading": "h"}.get(it.get("style"), "b"), it.get("color")))
        return items

    def column(self, col, left, top, width, height, size, name):
        tf = self.text_box(left, top, width, height, name)
        sizes = []
        for i, (text, kind, col_name) in enumerate(self.column_items(col)):
            sz, after = (size + 2, 8) if kind == "h" else (size, 5)
            p = self.write(tf, i, [(text, sz, kind == "h", self.rgb(col_name, "text"))], after)
            sizes.append((text, sz, after))
            if kind == "b":
                ppr = p._p.get_or_add_pPr()
                ppr.set("marL", str(Pt(16)))
                ppr.set("indent", str(-Pt(16)))
                ppr.append(parse_xml(BULLET))
        self.check(name, sizes, width - 16, height)

    def columns(self, left, right, top, height, size):
        if right:
            w = (self.width - COLUMN_GAP) / 2
            self.column(left or {}, self.left, top, w, height, size, "Left")
            self.column(right, self.left + w + COLUMN_GAP, top, w, height, size, "Right")
        elif left:
            self.column(left, self.left, top, self.width, height, size, "Body")

    def shape(self, kind, left, top, width, height, fill, name, radius=None):
        s = self.slide.shapes.add_shape(kind, Pt(left), Pt(top), Pt(width), Pt(height))
        s.name = name
        s.fill.solid()
        s.fill.fore_color.rgb = fill
        s.line.fill.background()
        s._element.remove(s._element.find(qn("p:style")))   # no theme shadow or font color
        if radius:
            s.adjustments[0] = radius
        s.text_frame.word_wrap = True
        s.text_frame.margin_left = s.text_frame.margin_right = Pt(12)
        return s

    def note(self, sl, top=None):
        """Call-out box at the bottom of the body; text before the first ':' is bold."""
        text = sl.get("note")
        if not text:
            return
        s = self.shape(MSO_SHAPE.ROUNDED_RECTANGLE, self.left, top or self.note_top, self.width, NOTE_H, self.rgb("light"), "Note", 0.12)
        s.text_frame.vertical_anchor = MSO_ANCHOR.MIDDLE
        colon = text.find(":")
        cut = colon + 1 if 0 < colon < 40 else 0
        runs = [(t, 14, bold, self.rgb("text")) for t, bold in ((text[:cut], True), (text[cut:], False)) if t]
        self.write(s.text_frame, 0, runs)
        self.check("Note", [(text, 14, 0)], self.width - 24, NOTE_H)

    # ---- slide types ----
    def cover(self, sl):
        self.new("cover")
        self.fill_placeholders("cover", title="\v".join(as_list(sl.get("title"))), subtitle="\n".join(as_list(sl.get("subtitle"))))

    def divider(self, sl):
        self.new("divider")
        self.fill_placeholders("divider", title=sl["title"])

    def closing(self, sl):
        self.new("closing")
        self.fill_placeholders("closing", title=sl.get("title") or "Thank you")

    def two_column(self, sl):
        self.content(sl["title"])
        self.columns(sl.get("left"), sl.get("right"), self.top, self.body_bottom(sl) - self.top, sl.get("size", 14))
        self.note(sl)

    def bullets(self, sl):
        self.content(sl["title"])
        self.columns(sl.get("left") or sl, None, self.top, self.body_bottom(sl) - self.top, sl.get("size", 14))
        self.note(sl)

    def table(self, sl):
        size, rows, row_h = sl.get("size", 13), sl["rows"], sl.get("rowHeight", 32)
        widths = sl.get("widths") or [1] * len(rows[0])
        col_w = [self.width * w / sum(widths) for w in widths]
        bold_first = sl.get("boldFirstColumn", True)
        head_fill, head_text = self.rgb(self.map.get("tableHeader"), "primary"), self.rgb(self.map.get("tableHeaderText"), "white")
        self.content(sl["title"])
        frame = self.slide.shapes.add_table(len(rows), len(widths), Pt(self.left), Pt(self.top), Pt(self.width), Pt(row_h * len(rows)))
        frame.name = "Table"
        tb = frame.table
        for c, w in enumerate(col_w):
            tb.columns[c].width = Pt(w)
        height = 0
        for r, cells in enumerate(rows):
            tb.rows[r].height = Pt(row_h)
            lines = 1
            for c, w in enumerate(col_w):
                text = str(cells[c]) if c < len(cells) else ""
                cell = tb.cell(r, c)
                cell.margin_top = cell.margin_bottom = Pt(4)
                cell.vertical_anchor = MSO_ANCHOR.MIDDLE
                cell.fill.solid()
                cell.fill.fore_color.rgb = head_fill if r == 0 else self.rgb("white" if r % 2 else "light")
                self.write(cell.text_frame, 0, [(text, size, r == 0 or (c == 0 and bold_first), head_text if r == 0 else self.rgb("text"))])
                lines = max(lines, math.ceil(len(text) / max(1, int((w - 15) / (size * 0.5)))))
            height += max(row_h, lines * size * 1.2 + 8)
        bottom = self.top + height
        if sl.get("note"):
            top = max(self.note_top, bottom + 12)
            self.note(sl, top)
            bottom = top + NOTE_H
        if bottom > self.bottom + 5:
            self.warn(f"table/note ends near {bottom:.0f}pt, below the body area ({self.bottom}pt). Split rows across slides or reduce size/rowHeight")

    def flow(self, sl):
        """A row of colored process boxes with arrows, two bullet columns below."""
        self.content(sl["title"])
        steps, gap, top, height = sl["steps"], 21, self.top + 10, 105
        w = (self.width - gap * (len(steps) - 1)) / len(steps)
        for i, st in enumerate(steps):
            x = self.left + i * (w + gap)
            s = self.shape(MSO_SHAPE.ROUNDED_RECTANGLE, x, top, w, height, self.rgb(st.get("color"), "primary"), f"Step {i + 1}", 0.12)
            tf = s.text_frame
            tf.vertical_anchor = MSO_ANCHOR.TOP
            tf.margin_top = Pt(10)
            parts = [p for p in ((st.get("num"), 20, True), (st.get("title"), 14, True), (st.get("text"), 12, False)) if p[0]]
            for j, (text, size, bold) in enumerate(parts):
                self.write(tf, j, [(text, size, bold, self.rgb("white"))])
            self.check(f"Step {i + 1}", [(str(t), sz, 0) for t, sz, _ in parts], w - 24, height - 14)
            if i < len(steps) - 1:
                self.shape(MSO_SHAPE.RIGHT_ARROW, x + w + 4, top + 45, 13, 14, self.rgb("arrow"), "Arrow")
        below = self.top + 137
        self.columns(sl.get("left"), sl.get("right"), below, self.body_bottom(sl) - below, sl.get("size", 13))
        self.note(sl)

    def icon_grid(self, sl):
        """Grid of rounded color boxes with a white PNG icon, a bold title and short text beside each."""
        self.content(sl["title"])
        items, cols, size = sl["items"], int(sl.get("columns", 3)), sl.get("size", 13)
        n_rows, gx, gy, top = math.ceil(len(items) / cols), 24, 16, self.top + 5
        cw = (self.width - gx * (cols - 1)) / cols
        # Cap the row height so a short grid stays compact at the top of the body.
        rh = min(112, (self.body_bottom(sl) - top - gy * (n_rows - 1)) / n_rows)
        box = min(54, rh - 6)
        pad = round(box * 0.2)
        for i, it in enumerate(items):
            x, y = self.left + (i % cols) * (cw + gx), top + (i // cols) * (rh + gy)
            self.shape(MSO_SHAPE.ROUNDED_RECTANGLE, x, y, box, box, self.rgb(sl.get("color"), "primary"), f"Icon Box {i + 1}", 0.22)
            if it.get("icon"):
                icon = abs_path(it["icon"])
                if icon.exists():
                    self.slide.shapes.add_picture(str(icon), Pt(x + pad), Pt(y + pad), Pt(box - 2 * pad), Pt(box - 2 * pad))
                else:
                    self.warn(f"icon not found: {icon}")
            tw = cw - box - 12
            tf = self.text_box(x + box + 12, y - 3, tw, rh + 3, f"Item {i + 1}")
            parts = [p for p in ((it.get("title"), size + 2, True, "primary"), (it.get("text"), size, False, "text")) if p[0]]
            for j, (text, sz, bold, col) in enumerate(parts):
                self.write(tf, j, [(text, sz, bold, self.rgb(col))], 3 if bold else 0)
            self.check(f"Item {i + 1}", [(t, sz, 3) for t, sz, _, _ in parts], tw, rh)
        self.note(sl)

    def image(self, sl):
        """One picture, scaled proportionally into the body area; optional crop, caption and note."""
        self.content(sl["title"])
        path = abs_path(sl["image"])
        if not path.exists():
            raise SystemExit(f"Slide {self.n}: image not found: {path}")
        pic = self.slide.shapes.add_picture(str(path), 0, 0)
        pic.name = "Image"
        cut = {side: (sl.get("crop") or {}).get(side, 0) for side in ("left", "right", "top", "bottom")}
        pic.crop_left, pic.crop_right, pic.crop_top, pic.crop_bottom = cut["left"], cut["right"], cut["top"], cut["bottom"]
        w = Emu(pic.width).pt * (1 - cut["left"] - cut["right"])
        h = Emu(pic.height).pt * (1 - cut["top"] - cut["bottom"])
        area = self.body_bottom(sl) - self.top - (22 if sl.get("caption") else 0)
        k = min(self.width / w, area / h)
        w, h = w * k, h * k
        pic.width, pic.height = Pt(w), Pt(h)
        pic.left, pic.top = Pt(self.left + (self.width - w) / 2), Pt(self.top + (area - h) / 2)
        if sl.get("caption"):
            tf = self.text_box(self.left, self.top + (area + h) / 2 + 2, self.width, 20, "Caption")
            self.write(tf, 0, [(sl["caption"], 12, False, self.rgb("text"))], align=PP_ALIGN.CENTER).runs[0].font.italic = True
        self.note(sl)

    TYPES = {"cover": cover, "divider": divider, "closing": closing, "two-column": two_column, "bullets": bullets,
             "table": table, "flow": flow, "icon-grid": icon_grid, "image": image}

    def build(self, slides):
        for sl in slides:
            self.n += 1
            kind = sl.get("type")
            if kind not in self.TYPES:
                raise SystemExit(f"Slide {self.n}: unknown type '{kind}'. Types: {', '.join(self.TYPES)}")
            self.TYPES[kind](self, sl)
            if sl.get("notes"):
                self.slide.notes_slide.notes_text_frame.text = sl["notes"]


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("spec")
    ap.add_argument("--out")
    ap.add_argument("--theme")
    a = ap.parse_args()
    cfg = load_json(a.spec)
    out = output_path(a.out, cfg)
    deck = Deck(cfg, load_theme(a.theme or cfg.get("theme")))
    deck.build(cfg["slides"])
    deck.prs.save(str(out))
    print("OUTPUT:", out)
    print("SLIDES:", deck.n)
    for w in deck.warnings:
        print("WARNING:", w)
    if not deck.warnings:
        print("WARNINGS: none")


if __name__ == "__main__":
    main()
