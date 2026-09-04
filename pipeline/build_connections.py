#!/usr/bin/env python3
"""
build_connections.py — pipeline/curation/connections.json -> data/connections.json.

Emits the generic Connection entity (DATA_MODEL.md §2) that replaces embedded
relationship arrays. Each fact is stored as ONE directed edge; the reverse view
is derived from `inverse` (a different label, e.g. "father of" -> "son of") or
`symmetric: true` (the same label both ways, e.g. "brother of"). The app's
connectionsFor() does the deriving at render time — curation never writes the
same fact twice.

Validates every fromId/toId against the entity types that exist so far
(character, story, era, topic, verse, motif) and requires exactly one of
`inverse` / `symmetric: true` on every edge, so a reverse view is never
silently missing.

Usage
-----
    py pipeline/build_connections.py
    py pipeline/build_connections.py --check
"""

import argparse
import json
import os
import sys
from collections import Counter

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CURATION_DIR = os.path.join(REPO_ROOT, "pipeline", "curation")
DEFAULT_CURATION = os.path.join(CURATION_DIR, "connections.json")
DEFAULT_PACK_CURATION = os.path.join(CURATION_DIR, "starter_pack.json")
DEFAULT_STORIES_OUT = os.path.join(REPO_ROOT, "data", "stories.json")
DEFAULT_MOTIFS_OUT = os.path.join(REPO_ROOT, "data", "motifs.json")
DEFAULT_OUT = os.path.join(REPO_ROOT, "data", "connections.json")

CONN_FIELDS = ("id", "fromType", "fromId", "relationship", "toType", "toId",
               "symmetric", "inverse", "notes", "depthTags", "metadata")


def load(path):
    with open(path, encoding="utf-8") as fh:
        return json.load(fh)


def id_sets(pack, stories, motifs):
    return {
        "character": {c["id"] for c in pack["characters"]},
        "topic": {t["id"] for t in pack["topics"]},
        "verse": {v["id"] for v in pack["verses"]},
        "story": {s["id"] for s in stories.get("stories", [])},
        "era": {e["id"] for e in stories.get("eras", [])},
        "motif": {m["id"] for m in motifs},
    }


def build(conns, pack, stories, motifs):
    ids = id_sets(pack, stories, motifs)
    problems = []

    dupes = [i for i, n in Counter(c["id"] for c in conns).items() if n > 1]
    problems += ["duplicate connection id: %s" % i for i in dupes]

    seen_edges = set()
    for c in conns:
        unknown = set(c) - set(CONN_FIELDS)
        problems += ["%s has unexpected field %s" % (c["id"], f) for f in sorted(unknown)]

        for end, type_field, id_field in (("from", "fromType", "fromId"), ("to", "toType", "toId")):
            etype, eid = c.get(type_field), c.get(id_field)
            if etype not in ids:
                problems.append("%s: unknown %sType %r" % (c["id"], end, etype))
            elif eid not in ids[etype]:
                problems.append("%s: %s -> unknown %s %s" % (c["id"], end, etype, eid))

        has_inverse = bool(c.get("inverse"))
        is_symmetric = bool(c.get("symmetric"))
        if has_inverse and is_symmetric:
            problems.append("%s: has both inverse and symmetric — pick one" % c["id"])
        elif not has_inverse and not is_symmetric:
            problems.append("%s: needs inverse (a reverse label) or symmetric: true, "
                             "or the reverse view has no label to show" % c["id"])
        if is_symmetric and c.get("fromType") == c.get("toType") and c.get("fromId") == c.get("toId"):
            problems.append("%s: connects an entity to itself" % c["id"])

        edge = (c["fromType"], c["fromId"], c["relationship"], c["toType"], c["toId"])
        if edge in seen_edges:
            problems.append("%s: duplicate edge (same fact stored twice)" % c["id"])
        seen_edges.add(edge)

    if problems:
        raise SystemExit("error: %d problem(s):\n  %s" % (len(problems), "\n  ".join(problems)))

    out = []
    for c in sorted(conns, key=lambda c: (c["fromType"], c["fromId"], c["relationship"])):
        c = dict(c)
        c.setdefault("symmetric", False)
        c.setdefault("inverse", None)
        c.setdefault("notes", "")
        c.setdefault("depthTags", [])
        c.setdefault("metadata", {})
        out.append(c)
    return out


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--curation", default=DEFAULT_CURATION)
    ap.add_argument("--pack-curation", default=DEFAULT_PACK_CURATION)
    ap.add_argument("--stories", default=DEFAULT_STORIES_OUT,
                    help="built data/stories.json, for story/era id validation")
    ap.add_argument("--motifs", default=DEFAULT_MOTIFS_OUT,
                    help="built data/motifs.json, for motif id validation")
    ap.add_argument("--out", default=DEFAULT_OUT)
    ap.add_argument("--indent", type=int, default=None)
    ap.add_argument("--check", action="store_true")
    args = ap.parse_args()

    src = {k: v for k, v in load(args.curation).items() if not k.startswith("_")}
    stories = load(args.stories) if os.path.exists(args.stories) else {}
    motifs = load(args.motifs) if os.path.exists(args.motifs) else []
    result = build(src["connections"], load(args.pack_curation), stories, motifs)
    payload = json.dumps(result, ensure_ascii=False, indent=args.indent)

    if args.check:
        current = open(args.out, encoding="utf-8").read() if os.path.exists(args.out) else None
        if current == payload:
            print("connections are up to date (%d)" % len(result), file=sys.stderr)
            return
        print("connections would change — run without --check to write", file=sys.stderr)
        raise SystemExit(1)

    with open(args.out, "w", encoding="utf-8") as fh:
        fh.write(payload)
    print("wrote %d connections -> %s" % (len(result), args.out), file=sys.stderr)


if __name__ == "__main__":
    main()
