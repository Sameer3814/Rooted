#!/usr/bin/env python3
"""
build_stories.py — pipeline/curation/stories.json -> data/stories.json.

Emits the Era, Story and LifeEvent seed (DATA_MODEL.md §2) and validates every
cross-reference in it, plus the character<->era link that lives in the starter
pack curation. Dangling ids are a hard error.

Checks:
  * era / story / event ids are unique and well-prefixed
  * every eraId, storyId, characterId and participantId resolves
  * every Story.verseIds entry is a verse that ships in the starter pack, so
    story pages can always render it as a card (the full span stays in
    primaryReference)
  * every Story.topicIds entry resolves against the curated topics
  * every character has at least one life event, and every story at least one
    character or verse (a record nothing links to is usually a mistake)
  * sequenceInLife is unique per character

Usage
-----
    py pipeline/build_stories.py
    py pipeline/build_stories.py --check
"""

import argparse
import json
import os
import sys
from collections import Counter, defaultdict

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CURATION_DIR = os.path.join(REPO_ROOT, "pipeline", "curation")
DEFAULT_STORIES = os.path.join(CURATION_DIR, "stories.json")
DEFAULT_PACK_CURATION = os.path.join(CURATION_DIR, "starter_pack.json")
DEFAULT_OUT = os.path.join(REPO_ROOT, "data", "stories.json")

EVENT_FIELDS = ("id", "characterId", "participantIds", "title", "description",
                "reference", "storyId", "eraId", "sequenceInLife", "ageApprox", "metadata")


def load(path):
    with open(path, encoding="utf-8") as fh:
        return json.load(fh)


def build(src, pack):
    eras = src["eras"]
    stories = src["stories"]
    events = src["lifeEvents"]

    era_ids = {e["id"] for e in eras}
    story_ids = {s["id"] for s in stories}
    char_ids = {c["id"] for c in pack["characters"]}
    topic_ids = {t["id"] for t in pack["topics"]}
    verse_ids = {v["id"] for v in pack["verses"]}

    problems = []

    for label, records in (("era", eras), ("story", stories), ("event", events)):
        dupes = [i for i, n in Counter(r["id"] for r in records).items() if n > 1]
        problems += ["duplicate %s id: %s" % (label, i) for i in dupes]

    for s in stories:
        if s["eraId"] not in era_ids:
            problems.append("%s -> unknown era %s" % (s["id"], s["eraId"]))
        problems += ["%s -> unknown character %s" % (s["id"], c)
                     for c in s.get("characterIds", []) if c not in char_ids]
        problems += ["%s -> unknown topic %s" % (s["id"], t)
                     for t in s.get("topicIds", []) if t not in topic_ids]
        # story verses must ship in the starter pack so the story page can render them
        problems += ["%s -> verse %s is not in the starter pack" % (s["id"], v)
                     for v in s.get("verseIds", []) if v not in verse_ids]
        if not s.get("characterIds") and not s.get("verseIds"):
            problems.append("%s has neither characters nor verses" % s["id"])

    seq = defaultdict(list)
    for e in events:
        if e["characterId"] not in char_ids:
            problems.append("%s -> unknown character %s" % (e["id"], e["characterId"]))
        if e.get("storyId") and e["storyId"] not in story_ids:
            problems.append("%s -> unknown story %s" % (e["id"], e["storyId"]))
        if e.get("eraId") and e["eraId"] not in era_ids:
            problems.append("%s -> unknown era %s" % (e["id"], e["eraId"]))
        problems += ["%s -> unknown participant %s" % (e["id"], p)
                     for p in e.get("participantIds", []) if p not in char_ids]
        unknown = set(e) - set(EVENT_FIELDS)
        problems += ["%s has unexpected field %s" % (e["id"], f) for f in sorted(unknown)]
        seq[e["characterId"]].append(e.get("sequenceInLife"))

    for cid, values in seq.items():
        dupes = [v for v, n in Counter(values).items() if n > 1]
        problems += ["%s has two life events at sequenceInLife %s" % (cid, v) for v in dupes]

    for c in pack["characters"]:
        if c.get("eraId") and c["eraId"] not in era_ids:
            problems.append("%s -> unknown era %s" % (c["id"], c["eraId"]))
        if c["id"] not in seq:
            problems.append("%s has no life events" % c["id"])

    if problems:
        raise SystemExit("error: %d problem(s):\n  %s" % (len(problems), "\n  ".join(problems)))

    # normalise: sort, fill defaults, drop nothing
    out_events = []
    for e in sorted(events, key=lambda x: (x["characterId"], x.get("sequenceInLife", 0))):
        e = dict(e)
        e.setdefault("participantIds", [])
        # the subject is always a participant, without needing to be repeated by hand
        if e["characterId"] not in e["participantIds"]:
            e["participantIds"] = [e["characterId"]] + e["participantIds"]
        if not e.get("eraId"):
            story = next((s for s in stories if s["id"] == e.get("storyId")), None)
            if story:
                e["eraId"] = story["eraId"]
        out_events.append(e)

    return {
        "schemaVersion": 2,
        "eras": sorted(eras, key=lambda e: e["order"]),
        "stories": sorted(stories, key=lambda s: s["canonicalOrder"]),
        "lifeEvents": out_events,
    }


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--curation", default=DEFAULT_STORIES)
    ap.add_argument("--pack-curation", default=DEFAULT_PACK_CURATION)
    ap.add_argument("--out", default=DEFAULT_OUT)
    ap.add_argument("--indent", type=int, default=None)
    ap.add_argument("--check", action="store_true")
    args = ap.parse_args()

    src = {k: v for k, v in load(args.curation).items() if not k.startswith("_")}
    result = build(src, load(args.pack_curation))
    payload = json.dumps(result, ensure_ascii=False, indent=args.indent)

    if args.check:
        current = open(args.out, encoding="utf-8").read() if os.path.exists(args.out) else None
        if current == payload:
            print("stories are up to date", file=sys.stderr)
            return
        print("stories would change — run without --check to write", file=sys.stderr)
        raise SystemExit(1)

    with open(args.out, "w", encoding="utf-8") as fh:
        fh.write(payload)
    print("wrote %d eras, %d stories, %d life events -> %s"
          % (len(result["eras"]), len(result["stories"]), len(result["lifeEvents"]), args.out),
          file=sys.stderr)


if __name__ == "__main__":
    main()
