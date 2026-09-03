# Pipeline

Regenerates everything in `data/` from public-domain source text plus the
hand-curated selection in `curation/`. Nothing here runs at app runtime — the
app only reads the generated JSON.

Requires Python 3 (no third-party packages). On Windows the launcher is `py`.

## The two scripts

### `parse_books.py` — WEB source → `data/verses.json`
Downloads book JSON from [TehShrike/world-english-bible][src] (public domain /
CC0), groups the text entries by chapter+verse, normalises smart quotes to
ASCII and collapses whitespace, and emits the Verse schema (DATA_MODEL.md §2).

```sh
py pipeline/parse_books.py                      # genesis + psalms (what's shipped)
py pipeline/parse_books.py --books genesis exodus proverbs
py pipeline/parse_books.py --all                # all 66 books
py pipeline/parse_books.py --indent 2           # pretty-print instead of compact
```

Downloads are cached in `pipeline/.cache/` (git-ignored); delete it to re-fetch.
Use `--source-dir DIR` to parse from a local copy instead of the network.

Book slugs match the source filenames and the slug inside verse ids —
`genesis` → `verse_genesis_1_1`, `songofsolomon`, `1samuel`, and so on.

### `build_starter_pack.py` — curation + corpus → `data/starter-pack.json`
Takes `curation/starter_pack.json` (verse ids + their topic/character links,
plus the full Topic and Character records) and joins it against
`data/verses.json` to pull each verse's reference/book/chapter/verse/text.
Also writes `data/characters.json` from the same curation so the two files
can't drift.

```sh
py pipeline/build_starter_pack.py
py pipeline/build_starter_pack.py --check       # validate only; non-zero exit if stale
```

Every cross-reference is validated — a verse pointing at a topic that doesn't
exist, a character related to a missing character, a topic linked to an unknown
topic — and dangling ids are a hard error, not a warning.

### `tag_verses.py` — curation aid, writes nothing
Surfaces *candidate* verses for a topic so a human can pick the good ones. It
reads `curation/topic_lexicon.json` (keyword hints per topic), scans the corpus,
and prints ranked candidates — more keyword hits first, then a memorisable
length (~8–30 words), then shorter.

```sh
py pipeline/tag_verses.py --report                  # coverage for every topic
py pipeline/tag_verses.py --topic topic_fear        # candidates to pick from
py pipeline/tag_verses.py --topic topic_fear --limit 40 --include-tagged
py pipeline/tag_verses.py --untagged-topics
```

**It never writes tags.** Keyword matching can't read metaphor or context —
"fear of Yahweh" is reverence, not anxiety, which is why `topic_fear` carries an
`exclude` list. The human pass is the whole point; auto-tagging the corpus was
considered and deliberately rejected in favour of a smaller curated set.

## Starting a new topic

1. Add a lexicon entry in `curation/topic_lexicon.json` with `terms` (and
   `exclude` for predictable false positives).
2. `py pipeline/tag_verses.py --topic topic_yourthing --limit 30`
3. Hand-pick the ones that genuinely teach on it; add them to the verse records
   in `curation/starter_pack.json` (a verse can carry several topics).
4. Add the Topic record itself — `name`, `description`, `relatedTopicIds`.
5. `py pipeline/build_starter_pack.py`

## Adding to the starter pack

1. Make sure the book is parsed into `data/verses.json` (`parse_books.py --books ...`).
2. Add the verse id and its links to `curation/starter_pack.json`:
   ```json
   { "id": "verse_proverbs_3_5", "topicIds": ["topic_trust"], "characterIds": [] }
   ```
   Add any new Topic or Character records to the same file.
3. `py pipeline/build_starter_pack.py`

**Never edit `data/*.json` by hand** — it is generated and will be overwritten.
Verse text lives only in the corpus; the curation file holds selection and
links, never a copy of the text.

## Copyright

The WEB is public domain, which is why it's the core dataset. Re-verify the
source is still public domain before reproducing verse text in bulk. This does
**not** extend to copyrighted translations (NIV, ESV, …) — see the translation
note in `CLAUDE.md`.

[src]: https://github.com/TehShrike/world-english-bible
