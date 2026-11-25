# Document builders

Build branded slide decks (.pptx) and Word documents (.docx) from a JSON spec. The theme names the template
and maps its layouts and styles, so logos, fonts, header and footer come from the template. Runs on Windows,
macOS and Linux with [uv](https://docs.astral.sh/uv/); Microsoft Office is not needed.

```sh
uv run tools/docs/build_deck.py tools/docs/examples/weekly-report-deck.json
uv run tools/docs/build_doc.py  tools/docs/examples/weekly-report-doc.json
```

Both accept `--out <path>` and `--theme <path>`. Paths in specs and themes are relative to the repo root.
Keep your own specs in `tools/docs/specs/` (not in git). The output file is replaced if it exists.
The deck builder prints `WARNING:` lines for text that probably does not fit; this is an estimate, so also
look at the result (`soffice --headless --convert-to pdf <file>` with LibreOffice, or open it).

## Theme

Used in this order: `--theme`, `"theme"` in the spec, `templates/theme.local.json` (yours, not in git),
`templates/theme.json` (neutral default).

| Key | Meaning |
|---|---|
| `identity` | `organization`, `logo`, `logoDark` (PNG/JPG). Only used by `make_templates.py`. |
| `fonts`, `colors` | `colors` are the names specs can use; `primary`, `accent`, `text`, `light`, `white`, `arrow` are required |
| `deck.template` | The .pptx file |
| `deck.cover/divider/content/closing` | `layout` (name or index) and the placeholder index of `title` (and `subtitle` on the cover) |
| `deck.body` | Free area of a content slide in points: `left`, `top`, `width`, `bottom` (a 16:9 slide is 960 × 540) |
| `doc.template`, `doc.styles` | The .docx file and its style names; a missing style falls back to Normal |
| `doc.labelFill`, `headerFill`, `headerText` | Table colors |

### No company template

Copy `templates/theme.json` to `templates/theme.local.json`, change `identity`, `colors` and `fonts`, point
both `template` paths into `templates/private/`, then run `uv run tools/docs/make_templates.py`.

### Use your own template

1. Put the .pptx/.docx in `templates/private/` (not in git).
2. List the layouts and placeholders:

   ```sh
   uv run --with python-pptx==1.0.2 python -c "import sys; from pptx import Presentation; [print(repr(l.name), [(p.placeholder_format.idx, p.name, round(p.left.pt), round(p.top.pt), round(p.width.pt), round(p.height.pt)) for p in l.placeholders]) for l in Presentation(sys.argv[1]).slide_layouts]" "templates/private/My Deck.pptx"
   ```

3. Copy `templates/theme.json` to `templates/theme.local.json` and fill the `deck` map: pick a cover, a
   section, a title-only and a closing layout, and set `body` to the free area below the title.
4. For Word, set `doc.styles` to the style names in your document.
5. Branding must be in the slide layouts or master. Slides already in the file are dropped; pictures that
   exist only on those slides are not carried over.

## Deck spec

```json
{ "output": "documents/Weekly Report.pptx", "slides": [ { "type": "cover", "title": "Weekly Report" } ] }
```

| `type` | Fields |
|---|---|
| `cover` | `title`, `subtitle` (string or array of lines) |
| `divider` | `title` |
| `two-column` | `title`, `left`, `right`, `size` (default 14), `note` |
| `bullets` | `title`, `heading`, `color`, `items`, `size`, `note` |
| `table` | `title`, `rows` (first row = header), `widths` (relative), `size` (13), `rowHeight` (32), `boldFirstColumn` (true), `note` |
| `flow` | `title`, `steps` [{`num`,`title`,`text`,`color`}] (3–6), `left`, `right`, `size`, `note` |
| `icon-grid` | `title`, `items` [{`icon`,`title`,`text`}], `columns` (3), `color`, `size` (13), `note` |
| `image` | `title`, `image`, `crop`, `caption`, `note` |
| `closing` | `title` (default "Thank you") |

- Every slide may have `notes` (speaker notes).
- **Column** (`left`/`right`): `{ "heading": "Pros", "color": "blue", "items": ["bullet", { "text": "no bullet", "style": "plain" }, { "text": "Sub-heading", "style": "heading", "color": "red" }] }`
- **`note`**: call-out at the bottom; text before the first `:` is bold.
- **`icon`**: square PNG, transparent background, white strokes. Title ~25 characters, text ~2 lines.
- **`crop`**: fractions cut from each side, `{ "top": 0.15, "bottom": 0.15 }`.
- **Colors**: a name from the theme's `colors`, or hex `"RRGGBB"`.
- Fit guide: ~6–7 two-line bullets per column at size 14; ~8 table rows; titles up to ~45 characters.

## Document spec

```json
{ "output": "outputs/Monthly Report.docx", "blocks": [ { "type": "heading", "level": 1, "text": "Monthly Report" } ] }
```

| `type` | Fields |
|---|---|
| `heading` | `level` (1–3), `text` |
| `paragraph` | `text` |
| `bullets` / `numbered` | `items` |
| `info` | `rows` (key/value grid), `labelColumns` (default `[1,3]`, shaded), `widths` (relative) |
| `table` | `header`, `rows`, `widths` (relative) |
| `pagebreak` | – |

The default template's footer shows the file name, so name the output the way it should appear.
