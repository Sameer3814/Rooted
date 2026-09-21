#!/usr/bin/env python3
"""
parse_telugu_bible.py — eBible.org's tel2017 (Indian Revised Version,
Telugu) USFM source -> a parallel Verse-text corpus keyed by the SAME
verse ids as data/verses.json.

Source: https://ebible.org/find/details.php?id=tel2017 (the complete Old
and New Testament, USFM format), licensed CC BY-SA 4.0 — free to use and
redistribute with attribution, share-alike. This is a real, separate
licensing situation from the WEB corpus (parse_books.py's source, public
domain / CC0): keep the attribution line in data/verses_te.json's own
"license"/"source" metadata and in CLAUDE.md's provenance section intact
whenever this is re-run.

Unlike parse_books.py's source (structured JSON, one entry per verse
fragment), USFM is a plain-text markup format — a handful of very long
lines per book with \\c/\\v markers embedded inline alongside paragraph/
poetry formatting and footnote/cross-reference markup. This script parses
that with a small state machine + a regex cleanup pass (strip footnotes,
cross-references, and section headings entirely; strip every other USFM
marker while keeping its enclosed text) rather than a full USFM library,
since the goal is just plain verse text, not any of USFM's structure.

Output
------
data/verses_te.json — a flat array, one entry per verse:
    {"id": "verse_genesis_1_1", "reference": "Genesis 1:1", "book": "Genesis",
     "chapter": 1, "verse": 1, "text": "<Telugu text>",
     "translation": "IRV Telugu 2017 (tel2017)"}
Deliberately the SAME ids/book/chapter/verse fields parse_books.py already
uses for data/verses.json, so a Telugu verse can be looked up by simply
swapping which corpus file is read for a given id — no join table, no
schema change to Verse itself. Versification can still legitimately
differ verse-by-verse between the two (this is a different translation
tradition, not just a different language) — a verse present in one corpus
and absent in the other for the same id is expected here and there, not a
bug; `--check` reports the overlap so a real parsing regression is still
visible.

Usage
-----
    py pipeline/parse_telugu_bible.py                  # download (or use cache) + parse all 66 books
    py pipeline/parse_telugu_bible.py --check           # also compare id overlap against data/verses.json
    py pipeline/parse_telugu_bible.py --out data/verses_te.json --indent 2
"""

import argparse
import json
import os
import re
import sys
import urllib.request
import zipfile
import io

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CACHE_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".cache")
DEFAULT_OUT = os.path.join(REPO_ROOT, "data", "verses_te.json")
ZIP_URL = "https://ebible.org/Scriptures/tel2017_usfm.zip"
ZIP_CACHE_NAME = "tel2017_usfm.zip"

TRANSLATION_LABEL = "IRV Telugu 2017 (tel2017)"

# USFM 3-letter book code -> (slug used in verse ids, display name).
# The slug/display-name side is deliberately identical to parse_books.py's
# BOOKS dict, so verse ids line up between the two corpora.
BOOKS = {
    "GEN": ("genesis", "Genesis"), "EXO": ("exodus", "Exodus"),
    "LEV": ("leviticus", "Leviticus"), "NUM": ("numbers", "Numbers"),
    "DEU": ("deuteronomy", "Deuteronomy"), "JOS": ("joshua", "Joshua"),
    "JDG": ("judges", "Judges"), "RUT": ("ruth", "Ruth"),
    "1SA": ("1samuel", "1 Samuel"), "2SA": ("2samuel", "2 Samuel"),
    "1KI": ("1kings", "1 Kings"), "2KI": ("2kings", "2 Kings"),
    "1CH": ("1chronicles", "1 Chronicles"), "2CH": ("2chronicles", "2 Chronicles"),
    "EZR": ("ezra", "Ezra"), "NEH": ("nehemiah", "Nehemiah"),
    "EST": ("esther", "Esther"), "JOB": ("job", "Job"),
    "PSA": ("psalms", "Psalms"), "PRO": ("proverbs", "Proverbs"),
    "ECC": ("ecclesiastes", "Ecclesiastes"),
    "SNG": ("songofsolomon", "Song of Solomon"), "ISA": ("isaiah", "Isaiah"),
    "JER": ("jeremiah", "Jeremiah"), "LAM": ("lamentations", "Lamentations"),
    "EZK": ("ezekiel", "Ezekiel"), "DAN": ("daniel", "Daniel"),
    "HOS": ("hosea", "Hosea"), "JOL": ("joel", "Joel"), "AMO": ("amos", "Amos"),
    "OBA": ("obadiah", "Obadiah"), "JON": ("jonah", "Jonah"),
    "MIC": ("micah", "Micah"), "NAM": ("nahum", "Nahum"),
    "HAB": ("habakkuk", "Habakkuk"), "ZEP": ("zephaniah", "Zephaniah"),
    "HAG": ("haggai", "Haggai"), "ZEC": ("zechariah", "Zechariah"),
    "MAL": ("malachi", "Malachi"), "MAT": ("matthew", "Matthew"),
    "MRK": ("mark", "Mark"), "LUK": ("luke", "Luke"), "JHN": ("john", "John"),
    "ACT": ("acts", "Acts"), "ROM": ("romans", "Romans"),
    "1CO": ("1corinthians", "1 Corinthians"), "2CO": ("2corinthians", "2 Corinthians"),
    "GAL": ("galatians", "Galatians"), "EPH": ("ephesians", "Ephesians"),
    "PHP": ("philippians", "Philippians"), "COL": ("colossians", "Colossians"),
    "1TH": ("1thessalonians", "1 Thessalonians"), "2TH": ("2thessalonians", "2 Thessalonians"),
    "1TI": ("1timothy", "1 Timothy"), "2TI": ("2timothy", "2 Timothy"),
    "TIT": ("titus", "Titus"), "PHM": ("philemon", "Philemon"),
    "HEB": ("hebrews", "Hebrews"), "JAS": ("james", "James"),
    "1PE": ("1peter", "1 Peter"), "2PE": ("2peter", "2 Peter"),
    "1JN": ("1john", "1 John"), "2JN": ("2john", "2 John"),
    "3JN": ("3john", "3 John"), "JUD": ("jude", "Jude"),
    "REV": ("revelation", "Revelation"),
}

FILENAME_RE = re.compile(r"^\d+-([0-9A-Z]{3})tel2017\.usfm$")

# Markers whose *body* must be dropped entirely (not just the tag) — these
# aren't verse text: footnotes, cross-references, and section headings.
DROP_BLOCK_RE = re.compile(
    r"\\f\s.*?\\f\*"       # footnote ... \f*
    r"|\\x\s.*?\\x\*"      # cross-reference ... \x*
    r"|\\s\d?\s[^\\]*"     # section heading, up to the next marker
    r"|\\r\s[^\\]*"        # parallel-passage reference line
    r"|\\rem\s[^\\]*",     # translator remark
    re.DOTALL,
)
# Every remaining backslash marker (chapter/verse markers are handled by
# CV_RE below before this ever runs; this catches paragraph/poetry markers
# like \p \m \q1 \q2 and inline character markers like \wj \wj* \nd \nd*
# \add \add* — stripped, keeping whatever text they wrap).
STRIP_MARKER_RE = re.compile(r"\\[a-zA-Z]+\d?\*?")
CV_RE = re.compile(r"\\c\s+(\d+)|\\v\s+(\d+)")


def clean_verse_text(raw):
    text = DROP_BLOCK_RE.sub(" ", raw)
    text = STRIP_MARKER_RE.sub(" ", text)
    return re.sub(r"\s+", " ", text).strip()


def parse_usfm(content, slug, display):
    """Split one book's raw USFM text into Verse objects."""
    # Only content from the first \c marker onward is scripture — \id/\h/
    # \toc*/\mt*/\is1/\ip etc. before it are title-page/introduction material.
    first_c = content.find("\\c ")
    if first_c == -1:
        return []
    content = content[first_c:]

    verses = []
    chapter = None
    cursor = 0
    matches = list(CV_RE.finditer(content))
    for i, m in enumerate(matches):
        start_of_body = m.end()
        end_of_body = matches[i + 1].start() if i + 1 < len(matches) else len(content)
        body = content[start_of_body:end_of_body]
        if m.group(1) is not None:
            chapter = int(m.group(1))
            continue
        verse_num = int(m.group(2))
        if chapter is None:
            continue
        text = clean_verse_text(body)
        if not text:
            continue
        verses.append({
            "id": "verse_%s_%d_%d" % (slug, chapter, verse_num),
            "reference": "%s %d:%d" % (display, chapter, verse_num),
            "book": display,
            "chapter": chapter,
            "verse": verse_num,
            "text": text,
            "translation": TRANSLATION_LABEL,
        })
    return verses


def fetch_zip(cache_dir):
    os.makedirs(cache_dir, exist_ok=True)
    cached = os.path.join(cache_dir, ZIP_CACHE_NAME)
    if not os.path.exists(cached):
        print("  downloading %s" % ZIP_URL, file=sys.stderr)
        # ebible.org's CDN (Cloudflare) 403s Python's default urllib User-Agent.
        req = urllib.request.Request(ZIP_URL, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=120) as resp:
            payload = resp.read()
        with open(cached, "wb") as fh:
            fh.write(payload)
    with open(cached, "rb") as fh:
        return fh.read()


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--cache-dir", default=CACHE_DIR, help="where the downloaded zip is cached")
    ap.add_argument("--out", default=DEFAULT_OUT, help="output path (default: data/verses_te.json)")
    ap.add_argument("--indent", type=int, default=None,
                    help="pretty-print with this indent (default: compact)")
    ap.add_argument("--check", action="store_true",
                    help="report id overlap against data/verses.json")
    args = ap.parse_args()

    zip_bytes = fetch_zip(args.cache_dir)
    all_verses = []
    seen_codes = set()
    with zipfile.ZipFile(io.BytesIO(zip_bytes)) as zf:
        for name in zf.namelist():
            m = FILENAME_RE.match(os.path.basename(name))
            if not m:
                continue
            code = m.group(1)
            if code not in BOOKS:
                print("  ! unknown book code %s (%s) — skipped" % (code, name), file=sys.stderr)
                continue
            slug, display = BOOKS[code]
            content = zf.read(name).decode("utf-8")
            verses = parse_usfm(content, slug, display)
            print("  %-16s %5d verses" % (display, len(verses)), file=sys.stderr)
            all_verses.extend(verses)
            seen_codes.add(code)

    missing = [code for code in BOOKS if code not in seen_codes]
    if missing:
        print("  ! missing book(s) in the archive: %s" % ", ".join(missing), file=sys.stderr)

    os.makedirs(os.path.dirname(os.path.abspath(args.out)), exist_ok=True)
    with open(args.out, "w", encoding="utf-8") as fh:
        json.dump(all_verses, fh, ensure_ascii=False, indent=args.indent)
    print("wrote %d verses -> %s" % (len(all_verses), args.out), file=sys.stderr)

    if args.check:
        en_path = os.path.join(REPO_ROOT, "data", "verses.json")
        with open(en_path, encoding="utf-8") as fh:
            en_ids = {v["id"] for v in json.load(fh)}
        te_ids = {v["id"] for v in all_verses}
        overlap = en_ids & te_ids
        print("  English corpus: %d verses" % len(en_ids), file=sys.stderr)
        print("  Telugu corpus:  %d verses" % len(te_ids), file=sys.stderr)
        print("  shared ids:     %d (%.1f%% of English)" %
              (len(overlap), 100.0 * len(overlap) / len(en_ids)), file=sys.stderr)


if __name__ == "__main__":
    main()
