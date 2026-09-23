#!/usr/bin/env python3
"""
parse_hebrew_interlinear.py — the Open Scriptures Hebrew Bible
(morphhb, the Westminster Leningrad Codex tagged word-by-word with
Strong's numbers and morphology) -> a per-verse Hebrew word-array
corpus, data/interlinear_ot.json, keyed by the SAME verse ids
data/verses.json already uses (item 151's Greek NT counterpart is
parse_greek_interlinear.py).

Source: https://github.com/openscriptures/morphhb (the wlc/ directory,
one OSIS XML file per book). The Hebrew text itself (Westminster
Leningrad Codex) is Public Domain; the lemma/morphology tagging on top
of it is licensed CC BY 4.0 — keep the attribution in CLAUDE.md's
provenance section intact whenever this is re-run.

Each <w> element in the source carries a `lemma` attribute like
"b/7225" or "c/d/776" — one or more "/"-separated parts, each either a
bare Strong's number (optionally with a trailing single-letter
homograph suffix, e.g. "1254 a" for a second BDB sense of that root)
or a single alphabetic code for an inseparable Hebrew prefix
(conjunction, preposition, definite article, relative pronoun — these
don't carry their own Strong's number in the classic system, so they're
recorded as a `prefix` tag rather than resolved against the lexicon).
Homograph suffixes are dropped when resolving to data/lexicon_full.json
since that dictionary isn't itself homograph-split (verified: it has
"H1254" but no "H1254a") — a real, minor precision loss, not a bug.

The element's own text often contains internal "/" characters lining up
with the lemma's own "/" split (marking where one word's prefix ends
and its root begins) — stripped from the *displayed* Hebrew, since real
Hebrew text never contains a literal slash.

Usage
-----
    py pipeline/parse_hebrew_interlinear.py
    py pipeline/parse_hebrew_interlinear.py --check   # report % of verses covered vs data/verses.json
"""

import argparse
import json
import os
import re
import sys
import urllib.request
import xml.etree.ElementTree as ET

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CACHE_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".cache", "wlc")
DEFAULT_OUT = os.path.join(REPO_ROOT, "data", "interlinear_ot.json")
RAW_BASE = "https://raw.githubusercontent.com/openscriptures/morphhb/master/wlc/"

NS = {"osis": "http://www.bibletechnologies.net/2003/OSIS/namespace"}

# OSIS book code -> (slug, display) — deliberately the same 39 OT
# slugs parse_books.py/parse_telugu_bible.py already use, so verse ids
# line up across all three corpora.
BOOKS = {
    "Gen": ("genesis", "Genesis"), "Exod": ("exodus", "Exodus"),
    "Lev": ("leviticus", "Leviticus"), "Num": ("numbers", "Numbers"),
    "Deut": ("deuteronomy", "Deuteronomy"), "Josh": ("joshua", "Joshua"),
    "Judg": ("judges", "Judges"), "Ruth": ("ruth", "Ruth"),
    "1Sam": ("1samuel", "1 Samuel"), "2Sam": ("2samuel", "2 Samuel"),
    "1Kgs": ("1kings", "1 Kings"), "2Kgs": ("2kings", "2 Kings"),
    "1Chr": ("1chronicles", "1 Chronicles"), "2Chr": ("2chronicles", "2 Chronicles"),
    "Ezra": ("ezra", "Ezra"), "Neh": ("nehemiah", "Nehemiah"),
    "Esth": ("esther", "Esther"), "Job": ("job", "Job"),
    "Ps": ("psalms", "Psalms"), "Prov": ("proverbs", "Proverbs"),
    "Eccl": ("ecclesiastes", "Ecclesiastes"), "Song": ("songofsolomon", "Song of Solomon"),
    "Isa": ("isaiah", "Isaiah"), "Jer": ("jeremiah", "Jeremiah"),
    "Lam": ("lamentations", "Lamentations"), "Ezek": ("ezekiel", "Ezekiel"),
    "Dan": ("daniel", "Daniel"), "Hos": ("hosea", "Hosea"),
    "Joel": ("joel", "Joel"), "Amos": ("amos", "Amos"),
    "Obad": ("obadiah", "Obadiah"), "Jonah": ("jonah", "Jonah"),
    "Mic": ("micah", "Micah"), "Nah": ("nahum", "Nahum"),
    "Hab": ("habakkuk", "Habakkuk"), "Zeph": ("zephaniah", "Zephaniah"),
    "Hag": ("haggai", "Haggai"), "Zech": ("zechariah", "Zechariah"),
    "Mal": ("malachi", "Malachi"),
}

LEMMA_NUM_RE = re.compile(r"^(\d+)\s*([a-z])?$")


def fetch(osis_code, cache_dir):
    os.makedirs(cache_dir, exist_ok=True)
    cached = os.path.join(cache_dir, osis_code + ".xml")
    if not os.path.exists(cached):
        url = RAW_BASE + osis_code + ".xml"
        print("  downloading %s" % url, file=sys.stderr)
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=120) as resp:
            payload = resp.read()
        with open(cached, "wb") as fh:
            fh.write(payload)
    with open(cached, "rb") as fh:
        return fh.read()


def resolve_lemma(lemma):
    """`lemma` e.g. "b/7225" or "c/d/776" or "1254 a" -> a list of
    tokens, each either {"strongs": "H1234"} or {"prefix": "b"}."""
    if not lemma:
        return []
    parts = []
    for raw in lemma.split("/"):
        raw = raw.strip()
        if not raw:
            continue
        m = LEMMA_NUM_RE.match(raw)
        if m:
            parts.append({"strongs": "H" + m.group(1)})
        else:
            parts.append({"prefix": raw})
    return parts


def parse_book(xml_bytes, slug, display):
    """Each verse -> a list of [text, strongsIds] tuples, not
    {"text":..., "strongs":...} objects — the full Hebrew OT is ~305,000
    word tokens, and the repeated key names alone added ~8MB to the
    output (22MB vs ~14MB) for no benefit an app reading this
    programmatically needs. `morph` (the per-word grammar code) is
    dropped entirely for the same reason — nothing in this app's
    planned interlinear UI (item 151) shows grammatical parsing, only
    original text + a tap-through to the Strong's lexicon, so it would
    be pure unused weight in every download. Re-add it later, from the
    same cached source XML, if a real morphology feature needs it."""
    root = ET.fromstring(xml_bytes)
    out = {}
    for verse_el in root.iter("{%s}verse" % NS["osis"]):
        osis_id = verse_el.get("osisID")
        if not osis_id:
            continue
        book_code, chapter, verse_num = osis_id.split(".")
        verse_id = "verse_%s_%s_%s" % (slug, chapter, verse_num)
        tokens = []
        for w in verse_el.findall("{%s}w" % NS["osis"]):
            text = "".join(w.itertext()).replace("/", "")
            if not text:
                continue
            strongs_ids = [p["strongs"] for p in resolve_lemma(w.get("lemma", "")) if "strongs" in p]
            tokens.append([text, strongs_ids])
        if tokens:
            out[verse_id] = tokens
    return out


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--cache-dir", default=CACHE_DIR)
    ap.add_argument("--out", default=DEFAULT_OUT)
    ap.add_argument("--indent", type=int, default=None)
    ap.add_argument("--check", action="store_true",
                    help="report percent of data/verses.json's OT verses covered")
    args = ap.parse_args()

    merged = {}
    for osis_code, (slug, display) in BOOKS.items():
        xml_bytes = fetch(osis_code, args.cache_dir)
        verses = parse_book(xml_bytes, slug, display)
        print("  %-16s %5d verses" % (display, len(verses)), file=sys.stderr)
        merged.update(verses)

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
        print("  English OT verses: %d" % len(en_ids), file=sys.stderr)
        print("  Hebrew OT verses:  %d" % len(merged), file=sys.stderr)
        print("  shared ids:        %d (%.1f%% of English OT)" %
              (len(overlap), 100.0 * len(overlap) / len(en_ids)), file=sys.stderr)


if __name__ == "__main__":
    main()
