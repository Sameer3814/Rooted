#!/usr/bin/env python3
"""
parse_chapter_sections.py -- real paragraph boundaries from the WEB source
-> data/chapter_sections.json.

Source: the same TehShrike/world-english-bible per-book JSON parse_books.py
already downloads/caches (see that file's own docstring for the format).
Besides "paragraph text"/"line text" entries, the source also carries
"paragraph start" markers -- the WEB translation's own real literary
paragraph breaks, not an editorially-chosen study-Bible heading scheme
(which this project has no license or data source for, and won't guess at
-- see CLAUDE.md's standing "curated, not invented" rule). Shepherd's Path
(item 180) uses these as real sub-chapter unit boundaries when a user adds
a whole chapter to their practice library, instead of one lesson-sized unit
per chapter regardless of length.

Output
------
data/chapter_sections.json -- a flat object:
    { "Romans|1": [1, 8, 13, 22, 26], ... }
keyed by "{book}|{chapter}", each value the ascending list of verse numbers
where a new paragraph begins in that chapter (always starts with 1 -- every
chapter's first text entry is preceded by its own "paragraph start").
Chapters with no internal paragraph break at all (short chapters, a few
poetic ones) simply get a single-element list, [1] -- not an error, not
padded to look like more sections than the text actually has.

Usage
-----
    py pipeline/parse_chapter_sections.py                 # all 66 books
    py pipeline/parse_chapter_sections.py --books romans
    py pipeline/parse_chapter_sections.py --check          # dry run, exit 1 if data/chapter_sections.json would change
"""

import argparse
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from parse_books import BOOKS, DEFAULT_BOOKS, CACHE_DIR, fetch_book  # noqa: E402

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DEFAULT_OUT = os.path.join(REPO_ROOT, "data", "chapter_sections.json")


def chapter_sections(slug, entries):
    """book slug, raw entries -> {chapter: [verse, verse, ...]} real paragraph starts."""
    display = BOOKS[slug]
    out = {}
    pending_start = False
    for entry in entries:
        t = entry.get("type")
        if t == "paragraph start":
            pending_start = True
            continue
        if t not in ("paragraph text", "line text"):
            continue
        chapter, verse = entry.get("chapterNumber"), entry.get("verseNumber")
        if chapter is None or verse is None:
            continue
        bucket = out.setdefault(chapter, [])
        if pending_start or not bucket:
            if not bucket or bucket[-1] != verse:
                bucket.append(verse)
            pending_start = False
    return display, out


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--books", nargs="+", metavar="SLUG",
                    help="book slugs to parse (default: all 66)")
    ap.add_argument("--source-dir", help="read book JSON from here instead of downloading")
    ap.add_argument("--cache-dir", default=CACHE_DIR, help="where downloads are cached")
    ap.add_argument("--out", default=DEFAULT_OUT, help="output path")
    ap.add_argument("--indent", type=int, default=2, help="pretty-print indent (default: 2)")
    ap.add_argument("--check", action="store_true", help="dry run -- exit 1 if output would change")
    args = ap.parse_args()

    slugs = args.books or DEFAULT_BOOKS
    unknown = [s for s in slugs if s not in BOOKS]
    if unknown:
        ap.error("unknown book slug(s): %s" % ", ".join(unknown))

    result = {}
    for slug in slugs:
        entries = fetch_book(slug, args.cache_dir, args.source_dir)
        display, chapters = chapter_sections(slug, entries)
        multi = 0
        for chapter in sorted(chapters):
            starts = chapters[chapter]
            result["%s|%d" % (display, chapter)] = starts
            if len(starts) > 1:
                multi += 1
        print("  %-16s %3d chapters, %3d with 2+ sections" % (display, len(chapters), multi), file=sys.stderr)

    new_json = json.dumps(result, ensure_ascii=False, indent=args.indent, sort_keys=True)

    if args.check:
        old_json = None
        if os.path.exists(args.out):
            with open(args.out, encoding="utf-8") as fh:
                old_json = fh.read()
        if old_json == new_json:
            print("chapter_sections.json up to date", file=sys.stderr)
            return
        print("chapter_sections.json WOULD CHANGE", file=sys.stderr)
        sys.exit(1)

    os.makedirs(os.path.dirname(os.path.abspath(args.out)), exist_ok=True)
    with open(args.out, "w", encoding="utf-8") as fh:
        fh.write(new_json)
    print("wrote %d chapter entries -> %s" % (len(result), args.out), file=sys.stderr)


if __name__ == "__main__":
    main()
