#!/usr/bin/env python3
"""
tag_verses.py — surface *candidate* verses for a topic from the parsed corpus.

This is a curation aid, not an auto-tagger. It never writes tags. It reads a
keyword lexicon (curation/topic_lexicon.json), scans data/verses.json, and
prints ranked candidates so a human can hand-pick the good ones into
curation/starter_pack.json. Keyword matching can't read metaphor or context —
"fear of Yahweh" is reverence, not anxiety — so the human pass is the point.

Ranking favours verses that are actually worth memorising: more keyword hits
first, then a memorisable length (roughly 8-30 words), then shorter.

Usage
-----
    py pipeline/tag_verses.py --report                 # coverage for every topic
    py pipeline/tag_verses.py --topic topic_fear       # candidates for one topic
    py pipeline/tag_verses.py --topic topic_fear --limit 40 --include-tagged
    py pipeline/tag_verses.py --untagged-topics        # topics with no verses yet
"""

import argparse
import json
import os
import re
import sys

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CURATION_DIR = os.path.join(REPO_ROOT, "pipeline", "curation")
DEFAULT_LEXICON = os.path.join(CURATION_DIR, "topic_lexicon.json")
DEFAULT_CURATION = os.path.join(CURATION_DIR, "starter_pack.json")
DEFAULT_CORPUS = os.path.join(REPO_ROOT, "data", "verses.json")

IDEAL_MIN_WORDS = 8
IDEAL_MAX_WORDS = 30


def load(path):
    with open(path, encoding="utf-8") as fh:
        return json.load(fh)


def term_pattern(term):
    """Whole-word-ish match; multi-word terms match as a phrase."""
    return re.compile(r"(?<!\w)" + re.escape(term.lower()) + r"(?!\w)")


def score(verse, patterns, excludes):
    text = verse["text"].lower()
    for pattern in excludes:
        if pattern.search(text):
            return None
    hits = sum(1 for pattern in patterns if pattern.search(text))
    if not hits:
        return None
    words = len(verse["text"].split())
    # 0 penalty inside the memorisable band, growing outside it
    if words < IDEAL_MIN_WORDS:
        length_penalty = IDEAL_MIN_WORDS - words
    elif words > IDEAL_MAX_WORDS:
        length_penalty = words - IDEAL_MAX_WORDS
    else:
        length_penalty = 0
    return (-hits, length_penalty, words)


def candidates(topic_id, lexicon, corpus):
    entry = lexicon[topic_id]
    patterns = [term_pattern(t) for t in entry.get("terms", [])]
    excludes = [term_pattern(t) for t in entry.get("exclude", [])]
    scored = []
    for verse in corpus:
        rank = score(verse, patterns, excludes)
        if rank is not None:
            scored.append((rank, verse))
    scored.sort(key=lambda pair: pair[0])
    return [verse for _, verse in scored]


def tagged_map(curation):
    """topic id -> set of verse ids already curated under it."""
    out = {}
    for verse in curation["verses"]:
        for topic_id in verse.get("topicIds", []):
            out.setdefault(topic_id, set()).add(verse["id"])
    return out


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--topic", help="topic id to list candidates for")
    ap.add_argument("--report", action="store_true", help="coverage summary for all topics")
    ap.add_argument("--untagged-topics", action="store_true",
                    help="list topics that have no curated verses yet")
    ap.add_argument("--limit", type=int, default=25)
    ap.add_argument("--include-tagged", action="store_true",
                    help="also show candidates already curated under this topic")
    ap.add_argument("--lexicon", default=DEFAULT_LEXICON)
    ap.add_argument("--curation", default=DEFAULT_CURATION)
    ap.add_argument("--corpus", default=DEFAULT_CORPUS)
    args = ap.parse_args()

    # keys starting with "_" are documentation, not topics
    lexicon = {k: v for k, v in load(args.lexicon).items() if not k.startswith("_")}
    curation = load(args.curation)
    corpus = load(args.corpus)
    tagged = tagged_map(curation)
    known_topics = {t["id"] for t in curation["topics"]}

    if args.report or args.untagged_topics:
        rows = []
        for topic_id in sorted(set(lexicon) | known_topics):
            curated = len(tagged.get(topic_id, ()))
            if topic_id in lexicon:
                found = len(candidates(topic_id, lexicon, corpus))
            else:
                found = None
            rows.append((topic_id, curated, found))
        if args.untagged_topics:
            rows = [r for r in rows if r[1] == 0]
        print("%-24s %8s %12s" % ("topic", "curated", "candidates"))
        for topic_id, curated, found in rows:
            missing = "" if topic_id in known_topics else "  (not in curation!)"
            no_lex = "" if found is not None else "  (no lexicon entry)"
            print("%-24s %8d %12s%s%s"
                  % (topic_id, curated, "-" if found is None else found, missing, no_lex))
        print("\n%d topics, %d curated verse-tags total"
              % (len(rows), sum(len(v) for v in tagged.values())))
        return

    if not args.topic:
        ap.error("pass --topic TOPIC_ID, --report, or --untagged-topics")
    if args.topic not in lexicon:
        ap.error("no lexicon entry for %s (add one to %s)" % (args.topic, args.lexicon))

    already = tagged.get(args.topic, set())
    found = candidates(args.topic, lexicon, corpus)
    shown = 0
    print("# %s — %d candidates, %d already curated\n" % (args.topic, len(found), len(already)))
    for verse in found:
        is_tagged = verse["id"] in already
        if is_tagged and not args.include_tagged:
            continue
        print("%s %-18s %s" % ("*" if is_tagged else " ", verse["reference"], verse["text"]))
        shown += 1
        if shown >= args.limit:
            break
    if shown < len(found):
        print("\n... %d more (raise --limit)" % (len(found) - shown))


if __name__ == "__main__":
    main()
