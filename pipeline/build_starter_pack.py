#!/usr/bin/env python3
"""
build_starter_pack.py — assemble data/starter-pack.json, the seed content the
app loads on first run.

Takes the hand-curated selection in pipeline/curation/starter_pack.json (verse
ids + their topic/character links, plus the full Topic and Character records)
and joins it against the parsed corpus (data/verses.json) to pull each verse's
reference/book/chapter/verse/text. Verse text is never duplicated in the
curation file — the corpus is the single source of truth for it.

Also writes data/characters.json (the same characters, standalone) from the
same curation, so the two files cannot drift apart.

Every topic/character/verse cross-reference is validated; dangling ids are a
hard error.

The output carries NO `progress` field: practice progress is user state, stored
separately under `rooted-progress` (DATA_MODEL.md §5, §7, §8.1).

Usage
-----
    py pipeline/build_starter_pack.py
    py pipeline/build_starter_pack.py --check     # verify without writing
"""

import argparse
import json
import os
import sys

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DEFAULT_CURATION = os.path.join(REPO_ROOT, "pipeline", "curation", "starter_pack.json")
DEFAULT_CORPUS = os.path.join(REPO_ROOT, "data", "verses.json")
DEFAULT_OUT = os.path.join(REPO_ROOT, "data", "starter-pack.json")
DEFAULT_CHARACTERS_OUT = os.path.join(REPO_ROOT, "data", "characters.json")

# Verse fields copied from the corpus into the starter pack.
CORPUS_FIELDS = ("reference", "book", "chapter", "verse", "text", "translation")


def load(path):
    with open(path, encoding="utf-8") as fh:
        return json.load(fh)


def build(curation, corpus):
    by_id = {v["id"]: v for v in corpus}

    missing = [v["id"] for v in curation["verses"] if v["id"] not in by_id]
    if missing:
        raise SystemExit(
            "error: %d curated verse id(s) not in the corpus: %s\n"
            "Parse the book(s) they belong to first "
            "(py pipeline/parse_books.py --books ...)."
            % (len(missing), ", ".join(missing))
        )

    verses = []
    for picked in curation["verses"]:
        source = by_id[picked["id"]]
        verse = {"id": picked["id"]}
        verse.update({f: source[f] for f in CORPUS_FIELDS if f in source})
        verse["topicIds"] = picked.get("topicIds", [])
        verse["characterIds"] = picked.get("characterIds", [])
        verses.append(verse)

    # Referential integrity: every topic/character id a verse points at must exist.
    topic_ids = {t["id"] for t in curation["topics"]}
    char_ids = {c["id"] for c in curation["characters"]}
    problems = []
    for verse in verses:
        problems += ["%s -> unknown topic %s" % (verse["id"], t)
                     for t in verse["topicIds"] if t not in topic_ids]
        problems += ["%s -> unknown character %s" % (verse["id"], c)
                     for c in verse["characterIds"] if c not in char_ids]
    for character in curation["characters"]:
        problems += ["%s -> unknown character %s" % (character["id"], r["characterId"])
                     for r in character.get("relationships", [])
                     if r["characterId"] not in char_ids]
        problems += ["%s -> unknown verse %s" % (character["id"], v)
                     for v in character.get("verseIds", [])
                     if v not in {x["id"] for x in verses}]
    for topic in curation["topics"]:
        problems += ["%s -> unknown topic %s" % (topic["id"], r)
                     for r in topic.get("relatedTopicIds", []) if r not in topic_ids]
    if problems:
        raise SystemExit("error: dangling references:\n  " + "\n  ".join(problems))

    return {
        "schemaVersion": curation.get("schemaVersion", 2),
        "verses": verses,
        "topics": curation["topics"],
        "characters": curation["characters"],
    }


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--curation", default=DEFAULT_CURATION)
    ap.add_argument("--corpus", default=DEFAULT_CORPUS)
    ap.add_argument("--out", default=DEFAULT_OUT)
    ap.add_argument("--characters-out", default=DEFAULT_CHARACTERS_OUT)
    ap.add_argument("--indent", type=int, default=None,
                    help="pretty-print with this indent (default: compact)")
    ap.add_argument("--check", action="store_true",
                    help="build and validate, but don't write; non-zero exit if output would change")
    args = ap.parse_args()

    pack = build(load(args.curation), load(args.corpus))
    outputs = [
        (args.out, json.dumps(pack, ensure_ascii=False, indent=args.indent)),
        (args.characters_out,
         json.dumps(pack["characters"], ensure_ascii=False, indent=args.indent)),
    ]

    if args.check:
        stale = [path for path, payload in outputs
                 if (open(path, encoding="utf-8").read() if os.path.exists(path) else None) != payload]
        if not stale:
            print("outputs are up to date (%d verses)" % len(pack["verses"]), file=sys.stderr)
            return
        print("would change: %s — run without --check to write" % ", ".join(stale), file=sys.stderr)
        raise SystemExit(1)

    for path, payload in outputs:
        with open(path, "w", encoding="utf-8") as fh:
            fh.write(payload)
    print("wrote %d verses, %d topics, %d characters -> %s (+ %s)"
          % (len(pack["verses"]), len(pack["topics"]), len(pack["characters"]),
             args.out, args.characters_out),
          file=sys.stderr)


if __name__ == "__main__":
    main()
