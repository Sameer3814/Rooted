#!/usr/bin/env python3
"""
parse_strongs_dictionary.py — the OpenScriptures JSON re-encoding of James
Strong's public-domain 1890/1894 Hebrew and Greek dictionaries ->
data/lexicon_full.json, a single Strong's-id-keyed lexicon covering (nearly)
every Hebrew and Greek word in the Bible.

Source: https://github.com/openscriptures/strongs (hebrew/strongs-hebrew-
dictionary.js, greek/strongs-greek-dictionary.js). Strong's own dictionary
text is public domain; OpenScriptures' JSON re-encoding of it is licensed
CC BY-SA — a real, different situation from the raw 1890s text, the same
attribution + share-alike shape as the Telugu Bible source
(parse_telugu_bible.py). Keep the attribution line in this file's own
docstring and in CLAUDE.md's provenance section intact whenever this is
re-run.

This is deliberately a SEPARATE, much larger file from data/lexicon_seed.json
(item 150) rather than a replacement of it — lexicon_seed.json stays as a
small, hand-curated set of ~39 well-known words with richer editorial
fields (occurrences, part-of-speech type, a real linked example verse from
this app's own curated content) that the raw dictionary doesn't carry.
data/lexicon_full.json is the broad, lazily-loaded base (~14,300 entries,
mirroring the corpus/data.verses split already established for
data/verses.json vs data/starter-pack.json) — the app overlays
lexicon_seed.json's richer entries on top of it by id at render time, the
same seed-plus-overlay pattern used everywhere else in this codebase.

Each source file is a JS file assigning a bare object literal to a
variable (`var strongsHebrewDictionary = {...};`) rather than a JSON
document on its own — this script strips the `var NAME = ` prefix and the
trailing `;` and parses the remainder as JSON directly (it already is
valid JSON once isolated, verified against both files before writing this
comment).

Usage
-----
    py pipeline/parse_strongs_dictionary.py
    py pipeline/parse_strongs_dictionary.py --out data/lexicon_full.json --indent 2
"""

import argparse
import json
import os
import re
import sys
import urllib.request

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CACHE_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".cache")
DEFAULT_OUT = os.path.join(REPO_ROOT, "data", "lexicon_full.json")

SOURCES = {
    "Hebrew": (
        "https://raw.githubusercontent.com/openscriptures/strongs/master/hebrew/strongs-hebrew-dictionary.js",
        "strongs-hebrew-dictionary.js",
        "strongsHebrewDictionary",
    ),
    "Greek": (
        "https://raw.githubusercontent.com/openscriptures/strongs/master/greek/strongs-greek-dictionary.js",
        "strongs-greek-dictionary.js",
        "strongsGreekDictionary",
    ),
}

ASSIGN_START_RE = re.compile(r"var\s+\w+\s*=\s*")


def fetch(url, cache_dir, cache_name):
    os.makedirs(cache_dir, exist_ok=True)
    cached = os.path.join(cache_dir, cache_name)
    if not os.path.exists(cached):
        print("  downloading %s" % url, file=sys.stderr)
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=120) as resp:
            payload = resp.read()
        with open(cached, "wb") as fh:
            fh.write(payload)
    with open(cached, encoding="utf-8") as fh:
        return fh.read()


def strip_html(s):
    """Strong's def/derivation fields carry stray {curly-brace cross-refs}
    and the occasional HTML entity from the XML->JSON conversion; keep the
    text but drop the outer braces since they're not meaningful markup
    here, just how the source denotes a cross-reference gloss."""
    if not s:
        return s
    s = s.replace("&nbsp;", " ")
    return re.sub(r"\s+", " ", s).strip()


def first_clause(s, limit=60):
    if not s:
        return ""
    s = strip_html(s)
    cut = re.split(r"[;,.]", s, maxsplit=1)[0].strip()
    if len(cut) > limit:
        cut = cut[:limit].rsplit(" ", 1)[0] + "…"
    return cut or s[:limit]


def parse_language(raw_text, var_name, language):
    m = ASSIGN_START_RE.search(raw_text)
    if not m:
        raise SystemExit("could not find `var %s = {...}` in the source file" % var_name)
    # Everything from the opening `{` to the object's own matching closing
    # `}` — found by brace-counting rather than a regex, since the two
    # source files close the literal differently (one on its own line,
    # the other packed onto the same line as `module.exports = ...`) and
    # neither shape survives a single regex reliably once string values
    # can themselves contain braces.
    # Some entries legitimately contain literal "{"/"}" inside their own
    # string values (e.g. H2's strongs_def is "{father}", a cross-
    # reference gloss) — so brace-counting has to track JSON string
    # context (quotes, and backslash-escapes inside them) rather than
    # just counting braces blindly.
    body = raw_text[m.end():]
    depth = 0
    end = None
    in_string = False
    escaped = False
    for i, ch in enumerate(body):
        if in_string:
            if escaped:
                escaped = False
            elif ch == "\\":
                escaped = True
            elif ch == '"':
                in_string = False
            continue
        if ch == '"':
            in_string = True
        elif ch == "{":
            depth += 1
        elif ch == "}":
            depth -= 1
            if depth == 0:
                end = i + 1
                break
    if end is None:
        raise SystemExit("could not find the closing brace for %s" % var_name)
    obj = json.loads(body[:end])
    out = {}
    for sid, entry in obj.items():
        definition = strip_html(entry.get("strongs_def") or entry.get("kjv_def") or "")
        origin = strip_html(entry.get("derivation") or "")
        # strongs_def's own first clause, not kjv_def's — kjv_def just
        # lists every King James rendering (often alphabetized), so its
        # first entry ("angels" for H430/Elohim) isn't a meaningful
        # summary the way strongs_def's own lead clause is.
        short_def = first_clause(definition or entry.get("kjv_def"))
        out[sid] = {
            "id": sid,
            "language": language,
            "lemma": entry.get("lemma", ""),
            "translit": entry.get("xlit") or entry.get("translit") or "",
            "pronunciation": entry.get("pron") or "",
            "definition": definition or short_def,
            "shortDef": short_def,
            "origin": origin,
        }
    return out


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--cache-dir", default=CACHE_DIR)
    ap.add_argument("--out", default=DEFAULT_OUT)
    ap.add_argument("--indent", type=int, default=None)
    args = ap.parse_args()

    merged = {}
    for language, (url, cache_name, var_name) in SOURCES.items():
        raw_text = fetch(url, args.cache_dir, cache_name)
        entries = parse_language(raw_text, var_name, language)
        print("  %-8s %5d entries" % (language, len(entries)), file=sys.stderr)
        merged.update(entries)

    os.makedirs(os.path.dirname(os.path.abspath(args.out)), exist_ok=True)
    with open(args.out, "w", encoding="utf-8") as fh:
        json.dump(merged, fh, ensure_ascii=False, indent=args.indent, sort_keys=True)
    print("wrote %d entries -> %s" % (len(merged), args.out), file=sys.stderr)


if __name__ == "__main__":
    main()
