"""Shared by the builders: paths, theme loading, colors."""

import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def abs_path(p):
    p = Path(p)
    return p if p.is_absolute() else ROOT / p


def load_json(path):
    return json.loads(Path(path).read_text(encoding="utf-8-sig"))


def load_theme(path=None):
    """The given theme, else templates/theme.local.json (yours, not in git), else templates/theme.json."""
    if not path:
        path = "templates/theme.local.json"
        if not abs_path(path).exists():
            path = "templates/theme.json"
    return load_json(abs_path(path))


def color(theme, name, default=None):
    """Theme color name or hex RRGGBB -> 'RRGGBB'."""
    name = name or default
    value = theme["colors"].get(name, name).lstrip("#")
    if not re.fullmatch(r"[0-9A-Fa-f]{6}", value):
        raise SystemExit(f"Unknown color '{name}': not in the theme's colors and not a hex RRGGBB")
    return value.upper()


def output_path(arg, cfg):
    out = arg or cfg.get("output")
    if not out:
        raise SystemExit("No output path: pass --out or set 'output' in the spec.")
    out = abs_path(out)
    out.parent.mkdir(parents=True, exist_ok=True)
    return out
