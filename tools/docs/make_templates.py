# /// script
# requires-python = ">=3.10"
# dependencies = ["python-pptx==1.0.2", "python-docx==1.2.0"]
# ///
"""Generate a plain deck and document template from a theme: its colors, fonts, name and logo.

Use it when you have no company template of your own.

  uv run tools/docs/make_templates.py [--theme templates/theme.local.json] [--force]
"""

import argparse
import datetime
import re
from xml.sax.saxutils import escape

import docx
from docx.enum.style import WD_STYLE_TYPE
from docx.enum.text import WD_TAB_ALIGNMENT
from docx.oxml import parse_xml as docx_xml
from docx.oxml.ns import qn
from docx.shared import Pt, RGBColor
from pptx import Presentation
from pptx.dml.color import RGBColor as PRGB
from pptx.oxml import parse_xml
from pptx.oxml.ns import qn as pqn
from pptx.util import Pt as PPt

from theme import abs_path, color, load_theme

NS = ('xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main" '
      'xmlns:p="http://schemas.openxmlformats.org/presentationml/2006/main" '
      'xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships"')
W_NS = 'xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main"'


def blank_properties(props):
    props.author = props.last_modified_by = props.comments = props.title = props.keywords = ""
    props.created = props.modified = datetime.datetime(2026, 1, 1)


def frame(shape, left, top, width, height):
    shape.left, shape.top, shape.width, shape.height = PPt(left), PPt(top), PPt(width), PPt(height)


def text_style(shape, size, rgb, anchor, bold):
    """Text defaults of a layout placeholder; slides inherit them."""
    body = shape._element.txBody
    pr = body.find(pqn("a:bodyPr"))
    for child in list(pr):
        pr.remove(child)
    for k, v in (("anchor", anchor), ("lIns", "0"), ("rIns", "0")):
        pr.set(k, v)
    body.replace(body.find(pqn("a:lstStyle")), parse_xml(
        f'<a:lstStyle {NS}><a:lvl1pPr marL="0" indent="0" algn="l"><a:buNone/>'
        f'<a:defRPr sz="{size * 100}" b="{int(bold)}" cap="none"><a:solidFill><a:srgbClr val="{rgb}"/></a:solidFill></a:defRPr>'
        f"</a:lvl1pPr></a:lstStyle>"))


def box_xml(tree, name, left, top, width, height, fill, text):
    return parse_xml(
        f'<p:sp {NS}><p:nvSpPr><p:cNvPr id="{900 + len(tree)}" name="{name}"/><p:cNvSpPr/><p:nvPr userDrawn="1"/></p:nvSpPr>'
        f'<p:spPr><a:xfrm><a:off x="{PPt(left)}" y="{PPt(top)}"/><a:ext cx="{PPt(width)}" cy="{PPt(height)}"/></a:xfrm>'
        f'<a:prstGeom prst="rect"><a:avLst/></a:prstGeom>{fill}<a:ln><a:noFill/></a:ln></p:spPr>'
        f'<p:txBody><a:bodyPr lIns="0" wrap="square"/><a:lstStyle/><a:p>{text}</a:p></p:txBody></p:sp>')


def bar(layout, left, top, width, height, rgb):
    tree = layout.shapes._spTree
    fill = f'<a:solidFill><a:srgbClr val="{rgb}"/></a:solidFill>'
    tree.insert(2, box_xml(tree, "Bar", left, top, width, height, fill, '<a:endParaRPr lang="en-US"/>'))


def brand(layout, left, top, rgb, organization, logo):
    tree = layout.shapes._spTree
    if logo:
        image, rid = layout.part.get_or_add_image_part(str(abs_path(logo)))
        w, h = image.scale(None, PPt(22))
        tree.append(parse_xml(
            f'<p:pic {NS}><p:nvPicPr><p:cNvPr id="{900 + len(tree)}" name="Logo"/><p:cNvPicPr/><p:nvPr userDrawn="1"/></p:nvPicPr>'
            f'<p:blipFill><a:blip r:embed="{rid}"/><a:stretch><a:fillRect/></a:stretch></p:blipFill>'
            f'<p:spPr><a:xfrm><a:off x="{PPt(left)}" y="{PPt(top)}"/><a:ext cx="{w}" cy="{h}"/></a:xfrm>'
            f'<a:prstGeom prst="rect"><a:avLst/></a:prstGeom></p:spPr></p:pic>'))
    elif organization:
        run = (f'<a:r><a:rPr lang="en-US" sz="1200"><a:solidFill><a:srgbClr val="{rgb}"/></a:solidFill></a:rPr>'
               f"<a:t>{escape(organization)}</a:t></a:r>")
        tree.append(box_xml(tree, "Organization", left, top, 500, 22, "<a:noFill/>", run))


def background(layout, rgb):
    layout.background.fill.solid()
    layout.background.fill.fore_color.rgb = PRGB.from_string(rgb)


def make_deck(theme, out):
    def c(name):
        return color(theme, name)

    ident = theme["identity"]
    org, logo = ident.get("organization", ""), ident.get("logo")
    logo_dark = ident.get("logoDark") or logo
    prs = Presentation()
    prs.slide_width, prs.slide_height = PPt(960), PPt(540)

    layouts = prs.slide_layouts
    cover, divider, content, closing = layouts[0], layouts[2], layouts[5], layouts[1]
    for layout in list(layouts):
        if layout not in (cover, divider, content, closing):
            layouts.remove(layout)

    # Theme colors and fonts
    master = prs.slide_master
    part = next(r.target_part for r in master.part.rels.values() if r.reltype.endswith("/theme"))
    xml = part.blob.decode("utf-8")
    for slot, name in {"dk2": "primary", "accent1": "primary", "accent2": "accent", "accent3": "green",
                       "accent4": "orange", "accent5": "red", "accent6": "grey"}.items():
        xml = re.sub(rf"(<a:{slot}>).*?(</a:{slot}>)", rf'\g<1><a:srgbClr val="{c(name)}"/>\g<2>', xml, flags=re.S)
    for slot, name in {"majorFont": "heading", "minorFont": "body"}.items():
        xml = re.sub(rf'(<a:{slot}>\s*<a:latin typeface=")[^"]*', rf"\g<1>{escape(theme['fonts'][name])}", xml)
    part._blob = xml.encode("utf-8")

    for ph in list(master.placeholders):   # title and body inside the 16:9 slide; no date/footer/number
        if ph.placeholder_format.idx == 0:
            frame(ph, 50, 38, 860, 48)
        elif ph.placeholder_format.idx == 1:
            frame(ph, 50, 112, 860, 378)
        else:
            ph._element.getparent().remove(ph._element)

    titles = {}
    for name, layout in (("Cover", cover), ("Divider", divider), ("Content", content), ("Closing", closing)):
        layout.name = name
        for ph in list(layout.placeholders):
            idx = ph.placeholder_format.idx
            if idx == 0:
                titles[name] = ph
            elif name == "Cover" and idx == 1:
                subtitle = ph
            else:
                ph._element.getparent().remove(ph._element)

    background(cover, c("primary"))
    frame(titles["Cover"], 60, 140, 800, 160)
    text_style(titles["Cover"], 44, c("white"), "b", True)
    frame(subtitle, 60, 326, 800, 80)
    text_style(subtitle, 18, c("white"), "t", False)
    bar(cover, 60, 310, 90, 4, c("accent"))
    brand(cover, 60, 478, c("white"), org, logo_dark)

    frame(titles["Divider"], 82, 200, 800, 140)
    text_style(titles["Divider"], 40, c("primary"), "ctr", True)
    bar(divider, 50, 200, 8, 140, c("accent"))

    frame(titles["Content"], 50, 38, 860, 48)
    text_style(titles["Content"], 28, c("primary"), "ctr", True)
    bar(content, 50, 90, 60, 3, c("accent"))
    brand(content, 50, 506, c("grey"), org, logo)

    background(closing, c("primary"))
    frame(titles["Closing"], 60, 190, 840, 140)
    text_style(titles["Closing"], 44, c("white"), "ctr", True)
    brand(closing, 60, 478, c("white"), org, logo_dark)

    blank_properties(prs.core_properties)
    prs.save(out)


def set_font(style, name, size, rgb=None, bold=None):
    style.font.name, style.font.size = name, Pt(size)
    fonts = style.element.get_or_add_rPr().get_or_add_rFonts()
    for a in list(fonts.attrib):
        if "Theme" in a:
            del fonts.attrib[a]
    for a in ("w:ascii", "w:hAnsi", "w:cs", "w:eastAsia"):
        fonts.set(qn(a), name)
    if rgb:
        style.font.color.rgb = RGBColor.from_string(rgb)
    if bold is not None:
        style.font.bold = bold


def make_doc(theme, out):
    st = theme["doc"]["styles"]
    d = docx.Document()
    sec = d.sections[0]
    sec.page_width, sec.page_height = Pt(595.3), Pt(841.9)   # A4
    sec.top_margin, sec.bottom_margin = Pt(72), Pt(64)
    sec.left_margin = sec.right_margin = Pt(64)

    body_font, head_font = theme["fonts"]["body"], theme["fonts"]["heading"]
    set_font(d.styles["Normal"], body_font, 11)
    d.styles[st["body"]].paragraph_format.space_after = Pt(6)
    for i, size in enumerate((20, 15, 12), 1):
        s = d.styles[st[f"heading{i}"]]
        set_font(s, head_font, size, color(theme, "primary"), True)
        s.paragraph_format.space_before, s.paragraph_format.space_after = Pt(12), Pt(6)
    for key in ("tableHeader", "tableText"):
        s = d.styles.add_style(st[key], WD_STYLE_TYPE.PARAGRAPH)
        s.base_style = d.styles["Normal"]
        set_font(s, body_font, 10, bold=True if key == "tableHeader" else None)
        s.paragraph_format.space_before = s.paragraph_format.space_after = Pt(2)

    head = sec.header.paragraphs[0]
    if theme["identity"].get("logo"):
        head.add_run().add_picture(str(abs_path(theme["identity"]["logo"])), height=Pt(24))
    else:
        run = head.add_run(theme["identity"].get("organization", ""))
        run.font.size, run.font.color.rgb = Pt(9), RGBColor.from_string(color(theme, "grey"))

    foot = sec.footer.paragraphs[0]
    set_font(foot.style, body_font, 9, color(theme, "grey"))
    stops = foot.style.paragraph_format.tab_stops
    stops.clear_all()
    stops.add_tab_stop(sec.page_width - sec.left_margin - sec.right_margin, WD_TAB_ALIGNMENT.RIGHT)

    def field(code):
        foot._p.append(docx_xml(f'<w:fldSimple {W_NS} w:instr=" {code} "><w:r><w:t>1</w:t></w:r></w:fldSimple>'))

    field("FILENAME")
    foot.add_run("\t")
    field("PAGE")
    blank_properties(d.core_properties)
    d.save(out)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--theme")
    ap.add_argument("--force", action="store_true", help="replace existing template files")
    a = ap.parse_args()
    theme = load_theme(a.theme)
    for kind, make in (("deck", make_deck), ("doc", make_doc)):
        out = abs_path(theme[kind]["template"])
        if out.exists() and not a.force:
            raise SystemExit(f"{out} exists. Pass --force to replace it.")
        out.parent.mkdir(parents=True, exist_ok=True)
        make(theme, str(out))
        print("TEMPLATE:", out)


if __name__ == "__main__":
    main()
