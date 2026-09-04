#!/usr/bin/env python3
"""
parse_books.py — World English Bible (WEB) source JSON -> Rooted's Verse schema.

Source: https://github.com/TehShrike/world-english-bible (public domain / CC0).
The WEB itself is public domain. Re-verify the source is still public domain
before reproducing verse text in bulk; this reasoning does NOT extend to
copyrighted translations (see CLAUDE.md).

Source format
-------------
Each book file is a flat array of entries. The ones that carry verse text are:
    {"type": "paragraph text", "chapterNumber": 1, "verseNumber": 1,
     "sectionNumber": 1, "value": "In the beginning, ..."}
    {"type": "line text", ...}                 # poetry (Psalms, blessings, ...)
Everything else is structure ("paragraph start", "line break", "stanza end")
or a Psalm superscription ("header", which carries no verse number and is
deliberately skipped — it is not a verse).

A single verse is often split across several entries; they are grouped by
(chapterNumber, verseNumber) and joined in sectionNumber order.

Output
------
data/verses.json — a flat array of Verse objects (DATA_MODEL.md §2):
    {"id": "verse_genesis_1_1", "reference": "Genesis 1:1",
     "book": "Genesis", "chapter": 1, "verse": 1,
     "text": "...", "translation": "WEB", "topicIds": [], "characterIds": []}

Usage
-----
    py pipeline/parse_books.py                      # genesis + psalms + exodus + ruth + leviticus + numbers (shipped set)
    py pipeline/parse_books.py --books genesis exodus
    py pipeline/parse_books.py --all                # all 66 books
    py pipeline/parse_books.py --out data/verses.json --indent 2
"""

import argparse
import json
import os
import re
import sys
import urllib.request

SOURCE_BASE = "https://raw.githubusercontent.com/TehShrike/world-english-bible/master/json"

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CACHE_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".cache")
DEFAULT_OUT = os.path.join(REPO_ROOT, "data", "verses.json")

# The books currently shipped in data/verses.json.
DEFAULT_BOOKS = ["genesis", "psalms", "exodus", "ruth", "leviticus", "numbers"]

# slug (== source filename stem, == the slug used in verse ids) -> display name
BOOKS = {
    "genesis": "Genesis", "exodus": "Exodus", "leviticus": "Leviticus",
    "numbers": "Numbers", "deuteronomy": "Deuteronomy", "joshua": "Joshua",
    "judges": "Judges", "ruth": "Ruth", "1samuel": "1 Samuel",
    "2samuel": "2 Samuel", "1kings": "1 Kings", "2kings": "2 Kings",
    "1chronicles": "1 Chronicles", "2chronicles": "2 Chronicles",
    "ezra": "Ezra", "nehemiah": "Nehemiah", "esther": "Esther", "job": "Job",
    "psalms": "Psalms", "proverbs": "Proverbs", "ecclesiastes": "Ecclesiastes",
    "songofsolomon": "Song of Solomon", "isaiah": "Isaiah",
    "jeremiah": "Jeremiah", "lamentations": "Lamentations",
    "ezekiel": "Ezekiel", "daniel": "Daniel", "hosea": "Hosea", "joel": "Joel",
    "amos": "Amos", "obadiah": "Obadiah", "jonah": "Jonah", "micah": "Micah",
    "nahum": "Nahum", "habakkuk": "Habakkuk", "zephaniah": "Zephaniah",
    "haggai": "Haggai", "zechariah": "Zechariah", "malachi": "Malachi",
    "matthew": "Matthew", "mark": "Mark", "luke": "Luke", "john": "John",
    "acts": "Acts", "romans": "Romans", "1corinthians": "1 Corinthians",
    "2corinthians": "2 Corinthians", "galatians": "Galatians",
    "ephesians": "Ephesians", "philippians": "Philippians",
    "colossians": "Colossians", "1thessalonians": "1 Thessalonians",
    "2thessalonians": "2 Thessalonians", "1timothy": "1 Timothy",
    "2timothy": "2 Timothy", "titus": "Titus", "philemon": "Philemon",
    "hebrews": "Hebrews", "james": "James", "1peter": "1 Peter",
    "2peter": "2 Peter", "1john": "1 John", "2john": "2 John",
    "3john": "3 John", "jude": "Jude", "revelation": "Revelation",
}

TEXT_TYPES = {"paragraph text", "line text"}

# The source uses typographic quotes; the corpus is normalised to ASCII quotes.
# Em dashes are kept as-is.
SMART_QUOTES = {
    "‘": "'", "’": "'",   # ‘ ’
    "“": '"', "”": '"',   # “ ”
}


def normalize(text):
    """Smart quotes -> ASCII, collapse all whitespace (incl. NBSP) to single spaces."""
    for src, dst in SMART_QUOTES.items():
        text = text.replace(src, dst)
    return re.sub(r"\s+", " ", text).strip()


def fetch_book(slug, cache_dir, source_dir=None):
    """Return the raw entry list for one book, from --source-dir, cache, or the network."""
    filename = slug + ".json"
    if source_dir:
        path = os.path.join(source_dir, filename)
        with open(path, encoding="utf-8") as fh:
            return json.load(fh)

    os.makedirs(cache_dir, exist_ok=True)
    cached = os.path.join(cache_dir, filename)
    if not os.path.exists(cached):
        url = "%s/%s" % (SOURCE_BASE, filename)
        print("  downloading %s" % url, file=sys.stderr)
        with urllib.request.urlopen(url, timeout=60) as resp:
            payload = resp.read()
        with open(cached, "wb") as fh:
            fh.write(payload)
    with open(cached, encoding="utf-8") as fh:
        return json.load(fh)


def parse_book(slug, entries):
    """Group a book's text entries into Verse objects, in canonical order."""
    display = BOOKS[slug]
    buckets = {}
    for entry in entries:
        if entry.get("type") not in TEXT_TYPES:
            continue
        chapter, verse = entry.get("chapterNumber"), entry.get("verseNumber")
        value = entry.get("value")
        if chapter is None or verse is None or not value:
            continue
        buckets.setdefault((chapter, verse), []).append(
            (entry.get("sectionNumber") or 0, value)
        )

    verses = []
    for chapter, verse in sorted(buckets):
        parts = sorted(buckets[(chapter, verse)], key=lambda p: p[0])
        text = normalize(" ".join(part[1] for part in parts))
        if not text:
            continue
        verses.append({
            "id": "verse_%s_%d_%d" % (slug, chapter, verse),
            "reference": "%s %d:%d" % (display, chapter, verse),
            "book": display,
            "chapter": chapter,
            "verse": verse,
            "text": text,
            "translation": "WEB",
            "topicIds": [],
            "characterIds": [],
        })
    return verses


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--books", nargs="+", metavar="SLUG",
                    help="book slugs to parse (default: %s)" % " ".join(DEFAULT_BOOKS))
    ap.add_argument("--all", action="store_true", help="parse all 66 books")
    ap.add_argument("--source-dir", help="read book JSON from here instead of downloading")
    ap.add_argument("--cache-dir", default=CACHE_DIR, help="where downloads are cached")
    ap.add_argument("--out", default=DEFAULT_OUT, help="output path (default: data/verses.json)")
    ap.add_argument("--indent", type=int, default=None,
                    help="pretty-print with this indent (default: compact)")
    args = ap.parse_args()

    if args.all:
        slugs = list(BOOKS)
    else:
        slugs = args.books or DEFAULT_BOOKS

    unknown = [s for s in slugs if s not in BOOKS]
    if unknown:
        ap.error("unknown book slug(s): %s" % ", ".join(unknown))

    all_verses = []
    for slug in slugs:
        entries = fetch_book(slug, args.cache_dir, args.source_dir)
        verses = parse_book(slug, entries)
        print("  %-16s %5d verses" % (BOOKS[slug], len(verses)), file=sys.stderr)
        all_verses.extend(verses)

    os.makedirs(os.path.dirname(os.path.abspath(args.out)), exist_ok=True)
    with open(args.out, "w", encoding="utf-8") as fh:
        json.dump(all_verses, fh, ensure_ascii=False, indent=args.indent)

    print("wrote %d verses -> %s" % (len(all_verses), args.out), file=sys.stderr)


if __name__ == "__main__":
    main()
