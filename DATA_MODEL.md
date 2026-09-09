# Rooted — Data Model

The full schema for every entity Rooted needs, including the vision features
that aren't built yet. This is a **design pass, not a data-entry pass** — the
shapes are decided here so features can be added additively (see CLAUDE.md
"Design philosophy"). Content is then gathered in vertical slices, one feature
at a time.

**Keep this file in sync.** Any schema or entity change goes here in the same
pass that changes the code or data.

Status legend for each entity:
- **live** — exists in `data/*.json` and the app reads it
- **partial** — exists but incomplete or not wired into the app
- **planned** — designed here, not yet created

---

## 1. Conventions

### IDs
Stable, human-readable, type-prefixed strings. Never auto-increment numbers.
Assigned once and never changed (they're how hand-curated and bulk-imported
data merge without collisions).

| Entity        | Prefix        | Example                          |
|---------------|---------------|----------------------------------|
| Verse         | `verse_`      | `verse_genesis_1_1`              |
| Topic         | `topic_`      | `topic_forgiveness`              |
| Character     | `char_`       | `char_david`                     |
| Story         | `story_`      | `story_binding_of_isaac`         |
| Era           | `era_`        | `era_patriarchs`                 |
| Life event    | `event_`      | `event_abraham_call`             |
| Motif         | `motif_`      | `motif_younger_son_chosen`       |
| Media         | `media_`      | `media_char_david_portrait`      |
| Connection    | `conn_`       | `conn_isaac_child_of_abraham`    |
| Challenge type| `challenge_`  | `challenge_fill_blank`           |
| Practice session | `session_` | `session_20260903_0912`          |
| Journal entry | `journal_`    | `journal_20260903_1030`          |

Verse IDs follow `verse_<book>_<chapter>_<verse>`, book slug lowercased with no
spaces (`songofsolomon`). Everything else is `<prefix><slug>` where the slug is
lowercase, `_`-separated, and descriptive.

### Open strings over enums
`roles`, relationship labels, `motif` names, `depthTags`, media `role`, etc. are
free-form data. Adding a new kind should mean adding data, not editing a code
enum. Code may *recognise* certain known strings (e.g. to pick an icon) but must
degrade gracefully for unknown ones.

### The `metadata` bag
Every content entity may carry `"metadata": {}` — an open object for speculative
or one-off fields. Prove a field is needed in `metadata` before promoting it to
a first-class schema field.

### Content vs. user state
Content entities (Verse, Topic, Character, …) are shared/seed data and live in
`data/*.json`. User state (progress, sessions, journal) is per-user and lives in
`window.storage`. **They never share object identity** — resetting progress must
not be able to delete a verse. See §7.

---

## 2. Content entities

### Verse — *live*
```json
{
  "id": "verse_genesis_22_8",
  "reference": "Genesis 22:8",
  "book": "Genesis",
  "chapter": 22,
  "verse": 8,
  "text": "Abraham said, \"God will provide himself the lamb for a burnt offering, my son.\" So they both went together.",
  "translation": "WEB",
  "topicIds": ["topic_faith", "topic_trust"],
  "characterIds": ["char_abraham", "char_isaac"],
  "storyIds": ["story_binding_of_isaac"],
  "motifIds": ["motif_substitutionary_sacrifice"],
  "depthTags": ["intro"],
  "metadata": {}
}
```
- `book` / `chapter` / `verse` are structured fields alongside the display
  `reference` string — needed for sorting, range queries, and the browse UI over
  the full corpus. Emitted by `pipeline/parse_books.py`. *(Live since
  2026-09-03; §8.2.)*
- `translation` stays a string. WEB is the only value today; do not hardcode
  that assumption anywhere. See §10.
- `storyIds` / `motifIds` / `depthTags` are **new**, all optional, default `[]`.
- **No `progress` field.** Progress lives in user state (`rooted-progress`),
  keyed by verse id — see §7. (Done 2026-09-03; §8.1.)

### Topic — *live*
```json
{
  "id": "topic_greed",
  "name": "Greed",
  "description": "Wanting more than enough, and trusting wealth over God.",
  "relatedTopicIds": ["topic_contentment", "topic_envy"],
  "depthTags": [],
  "metadata": {}
}
```
- `relatedTopicIds` is a flat, untyped, symmetric adjacency list — fine for
  "topics connect to topics" as long as the only relationship is "related."
- The moment we want *typed* topic relations ("contrasts with", "leads to",
  "is a form of"), migrate these edges to **Connection** (§2 Connection) and
  leave `relatedTopicIds` as a derived convenience or drop it. Don't add a
  second embedded array.

### Character — *live* (95 characters: 17 Genesis, 8 Exodus, 5 Ruth, 2 Leviticus, 4 Numbers, 2 Joshua, 10 Judges, 7 1 Samuel, 9 2 Samuel, 10 1 Kings, 12 2 Kings, 9 Chronicles)
```json
{
  "id": "char_jacob",
  "name": "Jacob",
  "alsoKnownAs": ["Israel"],
  "roles": ["renamed Israel", "father of the twelve tribes"],
  "eraId": "era_patriarchs",
  "summary": "Isaac and Rebekah's younger twin...",
  "verseIds": ["verse_genesis_28_15"],
  "mediaIds": ["media_char_jacob_portrait"],
  "depthTags": [],
  "metadata": {}
}
```
- `eraId` replaced the old free-string `era` (`"Patriarchs"`) — *(done
  2026-09-04; §8.3)*.
- **`roles` must distinguish the person.** Three men all tagged `"patriarch"`
  told the reader nothing; roles are what the People list shows under each name,
  so they should be the phrase you'd use to place someone — `"called out of
  Ur"`, `"the promised son"`, `"sold his birthright"`. Free strings
  (philosophy #1); `charIcon()` pattern-matches a few known words for an icon
  and falls back to a generic one.
- `alsoKnownAs` is **planned** — for search (Abram/Abraham, Saul/Paul).
- **No `relationships[]` on Character.** Family links are **Connection**
  records (below), queried at render time by `characterRelationships()`. Done
  2026-09-04, §8.4 — this was the textbook case for the generic entity: the
  links are typed ("son of"), directional, and browsable in their own right.
- **No `storyIds` / `lifeEventIds` on Character.** Those point the other way —
  `Story.characterIds` and `LifeEvent.characterId` / `participantIds` — and the
  app derives a character's stories and timeline from them
  (`characterStories`, `characterTimeline`). One direction only, so the two
  can't disagree.
- `verseIds` / `mediaIds` stay as embedded id arrays — cheap, stable, and drive
  lookups the UI does constantly.

### Story — *live*
A narrative unit — one episode. Bigger than a verse, smaller than a book.
```json
{
  "id": "story_binding_of_isaac",
  "title": "The Binding of Isaac",
  "summary": "God tests Abraham by asking him to sacrifice Isaac; a ram is provided in his place.",
  "primaryReference": "Genesis 22:1-19",
  "verseIds": ["verse_genesis_22_1", "verse_genesis_22_8", "verse_genesis_22_14"],
  "characterIds": ["char_abraham", "char_isaac"],
  "eraId": "era_patriarchs",
  "topicIds": ["topic_faith", "topic_trust"],
  "motifIds": ["motif_substitutionary_sacrifice", "motif_mountain_encounter"],
  "canonicalOrder": 1201,
  "depthTags": ["intro"],
  "metadata": {}
}
```
- `canonicalOrder` — an integer for rough chronological/narrative sorting across
  the whole OT. Sparse on purpose (leave gaps: 100, 110, 120 …) so stories can be
  inserted without renumbering. Not a claim about exact dates. Lesson from
  adding Numbers (§8.16): leave gaps between *books*, not just within one —
  Ruth's block (700-740) left no room for Numbers' 7 stories, which sit
  earlier in the timeline (wilderness wandering, before the Judges period).
  Fixed by bumping Ruth's block to 800-840. Had to bump it **again** to
  900-940 when Judges (§8.19) needed room in the same 730-800 gap — leave a
  bigger gap between books than seems necessary the first time, not just
  when a collision actually happens. Renumbering itself is cheap (it's
  curation data, not user data) — just re-run `build_stories.py` after.
  The payoff showed up at Chronicles (§8.24): its 11 stories slot
  *between* existing Samuel/Kings stories (David's temple prep just before
  Solomon at 1196–1198; the kings of Judah interleaved with the northern
  kings at 1305/1315/1335/1465/1475/…) with no renumbering, purely
  because the 10-wide gaps were already there.
- `verseIds` must be verses that **ship in the starter pack**, so a story page
  can always render them as cards; `build_stories.py` enforces this. The full
  span always lives in `primaryReference`, which is a display string, not ids.
- Story-to-story links (foreshadows / parallels / fulfilled-by) are
  **Connections**, not an embedded array. Not built yet.

### Era — *live*
A broad period, used for the timeline and "who else lived then."
```json
{
  "id": "era_patriarchs",
  "name": "The Patriarchs",
  "summary": "Abraham, Isaac, Jacob, and Joseph; the family through which the nation of Israel begins.",
  "order": 3,
  "approxRange": "c. 2000–1650 BC",
  "metadata": {}
}
```
- `order` — integer, sequences the eras.
- `approxRange` — free string; scholarship varies and we don't want to imply
  false precision.
- **An era's display text can go stale as content accumulates under its id.**
  `era_exodus` was named "The Exodus begins" / "in Egypt" when it only held
  the plagues and Sinai; by the time Leviticus, Numbers, and Deuteronomy (40
  years later, at the Jordan) had all been folded into the same id, the name
  no longer honestly described most of what was in it. Fixed (2026-09-04,
  §8.17) by rewriting `name`/`summary`/`approxRange` to span the whole
  wilderness period — the `id` never changes, so no character's `eraId`
  reference needed touching. Worth rereading an era's display text each time
  a book that extends it is added, not just its id.

### LifeEvent — *live*
One dated-ish moment in a person's life. The unit behind the character timeline
("highlights of their life").
```json
{
  "id": "event_abraham_call",
  "characterId": "char_abraham",
  "participantIds": ["char_abraham", "char_sarah", "char_lot"],
  "title": "Called to leave Haran",
  "description": "Yahweh tells Abram to leave his country for a land he will be shown, with the promise of becoming a great nation.",
  "reference": "Genesis 12:1-9",
  "storyId": "story_call_of_abram",
  "eraId": "era_patriarchs",
  "sequenceInLife": 1,
  "ageApprox": 75,
  "metadata": {}
}
```
- `characterId` is the primary subject — the person whose timeline this event
  belongs to. `participantIds` is everyone in the scene; the build script
  **prepends the subject automatically**, so curation only lists the others.
- `sequenceInLife` — integer ordering within that character's life. Sparse
  (10, 20, 30 …); `build_stories.py` rejects duplicates per character.
- `ageApprox` — optional; only when the text actually gives it.
- `eraId` is inherited from the event's story when omitted.
- `storyId` is optional — a few events (Abraham's death, Rachel's death) belong
  to no curated story. In the app those timeline entries simply aren't tappable.
**"Who else was around then"** is deliberately computed from real co-occurrence
rather than from an era label. `sharesScenesWith(charId)` collects everyone who
appears in the same life events or stories — that's evidence, not a guess. Era
grouping is shown separately and labelled honestly ("Also in The Patriarchs"),
because an era spanning four generations does *not* make Abraham and Joseph
contemporaries. Genuine parallel-story links will be **Connections**
(`"contemporary of"`, `"parallels"`) when that's built.

### Motif — *live* (15 motifs)
A recurring biblical pattern (younger-son-chosen, exile-and-return,
barren-woman-given-a-child, water-in-the-wilderness…).
```json
{
  "id": "motif_younger_son_chosen",
  "name": "The younger son is chosen",
  "description": "God repeatedly bypasses the firstborn and the cultural rule of primogeniture.",
  "exampleReferences": ["Genesis 25:23", "Genesis 48:14", "1 Samuel 16:11"],
  "depthTags": ["deep"],
  "metadata": {}
}
```
- **Motif instances** (this motif shows up in that story / character / verse)
  are **Connections** — `fromType: "motif"`, `toType: "story" | "character" |
  "verse"`, `relationship: "instance of"`, `inverse: "has motif"`. No separate
  MotifInstance entity; this was the deliberate demonstration of the generic
  Connection pattern (§8.4), and it's live now — `motifInstances()` /
  `motifsFor()` fall straight out of `connectionsFor()`, no new query logic.
- **`build_motifs.py` requires ≥2 `exampleReferences`.** A "motif" with one
  occurrence is just a fact about that one story — not curated as a motif
  until a genuine second instance exists in the content. (Done 2026-09-04,
  §8.12): 6 motifs, each with real instances in the current content — not
  force-fit onto single occurrences.

### Media — *planned*
Illustrations, maps, decorative art. A **separate linked entity** so art style,
multiple images, and dark-mode variants can change without touching content.
```json
{
  "id": "media_char_david_portrait",
  "type": "image",
  "role": "portrait",
  "subjectType": "character",
  "subjectId": "char_david",
  "src": "media/char_david.png",
  "alt": "Illustrated portrait of a young David with a sling and a lyre.",
  "style": "warm-storybook",
  "variants": [{ "scheme": "dark", "src": "media/char_david_dark.png" }],
  "credit": "",
  "metadata": {}
}
```
- `role` — free string; expected values `portrait`, `scene`, `map`,
  `decorative`.
- `subjectType` / `subjectId` — what the media is *of*. Also discoverable from
  the subject via its `mediaIds` array.

### Connection — *live* (the generic relationship entity)
One directed, typed edge between any two entities. Replaces embedded
relationship arrays. Design philosophy #4.
```json
{
  "id": "conn_isaac_child_of_abraham",
  "fromType": "character",
  "fromId": "char_isaac",
  "relationship": "child of",
  "toType": "character",
  "toId": "char_abraham",
  "symmetric": false,
  "inverse": "parent of",
  "notes": "The child of the promise, born to Abraham at 100 and Sarah at 90.",
  "depthTags": [],
  "metadata": {}
}
```
Rules:
- Store **one** directed edge. If `symmetric` is true (`"sibling of"`,
  `"contemporary of"`), the app shows it from both ends. If not, `inverse` gives
  the label to show from the other end (`"child of"` ⇄ `"parent of"`); the app
  derives the reverse view rather than storing a second row.
  `build_connections.py` requires exactly one of `inverse` / `symmetric` on
  every edge, so a reverse view is never silently missing.
- `fromType` / `toType` are entity-type strings: `character`, `story`, `verse`,
  `topic`, `motif`, `era`.
- What belongs in Connection: anything typed with a label, anything carrying
  `notes`, anything the user browses as a relationship itself, motif instances,
  story→story (foreshadows / parallels / fulfilled by), typed topic→topic.
- What stays an embedded id array: plain membership/tagging lookups the UI does
  constantly — `Verse.topicIds`, `Verse.characterIds`, `Story.verseIds`,
  `Character.storyIds`, etc.

**Live since 2026-09-04 (§8.4)**, migrated from `Character.relationships[]`:
26 connections replace 51 embedded entries — most relationship facts had been
stored twice (Abraham "husband of" Sarah *and* Sarah "wife of" Abraham as two
separate embedded rows); Connection stores each fact once and derives the
other direction. The migration also **found a gap for free**: Abraham→Hagar
had no reverse entry in the old data, so Hagar's page never showed she was his
wife — `connectionsFor()` now derives it correctly from the one stored edge.
`data/connections.json` is small and loaded at boot alongside `stories.json`,
outside the content overlay (nothing here is user-editable yet).

---

## 3. Challenge system — *partial* (interface + 4 types)

Challenge types are **data-described and pluggable**, not a hardcoded switch
(design philosophy #5). Implemented in `index.html` as the `CHALLENGE_TYPES`
registry (§8.2, §8.5).

### ChallengeType
Each entry is `config` data + methods:
```js
challenge_fill_blank: {
  id: 'challenge_fill_blank',
  name: 'Fill in the blank',
  appliesToEntityTypes: ['verse'],
  config: { blankRatio: 0.3, maxBlanks: 4, minWordLength: 4 },
  enabled: true,
  build, render, check, score, /* interact?, controls? */   // the interface below
}
```

### Shared generator interface
Every type implements the same contract, so `startPractice` / `renderPractice` /
`checkPractice` never branch on the type:

| Method | Contract |
|--------|----------|
| `build(entity, config)` | → opaque `state` object; holds everything render/check need. Called once per queue item at `startPractice`. Must init `checked:false`. |
| `render(state)` | → HTML string. Reads `state.checked` to switch between the input view and the graded view. Must preserve what the user entered once `checked`. |
| `check(state)` | reads its own DOM (it knows its selectors), **mutates** `state` (`checked=true`, per-item results, `allCorrect`), returns `{ allCorrect, correctCount, total }`. |
| `score(state)` | → number 0..1 (fraction correct). Called after grading, whichever route finalized it (`check` or a self-grading `interact`). |
| `interact(state, ds)` | *optional.* Handles a tap on an element the type rendered with `data-action="practice-interact"` (`ds` = that element's `dataset`). Mutates `state`; the flow re-renders. If it sets `state.checked` itself (a self-graded type finalizing), the caller does the same session bookkeeping `check()` would have — see `challenge_first_letters`. Used by scramble for tap-to-place; unused by fill-in-blank (native inputs). |
| `controls(state)` | *optional.* HTML for the action-button area while `!state.checked`, replacing the generic "Check" button. For a type whose finalization isn't a single auto-graded tap — a self-graded reveal needs a "Reveal" step and then two grading buttons, not one "Check". |

Session shape: `{ challengeTypeId, queue:[{verseId, state}], index, results:[{verseId, allCorrect, score}] }`.
`startPractice(verseIds, challengeTypeId)` — `challengeTypeId` defaults to
`settings.challengeTypeId` (persisted to `rooted-settings`; chosen via the
segmented picker on Home, shown whenever ≥2 verse types are `enabled`).

**challenge_scramble** — words become tappable chips; tap to place in order,
tap a placed chip to return it. For verses longer than `config.maxWords` (14)
only a random contiguous window is scrambled and the rest shown as fixed
context, so long verses stay playable.

**challenge_first_letters** ("Progressive reveal") — **self-graded**, unlike
the other two. Every word is shown as its first letter plus underscores for
the rest (`don't` → `d__'_`, punctuation and apostrophes left alone — it walks
characters rather than assuming letters are contiguous, so it doesn't mis-blank
words with internal punctuation). The user recalls the verse from memory, taps
**Reveal** to see the full text, then **Got it** / **Missed it** grades their
own recall — there's no DOM input to check a string against, which is why this
type needed `interact` + `controls` rather than the `check`-button path. This
is the type that proved those two additions to the interface were worth having.

**challenge_verse_ladder** ("Verse ladder") — **self-graded**, same family as
Progressive reveal, built the same day as a Tier 1 engagement feature (see
§8's checklist). Instead of one reveal/hide toggle, words disappear in
graduated steps — `config.stageRatios: [0, 0.25, 0.5, 0.75, 1]` — climbing
from the full text down to first-letters-only (`hintWord()`, the same
helper `challenge_first_letters` uses). `build()` picks one random word
order and keeps it fixed for the whole climb, so each stage's hidden set is
always a **superset** of the one before — nothing that's already hidden
ever reappears, which is what makes it feel like a ladder rather than a
reshuffle. `interact()` handles two different taps: `data-advance` moves to
the next rung without finalizing (a plain re-render, same as scramble's
tap-to-place), `data-selfgrade` finalizes at the last rung exactly like
Progressive reveal's Got it/Missed it. `controls()` switches between a
single "Hide more" button and the two-button self-grade pair depending on
which rung the state is on.

Planned types (all `appliesToEntityTypes: ["verse"]` unless noted):
`challenge_fill_blank` (built), `challenge_scramble` (built),
`challenge_first_letters` (built), `challenge_verse_ladder` (built),
`challenge_type_it_out`, `challenge_reference_match`,
`challenge_story_order` (`["story"]`), `challenge_character_match`
(`["character"]`). Adding one = a new registry entry, nothing else.

---

## 4. Depth / difficulty layers

Any content entity may carry `depthTags: string[]` (free strings, e.g. `intro`,
`standard`, `deep` — think Sunday-school vs. seminary). Empty = shown at all
depths. The app has one active depth setting (user state, §7) and filters
content whose `depthTags` are non-empty and don't include the active depth.
Nothing is *hidden* by default — depth is opt-in tagging.

---

## 5. Storage layout

| Path / key | Contents | Notes |
|------------|----------|-------|
| `data/starter-pack.json` | curated first-run seed: 652 verses + 35 topics + 95 characters | loaded on first run; **generated** by `build_starter_pack.py` |
| `pipeline/curation/starter_pack.json` | the hand-curation behind the above | verse ids + topic/character links + the Topic and Character records; **never** verse text |
| `pipeline/curation/topic_lexicon.json` | keyword hints per topic | input to `tag_verses.py` only; never becomes tags |
| `data/verses.json` | full parsed WEB corpus (14,478 verses: Genesis, Psalms, Exodus, Ruth, Leviticus, Numbers, Deuteronomy, Joshua, Judges, 1 Samuel, 2 Samuel, 1 Kings, 2 Kings, 1 Chronicles, 2 Chronicles) | **generated** by `parse_books.py`; lazily fetched by the Browse screen on first open, then held in memory (`corpus`) |
| `data/characters.json` | standalone characters, same curation as the starter pack | **generated** by `build_starter_pack.py` from the same curation; not read by the app |
| `data/stories.json` | 9 eras, 134 stories, 329 life events | **generated** by `build_stories.py`; loaded at boot (small) |
| `data/motifs.json` | 15 motifs | **generated** by `build_motifs.py`; loaded at boot (small) |
| `data/connections.json` | 117 Connection edges | **generated** by `build_connections.py`; loaded at boot (small), outside the content overlay |
| `media/` | *planned* | illustration assets referenced by Media entities |
| `window.storage: rooted-content` | user overlay `{ verses, topics, characters }` | **done** — merged over seed by id at load (`mergeContent`); only written once the user adds/edits something |
| `window.storage: rooted-progress` | map of `verseId → VerseProgress` | **done** — §7 |
| `window.storage: rooted-sync-meta` | `{ updatedAt }` — local edit clock for cloud sync | **done** — §7.1, stamped by `touchSyncMeta()` on every content/progress/settings write |
| `window.storage: rooted-sessions` | practice session log | planned — optional / trimmable |
| `window.storage: rooted-journal` | discovery journal entries | planned — §7 |
| `window.storage: rooted-settings` | preferences (`challengeTypeId` so far; depth, goals planned) | *partial* — §7, `saveSettings()` |
| `window.storage: rooted-app-data` | pre-split single blob | legacy — migrated once on boot by `migrateLegacy`, then ignored |
| Cosmos DB `RootedDB/UserData` (partition key `/userId`) | one document per signed-in user: `{ id, userId, identityProvider, content, progress, settings, updatedAt }` | **done** — §7.1, optional cloud mirror of the four keys above, written via `api/src/functions/sync.js` |

> The content/progress split (§8.1) is implemented. On first boot after the
> split, an existing `rooted-app-data` blob is read once: entities not in the
> seed become the `rooted-content` overlay, per-verse `progress` sub-objects
> become the `rooted-progress` map, and the old key is left in place but no
> longer read.

> **Local dev:** `window.storage` is a Claude-runtime API. When the page is
> opened from a plain web server, `index.html` installs a `localStorage`-backed
> fallback with the same shape (top of the `<script>`, `if(!window.storage)`).
> So data persists per-browser during local testing. Reset it with
> `localStorage.clear()` in the console.

Seed vs. user data merge rule: **seed files are the source of truth for seed
ids.** User edits to a seed entity are stored as an overlay in `rooted-content`
and re-applied on load, so pulling a new seed pack doesn't silently clobber the
user, and doesn't silently lose their edits either.

One refinement (`mergeEntity`, `LINK_FIELDS`): an **empty** link array in the
overlay never blanks out a non-empty one from the seed. A verse added from
Browse is stored with `topicIds: []`; when a later starter pack ships that same
id *with* topics and characters attached, the seed's links fill in rather than
being erased. Non-empty user links still win. This matters on the normal path,
not just as an edge case — every starter-pack expansion adds content for ids
some users already hold.

---

## 6. Full-corpus pipeline — *live* (`pipeline/`, see `pipeline/README.md`)

Everything in `data/` is generated. **Never hand-edit `data/*.json`.**

- **`pipeline/parse_books.py`** — WEB Bible JSON
  (`TehShrike/world-english-bible`, CC0) → `data/verses.json`. Handles prose
  books (`paragraph text`) and poetic books (`line text`), grouping entries by
  chapter+verse and joining in `sectionNumber` order; skips Psalm
  superscriptions (`header`, no verse number). Normalises smart quotes to ASCII
  and collapses whitespace; keeps em dashes. Emits `book`/`chapter`/`verse`.
  Knows all 66 book slugs; `--all` parses the whole Bible. Downloads cached in
  `pipeline/.cache/` (git-ignored).
- **`pipeline/build_starter_pack.py`** — `pipeline/curation/starter_pack.json`
  (verse ids + topic/character links + the full Topic and Character records)
  joined against the corpus → `data/starter-pack.json` **and**
  `data/characters.json` (same source, so they can't drift). Validates every
  cross-reference; dangling ids are a hard error. Emits **no `progress` field**.
  `--check` verifies without writing.

- **`pipeline/build_stories.py`** — `pipeline/curation/stories.json` →
  `data/stories.json` (eras, stories, life events). Validates every era / story /
  character / participant / topic / verse reference, rejects duplicate
  `sequenceInLife` per character, and requires every character to have at least
  one life event and every story at least one character or verse. Prepends each
  event's subject to `participantIds` and inherits `eraId` from the story.
- **`pipeline/build_motifs.py`** — `pipeline/curation/motifs.json` →
  `data/motifs.json`. Requires ≥2 `exampleReferences` per motif — a pattern
  with one occurrence is just a fact about that one story.
- **`pipeline/build_connections.py`** — `pipeline/curation/connections.json` →
  `data/connections.json`. Requires exactly one of `inverse` / `symmetric` per
  edge, rejects an edge connecting an entity to itself, rejects the same fact
  stored twice, and validates every `fromId`/`toId` against the entity types
  that exist so far (`character`, `story`, `topic`, `verse`, `era`, `motif`).
  Run **after** `build_stories.py` and `build_motifs.py` — it validates
  against their output.
- **`pipeline/tag_verses.py`** — a curation *aid* that writes nothing. Reads
  `curation/topic_lexicon.json` (keyword hints per topic) and prints ranked
  candidate verses for a human to hand-pick, ranked by keyword hits then
  memorisable length. `--report` shows per-topic coverage.

Verse text lives **only** in the corpus — the curation file holds selection and
links, never a copy of the text. Rebuilding reproduces the shipped data exactly.

**Topic tagging is hand-curated, not generated.** Auto-tagging the whole corpus
was considered and rejected: keyword matching can't read metaphor or context
("fear of Yahweh" is reverence, not anxiety), and for practice you want 10–30
strong verses per topic rather than thousands of noisy ones. The lexicon
surfaces candidates; a person picks.

Re-verify the source is still public domain before reproducing verse text in
bulk. This does **not** extend to copyrighted translations (see CLAUDE.md NIV
note).

---

## 7. User-state entities

### VerseProgress
```json
{
  "verseId": "verse_genesis_1_1",
  "status": "learning",
  "timesReviewed": 3,
  "lastScore": true,
  "lastPracticedAt": "2026-09-03T09:12:00.000Z",
  "nextReview": "2026-09-06T09:12:00.000Z",
  "history": [
    { "at": "2026-09-03T09:12:00.000Z", "challengeTypeId": "challenge_fill_blank", "score": 1 }
  ]
}
```
- `status` ∈ `new | learning | review | mastered` (drives the simple SRS
  interval ladder already in `scheduleNext`). **Display only** — never the
  stored value itself — these map to the brand-flavored labels Seedling /
  Rooted / Flourishing / Mastered (`MASTERY_LABELS`/`masteryLabel()` in
  `index.html`), so a status rename never means a data migration.
- Stored as a map keyed by `verseId` under `rooted-progress`. A verse with no
  entry is treated as `new`.
- `history[]` is also what streaks are derived from (`computeStreak()`,
  `practiceCountsByDay()`) — no separate storage, purely a new view over
  data already being recorded on every `recordPractice()` call. A Home
  activity heatmap was built on top of `practiceCountsByDay()` and then
  removed the next day on feedback (§27) — the function stays regardless,
  since `computeStreak()` needs it and it's the natural data source if a
  heatmap comes back on a future profile screen. Streak days are
  calendar days in the **viewer's local timezone** (history timestamps are
  UTC ISO strings) — a streak resetting at UTC midnight instead of the
  user's own midnight would feel broken. A streak counts back from
  yesterday, not today, if nothing's logged yet today — the day not
  having happened yet shouldn't read as a broken streak.

### PracticeSession *(optional, for stats)*
```json
{
  "id": "session_20260903_0912",
  "startedAt": "2026-09-03T09:12:00.000Z",
  "endedAt": "2026-09-03T09:18:00.000Z",
  "challengeTypeId": "challenge_fill_blank",
  "source": { "type": "due" },
  "results": [{ "verseId": "verse_genesis_1_1", "score": 1 }]
}
```
`source.type` ∈ `due | topic | verse | character | story` (+ an `id` when scoped).

### JournalEntry — *planned* ("discovery journal")
```json
{
  "id": "journal_20260903_1030",
  "createdAt": "2026-09-03T10:30:00.000Z",
  "title": "Wells and betrothals",
  "body": "Isaac, Jacob, and Moses all meet their wives at a well...",
  "links": [
    { "type": "story", "id": "story_rebekah_at_the_well" },
    { "type": "motif", "id": "motif_meeting_at_a_well" }
  ],
  "tags": ["type-scene"]
}
```

### Settings — *partial*
```json
{ "challengeTypeId": "challenge_scramble", "dailyGoal": 10, "activeDepth": "standard" }
```
- `challengeTypeId` — live. Default `challenge_fill_blank`; falls back to it if
  the stored id is unknown.
- `dailyGoal` — live. Default 10. Caps how many due verses a practice session
  pulls (`practiceQueue`), so the 247-verse seed doesn't all come due at once on
  a fresh install. No UI to change it yet; Home shows "Practice 10 of 247 due".
- `activeDepth` — planned (§4).

### 7.1 Cloud sync — *live* (optional, opt-in)

The app is a static site with no backend by default — `window.storage`
(§5) is always the fast, offline-capable source of truth, and everything
above this subsection works exactly as described with zero network calls.
Cloud sync is a second, optional layer on top, for a visitor who signs in:
the same four keys (`rooted-content`, `rooted-progress`, `rooted-settings`,
`rooted-sync-meta`) additionally mirror to one Cosmos DB document via
`/api/sync` (`api/src/functions/sync.js`), so a second device can pick up
the same library and progress. Signing in is never required — an
anonymous visitor never calls `/api/sync` at all (see `pullAndMerge()` /
`pushToCloud()` in `index.html`, both no-ops when `account` is null).

**Identity.** Auth is Azure Static Web Apps' built-in platform
authentication, not app code — `/.auth/login/github` and `/.auth/logout`
are plain links, no OAuth app registration needed for GitHub specifically
(one of SWA's "pre-configured" providers). `/.auth/me` returns the signed-in
`clientPrincipal` (`{userId, userDetails, identityProvider, userRoles}`);
`userId` is the partition key and document id in Cosmos. Switching the
login provider later (the owner's explicit intent — GitHub was chosen for
zero setup, not because it's final) means enabling a different SWA
provider — but note each provider yields a **different** `userId` for the
same person, so it's a fresh account under the new provider, not a
migration. If provider portability ever matters, that's a future problem
to solve deliberately (e.g. a provider-agnostic account entity), not
something the current design gets for free.

**Sync bundle** (one Cosmos document per user):
```json
{
  "id": "gh|1234567",
  "userId": "gh|1234567",
  "identityProvider": "github",
  "content": { "verses": [...], "topics": [...], "characters": [...] },
  "progress": { "verse_genesis_1_1": { "...VerseProgress" } },
  "settings": { "challengeTypeId": "challenge_scramble", "dailyGoal": 10 },
  "updatedAt": "2026-09-06T10:30:00.000Z"
}
```

**Merge strategy: whole-bundle last-write-wins, not per-field.** Every
local edit stamps `rooted-sync-meta.updatedAt` (via `touchSyncMeta()`,
called from `saveContent`/`saveProgress`/`saveSettings`). On sign-in (and
on demand via the "Synced" / "Sync failed" tap target in the Home account
bar), `pullAndMerge()` compares that local timestamp against the cloud
document's `updatedAt`: whichever is newer **replaces the other side
entirely** — not a per-verse or per-field merge. Deliberately simple for
v1: correct for "one person, a couple of devices," not for editing the
same account offline on two devices at the same time (the older side's
changes since the last sync would be lost in that case). A field-level
merge is a clean future upgrade if that ever becomes a real problem — see
"Known gaps" in CLAUDE.md.

**Security boundary.** The Cosmos connection string lives only as a
Function App setting (`COSMOS_CONNECTION_STRING`, set in the Azure Portal,
never in the repo or in client JS). `staticwebapp.config.json` restricts
`/api/*` to the `authenticated` role at the platform level; `sync.js` also
independently decodes the server-verified `x-ms-client-principal` header
itself and never trusts a `userId` from the request body — defense in
depth, not reliance on either layer alone.

**Local backup (export/import) reuses this bundle shape.** §7.1's
`{content, progress, settings}` shape isn't just the Cosmos document — it's
also exactly what `exportBundle()` downloads as a `.json` file and what
`importFromFile()` reads back in (`index.html`, Home's "Your data" card).
One shape, three places (`localStorage` keys split apart, one Cosmos
document, one export file) rather than three different serializations to
keep in sync. Unlike cloud sync, export/import needs no sign-in — it's the
fallback for the anonymous case cloud sync doesn't cover, and a manual
safety net regardless (a single device's `localStorage` is still one
browser-data-clear away from gone). Import is a deliberate, confirmed,
whole-bundle overwrite of local state — not a merge, and not automatic.

---

## 8. Current state → target: migration checklist

1. ~~**Drop `progress` from seed files.** Move to `rooted-progress` map keyed by
   verse id. Update `boot()` / `scheduleSave` to split content vs. progress
   instead of one `rooted-app-data` blob.~~ **Done (2026-09-03).** Seed files
   carry no `progress`. `index.html` now has `content` (overlay → `rooted-content`),
   `progress` (map → `rooted-progress`), and `data` (seed + overlay, rendered).
   `scheduleNext` → `recordPractice(verseId, correct, challengeTypeId)`, which
   also appends a `history` entry. `migrateLegacy` handles the old blob.
2. ~~**Add structured `book` / `chapter` / `verse`** to the Verse schema and the
   parser output; backfill existing seed verses.~~ **Done (2026-09-03)**, as
   part of rebuilding the pipeline (item 7). All 3,994 corpus verses and all 17
   starter verses carry them.
3. ~~**`Character.era` (string) → `eraId` (ref).** Create `era_*` entities; add
   `data/stories.json` (or an eras file).~~ **Done (2026-09-04).** 3 eras;
   `data/stories.json` carries eras, stories and life events. People are grouped
   by era, and `Character.roles` were rewritten to actually distinguish people
   (three men reading "patriarch" told the reader nothing).
4. ~~**`Character.relationships[]` → Connection.** Create `data/connections.json`,
   move the ~20 embedded edges, add `symmetric` / `inverse`. Update the
   character detail screen to read Connections.~~ **Done (2026-09-04).**
   26 connections replace 51 embedded entries (most facts had been stored
   twice, once per direction). `pipeline/build_connections.py` requires
   `inverse` or `symmetric` on every edge and validates every reference.
   `connectionsFor()` / `characterRelationships()` derive the reverse view at
   render time. Caught a real gap in the old data for free: Abraham→Hagar had
   no reverse entry, so her page never said she was his wife.
5. ~~**Factor fill-in-blank into the ChallengeType interface** (§3) before adding
   scramble.~~ **Done (2026-09-03).** `CHALLENGE_TYPES` registry;
   `buildBlanks`/hardcoded practice flow replaced by `build/render/check/score`.
   Also fixed: typed answers no longer vanish from the blanks after "Check".
   Then **`challenge_scramble` added** as a second registry entry (2026-09-03)
   — validated the interface: only new code was the registry entry, the
   optional `interact` hook, a `set-challenge` action, and the Home picker.
   Introduced `rooted-settings` (§7) for the persisted type choice. Then
   **`challenge_first_letters` added** as a third (2026-09-04) — this one
   needed two more optional interface members, `interact`-driven finalization
   and `controls`, because self-grading doesn't fit the "one auto-graded Check
   tap" shape the first two types share. See §3.
6. ~~**Wire `data/characters.json` in or delete it** — right now it's dead weight
   duplicating the characters inside `starter-pack.json`.~~ **Resolved
   (2026-09-03).** Still not read by the app, but it's now *generated* from the
   same curation as the starter pack, so the duplicate can't drift. Wire it in
   or drop it whenever there's a reason to.
7. ~~Rebuild the `pipeline/` scripts (§6).~~ **Done (2026-09-03).**
   `parse_books.py` + `build_starter_pack.py` + `curation/starter_pack.json` +
   `pipeline/README.md`. Verified to reproduce the shipped corpus and starter
   pack byte-for-byte (plus the new structured fields). The rebuild's
   cross-reference validation also caught a pre-existing dangling id —
   `char_abraham` → `char_ishmael`, a character that didn't exist — fixed by
   adding Ishmael (characters: 10 → 11).
8. ~~**Wire the full corpus into the app** — needs verse search/browse UI, since
   3,994 verses can't go in one list.~~ **Done (2026-09-03).** New Browse
   screen (5th nav item): search across all verses by text or reference, or
   drill book → chapter → verse. Corpus is lazily fetched on first open
   (`loadCorpus`), never at boot, and not precached by the service worker.
   Adding a verse copies it into the user's `rooted-content` overlay, so it
   immediately joins the practice rotation. See §9.

9. **Topic tagging at scale.** **Done (2026-09-03).** Seed grew from 17 verses /
   15 topics to **230 verses / 27 topics / 270 tag assignments**, every topic
   carrying 6–14 hand-picked verses, every Topic now with a real `description`
   and populated `relatedTopicIds` (the topic-to-topic graph the vision asks
   for). Approach: `tag_verses.py` surfaces candidates from a keyword lexicon,
   a human picks — see §6. Genesis verses also gained `characterIds`, so
   character detail pages went from 0–2 verses to up to 18.
10. ~~**`Story` / `Era` / `LifeEvent` entities.**~~ **Done (2026-09-04).**
    3 eras, 32 stories, 85 life events. Character detail now leads with a
    **timeline** ("Their life"), then Family (the `relationships[]` data, which
    had never been rendered), Stories, Key verses, "Appears alongside"
    (co-occurrence) and "Also in <era>". New Story detail screen and a Stories
    list grouped by era, reached from People. See §9.
11. **Expand beyond Genesis.** **Started (2026-09-04)** with Moses' early life
    (Exodus 2–4): `era_exodus`, 6 characters (Moses, Jochebed, Miriam, Aaron,
    Pharaoh's Daughter, Zipporah), 4 stories, 20 life events, 8 connections,
    17 curated verses, 1 new topic (`topic_deliverance`). `parse_books.py`
    now ships Exodus in the corpus too (5,207 verses total). The pipeline made
    the *text* side trivial (`--books exodus`); the curation/content side —
    picking verses, writing stories and life events, tagging — is still real
    work per book, and is what actually took the time here.
12. **`Motif` entity, and story→story Connections.** **Done (2026-09-04).**
    5 motifs (`build_motifs.py`), each with 3 real instances in the existing
    content — not force-fit onto single occurrences; a motif with fewer than 2
    is rejected by the builder. New "Patterns" screens (list + detail),
    reached from People; a "Pattern" badge row on Character and Story detail
    pages. Also the first story↔story Connection (`"parallels"`, symmetric):
    Joseph's brothers deceiving Jacob with a blood-soaked coat directly
    mirrors Jacob deceiving Isaac with animal skins — shown as "Related
    stories" on the Story detail page. `motifInstances()` / `motifsFor()` /
    `relatedStories()` all fall straight out of the existing `connectionsFor()`
    — no new query machinery, which is exactly what making Connection generic
    back in §8.4 was for.
13. **Expand beyond Genesis, continued: the whole book of Ruth.** **Done
    (2026-09-04).** `era_judges` (order 5, after `era_exodus`); 5 characters
    (Ruth, Naomi, Boaz, Elimelech, Orpah); 5 stories covering all 4 chapters;
    19 life events; 19 curated verses; 1 new topic (`topic_loyalty` — human
    steadfastness, distinct from `topic_faithfulness`'s framing around *God's*
    loving-kindness); 8 new connections including a levirate-marriage-shaped
    family (mother-in-law/daughter-in-law, sister-in-law, kinsman); and a 6th
    motif, `motif_famine_and_a_foreign_land`, whose two instances are
    `story_jacob_to_egypt` (Genesis) and the new `story_famine_to_moab` (Ruth)
    — the first motif to span two different books, which is exactly the kind
    of connection this whole schema exists to make visible. Same repeatable
    shape as the Exodus expansion: parse the book, pick verses, write stories
    and events, tag, then look for what it echoes in what's already there.
14. **Finish the book of Exodus (chapters 5–40).** **Done (2026-09-04).**
    9 more stories (the plagues, the Passover, the Red Sea, the song of the
    sea, manna and water, the battle with Amalek, the covenant at Sinai, the
    golden calf, the tabernacle's glory); 2 new characters — **Pharaoh**
    (never named in the text; represents the throne rather than committing to
    one ruler across the narrative) and **Joshua** (introduced here on
    purpose, well before the book that will bear his name); 34 curated verses;
    a 7th motif, `motif_intercession_for_others`, connecting Abraham's plea
    for Sodom (`story_pleading_for_sodom`, Genesis) to Moses' plea for Israel
    after the golden calf (`story_golden_calf`, Exodus) — two people risking
    everything to stand between God's judgment and people who did nothing to
    earn mercy. No new topics needed; the existing 29 already covered this
    content well, a sign the topic set is maturing.

    **Going forward, book order is canonical** (owner's direction,
    2026-09-04): Exodus → Leviticus → Numbers → Deuteronomy → Joshua → ...
    Ruth landed earlier, out of order, and stays — it isn't being undone,
    this just governs what comes next. **Leviticus is a different shape of
    problem** — see §11.
15. **Leviticus.** **Done (2026-09-04).** Owner's choice from §11's three
    options: **Story treatment for the few real narrative incidents**, on top
    of a verses-and-topics pass across the legal material. 3 new stories (the
    ordination of Aaron, Nadab and Abihu's death, the blasphemer stoned) —
    genuinely all the narrative Leviticus has in 27 chapters; 2 new characters
    (Nadab, Abihu — Aaron's sons, needed for the second story); 19 curated
    verses across the law, including Leviticus 19:18 ("love your neighbor as
    yourself" — from here, not the New Testament) and 11:44/19:2 ("be holy,
    for I am holy"); 2 new topics, `topic_holiness` and `topic_love`, neither
    of which the existing 29 could honestly cover; and the first
    `"contrasts with"` story↔story Connection — the ordination and Nadab-and-
    Abihu stories are a deliberate pair in the text itself (the same fire
    from Yahweh that accepts one offering kills two sons for another, days
    apart), so the relationship label needed to say that rather than reuse
    `"parallels"`. No new era — Leviticus happens while Israel is still
    camped at Sinai, so its content stays in `era_exodus`.
16. **Numbers.** **Done (2026-09-04).** Back to the narrative playbook — Numbers
    is much more story-shaped than Leviticus, though it still has long
    census/law stretches that got the lighter verses-only treatment instead of
    forced Story records (reusing the §8.15 decision, as anticipated). 7 new
    stories: Miriam and Aaron oppose Moses, the twelve spies, Korah's
    rebellion, water from the rock a second time (Moses strikes instead of
    speaks — the reason he never enters Canaan), the deaths of Miriam and
    Aaron, the bronze serpent, Balaam's donkey. 4 new characters — Caleb,
    Korah, Eleazar (Aaron's successor, `son of`/`father of` Aaron via
    Connection), Balaam. 28 curated verses, including the Aaronic blessing
    (Numbers 6:24-26, no story needed — pure verses-and-topics) and the
    messianic "a star will come out of Jacob" (24:17). No new topics — the
    existing 31 covered it.

    **Two new motifs, both spanning multiple books** — the clearest evidence
    yet that the schema is doing its job: `motif_wilderness_grumbling`
    (`story_manna_and_water` in Exodus; `story_water_from_the_rock_again` and
    `story_bronze_serpent` in Numbers) and `motif_unauthorized_holy_things`
    (`story_nadab_and_abihu` in Leviticus; `story_korahs_rebellion` in
    Numbers). Neither would be visible without Connection already existing
    from §8.4, and neither needed anything new built to add — just more
    `motif → story` edges in `curation/connections.json`.

    Required bumping Ruth's `canonicalOrder` block (700-740 → 800-840) to make
    room for Numbers' 7 stories, which sit earlier in the timeline — see the
    Story `canonicalOrder` note above.
17. **Deuteronomy.** **Done (2026-09-04).** Almost entirely Moses' three
    farewell speeches, so — reusing the §8.15 decision again, as anticipated —
    the lighter Leviticus-style pass: verses and topics throughout, Story
    treatment for its only two genuine narrative beats. `story_moses_
    commissions_joshua` (31:1-8, 34:9 — Moses lays hands on Joshua before all
    Israel) and `story_moses_views_and_dies` (34:1-12 — Nebo, the land he
    won't enter, his death at 120, the eulogy that no prophet like him has
    arisen since). No new characters or topics — both Moses and Joshua already
    existed, and the existing 31 topics covered everything, including the
    Shema (6:4-5) and "man does not live by bread alone" (8:3). One new
    Connection kind: `"successor of"` (Joshua → Moses, `inverse: "predecessor
    of"`). `motif_gods_reassurance` picked up a 4th instance, directly on a
    verse rather than a story: Deuteronomy 31:23, God's "I will be with you"
    at Joshua's commissioning — the same words Isaac and Jacob heard
    generations earlier, now said to a successor at a leadership handoff.

    Also corrected `era_exodus`'s display text (see the Era section above) —
    stale since it still read "The Exodus begins" / "in Egypt" after three
    more books' worth of content, spanning 40 years and ending at the Jordan,
    had been folded into the same era id.
18. **Joshua.** **Done (2026-09-04).** Narrative again — the full playbook,
    same as Genesis/Exodus/Numbers. New era, `era_conquest` (order 5, between
    `era_exodus` and `era_judges`, which moved to order 6). 9 stories: Joshua
    takes charge; Rahab and the spies; crossing the Jordan; the fall of
    Jericho; Achan's sin and the second battle for Ai; the Gibeonite
    deception; the sun standing still; Caleb receiving Hebron (a direct
    payoff of a promise from `story_twelve_spies` in Numbers, 45 years
    earlier — extends Caleb's existing timeline rather than starting a new
    arc); Joshua's farewell ("as for me and my house, we will serve
    Yahweh," 24:15). 2 new characters — Rahab, Achan. 28 curated verses. No
    new topics — the existing 31 covered it again.

    Two motif payoffs: `motif_gods_reassurance` picked up a **5th** instance
    (Joshua 1:5, "as I was with Moses, so I will be with you" — spoken at the
    very moment Joshua's leadership begins, echoing Deuteronomy 31:23's
    instance at his commissioning one book earlier). And a new motif,
    `motif_foreign_woman_of_faith` (`story_rahab_and_the_spies` in Joshua;
    `story_ruth_clings_to_naomi` in Ruth) — two women with no claim on Israel
    or its God who choose both anyway, and both end up ancestors of David.
    Neither motif needed new code; both are `motif → story`/`verse`
    Connection edges, same as every motif since §8.4.
19. **Judges.** **Done (2026-09-04).** Narrative again, the full playbook —
    but **no new era**. Judges' setting is exactly the period `era_judges`
    already describes (it was created for Ruth); rewrote that era's summary
    at the same time, since it had only ever talked about Ruth and now needed
    to describe the judge cycle honestly too — same lesson as `era_exodus` in
    §8.17, applied proactively this time instead of after the fact. 6 stories:
    Ehud and Eglon; Deborah, Barak, and Jael; Gideon and the three hundred;
    Jephthah's vow; Samson's birth; Samson and Delilah. 10 new characters —
    more than any prior single-book pass, because Judges simply names more
    distinct people per episode than Genesis/Exodus/Numbers/Joshua did.
    34 curated verses. No new topics — the existing 31 covered it, again.

    A new motif, `motif_who_am_i_reluctant_call` (Exodus 3:11, Moses at the
    burning bush; Judges 6:15, Gideon at the wine press) — both told they're
    being sent, both immediately arguing they're the wrong person, before
    either does anything the calling actually required. Both instances
    attach directly to **verses**, which exposed a real gap: `motifsFor()`
    already worked generically for any entity type, but the UI only ever
    called it from Character and Story detail — verse-attached instances
    (this motif, plus two of `motif_gods_reassurance`'s five) had nowhere to
    show a "Pattern" badge at all. Fixed by adding the same
    `renderMotifBadges(motifsFor('verse', id))` call to `renderVerseDetail`
    that Character and Story pages already had. Worth checking for this kind
    of gap whenever a new attachment point for an existing generic pattern
    shows up — the query layer being generic doesn't guarantee the UI kept up.

20. **1 Samuel.** **Done (2026-09-04).** Narrative again, the full playbook.
    New era, `era_united_kingdom` (order 7) — Israel's first three kings.
    10 stories: Hannah's prayer (and giving Samuel to Eli); Samuel's call
    and Eli's death when the ark is captured; Israel demanding a king;
    Saul's rejection ("to obey is better than sacrifice"); David anointed
    while still a shepherd; David and Goliath; David and Jonathan's
    covenant; Saul hunting David through the wilderness (who spares him
    twice rather than raise a hand against Yahweh's anointed); the witch of
    Endor; the deaths of Saul and Jonathan at Gilboa. 7 new characters
    (Hannah, Eli, Samuel, Saul, David, Goliath, Jonathan). 38 curated
    verses. 1 new topic, `topic_obedience` (Saul's rejection needed it —
    existing topics didn't cover "obeying a direct command" specifically).

    3 new Connections: Hannah "mother of" Samuel, Saul "father of"
    Jonathan, Eli "raised" Samuel (a relationship kind not seen before —
    not a blood relation, but a real one worth naming). Two existing
    motifs gained instances rather than needing new ones: David becomes
    `motif_younger_son_chosen`'s 4th instance (youngest of Jesse's sons,
    same shape as Isaac, Jacob, and Joseph), and Saul's "am I not a
    Benjamite, of the smallest of the tribes of Israel, and my family the
    least of all the families of the tribe of Benjamin?" (1 Samuel 9:21)
    becomes `motif_who_am_i_reluctant_call`'s 3rd instance, alongside Moses
    and Gideon — attached directly to a verse, the same shape §8.19 already
    wired a badge for. No new UI or query code needed for either — pure
    payoff from Connection being generic since §8.4.

21. **2 Samuel.** **Done (2026-09-04).** Narrative again, the full playbook.
    **No new era** — folds into the same `era_united_kingdom` §8.20
    created for 1 Samuel, since it's the same period continuing directly
    (David's reign), not a new one. 10 stories: David's lament for Saul and
    Jonathan; David becomes king over all Israel and takes Jerusalem;
    Michal despises David for dancing before the ark; God's covenant with
    David's house; David's kindness to Mephibosheth for Jonathan's sake;
    David and Bathsheba, and the killing of Uriah; Nathan's confrontation
    ("you are the man"); the rape of Tamar and Absalom's revenge on Amnon;
    Absalom's rebellion; the death of Absalom. 9 new characters (Michal,
    Bathsheba, Uriah, Nathan, Absalom, Tamar, Amnon, Mephibosheth, Joab) —
    more than any prior single-book pass (Judges' 10 was spread across 6
    stories; these 9 concentrate across the second half of one book). 39
    curated verses. No new topics — the existing 32 (temptation,
    repentance, justice, betrayal, sorrow, loyalty, forgiveness) covered
    every beat without needing more.

    11 new Connections, including a relationship kind not seen before:
    `"daughter of"` as the inverse of `"father of"` when the child is
    female (Saul → Michal), matching the pattern already established for
    mothers (Jochebed → Miriam, §8.3). A new motif,
    `motif_prophet_confronts_the_king`, connects Samuel telling Saul "to
    obey is better than sacrifice" (1 Samuel 15:22-23, already curated) to
    Nathan telling David "you are the man" (2 Samuel 12:1-7) — not
    recognized as a motif until this second real instance existed, per the
    standing rule. Both instances attach to **stories**, not verses, so no
    new UI wiring was needed — `renderMotifBadges` on Story detail already
    handled it.

22. **1 Kings.** **Done (2026-09-04).** Narrative again, the full
    playbook. New era, `era_divided_kingdom` (order 8) — `era_united_kingdom`
    (§8.20) stays as-is for Solomon's reign, since it's still the same
    period as David's; the new era starts at the split. 12 stories: Solomon
    crowned over his older brother Adonijah; Solomon asks for wisdom
    instead of riches; Solomon's judgment between two women over a baby;
    building and dedicating the temple; the queen of Sheba; Solomon's
    downfall into idolatry through his foreign wives; the kingdom divides
    when Rehoboam rejects the elders' counsel; Jeroboam's golden calves at
    Dan and Bethel; Elijah fed by ravens and sustaining a widow through
    famine; Elijah's contest with the prophets of Baal on Mount Carmel;
    Elijah at Horeb; Naboth's vineyard. 10 new characters (Solomon,
    Adonijah, the queen of Sheba, Rehoboam, Jeroboam, Elijah, the widow of
    Zarephath, Ahab, Jezebel, Naboth) — the most in a single pass so far,
    reflecting how many named figures 1 Kings introduces. 40 curated
    verses. 1 new topic, `topic_idolatry` (golden calves and Baal worship
    needed it — nothing existing fit cleanly).

    7 new Connections: 5 family (David→Solomon, Bathsheba→Solomon,
    David→Adonijah, Solomon→Rehoboam, Ahab↔Jezebel) plus 2 motif
    instances. No new motifs — two existing ones gained real instances
    instead: Solomon becomes `motif_younger_son_chosen`'s 5th (crowned
    over his older brother Adonijah, the same shape as Isaac, Jacob,
    Joseph, and David), and Elijah confronting Ahab over Naboth's murder
    becomes `motif_prophet_confronts_the_king`'s 3rd, alongside
    Samuel/Saul (§8.19) and Nathan/David (§8.21) — a pattern now
    established across three different prophets and three different
    kings. Both instances attach to entities the UI already had badges
    wired for (character and story respectively), so again no new query
    or rendering code.

23. **2 Kings.** **Done (2026-09-06).** Narrative again, the full
    playbook. New era, `era_exile` (order 9) — but only for the last
    story; everything up to the fall of Jerusalem is still the divided
    monarchy, so `era_divided_kingdom` carries the other 12 new stories.
    13 stories: Elijah taken up in a whirlwind and Elisha taking his
    mantle; the widow's oil; the Shunammite woman's son; Naaman healed
    (and Gehazi's greed); the chariots of fire; the siege of Samaria
    lifted; Jehu and the death of Jezebel; the death of Elisha; the fall
    of the northern kingdom to Assyria; Hezekiah and Sennacherib;
    Hezekiah's illness; Josiah and the rediscovered Book of the Law; the
    fall of Jerusalem. 12 new characters (Elisha, Naaman, Gehazi, the
    Shunammite woman, Jehu, Hezekiah, Sennacherib, Isaiah, Josiah,
    Huldah, Nebuchadnezzar, Zedekiah). 57 curated verses. 1 new topic,
    `topic_prayer` — Hezekiah's two prayers (2 Kings 19:15-19, 20:2-3)
    are model laments, and there was already a lot of prayer content
    (Hannah, Solomon's dedication, Elijah) to gather under it.

    5 new Connections: `"successor of"` reused for Elisha/Elijah (same
    as Joshua/Moses, §8.17), a first `"servant of"` (Gehazi/Elisha), and
    3 motif instances. One new motif, `motif_prophet_raises_a_dead_child`
    — Elijah reviving the widow of Zarephath's son (1 Kings 17, already
    curated) and Elisha reviving the Shunammite woman's; a real second
    instance turned an isolated miracle into a pattern. `motif_gods_reassurance`
    also picked up its 6th instance (2 Kings 6:16, "those who are with us
    are more than those who are with them"), and its `exampleReferences`
    display list was brought current — it had still shown only the first
    three since §8.17/§8.18 added Deuteronomy 31:23 and Joshua 1:5 as
    Connections without touching the Motif record. Worth remembering that
    `exampleReferences` (a curated display sample on the Motif) and the
    Connection instances (what "Where it shows up" lists) are separate and
    can drift; keep the sample honest when adding instances.

24. **1–2 Chronicles.** **Done (2026-09-06).** Full playbook, done as one
    pass across both books, but deliberately **scoped to Chronicles-unique
    material**. Chronicles retells Samuel–Kings from a temple-and-Judah
    angle; duplicating stories the app already has (David's reign, the
    temple, the fall of Jerusalem) would just clutter the per-character
    and per-era views. So the curation added 11 new stories only where
    Chronicles genuinely adds something:
    - **David** (`era_united_kingdom`): the census and the threshing floor
      of Ornan becoming the temple site (1 Chr 21); David gathering
      materials and charging Solomon (1 Chr 22, 28); David's "all things
      come from you, and of your own we have given you" prayer (1 Chr 29).
    - **Kings of Judah** (`era_divided_kingdom`) — the ones Kings passes
      over fast: Abijah winning by reliance on Yahweh (2 Chr 13); Asa's
      early trust and late failure (2 Chr 14–16); Jehoshaphat sending the
      choir out ahead of the army, "the battle is not yours but God's"
      (2 Chr 20); Joash restoring the temple and then having the priest
      Zechariah stoned (2 Chr 24); Uzziah struck with leprosy for forcing
      his way into the temple (2 Chr 26); Hezekiah's great Passover
      (2 Chr 29–31); Manasseh's repentance in a Babylonian prison
      (2 Chr 33).
    - **The exile** (`era_exile`): the decree of Cyrus (2 Chr 36:22-23) —
      Chronicles ends on the road home.

    9 new characters (Abijah, Asa, Jehoshaphat, Joash, Jehoiada,
    Zechariah son of Jehoiada, Uzziah, Manasseh, Cyrus). 50 curated
    verses. 1 new topic, `topic_seeking_god` ("if you seek him, he will
    be found by you" is a Chronicles refrain — 1 Chr 28:9, 2 Chr 7:14,
    14:11, 15:2, 26:5, 31:21). 6 family Connections fill in the Davidic
    line of Judah (Rehoboam→Abijah→Asa→Jehoshaphat; Hezekiah→Manasseh;
    Jehoiada→Zechariah; Jehoiada "raised" Joash). Two new motifs:
    `motif_stand_still_and_see` (Exodus 14:13-14 and 2 Chr 20:15-17,
    nearly the same words — its instances attach to `story_crossing_the_red_sea`
    and `story_jehoshaphats_battle`, so the badge now appears on the
    already-existing Exodus story too) and `motif_pride_before_the_fall`
    (Rehoboam and Uzziah — "when he was strong, his heart was lifted
    up"). `motif_prophet_confronts_the_king` gained a 4th instance,
    Zechariah/Joash — the variant where the king kills the messenger.
    2 Chr 7:14 and 7:1 were added to the **existing** 1 Kings temple
    story's `verseIds` rather than a new story — the pattern for parallel
    material going forward: extend the existing story, don't duplicate it.

25. **Cloud sync (§7.1).** **Done (2026-09-06).** The app's first backend.
    Content moved beyond OT books for this pass — three new resources:
    Azure Static Web Apps' linked/managed Functions API (`api/`, deployed
    from the same repo, same GitHub Actions pipeline, `api_location: "api"`
    in the workflow), Azure Cosmos DB for NoSQL (Free Tier — 1000 RU/s +
    25 GB, free forever, not a 12-month trial), and SWA's built-in
    authentication (GitHub, zero OAuth-app registration needed). One
    endpoint, `GET/POST /api/sync`, one document per user
    (`RootedDB/UserData`, partition key `/userId`). Client-side:
    `pullAndMerge()` / `pushToCloud()` / `touchSyncMeta()` in `index.html`,
    plus an account bar (`renderAccountBar()`, on the Settings screen —
    moved off Home on 2026-09-08 feedback, see §26) that's invisible
    scaffolding when signed out — an anonymous visitor never calls
    `/api/sync` and the app behaves exactly as it did before this pass.

    Chose **offline-first with whole-bundle last-write-wins sync** over
    "server is the source of truth" — deliberately, since the PWA's
    offline-capable identity predates this and shouldn't regress. Real
    tradeoff, not a hidden detail: editing the same account on two devices
    offline at the same time can lose one side's changes on next sync — see
    §7.1 for why that's an acceptable v1 scope, not an oversight.

    `staticwebapp.config.json` gained `/api/*` → `allowedRoles:
    ["authenticated"]` (platform-level gate) on top of `sync.js`'s own
    server-side principal check (defense in depth, not reliance on either
    alone). `COSMOS_CONNECTION_STRING` is a Function App setting, set once
    directly in the Azure Portal — deliberately never passed through chat
    or written to a file by an agent, after an earlier attempt to do
    exactly that (with a GitHub PAT, for the initial repo push) was
    correctly blocked by a safety guardrail. That became the standing
    pattern for every credential since: portal-direct, or a scoped
    mechanism that never puts the secret in a command or a tracked file
    (the SSH deploy key set up for pushing to GitHub is the other example).

26. **Local backup: JSON export/import (§7.1).** **Done (2026-09-08).**
    Closes the gap §25 left open — cloud sync only covers signed-in users,
    and this app's default, expected mode is anonymous. Two buttons on a
    "Your data" card: **Export** (`exportBundle()` / `downloadExport()`)
    downloads `rooted-backup-<date>.json` in exactly the same `{content,
    progress, settings}` shape as the Cosmos document, plus
    `app`/`exportedAt`; **Import** (`validateImportBundle()` /
    `importFromFile()`) reads a file back in. Validation is lenient by
    design — a file can contain any subset of the three keys (e.g. someone
    might hand-edit a settings-only file) — but rejects anything with none
    of them, or a field that's present but the wrong shape, with a specific
    error rather than a silent no-op or a crash. Import always confirms
    before acting (`confirm()`) since it's a **whole-bundle overwrite** of
    local state, not a merge — matches the same "don't get clever" choice
    made for cloud sync's merge strategy (§7.1), for the same reason: this
    is a manual, occasional, deliberate action, not something that needs
    to survive concurrent edits.

    Both this card and the account bar (§25) landed on Home first, then
    moved to a new **Settings** screen (gear icon, top-right of Home) the
    same day, on direct feedback: occasional-use controls were pushing the
    actual daily-use content (due-today stats, the Practice button) below
    the fold. `renderSettings()` in `index.html`. Standing rule from this:
    account/settings-shaped additions default to Settings, not Home.

27. **Streaks, activity heatmap, and brand mastery labels (§7).**
    **Done (2026-09-08).** First of the post-cloud-sync Tier 1 engagement
    features (owner's prioritized list). Zero new storage — purely new
    views over `VerseProgress.history[]`, already written by
    `recordPractice()` since day one: `computeStreak()` and
    `practiceCountsByDay()` derive everything from it. Home's stat row
    gained a 4th card ("day streak"). `status`'s raw values
    (`new|learning|review|mastered`) now always render through
    `masteryLabel()` → Seedling/Rooted/Flourishing/Mastered, replacing an
    ad hoc label object that lived inline in the verse-detail renderer.
    "Rooted" as the mid-tier label is a deliberate small pun on the app's
    own name, not an accident.

    Also shipped in this pass: a compact 7×7 practice-activity heatmap
    below the stat row (calendar-style, day-of-week columns, shown only
    once there was activity to show). **Removed the very next day
    (2026-09-09)** on direct feedback — didn't land well on Home. Not
    ruled out entirely: the owner floated a future profile screen as
    where it might belong instead (ties into the accounts-required
    direction — see the `rooted-product-vision` memory). `renderHeatmap()`
    was deleted along with its CSS; `practiceCountsByDay()` stayed, since
    `computeStreak()` depends on it and it's the obvious data source to
    reuse if a heatmap comes back. The streak stat card and mastery labels
    from this same pass were **not** part of the complaint and stayed as-is.

28. **Verse Ladder, a 4th challenge type (§3).** **Done (2026-09-09).**
    Second Tier 1 engagement feature. Progressive word-stripping — full
    text down to first-letters-only across 5 graduated stages, self-graded
    at the end. No changes needed anywhere outside the `CHALLENGE_TYPES`
    registry itself — `startPractice`/`renderPractice`/`practiceInteract`
    stayed untouched, which is exactly the payoff the pluggable interface
    (§8.5) was built for. Full test coverage including a real end-to-end
    session run through the actual `startPractice()`/`practiceInteract()`
    dispatch (not just calling the type object's methods directly), which
    is what actually proves `interact()`'s "advance without finalizing,
    then finalize on the last tap" two-mode behavior works through the
    real event-handling path, not just in isolation.

29. **Visual system v2 — surfaces over outlines, one accent system.**
    **Done (2026-09-09).** Direct response to owner feedback that the app
    "doesn't look like a polished app in the market... looks basic" and
    should read as premium — the same **warm-storybook direction**
    (unchanged, still the decision on record; see "Visual direction"
    below), executed with real elevation and hierarchy instead of flat
    fills and 1px borders everywhere. The owner supplied a precise brief
    (six numbered rules, exact hex values) after reviewing a design-system
    artifact showing the direction across four real screens before
    anything touched the live app. Six changes, all in `index.html`:

    - **Surfaces, not outlines.** `--paper` → `#F8F5EE` (warm stone), card
      surfaces (`--paper-raised`) → pure `#FFFFFF`, every `border:1px
      solid var(--line)` on a content surface (`.card`, `.stat-card`,
      `.navbar`, buttons, inputs, `.segmented`, `.chapter-cell`, chips,
      `.back-btn`) replaced by `box-shadow:var(--shadow-card)` (`0 4px
      20px rgba(44,34,30,.05)`) or, for small controls, dropped to a
      filled `--surface-sunken` background instead. `--line` itself is
      redefined from a solid hex to `rgba(44,34,30,.08)` — an actual
      hairline, used only for dividers now (§4 below), never a card edge.
      Where a border carried real *state* meaning rather than decoration
      — scramble chip correct/wrong/picked, chapter-cell `:active` — the
      border stayed, just moved to `border:1px solid transparent` as its
      neutral resting state so the colored state override still has
      something to color.
    - **Legible ink.** `--ink` → `#2C221E` (was `#3A2E22`), `--ink-soft` →
      `#756B63` (was `#7A6A55`), `--ink-faint` → `#A79C8E`.
    - **One accent system, three roles.** Gold (`--gold #D49E35`) for
      primary actions and urgency ("Due today"); sage (`--sage #2E7D32`
      on `--sage-wash #E8F5E9`) for progress/mastery ("Mastered"); a new
      neutral, tan (`--tan-deep #8C7357` on `--tan-wash #F1E9DA`), for
      plain metadata (topic tags, character roles, relationship-type
      labels) and avatar-placeholder fills. `--plum`/`--plum-deep`/
      `--plum-wash` are **removed entirely**, not recolored in place —
      `.tag.plum` had been doing two unrelated jobs (a verse's "due"
      status *and* a character's role pills), which is exactly the kind
      of accidental reuse "mismatched" badge colors usually comes from.
      Split into real modifier classes — `.tag--gold`, `.tag--sage`,
      `.tag--tan` — one semantic role each, fixed at both call sites
      (`renderVerseCard`'s status tag, `renderCharacterDetail`'s roles).
      Motif "Pattern" badges (`renderMotifBadges`) went to `tag--gold` —
      a discovery worth noticing, not neutral metadata.
    - **Rows over cards.** New `.list-row` pattern — borderless,
      `border-bottom:1px solid var(--line)` between rows, no fill of its
      own. Replaces `.card` in `renderCharacterRow()` (used by the People
      list, "Family," and "Appears alongside") and the Browse book list
      in `renderBrowseResults()`. Verse cards and stat cards **stay**
      cards — they're the hero/featured content this rule explicitly
      carves out, not plain rows.
    - **Hero headers.** New `.hero` pattern — big centered avatar (88px,
      up from a cramped 56px box), name as a real `<h1>`, tags, meta line,
      left-aligned summary below — replacing the old `.screen-head` +
      modest `.card` combo on **both** `renderCharacterDetail()` and
      `renderStoryDetail()` (story's hero uses a book icon in place of an
      avatar, and its title in the `<h1>` slot instead of a name).
    - **Floating frosted nav.** `.navbar` lifted off the screen edge
      (`left/right:16px; bottom:16px`), rounded (`border-radius:22px`),
      `backdrop-filter:blur(12px)` over `rgba(255,255,255,.88)`,
      `box-shadow:var(--shadow-nav)`. Active/inactive is a filled gold
      chip (new `.dot` wrapper span around each icon) rather than a
      filled/outline glyph swap — the pinned Tabler webfont version
      doesn't reliably ship true filled/outline pairs for every icon, so
      building the distinction into markup+CSS is more robust than
      depending on font variants that may not exist. `body`'s
      `padding-bottom` bumped 78px → 104px to clear the now-floating bar.

    Deliberately **not** touched: the Fraunces/Inter pairing (the brief
    was about surfaces/color/hierarchy, not typefaces), `--danger` (no
    complaint about it, already warm-toned), `.blank`/`.progress-track`/
    `.timeline::before`'s use of `--line` as a functional fill/connector
    color rather than a border (still correct at the new lighter value).

    Full regression suite (all prior feature passes) stayed green
    throughout — this was a pure presentation-layer pass, verified by a
    new dedicated test asserting the new patterns actually render
    (`.list-row` not `.card` in the right places, `.hero` present on both
    detail pages, zero remaining functional references to `plum`) rather
    than just trusting the diff.

    **Refinement pass, same day.** After looking at the deployed result,
    the owner sent four precise corrections: `--paper` deepened again to
    `#F3EFE6` (a richer linen than the first pass's `#F8F5EE`) and
    `--shadow-card`'s blur tightened to 16px; `body`'s `padding-bottom`
    raised 104px → 120px (with `!important`, specified explicitly — the
    floating nav was clipping the bottom-most content on a real device,
    a real bug the test suite couldn't have caught since it never
    measures rendered layout, only markup/CSS-source presence);
    `renderTopics()` converted from `.card` rows to `.list-row` (missed
    in the first pass — the brief's rule 4 named the book/people
    browsers explicitly but Topics is the same shape and should have
    been included); `.hero-avatar` resized 88px → 76px with a tighter
    `border-radius:20px` and a literal `#EFE9DC` fill (its icon color
    moved from gold to `--tan-deep` to stay coherent with that new warm
    -neutral fill, since the brief didn't specify one), `.hero h1` sized
    up to `2rem` with explicit `margin:12px 0 8px` replacing the avatar's
    own bottom margin so the two don't stack. Test suite extended with
    assertions for each of the four exact values (not just "changed
    somehow") — see `test_design_system.js`'s "v2.1 refinements" section.

---

## 9. How the app reads this data

### Corpus vs. library
An important distinction the UI depends on:
- **Corpus** (`corpus`, from `data/verses.json`) — reference material. Read-only,
  lazily loaded, never persisted to user storage, not in `data.verses`.
- **Library** (`data.verses`) — the seed pack plus whatever the user added.
  This is what Home lists, what topics filter, and what practice draws from.

`findVerse` only ever looks at the library. Browse results are rendered from the
corpus and marked "in your verses" when `findVerse(id)` hits — the same stable
id (`verse_genesis_1_3`) means adding is idempotent and a re-parse of the corpus
can never duplicate a verse the user already has.

### Derived, never stored twice
Several things the UI shows are computed at render time rather than kept as
fields, so two copies can never disagree:

| Shown | Derived from |
|-------|--------------|
| A character's timeline | `LifeEvent.characterId`, ordered by `sequenceInLife` |
| A character's stories | `Story.characterIds` |
| A character's family | `connectionsFor('character', id)` — one directed edge per fact, reverse label derived from `inverse`/`symmetric` |
| "Appears alongside" | shared `LifeEvent.participantIds` / `Story.characterIds` — real co-occurrence, not an era guess |
| "Also in <era>" | `Character.eraId`, and only for people *not* already listed above |
| A topic's verses | `Verse.topicIds` |
| Verses due today | `rooted-progress` + `isDue`, capped by `settings.dailyGoal` |
| A motif's instances | `connectionsFor('motif', id)` |
| Motifs a story/character/**verse** belongs to | `connectionsFor(type, id)` filtered to `otherType==='motif'` — wired into all three detail screens since §8.19; a motif instance can attach to any of the three, so the badge has to too |
| A story's related stories | `connectionsFor('story', id)` filtered to `otherType==='story'` |

---

## 10. Translations

`Verse.translation` is a per-verse string. WEB is the only value now and is
public domain. Rules:
- Never assume WEB in code — always read the field.
- NIV and other copyrighted translations require a license from the publisher;
  the path is their official API/licensing program, not embedding PDF text. See
  CLAUDE.md.
- If multiple translations land, add a small `Translation` registry entity
  (`{ id, abbrev, name, isPublicDomain, licenseNote }`) rather than scattering
  translation metadata.

---

## 11. Open questions

- Granularity of `canonicalOrder` / cross-OT event ordering — how precise do we
  actually want to be given genuine scholarly disagreement?
- Motifs: hand-authored only, or eventually surface "possible motif" suggestions
  for the user to confirm into the journal?
- Do user-added characters/verses get to participate in Connections and motifs,
  or are those seed-only for now?
- Multi-translation UI: side-by-side, toggle, or per-verse preference?
- ~~§8.14: how should Leviticus be curated?~~ **Resolved (2026-09-04),
  §8.15** — option (b): Story treatment for the ~3 genuine narrative
  incidents, verses-and-topics for the rest. The same question will come back
  for any future law-heavy book (large stretches of Numbers and Deuteronomy
  are also legal/instructional, not narrative) — reuse this decision rather
  than re-litigating it each time, unless the owner says otherwise.
