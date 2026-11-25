# Reference index

Map of `references/`, one line per file. Claude reads this first, then only the relevant files in
`distilled/`. Files in `raw/` are opened only when processing new references or on request.

## How to use

1. Put originals in `raw/` (not in git): `raw/<topic>/`, `raw/images/<topic>/`, `raw/videos/<topic>/`.
2. Tell Claude: "process new references".
3. Claude reads each new file once and writes or updates a summary in `distilled/` and the tables below.
4. Feedback ("remember this", "don't do that") goes in the *Rules* section of the matching `distilled/` file.

⭐ = best example; follow it before other samples.

Assets used in output are not references: icons go in `templates/icons/`, brand assets in `brands/<brand>/`.

## Tools

| Tool | For | Result |
|---|---|---|
| `tools/video_study.sh <video>` | Video | `distilled/videos/<name>/` |
| `tools/image_sheet.sh <folder>` | Images/icons | `distilled/sheets/<folder>.png` and a file order list |

## Summaries (distilled/)

| File | Content | Used for | Source (raw) | Updated |
|---|---|---|---|---|
| _(none yet)_ | | | | |

## Studied videos (distilled/videos/)

| Folder | Video | Format | Gist (one sentence) | ⭐ |
|---|---|---|---|---|
| _(none yet)_ | | | | |

## Raw files (raw/)

| File | Content | Processed? |
|---|---|---|
| _(none yet)_ | | |
