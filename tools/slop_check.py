#!/usr/bin/env python3
"""Anti-slop linter for marketing copy.

Flags the patterns that make text read as generic AI output, plus the brand's
own rules from brands/<brand>/lexicon.json.

Usage:
  slop_check.py --brand example FILE...     check files (md, txt, json, tsx)
  echo "text" | slop_check.py --brand example -

Exit status: 0 clean, 2 findings (errors), 1 usage error. Warnings alone exit 0.
Standard library only.
"""

import argparse
import json
import os
import re
import sys
import unicodedata

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Words and phrases that mark generic AI copy. Lower case; matched on word
# boundaries. Extend in ANTI-SLOP.md and here together, or per brand in lexicon.json.
BANNED = [
    "delve", "delves", "delving", "tapestry", "testament to", "realm",
    "unleash", "unlock the power", "unlock your", "elevate your", "supercharge",
    "game-changer", "game changer", "revolutionize", "revolutionise",
    "seamless", "seamlessly", "cutting-edge", "state-of-the-art", "next-level",
    "leverage", "synergy", "robust solution", "harness the power",
    "in today's fast-paced", "in today's digital", "ever-evolving", "ever-changing",
    "navigate the complexities", "navigating the", "embark on", "journey",
    "look no further", "whether you're", "say goodbye to", "say hello to",
    "it's not just", "not just a", "more than just", "dive in", "dive into",
    "let's dive", "buckle up", "picture this", "imagine a world",
    "transformative", "empower", "empowers", "empowering", "effortlessly",
    "boost productivity", "take it to the next level", "streamline your workflow",
    "all-in-one", "one-stop", "best-in-class", "world-class", "innovative",
    "crucial", "pivotal", "paramount", "meticulous", "meticulously",
    "in conclusion", "furthermore", "moreover", "additionally",
]

HIDDEN = (
    (0x00AD, 0x00AD), (0x061C, 0x061C), (0x115F, 0x1160), (0x180E, 0x180E),
    (0x200B, 0x200F), (0x202A, 0x202E), (0x2060, 0x2064), (0x2066, 0x2069),
    (0x3164, 0x3164), (0xFEFF, 0xFEFF), (0xFFA0, 0xFFA0), (0xE0000, 0xE007F),
)

EMOJI = re.compile("[\U0001F300-\U0001FAFF☀-➿]")


def load_lexicon(brand):
    if not brand:
        return {}
    path = os.path.join(ROOT, "brands", brand, "lexicon.json")
    try:
        with open(path, encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        sys.exit(f"slop_check: no lexicon at {path}")


def phrase_re(phrase):
    return re.compile(r"(?<![\w-])" + re.escape(phrase) + r"(?![\w-])", re.IGNORECASE)


def check_text(name, text, lex):
    errors, warnings = [], []
    banned = [b for b in BANNED if b not in lex.get("allow", [])] + lex.get("banned", [])
    patterns = [(b, phrase_re(b)) for b in banned]
    spell = {wrong: right for right, wrongs in lex.get("spellings", {}).items() for wrong in wrongs}
    rules = lex.get("rules", {})

    for n, line in enumerate(text.splitlines(), 1):
        where = f"{name}:{n}"
        for ch in line:
            cp = ord(ch)
            if any(lo <= cp <= hi for lo, hi in HIDDEN):
                errors.append(f"{where}: hidden character U+{cp:04X} {unicodedata.name(ch, '')}")
        for phrase, rx in patterns:
            if rx.search(line):
                errors.append(f'{where}: slop phrase "{phrase}"')
        for wrong, right in spell.items():
            if re.search(r"(?<!\w)" + re.escape(wrong) + r"(?!\w)", line):
                errors.append(f'{where}: write "{right}", not "{wrong}"')
        if "—" in line and not rules.get("allow_em_dash", False):
            errors.append(f"{where}: em dash; use a period, comma or colon")
        if "!" in re.sub(r"!\[|!=", "", line) and not rules.get("allow_exclamation", False):
            errors.append(f"{where}: exclamation mark")
        if EMOJI.search(line) and not rules.get("allow_emoji", False):
            warnings.append(f"{where}: emoji")
        if re.search(r"\b\w+, \w+,? and \w+\b", line):
            warnings.append(f"{where}: list of three; is each item real and specific?")
        if line.strip().endswith("?") and len(line.strip()) < 80:
            warnings.append(f"{where}: rhetorical-question opener; lead with the fact instead")
        max_words = rules.get("max_sentence_words")
        if max_words:
            for sent in re.split(r"(?<=[.?!])\s+", line):
                if len(sent.split()) > max_words:
                    warnings.append(f"{where}: sentence over {max_words} words")
    return errors, warnings


COPY_KEYS = {"hook", "text", "cta", "headline", "body", "eyebrow", "title", "caption", "sub", "label", "prompt", "reply", "note"}


def copy_fields(node):
    """For render specs, lint only the text people will read, not paths or ids."""
    if isinstance(node, dict):
        for k, v in node.items():
            if k in COPY_KEYS and isinstance(v, str):
                yield v
            else:
                yield from copy_fields(v)
    elif isinstance(node, list):
        for v in node:
            yield from copy_fields(v)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--brand")
    ap.add_argument("files", nargs="+")
    args = ap.parse_args()
    lex = load_lexicon(args.brand)
    all_errors, all_warnings = [], []
    for f in args.files:
        text = sys.stdin.read() if f == "-" else open(f, encoding="utf-8").read()
        if f.endswith(".json"):
            text = "\n".join(copy_fields(json.loads(text)))
        e, w = check_text(f, text, lex)
        all_errors += e
        all_warnings += w
    for line in all_errors:
        print("ERROR  " + line)
    for line in all_warnings:
        print("warn   " + line)
    if not all_errors and not all_warnings:
        print("clean")
    return 2 if all_errors else 0


if __name__ == "__main__":
    sys.exit(main())
