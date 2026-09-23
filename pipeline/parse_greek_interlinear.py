#!/usr/bin/env python3
"""
parse_greek_interlinear.py — STEPBible's TAGNT (Translators Amalgamated
Greek New Testament) -> a per-verse Greek word-array corpus,
data/interlinear_nt.json, keyed by the SAME verse ids data/verses.json
already uses (the Hebrew OT counterpart is parse_hebrew_interlinear.py).

Source: https://github.com/STEPBible/STEPBible-Data, the two files under
"Translators Amalgamated OT+NT/" named "TAGNT Mat-Jhn ..." and "TAGNT
Act-Rev ...". Licensed CC BY 4.0 ("Data created by www.STEPBible.org
based on work at Tyndale House Cambridge") — keep the attribution in
CLAUDE.md's provenance section intact whenever this is re-run.

Format: a large plain-text preamble (license, field descriptions, editor
notes) followed by tab-separated data rows, re-introduced with a fresh
header row (`Word & Type\tGreek\t...`) at the top of every chapter. Each
data row's own first column carries the reference AND the word's own
textual-variant flag together, e.g. "Mat.1.3#02=NKO" — word #2 of
Matthew 1:3, present in the Nestlé-Aland (N), Textus Receptus/KJV-
tradition (K), and Other (O) editions alike. Only rows whose flag
actually *includes* Nestlé-Aland — starting with "N"/"n", not "K"/"O"
or a parenthesized "(N)" meaning absent — are kept, since that's the
critical-text tradition WEB (this app's own English translation) and
virtually every modern translation follows; a flag like "K(O)" (found
in the Textus Receptus but not Nestlé-Aland at all) marks a KJV-only
reading with no WEB counterpart to align against. This mirrors the
file's own documented taxonomy exactly (verified against its header
summary table before writing this comment) rather than a guess.

The 4th column ("dStrongs = Grammar", e.g. "G0011=N-NSM-P" or
"G2384H=N-NSM-P") carries a *disambiguated* Strong's number — a
leading-zero-padded base number plus, sometimes, a trailing
single-letter homograph/sense suffix. Both are normalized away when
resolving against data/lexicon_full.json (verified: it has "G11" but
neither "G0011" nor "G11H").

Usage
-----
    py pipeline/parse_greek_interlinear.py
    py pipeline/parse_greek_interlinear.py --check   # report percent of NT verses covered vs data/verses.json
"""

import argparse
import json
import os
import re
import sys
import urllib.request

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CACHE_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".cache")
DEFAULT_OUT = os.path.join(REPO_ROOT, "data", "interlinear_nt.json")
RAW_BASE = ("https://raw.githubusercontent.com/STEPBible/STEPBible-Data/master/"
            "Translators%20Amalgamated%20OT%2BNT/")
SOURCE_FILES = [
    "TAGNT Mat-Jhn - Translators Amalgamated Greek NT - STEPBible.org CC-BY.txt",
    "TAGNT Act-Rev - Translators Amalgamated Greek NT - STEPBible.org CC-BY.txt",
]

# TAGNT book code -> (slug, display) — the same 27 NT slugs
# parse_books.py/parse_telugu_bible.py already use.
BOOKS = {
    "Mat": ("matthew", "Matthew"), "Mrk": ("mark", "Mark"),
    "Luk": ("luke", "Luke"), "Jhn": ("john", "John"),
    "Act": ("acts", "Acts"), "Rom": ("romans", "Romans"),
    "1Co": ("1corinthians", "1 Corinthians"), "2Co": ("2corinthians", "2 Corinthians"),
    "Gal": ("galatians", "Galatians"), "Eph": ("ephesians", "Ephesians"),
    "Php": ("philippians", "Philippians"), "Col": ("colossians", "Colossians"),
    "1Th": ("1thessalonians", "1 Thessalonians"), "2Th": ("2thessalonians", "2 Thessalonians"),
    "1Ti": ("1timothy", "1 Timothy"), "2Ti": ("2timothy", "2 Timothy"),
    "Tit": ("titus", "Titus"), "Phm": ("philemon", "Philemon"),
    "Heb": ("hebrews", "Hebrews"), "Jas": ("james", "James"),
    "1Pe": ("1peter", "1 Peter"), "2Pe": ("2peter", "2 Peter"),
    "1Jn": ("1john", "1 John"), "2Jn": ("2john", "2 John"),
    "3Jn": ("3john", "3 John"), "Jud": ("jude", "Jude"),
    "Rev": ("revelation", "Revelation"),
}

ROW_RE = re.compile(r"^([0-9A-Za-z]+)\.(\d+)\.(\d+)#(\d+)=(\(?[A-Za-z()]+)$")
GREEK_RE = re.compile(r"^(\S+)\s*\(")
DSTRONG_RE = re.compile(r"^([HG])0*(\d+)([A-Za-z]?)=")


def fetch(filename, cache_dir):
    os.makedirs(cache_dir, exist_ok=True)
    cached = os.path.join(cache_dir, filename)
    if not os.path.exists(cached):
        url = RAW_BASE + urllib_quote(filename)
        print("  downloading %s" % url, file=sys.stderr)
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=120) as resp:
            payload = resp.read()
        with open(cached, "wb") as fh:
            fh.write(payload)
    with open(cached, encoding="utf-8-sig") as fh:
        return fh.read()


def urllib_quote(s):
    import urllib.parse
    return urllib.parse.quote(s)


def includes_nestle_aland(flag):
    """"NKO"/"N(K)(O)"/"N(O)"/"n(o)" -> True (present in the critical
    text, WEB's own tradition); "K(O)"/"O" -> False (absent from it
    entirely) — the flag's first character is parenthesized exactly
    when that edition doesn't carry the word."""
    return bool(flag) and flag[0] in ("N", "n")


def parse_source(raw_text, seen_ids):
    out = {}
    for line in raw_text.split("\n"):
        if "\t" not in line:
            continue
        cols = line.split("\t")
        if len(cols) < 4:
            continue
        m = ROW_RE.match(cols[0].strip())
        if not m:
            continue
        book_code, chapter, verse_num, _word_idx, flag = m.groups()
        if not includes_nestle_aland(flag):
            continue
        if book_code not in BOOKS:
            continue
        slug, display = BOOKS[book_code]
        verse_id = "verse_%s_%s_%s" % (slug, chapter, verse_num)

        greek_field = cols[1].strip()
        gm = GREEK_RE.match(greek_field)
        text = gm.group(1) if gm else greek_field.split(" ")[0]

        strongs_ids = []
        dm = DSTRONG_RE.match(cols[3].strip())
        if dm:
            strongs_ids = [dm.group(1) + dm.group(2)]

        out.setdefault(verse_id, []).append([text, strongs_ids])
        seen_ids.add(book_code)
    return out


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--cache-dir", default=CACHE_DIR)
    ap.add_argument("--out", default=DEFAULT_OUT)
    ap.add_argument("--indent", type=int, default=None)
    ap.add_argument("--check", action="store_true")
    args = ap.parse_args()

    merged = {}
    seen_ids = set()
    for filename in SOURCE_FILES:
        raw_text = fetch(filename, args.cache_dir)
        verses = parse_source(raw_text, seen_ids)
        print("  %-60s %5d verses" % (filename[:60], len(verses)), file=sys.stderr)
        merged.update(verses)

    missing = [code for code in BOOKS if code not in seen_ids]
    if missing:
        print("  ! missing book(s): %s" % ", ".join(missing), file=sys.stderr)

    os.makedirs(os.path.dirname(os.path.abspath(args.out)), exist_ok=True)
    with open(args.out, "w", encoding="utf-8") as fh:
        json.dump(merged, fh, ensure_ascii=False, indent=args.indent)
    print("wrote %d verses -> %s" % (len(merged), args.out), file=sys.stderr)

    if args.check:
        en_path = os.path.join(REPO_ROOT, "data", "verses.json")
        with open(en_path, encoding="utf-8") as fh:
            en_ids = {v["id"] for v in json.load(fh) if v["id"].split("_")[1] in
                      {s for s, _ in BOOKS.values()}}
        overlap = en_ids & set(merged.keys())
        print("  English NT verses: %d" % len(en_ids), file=sys.stderr)
        print("  Greek NT verses:   %d" % len(merged), file=sys.stderr)
        print("  shared ids:        %d (%.1f%% of English NT)" %
              (len(overlap), 100.0 * len(overlap) / len(en_ids)), file=sys.stderr)


if __name__ == "__main__":
    main()
