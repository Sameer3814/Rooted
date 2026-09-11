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
py pipeline/parse_books.py                      # genesis + psalms + exodus + ruth + leviticus + numbers + deuteronomy + joshua + judges + 1samuel + 2samuel + 1kings + 2kings + 1chronicles + 2chronicles (what's shipped)
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

### `build_stories.py` — curation → `data/stories.json`
Emits the Era, Story and LifeEvent seed from `curation/stories.json`.

```sh
py pipeline/build_stories.py
py pipeline/build_stories.py --check
```

Validates every era, story, character, participant, topic and verse reference;
rejects duplicate `sequenceInLife` within one character; and requires every
character to have at least one life event and every story at least one character
or verse (a record nothing links to is usually a mistake). Story `verseIds` must
be verses that ship in the starter pack, so a story page can always render them.

It also normalises: each event's subject is prepended to `participantIds`
automatically, and an event inherits `eraId` from its story when omitted.

### `build_motifs.py` — curation → `data/motifs.json`
Emits the Motif entity from `curation/motifs.json` — name, description, and
`exampleReferences` (display strings, not verse ids).

```sh
py pipeline/build_motifs.py
py pipeline/build_motifs.py --check
```

**Requires at least 2 `exampleReferences`.** A "motif" with one occurrence is
just a fact about that one story — not curated as a motif until a genuine
second instance turns up in the content. A motif's actual instances (this
motif shows up in that story/character/verse) aren't part of the Motif record
at all — they're Connections, added to `curation/connections.json` the same
way any other edge is (`fromType: "motif"`, `relationship: "instance of"`,
`inverse: "has motif"`).

### `build_connections.py` — curation → `data/connections.json`
Emits the generic Connection entity from `curation/connections.json` — the
`{fromType, fromId, relationship, toType, toId}` edge that replaces embedded
relationship arrays (`Character.relationships[]` was the original one). Also
carries Motif instances and story↔story links (`"parallels"`, `"foreshadows"`)
— anything typed and directional goes here, not a new embedded array.

```sh
py pipeline/build_connections.py
py pipeline/build_connections.py --check
```

**Store each fact once.** Every edge needs exactly one of `inverse` (a
different label for the reverse view, e.g. `"father of"` ⇄ `"son of"`) or
`symmetric: true` (the same label both ways, e.g. `"brother of"`) — the builder
rejects an edge with neither, or with both. The app derives the reverse view at
render time (`connectionsFor()`), so don't write the same fact twice from both
ends the way the old embedded arrays did. Run this **after** `build_stories.py`
and `build_motifs.py` — it validates every `fromId`/`toId` against their output.

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

## Adding a character, story, life event or pattern

Characters live in `curation/starter_pack.json`; eras, stories and life events
live in `curation/stories.json`; motifs live in `curation/motifs.json`;
family/other relationships and motif instances live in
`curation/connections.json`. Run all four builders in this order — later ones
validate against earlier ones' output:

```sh
py pipeline/build_starter_pack.py && py pipeline/build_stories.py && py pipeline/build_motifs.py && py pipeline/build_connections.py
```

Worth knowing:
- **`roles` should distinguish the person.** They're what the People list shows
  under each name, so "called out of Ur" earns its place and "patriarch" does
  not — three men carrying the same label tells the reader nothing.
- **Give every character at least one life event.** The builder enforces it; a
  character with an empty timeline looks broken in the app.
- **A motif needs a genuine second instance before it's a motif.** One
  occurrence is just a fact about that story; `build_motifs.py` requires at
  least 2 `exampleReferences`. Don't force a pattern onto content that only
  has one example — wait until a real second one turns up.
- **A motif's `exampleReferences` and its Connection instances are
  separate lists** and can drift apart. `exampleReferences` (on the Motif
  record) is a short curated display sample shown as a hint line;
  the Connections with `fromType: "motif"` are what the Pattern page's
  "Where it shows up" list is built from. When you add a new instance as a
  Connection, add the reference to `exampleReferences` too unless the
  sample is already long enough to make the point.
- **Books are being added in canonical order** (Genesis, Exodus, Leviticus,
  Numbers, ... — Ruth landed earlier and is the one exception). Books are not
  all the same shape, though: Genesis, Exodus, Ruth and Numbers are narrative
  and fit the full playbook above. Leviticus is almost entirely law and
  ritual — it got a lighter pass instead: verses and topics throughout, Story
  treatment only for its handful of genuine narrative incidents (ordination
  of Aaron, Nadab and Abihu, the blasphemer — three in 27 chapters). Numbers
  mixed both: real narrative (the spies, Korah, Balaam...) got Stories, its
  long census/law stretches got the lighter verses-only pass. Deuteronomy —
  almost entirely Moses' three farewell speeches — got the lighter pass too,
  same as predicted: verses/topics throughout, Stories only for its two real
  narrative beats (Moses commissioning Joshua; Moses viewing the land and
  dying on Nebo). Joshua (the book) went back to the full playbook — narrative
  again, as predicted (Rahab, Jericho, Achan, the Gibeonites, the sun
  standing still, Caleb's payoff, Joshua's farewell). Judges was narrative
  too, as predicted — Ehud, Deborah/Barak/Jael, Gideon, Jephthah, Samson —
  and it slotted straight into the era_judges Ruth had already established
  rather than needing a new one. 1 Samuel was narrative throughout — no
  lighter pass needed — and got its own new era (era_united_kingdom), since
  it's a genuinely new period, not a continuation of era_judges. 2 Samuel
  was also narrative throughout and folded into that same era (David's
  reign continuing directly from 1 Samuel, not a new period) — the same
  "same era, no new one" call as Judges, just for the opposite reason
  (genuinely the same period, vs. era_judges already covering it). 1 Kings
  was narrative throughout too, but this time genuinely needed a new era
  partway through the book: Solomon's reign is still era_united_kingdom,
  but once the kingdom splits (chapter 12) a new era_divided_kingdom
  starts — the split happens mid-book, which the era boundary just has to
  follow rather than aligning to book boundaries. 2 Kings did the same
  thing again at its other end: 12 of its 13 stories are still
  era_divided_kingdom, and only the fall of Jerusalem crosses into the
  new era_exile. 1-2 Chronicles was done as a single pass and was
  handled differently again: it *retells* Samuel-Kings, so rather than a
  light pass OR duplicate stories, the curation added stories only for
  Chronicles-unique material (David's temple prep, the kings of Judah
  that Kings skims, Cyrus's decree) and folded genuinely parallel gems
  like 2 Chr 7:14 into the *existing* Kings stories' verseIds. That's the
  pattern for any future retold material (the Gospels will need it too):
  extend the existing story, don't clone it.
- **Reread an era's `name`/`summary`/`approxRange` each time a new book
  extends it, not just its `id`.** `era_exodus` still read "The Exodus
  begins" / "in Egypt" after Leviticus, Numbers, and Deuteronomy — 40 years
  later, at the Jordan — had all been folded into it. The `id` never needs to
  change (nothing references the display text), but the display text can go
  quietly stale exactly the way `Character.era` free-strings used to.
- **Leave a bigger `canonicalOrder` gap between books than feels necessary.**
  Ruth's block was placed right after Exodus/Leviticus with only room for a
  few more stories; adding Numbers (which sits chronologically *before* Ruth)
  meant bumping Ruth's whole block up by 100 to make space. Cheap to fix (it's
  curation data — edit and re-run `build_stories.py`), but leave headroom
  between each book's range from the start and you won't need to.
- **Ezra/Nehemiah was the opposite case from Chronicles**: genuinely new
  narrative, not a retelling, so it got the full playbook and a clean new
  era (`era_return_from_exile`) rather than Chronicles's
  scoped-to-unique-material treatment. It also reused an existing
  character across eras without moving him — `char_cyrus` (introduced in
  the Chronicles pass, `eraId: era_exile`) appears in the new era's first
  story too; a character's `eraId` is where their own arc is centered, not
  every story they're mentioned in. And it introduced the first
  relationship type that isn't family, succession, or servanthood —
  `"worked alongside"` (symmetric) — a reminder that Connection
  relationship strings are free-form data (design philosophy #1), not a
  fixed list to pick from.
- **Esther's era placement follows Bible book order, not strict
  chronology** — and that's a deliberate, previously-made call, not a
  new exception. Esther's story (under Ahasuerus/Xerxes) actually happens
  *before* Ezra's and Nehemiah's returns (under Artaxerxes), but
  `era_esther`'s `order` still comes after `era_return_from_exile`,
  because this project's stated policy (CLAUDE.md "Known gaps" §3) is to
  follow canonical Bible book order for anything past Ruth, not
  re-sequence by history. `order` is a display/grouping field, not a
  historical timeline — don't try to make it one.
- **Not every book needs a new era, and not every book needs an era at
  all.** Job got a new one (`era_job`) because it's genuinely undated
  and outside Israel's own history — no existing era honestly fits.
  Proverbs, Ecclesiastes, and Song of Solomon needed **no** era at all —
  they have no narrative, so no Stories, so nothing that requires
  `eraId`; they're just curated verses. Don't manufacture a Story or an
  Era for a book just to give it "the full treatment" — match the
  treatment to what the book actually is (Leviticus set this precedent
  first; the wisdom books confirm it generalizes).
- **`DEFAULT_BOOKS` and `data/verses.json` should track what's actually
  curated, not what's merely been read.** While curating the wisdom
  books, all 21 remaining OT books' raw text got parsed at once (adding
  every slug to `DEFAULT_BOOKS` in one edit) purely to make reading
  ahead easier. That was reverted before committing — `DEFAULT_BOOKS`
  was scoped back down to only the books actually curated at that
  commit, and `data/verses.json` regenerated to match. Reading ahead for
  your own research is fine; shipping a corpus that's ahead of the
  curation it claims to represent isn't — CLAUDE.md's own description of
  `data/verses.json` says it tracks `DEFAULT_BOOKS` exactly.
- **The last stretch (the Twelve) paid off every earlier "extend, don't
  clone" and "reuse an existing era" call from this whole project.**
  Haggai and Zechariah didn't need new stories because Ezra 5-6 already
  told their moment — extending `story_temple_completed`'s `verseIds`
  and `characterIds` took minutes, not a new curation pass. Hosea,
  Amos, and Jonah didn't need a new era because `era_divided_kingdom`
  already existed. And `motif_gracious_and_merciful_formula` was only
  visible at all because Exodus 34:6 and Nehemiah 9:17 were sitting in
  the curation from passes done weeks apart — a motif spanning that
  much distance is exactly the kind of thing that's easy to miss
  without deliberately checking new content against what's already
  there. When curating late books, actively look for echoes of already-
  curated verses, not just new content in isolation.
- **Common names collide once the canon gets big enough to have real
  duplicates.** Starting the New Testament, `char_joseph` was reused
  for Mary's husband without checking — Genesis's Joseph already had
  that id. `build_stories.py` caught it immediately (both Josephs'
  life events collided on the same `sequenceInLife` numbers under one
  shared character id), but check for an existing id *before* writing
  a character record, not after the builder complains. The fix,
  `char_joseph_husband_of_mary`, follows the same pattern already used
  for the two Zechariahs (`char_zechariah` the priest, `char_zechariah_prophet`
  the minor prophet) — both people keep their real, accurate `name`
  ("Joseph," "Zechariah"), disambiguated by a longer `id`, era
  grouping, and their own summary, not by inventing a nickname that
  isn't in the text.
- **Recurring NT characters (Jesus, Peter, the inner circle) need their
  current max `sequenceInLife` checked before every new batch, not
  assumed.** Unlike most OT figures, who accumulate life events across
  months-apart passes on unrelated books, Jesus and Peter pick up new
  events in nearly *every single* NT curation batch, since they're in
  almost every story. Reusing round numbers (this pipeline's usual
  10/20/30 spacing) without checking the actual current max caused a
  real collision adding the Last Supper batch — `char_peter` already
  had events at 40 and 50 from two *different* earlier batches (the
  Transfiguration pass and the Peter's-confession pass), and the new
  foot-washing/Gethsemane events picked the same numbers by coincidence.
  `build_stories.py` catches it immediately, but for characters this
  central, query their existing `sequenceInLife` values first
  (`py -c "..."` one-liner against `pipeline/curation/stories.json` is
  fast) rather than guessing round numbers and fixing after the fact.
- **When a new/minor character's story centers on an interaction with an
  existing major character, tag the major character too — it's easy to
  tag only the person the batch is "about."** Found in the "deep study"
  supporting-cast passes (DATA_MODEL.md items 66-68): 2 Samuel's Abner/
  Ittai/Hushai/Shimei/Amasa/Sheba stories all center on decisions David
  himself makes (receiving Abner, offering Ittai an out, sending Hushai
  back, restraining Abishai, appointing Amasa, sending Joab after Sheba)
  — but `char_david` was never added to any of those stories'
  `characterIds`, only the new minor character was. Same bug, same batch
  shape, in the very next pass: three of Paul's-circle's eight new
  stories (Lydia's conversion, Priscilla and Aquila) never got
  `char_paul` tagged even though he's the one preaching/lodging in every
  one of them. The symptom is invisible unless you actually go look at
  the *major* character's own page — `characterStories()` filters purely
  on `characterIds` membership, so an untagged story doesn't error
  anywhere, it just silently never shows up in "Stories" on the
  character it should be most relevant to. The user caught it by
  checking Paul's own profile after a batch that was "about" ten other
  people. Checklist for every new story from now on: after listing who
  it's centrally *about*, separately ask "which existing major character
  is also directly present or acting in this scene?" and tag them too —
  don't assume a big person's page will pick up small interactions for
  free just because a minor character on the other end of them exists.

## Copyright

The WEB is public domain, which is why it's the core dataset. Re-verify the
source is still public domain before reproducing verse text in bulk. This does
**not** extend to copyrighted translations (NIV, ESV, …) — see the translation
note in `CLAUDE.md`.

[src]: https://github.com/TehShrike/world-english-bible
