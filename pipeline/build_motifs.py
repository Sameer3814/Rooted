#!/usr/bin/env python3
"""
build_motifs.py — pipeline/curation/motifs.json -> data/motifs.json.

Emits the Motif entity (DATA_MODEL.md §2). A Motif record carries no links of
its own — every instance (this motif shows up in that story/character/verse)
is a Connection (fromType:"motif", relationship:"instance of", toType:"story"
| "character" | "verse") in curation/connections.json, validated by
build_connections.py. This script only validates the Motif records
themselves: unique ids, non-empty name/description, at least two example
references (a "motif" with one occurrence is just a fact about one story).

Usage
-----
    py pipeline/build_motifs.py
    py pipeline/build_motifs.py --check
"""

import argparse
import json
import os
import sys
from collections import Counter

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DEFAULT_CURATION = os.path.join(REPO_ROOT, "pipeline", "curation", "motifs.json")
DEFAULT_OUT = os.path.join(REPO_ROOT, "data", "motifs.json")

MOTIF_FIELDS = ("id", "name", "description", "exampleReferences", "depthTags", "metadata")


def load(path):
    with open(path, encoding="utf-8") as fh:
        return json.load(fh)


def build(motifs):
    problems = []
    dupes = [i for i, n in Counter(m["id"] for m in motifs).items() if n > 1]
    problems += ["duplicate motif id: %s" % i for i in dupes]

    for m in motifs:
        unknown = set(m) - set(MOTIF_FIELDS)
        problems += ["%s has unexpected field %s" % (m["id"], f) for f in sorted(unknown)]
        if not m.get("name"):
            problems.append("%s: missing name" % m["id"])
        if not m.get("description"):
            problems.append("%s: missing description" % m["id"])
        refs = m.get("exampleReferences", [])
        if len(refs) < 2:
            problems.append("%s: needs at least 2 exampleReferences — a pattern with one "
                             "occurrence is just a fact about that one story" % m["id"])

    if problems:
        raise SystemExit("error: %d problem(s):\n  %s" % (len(problems), "\n  ".join(problems)))

    out = []
    for m in sorted(motifs, key=lambda m: m["id"]):
        m = dict(m)
        m.setdefault("depthTags", [])
        m.setdefault("metadata", {})
        out.append(m)
    return out


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--curation", default=DEFAULT_CURATION)
    ap.add_argument("--out", default=DEFAULT_OUT)
    ap.add_argument("--indent", type=int, default=None)
    ap.add_argument("--check", action="store_true")
    args = ap.parse_args()

    src = load(args.curation)
    result = build(src["motifs"])
    payload = json.dumps(result, ensure_ascii=False, indent=args.indent)

    if args.check:
        current = open(args.out, encoding="utf-8").read() if os.path.exists(args.out) else None
        if current == payload:
            print("motifs are up to date (%d)" % len(result), file=sys.stderr)
            return
        print("motifs would change — run without --check to write", file=sys.stderr)
        raise SystemExit(1)

    with open(args.out, "w", encoding="utf-8") as fh:
        fh.write(payload)
    print("wrote %d motifs -> %s" % (len(result), args.out), file=sys.stderr)


if __name__ == "__main__":
    main()
