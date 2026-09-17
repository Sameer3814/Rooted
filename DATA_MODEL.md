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

### Character — *live* (254 characters — full 66-book Bible as of 2026-09-10, plus seven "deep study" supporting-cast slices (2 Samuel, Paul's circle, Genesis, 1 Samuel/Exodus/Numbers, the Gospels, Job/1 Kings/Esther/Acts, and Genesis/Numbers/Judges/2 Kings again), items 66-67 and 70-74 — see DATA_MODEL.md §8 for the running per-book/per-batch breakdown, no longer itemized here since it stopped being sustainable to keep current inline)
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

### Motif — *live* (20 motifs)
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
| `data/starter-pack.json` | curated first-run seed: 1,648 verses + 38 topics + 254 characters | loaded on first run; **generated** by `build_starter_pack.py` |
| `pipeline/curation/starter_pack.json` | the hand-curation behind the above | verse ids + topic/character links + the Topic and Character records; **never** verse text |
| `pipeline/curation/topic_lexicon.json` | keyword hints per topic | input to `tag_verses.py` only; never becomes tags |
| `data/verses.json` | full parsed WEB corpus — the entire 66-book Bible (31,098 verses; `DEFAULT_BOOKS` in `parse_books.py` has the exact list) | **generated** by `parse_books.py`; lazily fetched by the Browse screen on first open, then held in memory (`corpus`) |
| `data/characters.json` | standalone characters, same curation as the starter pack | **generated** by `build_starter_pack.py` from the same curation; not read by the app |
| `data/stories.json` | 16 eras, 284 stories, 730 life events | **generated** by `build_stories.py`; loaded at boot (small) |
| `data/motifs.json` | 20 motifs | **generated** by `build_motifs.py`; loaded at boot (small) |
| `data/connections.json` | 137 Connection edges | **generated** by `build_connections.py`; loaded at boot (small), outside the content overlay |
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
  pulls (`practiceQueue`), so the 1,648-verse seed doesn't all come due at once
  on a fresh install. UI: a 5/10/15/20/25 preset picker on Settings
  (`renderGoalCard()`, §8.31) — a chip set rather than a free-typed number
  input, so an invalid or extreme value is never possible.
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

30. **People search.** **Done (2026-09-09).** Live-filter search on the
    People screen, mirroring Browse's existing search UX exactly rather
    than inventing a new pattern: a `.search-wrap` input
    (`renderCharacters()`), a module-level query string (`peopleQuery`,
    parallel to `browse.q`), a 140ms-debounced `input` listener wired in
    `bindEvents()`'s global section, and a `renderPeopleResults()` /
    `refreshPeopleResults()` split so typing only re-renders the
    `#people-results` subtree — the input never loses focus or caret
    position mid-keystroke, same reasoning as Browse's search.

    Matches on **name or role**, case-insensitive substring — e.g.
    "king" surfaces every character whose `roles[]` mentions it. Worth
    doing given the project's standing rule that `Character.roles` are
    curated to actually distinguish people, not generic labels (CLAUDE.md)
    — that same specificity makes role search genuinely useful rather
    than a token gesture. Empty query still shows the original
    era-grouped view with the Stories/Patterns quick-link cards
    (`renderPeopleResults()`'s no-query branch) — search doesn't replace
    that, it's a second way in. No new storage; `peopleQuery` is
    view-only state, not persisted, matching how `browse.q` already
    behaves (search state does *not* reset on nav-bar navigation away
    and back, deliberately consistent between the two screens).

31. **`settings.dailyGoal` UI.** **Done (2026-09-09).** Closes a gap
    that's existed since `dailyGoal` was introduced (§8.1) — a working
    setting with no way to change it. `renderGoalCard()` on the Settings
    screen: a 5/10/15/20/25 preset picker reusing the existing
    `.segmented` chip component (same one the Home challenge-type picker
    already uses) rather than a free-typed number input, so there's no
    validation to write — every tap sets a known-good value. New
    `set-daily-goal` action in `onAction()`, same shape as the existing
    `set-challenge` handler it sits next to. Takes effect immediately
    (`practiceQueue()` and Home's "Practice N of M due" both read
    `settings.dailyGoal` live) and syncs like any other setting change —
    `saveSettings()` already called `touchSyncMeta()`, nothing new needed
    there. Tested through the real `onAction()` dispatch, not just the
    render function in isolation — confirms the string `dataset.id` a
    real click event delivers gets converted to a number before it's
    stored (`+id`), and that the new goal actually changes what
    `practiceQueue()` and Home produce, not just what the chip shows as
    active.

32. **Dynamic/tactile UX pass — "feel like Duolingo, keep warm
    storybook."** **Done (2026-09-09).** Five pieces, all in `index.html`:

    - **Tactile press feedback.** One shared rule —
      `transition: transform .15s cubic-bezier(.34,1.56,.64,1)` +
      `:active{transform: scale(.96)}` — across every tappable surface
      (`.btn`, `.chip`, `.navitem`, `.card.tap`, `.list-row.tap`,
      `.chapter-cell`, `.back-btn`), added once rather than touching each
      component's own block. Composes cleanly with each element's
      existing `:active` treatment (background/box-shadow/border-color
      changes) since `transform` is an independent property. Scramble
      chips also get a `chipIn` pop-in keyframe on every render — a
      lighter, more robust stand-in for a true FLIP slide-between-
      containers animation, which would need per-chip position tracking
      across two separate drop zones; this reads as "fluid placement"
      without that complexity.
    - **Plant-growth mastery stages, re-labeled.** `MASTERY_LABELS`
      (§7/§27) changed from plain text (Seedling/Rooted/Flourishing/
      Mastered) to explicit emoji growth stages: 🌱 Seedling → 🌿
      Sprouting → 🌳 Rooted → 👑 Flourishing. **Supersedes §27's naming**
      — "Rooted" moved from the *learning* tier to the *review* tier, and
      "Mastered" became "👑 Flourishing." `renderVerseCard()` also changed
      to show the growth-stage tag on **every** verse card regardless of
      status (previously only `mastered`/`due` got a tag at all) — colored
      `tag--sage` only for `mastered`, `tag--tan` for the three
      in-progress stages, deliberately not a 4th accent color; the emoji
      + copy carry the distinction, not more palette (keeps rule 3 from
      the visual-system pass, §29, intact: three roles, not four-plus).
    - **Daily-goal progress ring (Home).** `renderGoalRing()` — an inline
      SVG ring (`stroke-dasharray`/`stroke-dashoffset`, no library), shown
      only when something's due (same conditional as the Practice CTA).
      `todaysPracticeCount()` (new, sits by `computeStreak()`) reuses
      `practiceCountsByDay()` — zero new storage, another view over
      `VerseProgress.history[]`. Fill is capped at the goal even if more
      than the goal was practiced today (no overflow past a full ring).
    - **Session-complete celebration, and a real bug fix.** Rewrote the
      completion screen in `renderPractice()`: a slide-up entrance, a
      bounced-in icon, two staggered animated stat tiles (verses
      reviewed, current day streak — the *current* streak, since this
      session's practice may have just extended it), and a small
      CSS-only spark burst (`renderSparks()` — randomized-trajectory
      `<span>`s using a `rotate(var(--angle)) translateY(var(--dist))`
      technique, not a `<canvas>` + `requestAnimationFrame` particle
      system, which would cost real per-frame JS and battery for a
      decorative flourish that doesn't need it). **While rewriting this,
      found and fixed a real latent bug**: the old code did
      `session = null` unconditionally the moment the completion branch
      rendered — harmless on the very first render, but a background
      `render()` (a cloud sync landing, for instance — `pushToCloud()`/
      `pullAndMerge()` both call `render()`) arriving *before* the user
      tapped "Done" would silently reset the tally to "0/0 correct" on
      screen. Fix: stop nulling `session` in the render function (the
      branch condition, `session.index >= session.queue.length`, is
      already stable across repeated renders on its own) and only clear
      it when the user actually leaves — the "Done" button now uses the
      existing `exit-practice` action instead of a bare `go-home`.
    - **Sound and haptics.** `playSfx(type)` — `'tap' | 'correct' |
      'complete'` — synthesizes short tones via the Web Audio API
      (`OscillatorNode` + `GainNode` envelopes), no audio files, no new
      assets. One `AudioContext`, created lazily on first call (browsers
      require a user gesture before audio can start; `playSfx` is always
      called from inside a click-handler chain, so that's already
      satisfied). `hapticBuzz(pattern)` wraps `navigator.vibrate()`. Both
      wrapped in `try/catch` and silently no-op if unsupported (Web Audio
      blocked, or `navigator.vibrate` absent — notably all of iOS
      Safari) — sound and haptics are enhancement, never a dependency.
      Wired into the real interaction points: `checkPractice()` and the
      finalizing branch of `practiceInteract()` play `'correct'` +
      buzz only on a correct grade (not a generic tap-then-correct
      double-fire); a non-finalizing `practiceInteract()` (a chip
      pick/unpick, a Verse Ladder "Hide more") plays `'tap'`; the
      `next-practice` handler plays `'complete'` exactly when that
      increment crosses into "session finished." Gated by one new
      setting, `settings.soundEnabled` (default `true`, threaded through
      all four places `settings` gets constructed — boot, cloud-sync
      adopt, import-file adopt, the in-memory default) — a single mute
      toggle covers both sound and haptics, on a new "Sound & haptics"
      card on Settings (`renderSoundCard()`), since a study app needs an
      easy off switch for quiet settings, not just an on switch.

    Full test coverage (`test_dynamic_ux.js`): the shared tactile-press
    CSS rule and reduced-motion override actually present in source; the
    exact emoji label mapping; the ring's `stroke-dashoffset` math
    verified against the real formula for a known count/goal, including
    the over-100%-cap case; **the session-null bug reproduced and proven
    fixed** — render the complete screen twice in a row and confirm the
    tally doesn't change; sound/haptic calls verified via spy overrides
    through the *real* `checkPractice()`/`practiceInteract()`/
    `next-practice` dispatch (not called directly in isolation), including
    that both degrade to a graceful no-op with no `AudioContext` or
    `navigator.vibrate` available at all, matching what a real un-supporting
    browser looks like. Full existing regression suite (10 files) stayed
    green throughout.

33. **Ezra/Nehemiah.** **Done (2026-09-10).** Full playbook, done as one
    pass across both books — the first genuinely new narrative since
    Chronicles started retelling Samuel–Kings. A new era,
    `era_return_from_exile` (order 10), holds 12 stories:
    - **The first return** (Ezra 1–6): Zerubbabel and the priest Jeshua
      lead the exiles home and rebuild the altar despite fear of the
      surrounding peoples (Ezra 3); local adversaries get the work
      halted by royal decree for years (Ezra 4); Haggai and Zechariah
      spur a second start, Darius confirms Cyrus's original decree, and
      the temple is finished and dedicated with a Passover celebration
      (Ezra 5–6).
    - **Ezra's return** (Ezra 7–10): a generation later, Ezra — a
      priest-scribe who "set his heart to seek Yahweh's law, and to do
      it, and to teach" (Ezra 7:10) — leads a second return under a full
      grant of authority from Artaxerxes, then confronts the returned
      exiles' intermarriage with the surrounding nations with a public
      prayer of confession (Ezra 9–10).
    - **Nehemiah rebuilds the wall** (Neh 1–6): cupbearer to Artaxerxes
      in Susa, Nehemiah weeps and fasts on hearing the walls lie broken,
      gets the king's leave, and inspects the ruins by night before
      announcing his plan (Neh 1–2); Sanballat mocks and conspires
      against the builders, so Nehemiah arms half the workers while the
      other half builds (Neh 4); separately confronts the nobles over
      usury against the poor (Neh 5); finishes the wall in 52 days
      despite Sanballat's repeated traps and a hired false prophet
      (Neh 6).
    - **Renewal and reform** (Neh 8–13): Ezra reads the law aloud to the
      whole assembly — the people weep until told the day is holy,
      "the joy of Yahweh is your strength" (Neh 8:10) — and keep the
      Feast of Booths with the greatest gladness since Joshua's day,
      then confess corporately and seal a written covenant (Neh 8–9).
      Nehemiah's closing chapter has him return from a stint back in
      Persia to purge the temple of Tobiah, restore the Levites' pay,
      and enforce the Sabbath and marriage law — closing the book on his
      own recurring plea, "Remember me, my God, for good" (Neh 13:14).

    5 new characters (Zerubbabel, Jeshua — id `char_jeshua_priest`, kept
    distinct from Joshua son of Nun's `char_joshua` — Ezra, Nehemiah,
    Sanballat). 34 curated verses. No new topics: the existing 35 —
    `topic_prayer`, `topic_repentance`, `topic_scripture`,
    `topic_justice`, `topic_faithfulness`, `topic_seeking_god` among
    them — covered the material without strain. A new `"worked
    alongside"` symmetric Connection (the first relationship type that
    isn't family, succession, or servanthood) links Zerubbabel/Jeshua and
    Ezra/Nehemiah. One new motif, `motif_the_forgotten_law_rediscovered`
    — Josiah's rediscovery of the Book of the Law (2 Kings 22, already
    curated) and Ezra's public reading of it to a weeping-then-reforming
    assembly (Neh 8) — the same shape of a forgotten law found, met first
    with grief, then renewed covenant; a real second instance turned an
    isolated fact about Josiah into an actual pattern.

34. **Esther.** **Done (2026-09-10).** Full playbook, its own new era —
    `era_esther`, order 11. Deliberately **not** folded into
    `era_return_from_exile`: Esther's Jews never returned to Jerusalem at
    all, and the book's setting (the Persian court at Susa), cast, and
    concerns (survival as a minority under threat, not temple or wall
    rebuilding) are genuinely distinct from Ezra/Nehemiah's. Placed
    *after* `era_return_from_exile` in era order to match the project's
    stated policy of following Bible book order going forward (CLAUDE.md
    "Known gaps" §3, owner's direction 2026-09-04), even though
    Esther's events (under Ahasuerus/Xerxes, ~486-465 BC) fall
    chronologically *before* Ezra's and Nehemiah's returns (under
    Artaxerxes I, 458 and 445 BC) — the same trade-off already accepted
    for Ruth's placement. 8 stories, tracking the book's own tight plot
    beat for beat: Vashti deposed for refusing the king's summons; Esther
    crowned queen while concealing her people, and Mordecai's uncovered
    assassination plot (folded into the same story — both are Esther
    2, and the plot's payoff needs the character already established);
    Haman's promotion, Mordecai's refusal to bow, and the empire-wide
    decree to destroy the Jews; Mordecai's "for such a time as this" and
    Esther's "if I perish, I perish"; Esther's banquet invitation
    alongside Haman's gallows and his unplanned honoring of Mordecai
    (Esther 5-6, one story — the dramatic irony only lands if both
    halves of that night are together); Haman named and hanged on his
    own gallows; the decree reversed and Mordecai promoted; and the
    Jews' self-defense and the establishing of Purim (Esther 9-10, one
    story).

    5 new characters (Esther, Mordecai, Haman, Ahasuerus, Vashti). 23
    curated verses. No new topics — `topic_identity`, `topic_calling`,
    `topic_trust`, `topic_fear`, `topic_justice`, `topic_deliverance`,
    `topic_thanksgiving` already covered it. 3 new Connections: a third
    use of the `"raised"` relationship (introduced item 20, Eli/Samuel;
    reused item 24, Jehoiada/Joash) — Mordecai raised his orphaned cousin
    Esther as his own daughter — and two more `"husband of"` edges
    (Ahasuerus/Esther, Ahasuerus/Vashti). One new motif, `motif_hidden_identity_saves_the_people`
    — Joseph revealing himself to his brothers (Genesis 45:3, already
    curated) and Esther revealing she is a Jew to save her people
    (Esther 7:3-4) — the same shape of a Hebrew rising unrecognized in a
    foreign court, then revealing their identity at exactly the moment
    it can save their own people; a real second instance, not force-fit,
    since both stories independently hinge on concealment-then-reveal as
    the actual turning point, not an incidental detail.

    This closes out the Old Testament's historical narrative books
    (Joshua through Esther in Bible order). If continuing canonically,
    the poetic/wisdom books (Job, Psalms — already partly seeded,
    Proverbs, Ecclesiastes, Song of Songs) and the Prophets are what's
    left.

35. **Job, Proverbs, Ecclesiastes, Song of Solomon.** **Done
    (2026-09-10).** The owner asked to finish the rest of the Old
    Testament in one continuous pass; this is the first installment —
    the poetic/wisdom books.

    **Job** got the full playbook, including a new era — `era_job`,
    order 12. Deliberately not folded into any existing era: Job is set
    in "the land of Uz," never explicitly tied to Israel's own history,
    and its date is traditionally reckoned as very old, possibly
    pre-dating the patriarchs — there is no existing era it honestly
    belongs to. 4 stories track the book's real narrative frame (it
    isn't *only* poetry): **Job tested** — Satan argues Job's faith is
    only rewarded loyalty, and is allowed to take his children, wealth,
    and health in short order; Job refuses to curse God ("Yahweh gave,
    and Yahweh has taken away"). **Job's complaint and his friends'
    answers** (Job 3-37, one story spanning the whole poetic dialogue —
    splitting it further would fragment a single sustained argument) —
    Eliphaz leads the friends' case that suffering must be deserved;
    Job insists on his innocence while still crying out to God, and in
    the middle of despair declares "I know that my Redeemer lives."
    **Yahweh answers out of the whirlwind** — not with an explanation,
    but with a tour of creation's wonders Job cannot explain or
    control; Job repents not because his questions were answered but
    because he has now seen God himself ("I had heard of you by the
    hearing of the ear, but now my eye sees you"). **Job restored** —
    Yahweh rebukes Eliphaz and his companions by name, accepts Job's
    prayer for them, and gives Job double what he had before. 2 new
    characters: Job, and Eliphaz (the only one of the three friends
    given an individual Character record — he's the one Yahweh
    addresses by name in the rebuke, giving him real distinguishing
    significance the other two only share by association; Bildad and
    Zophar are named in the story text but don't get their own
    records). 14 curated verses.

    **Proverbs, Ecclesiastes, and Song of Solomon** got the lighter
    verses-and-topics treatment established with Leviticus — none of
    the three has a narrative to build Stories from. Proverbs alone
    contributed 37 curated verses (denser per chapter than almost
    anything curated so far — nearly every verse is independently
    quotable), Ecclesiastes 14, Song of Solomon 7 (chosen for taste as
    much as theme — the book's more explicit physical-description verses
    were skipped in favor of its more universally-resonant lines on
    love itself: "many waters can't quench love," "set me as a seal on
    your heart"). 3 new topics, all genuinely needed rather than
    force-fit: `topic_anger` (CLAUDE.md's own "vision" section names
    anger as an example practice topic, and Proverbs is saturated with
    it — "a gentle answer turns away wrath," "he who is slow to anger
    has great understanding"), `topic_friendship` ("a friend loves at
    all times," "iron sharpens iron," Ecclesiastes' "two are better
    than one"), and `topic_speech` ("death and life are in the power of
    the tongue," "a word fitly spoken is like apples of gold").

    Next: the Prophets — Isaiah, Jeremiah, Lamentations, Ezekiel,
    Daniel, then the Twelve (Hosea through Malachi).

36. **Isaiah.** **Done (2026-09-10).** No new era, no new characters —
    `char_isaiah` already existed (2 Kings pass, `eraId: era_divided_kingdom`),
    so this extended him rather than duplicating. His one real narrative
    beat, the call vision (Isaiah 6 — the seraphim's "Holy, holy, holy,"
    the coal that purifies his lips, "here am I, send me"), became
    `story_isaiahs_call`, slotted into the existing `era_divided_kingdom`
    at `canonicalOrder: 1478` (right at Uzziah's death, which the
    chapter dates itself by — between `story_uzziahs_pride` at 1475 and
    `story_fall_of_israel` at 1480). His single life event uses
    `sequenceInLife: 5`, before his two existing 2 Kings events (10, 20)
    — the call happens decades before Hezekiah's reign, and
    `sequenceInLife` only needs to be unique per character, not
    increment by a fixed step, so a value that sorts correctly ahead of
    existing events was enough. Isaiah 36-39 (Hezekiah and Sennacherib)
    is nearly word-for-word identical to 2 Kings 18-20 — already
    curated as `story_hezekiah_and_sennacherib` / `story_hezekiahs_illness`
    — so it was deliberately **not** re-curated as a duplicate story,
    continuing the "extend, don't clone" rule from the Chronicles pass
    (§8.24). The rest of the book (oracles of judgment and comfort, no
    narrative) got 39 curated verses spanning famous passages across all
    66 chapters — the call vision, the suffering-servant songs (Isaiah
    53), and the "comfort my people" / "those who wait for Yahweh"
    sequence in 40-66 — with **no new topics**: `topic_waiting`'s
    existing description ("the long gap between promise and
    fulfillment") already covers Isaiah's hope-in-exile material without
    needing a dedicated `topic_hope`.

37. **Jeremiah, Lamentations.** **Done (2026-09-10).** Unlike Isaiah,
    Jeremiah has substantial unique narrative content, so this got the
    full playbook: 4 new characters (Jeremiah; Baruch, his scribe;
    Ebed-Melech, the Ethiopian official who saved him from a cistern;
    Gedaliah, the governor assassinated within months of his
    appointment) and 6 new stories. Split across two *existing* eras by
    each story's own date rather than one fixed era per character —
    `era_divided_kingdom` for his call, the potter's house/temple-sermon
    persecution, and Baruch's burned-then-rewritten scroll (all
    pre-fall, under Josiah then Jehoiakim); `era_exile` for the cistern,
    Gedaliah's assassination, and the forced flight to Egypt (fall and
    aftermath, under Zedekiah and after). This meant threading new
    canonicalOrder values into an already-tight range (`story_jeremiahs_call`
    at 1508, between Manasseh's repentance at 1505 and Josiah's law
    rediscovery at 1510 — Jeremiah's call, in Josiah's 13th year,
    predates the law's rediscovery in his 18th) — a live example of why
    the pipeline README's "leave more canonicalOrder headroom than
    feels necessary" lesson (from Numbers bumping Ruth) matters even
    years into a project. Jeremiah's own protest at his call ("I don't
    know how to speak; I am a child," Jeremiah 1:6) is a clean 4th
    instance of `motif_who_am_i_reluctant_call` (Moses, Gideon, Saul) —
    added as a Connection, with the motif's `exampleReferences` updated
    to match. 19 curated verses for Jeremiah, no new topics. Lamentations,
    having no narrative of its own (it's poetry mourning an event
    already told), got 6 more curated verses standing independently,
    except one (Lamentations 1:12) folded into the *existing*
    `story_fall_of_jerusalem`'s `verseIds` rather than spawning a new
    story — continuing the "extend, don't clone" rule.

38. **Ezekiel.** **Done (2026-09-10).** No new era needed — Ezekiel
    prophesies entirely among the Babylonian exiles, so all 3 new
    stories fit the existing `era_exile`: his call vision by the river
    Chebar (the wheels-within-wheels throne vision, eating a scroll,
    made a watchman responsible to warn but not for whether Israel
    listens); his symbolic acts (besieging a clay tile of Jerusalem,
    lying bound on his side for the number of years of the nation's
    sin, then being forbidden to mourn his wife's sudden death as a
    sign that Jerusalem's fall will be too great a grief for ordinary
    mourning); and the valley of dry bones (Ezekiel 37 — a dead army of
    bones brought back to life as Yahweh's picture of national
    restoration for a people who had said "our hope is lost"). 1 new
    character (Ezekiel). `story_ezekiels_call` and
    `story_ezekiels_symbolic_acts` are both dated *before* Jerusalem's
    fall (canonicalOrder 1592, 1593 — ahead of
    `story_jeremiah_in_the_cistern` at 1595), while `story_valley_of_dry_bones`
    is dated after it (1608, following ch33's news that the city has
    fallen) — another case of a prophet's ministry needing per-story
    dating rather than one block placement, same lesson as item 37.
    18 curated verses, no new topics or motifs — the individual-
    responsibility oracle (Ezekiel 18, "the soul who sins shall die,"
    "I have no pleasure in the death of the wicked") and the new-heart
    oracle (Ezekiel 36:26-27) stand as independent curated verses
    rather than forced into a story, since they're declarative oracles,
    not narrated scenes.

39. **Daniel.** **Done (2026-09-10).** The most narrative-dense of the
    Prophets, so it got the fullest treatment of any book in this
    installment: 6 new characters (Daniel; Shadrach, Meshach, and
    Abednego — given individual records despite acting as an
    interchangeable trio throughout the text, matching the project's
    per-individual convention rather than inventing a group-record
    shape; Belshazzar; Darius the Mede) plus `char_nebuchadnezzar`
    extended (his existing summary only covered destroying Jerusalem —
    broadened to cover his defeat-by-wisdom, the furnace, and his own
    madness-then-restoration, a real part of his arc the 2 Kings-era
    summary had no reason to mention). 6 new stories, all in the
    existing `era_exile`: the king's food (ch1); Nebuchadnezzar's statue
    dream (ch2); the fiery furnace (ch3); Nebuchadnezzar's madness
    (ch4); the writing on the wall (ch5); the lions' den (ch6). Ordered
    by each event's actual date rather than book order — ch1 (605 BC,
    Nebuchadnezzar's first deportation) predates Ezekiel's call
    (593 BC), so `story_daniel_and_the_kings_food` sits at
    `canonicalOrder: 1590`, *before* `story_ezekiels_call` at 1592; ch5
    (Belshazzar, ~539 BC) and ch6 (Darius the Mede, right after) come
    much later, after the fall of Jerusalem and even after Gedaliah's
    assassination, so they sit at 1606 and 1609, just ahead of
    `story_cyrus_decree` at 1610. 26 curated verses, no new topics. One
    new motif, `motif_faithful_defiance_delivered`, connects the
    furnace and the lions' den — the book pairs these two stories with
    the same deliberate shape (refuse the king's command that would
    violate loyalty to God → sentenced to die for it → delivered in a
    way that makes the king himself acknowledge God), a real recurring
    pattern rather than two unrelated close calls.

40. **The Twelve (Hosea, Joel, Amos, Obadiah, Jonah, Micah, Nahum,
    Habakkuk, Zephaniah, Haggai, Zechariah, Malachi).** **Done
    (2026-09-10).** The final installment — with this, all 39 books of
    the Old Testament are curated. No new eras: every book with real
    narrative content fit an *existing* one. `era_divided_kingdom` took
    Hosea, Amos, and Jonah — all roughly contemporary with Jeroboam II
    of Israel, decades before the northern kingdom's fall, so they sit
    early in that era's `canonicalOrder` range (1471-1477, clustered
    just before `story_isaiahs_call` at 1478). `era_return_from_exile`
    took Haggai and Zechariah, whose own books are literally about the
    temple's rebuilding already curated from Ezra 5-6 — rather than new
    stories, their content **extends the existing**
    `story_temple_completed` (new `verseIds` — Haggai 2:4/2:9,
    Zechariah 4:6/4:10 — and both prophets added to its
    `characterIds`), continuing the "extend, don't clone" rule one more
    time. The other seven books (Joel, Obadiah, Micah, Nahum, Habakkuk,
    Zephaniah, Malachi) have no real narrative of their own, so they got
    the lighter verses-and-topics treatment with **no new Character
    records** for their authors — consistent with how Isaiah's and
    Proverbs' oracle verses mostly carry empty `characterIds` too.

    4 new stories: `story_hoseas_marriage` (Hosea marries Gomer, an
    unfaithful wife, as a lived picture of Israel's unfaithfulness —
    then is told to buy her back, picturing Yahweh's love anyway);
    `story_amos_confronts_amaziah` (the priest at Bethel tries to expel
    Amos, who answers that he was a shepherd, not a trained prophet,
    before Yahweh sent him); `story_jonah_flees_and_the_fish` and
    `story_jonah_and_nineveh` (split in two — the flight/storm/fish is
    a complete arc on its own before the actual commission in ch3
    begins; combining them would blur two different turning points). 6
    new characters: Hosea, Gomer, Amos, Jonah, Haggai, and Zechariah
    (`char_zechariah_prophet` — a distinct id from the existing
    `char_zechariah`, the priest Joash had stoned in the Chronicles
    pass; two real people named Zechariah already existed in the
    Bible's own text before this pass, not a curation collision). 60
    curated verses, no new topics — the existing 38 covered everything.

    Two new motifs, both genuine cross-book connections this final
    pass made possible: `motif_gracious_and_merciful_formula` — the
    same description of Yahweh ("gracious and merciful, slow to anger,
    abundant in loving kindness") recurs almost word-for-word from
    Exodus 34:6 (already curated, Genesis-era pass) through Nehemiah
    9:17 (already curated, the Ezra/Nehemiah pass) to Joel 2:13 to
    Jonah 4:2 — four instances spanning three different curation passes
    months apart, only recognizable as a pattern once the last piece
    (Jonah) was in place; its Connections attach directly to **verses**,
    not stories, since the recurrence is a repeated line, not a
    repeated narrative beat. `motif_trust_beyond_understanding`
    connects Job (`story_god_answers_job`) and Habakkuk 3:17-19 — both
    end not with their hard questions answered, but with a fuller sight
    of God's greatness that turns the sufferer from demanding answers
    to worship and trust anyway; a real second instance that turned an
    isolated fact about Job into an actual pattern, the same test every
    motif in this dataset has had to pass.

### The New Testament (started 2026-09-10)

All 39 OT books are curated as of item 40. The owner asked the same day
to continue into the NT. Before any content work, a real design
decision had to be made that the OT never faced: **how to handle four
Gospels that each retell the same life of Jesus.** Full rationale in
CLAUDE.md "Known gaps" item 9; the short version, extending the
project's existing "extend, don't clone" rule (Chronicles/Kings,
Isaiah 36-39/2 Kings 18-20, Haggai-Zechariah/Ezra) rather than
inventing a new principle:

- **One unified Story per event**, not four parallel retellings.
  `primaryReference` cites every Gospel that carries the event; curated
  verses can be drawn from more than one Gospel's account when each
  contributes something distinctive.
- **Each Gospel's genuinely unique material gets its own Story** — this
  is where real Gospel distinctiveness survives harmonizing, not where
  it gets lost. Luke: the fullest nativity, the prodigal son, the good
  Samaritan, Zacchaeus, Emmaus. Matthew: the magi, the fullest Sermon
  on the Mount, the Great Commission. John: Cana, Nicodemus, the woman
  at the well, Lazarus, the "I am" statements, foot-washing, doubting
  Thomas. Mark contributes almost no unique narrative — expected, not a
  gap, since its distinctiveness is pace and compression, not content.
- **One Character record per person** regardless of how many Gospels
  mention them.
- **New eras**: `era_birth_of_jesus`, `era_jesus_ministry`,
  `era_passion_and_resurrection` (Jesus's life), then
  `era_early_church` (Acts).
- **Epistles get the light verses-and-topics treatment** (Leviticus/
  Proverbs precedent) — they're letters, not narrative.
- **Revelation** gets a light Story for John's own framing vision (same
  treatment as Ezekiel's/Daniel's call narratives), then
  verses-and-topics for the rest.

41. **The birth of Jesus.** **Done (2026-09-10).** A new era,
    `era_birth_of_jesus`, order 13. 6 stories, matching Luke's and
    Matthew's own narrative units rather than splitting further:
    **Gabriel's announcements** (Luke 1:5-56 — the angel's visit to
    Zacharias in the temple and to Mary in Nazareth, plus Mary's visit
    to Elizabeth and her Magnificat, kept as one story since Luke tells
    them as a single interleaved unit); **John the Baptist is born**
    (Luke 1:57-80 — Zacharias's speech restored, his prophecy over his
    son); **Jesus is born in Bethlehem** (Luke 2:1-20); **Jesus
    presented at the temple** (Luke 2:21-40 — Simeon and Anna); **the
    wise men and the flight to Egypt** (Matthew 1:18-2:23 — Matthew's
    own, unique account of the same birth, including the angel's visit
    to Joseph rather than Mary, the magi, Herod's slaughter of the
    infants, and the family's escape); **the boy Jesus at the temple**
    (Luke 2:41-52 — age twelve).

    6 new characters: Jesus, Mary, Joseph, John the Baptist, Zacharias,
    Elizabeth. Joseph needed a non-obvious id, `char_joseph_husband_of_mary`
    — `char_joseph` was already taken by Genesis's Joseph, and reusing
    it produced a real build failure the first time through this pass
    (`build_stories.py` caught two people's life events colliding on
    the same `sequenceInLife` numbers under one shared id — exactly the
    kind of validation this pipeline exists to catch). Both display as
    "Joseph" (their real, accurate names) and are disambiguated by era
    grouping and by their own roles/summary on the Character detail
    page — the same pattern already used for the two unrelated
    Zechariahs (`char_zechariah`, the priest Joash had stoned; and
    `char_zechariah_prophet`, item 40).

    22 curated verses, no new topics — the existing 38 covered
    everything, including John's prologue ("In the beginning was the
    Word," John 1:1, 1:14), curated as standalone verses rather than
    forced into a Story since they're theological framing, not
    narrated action. `char_jesus`'s and `char_john_the_baptist`'s
    `eraId` is set to `era_birth_of_jesus` for now, since it's the only
    NT era that exists yet; both will move to `era_jesus_ministry` once
    that era is built next — the same "`eraId` is where a character's
    own arc is centered, not merely their first appearance" rule
    already applied to OT figures like Cyrus and Nebuchadnezzar.

42. **Jesus's ministry begins.** **Done (2026-09-10).** A new era,
    `era_jesus_ministry` (order 14) — `char_jesus` and
    `char_john_the_baptist` moved into it from the placeholder
    `era_birth_of_jesus` assignment item 41 used. 6 stories:
    **John the Baptist's ministry**; **Jesus is baptized** (the Spirit
    descending, the Father's voice); **Jesus is tempted** in the
    wilderness (three temptations, each answered with Scripture);
    **the first disciples follow Jesus** (John 1:35-51 — John's own,
    unique account of Andrew, Peter, Philip, and Nathanael meeting
    Jesus near the Jordan, distinct from and earlier than the Synoptics'
    by-the-lake calling); **water into wine at Cana** (John's first
    sign, John-unique); **Jesus calls the fishermen** (Luke 5:1-11's
    miraculous catch, used as `primaryReference` over Matthew
    4:18-22/Mark 1:16-20's much shorter parallel telling of the same
    formal call, since Luke's version is the fuller, more specific
    account — a direct application of "draw from whichever Gospel tells
    it most fully," item 41's stated rule, now applied for the first
    time to an event more than one Gospel actually tells).

    6 new characters: Peter, Andrew, James (id `char_james_son_of_zebedee`
    — there will be at least one more James in this canon, the Lord's
    brother, so the disambiguating id was chosen now rather than
    retrofitted later), John (id `char_john_apostle`, distinct from
    `char_john_the_baptist` — two Johns, same disambiguation-by-id
    pattern as the Josephs and Zechariahs), Philip, Nathanael. 16
    curated verses, no new topics.

43. **The Sermon on the Mount and three parables.** **Done
    (2026-09-10).** Establishes a new precedent worth stating plainly:
    **fictional figures inside Jesus's parables do not get Character
    records** — the good Samaritan, the priest and Levite who pass by,
    the prodigal son and his father and brother are not real,
    identifiable historical people the way every other Character in
    this dataset is (even unnamed-but-real figures like "the widow of
    Zarephath" describe one specific historical person). Their stories'
    `characterIds` carry only `char_jesus`, the one actually speaking.
    4 stories: **the Sermon on the Mount** (Matthew 5-7, kept as one
    story despite its length and range — Beatitudes, salt and light,
    the deeper law, the Lord's Prayer, treasure in heaven, anxiety,
    judging, the golden rule, the narrow gate, the wise and foolish
    builders — because it's genuinely one continuous discourse in one
    setting, the same reasoning that kept Job's friends' dialogue as
    one story across 35 chapters, item 35); **the parable of the sower**
    (Matthew 13:1-23, including Jesus's own explanation of it); **the
    good Samaritan** (Luke 10:25-37, Luke-unique); **the prodigal son**
    (Luke 15:11-32, Luke-unique). No new characters. 24 curated verses,
    no new topics — the Sermon alone contributed 14, comparable in
    density to how Proverbs (item 35) needed no new topics either
    despite being one of the most quotable stretches of text curated
    so far.

44. **Major miracles, Peter's confession, the Transfiguration.**
    **Done (2026-09-10).** 5 stories, no new characters. **The calming
    of the storm** (Mark 4:35-41 — used as `primaryReference` over
    Matthew 8:23-27/Luke 8:22-25's shorter parallels, Mark's being the
    most vivid: Jesus asleep on a cushion, the disciples' "don't you
    care that we are dying?"). **Feeding the five thousand** — the
    *only* miracle all four Gospels record; `primaryReference` cites
    all four rather than picking one, since none is meaningfully fuller
    than the others (unlike the calming of the storm or the calling of
    the fishermen, where one telling was genuinely richer — the "draw
    from whichever Gospel tells it fullest" rule from item 41 only
    applies when there's an actual difference in fullness to draw
    from). **Jesus walks on water**, including Peter's own attempt and
    near-sinking — Matthew-only among the Synoptics (Mark and John also
    have the walking-on-water itself, but only Matthew has the Peter
    material, so Matthew is `primaryReference`). **Peter's confession**
    at Caesarea Philippi ("you are the Christ, the Son of the living
    God") and Jesus's first prediction of his own death, met by Peter's
    rebuke and Jesus's sharp "get behind me, Satan." **The
    Transfiguration** — Moses and Elijah, the Father's voice repeating
    almost verbatim what was said at Jesus's baptism ("this is my
    beloved Son... listen to him"), witnessed by Peter, James, and John.
    14 curated verses, no new topics.

45. **John's unique material: Nicodemus, the woman at the well,
    Lazarus.** **Done (2026-09-10).** 3 stories, all John-only —
    exactly the kind of content item 41's design note anticipated
    Mark would *not* contribute and John *would*. **Nicodemus** (John
    3:1-21) — the "born again" conversation, ending in John 3:16.
    **The woman at the well** (John 4:1-42) — crosses two social lines
    at once (a Jewish man speaking to a Samaritan woman, alone), ends
    with an entire town converted on her testimony. **Lazarus raised
    from the dead** (John 11:1-44) — Jesus's last and greatest sign
    before his own death, deliberately delayed two days, ending in
    "Lazarus, come out!"

    6 new characters: Nicodemus; the Samaritan woman (id
    `char_samaritan_woman` — unnamed in the text, same treatment as
    the OT's "the widow of Zarephath": a real, specific person the
    narrative just doesn't name, not a reason to skip a Character
    record); Lazarus; Martha; Mary of Bethany (id
    `char_mary_of_bethany` — a third Mary in this canon already,
    alongside Jesus's mother and the not-yet-curated Mary Magdalene,
    so the disambiguating id was chosen immediately rather than
    retrofitted, same discipline as the Jameses and Johns); Thomas
    (first appearance — "let's go also, that we may die with him,"
    well before his famous doubt, which comes much later after the
    resurrection). 14 curated verses, no new topics.

46. **The road to Jerusalem, and the triumphal entry.** **Done
    (2026-09-10).** Closes out `era_jesus_ministry` and opens a new
    era, `era_passion_and_resurrection` (order 15). Two contrasting
    stories on the road to Jerusalem, both staying in
    `era_jesus_ministry`: **Zacchaeus** (Luke 19:1-10, Luke-unique) —
    a wealthy, despised tax collector gives away half his wealth on
    the spot, unprompted; **the rich young ruler** (Matthew 19:16-26)
    — a wealthy, law-keeping young man refuses the same invitation and
    walks away grieved. Deliberately *not* formalized as a Connection
    or motif — it's a real thematic contrast worth noting in prose (and
    noted in both stories' summaries), but it's two isolated character
    studies, not a recurring narrative shape told more than once the
    way an actual motif requires. Then **the triumphal entry**
    (Matthew 21:1-11, with Mark/Luke/John parallels cited in
    `primaryReference`) — the first story in the new era, at
    `canonicalOrder: 2600` (a clean jump from `era_jesus_ministry`'s
    2000s range, leaving obvious headroom for everything still ahead
    in Jesus's final week). Matthew 21:5's own citation of Zechariah
    9:9 ("your King comes to you, humble, and riding on a donkey") is
    curated as its own verse, `verse_matthew_21_5` — distinct from
    `verse_zechariah_9_9` (item 40) even though the words are nearly
    identical, since each captures a different moment: the prophecy
    and its fulfillment are two different verses to curate, not one.

    2 new characters: Zacchaeus; the rich young ruler (id
    `char_rich_young_ruler` — unnamed in the text, same "real person,
    no name given" treatment as the Samaritan woman, item 45, and the
    OT's widow of Zarephath). 9 curated verses, no new topics.

47. **The Last Supper through the arrest.** **Done (2026-09-10).** 5
    stories in `era_passion_and_resurrection`: **the Last Supper**
    (Matthew 26:17-30 — betrayal foretold, the bread and cup);
    **Jesus washes his disciples' feet** (John 13:1-17, 34-35,
    John-unique — servant leadership and the new commandment to love
    one another); **Jesus comforts his disciples** (John 14:1-16:33,
    John-unique — kept as one story covering the whole farewell
    discourse rather than one per chapter, since it's a single
    continuous address like the Sermon on the Mount, item 43: "I am
    the way, the truth, and the life," the vine and the branches,
    "in me you may have peace"); **Gethsemane** (Matthew 26:36-46 —
    the threefold prayer, the sleeping disciples); **betrayal and
    arrest** (Matthew 26:47-56 — Judas's kiss, the severed ear, "all
    those who take the sword will die by the sword").

    1 new character: Judas Iscariot (first Character record, though
    referenced earlier in narrative text — his `eraId` is
    `era_passion_and_resurrection`, where his one defining act
    happens). 18 curated verses, no new topics. Hit a real
    `sequenceInLife` collision building this batch — `char_peter`
    already had events at 40 and 50 from two earlier, unrelated
    batches (Peter's confession, and the Transfiguration), and this
    batch's new foot-washing and Gethsemane events picked the same
    numbers independently. Fixed by querying Peter's actual existing
    values before renumbering (60, 70) rather than guessing; see
    `pipeline/README.md`'s new lesson on checking `sequenceInLife` for
    high-frequency NT characters before each batch, not just OT
    figures who rarely collide since their appearances are spread
    across months-apart passes.

48. **The trials, Peter's denial, Judas's remorse.** **Done
    (2026-09-10).** 4 stories in `era_passion_and_resurrection`:
    **Jesus before the council** (Matthew 26:57-68 — Caiaphas's
    demand and Jesus's answer, condemned for blasphemy); **Peter's
    denial** (Matthew 26:69-75 — three denials, the rooster, weeping
    bitterly); **Judas's remorse** (Matthew 27:3-10 — his confession
    to unmoved priests, his death, the Field of Blood); **Jesus before
    Pilate** (Matthew 27:11-26 — Barabbas released, the crowd's
    demand, Pilate's hand-washing).

    3 new characters: Caiaphas, Pilate, Barabbas — all `eraId:
    era_passion_and_resurrection`, since each exists in the curated
    narrative for exactly one event. 11 curated verses, no new topics.

49. **The crucifixion and burial.** **Done (2026-09-10).** 2 stories.
    **The crucifixion** (`primaryReference` cites all three of
    Matthew 27:27-56, Luke 23:26-49, and John 19:16-30, since each
    Gospel contributes real, non-overlapping content to the same
    single event rather than one being fuller than the rest — Matthew
    has the mocking, the darkness, the temple veil tearing, and the
    centurion's confession; Luke alone has "Father, forgive them" and
    the exchange with the penitent thief; John alone has Jesus
    entrusting his mother to John's own care and the words "it is
    finished." This is a different citation shape than "draw from
    whichever Gospel tells it fullest" (item 41) — here no single
    Gospel is fuller, so the curated verse set itself draws from all
    three, each contributing its own distinct material to one Story).
    **Jesus is buried** (Matthew 27:57-66 — Joseph of Arimathea's
    tomb, the guard set to prevent a resurrection claim).

    4 new characters: Mary Magdalene (first Character record, though a
    significant figure across the ministry — her `eraId` is
    `era_passion_and_resurrection`, where her defining moments, being
    present at the cross and then first to the empty tomb, both fall);
    Simon of Cyrene; the penitent thief (id `char_penitent_thief` —
    unnamed in the text, same treatment as the Samaritan woman and the
    rich young ruler, items 45–46); Joseph of Arimathea. 10 curated
    verses, no new topics.

50. **The resurrection, appearances, Great Commission, ascension.**
    **Done (2026-09-10).** Closes out `era_passion_and_resurrection` —
    **all four Gospels are now fully curated.** 6 stories: **the empty
    tomb** (Matthew 28:1-15 — the angel, the women, the guards'
    bribe); **Jesus appears to Mary Magdalene** (John 20:11-18,
    John-unique — recognized only when he says her name); **the road
    to Emmaus** (Luke 24:13-35, Luke-unique — recognized only in the
    breaking of bread); **doubting Thomas** (John 20:24-29,
    John-unique — "my Lord and my God"); **the Great Commission**
    (Matthew 28:16-20); **the ascension** (Luke 24:50-53 —
    `primaryReference` is Luke alone for now; Acts 1:9-11 retells the
    same event from Luke's own second volume, so when Acts is curated
    next it should extend this story's `verseIds` rather than spawn a
    duplicate, the same "extend, don't clone" call as the crucifixion
    batch made for material split across Gospels).

    1 new character: Cleopas (named in Luke's Emmaus account; the
    second disciple on the road is never named). 16 curated verses, no
    new topics.

    **With this, the Gospels are done: 4 books, 3 eras
    (`era_birth_of_jesus`, `era_jesus_ministry`,
    `era_passion_and_resurrection`), and the full unified life of
    Jesus from Gabriel's announcement to the ascension — 44 curated
    stories in total across items 41–50, built exactly per the
    harmonization design from item 41's opening note: one Story per
    event regardless of how many Gospels tell it, each Gospel's real
    unique material preserved as its own Story rather than lost to
    harmonizing, one Character record per person no matter how many
    Gospels mention them. Next: Acts (the early church, a new era,
    `era_early_church`), then the epistles (light verses-and-topics
    treatment, per item 41's design note), then Revelation.**

51. **Acts begins: choosing Matthias, Pentecost, the first healing —
    plus a retroactive addition, the calling of Matthew.** **Done
    (2026-09-10).** A new era, `era_early_church` (order 16). Followed
    through on item 50's own note: `story_ascension` (in
    `era_passion_and_resurrection`) got Acts 1:8 and 1:11 added to its
    `verseIds` rather than a duplicate Acts-side story, since Acts 1
    retells the same ascension Luke's Gospel already ends on. 3 new
    stories in the new era: **choosing Matthias** (Acts 1:12-26 —
    Judas's empty place filled by lot); **Pentecost** (Acts 2:1-47,
    kept as one story spanning the tongues of fire, Peter's sermon,
    and the church's first communal life, since it's one continuous
    scene); **Peter heals a lame man** (Acts 3:1-10 — the first
    apostolic miracle, "what I have, I give you").

    Also caught and fixed a real gap while assembling the apostle list
    in Acts 1:13: **the calling of Matthew** (Matthew 9:9-13) had never
    been curated during the Gospel passes (items 41-50), even though
    it's real, substantial narrative — a clean miss, not a deliberate
    scope decision. Added retroactively to `era_jesus_ministry` at
    `canonicalOrder: 2260` (between the calling of the fishermen at
    2250 and the Sermon on the Mount at 2300 — its correct
    chronological slot), proving the pipeline's validation doesn't
    care *when* content is added, only that it's internally
    consistent; curation can be extended into an already-"finished"
    era at any point, same as any OT era that picked up new stories in
    later passes.

    2 new characters: Matthew (the tax collector, one of the twelve,
    traditionally the Gospel's author); Matthias (chosen to replace
    Judas). 16 curated verses, no new topics.

52. **Stephen's martyrdom and Saul's conversion.** **Done
    (2026-09-10).** 2 stories in `era_early_church`. **Stephen's
    martyrdom** (Acts 6:8-8:1) — the first Christian death, dying with
    words that echo Jesus's own on the cross ("Lord, don't hold this
    sin against them," compare Luke 23:34, item 49). **Saul's
    conversion** (Acts 9:1-22) — the Damascus road, Ananias's
    reluctant obedience, the scales falling from Saul's eyes.

    A naming decision worth stating plainly, since it governs every
    future Acts/epistle Connection and verse tag: **the id and
    canonical `name` are `char_paul`, "Paul," even in these early
    scenes where the text calls him "Saul."** Same precedent as
    `char_peter` (kept as "Peter" even for events before his renaming
    from Simon) and `char_jacob` (kept as "Jacob" despite becoming
    "Israel") — one Character record per person for their whole life,
    using whichever name is dominant across their total appearances,
    not whichever name the text happens to use in a given scene. Paul
    goes by "Paul" for the overwhelming majority of the NT (13
    epistles carry his name), so that's the id chosen now, before any
    of those epistles are curated — deciding it this early avoids ever
    having to rename it later once dozens of Connections and
    curated-verse `characterIds` already reference it.

    2 new characters: Stephen; Paul (first Character record — he was
    only referenced by name inside Stephen's own story text before
    this). 8 curated verses, no new topics.

53. **Peter and Cornelius.** **Done (2026-09-10).** 1 story in
    `era_early_church` (Acts 10:1-48) — the gospel's first deliberate
    step to Gentiles: Peter's vision reinterpreting clean and unclean
    ("what God has cleansed, you must not call unclean"), then the
    Holy Spirit falling on Cornelius's household exactly as it did on
    the disciples at Pentecost (item 51), read by Peter and the
    watching believers as unambiguous proof God's promise wasn't for
    Israel alone. 1 new character: Cornelius. 5 curated verses, no new
    topics.

54. **Paul's first missionary journey, the Jerusalem council, the
    Philippian jailer, the Areopagus.** **Done (2026-09-10).** 4
    stories in `era_early_church`. **Paul's first missionary journey**
    (Acts 13:1-14:28, kept light/summary-level rather than
    city-by-city, since the chapters cover many stops with similar
    shape — preach to Jews first, then Gentiles, face opposition, move
    on; Acts 13:9, "Saul, who is also called Paul," is the text's own
    hinge point for the name Paul becoming primary, confirming the
    naming call already made in item 52). **The Jerusalem council**
    (Acts 15:1-29 — the first church-wide theological dispute, resolved
    without requiring Gentile converts to keep the Mosaic law).
    **The Philippian jailer** (Acts 16:16-34 — the earthquake, the
    jailer's near-suicide, "what must I do to be saved?"). **Paul at
    the Areopagus** (Acts 17:16-34 — the "unknown God" altar used as
    common ground, "in him we live, move, and have our being").

    3 new characters: Barnabas (first Character record, though he
    exists earlier in Acts' own narrative — his defining acts, per
    established practice, are what's curated, not his first
    mention); Silas; the Philippian jailer (unnamed in the text, same
    treatment as the Samaritan woman and the rich young ruler, items
    45-46). 12 curated verses, no new topics.

55. **Paul's arrest, shipwreck, and arrival in Rome — Acts is
    complete.** **Done (2026-09-10).** 3 stories in `era_early_church`,
    closing the book. **Paul's arrest in Jerusalem** (Acts 21:27-26:32,
    kept as one story spanning the arrest itself and the trials before
    Felix, Festus, and Agrippa that follow — none of those hearings
    reaches a real verdict or adds new plot, only delay, so they didn't
    need Stories of their own; Acts 23:11, Jesus's promise that Paul
    "must testify also at Rome," is the thread that ties the arrest to
    everything left in the book). **Shipwrecked on the way to Rome**
    (Acts 27:1-28:10 — the storm, the angel's promise that no lives
    will be lost, the viper on Malta). **Paul in Rome** (Acts
    28:11-31 — two years of unhindered preaching under house arrest,
    the note the whole book ends on).

    No new characters — Felix, Festus, and Agrippa stay unrecorded as
    Characters, appearing only in story prose, since none of them adds
    a distinguishing act comparable to Pilate's or Caiaphas's in the
    Gospels (items 48-49); they're delay, not decision-makers. 9
    curated verses, no new topics.

    **With this, Acts is complete: 1 book, `era_early_church`, 13
    stories total (items 51-55), tracing the church from Pentecost in
    a locked room to Paul preaching openly in the capital of the
    empire. Next: the epistles — Romans through Jude — get the light
    verses-and-topics treatment established with Leviticus (item 41's
    design note), since they're letters, not narrative; then
    Revelation.**

56. **Romans.** **Done (2026-09-10).** The first epistle, and the
    template for how the rest will be handled: no Story records (no
    narrative — it's a letter), no new characters (Paul already
    exists), just curated verses tagged to existing topics. 20 verses
    covering the letter's core theology, chosen for how frequently
    they're quoted/memorized independent of this project: justification
    by faith (1:16-17, 3:23-24, 5:1), Christ's death for sinners while
    still sinners (5:8), death and resurrection in baptism (6:4),
    "the wages of sin is death" (6:23), no condemnation for those in
    Christ (8:1), "all things work together for good" (8:28), nothing
    able to separate us from God's love (8:31, 8:38-39), confessing
    Jesus as Lord (10:9), faith by hearing (10:17), the "living
    sacrifice" call to worship (12:1-2), overcoming evil with good
    (12:21), submission to authority (13:1), and a closing benediction
    on hope (15:13). No new topics — the existing 38 covered
    everything, including some of the New Testament's most quoted
    verses.

57. **1-2 Corinthians.** **Done (2026-09-10).** No Story records, no
    new characters — same light treatment as Romans. 22 curated verses:
    1 Corinthians contributed the body as a temple (6:19-20), fleeing
    temptation with God's promised way of escape (10:13), the love
    chapter (13:4-5, 13:13 — three representative verses rather than
    the full 4-7 passage, since curating every clause of one
    continuous description would fragment it more than it illuminates),
    the resurrection creed (15:3-4) and its climax ("death, where is
    your sting?", 15:55, 15:57-58). 2 Corinthians contributed the God
    of all comfort (1:3-4), "we walk by faith, not by sight" (5:7 —
    not selected; 4:18's "things which are not seen are eternal" was
    chosen instead as the fuller statement of the same idea, to avoid
    curating two verses making essentially one point), the new creation
    (5:17), Christ made sin for us (5:21), the cheerful giver (9:7),
    and "my grace is sufficient for you... when I am weak, then I am
    strong" (12:9-10, tagged to `char_paul` as his own testimony, not
    detached doctrine). No new topics.

58. **Galatians, Ephesians, Philippians, Colossians.** **Done
    (2026-09-10).** Grouped as one pass since all four are short,
    Pauline, and (per tradition) written from prison around the same
    period. No Story records, no new characters. 31 curated verses:
    Galatians — freedom in Christ (2:20, 5:1), "neither Jew nor
    Greek... male nor female" (3:28), the fruit of the Spirit
    (5:22-23), bearing one another's burdens (6:2), not growing weary
    in doing good (6:9). Ephesians — salvation by grace through faith,
    not works (2:8-10), forgiving as God forgave (4:32), the armor of
    God (6:10-12). Philippians — "to live is Christ, to die is gain"
    (1:21), Christ's humility as the pattern for the church's (2:3-10),
    "be anxious for nothing" and the peace that guards hearts (4:6-7),
    "I can do all things through Christ" (4:13, tagged to `char_paul`),
    God supplying every need (4:19). Colossians — Christ as the image
    of the invisible God and sustainer of all creation (1:15-17),
    seeking the things above (3:1), working heartily as for the Lord
    (3:23). No new topics — 38 topics have now carried 8 epistles and
    the whole Old and New Testament narrative without needing to grow
    since item 40 (the Twelve, end of the Old Testament).

59. **1-2 Thessalonians, 1-2 Timothy, Titus, Philemon.** **Done
    (2026-09-10).** Grouped as one pass — the remaining shorter
    Pauline letters (Thessalonian correspondence, then the three
    "pastoral" letters to individuals, then the one-page personal
    appeal to Philemon). No Story records, no new characters. 24
    curated verses: 1 Thessalonians — the resurrection of the dead in
    Christ and being caught up to meet the Lord (4:14, 4:16-17), four
    short, independently famous imperatives from chapter 5 (rejoice
    always, pray without ceasing, give thanks in everything, test all
    things). 2 Thessalonians — God's faithfulness to guard against the
    evil one (3:3), not growing weary in doing right (3:13). 1 Timothy
    — Paul calling himself the foremost of sinners Christ came to save
    (1:15, tagged to `char_paul`), contentment as great gain (6:6),
    the love of money as a root of evil (6:10), fighting the good
    fight of faith (6:12). 2 Timothy — no spirit of fear but of power,
    love, and self-control (1:7), Scripture as God-breathed and
    equipping (3:16-17), Paul's own summary near the end of his life,
    "I have fought the good fight... I have kept the faith" (4:7,
    tagged to `char_paul`). Titus — grace instructing believers to
    live godly lives (2:11-12), salvation by mercy, not works (3:5).
    Philemon — Paul's appeal for Onesimus to be received "no longer as
    a slave, but... a beloved brother" (1:16), and to charge any debt
    to Paul's own account instead (1:18, tagged to `char_paul` as his
    own offer, not a general doctrine) — the two verses that carry the
    whole letter's point without needing the full backstory of
    Onesimus curated as a Character, since he never appears again in
    what this project curates and his story here is entirely
    Philemon's decision, not his own action. No new topics.

60. **Hebrews, James, 1-2 Peter, 1-3 John, Jude.** **Done (2026-09-10).**
    Grouped as one pass — the general/catholic epistles, the last
    grouping before Revelation. No Story records, no new characters, no
    new topics. 42 curated verses: Hebrews — Jesus as the exact
    representation of God's being (1:3), faith defined and the great
    "cloud of witnesses" summons to run the race (11:1, 12:1), Jesus as
    the same yesterday, today, and forever (13:8). James — trials
    producing endurance (1:2-4), doing the word and not just hearing it
    (1:22), faith without works being dead (2:17, 2:26), the tongue as
    a small but untamable fire (3:5-6), humbling yourself before the
    Lord (4:10). 1 Peter — the living hope of the resurrection (1:3),
    being a royal priesthood and holy nation (2:9), wives and husbands
    living considerately together (3:7), casting all anxiety on God
    because he cares (5:7). 2 Peter — every good gift given through
    God's own glory and virtue (1:3), a day being like a thousand years
    to the Lord (3:8), God's patience wanting none to perish (3:9). 1
    John — God is light (1:5), God is love and love casting out fear
    (4:8, 4:18), the confidence that if we ask according to his will he
    hears us (5:14-15). 2 John — walking in truth and love as the
    Father's commandment (1:5-6). 3 John — Gaius commended for
    faithfulness to the brothers (1:5). Jude — contending for the faith
    once delivered (1:3), and the closing doxology, "able to keep you
    from stumbling" (1:24-25). **All 21 New Testament epistles are now
    done** — Romans through Jude, items 56-60 — each with the same
    light verses-and-topics treatment per item 41's design note, since
    none of them narrate action in the Story sense. 38 topics have now
    carried the entire epistolary corpus without needing to grow since
    item 40. **Revelation is the only book of the 66-book Bible left to
    curate.**

61. **Revelation — the entire 66-book Bible is now curated.** **Done
    (2026-09-10).** One Story, `story_johns_vision_on_patmos`
    (Revelation 1:9-20), for John's own framing vision — the same
    treatment given to Ezekiel's and Daniel's call/vision narratives in
    the Old Testament: exiled on Patmos, John is caught up in the
    Spirit, sees the risen Christ among seven lampstands ("I am the
    first and the last, and the Living one... I have the keys of Death
    and of Hades"), and is commissioned to write what he sees. No new
    Character — John the apostle already exists (`char_john_apostle`,
    item 42); this is simply his next life event, `sequenceInLife` 60
    (queried his existing values, `[10, 20, 30, 40, 50]`, before
    assigning — the recurring-character collision lesson from item 47
    still applies even at the very last character added to the whole
    project). The rest of the book — the seven letters, the throne-room
    worship, the martyrs under the altar, the great multitude, the
    dragon thrown down, "worthy is the Lamb," the thousand years and
    the final judgment, and the new heaven and new earth — got the
    light verses-and-topics treatment, since almost none of it is
    narrated action in the Story sense: 46 curated verses (including
    the one, Revelation 1:9, pulled in to satisfy the Story's own
    `verseIds` reference), all tagged to existing topics
    (`topic_worship` for the throne-room material, `topic_justice` for
    the judgment scenes, `topic_faithfulness` for "worthy... for you
    were slain," `topic_sorrow`/`topic_provision` for "he will wipe
    away every tear," `topic_waiting` for "surely I come quickly. Amen.
    Come, Lord Jesus"). No new topics — the same 38 that closed out the
    Old Testament (item 40) carried the entire New Testament, Gospels
    through Revelation, without ever needing to grow. **This completes
    the whole Bible: 66 books, 1,339 curated verses, 161 characters,
    237 stories, 529 life events, 20 motifs, 135 connections** — the
    entire arc from "let there be light" (Genesis 1:3) to "the grace of
    the Lord Jesus Christ be with all the saints. Amen" (Revelation
    22:21).

62. **Visual system v3 — modern dark theme, YouVersion-inspired.**
    **Done (2026-09-10).** With the entire Bible now curated, the owner
    wants to push on the visual side next: a dark background "like the
    YouVersion app," inspired by it but not copied, as a first pass
    meant to spark further design ideas rather than a final answer (more
    design work is planned "at the end"). Two decisions up front,
    confirmed with the owner before touching code: (1) **full swap**,
    not a light/dark toggle — the whole app moves to the new look, no
    `prefers-color-scheme` branching or per-user setting (a toggle can
    be added later if the owner wants both); (2) **drop Fraunces
    entirely** — the owner chose "go full sans" over keeping the serif
    for verse text, so the warm-storybook pairing (Fraunces headings/
    verse text + Inter UI text) established since the project's start is
    retired in favor of one typeface, Inter, throughout (headings and
    stat numbers now lean on weight — 700/800 — and slightly tightened
    letter-spacing for hierarchy, since a serif/sans contrast is no
    longer available to do that job).

    Every color in the app already ran through the same ~15 CSS custom
    properties (`--paper`, `--paper-raised`, `--surface-sunken`, `--ink`
    family, `--gold`/`--sage`/`--tan` accent triads, `--danger`) since
    v2's own design (§29) — a deliberate token system, not per-component
    hardcoding — so the theme swap is almost entirely a `:root` value
    change, not a rewrite: `--paper` (page bg) `#F3EFE6` → `#121316`
    (near-black), `--paper-raised` (card surface) `#FFFFFF` → `#1C1F24`,
    `--surface-sunken` (inputs/chips/segmented track) → `#24272E`,
    `--ink` → `#F1F0ED` (soft white, not pure), `--ink-soft`/`--ink-faint`
    lightened proportionally, `--line` → `rgba(255,255,255,.08)`. The
    three-role accent system from §29 stayed conceptually intact (gold =
    action/urgency, sage = progress/mastery, tan = metadata) but every
    value was re-picked for dark-background contrast rather than just
    inverted — brighter, more saturated gold (`#F2B33D`) and green
    (`#33D881`) so they actually pop the way the owner's brief asked for,
    tan shifted from a light-mode brown (`#8C7357`) to a cooler blue-gray
    (`#9FB0C3`) since brown reads muddy on near-black. The wash tokens
    (`--gold-wash` etc.) changed shape, not just color — solid pastel
    hex in light mode → low-alpha `rgba()` overlays in dark mode, since a
    solid light pastel chip would look like a mistake on a dark page; a
    translucent tint reads as a deliberate "highlighted tile" instead,
    which is also why avatar-placeholder fills (`.avatar`,
    `.list-avatar`, `.hero-avatar`) still use the same `--tan-wash`
    token and didn't need a separate one. Added one new token,
    `--danger-wash` (`rgba(255,107,87,.14)`), replacing two copies of a
    hardcoded `#F6E4DD` that had never been promoted to a variable in
    v2 — same wrong-error-color-in-two-places-instead-of-shared-token
    pattern the v2 pass caught and fixed for `.tag.plum`, caught again
    here on a smaller scale.

    Three real component fixes beyond a pure token swap, all reasoned
    from how dark UIs actually differ from light ones, not guessed at
    blind: (1) **box-shadow alone stops reading as elevation on a dark
    page** — a dark shadow over an already-dark background barely
    renders, so `.card`, `.stat-card`, `.hero`, and `.back-btn` each
    gained a `1px solid rgba(255,255,255,.06)` border alongside their
    existing shadow, a standard dark-UI technique to keep a raised
    surface visually distinct from the page behind it. (2) the floating
    frosted nav's glass tint (`rgba(255,255,255,.88)`, a light frost)
    became a dark frost (`rgba(28,31,36,.88)`) plus the same subtle
    border, rather than just changing opacity on the old light value.
    (3) `.btn.primary`'s dark-brown-on-gold text color and shadow tint
    were re-picked to match the new gold hue rather than left pointing
    at the old one. `meta[name=theme-color]` and `manifest.json`'s
    `background_color`/`theme_color` both updated to `#121316` so the
    OS chrome (status bar, task-switcher card, splash screen) matches
    instead of flashing the old cream color on load — a detail that's
    easy to miss since it's invisible until you actually install the
    PWA or background-switch away from it.

    Deliberately **not** touched this pass: the nav's actual tab
    arrangement/icons (Home, Browse, Topics, People, Add) — the owner
    asked for the dark *look*, not new information architecture, and
    said more design work (including layout/IA ideas inspired by
    YouVersion's tab arrangement) is coming later once this first pass
    has been seen and reacted to; `icon.png` (still the placeholder
    noted since the project's start, now visually mismatched against
    the new dark chrome — a real known gap, not forgotten, just out of
    scope for a CSS-only pass); no automated visual regression check —
    this is a CSS/token change with no new markup shapes to assert
    against the way v2's `.list-row`/`.hero` presence could be, so
    verification here was a manual render check plus a full re-read of
    every hardcoded hex in the file to confirm nothing was missed (found
    and fixed three: `.hero-avatar`'s literal `#EFE9DC` fill and two
    copies of `#F6E4DD` on the danger/wrong states, folded into the new
    `--tan-wash`/`--danger-wash` tokens respectively). Verified by
    actually running the app locally (`py -m http.server`) and having
    the owner look at it in a browser, not just a markup/CSS-source
    read — the first real UI verification loop this project has had,
    now that a local-preview step exists to close it.

63. **Topics screen → colorful per-topic card grid, then a darker/
    punchier follow-up tune.** **Done (2026-09-10).** Two owner-driven
    iterations on top of v3 (item 62), both against a real YouVersion
    screenshot the owner shared (its Discover tab: a 2-column grid of
    solid-colored, per-topic cards on true black). Asked directly what
    stood out and how to adapt it (not copy it) for a topic-practice
    app rather than a content-discovery one — five things named:
    near-true-black ground, per-topic color coding, a neutral gray
    active-nav pill instead of a colored one, a home quick-action tile
    row, and bold high-contrast type (already covered by v3's Inter
    move). Owner picked the colorful-topics-grid as the one worth
    building now; the nav-pill and quick-action-tile ideas are noted
    but not built.

    **The grid.** `renderTopics()` (`index.html`) went from plain
    `.list-row` rows to a `.topic-grid` of `.topic-card`s — 2-column
    CSS grid, each card a solid color with a large, low-opacity Tabler
    icon inset top-right and the topic name + verse count anchored
    bottom-left, deliberately following the reference's photo-inset
    card composition without photos (no topic artwork exists yet).
    Two new client-only lookups, `TOPIC_PALETTE` (12 colors) and
    `TOPIC_ICONS` (one hand-picked icon per topic, keyed by id, falling
    back to a generic sparkle icon for any topic added later without an
    explicit entry), plus `topicColor(id)` — a simple string hash mod
    palette length, not array index, so a topic's color is stable
    across sessions but doesn't correlate with topic list order (two
    adjacent topics in the data shouldn't predictably land on adjacent
    colors). This is deliberately **client-side presentation only**, no
    `Topic` schema change — Design philosophy #2 reserves `metadata` for
    speculative *content* fields, and a color/icon-for-the-current-UI
    lookup is exactly the kind of thing that belongs in code instead
    (same reasoning as every other hardcoded icon already in this
    file). `.topic-card` was wired into the existing shared press-
    feedback rule and `prefers-reduced-motion` override alongside every
    other tappable surface, not given its own copy of that logic.

    **The tune.** After seeing the grid rendered, direct feedback: the
    background should go darker and the colors punchier. `--paper`
    `#121316` → `#08090B` (near-true-black, closer to the reference),
    `--paper-raised`/`--surface-sunken` deepened proportionally so the
    page/card/input elevation steps stayed visually distinct rather
    than collapsing into each other at the new darker baseline;
    `--gold`/`--sage` both re-saturated brighter for more pop
    (`#F2B33D`→`#F5AC1F`, `#33D881`→`#1FE07F`), `--danger` nudged too;
    the entire `TOPIC_PALETTE` re-picked more vivid at the same 12 hues
    (e.g. `#2E6F82`→`#1786AD`) rather than just brightened uniformly, to
    keep the per-hue character while adding punch; topic-card icon
    opacity `.28`→`.35` for a touch more presence. Every place a color
    value had been hardcoded elsewhere in the file rather than routed
    through its token (`.btn.primary`'s shadow tint, the navbar's frost
    tint, `meta[theme-color]`, `manifest.json`) was hunted down and
    updated to match, rather than left pointing at the pre-tune values
    — the same discipline item 62 established for the initial swap,
    reapplied here so a second pass doesn't reintroduce the exact kind
    of drift v2 already had to clean up once (`.tag.plum`, `#F6E4DD`
    duplicated twice).

64. **Topics search, and topic-colored topic detail pages.** **Done
    (2026-09-10).** Two more owner-requested follow-ups on the same
    Topics work (items 62-63), after approving the colorful grid: (1)
    a search bar was missing on the Topics screen even though People
    and Browse both have one; (2) tapping into a topic felt "bland"
    compared to its colorful card — the detail page should carry the
    same color.

    **Search.** `renderTopics()` split into a thin shell plus
    `renderTopicsResults()`, exactly mirroring the People screen's own
    split (`renderCharacters()`/`renderPeopleResults()`, §30) rather
    than inventing a different shape — same `.search-wrap` markup, same
    140ms-debounced `input` listener wired in `bindEvents()`, same
    `refresh*Results()` helper that re-renders just the results
    `<div>` on keystroke instead of the whole screen. New state var
    `topicsQuery`, filtering by name or description.

    **Topic-colored detail pages.** The interesting part: rather than
    hardcoding a topic's color into every element on its detail page
    (verse-card ref color, the practice button, related-topic tags —
    three separate call sites, two of them in shared components also
    used elsewhere), the page instead **locally overrides which color
    the existing "gold" accent role points to**. A new
    `topicAccentVars(id)` derives a brighter text-safe tint and a
    low-alpha wash from the topic's one base hex (the same
    base/deep/wash token shape gold/sage/tan already use) and returns
    them as an inline `style` string — `--gold`, `--gold-deep`,
    `--gold-wash`, and a new `--gold-shadow` token (promoted out of a
    literal `rgba()` that had been sitting directly in `.btn.primary`
    since v3, item 62, so it could be overridden too) — set on a
    wrapper `<div>` around the whole topic detail screen. Every
    component underneath (`renderVerseCard`'s `.ref`, `.btn.primary`,
    `.tag--gold`) already reads these same custom properties, so they
    pick up the topic's color for free through normal CSS cascade —
    zero changes to any shared component, and the override cleanly
    can't leak past the wrapper `<div>` into any other screen.
    Deliberately **not** re-themed: `.tag--sage` (mastery/"Mastered")
    and `.tag--tan` (metadata/topic-name pills) on the same verse
    cards — the three-role accent system (§29) still means something,
    and blending "Mastered" into whatever color the current topic
    happens to be would cost more meaning than the extra cohesion is
    worth. The page also gained a colored hero header (topic's icon +
    name + description on a full-color card, replacing the old plain
    `.screen-head`), with the back button restyled inline
    (translucent-black circle) since the default `.back-btn` styling
    assumes it's sitting on the page background, not on a saturated
    color block.

65. **Timeline builder — a drag-and-drop chronology puzzle over a
    character's LifeEvents.** **Done (2026-09-10/11).** First of the
    owner's "make the app feel visually interactive, not just readable"
    ideas (five were proposed; this one — closest to an already-planned
    `challenge_story_order` challenge type — was picked to build first).
    New screen, `timelineGame` (`renderTimelineGame()`), entered from a
    "Put their life in order" button on Character detail (shown once a
    character has ≥3 LifeEvents). Deliberately **not** part of the
    spaced-repetition verse-practice loop or the `CHALLENGE_TYPES`
    registry — there's no "due" schedule for ordering a life story, it
    just reshuffles fresh each time. Up to `n` events (3/5/8 for an
    Easy/Normal/Hard `.segmented` picker, `TIMELINE_DIFFICULTIES`) are
    sampled from the character's full timeline and shuffled; the user
    drags them into what they think is the right order via real Pointer
    Events (no external drag library — moving actual DOM nodes with
    `insertBefore` during `pointermove`, only reconciling back into
    state on drop/check, so a re-render never interrupts an in-progress
    gesture). "Check order" locks correctly-placed cards in an amber
    glow (`.tl-drag-correct`) with a `navigator.vibrate(20)` pulse per
    the owner's own spec; "Shuffle the rest" reshuffles only the
    still-wrong cards among themselves, a progressive puzzle rather
    than a full restart each attempt; a Reshuffle icon button gives an
    entirely fresh puzzle at the current difficulty.

    **Two real bugs, both caught by the owner actually using it (the
    first real UI bug-report loop this project has had, not just a
    design-taste one) rather than by re-reading the diff:**
    - **Lock-tracking by array index, not by event id.** The first
      version marked "slot i is solved" (`g.locked[i] = true`). But
      dragging an unlocked card past a locked one can shift the locked
      card's DOM index as a side effect of normal reflow (other cards
      moving around it) — the "solved" flag stayed pinned to the old
      index, not to the card, so a *different* card could slide into an
      already-"solved" slot and get shown as correct while the actually
      -misplaced card looked wrong. Screenshotted live: 4 cards locked
      correct + 1 wrong, which is mathematically impossible for a true
      permutation of 5 unique ids compared position-by-position (a
      permutation can't have exactly n-1 fixed points) — that
      impossibility is what proved it was a real bug, not a data
      surprise. Fixed by switching to `g.lockedIds` (a `Set` of event
      ids) and reconstructing the board on every check —
      already-locked ids are forced back to their one true correct
      index (`g.correctIds.indexOf`), unlocked ids fill the remaining
      slots in DOM relative order — so a locked card is now structurally
      immune to index drift. Verified with a standalone Node script
      simulating the exact drift scenario before shipping, not just
      re-reasoning about it.
    - **Reshuffle only changed the order, not which events were
      sampled.** `buildTimelineGame`'s sampling picked the exact same
      evenly-spaced midpoint indices every time for a given
      character+difficulty, so hitting Reshuffle only ever produced a
      new permutation of the identical 5 (or 3, or 8) events. Fixed by
      splitting the timeline into `n` roughly-equal segments and
      picking a *random* index within each segment instead of the fixed
      midpoint — Reshuffle can now swap which moments appear, not just
      their order, while still spreading across the character's whole
      life rather than letting all n picks cluster together.

66. **"Deep study" supporting-cast expansion, pass 1: 2 Samuel's
    civil-war and rebellion supporting cast.** **Done (2026-09-11).**
    New direction from the owner right after the whole Bible was first
    curated: every book so far only captured *major* figures and
    events; the owner wants supporting characters captured too — not by
    a raw mention-count threshold, but by whether they genuinely drive
    a story forward (their own example: David's commanders, Tamar's
    story — both already covered from the original pass, which is what
    surfaced the real gap: *other* supporting figures in the very same
    chapters never got their own records). First slice, chosen because
    it's the owner's own example book: 10 new characters, all inside
    the existing `era_united_kingdom` (no new era needed) — Abner
    (Saul's/Ishbosheth's commander who defects to David and is murdered
    by Joab in revenge), his killer's own brother Asahel (whose death
    starts that blood feud), Abishai (the third son of Zeruiah,
    recurring alongside Joab), Ahithophel and Hushai (the counselor
    whose advice is regarded "as if a man inquired at the inner
    sanctuary of God," defeated from the inside by David's own friend
    posing as a defector — directly fulfilling David's own prayer,
    "turn the counsel of Ahithophel into foolishness," 2 Samuel 15:31),
    Ittai the Gittite (a foreign commander who refuses David's offer to
    sit out his exile — "in what place my lord the king is... your
    servant will be there also"), Shimei (curses David during his
    flight, is spared from Abishai's sword, later begs mercy and gets
    it), Amasa (Absalom's commander, then David's own as a
    reconciliation gesture, then murdered by the jealous Joab he
    replaced), Sheba (leads a fresh revolt the moment Absalom's ends),
    and the wise woman of Abel (unnamed but real, same precedent as the
    widow of Zarephath — ends the siege against her city by her own
    negotiation, not a battle). 6 new stories, 23 new life events (2 of
    them on the *existing* `char_joab` — his murders of Abner and
    Amasa — queried his current `sequenceInLife` values, `[10, 20]`,
    before picking `5` and `30` so nothing collided, the same lesson
    from item 47 holding for a character revisited many batches later).
    Two new `"brother of"` Connections (Joab/Abishai, Joab/Asahel — the
    "sons of Zeruiah" trio). 22 new curated verses, no new topics — the
    existing 38 covered betrayal, loyalty, wisdom, forgiveness, and
    prayer without strain, including a direct hit for 2 Samuel 15:31
    (David's prayer against Ahithophel) on `topic_prayer`. This is
    explicitly the first slice of a long-haul, multi-session project —
    see CLAUDE.md's "Known gaps" item 10 for the fuller framing and the
    "narrative importance, not mention count" selection principle.

67. **"Deep study" supporting-cast expansion, pass 2: Paul's circle.**
    **Done (2026-09-11).** A much bigger gap than pass 1 found — almost
    none of Paul's actual companions were curated at all, not even
    Timothy or Titus despite epistles addressed to them by name, nor
    Mark or Luke despite being Gospel authors. 10 new characters, all
    inside the existing `era_early_church` (no new era needed):
    Priscilla and Aquila (the tentmaker couple who host Paul and take
    the eloquent-but-incomplete teacher Apollos aside to "explain the
    way of God more accurately" — Paul later says they "risked their
    own necks" for him), Apollos himself (whose later effective
    ministry in Corinth creates a faction problem Paul has to defuse:
    "I planted, Apollos watered, but God gave the increase"), Lydia
    (the first convert in Philippi, and Europe), John Mark (deserts
    partway through the first missionary journey, causes a split
    between Paul and Barnabas sharp enough that they part ways over it,
    and is explicitly reconciled decades later — "he is useful to me
    for service," 2 Timothy 4:11, likely Paul's last letter), Timothy
    and Titus (Paul's two closest delegates, each with an epistle
    addressed to them — Timothy introduced at Lystra and later called
    "my true child in faith"; Titus sent into the hard Corinthian
    situation and bringing Paul real comfort on his return), Onesimus
    and Philemon (the runaway slave and the master Paul appeals to on
    his behalf — the entire book of Philemon in miniature), and Demas
    (named in the very same last letter as John Mark, but as the one
    who left, "having loved this present world" — a small, deliberate
    contrast). 8 new stories, 25 new life events, including 3 on
    already-curated characters where the new material was genuinely
    also a beat in *their* story: Barnabas gets a new event for
    splitting from Paul over Mark (`sequenceInLife` 25, after his
    existing 10/20), and Paul gets two — meeting Timothy (45, between
    his existing 40/50) and sending Onesimus back to Philemon (95,
    after his existing max of 90) — each checked against his current
    values first, same discipline as pass 1's Joab events. One
    existing verse (1 Timothy 4:12, already curated for `topic_identity`
    with no character tag) got `char_timothy` merged onto it rather
    than being duplicated — the curation script was extended to merge
    topic/character tags onto an already-present verse id instead of
    raising an error, since this is the first batch in the whole
    project where new curation genuinely overlapped a previously-tagged
    verse rather than always hitting fresh ones. 41 new curated verses,
    no new topics — the existing 38 covered scripture, loyalty,
    friendship, forgiveness, betrayal, and temptation (Demas) without
    strain.

68. **Fix: back navigation always jumped to the top of the screen.**
    **Done (2026-09-11).** Reported directly by the owner: opening a
    character's profile from a scrolled-down position in a list, then
    going back, lost the scroll position — landed back at the top of
    the list instead of where they'd been. Root cause: `go()`
    unconditionally called `window.scrollTo(0,0)` on every navigation,
    forward or backward, with no memory of where any screen had been
    scrolled to. Fixed generally rather than special-cased to the
    People screen: a new `scrollPositions` map, keyed by
    `screen(+id)` (`scrollKey()`), records `window.scrollY` for the
    *current* view right before every navigation, and `go()` restores
    the saved position for the *destination* view if one exists
    (falling back to 0 for a screen/id never visited before, so a
    freshly opened detail page still opens at the top — only a
    genuine return trip restores anything). Since every navigation in
    the app already funnels through the one `go()` function, this one
    change fixes the problem everywhere it could occur — People,
    Topics, Browse, Stories, and every "back" action (`verse-back`,
    `story-back`, `motif-back`, `back-to-characters`, `back-to-topics`)
    — not just the specific case the owner happened to notice.

69. **Fix: major characters weren't tagged on new supporting-cast
    stories centered on their own decisions.** **Done (2026-09-11).**
    Reported directly by the owner after looking at Paul's own page
    following the Paul's-circle batch (item 67): the new characters
    were there, but several of the interactions weren't showing up on
    *Paul's* page. Root cause: `characterStories()` filters purely on
    `characterIds` membership (§9 below), and three of the eight new
    stories — Lydia's conversion, Priscilla and Aquila hosting him —
    never had `char_paul` added to that array, even though he's the
    one preaching/lodging in every one of them; the batch tagged the
    person each story was centrally *about* but not every major figure
    genuinely present in the scene. The same bug, same shape, turned
    out to already be sitting in the *previous* pass too (item 66):
    none of 2 Samuel's six new stories had `char_david` tagged, despite
    every one of them centering on a decision David himself makes
    (receiving Abner, offering Ittai a way out, sending Hushai back,
    restraining Abishai then pardoning Shimei, appointing Amasa,
    sending Joab after Sheba). Fixed both in one pass: `char_paul`
    added to the three under-tagged stories, `char_david` added to all
    six 2 Samuel ones, plus matching new life events on each of their
    own timelines so the "minor incidents" the owner asked for actually
    show up as moments in the *major* character's life too, not only
    the new minor character's — 2 new events on Paul (`sequenceInLife`
    48, 62, checked against his existing values first) and 6 on David
    (`sequenceInLife` 65, 132-134, 142, 144, same discipline). Lesson
    written up in `pipeline/README.md`'s lessons-learned section: when
    curating a new/minor character's story, separately ask which
    existing major character is also directly present, and tag them
    too — a story invisible on the wrong character's page doesn't
    error anywhere, so it's easy to miss without actually checking that
    page.

70. **"Deep study" supporting-cast expansion, pass 3: Genesis's
    supporting cast — the biggest gap found yet.** **Done (2026-09-11).**
    Only the direct patriarchal line (Abraham, Sarah, Hagar, Lot,
    Ishmael, Isaac, Rebekah, Esau, Jacob, Rachel, Leah, Joseph) had ever
    been curated in Genesis — every one of Jacob's other eleven sons,
    both concubine-wives, his one named daughter, Judah's
    daughter-in-law, his father-in-law, Joseph's Egyptian master and
    that master's wife, the servant who found Rebekah, and the two
    fellow prisoners whose dreams Joseph interprets were never touched
    at all, despite carrying some of Genesis's richest narrative
    material. 16 new characters, all inside the existing
    `era_patriarchs`: **Reuben, Simeon, Levi, Judah, Benjamin** (Jacob's
    other sons — Judah in particular carries a real arc, from
    proposing Joseph's sale, through fathering Perez by Tamar without
    recognizing her, to pledging his own life for Benjamin and
    receiving the "scepter" blessing that points toward the messianic
    line); **Bilhah, Zilpah** (Rachel's and Leah's servants, given to
    Jacob, mothers of four of the twelve tribes); **Dinah, Shechem**
    (her assault and the brothers' bloody revenge); **Tamar**
    (disambiguated as `char_tamar_judahs_daughter_in_law` since
    `char_tamar` already names David's daughter — same disambiguation
    pattern as the two Zechariahs and Joseph-husband-of-Mary; her
    story ends in Judah's own confession, "she is more righteous than
    I," and her son becomes a Davidic-line ancestor); **Laban** (the
    deceiver deceived — substitutes Leah for Rachel, echoing Jacob's
    own earlier deception of Isaac); **Potiphar, Potiphar's wife**
    (unnamed in the text, kept unnamed here per the project's standing
    precedent); **Abraham's servant** (also deliberately left unnamed
    — Genesis 24 itself never names him, and equating him with the
    Eliezer mentioned in passing back in Genesis 15:2 is a traditional
    inference the text doesn't actually make, so the more rigorous call
    is to follow the chapter's own anonymity rather than import a name
    from a different, unconnected verse); **the cupbearer, the baker**
    (Joseph's fellow prisoners — same three-day dream-interpretation
    structure, opposite outcomes, and the cupbearer's forgetting sets
    up the two-year delay before Joseph is ever freed).

    Unlike passes 1-2, this one leaned mostly on **extending existing
    Stories** rather than adding new ones, since the supporting cast
    was always part of scenes that were already curated (from the
    project's very first pass, long before the "major events only"
    critique existed): `story_rebekah_at_the_well`,
    `story_jacob_rachel_leah`, `story_joseph_sold`,
    `story_joseph_and_potiphar`, `story_joseph_interprets`, and
    `story_jacob_blesses_sons` all got the relevant new characters (and
    a few new verses) folded directly into their existing
    `characterIds`/`verseIds` rather than being duplicated — the
    project's long-standing "extend, don't clone" rule applied to
    *tagging* now, not just whole retold narratives. Four genuinely new
    stories cover material with no prior Story at all:
    `story_dinah_and_shechem`, `story_reuben_and_bilhah`,
    `story_judah_and_tamar`, and `story_brothers_return_for_benjamin`
    (the Simeon-hostage/Judah's-pledge arc across Genesis 42-44). Item
    69's lesson was applied proactively this time instead of being
    fixed after the fact: `char_jacob` is tagged and given new life
    events on both new stories he's genuinely present for (fearing the
    fallout from Dinah's revenge, hearing about Reuben and Bilhah,
    reluctantly risking Benjamin), and `char_joseph` gets one for
    testing his brothers before revealing himself — both characters'
    existing `sequenceInLife` ranges (`[10..100]` for each) checked
    first. 48 new curated verses, 2 existing ones (from the very first,
    pre-supporting-cast Genesis pass) merged with new character tags
    rather than duplicated. No new topics — the existing 38 covered
    betrayal, justice, humility, temptation, and blessing without
    strain.

71. **"Deep study" supporting-cast expansion, pass 4: three books at
    once — 1 Samuel, Exodus, Numbers.** **Done (2026-09-11).** A
    deliberate change of shape from passes 1-3: rather than one book's
    supporting cast, this pass spans three separate books' worth of
    rich, self-contained material that had nothing to do with each
    other narratively but shared the same "genuinely drives the plot,
    never curated" profile. 15 new characters, all inside existing
    eras (`era_united_kingdom` for the 1 Samuel figures,
    `era_exodus` for the rest — Numbers already lives there alongside
    Exodus, per its own earlier eras):

    **1 Samuel — David's fugitive years** (6 characters): Nabal and
    Abigail (his insult nearly gets his household killed; her
    intervention becomes the reason David marries her ten days after
    Yahweh strikes him dead), Doeg the Edomite and Ahimelech (the
    priest who unknowingly helps a fugitive David, defends himself to
    Saul's face, and is killed for it — along with 84 other priests and
    the entire city of Nob, when Saul's own guards refuse and Doeg does
    it himself), Abiathar (the one son of Ahimelech who escapes and
    becomes David's own priest for the rest of his reign), and Achish
    of Gath (fooled first, later genuinely trusted David as a vassal
    for over a year, and is the one forced to send him home before
    Gilboa).

    **Exodus** (3 characters): Jethro (his blunt "you will surely wear
    away" and the tiered-judges system Moses actually adopts), and
    Shiphrah and Puah, the two named Hebrew midwives whose civil
    disobedience — years before Moses is even born — is part of what
    keeps his whole generation alive.

    **Numbers** (6 characters): Phinehas (Aaron's grandson, whose
    on-the-spot zeal stops a plague and earns "my covenant of peace"),
    and Zelophehad's five individually-named daughters — Mahlah, Noah
    (`char_noah_daughter_of_zelophehad`, disambiguated from the
    flood's Noah), Hoglah, Milcah (`char_milcah_daughter_of_zelophehad`,
    disambiguated from Nahor's wife Milcah in Genesis), and Tirzah —
    whose joint petition ("why should the name of our father be taken
    away... because he had no son?") gets a direct, immediate ruling
    from Yahweh changing Israel's inheritance law: "the daughters of
    Zelophehad speak right." All five share nearly identical individual
    life events (each petitioning together) since the text itself
    treats their action as genuinely collective while still insisting
    on naming each of them individually — the same instinct honored
    here as five short records rather than one merged one.

    7 new stories (Nabal and Abigail; Doeg and the priests of Nob;
    David and Achish; Shiphrah and Puah; Jethro's advice; Phinehas
    stops the plague; Zelophehad's daughters), 45 new curated verses,
    no new topics. Item 69's lesson applied proactively from the start
    again: David, Saul, and Moses are each tagged and given a matching
    new life event on every story here they're genuinely part of
    (David helped at Nob, talked down by Abigail, serving Achish; Saul
    ordering Nob's priests killed; Moses adopting Jethro's plan and
    ruling on Zelophehad's daughters) — their existing `sequenceInLife`
    ranges (David up to 170, Saul up to 50, Moses up to 280) checked
    first in every case.

72. **"Deep study" supporting-cast expansion, pass 5: the Gospels'
    supporting cast.** **Done (2026-09-11).** The pattern behind every
    curated Gospel gap so far: the big, communal "nature miracles"
    (calming the storm, walking on water, feeding the 5000) were
    curated from the start, but the individual, personal healing and
    interaction stories — arguably the ones that show Jesus's
    character most directly, one person at a time — were never given
    their own Characters or Stories at all. 14 new characters, all
    inside `era_jesus_ministry` except two passion-week figures in
    `era_passion_and_resurrection`: **Bartimaeus** (the blind beggar at
    Jericho who cries louder when the crowd tells him to be quiet);
    **Jairus** and **the woman with the issue of blood** (two healings
    interwoven in one single episode, Mark 5 — a synagogue ruler's
    dying daughter and a bleeding woman's touch on Jesus's robe, told
    as one Story rather than split in two since the text itself never
    separates them); **the centurion of Capernaum** (whose grasp of
    military authority becomes the clearest picture of faith Jesus has
    yet seen — "not even in Israel"); **the widow of Nain** (unnamed,
    her only son raised — deliberately written up echoing the widow of
    Zarephath, the same shape of a grieving mother's last support
    restored); **Malchus** (the high priest's servant whose ear Peter
    cuts off at the arrest — folded into the *existing*
    `story_betrayal_and_arrest` rather than a new Story, since it's a
    detail within an already-curated scene, not a separate event);
    **the centurion at the cross** (folded into the existing
    `story_crucifixion` the same way); **Simon the Pharisee** and **the
    forgiven woman** (Luke 7:36-50 — deliberately kept distinct from
    Mary of Bethany's later, different anointing at Simon the *leper's*
    house, a conflation later tradition makes that the text itself
    never does); **Joanna** and **Susanna** (the named women, alongside
    Mary Magdalene, who financially supported Jesus's ministry — Joanna
    reappears by name at the empty tomb, Luke 24:10); **the man born
    blind** (John 9's extended interrogation-and-expulsion narrative,
    ending in him worshiping Jesus after being thrown out of the
    synagogue for his own testimony); **the paralytic lowered through
    the roof** (Jesus responds to *his friends'* faith, not just his
    own); and **Simon the leper** (host of the anointing at Bethany,
    where Mary of Bethany — already curated — anoints Jesus before his
    burial).

    9 new stories, 2 existing ones extended (`story_betrayal_and_arrest`,
    `story_crucifixion`), 52 new curated verses, no new topics.
    `char_jesus` — already carrying 39 life events, nearly one per
    existing Gospel Story — picked up 9 more, one for each new story
    he's the one acting in (his existing `sequenceInLife` values are
    the exact multiples of ten from 10 to 390, checked before inserting
    new ones like 95, 105, 145, 205, 225, 238 between them); `char_peter`
    picked up one for cutting off Malchus's ear (checked against his
    existing `[10..120]` range first). Item 69's lesson held from the
    start of the pass, same as items 70-71.

73. **"Deep study" supporting-cast expansion, pass 6: Job, 1 Kings,
    Esther, and Acts.** **Done (2026-09-11).** Four more books/eras at
    once, continuing the shape of pass 4:

    **Job** — only Eliphaz had ever been curated as one of Job's three
    friends, despite Bildad and Zophar each getting a full chapter of
    their own dialogue with Job. Adds **Bildad**, **Zophar** (both
    folded into the existing `story_jobs_complaint_and_friends` and
    `story_jobs_restoration` rather than duplicated — they're rebuked
    by Yahweh and restored alongside Eliphaz in the very same verses
    already curated there), **Elihu** (the younger fourth speaker who
    waits out of deference until the other three finish, then speaks
    at length — notably, Yahweh never rebukes him the way he does the
    other three), and **Job's wife** (unnamed, her one blunt line —
    "renounce God, and die" — folded into the existing `story_job_tested`).

    **1 Kings** — **Obadiah** (Ahab's own household manager, secretly
    hiding a hundred of Yahweh's prophets from Jezebel at his own risk;
    a new Story, `story_obadiah_hides_prophets`, placed right before
    the existing Carmel story since it's literally the scene that sets
    Carmel up) and **Micaiah** (the one prophet Ahab openly hates for
    telling him the truth — a new Story, `story_micaiahs_true_prophecy`,
    covering a battle and a death for Ahab that had never been curated
    at all despite Ahab already existing as a character since the
    original 1 Kings pass).

    **Esther** — **Hegai** (favors Esther among the women, folded into
    the existing `story_esther_becomes_queen`), **Zeresh** (Haman's
    wife, whose advice to build a gallows for Mordecai becomes the very
    gallows Haman is hanged on — folded into
    `story_esther_banquet_and_hamans_pride` and `story_hamans_fall`),
    and **Harbonah** (mentions the gallows to the king at exactly the
    right moment — folded into `story_hamans_fall`).

    **Acts** — **Ananias** and **Sapphira** (a new Story — the
    community-of-goods deception that ends in both of them dying at
    Peter's words, a real gap despite Pentecost and the early church's
    founding already being curated), **Simon Magus** and **Philip the
    evangelist** (one new Story spanning both of Philip's Acts 8
    episodes — Samaria and the Ethiopian eunuch — since the text treats
    them as one continuous ministry stretch; Philip's much later
    reappearance hosting Paul, Acts 21:8-9, folded into the existing
    `story_pauls_arrest` instead of forcing a third new Story for two
    verses), **Rhoda** (a new Story, `story_peters_prison_escape` —
    another real gap: Peter's own angelic prison escape in Acts 12 had
    never been curated at all, despite Peter already being one of the
    most-covered characters in the whole project), and **Eutychus**
    (a new Story for the young man Paul raises after he falls asleep
    and falls from a third-floor window).

    15 new characters, 6 new stories, 7 existing stories extended
    (`story_job_tested`, `story_jobs_complaint_and_friends`,
    `story_jobs_restoration`, `story_esther_becomes_queen`,
    `story_esther_banquet_and_hamans_pride`, `story_hamans_fall`,
    `story_pauls_arrest`), 53 new curated verses, no new topics. Item
    69's lesson held throughout: `char_job`, `char_elijah`, `char_ahab`,
    `char_jehoshaphat`, `char_esther`, `char_haman`, `char_peter`, and
    `char_paul` are each tagged and given a matching new life event on
    every story here they're genuinely part of — their existing
    `sequenceInLife` ranges (Job up to 40, Elijah up to 50, Ahab and
    Jehoshaphat up to 20, Peter up to 120, Paul up to 95) checked first
    in every case, this time as a matter of course rather than a lesson
    being freshly re-applied.

74. **"Deep study" supporting-cast expansion, pass 7: Genesis, Numbers,
    Judges, and 2 Kings.** **Done (2026-09-12).** 13 new characters:
    **Melchizedek** (Genesis 14 — king of Salem, priest of God Most
    High, blesses Abram and receives the Bible's first tithe, then
    never appears in Genesis again); **Abimelech** (`char_abimelech_king_of_gerar`
    — the "king of Gerar" role recurring across a generation, first
    with Abraham and Sarah, Genesis 20, then with Isaac and Rebekah,
    Genesis 26 — two separate new Stories for the same character,
    since the text never treats them as one continuous scene, just the
    same royal role playing out the same trick twice); **Balak**
    (Balaam's employer, folded into the *existing*
    `story_balaams_donkey` — which already spanned the whole Balaam
    narrative without ever naming who hired him); **Othniel** (Israel's
    actual first judge, Judges 3:7-11 — a real gap despite ten Judges
    characters already being curated, since the cycle's template-
    setting first deliverer had never been named) and **Shamgar** (one
    verse, shares Othniel's new Story since Judges places them back to
    back); a second, unrelated **Abimelech**
    (`char_abimelech_son_of_gideon` — Gideon's own son, who kills his
    seventy brothers on one stone, makes himself king, and dies by a
    millstone dropped from a besieged wall); the four "minor judges"
    **Tola**, **Jair**, **Ibzan**, **Elon**, **Abdon** (five people
    across two new Stories, each getting only a sentence or two of
    text — the same "name them individually even when the record is
    thin" instinct as Zelophehad's daughters, item 71); and
    **Athaliah** and **Jehosheba** (the six-year usurpation and the
    rescue that kept the Davidic line alive — folded into the
    *existing* `story_joash_and_zechariah`, which already spanned
    Joash's whole reign from his infant hiding onward, rather than a
    duplicate new Story for the same span).

    7 new stories, 2 existing ones extended
    (`story_balaams_donkey`, `story_joash_and_zechariah`), 40 new
    curated verses, no new topics. `char_abraham`, `char_sarah`,
    `char_isaac`, and `char_rebekah` — all already extensively
    curated since the project's very first pass — are each tagged and
    given a matching new life event on the Abimelech stories they're
    genuinely part of (their existing `sequenceInLife` ranges, up to
    120/50/60/40 respectively, checked first in every case, per item
    69's now-routine discipline).

75. **"People in this book" — browse a book, see who's in it, in the
    order they appear.** **Done (2026-09-12), redesigned same day
    after direct feedback.** Owner's request: with the "deep study"
    expansion making the per-book cast list genuinely rich (2 Samuel
    alone surfaces 22 named people), the app needed a way to just open
    a book and see everyone tagged in it, rather than only reaching a
    character from the People-grouped-by-era list.

    **First version** (superseded within the same session): a row of
    tappable pills sitting directly above the chapter grid on Browse's
    per-book view. The owner didn't like it inline and asked for a
    dedicated tab instead — "People in this book" as its own row,
    tapped into a full screen, listing people *chronologically*, with
    back navigation returning to that same screen rather than the
    People-grouped-by-era list.

    **Current version.** Browse's per-book view now shows a single
    `.list-row` — "People in Genesis," with a count — that navigates to
    a new screen, `bookPeople` (`renderBookPeople(book)`), listing
    every character tagged in that book as `.list-row`s via the same
    `renderCharacterRow()` already used on the People screen. "Order
    they appear" is read as *reading order through the book*, not
    strict historical chronology (Genesis and Judges, for instance,
    aren't always the same thing) — `charactersInBook(bookName)` now
    tracks each character's lowest `chapter*1000+verse` among their
    tagged verses in that book (chapter/verse numbers never reach
    1000, so this packs both into one sortable integer safely) and
    sorts by that, rather than the alphabetical order the first version
    used.

    **The back-navigation ask needed a real fix, not a one-off.**
    Tapping a person from `bookPeople` had to return there specifically
    on back, not to the generic People list. Rather than hardcode that
    one case, `open-character`'s handler was changed to always capture
    `from: view` (the exact pattern `open-verse`/`open-story`/
    `open-motif` already used) and Character detail's back button
    became a new `character-back` action reading `view.params.from`
    (falling back to the People list only if none was set) — replacing
    the old always-`back-to-characters` button. This one change fixes
    the same "always jumps to the wrong place" class of bug (§8 item 68)
    everywhere `open-character` is used, not just from `bookPeople` —
    Family cards, "Appears alongside" rows, and the Verse detail
    "People" section on a character's page now all correctly return to
    wherever the user actually came from. `scrollKey()` (item 68) also
    needed a small fix alongside this — it only recognized
    `view.params.id`, so every `bookPeople` view (keyed by
    `view.params.book`) collapsed onto the same cache entry regardless
    of which book was open; now checks either field.

    Deliberately **still no new `Character.book` field**, for the same
    reason as the first version: a character routinely spans several
    books (Moses across Exodus through Deuteronomy, David across
    Samuel, Kings, and Chronicles), so a single field would force a
    false one-book choice and need a migration across all 254
    characters. `charactersInBook()` stays a pure render-time
    derivation over `data.verses`, unchanged in that respect from the
    first version — only its sort order and its consumer (a full screen
    instead of an inline pill row) changed. Verified directly against
    the real curated data both times, not just reasoned about: Genesis's
    ordering opens Eve, then Adam, then Noah, then Abraham — each
    number checked against the actual `chapter*1000+verse` key before
    trusting the sort.

76. **Fix: real, fully-curated characters were silently missing from
    "People in this book."** **Done (2026-09-12).** Reported directly
    by the owner: Cain, Abel, and Lot never appeared in "People in
    Genesis" despite all three having existed as full Characters (with
    their own Stories) since the project's very first curation pass,
    weeks before "deep study" existed as a direction. Root cause:
    `charactersInBook()` (item 75) derived membership purely from a
    verse's own `characterIds` — but 15 real characters across the
    whole project (Cain, Abel, Hagar, Lot, Ishmael, Rachel, Leah,
    Pharaoh, Eleazar, Sanballat, Belshazzar, Elizabeth, Philip, Simon
    of Cyrene, Cornelius) have **zero** verses individually tagged to
    them — their scene's curated verse got tagged to a co-star instead
    (Genesis 4:7, `story_cain_and_abel`'s own verse, carries no
    `characterIds` at all). A character with a real Story and zero
    tagged verses was invisible to a feature that only read verse tags.

    Fixed by adding a second signal to `charactersInBook()`: walk every
    Story's own `verseIds`, and if any of them fall in the requested
    book, credit *every* character in that Story's `characterIds` —
    not just whoever the verse itself happened to name. This is exactly
    the same "the major/minor character actually present in a scene
    needs to be tagged, or they silently vanish from views that key off
    tags" shape as item 69's bug, one layer down: item 69 was about a
    *Story* missing a character tag; this one is about a *feature*
    trusting only one of two signals that already existed in the
    curated data. Fixed for all 14 of the 15 characters this way,
    verified directly against the built data before shipping (Genesis
    28 → 34 people, Cain/Abel now sandwiched between Adam and Noah
    exactly where Genesis 4 belongs).

    The 15th, **Hagar**, needed a real content fix, not a code one:
    both of her existing Stories (`story_hagar_and_ishmael`,
    `story_hagar_sent_away`) have had **empty `verseIds`** since their
    original curation — no curated verse existed anywhere for either
    signal to find. Added 8 real WEB verses across both (Genesis
    16:1-13, 21:9-19 — Hagar's conception and flight, "you are a God
    who sees," being sent away, and the angel opening her eyes to a
    well), filled into the previously-empty `verseIds` arrays. No new
    characters, stories, or topics — a pure gap-fill on two
    already-correctly-tagged Stories.

77. **Topics grid palette, punchier again.** **Done (2026-09-12).**
    Same ask as the item 63 follow-up, one more round: all 12
    `TOPIC_PALETTE` colors pushed more saturated/vivid again (e.g.
    `#1786AD`→`#0EA5D6`, `#D6237D`→`#F0158A`). Checked white-text
    contrast on every swatch before shipping this time, not just
    picked by eye — two of the brightened yellows
    (`#E0B800`/`#F5BE00`, both under 2.0:1 against white) were pulled
    back to deeper, still-punchier-than-before golds
    (`#B88E00`/`#9C7A1E`, 3.04:1/4.03:1) so the topic name text stays
    legible; the rest of the palette sits in the same 2.2-5.6:1 range
    the *original* palette (item 63) already did, so this isn't a new
    tradeoff, just not making the worst case worse. No CSS structure
    changes — `topicColor()`'s hash assignment and `topicAccentVars()`'s
    derived tint/wash for topic-detail pages are untouched, since only
    the twelve base hex values themselves changed.

78. **Home redesign, and a real identity shift: memorization is now one
    part of the app, not its whole front door.** **Done (2026-09-14).**
    Direct owner request, framed explicitly as a vision change, not just
    a layout one: "though this project started out as a Bible
    memorization tool, it has since evolved from it... I don't want
    memorization to be the app's identity, but just a part of it." This
    doesn't actually contradict anything already on record — CLAUDE.md's
    own "vision" section has said since the project's early days that
    "the owner's goal isn't just verse memorization — it's a study
    companion" — but Home itself never caught up to that; it had shown
    the MVP's original due-today/practice-button layout since
    2026-09-03. This item is Home's design finally matching a vision
    statement that predates it by weeks.

    **Practice becomes its own tab.** Everything Home used to show —
    the due-today/library/mastered/streak stat row, the daily-goal ring
    (`renderGoalRing()`), the challenge-type picker
    (`renderChallengePicker()`), the "Practice N due verses" button,
    and the full verse library list — moved verbatim into a new
    `renderPracticeLanding()`, which is what the Practice screen shows
    whenever there's no active session (previously the Practice screen
    only ever rendered an active session or the completion screen,
    since Home was the only way to *start* one — a session always
    existed by the time you landed there). A new bottom-nav tab,
    **Practice** (between Home and Browse), makes this screen reachable
    at all now that Home no longer hosts the one button that used to
    lead there. `renderPractice()` now branches three ways: no
    `session` → `renderPracticeLanding()`; `session.index >=
    session.queue.length` → the existing completion screen (unchanged);
    otherwise → the existing active-session UI (unchanged). "Done" on
    the completion screen (`exit-practice`) now returns to
    `go('practice')` instead of `go('home')`, landing back on the
    freshly-empty landing state rather than a Home that no longer shows
    any of this.

    **Home becomes purely editorial: Verse of the Day.** A date-seeded,
    stable-for-the-day pick from the user's own library (`data.verses`,
    the merged seed+overlay — not the full 31,098-verse corpus, so it's
    always something actually in the user's library), the same index
    for every device on a given day since it's a pure function of the
    date and library length, no stored state. Rendered as a warm
    gradient card (`.votd-card`, `--gold-wash` fading into
    `--paper-raised`) since there's no real verse artwork yet — the
    same "don't spend real money on imagery until the layout is proven"
    call already made once for character portraits
    (`generate_character_art.py`, not yet run for real). Tapping it
    opens the verse's own detail page via the existing `open-verse`
    action, which already threads `from: view` (item 75's fix) so back
    navigation correctly returns to Home.

    **Home becomes purely editorial: Unreached of the Day.** The
    owner's other idea — daily missionary/mission-field content, in the
    spirit of YouVersion's own Unreached of the Day feature — sourced
    from the free [Joshua Project API](https://joshuaproject.net/api/v2)
    rather than curated locally, a deliberate scope decision made after
    weighing it directly with the owner: static curated content stays
    fully offline like everything else in the app, but goes stale
    between manual refreshes; a live API stays current automatically
    but is a genuinely different kind of feature for this app — the
    first thing in it that isn't pre-curated, static, shipped data.

    Architecture, decided *before* writing any code, for two concrete
    reasons rather than by default: (1) Joshua Project's own
    documentation only shows server-side sample code (PHP/Python/Ruby)
    and never confirms CORS support for a direct browser fetch — an
    unconfirmed dependency the app shouldn't inherit; (2) even if CORS
    worked, the API key would have to ship inside the PWA's client-side
    JS, visible to anyone via view-source. So: a new Azure Function,
    `GET /api/unreached-of-the-day` (`api/src/functions/unreached.js`),
    proxies Joshua Project's `daily_unreached.json` endpoint server-side,
    reading the key from a `JOSHUA_PROJECT_API_KEY` Function App
    setting — the same "secret lives only in a server-side app setting,
    never in the repo or the client bundle" pattern `sync.js` already
    established for `COSMOS_CONNECTION_STRING`. Unlike `sync.js`, this
    endpoint is **not** gated to signed-in users (Home shows it to every
    visitor), so `staticwebapp.config.json` gained one explicit route
    exception (`/api/unreached-of-the-day`, `allowedRoles:
    ["anonymous"]`) placed *before* the general `/api/*` → authenticated
    wildcard rule, rather than loosening that wildcard itself. The
    upstream JSON is normalized server-side into a small, stable shape
    (`{name, country, population, religion, percentEvangelical,
    percentAdherent, language, photoUrl}`) built from Joshua Project's
    own documented column names (`PeopNameInCountry`, `Ctry`,
    `Population`, `PrimaryReligion`, `PercentEvangelical`,
    `PercentAdherents`, `PrimaryLanguageName`, `PeopleGroupPhotoURL`) —
    written from their published column-description docs before any key
    existed to test against.

    **Verified the same day, once the owner set `JOSHUA_PROJECT_API_KEY`.**
    A live check against the deployed endpoint
    (`/api/unreached-of-the-day`) returned a real people group (Pinjara,
    India, ~3.5M, Islam, Urdu) with every field populated exactly as
    `buildResult()` expected, including a working `photoUrl` — the
    field-name guesses were all correct on the first real call, no
    `buildResult()` fix needed. That live photo prompted a same-day
    follow-up: the card was originally text-only (photos were considered
    out of scope, the same "prove it first" reasoning applied to Verse
    of the Day and character portraits), but since Joshua Project
    already provides one for free with every response — no generation
    cost, no separate decision — `renderUnreachedCard()` now shows it as
    a 160px photo banner (`.unreached-photo`, `object-fit:cover`) above
    the text, with `onerror="this.remove()"` so a broken/missing image
    URL for a given people group just quietly drops the image rather
    than showing a broken-image icon — consistent with the whole
    feature's fail-quiet posture.

    **Fails quiet, by design, on both ends.** No key configured yet →
    the Function returns `501` (a real, expected, ongoing state right
    now) and the client (`loadUnreachedOfDay()`) treats that as
    `'unconfigured'`; any other failure (network error, malformed
    upstream response) becomes `'error'`. Both states, along with the
    initial `'loading'` state, render the card as nothing at all rather
    than an error banner — this is optional editorial content on a
    screen nobody depends on for a core workflow, so a missing card
    should be invisible, not alarming. `loadUnreachedOfDay()` is called
    unconditionally at the top of every `renderHome()` call but is a
    no-op once `status` leaves `'idle'`, so it fires exactly once per
    app session regardless of how many times the user revisits the Home
    tab — this is once-a-day content, not something to refetch on every
    tab switch.

    **One real risk flagged, not yet hit.** `unreached.js` uses the
    global `fetch()` (no `node-fetch` dependency added), which requires
    Node 18+ in the Azure Functions runtime; `api/package.json` and
    `host.json` don't pin an explicit Node version, and Azure Static Web
    Apps' current default runtime is well past that threshold as of
    2026, but this is a real, if small, deployment assumption worth
    knowing about if the function ever fails with "fetch is not
    defined."

79. **Unreached of the Day: a real detail page, and a fixed photo crop.**
    **Done (2026-09-14).** Direct feedback on the shipped card: the
    Home preview's photo wasn't showing fully (a fixed 160px
    `object-fit:cover` box was cropping into portrait photos, cutting
    off the top of the subject's head — visible in a screenshot the
    owner sent), and the card itself felt flat with nowhere to go once
    tapped.

    **Photo crop fix, Home preview.** `.unreached-photo` bumped from
    160px to 190px tall and gained `object-position:center 20%` instead
    of the implicit center-center crop — biases the visible crop toward
    the top of the frame, where a portrait photo's face actually is,
    rather than splitting the crop evenly top/bottom. Still a deliberate
    crop, not the fix for "not displayed fully" — that's the new detail
    page.

    **New `unreachedDetail` screen — the actual fix for "not displayed
    fully."** Tapping the Home card (`.unreached-card` gained
    `tap`/`open-unreached`) now opens a dedicated page,
    `renderUnreachedDetail()`, whose photo (`.unreached-full-photo`) uses
    `width:100%;height:auto` — no `object-fit` at all, so the image
    renders at its full natural aspect ratio with nothing cropped out,
    genuinely showing the whole picture. The page also surfaces fields
    the compact Home card never had room for: population, percent
    evangelical, and percent adherent as a `.stat-row` (reusing the same
    stat-card pattern Practice's landing page uses), plus country,
    religion, and language in a plain `.card` of label/value rows
    (`.char-row` with `justify-content:space-between`, the same pattern
    Settings already uses for its account-bar rows). Closes on a short
    framing paragraph about what "unreached" means and why the card
    exists, rather than just a wall of stats.

    Reached only from Home (no other screen links to it), so back
    navigation is a plain `go-home` rather than needing the generalized
    `from`-tracking pattern from item 75 — there's no ambiguity about
    where "back" should go for a screen with exactly one entry point.

80. **Unreached of the Day, Home card: full redesign to a side-by-side
    layout.** **Done (2026-09-14).** The top-banner photo treatment
    from item 79 still didn't satisfy "show the whole picture" for the
    owner even after the crop-bias fix — a hand-drawn sketch supplied
    directly: text on the left, a small square photo box on the right,
    replacing the full-width banner entirely. `.unreached-card-inner`
    is now a flex row — `.unreached-text` (label, name, meta, population
    — unchanged content, just no longer sharing space with a banner
    image above it) on the left, `.unreached-photo-box` (a fixed 68×68
    rounded square, `background:var(--surface-sunken)` so it reads as a
    deliberate frame rather than empty space) on the right. Inside that
    box, `.unreached-photo` uses `object-fit:contain` rather than
    `cover` — the whole point of this pass — so the image is never
    cropped even at this small size; a non-square source photo
    letterboxes inside the square frame instead of losing any of the
    image, which is exactly what "the entire picture" means literally.
    The full-size, natural-aspect-ratio treatment on the detail page
    (`.unreached-full-photo`, item 79) is untouched — this pass only
    changed the compact Home preview.

81. **Home v5: YouVersion Verse of the Day + Unsplash imagery, Motif
    Spotlight, and a subtle practice nudge.** **Done (2026-09-14).** The
    owner shared a new wireframe (streak badge, hero VOTD+image card,
    a two-column Unreached/Motif row, a bottom practice button) after
    learning YouVersion has a free Platform API. Two things were
    corrected before building, both confirmed by research rather than
    assumed: YouVersion's VOTD endpoint (`/v1/verse_of_the_days/{day}`,
    opened April 2026, free for non-commercial use) has **no background
    images**, and the wireframe's practice button would partially
    reverse the item 78 identity shift. The owner resolved both via
    AskUserQuestion: source imagery **separately from Unsplash**, and
    keep any practice reminder **subtle** rather than the sketched
    button. The streak badge from the wireframe was deliberately **not**
    built — it's progress content, which item 78's own "how to apply"
    note says to flag rather than silently add back to Home.
    - **`api/src/functions/verse-of-the-day.js`** (new) — proxies
      YouVersion the same way `unreached.js` proxies Joshua Project: key
      server-side only (`YOUVERSION_APP_KEY`, a Function App setting,
      never in chat or a file), CORS unconfirmed in YouVersion's docs so
      a same-origin proxy sidesteps it. Asks for `format=text` (the
      endpoint returns HTML by default) and `language_ranges=en`
      (required or the upstream call 422s). Normalizes to
      `{text, reference}`.
    - **`api/src/functions/verse-image.js`** (new) — proxies Unsplash's
      `/photos/random?query=...` for a background photo, entirely
      separate from the YouVersion call above per the owner's choice.
      Keyword is date-seeded from a small fixed pool (nature, mountains,
      sunrise, ocean, forest, sky, desert, meadow) — not derived from
      the verse's topic, which the owner also explicitly chose over
      building a topic→keyword map. Needs `UNSPLASH_ACCESS_KEY`.
      Unsplash's API Terms require on-image attribution to both Unsplash
      and the specific photographer, linked to their profile with UTM
      params — that can only be satisfied client-side, so the proxy
      returns `{imageUrl, photographerName, photographerUrl}` and
      `renderVerseOfTheDayCard()` renders the attribution line itself
      (`.votd-attribution`), never omitted when an image is shown.
    - Both new endpoints got the same `staticwebapp.config.json`
      anonymous-route exception as `/api/unreached-of-the-day`, and the
      same `local.settings.json.example` documentation entries as
      `JOSHUA_PROJECT_API_KEY`.
    - **`renderVerseOfTheDayCard()`** now prefers the YouVersion-sourced
      remote verse (`votdRemote`) over the existing local date-seeded
      pick (`verseOfTheDay()`, kept unchanged as the fallback for
      not-configured/error states). When an Unsplash image loads
      (`votdImage`), the card's background becomes that photo under a
      dark gradient overlay for text legibility, with the attribution
      line beneath. One real trade-off, accepted rather than solved:
      a YouVersion-sourced verse has no corresponding local `Verse`
      record, so the card stops being tappable-to-detail in that case
      (`open-verse` only fires when the local pick is what's shown).
    - **Motif Spotlight** (new) — `motifOfTheDay()` (same date-seeded
      index pattern as `verseOfTheDay()`) plus `renderMotifSpotlightCard()`,
      surfacing one of the 20 curated Motifs on Home, tapping through to
      the existing Pattern detail page. Text only — no Motif imagery
      exists, same "prove the layout before spending on imagery"
      sequencing already used for character portraits and this same
      Verse of the Day card before its own photo (item 81 itself).
    - **`.home-duo`** — a new two-column grid row holding the Unreached
      of the Day and Motif Spotlight cards side by side, per the
      wireframe's layout. `renderHome()` only wraps them in the grid
      when both actually rendered content (either can independently be
      hidden — Unreached when unconfigured/erroring, Motif Spotlight
      only if `motifs` were ever empty) — otherwise whichever one exists
      renders full-width rather than leaving an empty grid cell.
    - **`renderPracticeNudge()`** (new) — the one deliberate reintroduction
      of practice-adjacent content on Home, built exactly to the "keep it
      subtle" brief: a single centered text line, "N verses due for
      practice", `.practice-nudge` styled as quiet muted text with no
      button chrome, taps through to the Practice tab (new `go-practice`
      action). Renders nothing at all when zero verses are due.
    - `sw.js` bumped to `rooted-v77`.

82. **Home v6: hand-specified full redesign — greeting/streak header, a
    media-heavy VOTD hero, and a shared "discovery card" format for
    Unreached of the Day and a new Story of the Day.** **Done
    (2026-09-14), same day as item 81.** Item 81's two-column layout
    ("doesn't look good") was replaced wholesale by a detailed,
    section-by-section spec the owner wrote out directly, rather than a
    wireframe sketch this time. Motif Spotlight and the two-column
    `.home-duo` row are both gone — not in the new spec at all, so
    removed rather than kept as dead code (`motifOfTheDay()`,
    `renderMotifSpotlightCard()` deleted). The streak badge, notably,
    *is* back on Home this time — explicitly requested — which reverses
    the item 81 choice to leave it off as "progress content." Recorded
    here rather than silently overwritten: the item 78 "how to apply"
    note said to flag rather than silently reintroduce progress content;
    this is that flag, and the owner's own explicit spec is the
    resolution — streaks read as a return-visit habit signal, not a
    memorization stat, and the owner wants it front and center the way
    YouVersion itself does it.
    - **`greeting()`** — pure function of `new Date().getHours()`, one of
      five bands (night/morning/afternoon/evening/night), no new storage.
    - **`renderHomeHeader()`** (new) — replaces the old plain
      `.topbar`/brand row entirely. Left: the greeting plus a fixed
      sub-line. Right: `computeStreak()` (already existed, DATA_MODEL.md
      §7, previously only shown in Practice's stat row and the session-
      complete screen) rendered as `.streak-badge` — an orange/red
      gradient pill with a flame icon, high-contrast on purpose per the
      owner's "just like YouVersion" reference — next to the existing
      settings gear button. Hidden entirely at a 0-day streak rather
      than showing "0 days," since a badge announcing zero reads as a
      failure state, not a habit prompt.
    - **`placeholderArt(seed, hueBase)`** (new) — a small inline-SVG data
      URI (an abstract gradient + sun + mountain silhouette in the app's
      gold family by default), hue-seeded from an id via the same
      31-multiplier string hash `topicColor()` already uses elsewhere in
      this file, so different verses/stories/people get a distinct but
      still on-brand placeholder rather than one image repeated
      everywhere. Exists specifically so "what does a media-heavy layout
      feel like" can be judged today, with zero external image
      dependency and zero new binary assets to manage — swapping in a
      real photo or a generated story illustration later only means
      changing what feeds the `src`/`background-image`, not the markup.
      One real bug caught before shipping: `encodeURIComponent` does not
      escape `'`, so the SVG's own attributes had to be written with `"`
      instead — a single-quoted SVG would have leaked literal `'`
      characters into the data URI and broken the single-quoted JS
      string an `onerror` fallback embeds it in.
    - **`renderVerseOfTheDayCard()`**, rebuilt as `.votd-hero` — a
      full-width, full-bleed card (`background-size:cover`, a
      `180deg` dark gradient overlay via `::before` for text legibility)
      instead of item 81's flat card. Real Unsplash photo when
      `votdImage` is ready, `placeholderArt()` otherwise — both paths
      render identically, so there's nothing to change in markup once
      `UNSPLASH_ACCESS_KEY` is set. Verse text now renders in
      **Fraunces** (italic), brought back specifically for this card —
      the rest of the app stayed all-Inter per the v3 dark-theme
      decision (CLAUDE.md "Visual direction"), but the owner's spec
      asked for serif verse text here, so `Fraunces:ital,wght@0,500;
      0,600;1,500` was added back to the Google Fonts `<link>`
      (`index.html` `<head>`) as a scoped addition, not a reversal of v3
      — nothing else references the family. A `.votd-action` pill
      ("Read chapter") now sits inside the card as an explicit tap
      target, shown only when the card is actually tappable (the local
      pick, not a YouVersion-sourced verse with no local `Verse` record
      to open — same constraint item 81 already had).
    - **`storyOfTheDay()` / `renderStoryOfTheDayCard()`** (new) — a
      date-seeded pick from `lore.stories` (same indexing shape as
      `verseOfTheDay()`/old `motifOfTheDay()`), rendered in the new
      shared `.discovery-card` row format: title, `primaryReference`, a
      truncated summary snippet on the left, a `placeholderArt()`
      rectangular thumbnail on the right, tapping through to the
      existing Story detail page (`open-story`). This is the first Home
      surface for the Stories side of the app (Verse of the Day and
      Unreached of the Day were both non-narrative); real per-story
      illustrations are a known future investment (CLAUDE.md known-gaps
      item 2's sibling — character portraits already flagged that
      cost), not attempted here.
    - **`renderUnreachedCard()`** ported onto the same shared
      `.discovery-card`/`.discovery-card-inner`/`.discovery-thumb-box`/
      `.discovery-thumb` classes Story of the Day uses (previously
      `.unreached-card`-prefixed classes, unique to that one card) —
      the "old format" the owner asked to return to (item 80's rectangle-
      with-photo-on-the-right shape) is now the shared row format both
      cards use, not a one-off. Falls back to `placeholderArt(d.name,
      205)` (a fixed blue-family hue) when Joshua Project's own
      `photoUrl` is missing or fails to load, rather than the old
      behavior of just omitting the image box.
    - **`renderPracticeNudge()`** rewritten to the owner's exact copy —
      "Practice N of M due verses →" (N capped at the daily goal, M the
      full due count) — and restyled from a plain centered text line to
      a full-width high-contrast pill (`.practice-nudge`, gold text on a
      raised card background with a hairline border), still shown only
      when `dueVerses().length > 0`.
    - **Bottom nav:** the "People" tab is relabeled **"Study"** (still
      `data-nav="characters"`, same route — People/Stories/Patterns all
      already lived together behind that one tab; only the label was
      stale). Screen-level titles ("People", "Stories", "Patterns")
      inside that tab are unchanged — this only renamed the tab itself.
    - `sw.js` bumped to `rooted-v78`.

83. **Real placeholder photos for the Verse of the Day hero and Story of
    the Day thumbnail, replacing `placeholderArt()`'s generated SVGs in
    those two spots.** **Done (2026-09-14), same day as item 82.** The
    owner supplied two actual images — a mountain-valley landscape photo
    for Verse of the Day, and an illustrated "feeding of the 5000" scene
    for Story of the Day — to use as placeholders until real per-item
    media (Unsplash for VOTD, generated story illustrations) exists.
    - Both arrived oversized for a mobile PWA (the mountain photo was
      3,997,081 bytes at 5760×3840 — a single hero background that size
      would dominate Home's whole load weight). Resized and re-encoded
      with Pillow before committing: `media/home/votd-placeholder.jpg`
      (1200px wide, quality 72 — 165KB) and `media/home/story-
      placeholder.jpg` (600×600, quality 75 — 64KB, since it only ever
      renders inside an 88×72 thumbnail box). The original full-size
      files stay in `pipeline/.artscratch/` (already gitignored — that
      directory exists for the unrelated Gemini character-art pipeline's
      own scratch output, and these just happened to land there too) and
      were never committed.
    - `renderVerseOfTheDayCard()`'s placeholder branch now points at
      `media/home/votd-placeholder.jpg` instead of calling
      `placeholderArt()`; `renderStoryOfTheDayCard()`'s thumbnail does
      the same with `media/home/story-placeholder.jpg` — every Story
      shares this one image for now, regardless of which story the
      date-seed picks, since there's no per-story art yet to key off.
      `placeholderArt()` itself is untouched and still backs Unreached
      of the Day's fallback (`placeholderArt(d.name, 205)`) when Joshua
      Project doesn't supply a photo — that slot doesn't have a supplied
      photo to use instead.
    - `sw.js`'s precache list (`ASSETS`) gained both new paths — Home
      shows one of these on every visit, so they're worth having offline
      from install rather than only picked up by the runtime cache after
      a first online view. Bumped to `rooted-v79`.

84. **Home v6 CSS polish pass — precise spec for the VOTD hero, its CTA,
    the shared discovery-card thumbnails, and the header settings
    button.** **Done (2026-09-14).** The owner sent exact CSS values
    rather than a visual critique this time. `.votd-hero` (the card the
    spec called `.votd-card` — kept its actual class name, already
    referenced from `renderVerseOfTheDayCard()`): `background-position`
    changed from `center` to `center 35%` (biases the placeholder/
    Unsplash photo toward its upper-middle rather than dead center),
    explicit `border:none;border-radius:24px` (the inherited `.card`
    hairline border/20px radius weren't visibly "bright," but the spec
    asked for an explicit override rather than relying on inheritance),
    label/reference color changed from `var(--gold-deep)` to the spec's
    literal `#D49E35` on this card only — a deliberate one-off, not a
    new design-system token. The "Read chapter" CTA (`.votd-action`,
    the spec's `.btn-read-chapter`) restyled to frosted glass exactly as
    specified (`rgba(255,255,255,.15)` + `backdrop-filter:blur(8px)` +
    `rgba(255,255,255,.2)` border) with `margin-top:16px`. Discovery
    thumbnails (`.discovery-thumb-box`/`.discovery-thumb`, shared by
    Unreached of the Day and Story of the Day) now both explicitly carry
    `88×68`, `border-radius:14px`, `object-fit:cover` — previously
    72px-tall boxes with a 12px radius token; now pinned to the exact
    spec values on both the box and the `<img>` itself so there's no
    daylight between them regardless of what's inside. The header
    settings button got a new `.home-settings-btn` class (added
    alongside its existing `.back-btn`, not replacing it, so it keeps
    the shared press-feedback animation for free) — `42×42px`, a 22px
    icon, and a frosted `rgba(255,255,255,.08)` background with a
    `rgba(255,255,255,.1)` border — scoped to Home's settings button
    only, not a global `.back-btn` change, since that class is shared by
    every back button across the app. `sw.js` bumped to `rooted-v80`.

85. **App-wide type scale — shared CSS custom properties for eyebrows,
    titles, body copy, scripture text, headings, and nav/CTA text,
    replacing years of one-off per-component font sizes.** **Done
    (2026-09-14).** The owner sent an explicit token spec (`--text-xs`
    through `--text-2xl`, `--text-primary`/`--text-secondary`/
    `--text-accent`, `--font-sans`/`--font-display`) with a role-by-role
    mapping across every screen, not just Home this time. Added to
    `:root`: `--text-xs:12px`, `--text-sm:14px`, `--text-base:16px`,
    `--text-lg:18px`, `--text-xl:22px`, `--text-2xl:28px`,
    `--text-primary:var(--ink)`, `--text-secondary:var(--ink-soft)`,
    `--font-sans:'Inter',sans-serif`, `--font-display:'Fraunces',serif`.
    `--text-accent` is `#D49E35` specifically (not `var(--gold-deep)`) —
    the exact hex the prior CSS-polish pass (item 84) had already set
    literally on the VOTD label/ref, reused here as the token's value
    rather than introducing a second, slightly different gold.
    - **Eyebrows & badges** (`text-xs`/700/`.05em`/uppercase): applied
      to `.votd-label`, `.discovery-label` (both "Unreached of the Day"
      and "Story of the Day" render through this one shared class —
      changed its color from `var(--tan-deep)` to `--text-accent` to
      match), and `.topic-card .meta` (the verse-count line). One
      deliberate deviation from the literal spec: `.tag` (verse status
      badges — Mastered/Due today/Seedling etc.) got the size/weight/
      caps/letter-spacing treatment but **kept each variant's own color**
      (gold/sage/tan) rather than switching to a single `--text-accent`
      — that three-way color split is deliberate (design philosophy
      rule 3, reaffirmed in the v3 Topics writeup: sage=mastery,
      tan=metadata, gold=urgency) and collapsing it to one accent color
      would erase real meaning the badges currently carry. Similarly,
      `.topic-card .meta` kept its white-on-opacity color instead of
      `--text-accent` — these cards render on arbitrary saturated
      per-topic backgrounds (`TOPIC_PALETTE`), where gold text wouldn't
      stay legible against every color in that palette.
    - **Card & section titles** (`text-lg`/600/`line-height:1.3`):
      applied via the global `h3` rule (covers every card that renders a
      plain `<h3>` — story titles, "Stories"/"Patterns" hub cards,
      Character-in-list `<h3>`s, etc., all for free) plus two explicit
      classes that don't use `<h3>`: `.list-row .name` (book titles in
      Browse, character/people names in Study's People list) and
      `.topic-card .name` (topic names on the colorful grid — its color
      stayed the existing near-white rather than switching to literal
      `#fff`, negligible visual difference since `--text-primary` is
      `#F5F4F1`). `.discovery-card h3` was an existing 15.5px override on
      top of the (then-16px) global `h3` — updated to the same
      `text-lg`/600/1.3 values explicitly rather than deleting the
      override, so its `margin-bottom:3px` stayed intact.
    - **Body copy & subtext** (`text-sm`/400/`--text-secondary`/
      `line-height:1.4`): applied to `.field-hint`, `.char-row .meta`,
      `.list-row .meta` (chapter counts in Browse), and
      `.discovery-meta`/`.discovery-sub` — the latter two were merged
      into one rule since the spec asks for one body/subtext treatment
      and they'd previously only differed by a point or two of size and
      which faint ink token they used; that visual distinction is now
      gone by design, not by omission.
    - **Scripture & verse text** (`--font-display`, `text-base`
      generally, `text-xl` for hero/standalone quotes,
      `line-height:1.45`, `--text-primary`): applied to `.verse-card
      .text` (used by compact verse-list cards and Browse's per-verse
      chapter-reading cards — stays at `text-base`) and `.practice-verse`
      (the fill-in-blank challenge's verse display). Verse Detail's own
      standalone quote (an inline `style=` override on `.verse-card
      .text`) was bumped from a hardcoded `20px` to `var(--text-xl)`,
      since that's this app's one "hero/standalone quote" context for
      this class. **Notable, and flagged rather than done silently:**
      this reopens Fraunces beyond the VOTD-only scoping item 82
      explicitly called out ("nothing else references the family") —
      now `.verse-card .text` and `.practice-verse` both use
      `--font-display` too, on the owner's explicit instruction this
      time, covering Home, Verse Detail, and Practice cards as asked.
      `.votd-text` itself moved from a hardcoded `21px` to the exact
      `text-xl` (22px) token.
    - **Screen headings & greetings** (`text-2xl`/700/`--text-primary`):
      the global `h1` rule now reads `var(--text-2xl)` (28px, up from
      26px) — covers "Browse," "Topics," "Study," and every other plain
      `<h1>` screen title for free. `.home-greet` ("Good afternoon")
      updated to match exactly rather than keeping its own smaller
      20px value, so the greeting now reads at the same size as a
      screen title.
    - **Bottom nav & CTA buttons**: `.navbar .navitem span` (tab labels)
      moved from `10.5px` to `text-xs` (12px). `.btn.primary` (used
      everywhere a real primary action button appears — "Practice this
      verse," Practice landing's start button, etc.) gained explicit
      `text-base`/600, up from the shared `.btn` base's smaller 14px/500
      — secondary/ghost/utility buttons (Export, Import, Add, etc.) keep
      the unchanged base size, only primary CTAs got bigger. The two
      non-`.btn` custom CTA pills the spec named directly —
      `.votd-action` ("Read chapter") and `.practice-nudge` ("Practice N
      of M due verses") — were updated to the same `text-base`/600 pair
      individually, since neither uses the shared `.btn` class.
    - `sw.js` bumped to `rooted-v81`.

86. **Gospel/Acts content-audit gap-fill — done (2026-09-14).** An owner
    content audit found well-known Gospel and Acts episodes whose verse
    text already existed in `data/verses.json` but had never been
    selected into a Story: 20 new stories, 7 new characters, 54 new
    curated verses, 1 new topic (`topic_generosity`), 1 new connection,
    across `era_jesus_ministry`, `era_passion_and_resurrection`, and
    `era_early_church` — no new eras needed. Highest priority, per the
    owner's own framing: John 21's breakfast on the shore and Peter's
    threefold restoration (`story_breakfast_on_the_shore`), tagging both
    `char_jesus` and `char_peter` with matching new life events.
    - **Individual Gospel healings/encounters**: the Gerasene demoniac /
      "Legion" (`story_gerasene_demoniac`), the pool of Bethesda
      (`story_pool_of_bethesda`), the ten lepers (`story_ten_lepers_one_returns`,
      the one who returns — a Samaritan — getting the thanksgiving-topic
      tag), the Syrophoenician/Canaanite woman's daughter
      (`story_syrophoenician_womans_daughter`), and Mary and Martha
      (`story_mary_and_martha` — both sisters already existed as
      characters from the raising-of-Lazarus curation, so this reused
      `char_martha`/`char_mary_of_bethany` rather than inventing new
      ones, adding one new life event to each at `sequenceInLife: 5`,
      *before* their existing Lazarus-story event, since Luke situates
      this visit well before Lazarus's death).
    - **Feeding the four thousand** (`story_feeding_the_4000`) — curated
      as genuinely distinct from the already-curated feeding of the five
      thousand, per the owner's own instruction not to force a
      Connection between them where none is asked for; none was added.
    - **The widow's offering** (`story_widows_offering`) — needed a new
      topic, `topic_generosity` (related to `topic_love`/
      `topic_faithfulness`), since none of the existing 38 fit a story
      about sacrificial giving specifically.
    - **The death of John the Baptist** (`story_death_of_john_the_baptist`)
      — two new characters, `char_herod_antipas` and `char_herodias`
      (his wife, previously his brother's), connected by a new
      `"husband of"`/`"wife of"` Connection (a real stated fact:
      "Herodias, his brother Philip's wife, for he had married her").
      Herodias's dancing daughter is unnamed in the WEB text (tradition
      calls her Salome, but the Bible doesn't), so per this project's
      standing rule she gets no Character record. Placed in
      `era_jesus_ministry` — `char_john_the_baptist`'s `eraId` was
      already `era_jesus_ministry` (checked before curating, per the
      task's own instruction), so no era move was needed. `char_jesus`
      is *not* tagged on this story — he isn't present in the scene
      (Herod's banquet), and the "tag every major character actually
      present" lesson (item 69/DATA_MODEL §8 lessons) cuts both ways:
      don't undertag a present character, but don't force-tag an absent
      one either.
    - **Temple cleansing — judgment call, curated as two distinct
      events, not one.** John 2:13-22 places Jesus's cleansing of the
      temple at the very start of his ministry (right after the Cana
      wedding); Matthew 21:12-13/Mark 11:15-17/Luke 19:45-46 place a
      cleansing during the temple's *final* week before the
      crucifixion, the day after the triumphal entry, as the direct
      provocation that hardens the chief priests against him. Unlike
      the feeding of the five thousand (one event, four Gospels, same
      point in the timeline) or Isaiah 36-39/2 Kings 18-20 (the same
      retold event, extended not cloned), these two accounts sit at
      opposite ends of Jesus's ministry with no textual signal either
      Gospel writer meant the other's moment — so this is judged a
      genuine repeated action (cleansing a temple that had drifted back
      into commerce, twice, years apart), not one event told twice.
      Curated as `story_temple_cleansing_early` (`era_jesus_ministry`,
      right after `story_water_to_wine`) and
      `story_temple_cleansing_passion_week` (`era_passion_and_resurrection`,
      right after `story_triumphal_entry`), both tagged `topic_holiness`.
    - **Five more parables as Stories**, matching the `prodigal_son`/
      `good_samaritan` precedent: the lost sheep and lost coin
      (`story_lost_sheep_and_coin` — one Story for both, since Luke
      tells them back to back as one discourse), the rich man and
      Lazarus (`story_rich_man_and_lazarus` — this parable's Lazarus is
      a different, fictional figure from the real `char_lazarus` of
      Bethany despite the shared name; no Character record for either
      him or the rich man, matching this project's standing rule that
      fictional parable figures never get Character records), the
      talents, the ten virgins, and the sheep and the goats (all three
      Matthew 25 parables placed in `era_passion_and_resurrection`, not
      `era_jesus_ministry` — Matthew 25 is the Olivet Discourse,
      delivered on the Tuesday of Passion week, so all three slot
      between `story_widows_offering` and `story_last_supper`
      chronologically, not with the rest of Jesus's parables).
    - **Acts**: Dorcas/Tabitha raised by Peter (`story_tabitha_raised`,
      new character `char_tabitha`, new `char_peter` life event at
      `sequenceInLife: 115` — placed *before* his existing
      Cornelius-vision event at 120, since Acts 9 precedes Acts 10); the
      Ephesus riot (`story_ephesus_riot`, new character
      `char_demetrius`, `char_paul` tagged with a matching new life
      event per the item-69 lesson since the riot is directly provoked
      by his preaching); Paul's farewell to the Ephesian elders
      (`story_pauls_farewell_to_ephesian_elders`).
    - **Paul's trials — real gap found and fixed.** `story_pauls_arrest`
      previously compressed Paul's arrest *and* his years of trials
      before Felix, Festus, and Agrippa into one story citing
      `Acts 21:27-26:32` with only 5 verses — exactly the compression
      the task asked to check for. Split into two: `story_pauls_arrest`
      now scopes to the arrest and Sanhedrin hearing only
      (`Acts 21:27-23:35`), and a new `story_pauls_trials`
      (`Acts 24:1-26:32`) covers the trials themselves, with three new
      characters (`char_felix`, `char_festus`, `char_agrippa`) all
      tagged alongside `char_paul`. `verse_acts_26_29` (Paul's "I wish
      you were as I am, chains excepted") moved from the old
      `story_pauls_arrest` to the new `story_pauls_trials`, where it
      actually belongs.
    - No new eras. `sw.js` bumped to `rooted-v82`.

87. **Search on the Stories screen.** **Done (2026-09-14).** Now that
    Stories numbers over 200 across 16 eras, finding one by scrolling
    era-by-era was the same problem People and Topics had already
    solved. Mirrors that exact pattern rather than inventing a new one:
    `storiesQuery` state, its own `#stories-results` subtree,
    `renderStoriesResults()` split out of `renderStories()` (era-grouped
    browse view when the query is empty, a flat match list when it
    isn't), a `#stories-search` input wired the same debounced way
    (`refreshStoriesResults()`, 140ms, `bindEvents()` re-run on the
    result subtree only — not a full `render()`). Matches on title,
    `primaryReference`, or `summary` (case-insensitive substring) — the
    three fields a title/reference/blurb search reasonably covers;
    People's search matches name/role and Topics matches name, so this
    keeps the same "match what's visibly on the card" principle. No new
    CSS — `.search-wrap`, `.result-count`, `.empty` were all already
    shared components. `sw.js` bumped to `rooted-v83`.

88. **Second content-gap audit, batch fill — done (2026-09-15).** A
    second owner audit (the first, item 86, filled Gospel/Acts gaps)
    found more real, verified gaps — checked directly against
    `data/stories.json`/`data/verses.json` before curating, not
    guessed. 9 new stories, 6 new characters, 47 new curated verses,
    5 new connections, across `era_creation`, `era_flood`,
    `era_jesus_ministry`, and `era_early_church` — no new eras, no new
    topics (all fit the existing 39).
    - **Genesis, `era_flood`**: the Tower of Babel
      (`story_tower_of_babel`, Genesis 11:1-9) had zero coverage
      despite being one of Genesis's most iconic episodes — no named
      individuals in the text, so `characterIds: []`, matching
      `story_creation`'s precedent for a story with no named actor.
      Noah's drunkenness and the curse of Canaan
      (`story_noahs_drunkenness_and_canaans_curse`, Genesis 9:18-27)
      needed four new characters — Ham, Shem, Japheth, Canaan — since
      none of Noah's sons had Character records yet; each is
      individually addressed in Noah's own blessing/curse, the same
      bar Jacob's twelve sons cleared in item 70. `era_flood`'s own
      summary was stale in exactly the way the pipeline README warns
      about (`build_stories.py`'s lesson list) — it only described the
      flood itself, not this aftermath material now folded into the
      same era — so it was rewritten to cover both.
    - **Genesis, `era_creation` — Enoch, a real judgment call.**
      Genesis 5:21-24 ("Enoch walked with God... he was not found, for
      God took him") is four verses of genealogy-formula text with no
      scene, dialogue, or action to build a Story around — unlike
      Melchizedek (`story_melchizedek_blesses_abram`), which kept its
      Story despite similarly few verses because it's a real scene
      (Abram meets him, receives a blessing, pays a tithe). Decided:
      no Story record, matching the Leviticus/Deuteronomy precedent of
      verses-only treatment for non-narrative material — just two
      curated verses (5:22, 5:24) and a new `char_enoch`
      (`era_creation`) with one life event.
    - **`era_jesus_ministry` — four more Gospel episodes**, extending
      the existing prodigal-son/good-samaritan/lost-sheep-and-coin/
      rich-man-and-lazarus/talents/ten-virgins/sheep-and-goats parable
      precedent: the unforgiving servant (`story_unforgiving_servant`,
      Matthew 18:21-35, tagging `char_peter` for the question that
      prompts it), the Pharisee and the tax collector
      (`story_pharisee_and_tax_collector`, Luke 18:9-14), and the
      workers in the vineyard (`story_workers_in_the_vineyard`,
      Matthew 20:1-16) — all fictional-parable-figures-get-no-Character
      -record, per the standing rule. Jesus blessing the little
      children (`story_jesus_blesses_the_children`, Mark 10:13-16) is
      real narrative, not a parable, and got its own `char_jesus` life
      event placed right before his existing rich-young-ruler event,
      matching Mark's own sequence (10:13-16 immediately precedes
      10:17-31).
    - **`era_early_church` — a real, verified compression gap.**
      `story_pauls_first_missionary_journey` cites Acts 13:1-14:28 as
      its `primaryReference` but carried only 2 curated verses — a
      broad summary, not real coverage of Paul and Barnabas mistaken
      for gods and Paul's stoning at Lystra (Acts 14:8-20). Added
      alongside it, not in place of it, as its own properly-scoped
      `story_stoning_at_lystra`, with matching new life events for
      `char_paul` and `char_barnabas` — the same "extend the family,
      don't shrink the summary" move as `story_pauls_trials` beside
      `story_pauls_arrest` in item 86.
    - **The choosing of the seven** (`story_choosing_the_seven`,
      Acts 6:1-6) — a judgment call on Acts 6:5's five other named men
      (Prochorus, Nicanor, Timon, Parmenas, Nicolaus), weighed against
      Zelophehad's five daughters (item 71), who *did* each get
      Character records. The daughters individually petition Moses and
      change inheritance law by name, referenced again later in
      Joshua; these five are named once in a list and never act or
      speak individually anywhere else in the text — narrative
      importance, not a mention-count threshold, is the stated bar
      (CLAUDE.md item 10), and this group doesn't clear it the way the
      daughters did. Decided: only `char_stephen` and
      `char_philip_evangelist` (both already existed) get a new life
      event on this story, at `sequenceInLife: 5` — before their
      existing events — since the choosing precedes both their later
      ministries; the other five are named in the verse text only, no
      new Character records.
    - **The death of Herod Agrippa I** (`story_death_of_herod_agrippa`,
      Acts 12:20-23) — a new `char_herod_agrippa_i`, verified as a
      genuinely distinct person from the already-curated
      `char_herod_antipas` (item 86: killed John the Baptist).
      Agrippa I was Antipas's nephew, not the same man — he has James
      executed and imprisons Peter earlier in Acts 12, then is struck
      down after accepting a crowd's acclaim as a god. A new
      `"nephew of"`/`"uncle of"` connection links the two Herods
      explicitly, the same disambiguation pattern already used for the
      two Josephs and two Zechariahs (pipeline README lessons).
    - Five new connections total (three `"father of"` edges for Noah's
      sons, one `"father of"` for Ham/Canaan, one `"nephew of"` for the
      two Herods). No new motifs — nothing in this batch had a genuine
      second instance to pair with. `sw.js` bumped to `rooted-v84`.
89. **Third content-gap audit, batch fill — done (2026-09-15).** A third
    owner audit (items 86 and 88 were the first two) — again, real gaps
    confirmed against `data/stories.json`/`data/verses.json` before
    curating, not guessed. 11 new stories, zero new characters, 63 new
    curated verses, 4 new life events, across `era_jesus_ministry`,
    `era_passion_and_resurrection`, `era_divided_kingdom`, and
    `era_judges` — no new eras, no new characters, no new topics (all
    fit the existing 39). Zero new characters is itself notable — every
    gap in this batch turned out to involve either unnamed figures (the
    standing rule: only real, named/identifiable people get Character
    records) or people already curated.
    - **`era_jesus_ministry` — six more Gospel episodes.** The woman
      caught in adultery (`story_woman_caught_in_adultery`, John 8:1-11
      — "he who is without sin among you, let him throw the first stone
      at her") and Jesus rejected at his hometown synagogue in Nazareth
      (`story_jesus_rejected_at_nazareth`, Luke 4:16-30 — "no prophet is
      acceptable in his hometown," the crowd tries to throw him off a
      cliff) each tag only `char_jesus`; no one else in either text is
      named. The sending of the twelve (`story_jesus_sends_out_the_twelve`,
      Matthew 10:1-15; Mark 6:7-13; Luke 9:1-6) and the sending of the
      seventy-two (`story_jesus_sends_out_the_seventy_two`, Luke 10:1-24
      — "the harvest is plentiful," "I saw Satan fall like lightning")
      are both Jesus's own action, not any individual disciple's, so
      neither gets a life event on anyone but him — considered tagging
      the already-curated apostles named in Matthew 10:2-4 (Peter,
      Andrew, Thomas, Matthew, Judas Iscariot all exist as characters)
      but decided against it, since the text doesn't show them doing
      anything individually here. The persistent widow and the unjust
      judge (`story_persistent_widow_and_unjust_judge`, Luke 18:1-8)
      is a parable, so `char_jesus` only, same as every other parable
      story.
    - **The wedding banquet: two distinct parables, not one told twice.**
      Matthew 22:1-14 and Luke 14:15-24 share a surface shape (a host,
      refused invitations, a servant sent to gather replacement guests)
      but diverge enough to be genuinely separate stories: Matthew's has
      a king, armies destroying the murderers of his servants and
      burning their city, and a second scene where a guest without
      wedding clothes is bound and thrown into the outer darkness —
      none of which Luke's simpler dinner-party parable has at all.
      Matthew's is also textually and thematically Passion week material
      (delivered in the temple right after the temple cleansing, in the
      same judgment register as the parables that follow it), while
      Luke's is spoken at a Pharisee's table mid-ministry. Curated as
      two Stories in two different eras:
      `story_parable_of_the_wedding_banquet` (Matthew 22:1-14) sits in
      `era_passion_and_resurrection`, right after
      `story_temple_cleansing_passion_week` and before `story_ten_virgins`
      — the same Matthew 21-25 stretch of judgment parables;
      `story_parable_of_the_great_feast` (Luke 14:15-24) sits in
      `era_jesus_ministry`, in the same journey-to-Jerusalem stretch as
      `story_lost_sheep_and_coin` and `story_prodigal_son`. Both tag
      only `char_jesus`.
    - **Numbers, `era_exodus` — Aaron's rod buds folded into the existing
      Korah story, not cloned.** Numbers 17:1-11 is Yahweh's direct
      response to the people's continued grumbling after the ground
      swallowed Korah days earlier — same scene's aftermath, not a new
      incident — so it extends `story_korahs_rebellion` rather than
      getting its own Story, the same "extend, don't clone" call as
      Isaiah 36-39/2 Kings 18-20 and the Chronicles material. Its
      `primaryReference` grew to `"Numbers 16:1-35; 17:1-11"`, its
      summary now covers both, and it picked up 3 more verses. New life
      events for `char_aaron` (`event_aaron_rod_buds`, sequence 105,
      between his existing confronting-Korah event at 100 and being
      barred from Canaan at 110) and `char_moses`
      (`event_moses_aaron_rod_buds`, sequence 225, right after his own
      confronting-Korah event at 220).
    - **2 Kings 6 — the floating ax head is the real gap, the blinded
      army already wasn't.** The task brief named "the floating ax head
      and the blinded Aramean army at Dothan (2 Kings 6:1-23)" as one
      chapter-sized gap, but checking `data/stories.json` first showed
      `story_elisha_and_the_blinded_army` (2 Kings 6:8-23) already
      existed — only 6:1-7, the ax head, was actually missing. That also
      settles the one-vs-two-stories question: 2 Kings 4's widow's-oil
      and Shunammite's-son miracles, textually just as adjacent, were
      already curated as two separate Stories
      (`story_elisha_and_the_widows_oil`, `story_elisha_and_the_shunammite`),
      so the new `story_elishas_floating_axe_head` follows that same
      precedent rather than merging into the existing blinded-army
      story. `char_elisha` gets one new life event
      (`event_elisha_floats_axe_head`, sequence 45, between Naaman
      healed at 40 and the blinded army at 50); the prophet who loses
      the ax head is unnamed in the text, so no new Character.
    - **Judges 19-21 — the Levite's concubine and the war against
      Benjamin, curated directly, not softened.** Confirmed genuinely
      uncovered (`data/stories.json` had nothing past Samson), and the
      owner explicitly confirmed this dark material belongs in the app
      rather than being skipped. Split into three Stories at the text's
      own scene breaks, matching how multi-chapter arcs like Absalom's
      rebellion and Esther were split rather than compressed into one:
      `story_levites_concubine` (Judges 19 — the assault at Gibeah and
      the dismembered body sent through Israel's territory),
      `story_war_against_benjamin` (Judges 20 — the war itself, Israel's
      two early defeats, and the near-destruction of the tribe), and
      `story_wives_for_benjamin` (Judges 21 — Jabesh Gilead's daughters
      and the abduction at the Shiloh festival, closing on the book's own
      thesis line, "everyone did that which was right in his own eyes").
      Verse *text* is exactly the WEB translation throughout, unedited —
      only verse *selection* (always a curated choice, same as every
      other story) narrowed around the single most graphic sentence in
      chapter 19 (the description of the assault itself, v25) while
      still keeping the verses on either side of it (the mob's demand,
      v22; finding her at the door, v28; the dismemberment, v29) that
      make what happened unambiguous without lingering on it. No new
      Character records: every participant in all three chapters is
      unnamed ("a certain Levite," "his concubine," "the men of
      Gibeah," Jabesh Gilead, the daughters of Shiloh) — verified
      directly against the text, not assumed, since named participants
      have cleared a much lower bar than this in past passes (e.g.
      Zelophehad's daughters, item 71). One existing character does
      belong on the war story, though, caught by the same discipline as
      items 66-67's "tag the major character too" lesson: `char_phinehas`
      (introduced item 71, era_exodus) is the one who stands before the
      ark and inquires of Yahweh at Judges 20:27-28, so he's tagged with
      a new life event (`event_phinehas_war_against_benjamin`, sequence
      30) even though his own `eraId` stays in the Exodus period where
      his arc is centered. `era_judges`'s summary was also reread and
      extended per the pipeline README's stale-era-text lesson — it
      only described the deliverer cycle, not the book's own grim
      closing coda.
    - No new motifs or connections — nothing in this batch paired with a
      genuine second instance, and no new family/relationship facts were
      introduced. `sw.js` bumped to `rooted-v85`.

90. **Two new Home cards: Word of the Day (Hebrew/Greek) and This Day in
    Church History.** **Done (2026-09-15).** Both are new, small, static
    reference datasets — not derived from the existing Bible-content
    pipeline (`pipeline/curation/*.json` → `build_*.py`), since neither
    is Bible *text* curation; they're separate editorial content in the
    same spirit as Verse/Unreached/Story of the Day.
    - **`data/word_of_the_day.json`** — a flat array of 13 entries
      (`id`, `word` the original Hebrew/Greek script, `transliteration`,
      `language`, `strongs` id, `meaning`, `summary`, `verseIds`), hand-
      picked to cover the terms named directly in the request (Hesed,
      Shalom, Agape, Logos, Pneuma, Eirene, Koinonia, Halal, Ruach,
      Charis) plus three more (Emet, Tov, Chara) for a rounder set.
      Every `verseIds` entry was checked against the actual seed library
      (`data/starter-pack.json`) before being written in, so every word
      genuinely has at least one real, already-curated verse it can link
      to — no placeholder or invented references.
    - **`data/church_history.json`** — an object keyed by local `MM-DD`
      (`year`, `title`, `category`, `description`, `takeaway`, plus a
      `"default"` fallback entry for any date without a specific match).
      13 dated entries. Every date was verified via web search before
      being written in, not recalled from memory alone — an educational
      "on this day" feature presenting wrong dates as fact would be a
      real quality problem, not just a cosmetic one. One real collision
      surfaced during that research: both Dietrich Bonhoeffer's execution
      and the start of the Azusa Street Revival are April 9, in different
      years (1945 and 1906) — since this schema is one entry per `MM-DD`
      (not an array), Bonhoeffer was kept and Azusa Street dropped from
      this seed round rather than force a collision; either the schema
      would need to become date→array, or Azusa Street would need a
      different anchor date, if it's added later.
    - **Loading**: `loadWordOfTheDayData()`/`loadChurchHistoryData()`
      follow the exact `loadMotifs()`/`loadConnections()` shape — fetch
      at boot, fail-quiet to an empty array/object on any error, so a
      missing or broken file just means the card doesn't render rather
      than a broken boot. Both awaited in `boot()` alongside the other
      seed-data loaders, before the first `render()`.
    - **`wordOfTheDay()`** and **`churchHistoryToday()`**: the word pick
      is date-seeded the same way as `verseOfTheDay()`/`storyOfTheDay()`
      (a rotating index into the array — which specific word shows
      depends only on the calendar date, not which entries exist, so
      adding more words later shifts the rotation but never breaks it).
      Church History is different on purpose — it's a *lookup* keyed by
      today's actual `MM-DD`, not a rotating index, since there's exactly
      one right answer for "what happened on this date" rather than any
      valid rotation through a list.
    - **`renderWordOfTheDayCard()`**: the Hebrew/Greek script renders at
      an explicit `24px` (`.word-script`) — the one place in this pass
      that doesn't map onto the existing `--text-xs` through `--text-2xl`
      scale (item 85), since the request was specific about this exact
      size and it genuinely sits between `--text-xl` (22px) and
      `--text-2xl` (28px). Everything else on both new cards *does* use
      the existing type-scale tokens and the existing `.word-eyebrow`/
      eyebrow pattern from `.votd-label`/`.discovery-label` — a new class
      only because Word of the Day and Church History share it with each
      other, not because it needed different values.
    - **Card surface — one deliberate deviation from the literal spec,
      matching the reasoning already established in item 85**: the
      request specified `#1C1917` for the card background and literal
      `#FFFFFF`/`#B8AEA5` for text. Used `var(--paper-raised)` (`#18191D`)
      and the existing `--text-primary`/`--text-secondary` tokens instead
      — `#1C1917` is close enough to the existing card token that using
      it literally would have put two very slightly different "dark
      card" shades on the same Home feed, which reads as a bug, not a
      design choice. Padding was bumped to the requested `20px`
      specifically on these two cards (`.word-card,.church-history-card`)
      since the shared `.card` base still defaults to `16px` everywhere
      else and there was no reason to change that globally for this.
    - **Church History's "bottom modal sheet" → a full detail screen
      instead, another deliberate deviation.** This app has zero modal/
      overlay components anywhere — every other "see more" interaction
      (Unreached of the Day's detail page being the closest precedent)
      is a full screen reached via `go()`, with a back button, that
      participates in scroll-position restoration and the same back-nav
      conventions as everything else. Building a first bottom-sheet
      primitive for one card would add a whole new UI paradigm (backdrop,
      dismiss gesture, z-index/safe-area handling) nothing else in the
      app uses, for a single use site. `renderChurchHistoryDetail()`
      matches `renderUnreachedDetail()`'s shape instead: `go-home` back
      button, full description, and the `takeaway` field rendered as a
      distinct callout (`.church-history-takeaway`) below a divider.
    - `sw.js`'s precache list gained both new JSON files (Home reads one
      of each on every visit, same reasoning as the two placeholder
      photos already there). Bumped to `rooted-v86`.

91. **Real generated character portraits — a first batch of 25, wired
    into the app.** **Done (2026-09-15).** `pipeline/generate_character_art.py`
    (built earlier as a `--test`-only validation tool, `--batch` never
    implemented) generated a real, deliberately non-photorealistic
    stylized-3D-animation portrait for 25 major characters, each with a
    real story-appropriate background setting (Moses on Sinai, Daniel
    among the lions, Esther in the Persian court, etc.) rather than a
    blank atmospheric wash. Two art-direction corrections came from
    direct feedback after the first pass: Samson initially read as
    weary/weak rather than mighty, and Samuel — whose `roles` field
    literally opens with "heard God's voice as a boy" — kept generating
    as a child despite being popularly known as an elder prophet who
    anointed two kings. Both fixed with a new `description` override
    mechanism in `build_prompt()`/`character_art_settings.json` (an
    entry can now be a plain setting string, or `{"setting":...,
    "description":...}` when the character's own `roles` text would
    otherwise mislead the model) — layered in ADDITION to the real
    `Character.roles` data, never by editing that data itself, since
    `roles` is real app-facing content shown elsewhere, not just an art
    prompt input. Samson's fix also added explicit physicality cues
    (broad-shouldered, muscular, straining against the cracking pillars)
    since the base style prompt never specified build at all.
    - **Wiring, a deliberate shortcut instead of the full `Media` entity**
      (design philosophy #3: a separate linked entity, multiple images
      per character, etc.): `data/character_portraits.json` is just a
      flat array of the 25 character ids that have a real photo at
      `media/characters/<id>.jpg` — no Media records, no `mediaIds` on
      Character, no `build_media.py`. For a partial batch (25 of 261
      characters) this one manifest file plus a fallback check does the
      same job with far less machinery; the real `Media` entity is still
      exactly where it was in the design — real future work once/if
      portraits cover most of the cast, not attempted here.
    - **`charPortraitUrl(charId)`** checks the manifest (loaded into a
      `Set`, `characterPortraits`) and returns the image path or `null`.
      **`charAvatarInner(c)`** is the small-avatar swap — an `<img>` when
      a portrait exists, the existing `charIcon()` icon otherwise — used
      everywhere a character shows up as a small avatar: `renderCharacterRow()`
      (People/Study lists, "People in this book," Appears-alongside,
      Also-in-era), the Family rows and the Verse Detail "People" rows on
      Character Detail (both previously inlined their own icon markup,
      now call the shared helper instead of duplicating the swap logic a
      third time).
    - **Character Detail's hero** is the "full image" the owner asked
      for: `charPortraitUrl()` decides between the old small
      `.hero-avatar` icon-in-a-box (unchanged, still what every other
      character without a portrait yet shows) and a new full-width
      `.hero-photo` — rendered *above* the `.hero` card, not squeezed
      inside its centered-text padding, matching the same "full-bleed
      image above the info card" shape `.unreached-full-photo` already
      established rather than inventing a second treatment.
    - Portraits are **not** added to `sw.js`'s precache list — same
      reasoning as `data/verses.json` staying lazy: only one character's
      photo loads per visit to their page, not all 25 on every visit, so
      precaching the whole batch at install would be pure waste. The
      existing runtime fetch-cache picks each one up after its first
      view, same as any other asset. `sw.js` bumped to `rooted-v87`.
    - Source images (1024×1024, ~700-800KB each straight from Gemini)
      were resized to 640×640 and re-compressed before committing —
      18.4MB across 25 files down to 1.6MB, the same "optimize before
      committing" step already established for the Home placeholder
      photos (item 83).

92. **Second character-portrait batch — 25 more, 50 total (of 261).**
    **Done (2026-09-15), same day as item 91.** Same pipeline, same
    wiring (`data/character_portraits.json` just grew from 25 to 50
    ids; no code changes needed since item 91 already built the manifest
    + fallback approach generically). New characters: Sarah, Rachel,
    Leah, Miriam, Aaron, Joshua, Caleb, Rahab, Boaz, Saul, Goliath,
    Jonathan, Bathsheba, Absalom, Nathan, Elisha, Jeremiah, Ezekiel, Job,
    Nehemiah, Ezra, Mordecai, John the Baptist, Mary Magdalene, Lazarus —
    each with its own distinct signature setting in
    `character_art_settings.json` (Miriam at the Red Sea shore with a
    timbrel, Goliath in the valley of Elah with both armies faced off,
    Absalom's hair caught in the branches mid-battle, Lazarus stepping
    from the tomb doorway in grave clothes, etc.), deliberately varied
    from batch 1's mix of settings (more rivers, battlefields, city
    gates, and a tomb garden this time, rather than repeating mostly
    mountains/temples/desert-night).
    - **One preemptive fix, not a correction after the fact:** Miriam's
      `roles` field opens with "watched over the basket" (young Miriam
      guarding baby Moses on the Nile, Exodus 2) — the same shape of
      issue that made Samuel render as a child in item 91. Caught before
      generating, not after: gave her a `description` override anchoring
      her instead to her adult, popularly-remembered role as the
      prophetess who led the women's celebration at the Red Sea (Exodus
      15), matching the batch's own timbrel-and-shoreline setting for
      her. No other character in this batch needed the override
      mechanism.
    - No new stylization corrections needed this round — the fixes from
      item 91 (explicit non-photorealistic stylization cues, the
      `description`-override mechanism) held up cleanly across all 25
      new generations on the first pass, including several older/
      weathered faces (Job, Jeremiah, Ezra) that would have been the
      likeliest candidates to drift toward photorealism the way Moses
      and Samson originally did.
    - `sw.js` bumped to `rooted-v88`.

93. **Expression direction by character arc, plus a third portrait batch
    (25 more, 75 total).** **Done (2026-09-15), same day as item 92.**
    Direct feedback: Paul's existing portrait (item 91, the Damascus-road
    setting) read flat/unhappy despite his arc ending in triumph
    ("I have fought the good fight"). Fixed the general problem, not
    just Paul's one image: `generate_character_art.py` now takes an
    explicit `expression` direction on every generation —
    `EXPRESSION_POSITIVE` (warm, genuinely joyful, an unmistakable
    smile), `EXPRESSION_NEGATIVE` (subtly stern/hardened — tension in
    the brow, dignified and human, explicitly NOT cartoonish or
    exaggerated villain-coded), or `EXPRESSION_NEUTRAL` (calm, composed,
    neither smiling nor stern) — a per-character judgment call recorded
    as a third optional field in `character_art_settings.json` entries
    (alongside `setting` and `description`), defaulting to neutral when
    omitted. The rule: a character whose own arc resolves well (faith
    rewarded, redemption, vindication) reads positive; a character
    defined by villainy or a story that indicts them reads negative;
    everyone else (including tragic-but-not-villainous figures like Saul
    or Absalom, from earlier batches) reads neutral. Paul was
    regenerated with `expression: positive` — same Damascus setting,
    now genuinely smiling — and the updated image replaces his existing
    `media/characters/char_paul.jpg` in place.
    - **Retroactive scope, decided deliberately, not by default:** the
      owner explicitly chose to apply this only going forward, not
      re-audit and regenerate the other 49 already-committed portraits.
      Most already happened to land reasonably (Job's suffering,
      Jeremiah's tears, Absalom's distress, Saul's troubled stare all
      already fit their arcs without needing the new mechanism) — this
      was a deliberate scope decision, not an oversight, and is worth
      knowing if a future pass ever wants to audit the earlier batches
      against the same rule.
    - **Batch 3 characters (25 new, chosen specifically to exercise all
      three expression values, not just positives):** positive —
      Abel, Naboth, Naaman, Hezekiah, Josiah, Nebuchadnezzar (his own
      arc ends in blessing the Most High, Daniel 4:34), Cyrus,
      Zerubbabel, Barnabas, Stephen. Negative — Cain, Laban, Pharaoh (of
      the Exodus), Balaam, Achan, Jezebel, Ahab, Gehazi, Belshazzar,
      Ananias, Simon Magus, Judas Iscariot. Neutral — Esau, Eli, Pilate.
      Each also got its own distinct signature setting in
      `character_art_settings.json` (Belshazzar's literal "MENE, TEKEL,
      UPHARSIN" rendered glowing on the banquet-hall wall behind him;
      Achan with the buried plunder visible at his feet; Ananias and
      Simon Magus both visibly holding money, the detail that defines
      each of their stories).
    - No new stylization drift this round either — the same
      non-photorealistic cues from item 91 held up across another 25
      generations, this time deliberately including several
      older/weathered faces (Eli, Laban, Nebuchadnezzar) that would have
      been likely photorealism candidates.
    - `sw.js` bumped to `rooted-v89`.

94. **Fourth character-portrait batch — 25 more, 100 total (of 267).**
    **Done (2026-09-15).** First batch of a long-haul push to cover the
    remaining supporting-cast characters from the "deep study" curation
    (item 10) that only got real content, never portraits. New
    characters, all from `era_patriarchs`/`era_exodus`/`era_judges`/
    `era_united_kingdom`: Hagar, Lot, Ishmael, Jochebed, Pharaoh's
    daughter, Zipporah, Naomi, Elimelech, Orpah, Nadab, Abihu, Korah,
    Eleazar, Ehud, Barak, Sisera, Jael, Jephthah, Jephthah's daughter,
    Delilah, Hannah, Michal, Uriah, Tamar (David's daughter), Amnon —
    each with a distinct, story-specific setting (Jochebed and Pharaoh's
    daughter both at the Nile but from opposite sides of the same scene;
    Jael at her own tent entrance with the tent peg and mallet in hand;
    Nadab and Abihu both before the tabernacle altar but in different
    framings so the pair doesn't look duplicated; Delilah with the
    shears visible on a table; Uriah in a rain-soaked war camp). No
    `description`-override fixes were needed this batch — every
    `roles` phrase for these 25 either already matched their defining-
    story age or didn't carry an age signal at all, unlike Samuel/
    Miriam/Josiah's origin-story phrasing in earlier batches. Expression
    calls: positive — Jochebed, Pharaoh's daughter, Naomi, Eleazar,
    Ehud, Barak, Jael, Hannah; negative — Nadab, Abihu, Korah, Sisera,
    Delilah, Amnon; neutral — Hagar, Lot, Ishmael, Zipporah, Elimelech,
    Orpah, Jephthah, Jephthah's daughter, Michal, Uriah, Tamar. No
    stylization drift on any of the 25 — the non-photorealistic cues
    from item 91 held up cleanly again, including on several
    older/weathered faces (Elimelech, Korah). `sw.js` bumped to
    `rooted-v90`.

95. **Fifth character-portrait batch — 25 more, 125 total (of 267).**
    **Done (2026-09-15).** `era_united_kingdom`, `era_divided_kingdom`,
    `era_return_from_exile`, and `era_esther` supporting cast:
    Mephibosheth, Joab, Adonijah, the queen of Sheba, Rehoboam,
    Jeroboam, the widow of Zarephath, the Shunammite woman, Jehu,
    Sennacherib, Huldah, Zedekiah, Abijah, Asa, Jehoshaphat, Joash,
    Jehoiada, Zechariah son of Jehoiada, Uzziah, Manasseh, Jeshua (the
    high priest), Sanballat, Haman, Ahasuerus, Vashti.
    - **One `description`-override fix, same pattern as Josiah:**
      Joash's `roles` field opens with "the boy king who restored the
      temple" — but the temple restoration itself happened in his 23rd
      regnal year (2 Kings 12:6), and the priest's-son killing later
      still, both well into adulthood. Caught before generating: gave
      him a description anchoring him as "king of Judah for forty
      years, in the mature middle years of his reign... a grown adult
      man, not a boy or child, despite having been crowned as a child."
    - **Two retries, different causes:** the queen of Sheba's first
      prompt (mentioning "gold" among her caravan's cargo) was rejected
      outright by Gemini's content filter (HTTP 400, "prohibited
      content guidelines") — reworded to "ornate chests" and it
      generated cleanly on retry, no visual problem, a request-blocked
      case rather than a bad-image case. Sennacherib's first generation
      came back in a flatter, more graphic-novel/vector-shaded style
      than the rounded 3D look every other portrait has — not
      photorealism drift (the opposite direction on the same axis the
      style prompt guards against) — a plain retry with the identical
      prompt produced the correct rounded 3D-animation look on the
      first attempt.
    - Expression calls: positive — Mephibosheth, the queen of Sheba,
      the widow of Zarephath, the Shunammite woman, Huldah, Abijah,
      Jehoshaphat, Jehoiada, Zechariah (Jehoiada's son), Manasseh,
      Jeshua; negative — Joab, Adonijah, Rehoboam, Jeroboam,
      Sennacherib, Joash, Uzziah, Sanballat, Haman; neutral — Jehu,
      Zedekiah, Asa, Ahasuerus, Vashti. `sw.js` bumped to `rooted-v91`.

96. **Sixth character-portrait batch — 25 more, 150 total (of 267).**
    **Done (2026-09-15).** `era_exile`, `era_divided_kingdom`,
    `era_return_from_exile`, `era_birth_of_jesus`, and the first
    `era_jesus_ministry` characters (John's Gospel and the Twelve):
    Eliphaz, Baruch, Ebed-Melech, Gedaliah, Shadrach, Meshach, Abednego,
    Darius the Mede, Hosea, Gomer, Amos, Haggai, Zechariah (the
    prophet — distinct from the earlier-batch priest of the same name),
    Joseph (Mary's husband), Zacharias, Elizabeth, Andrew, James son of
    Zebedee, John (the apostle), Philip the apostle, Nathanael,
    Nicodemus, the Samaritan woman, Martha, Mary of Bethany. No
    `description`-override fixes needed — none of this batch's `roles`
    text carried an origin/youth framing that would mislead the model
    (Elizabeth's "unlikely pregnancy in old age" is itself the correct
    age cue, and rendered that way without prompting).
    - **One mid-batch network failure, not a content or style
      problem:** the first `--test` run died on Elizabeth with a raw
      `ConnectionResetError` (a dropped TCP connection mid-response,
      not an API error response) after successfully completing the
      first 14 characters. Simply re-ran `--test` for the remaining 11
      ids (Elizabeth onward); all completed cleanly on the retry with
      no prompt changes.
    - Shadrach, Meshach, and Abednego were deliberately given three
      different moments from the same furnace scene (calm before the
      open furnace mouth; walking out through the flames unsinged;
      standing firm before the golden image beforehand) so the three
      portraits read as distinct scenes rather than three near-
      duplicate images of the same pose.
    - Expression calls: positive — Baruch, Ebed-Melech, Shadrach,
      Meshach, Abednego, Darius the Mede, Hosea, Amos, Haggai,
      Zechariah the prophet, Joseph, Zacharias, Elizabeth, Andrew,
      James, John, Philip, Nathanael, Nicodemus, the Samaritan woman,
      Martha, Mary of Bethany; negative — Eliphaz; neutral — Gedaliah,
      Gomer. `sw.js` bumped to `rooted-v92`.

97. **Seventh character-portrait batch — 25 more, 175 total (of 267).**
    **Done (2026-09-15).** The rest of the Gospels' named supporting
    cast, the Passion/Resurrection cast, early Acts figures, and a
    cluster of `era_united_kingdom` civil-war/rebellion figures from
    the item 10 "deep study" pass that had never gotten portraits:
    Thomas, Zacchaeus, the rich young ruler, Caiaphas, Barabbas, Simon
    of Cyrene, the penitent thief, Joseph of Arimathea, Cleopas,
    Matthew, Matthias, Cornelius, Silas, the Philippian jailer, Abner,
    Asahel, Abishai, Ahithophel, Hushai, Ittai, Shimei, Amasa, Sheba,
    the wise woman of Abel, Priscilla. No `description`-override fixes
    needed and no stylization retries — all 25 passed visual QA on the
    first generation.
    - The penitent thief and Simon of Cyrene both needed care around
      the crucifixion setting (a cross, Golgotha) — handled the same
      tasteful, dignified way the existing `char_centurion_at_the_cross`
      and `char_judas_iscariot` entries already do, no new precedent
      needed.
    - Expression calls: positive — Thomas, Zacchaeus, Simon of Cyrene,
      the penitent thief, Joseph of Arimathea, Cleopas, Matthew,
      Matthias, Cornelius, Silas, the Philippian jailer, Hushai, Ittai,
      the wise woman of Abel, Priscilla; negative — Caiaphas,
      Ahithophel, Shimei, Sheba; neutral — the rich young ruler,
      Barabbas, Abner, Asahel, Abishai, Amasa. `sw.js` bumped to
      `rooted-v93`.

98. **Eighth character-portrait batch — 25 more, 200 total (of 267).**
    **Done (2026-09-15).** Paul's circle from Acts/the epistles, and
    Genesis's patriarchal-family supporting cast from the item 10 "deep
    study" pass: Aquila, Apollos, Lydia, John Mark, Timothy, Titus,
    Onesimus, Philemon, Demas, Reuben, Simeon, Levi, Judah, Benjamin,
    Bilhah, Zilpah, Dinah, Shechem, Tamar (Judah's daughter-in-law),
    Potiphar, Potiphar's wife, Abraham's servant, Pharaoh's cupbearer,
    Pharaoh's baker, Nabal. No `description`-override fixes needed. All
    25 passed visual QA on the first generation with one exception:
    Simeon and Levi's shared "gate of Shechem" scene, and Dinah's own
    portrait, both touch the Genesis 34 assault/massacre narrative
    directly in their `roles` text — handled with the same tasteful,
    non-graphic restraint the crucifixion-adjacent portraits (item 97)
    already established, no new content-safety issue.
    - Expression calls: positive — Aquila, Apollos, Lydia, John Mark,
      Timothy, Titus, Onesimus, Philemon, Judah, Benjamin, Tamar
      (Judah's daughter-in-law), Abraham's servant, Pharaoh's
      cupbearer; negative — Demas, Simeon, Levi, Shechem, Potiphar's
      wife, Nabal; neutral — Reuben, Bilhah, Zilpah, Dinah, Potiphar,
      Pharaoh's baker. `sw.js` bumped to `rooted-v94`.

99. **Ninth character-portrait batch — 25 more, 225 total (of 267).**
    **Done (2026-09-15).** Abigail (finalized from a prior session's
    generation and added to the manifest as this batch's first entry),
    the 1 Samuel/Exodus/Numbers "deep study" supporting cast (Doeg,
    Ahimelech, Abiathar, Achish, Jethro, Shiphrah, Puah, Phinehas, and
    Zelophehad's five individually-named daughters — Mahlah, Noah,
    Hoglah, Milcah, Tirzah), and the Gospels' personal healing/
    interaction supporting cast (Bartimaeus, Jairus, the woman with the
    issue of blood, the centurion of Capernaum, the widow of Nain,
    Malchus, the centurion at the cross, Simon the Pharisee, the
    forgiven woman, Joanna, Susanna) — all from the item 10 "deep
    study" pass, settings for this exact batch already written in a
    prior session before credits ran out. No `description`-override
    fixes needed. All 25 passed visual QA on the first generation,
    including Malchus (the severed-ear moment at the arrest) and the
    centurion at the cross, both handled with the same tasteful,
    non-graphic restraint established in items 97-98.
    - Expression calls: positive — Abiathar, Jethro, Shiphrah, Puah,
      Phinehas, all five daughters of Zelophehad, Bartimaeus, Jairus,
      the woman with the issue of blood, the centurion of Capernaum,
      the widow of Nain, the centurion at the cross, the forgiven
      woman, Joanna, Susanna; negative — Doeg; neutral — Ahimelech,
      Achish, Malchus, Simon the Pharisee. `sw.js` bumped to
      `rooted-v95`.

100. **Tenth character-portrait batch — 25 more, 250 total (of 267).**
    **Done (2026-09-15).** The remaining Gospels supporting cast (the
    man born blind, the paralytic lowered through the roof, Simon the
    leper), Job's other three friends and his wife (Bildad, Zophar,
    Elihu, Job's wife), the 1-2 Kings and Esther "deep study" cast
    (Obadiah, Micaiah, Hegai, Zeresh, Harbonah), the Acts "deep study"
    cast (Sapphira, Philip the evangelist, Rhoda, Eutychus), and a
    Genesis/Numbers/Judges cluster new to this batch (Melchizedek, the
    recurring Abimelech king of Gerar, Balak, Othniel, Shamgar, Gideon's
    son Abimelech, and the four "minor judges" Tola, Jair, Ibzan) — all
    from the item 10 "deep study" pass. Settings for this whole batch
    were newly written this session (none pre-existed), following the
    established pattern of one real, specific, story-appropriate
    setting per character; Bildad and Zophar reused the same ash-heap
    staging already established for Eliphaz (item 90) since all three
    are Job's argumentative friends in the same scene, while Elihu —
    whose own roles text already reads "a younger fourth speaker," an
    accurate description of his actual defining moment rather than a
    misleading youth/legacy mismatch — needed no override, unlike the
    Samuel/Miriam/Josiah/Joash pattern this project keeps watching for.
    No `description`-override fixes needed this batch. All 25 passed
    visual QA on the first generation.
    - Expression calls: positive — the man born blind, the paralytic
      lowered through the roof, Obadiah, Micaiah, Hegai, Philip the
      evangelist, Rhoda, Eutychus, Melchizedek, Othniel, Shamgar, Jair,
      Ibzan; negative — Bildad, Zophar, Job's wife, Zeresh, Sapphira,
      Balak, Gideon's son Abimelech; neutral — Simon the leper, Elihu,
      Harbonah, the king of Gerar Abimelech, Tola. `sw.js` bumped to
      `rooted-v96`.

101. **Eleventh (final) character-portrait batch — 17 more, 267 total
    (of 267). Full coverage reached.** **Done (2026-09-15).** The last
    of the "deep study" supporting cast plus a handful of characters
    that predate that whole effort: the two remaining minor judges
    (Elon, Abdon), Athaliah and Jehosheba from the 2 Kings usurpation
    story, Herod Antipas and Herodias from John the Baptist's death,
    the rest of the Acts "deep study" cast (Tabitha, Demetrius, Felix,
    Festus, Agrippa), Noah's three sons and Ham's son Canaan (Ham,
    Shem, Japheth, Canaan — never curated with the rest of the flood
    narrative's major cast), Enoch (Genesis's other pre-flood figure
    "taken" rather than dying), and Herod Agrippa I (Acts 12's
    persecuting king, distinct from both Herod Antipas above and the
    Agrippa of Paul's later hearing). Settings newly written this
    session — Enoch's called for real creative judgment, since his
    entire biblical record is two verses with no scene to stage;
    settled on a soft, radiant "path between earth and sky" visual for
    his defining "walked with God... then he was not, for God took
    him" moment rather than forcing a conventional backdrop. No
    `description`-override fixes needed. All 17 passed visual QA on
    the first generation.
    - Expression calls: positive — Abdon, Jehosheba, Tabitha, Shem,
      Japheth, Enoch; negative — Athaliah, Herod Antipas, Herodias,
      Demetrius, Felix, Ham, Herod Agrippa I; neutral — Elon, Festus,
      Agrippa, Canaan. `sw.js` bumped to `rooted-v97`.

    **With this, all 267 characters in the starter pack now have a
    real generated portrait** — `data/character_portraits.json` holds
    267 unique ids, every one with a matching file in
    `media/characters/`, verified by script at the end of this batch.
    See CLAUDE.md's known-gaps item 2 for the closing note on the
    manifest-vs-`Media`-entity tradeoff this now opens up.

102. **Character carousel arrows, and swipe-left-to-go-back everywhere
    (revised same day from an initial swipe-only version).** **Done
    (2026-09-15).** The first version made Character Detail's
    swipe-left mean "next character" instead of "back," overriding the
    app-wide swipe-back rule on that one screen. Direct feedback: that
    read as inconsistent (the same gesture meaning different things on
    different screens) and undiscoverable (nothing on screen hinted a
    character-to-character swipe existed at all — the owner described
    it as "blindly swiping and figuring out where to swipe"). Replaced
    same day with visible left/right arrow buttons for the carousel,
    which frees swipe-left to mean exactly one thing everywhere,
    including Character Detail: go back.
    - **`allCharactersOrdered()`** — every character, era by era in
      `lore.eras`' own order, then any without a matching era appended
      last — the exact same grouping `renderPeopleResults()` already
      shows on the Study tab's People list, so paging through the
      carousel matches the order a user would already expect from
      browsing that list. **`adjacentCharacter(id, dir)`** looks up the
      next (`dir=1`) or previous (`dir=-1`) character in that order,
      returning `null` at either end.
    - **`.hero-nav-prev`/`.hero-nav-next`** — two small circular buttons
      overlaid directly on the character's portrait (`.hero-photo-wrap`),
      left/right-center, frosted dark background so they read on any
      photo. Each just reuses the existing `open-character` action
      (`data-id` set to the adjacent character), so paging through the
      carousel is indistinguishable from tapping a character row
      anywhere else in the app — no new action, no new navigation
      concept. A button is omitted entirely (not just disabled) at
      either end of the ordered list, so there's never a dead arrow that
      taps to nothing. Because `open-character` sets `from: view` the
      same way it always has, the existing back button
      (`character-back`) naturally walks back through the carousel one
      character at a time if that's how the visitor arrived — a
      standard navigation-stack behavior, not special-cased.
    - **Swipe-left-to-go-back, now with no per-screen exception**:
      triggers whatever the currently-rendered screen's own back button
      does, found generically via the visible `.back-btn[data-action]`
      element and a real `.click()` on it — reuses every existing
      back-nav action (`verse-back`, `character-back`, `back-to-topics`,
      `back-to-characters`, `motif-back`, `back-to-browse-book`, etc.)
      with zero per-screen code, and does nothing on any screen with no
      back button (Home, any bottom-nav tab root). Wired once at script
      load via a single `pointerdown`/`pointerup` pair on `#app`
      (Pointer Events, not separate touch/mouse handlers — same choice
      `wireTimelineDrag()` already made): a swipe is a leftward gesture
      of at least 60px, more horizontal than vertical, completed within
      800ms — a tap, a scroll, or a rightward swipe never qualifies. No
      live drag visual is rendered; only the net displacement between
      pointerdown and pointerup is read.
    - `sw.js` bumped to `rooted-v99`.

103. **Two real bugs in item 102, caught by direct device testing.**
    **Done (2026-09-15), same day.**
    - **The top-left back button was going to the previous carousel
      character instead of the true entry point (Study/People).** Cause:
      `.hero-nav-prev`/`.hero-nav-next` reused the existing
      `open-character` action, which sets `from: view` — meaning each
      arrow tap made "the character page just left" the new back target,
      so tapping through several characters via the arrows and then
      hitting the real back button just walked backward through that
      chain one character at a time, never reaching Study. Fixed with a
      new `char-carousel-nav` action that instead carries the ORIGINAL
      `from` forward unchanged (`from: view.params.from`) on every
      carousel hop — the back button now always returns to wherever the
      visitor actually entered the carousel, no matter how many
      characters they paged through first.
    - **Swipe-left-to-go-back wasn't registering on a real device at
      all.** Two contributing causes, both fixed:
      1. `.app` had no `touch-action` set, so mobile browsers were free
         to decide a horizontal drag belonged to native scrolling and
         send `pointercancel` instead of `pointerup` — silently
         swallowing the gesture before `wireSwipeBack()` ever saw a
         completed swipe. Added `touch-action:pan-y` to `.app`, which
         tells the browser vertical panning is its job but leaves
         horizontal gestures for the page's own JS to interpret.
      2. Separately, the generic `.back-btn[data-action]` query would
         have matched Home's settings gear (`.home-settings-btn`, which
         reuses the `.back-btn` class purely for its shared press-
         feedback styling, with `data-action="go-settings"`) — meaning
         swipe-left on Home would have jumped to Settings instead of
         correctly doing nothing. Query now excludes
         `.home-settings-btn` explicitly.
    - `sw.js` bumped to `rooted-v100`.

104. **Swipe-back: corrected direction, and a real gap in Browse.**
    **Done (2026-09-15), same day.** Two more fixes from direct
    testing, on top of item 103's:
    - **Wrong direction.** The owner's original request said "swipe
      left," which is what got built — but on actually testing it, the
      owner realized that was their own mistake: the intended gesture
      is swipe RIGHT, matching the standard iOS/Android edge-swipe-back
      convention every other app already trains people to expect.
      Flipped the threshold check (`dx <= 60` now gates instead of
      `dx >= -60`) — swiping right triggers back, swiping left now does
      nothing app-wide.
    - **Browse's book → chapter → verse levels didn't respond at all,
      in either direction.** Cause: unlike every other detail screen,
      Browse's deeper levels use a breadcrumb trail (`renderCrumbs()`,
      the `.crumbs` div — "All books › Genesis › Chapter 3") instead of
      a `.back-btn` arrow, so the swipe handler's `.back-btn[data-action]`
      query found nothing there and silently did nothing. Fixed with a
      second fallback: when no `.back-btn` exists, click the LAST button
      inside `.crumbs` — which is always "go up exactly one level" at
      both nesting depths (the book crumb at verse level clears just the
      chapter; "All books" at the chapter-grid level clears the book
      too), so no new navigation logic was needed, only a second place
      to look for an existing one. Browse's own root book list has
      neither a back-btn nor crumbs and correctly still does nothing,
      consistent with every other bottom-nav tab root.
    - `sw.js` bumped to `rooted-v101`.

105. **Story illustration pipeline, on a completely separate free
    (non-Gemini) toolchain — a style-test batch, nothing wired into the
    app yet.** **Done (2026-09-15).** After the character-portrait work
    (items 90-101), the owner wanted the same treatment for Stories, but
    explicitly did not want to spend more on Gemini API credits. Decided
    against reusing `generate_character_art.py` — this needed a
    genuinely different, no-cost pipeline: **Stable Diffusion XL running
    on Google Colab's free-tier T4 GPU**, chosen over FLUX.1[schnell]
    specifically because schnell's ~12B parameters typically want ~24GB
    VRAM at fp16 and would fight the T4's 16GB, while SDXL fits
    comfortably with mature Colab/`diffusers` tooling. Real, flagged
    tradeoff going in: SDXL is a completely different model family from
    Gemini's image generator, so matching the established stylized-3D-
    animation look is NOT guaranteed through prompting alone the way it
    was tuned for Gemini — this batch is explicitly a style TEST, to be
    judged before any larger commitment (~324 stories total), the same
    "prove it small before scaling" discipline used for every character-
    art batch.
    - **Two-machine workflow, unlike the Gemini pipeline** (which runs
      and commits entirely on this machine): Colab can't write into this
      repo directly, so generation happens there, comes back as a
      downloaded zip, and gets brought in by hand. `pipeline/
      colab_story_art_sdxl.ipynb` (new) is the Colab notebook itself —
      installs `diffusers`/`transformers`/`accelerate`, loads
      `stabilityai/stable-diffusion-xl-base-1.0` in fp16 with
      `DPMSolverMultistepScheduler` and attention slicing (keeps it
      inside the T4's 16GB), generates at 1216×832 (one of SDXL's native
      trained resolutions, ~3:2 — a wide landscape scene suits a
      multi-figure narrative moment far better than the character
      portraits' tight 1:1 close-up crop), and zips the results for
      download via `google.colab.files.download()`.
    - **Style prompt**, a same-design-language sibling of
      `generate_character_art.py`'s `STYLE_SUFFIX` but rewritten for a
      wide multi-figure SCENE rather than a close-up single-character
      portrait (no "CLOSE-UP HEAD-AND-SHOULDERS" framing; explicit "wide
      establishing scene, full figures and environment both visible"
      instead). One real mechanism difference from the Gemini pipeline,
      not just cosmetic: SDXL has a dedicated `negative_prompt` channel,
      which is where "not photorealistic," "not flat vector art," etc.
      now live — negation embedded in the main positive prompt (as
      `generate_character_art.py` does successfully for Gemini) is much
      less reliable for SD-family diffusion models, so this pipeline
      deliberately does NOT copy that part of the Gemini prompt
      structure verbatim.
    - **`pipeline/curation/story_art_settings.json`** (new) — same shape
      as `character_art_settings.json`, a flat map of story id → a real,
      specific scene description. Seeded with exactly the 6 stories the
      notebook currently generates (Creation, the Flood, Feeding the
      5,000, David and Goliath, the Crucifixion, Daniel in the Lions'
      Den), chosen to span visually distinct moods rather than similar
      ones, so the style test is a fair one. Not yet 324 entries — that
      full curation pass is real future work, gated on this test batch
      actually looking right.
    - **`pipeline/import_story_art.py`** (new) — the "bring it back into
      the repo" half of the two-machine workflow. Reads every
      `<story_id>.png`/`.jpg` out of `pipeline/.storyart_incoming/`
      (new, gitignored — the drop point for an unzipped Colab download),
      validates each id against `data/stories.json` (rejects anything
      that isn't a real story id rather than silently importing garbage),
      resizes to 960px wide (proportional height, since these are ~3:2
      not square) and re-compresses before writing to
      `media/stories/<id>.jpg`, and appends to a new flat manifest,
      `data/story_illustrations.json` — deliberately the same
      "manifest, not a full Media entity" shortcut `data/
      character_portraits.json` already established, not a new pattern.
      Does not touch `index.html` — no frontend wiring exists yet for
      story illustrations; that's the next step once the 6-story style
      test is reviewed and approved.
    - `.gitignore` gained `pipeline/.storyart_incoming/` (this pass also
      finally committed the `pipeline/.env.local`/`pipeline/.artscratch/`
      rules from the character-art work, which had been sitting
      uncommitted in the working copy the entire time since that
      pipeline was first built).

106. **Story art v2: the 6-story style test failed, root cause found,
    fixed with a community LoRA plus two scene-description rewrites.**
    **Done (2026-09-15), same day.** The owner reviewed item 105's first
    batch and called it "horrible" — confirmed by looking at all 6
    images directly: Creation and the Flood read as generic fantasy
    digital-painting, the Crucifixion came out as a monochrome stock-
    photo silhouette with no illustrated character detail at all, and
    David and Goliath rendered Goliath as a full sci-fi robot/mech
    instead of an armored man. Feeding the 5,000 and Daniel in the
    Lions' Den were closer, though Daniel himself was an unlit
    silhouette and the "lions" looked more like dogs.
    - **Root cause, confirmed by research before attempting a fix**: base
      `stable-diffusion-xl-base-1.0` has no reliable default lean toward
      "stylized 3D animation" — its output style is essentially
      unconstrained by that phrase alone, unlike Gemini's model, which
      handled the same style instructions well (see item 91). This isn't
      a prompt-wording problem, it's a base-model-capability gap.
      Confirmed no single well-known SDXL checkpoint is reliably known
      for a modern Pixar/DreamWorks look the way e.g. "Juggernaut XL" is
      known for photoreal — this style lives in community LoRAs layered
      on a general checkpoint, not full fine-tunes.
    - **Fix: a verified, well-adopted LoRA, not a guess.** CivitAI's
      "Pixar Style (SDXL)" (civitai.com/models/188525) — 201.6K
      downloads, 575 "overwhelmingly positive" reviews, SDXL 1.0 base,
      CreativeML Open RAIL++-M license (permits this use) — chosen over
      several other real-but-thin-adoption alternatives found during
      research (a full checkpoint claiming this style, `DynaVision-XL`,
      had ~15 downloads/month; a competing LoRA's own author called it
      "a kinda failed attempt"). The notebook now has the owner download
      the `.safetensors` file from CivitAI by hand and upload it via a
      new `files.upload()` cell — CivitAI downloads aren't reliably
      scriptable from Colab without auth, so this stayed a manual step
      rather than risk a broken/expiring hardcoded URL. Loaded via
      `pipe.load_lora_weights(...)`, applied at `cross_attention_kwargs=
      {"scale": 0.9}` (the card's own recommended 0.8-1.0 range), with
      its trigger phrase `"pixar style"` added to the front of
      `STYLE_SUFFIX` (the card's docs say the phrase must appear
      literally in the prompt for the style to activate reliably).
    - **`NEGATIVE_PROMPT` expanded** to directly counter what was
      actually seen, not hypothetical failure modes: added `digital
      painting`, `concept art`, `matte painting`, `stock photo`,
      `monochrome`, `black and white`, `silhouette only` (the
      Creation/Flood/Crucifixion failures) and `robot`, `mecha`,
      `mechanical`, `cyborg`, `sci-fi armor` (the Goliath failure).
    - **Two scene descriptions rewritten**, in both the notebook's
      embedded test dict and `story_art_settings.json` (kept in sync):
      Goliath's now explicit ("a giant of a MAN... fully human, not a
      robot or machine... bronze scale armor") instead of just
      "massive armored... giant," which is what a diffusion model read
      as license to invent battle-mech armor; the Crucifixion's dropped
      "silhouetted" entirely and asks for lit, colored mourners instead,
      since that one word was very likely what pushed the whole image
      into monochrome stock-photo territory.
    - **Not attempted this pass, flagged as a known limitation**: the
      small/distorted-face problem in wide crowd shots (Feeding the
      5,000's background faces, Daniel's own unlit face) is a pixel-
      budget issue — SDXL is trained at ~1024×1024, so a wide scene
      allocates very few pixels per individual face. Research found the
      real fix (per-face detection + inpainting, the mechanism behind
      A1111's "ADetailer" extension) is real extra engineering — a face-
      detection model plus a second `StableDiffusionXLInpaintPipeline`
      pass per detected face — not attempted here; a plain image-wide
      hires-fix/img2img pass was confirmed NOT to meaningfully fix this
      specific problem (the added resolution spreads across the whole
      scene, not onto individual faces), so it wasn't added either.
      Worth revisiting if the LoRA fix alone isn't enough once this
      round is reviewed.
    - **Addendum, same day**: the owner's actual run of this notebook
      hit `ImportError: Found an incompatible version of torchao. Found
      version 0.10.0, but only versions above 0.16.0 are supported` on
      `pipe.load_lora_weights(...)` — Colab's preinstalled `torchao` is
      too old for the `peft` version `diffusers` pulls in for LoRA
      loading. Fixed by explicitly installing `peft` and `torchao>=0.16.0`
      in the install cell, with a note that a Colab **runtime restart**
      is required if the old versions were already imported in that
      session (a `pip install -U` doesn't retroactively patch an
      already-running Python process).
    - **Second addendum, same day**: a further run hit `IndexError: list
      index out of range` in `diffusers/utils/peft_utils.py`'s
      `get_peft_kwargs()` on the same `load_lora_weights(...)` call — the
      LoRA file parsed but yielded zero keys matching either the
      diffusers-native or Kohya-style naming pattern, so the rank dict
      the loader builds from those keys came back empty. Not yet root-
      caused — rather than guess again, added a diagnostic cell (loads
      the raw safetensors state dict directly, prints the key count and
      first 15 keys, classifies them against both naming patterns) ahead
      of a rewritten load cell that surfaces that diagnosis inline if the
      load fails again. Unresolved as of this writing — waiting on the
      owner to re-run and report either the diagnostic output or a new
      result.

107. **Practice screen overhaul + app-wide emoji removal — done
    (2026-09-16).** Two owner requests handled together since both touch
    the same screen. First, a "modern, high-end learning launchpad"
    redesign of Practice (`index.html`):
    - **`.practice-hero-card`** combines the existing daily-goal ring
      (`renderGoalRing()`, unchanged, item 32) and challenge-type picker
      (`renderChallengePicker()`, unchanged) with a new full-width
      primary CTA, `renderPracticeHero()` — "Start Practice Session (N
      Verses)" instead of the old inline-icon sentence-style button.
    - **`renderPracticeStatsStrip()`** replaces the old 4-box `.stat-row`
      grid with one horizontal bar on `--surface-sunken` (the dark-token
      family already in place since visual system v3 — see "Visual
      direction" above — no new hex values needed, the owner's requested
      `#1C1917`/`#B8AEA5` already match `--surface-sunken`/`--ink-soft`
      closely enough that reusing the existing tokens was the right
      call, not a near-duplicate pair): streak, mastered count, and
      library size,
      each with its own inline-SVG icon (see below).
    - **Sticky filter tabs** (`renderPracticeFilterTabs()`, new
      `practiceFilter` state, `set-practice-filter` action): All / Due
      Today / Mastered, each showing its own live count, filtering via
      a new `filteredPracticeVerses()` — `renderPracticeLanding()` now
      reads from that instead of the unfiltered `data.verses` directly.
    - **Topic tags on verse cards became soft, lowercase hashtag pills**
      (`.tag--pill`, `hashtagify()`) — deliberately a *new*, scoped CSS
      class rather than a change to `.tag` itself, which stays the
      uppercase eyebrow badge everywhere else in the app (that split was
      a deliberate earlier decision, item 85 — reversing it globally
      here would have silently undone that).
    - **A 4-segment mastery bar** (`renderMasteryBar()`, ordered
      `MASTERY_STAGES`) replaces the old uppercase mastery `.tag` inside
      each verse card's tag row, moved to the card's top-right corner
      (`.mastery-bar`, absolutely positioned — `.verse-card` gained its
      first base rule, `position:relative`, since none existed before).

    Second, app-wide emoji removal. A full regex scan found only **four**
    real Unicode emoji anywhere in `index.html` — all inside
    `MASTERY_LABELS` (🌱🌿🌳👑) — everything else the request named
    (streak flame, verse-of-the-day sun, Word-of-the-Day/Church-History
    eyebrows, practice-button icons) was already a Tabler icon-font glyph
    (`ti-flame`/`ti-sun`/`ti-abc`/`ti-building-church`/`ti-swords`), not a
    literal emoji character. Handled both cases:
    - `MASTERY_LABELS` de-emojified to plain text (Seedling/Sprouting/
      Rooted/Flourishing) — mastery now reads through the new bar
      indicator above instead of an emoji in the label text.
    - A new inline-SVG icon system: `ICON_PATHS`/`icon(name, size)`
      (real Lucide line-icon path data, fetched from Lucide's own source
      rather than hand-approximated, stroke-width overridden to 1.75 per
      the brief) plus a shared `.app-icon` CSS rule
      (`display:inline-flex; vertical-align:middle; flex-shrink:0`, no
      hardcoded color — `stroke="currentColor"` follows whatever
      surrounding text color it's dropped into, so one icon call works
      correctly in the streak badge's white-on-gradient text, a plain
      dark-mode label, etc. without per-context overrides). Replaced the
      five requested Tabler icons at their exact usage sites (streak
      badge → `flame`, Verse-of-the-Day label → `sun`, Word-of-the-Day
      and both Church-History eyebrows → `languages`/`landmark`, the
      three "Practice this verse/topic" buttons and the new hero CTA →
      `sparkles`) — the bottom-nav Practice tab's own `ti-swords` was
      left as the Tabler glyph, since the request was scoped to card
      headers/badges/buttons/metrics, not nav icons, and converting the
      nav bar wasn't asked for. `TOPIC_ICONS`'s per-topic card icons
      (`topic_creation:'ti-sun'`, `topic_anger:'ti-flame'`, etc.) are a
      different, unrelated feature (colorful topic-grid coding, item 63)
      and were left untouched for the same reason.

    `sw.js` bumped to `rooted-v102`.

108. **Story art: SDXL/Colab pipeline abandoned, switched back to Gemini
    — done (2026-09-16).** The item-106 LoRA fix got the Colab notebook
    actually loading and generating (after two more real version-pin
    fixes below), but reviewing the resulting 6-story batch directly
    showed the same underlying problem the LoRA fix was meant to solve
    was only half-solved: David and Goliath, Feeding the 5,000, and the
    lions' den all landed the target stylized-3D-animation look well,
    but Creation, the Flood, and the Crucifixion's wide vista still read
    as generic realistic/matte-painting — the LoRA's influence was
    clearly weaker on landscape/atmosphere-heavy scenes with no close
    foreground character to "anchor" the style. Owner's call after
    seeing all 6: **not worth continuing to fight LoRA inconsistency for
    free** — going back to Gemini (billed, but proven at 267/267 on the
    character portraits with zero style drift) rather than spending more
    time tuning SDXL prompts/scale for the weak cases.
    - **New `pipeline/generate_story_art.py`**, structured identically to
      `generate_character_art.py` (same `--test`/`--batch` shape, same
      `.env.local` key loading, same Gemini endpoint/response parsing) —
      but unlike that script's own `--batch` (still stubbed
      "not yet implemented," since the 267 real character portraits were
      actually produced by one-off per-batch scripts, not this reusable
      one), this new script's `--batch` **is** fully wired: generates,
      resizes to the same 960px-wide JPEG q82
      `import_story_art.py` already used, writes directly to
      `media/stories/<id>.jpg`, and updates
      `data/story_illustrations.json` in one step — no Colab-style
      two-machine incoming/import dance needed, since Gemini runs
      synchronously from wherever this script executes.
    - **`STYLE_SUFFIX` rewritten**, not just copied from the character
      script — explicitly instructs that environment/landscape elements
      (mountains, sky, water, clouds) must read as stylized animated art
      even with no foreground character present, directly targeting the
      failure mode just seen (the character script's own STYLE_SUFFIX
      had no reason to say this, since every character prompt always has
      exactly one foreground subject).
    - Reuses the existing `pipeline/curation/story_art_settings.json`
      scene descriptions verbatim (including the Goliath/Crucifixion
      rewrites from item 106) as the first test batch — the scene
      *content* was never the problem, only the renderer.
    - `pipeline/colab_story_art_sdxl.ipynb`, `story_art_settings.json`,
      and `import_story_art.py` are kept, not deleted — they're now
      historical record of a real approach that was tried and measured,
      the same way the project keeps every other superseded decision
      documented rather than erased.
    - **Not yet run** as of this writing — the owner needs to add more
      Gemini credits first (the same billing gate hit earlier in the
      character-portrait work). `--test` on the 6 stories above is the
      next step once credits are available, same validate-before-batch
      discipline as the character pipeline.
    - **Addendum, same day, before the above conclusion was reached**:
      getting the Colab notebook to actually run required two more
      real version-pin fixes, both found by inspecting the LoRA file's
      actual tensor keys rather than guessing: (1) `diffusers`'s latest
      release (0.40.0, pulled by the install cell's `-U` flag) crashed
      with the same `IndexError: list index out of range` in
      `get_peft_kwargs()` even though the file was confirmed to be a
      completely standard Kohya SDXL LoRA (proper `lora_unet_`/
      `lora_te1_`/`lora_te2_` keys, all three SDXL components present,
      nothing unrecognized) — pinned to `diffusers==0.31.0`, a version
      with well-documented real-world compatibility for this exact
      SDXL+Kohya+CivitAI combination; (2) pinning `diffusers` alone then
      surfaced `ImportError: cannot import name 'FLAX_WEIGHTS_NAME'`,
      since `transformers` was still on latest and had dropped Flax
      support (removing that symbol) that `diffusers 0.31.0`'s SDXL
      pipeline still imports — pinned `transformers==4.46.3`, from the
      same release era. Both required a Colab runtime restart to take
      effect, same reason as the original torchao fix.

109. **4-Pillar navigation — done (2026-09-16), owner-specified
    architecture.** Collapsed the bottom nav from 6 tabs (Home,
    Practice, Browse, Topics, Study/People, Add) down to 4: **Home**
    (unchanged — the editorial daily-inspiration feed from item 82),
    **Practice** (unchanged — the memorization engine from item 78),
    **Discover** (new — Scripture reading, the canonical index, topic
    collections, and character/story profiles), and **Study**
    (redefined — the "deep theological suite" pillar; Patterns is its
    only real content today, see below). This is a real information-
    architecture change, not a rename — Browse, Topics, People, and
    Stories move out from being independent nav roots into Discover;
    Patterns moves out of the old People-grouped screen into Study;
    "Add" loses its own tab entirely.
    - **`renderDiscover()`** (new) is a thin hub screen — four cards
      (Read the Bible / Topics / People / Stories) linking to the
      existing `renderBrowse()`/`renderTopics()`/`renderCharacters()`/
      `renderStories()` screens completely unchanged. Deliberately not a
      rewrite of any of them: each already works, is independently
      reachable (a character's `from` trail still returns to People/
      Stories directly, not back through this hub), and a full rewrite
      wasn't asked for or needed — this is a nav-only pass, consistent
      with the owner's explicit sequencing choice below.
    - **Study's bottom-nav button routes directly to the existing
      `renderMotifs()` (Patterns) screen** rather than a new, currently-
      identical "study hub" screen — its `data-nav` is literally
      `"motifs"`. Real timelines and family relationships already exist
      but live inline on Character Detail, not as standalone Study
      views; interlinear/Strong's data, interactive connection node
      graphs, and commentaries are all unbuilt vision items (see Known
      Gaps). Deliberately did NOT ship placeholder "coming soon" cards
      for those — `renderMotifs()` stays an honest, fully-working
      screen, and the roadmap commitment lives in CLAUDE.md/Known Gaps
      instead of fake UI.
    - **Both `renderStories()` and `renderMotifs()` changed from a
      `.screen-head` + back-button layout to a plain `.topbar`** (no
      back button) — they were previously reached only as a sub-page
      pushed from the People screen (`back-to-characters` always
      returned there); now they're root destinations of their own pillar,
      matching the header style every other nav-root screen already uses
      (Browse/Topics/Characters). The `back-to-characters` and
      `open-motifs` actions became fully dead once their only callers
      (two quick-cards on the People screen) were removed, and were
      deleted rather than left as unreachable code.
    - **The People screen's own "Stories" and "Patterns" quick-cards
      were removed** — both are now peer top-level destinations (Stories
      as a Discover-hub card alongside People itself; Patterns moved
      entirely to Study), so re-surfacing them nested inside People would
      blur the exact pillar boundary this restructuring exists to draw.
    - **"Add" (New verse / New person / Find a verse) lost its own
      bottom-nav tab** — not named anywhere in the owner's 4-tab spec,
      and enforcing exactly 4 tabs meant it needed a new entry point
      rather than staying a 5th. Landed as a small `+` icon button next
      to Practice's "Your verses" section label (`go-add` action,
      already-existing `renderAddMenu()` screen unchanged) — the most
      natural home for it, since adding your own verse/person is a
      library-management action, and Practice already owns "your
      verses." `renderAddMenu()` gained a real back button (`.screen-head`
      + `go-practice`) since it's now genuinely a sub-page rather than a
      nav root, which it never needed one for before.
    - **Icons, type scale, dark palette**: the icon requirement (Lucide-
      style stroke SVGs, no emoji) and the type-scale requirement
      (12/14/18/22px) were already fully satisfied by items 85 and 107 —
      no change needed here. The palette values given
      (`#1C1917`/`#120E0C`) are close to but not identical to the
      existing v3 dark tokens (`--paper-raised` `#18191D` / `--paper`
      `#08090B`, a deliberate 2026-09-10 decision, see "Visual
      direction") — confirmed with the owner this was describing the
      existing dark theme loosely, not requesting a new palette, so no
      token values changed.
    - **Explicitly out of scope for this pass, by owner's own
      sequencing choice ("doc-first, build later")**: building the
      node-graph/interlinear/Strong's/commentary features themselves.
      Those are now tracked as their own Known Gaps items (CLAUDE.md) —
      this item is the navigation/architecture commitment only.
    `sw.js` bumped to `rooted-v103`.

110. **Timelines & Family Trees added to Study — done (2026-09-16).**
    Owner asked for these sourced from "The Bible Project Open
    Resources and Wikidata Biblical Graph Queries." Neither was used:
    The Bible Project doesn't publish a structured, machine-queryable
    dataset for this (their content is videos/infographics, not an
    API); Wikidata's SPARQL graph data on biblical figures is real but
    crowd-sourced and inconsistent, which would cut directly against
    this project's whole curation discipline — every relationship in
    this app is hand-verified against the actual WEB text, the same
    reasoning that rejected the NIV PDF early on. Confirmed with the
    owner and built both features entirely from data already curated
    here instead — zero new external dependency, ships immediately.
    - **Timeline** (`renderTimeline()`) — every `Era` in canonical
      `order`, each showing its `Story` records in `canonicalOrder`,
      reusing the exact `.timeline`/`.tl-item` CSS the per-character
      "Their life" section on Character Detail already uses (visual
      consistency, zero new CSS for the list itself). Distinct from
      that per-character view — this is the whole Bible, Creation to
      Revelation, one continuous scroll. Tapping a story opens the
      existing Story Detail screen (`open-story`, already `from`-aware).
    - **Family Tree** — a real visual SVG node-link graph, not a flat
      list (a flat list was offered as the lower-effort option; the
      owner chose the harder graph explicitly). Built in three layers:
      - `FAMILY_CORE_TYPES` + `familyGraph(rootId, maxGen)` — BFS over
        the existing `characterRelationships()` (itself just
        `connectionsFor('character', id)`, DATA_MODEL.md §2.4/§8.4),
        scoped to CORE blood/marriage types only (parent, child,
        spouse, sibling — the `+1`/`-1`/`0` generation deltas below).
        Deliberately excludes the looser relationship strings this app
        also stores (`uncle of`, `kinsman of`, `raised`, `servant of`,
        `mistress of`, `successor of`, `worked alongside`) — those
        don't have one clean generation delta relative to an arbitrary
        root, and a generation still naturally surfaces aunts/uncles/
        nephews/grandparents through the plain parent-child chain
        without needing them tagged explicitly. `maxGen` (default 2)
        bounds how far the BFS reaches, since an unbounded walk over
        the whole `Connection` graph isn't renderable on a phone screen
        for a well-connected figure. Verified against real curated data
        before shipping (not just unit-tested in the abstract): David's
        tree is 13 nodes/14 edges across generations -1..+2; Jacob's
        and Isaac's are each 11 nodes/18 edges across -2..+1; a
        childless/unconnected character (188 of 267 characters — most
        of the cast — currently have zero curated character-character
        connections at all) correctly degrades to a single node with an
        honest empty-state message, not a crash or a blank graph.
      - `layoutFamilyGraph(nodes, edges)` — a one-pass Sugiyama-style
        layered layout (rows = generations, columns reordered once by
        barycenter of each node's already-placed neighbors in the row
        above) written by hand rather than pulling in a graph-layout
        library — this app has zero third-party JS dependencies
        anywhere and introducing one for a single feature wasn't
        judged worth breaking that precedent for what's a genuinely
        small graph (a few dozen nodes at most, given only ~84
        character-character connections exist project-wide today).
      - `renderFamilyTree(id)` renders the layout as inline SVG
        (`<line>` edges color/dash-coded by relationship kind — solid
        gold for parent/child, dashed tan for spouse, dashed gray for
        sibling — plus a legend; `<g data-action="family-tree-nav">`
        nodes, styled/highlighted when they're the current root).
        Tapping any node re-centers the tree on that person, chaining
        `view.params.from` the same way Character Detail's own back
        button does, so repeated back-presses walk back through however
        many people were visited, ending at a search-driven picker
        screen (`renderFamilyTreePicker()`, same era-grouped-list +
        search pattern as People/Stories/Topics, own `familyTreeQuery`
        state) rather than dropping straight to the Study hub.
      - `wireFamilyTreePanZoom()` — hand-rolled pan (pointer drag) and
        zoom (mouse wheel + two-finger pinch, via a `pointerId -> {x,y}`
        map), since plain SVG has no built-in viewport gestures and
        nothing elsewhere in this app already solved this. Tap vs. drag
        is disambiguated by total pointer movement, then a captured
        one-time `click` suppressor swallows the trailing click after a
        real drag — same tap/gesture disambiguation shape as
        `wireSwipeBack()` (item 102), applied to a new problem.
    - **`renderStudy()`** — Study's real hub now (superseding item 109's
      "route straight to Patterns since that's the only real content"
      decision, which was explicitly provisional): three cards
      (Patterns/Timeline/Family Tree), same shape as `renderDiscover()`.
      The bottom-nav button's `data-nav` moved from `"motifs"` back to
      `"study"`; `NAV_GROUPS.study` now covers all three destinations.
    `sw.js` bumped to `rooted-v104`.

111. **Family Tree rendering overhaul — done (2026-09-16), same day as
    item 110.** The owner gave a full, hex-exact visual/engine spec
    (curved connectors, avatar node cards, a rigid parent-centered
    grid, a floating legend pill) to replace item 110's first-pass
    plain-SVG version. Implemented as a hybrid render rather than pure
    SVG shapes, since the spec's own properties (`object-fit`,
    `transition`, `box-shadow`, `backdrop-filter`) are standard CSS, not
    raw SVG attributes:
    - **`#family-tree-canvas`** now holds an absolutely-positioned
      `<svg class="tree-edges-svg">` (connector paths only,
      `pointer-events:none` per spec item 4, so panning/clicking always
      falls through to the canvas/cards beneath it) layered under real
      HTML `.tree-node-card` divs (avatar `<img>`, name, role) at the
      same coordinates — both children of one canvas element, so
      `wireFamilyTreePanZoom()`'s pan/zoom transform (unchanged logic,
      now targeting `#family-tree-canvas` instead of the old bare
      `<svg>`) moves lines and cards together as one unit.
    - **`familyTreeBezier(parent, child, NODE_W, NODE_H)`** (new) — the
      spec's exact cubic-Bezier "elbow": start at the parent's
      bottom-center, end at the child's top-center, both control points
      at the vertical midpoint between them (drops straight down,
      curves through the gap, arrives straight into the child). Applies
      only to parent-child edges, which is the only relationship where
      "bottom of one, top of the other" is geometrically meaningful;
      spouse/sibling edges (same row) stay a plain line between the
      two cards' facing edges.
    - **`layoutFamilyGraph()` rewritten** from the original one-pass
      barycenter reorder to genuine parent-centered positioning: a
      child's X defaults to the average X of its already-placed
      parent(s) (an only child lands exactly beneath its parent, the
      literal "Canaan beneath Ham" case the owner named), a married-in
      spouse with no blood tie upward anchors to their partner's X +
      `X_GAP` instead, and a single collision-resolution pass nudges
      any node whose desired X would overlap its left neighbor out to
      `neighbor.x + X_GAP` — preserving the parent-centered placement
      whenever there's room and only spreading siblings/co-spouses
      apart when they'd otherwise collide. `NODE_W`/`X_GAP`/`ROW_H`
      updated to the spec's exact `150`/`170`/`140`. Re-verified against
      real curated data before shipping (not just re-styled on faith):
      re-ran the same David/Jacob/Isaac/Ham trees as item 110's original
      verification — zero node overlaps in any row, and Ham→Canaan
      (single child, single line of descent) lands at the exact same X
      as its parent, confirming the spec's own worked example.
    - **A deliberately distinct warm bronze/dark palette, scoped ONLY to
      this feature's own CSS classes** (`.tree-node-card`, `.tree-avatar`,
      `.tree-legend`, the connector `stroke` colors) — `#1C1917`/
      `#2E2925`/`#26221F`/`#F5F2ED`/`#A39B92`/`#C69255`, taken literally
      from the owner's hex-exact spec rather than mapped onto the app's
      existing `--paper-raised`/`--gold` tokens. This is a different
      call than item 109's palette question earlier the same day (where
      loosely-similar values were confirmed as describing the existing
      v3 theme, not a change) — here the values are precise, numerous,
      and specific to one feature's own component styling, which reads
      as a deliberate scoped design choice rather than a loose
      description of what already exists. Does not touch or relitigate
      the app-wide v3 dark theme (see "Visual direction").
    - **"Selected node" highlight** (spec item 1's interactive-highlight
      requirement) is implemented as "the current focal/root person" —
      its card gets the active/glow treatment (spec item 2) and every
      edge touching it gets the highlighted stroke/glow (spec item 1) —
      rather than introducing a separate hover-only preview state this
      app has no other precedent for. Tapping any card still re-centers
      the tree on that person immediately, same navigation model as
      item 110.
    - One deliberate deviation from the letter of the spec, noted rather
      than silent: node cards use a fixed `width` (matching `NODE_W`)
      instead of `min-width`, with `text-overflow:ellipsis` on the name/
      role — needed so a long name can never grow a card wider than the
      layout engine accounted for and silently misalign its connector
      endpoints; the visual result (a clean 150px card, long names
      truncated) is the same either way.
    `sw.js` bumped to `rooted-v105`.

112. **Family Tree feedback pass — done (2026-09-16), same day as items
    110-111.** Three fixes from direct use:
    - **Swipe-right-to-go-back disabled on the rendered Family Tree
      screen.** `wireSwipeBack()`'s `pointerdown` handler now returns
      immediately if `#family-tree-viewport` exists in the DOM — a
      rightward pan to explore the tree was fighting the app-wide
      swipe-back gesture for the same pointer motion. Scoped to the
      viewport's presence (i.e. the actual rendered tree), not the
      whole `familyTree` screen id, so the picker/search screen (no
      viewport, no panning to protect) keeps swipe-back as normal.
    - **The picker now only lists people with a real curated family**,
      styled as "`{Name}'s Family`" cards (`renderFamilyCard()`,
      `hasFamilyTree()` — reuses `FAMILY_CORE_TYPES` to check for at
      least one core relationship) instead of every one of the app's
      267 characters. Direct owner feedback: most entries in the full
      list dead-ended on the "no family curated" empty state, which
      wasn't a useful browsing experience. This does list every
      *individual* with a connection (so both "Noah's Family" and, say,
      "Ham's Family" appear as separate entries even though they
      overlap) rather than clustering into one entry per family group —
      clustering would need real judgment calls about which person is
      each cluster's "main" one that weren't asked for, and letting any
      connected person be an entry point is arguably more useful for
      exploration anyway (open "Ham's Family" directly instead of
      always starting from Noah and drilling down).
    - **Filled real, verifiable family-connection gaps** — the owner
      named Jesus specifically as a family that "isn't available yet."
      Audited a set of well-known figures against `data/connections.json`
      and found seven real, Scripture-sourced facts that were already
      implicit in these characters' own curated `summary` text but had
      never been converted into a structured `Connection` edge: Mary
      "mother of" Jesus; Joseph "adoptive father of" Jesus (deliberately
      *not* plain "father of" — Jesus's own summary already says
      "conceived by the Holy Spirit," so the connection type needed to
      reflect a legal/adoptive relationship, not a biological one, the
      same care this project has shown elsewhere, e.g. Melchizedek,
      the two Josephs/two Zechariahs); Joseph "husband of" Mary;
      Zacharias "father of" and Elizabeth "mother of" John the Baptist
      (both already existed as characters with matching bios from the
      birth-of-Jesus curation — item 41 — just never linked to their
      son); Zacharias "husband of" Elizabeth; and Peter "brother of"
      Andrew (Peter's own summary already says "brought to Jesus by his
      brother Andrew"). All seven use characters that already existed —
      no new Character records were added, consistent with treating
      that as a separate, bigger curation decision than a same-day gap
      fill. `pipeline/curation/connections.json` → 150 connections
      (was 143), rebuilt via `py pipeline/build_connections.py` and
      verified idempotent (`--check`) and resolving correctly from both
      directions (e.g. `characterRelationships('char_jesus')` now
      returns both parents). This is necessarily a small, targeted pass,
      not a full audit of every character's family — most of the 267
      characters still have no curated family connections at all (188
      had none before this pass; 181 after), and filling that in more
      broadly is real, ongoing curation work in the same vein as items
      65-67/70-74/86/88-89, not something to do speculatively in one
      sitting. (188 characters had zero connections of any kind before
      this pass; 180 after — the 8 newly-connected are Mary, Joseph,
      Jesus, Zacharias, Elizabeth, John the Baptist, Peter, and Andrew.)
    `sw.js` bumped to `rooted-v106`.

113. **A fifth ChallengeType: Tap Builder (word-tile bank) — done
    (2026-09-17).** The owner's own spec (state engine, UI layout,
    check/feedback mechanics) mapped almost exactly onto the existing
    pluggable `ChallengeType` interface (design philosophy #5) — this
    added one new entry to `CHALLENGE_TYPES`, `challenge_tap_builder`,
    with no changes needed to the shared session/scoring/mastery
    machinery (`recordPractice()`, streaks, next-review scheduling all
    already generic over any challenge type).
    - **`build(verse, config)`** picks 4-6 eligible words (same
      length-based eligibility filter as `challenge_fill_blank`) as
      blanks, then calls `pickTapBuilderDistractors()` for 2-3 extra
      words and shuffles everything into one `bank` array. Distractors
      are drawn from `data.verses` (the user's own always-loaded
      library) rather than the full corpus in `data/verses.json` —
      that corpus is lazily fetched only once Browse has been opened
      (`loadCorpus()`), so sourcing from it here would make the
      exercise silently distractor-less (or need its own fetch) for
      anyone who opens Practice without visiting Discover first; this
      keeps the exercise genuinely offline-first as asked.
    - **`interact(state, ds)`** handles both tile-bank taps (fill the
      first empty slot) and placed-tile taps (clear that slot, return
      the tile to the bank) — same `interact()` extension point
      `challenge_scramble`'s pick/unpick chips already use, just with
      "first empty slot" instead of "next position in sequence."
    - **`canCheck(state)`** is a new, small, backward-compatible
      addition to the `ChallengeType` interface (every existing type
      defaults to always-checkable) — lets a type disable the generic
      Check button until its own notion of "ready" is met (here: every
      blank filled). `checkPractice()` now respects it, and
      `renderPractice()` renders the button `disabled` when it's false.
    - **`autoAdvanceMs`** is a second new optional interface property —
      on a correct check, `checkPractice()` schedules a guarded
      `setTimeout` (bails if the session moved on or ended before it
      fires) that calls a newly-extracted `advancePractice()` — the same
      function the existing "Continue" button now calls too, factored
      out of what used to be inline logic in the `next-practice` action
      handler. Tap Builder is the only type using this so far; the
      "Continue"/"Finish" button still always shows too, so nothing
      breaks if the timer is ever skipped (reduced-motion, a slow
      device, whatever) — auto-advance is a convenience layered on the
      existing flow, not a replacement for it.
    - **A distinct dark-obsidian/bronze component palette**, scoped only
      to Tap Builder's own new CSS classes (`.target-sentence-box`,
      `.tap-slot`, `.tap-tile`, `.tap-builder-check`), same reasoning as
      the Family Tree feature's own palette (item 111) — hex-exact
      values given for one specific component's own look, not a request
      to touch the shared `--gold`/`--sage`/`--danger` tokens every
      other challenge type still uses. The correct/incorrect slot colors
      (`#10B981`/`#EF4444`) are likewise scoped rather than redefining
      `--sage`/`--danger` app-wide.
    - **`.segmented` (the challenge-type picker) changed from an even
      `flex:1` grid to a horizontally-scrollable pill row** — a 5th
      option made "Progressive reveal" start wrapping mid-word on a
      narrow phone; same `overflow-x:auto` pattern `.practice-filter-tabs`
      already uses elsewhere.
    - Verified by simulation against real curated verses before
      shipping, not just read over: built the exercise for 30 random
      verses and played each one "perfectly" (always taps the correct
      tile) — every one graded fully correct with no crashes; separately
      confirmed tapping a placed tile correctly returns it to the bank
      (and re-enables that specific tile) and that a genuinely wrong
      placement is correctly marked incorrect.
    `sw.js` bumped to `rooted-v107`.

114. **Retired the four original ChallengeTypes; added First-Letter
    Sprint — done (2026-09-17), same day as item 113.** Owner's explicit
    direction: "get rid of the older exercises and keep the new ones."
    Deleted `challenge_fill_blank`, `challenge_scramble`,
    `challenge_first_letters` ("Progressive reveal"), and
    `challenge_verse_ladder` from `CHALLENGE_TYPES` entirely, along with
    their now-dead-code support (`hintWord()`, the `.blank`/`.chip`/
    `.scramble-*` CSS families, and `.chip` entries in the two shared
    press-feedback/reduced-motion selector lists). Every hardcoded
    `'challenge_fill_blank'` fallback (the four places `settings` gets
    its default `challengeTypeId`, plus `challengeType()`'s own
    not-found fallback) now points at `challenge_tap_builder` instead —
    a returning user whose `rooted-settings` still names one of the
    four removed ids is already caught by the existing
    `if(!CHALLENGE_TYPES[id]) settings.challengeTypeId = ...` guard at
    every load site, so this degrades cleanly rather than crashing on a
    stale stored id. `CHALLENGE_TYPES` now holds exactly two entries:
    Tap Builder (item 113) and the new one below.
    - **`challenge_first_letter_sprint`** ("First-Letter Sprint") — a
      speed-typing drill, genuinely different in kind from every
      previous type: driven by real keystrokes rather than taps on
      `data-action` elements. `build()` extracts each word's first
      A-Z letter (`firstLetter()`, ignoring case/leading punctuation;
      a token with no letter at all is auto-skipped rather than
      blocking the sprint) and starts a `Date.now()` clock immediately.
      Typing the right next letter reveals that word in full and
      advances instantly with a green flash; a wrong letter flashes red
      and does not advance — there is no failure path other than "not
      yet correct," so completing the verse always counts as a correct
      practice attempt (same shape the old self-graded types' "Got it"
      button always had).
    - **Keystrokes reach `interact()` through a new parallel entry
      point, not through `practiceInteract()`'s click-only path.**
      Refactored the shared finalize logic (push to `session.results`,
      `recordPractice()`, sound/haptics, the same guarded
      `autoAdvanceMs` timeout `checkPractice()` uses) out of
      `practiceInteract(el)` into a new `practiceInteractWith(ds)`;
      `practiceInteract(el)` now just calls it with `el.dataset` as
      before, and a new `practiceKeyInput(letter)` calls it with a
      synthetic `{letter}` "dataset" instead. Every existing type's
      click-driven `interact()` is completely unaffected — this only
      added a second way to reach the same shared machinery.
    - **`wireFirstLetterSprint()`** (new, called from `bindEvents()`
      alongside `wireTimelineDrag()`/`wireFamilyTreePanZoom()`) does two
      things after every full render: keeps a visually-hidden but real
      `<input>` focused (so physical-keyboard keystrokes land on it, and
      mobile virtual keyboards have something real to attach to — a
      single `input` event on that field is the one source of truth for
      "what letter was just typed," deliberately not a second, separate
      `document`-level `keydown` listener, which would have double-
      fired for the same keystroke whenever a physical keyboard was
      used), and starts a `setInterval` that updates a `#sprint-timer`
      span's `textContent` directly every 100ms. That timer interval is
      the one piece of this feature that deliberately does NOT go
      through the normal `render()` cycle — re-rendering the whole
      screen every 100ms would fight the keystroke-driven renders and
      repeatedly steal the hidden input's focus, the same reasoning
      `wireTimelineDrag()` already gives for moving real DOM nodes
      during a drag instead of re-rendering on every `pointermove`.
      Actual gameplay (each keystroke) still goes through the completely
      normal `interact()` -> `render()` cycle every other type uses —
      only the passive "seconds ticking up while you're not typing"
      display needed the exception.
    - **`renderPractice()` gained a third per-type template branch**
      (alongside Tap Builder's from item 113): Sprint also skips the
      shared `.card` wrapper (its own `.sprint-text-box` is a complete
      component already), skips the generic result banner (its own
      completion toast — "Completed in 6.4s! (120 WPM)" — replaces it),
      and swaps the ref line's normal "· Type Name" suffix for a live
      bronze timer while the sprint is running. `controls()` returns an
      empty string while not yet checked, suppressing the generic Check
      button entirely (there's nothing to check — typing is the whole
      interaction); the generic "Continue"/"Finish" button still appears
      once `checked` is true, same as every other type.
    - WPM is computed as words-per-minute on whole words (not the
      classic 5-characters-per-word convention) — this drill is about
      racing through word-initial recall, not raw character throughput,
      so the simpler, more literal metric fit better.
    - Verified by simulation against real curated verses before
      shipping: 40 random verses "typed" letter-perfect all completed
      and graded correct; a deliberately wrong keypress was confirmed to
      neither advance nor corrupt state, and a correct keypress
      immediately afterward advanced normally; the WPM formula was
      checked against a hand-computed example (10 words in a simulated
      5.0s came back as 120 WPM).
    - **Addendum, same day: real-device report ("not working properly
      with the mobile keyboard") led to a real architecture fix.** The
      simulation above only exercised the logic (`build`/`interact`),
      never an actual mobile browser — the bug was in how a keystroke
      reached the screen, not in the scoring logic. Root cause: every
      keystroke went through the normal `interact()` -> `render()`
      cycle every other challenge type uses, and this app's `render()`
      always rebuilds its whole subtree via `innerHTML =`. On a real
      phone that destroys and recreates the hidden `<input>` on every
      single letter typed, which closes the on-screen keyboard each
      time — functionally unusable. A second, compounding bug: because
      the hidden input has `pointer-events:none` (so it never visually
      intrudes), there was no way to tap it back open once the keyboard
      closed, especially after `autoAdvanceMs`'s `setTimeout` advanced
      to a new verse — a `setTimeout` callback isn't a direct user
      gesture, so a mobile browser won't reliably reopen a keyboard for
      a `.focus()` call made from inside one, even though the DOM
      `activeElement` does update correctly.
      - **Fix 1**: keystrokes on this challenge type no longer go
        through a full `render()` while the sprint is still in
        progress. `wireFirstLetterSprint()`'s `input` listener now calls
        `type.interact()` to mutate state exactly as before, then
        patches only `#sprint-text-box`'s `innerHTML` directly with a
        newly-extracted `sprintTokensHTML(state)` (shared with
        `render()`'s own initial markup, so the two can't drift) —
        the `<input>` element itself is never touched, so it keeps its
        focus and the keyboard stays open continuously through an
        entire verse. A real `render()` now only happens once, at the
        exact moment the sprint actually completes (`state.checked`),
        which is the point the screen legitimately needs to change to
        the toast/Continue view — so the finalize sequence
        (`recordPractice`, `session.results`, sound/haptics, the
        guarded `autoAdvanceMs` timeout) is duplicated inline in
        `wireFirstLetterSprint()` rather than reached through
        `practiceInteractWith()` (documented cross-reference left in
        both places so they're kept in sync if this ever changes).
      - **Fix 2**: a new, always-visible "Keyboard not showing? Tap
        here." hint under the sentence box
        (`data-action="focus-sprint-input"` -> a plain `input.focus()`
        called directly inside a real click handler, which — unlike a
        `setTimeout`-triggered one — mobile browsers do honor as a
        user-gesture-driven focus) gives the user an explicit, always-
        available way back to typing whenever the OS keyboard has been
        dismissed for any reason, most importantly right after an
        auto-advance to the next verse.
      - This is now a documented, load-bearing exception to this app's
        normal "one `render()` rebuilds everything" model — worth
        knowing before touching this challenge type again, or before
        assuming any future real-time/keystroke-driven feature can just
        reuse the standard `interact()` -> `render()` pattern unchanged.
    - **Second addendum, same day: fixing the keyboard closing surfaced
      a second real-device bug — the page scrolling the verse out of
      view on every keystroke.** Root cause was `.sprint-hidden-input`
      being `position:absolute` **in the document flow** right after
      `.sprint-text-box` — every keystroke's `sprintTokensHTML()` patch
      changes that box's rendered height (revealing a word), which
      moves the still-focused input along with it, and mobile browsers
      "helpfully" keep a focused input scrolled into view — so the page
      kept re-scrolling to chase the input every single keystroke,
      exactly the "blindly tapping" symptom reported. Fixed by making
      the input `position:fixed;top:0;left:0` — pinned to the viewport
      instead of the reflowing document, so it never moves regardless
      of what the sentence box does, breaking the feedback loop
      entirely. Also set an explicit `font-size:16px` on it, since a
      focused input computed under 16px triggers iOS Safari's own
      separate auto-zoom-and-scroll behavior — not confirmed as part of
      this specific report, but the same category of bug and cheap to
      close off pre-emptively while already in this code.
    `sw.js` bumped to `rooted-v110`.

115. **A third ChallengeType: Progressive Vanish — done (2026-09-17).**
    Self-graded like First-Letter Sprint (no wrong-answer path — typing/
    reciting it at all means success), but a much simpler interaction:
    pure taps, no keyboard, so none of item 114's real-device mobile
    bugs apply here at all.
    - **`build(verse, config)`** — the owner's spec named the
      constructor `initProgressiveVanish(verse)`; mapped onto this
      app's actual dispatch shape, `CHALLENGE_TYPES[id].build(verse,
      config)`, same architectural call already made for the other two
      new types' own similarly-named specs (a bespoke top-level init
      function per type would bypass the whole point of a pluggable
      `CHALLENGE_TYPES` registry). Tokenizes into `{text, vanished,
      isPunctuation}` objects per the spec's own shape, then picks a
      **fixed random order** deciding which non-punctuation words vanish
      first — the exact same "stage N's hidden set is a superset of
      stage N-1's" guarantee `challenge_verse_ladder` used before it was
      retired (item 114) — a genuinely good idea being reused under a
      new name/UI, not a sign the retirement didn't happen.
    - **`interact(state, ds)`** handles three distinct taps: `nextStage`
      (advance the climb, vanish the next 20% — computed as
      `round(totalNonPunct * currentStage/totalStages)` so 20/40/60/80/
      100% land on exact word counts, not a fixed 1/5-per-stage
      remainder that could round unevenly), `complete` (the final-stage
      button, relabeled "I Recited It Perfectly!" — finalizes exactly
      like every other self-graded type), and `peekWord` (spec item 2's
      "tap an individual blank to reveal it for 1.5s") — the one truly
      new mechanic: sets `state.peekIndex`, then a real `setTimeout`
      clears it again and calls the global `render()` directly. A
      `peekToken` counter guards it (an earlier peek's timeout firing
      after a newer tap superseded it doesn't clobber the newer one),
      and the timeout checks `session.queue[session.index].state ===
      state` by object identity before re-rendering (interact() only
      receives `state`, not `session`/`item`, so this is the cheapest
      correct way to confirm the user hasn't since left this verse) —
      same shape as `autoAdvanceMs`'s own guarded timeout elsewhere in
      this file, applied to a new problem.
    - **"Hold to Peek"** (spec item 3's secondary button — reveal every
      vanished word while pressed) is deliberately NOT run through
      `interact()`/`render()` at all: `wireProgressiveVanish()` just
      toggles a `peek-all` CSS class on the box directly on
      `pointerdown`/`pointerup`/`pointercancel`/`pointerleave`. There's
      nothing to score or persist about a peek, and routing a
      press-and-hold gesture through a full re-render per press/release
      would add a visible delay to what should feel instant — same
      reasoning `wireFamilyTreePanZoom()`/`wireTimelineDrag()` already
      give for direct DOM manipulation during a live gesture, applied
      here to "hold" instead of "drag." Also set
      `-webkit-touch-callout:none`/`user-select:none` on that button —
      a "hold" gesture on mobile Safari can otherwise trigger a text-
      selection callout, a lesson worth applying up front this time
      rather than waiting for a real-device report the way items 114's
      two mobile bugs were found.
    - Emoji in the owner's own spec text ("👁️ Hold to Peek," "I Recited
      It Perfectly! 🎉") were replaced with the existing Tabler icon
      font (`ti-eye`, `ti-sparkles`) instead of literal emoji characters
      — consistent with the app-wide emoji-removal decision (item 107),
      which this would have directly reversed if followed literally.
    - Verified by simulation against real curated verses before
      shipping: 30 random verses stage-advanced through all 5 steps
      each landed on the exact 20/40/60/80/100% vanished-word counts
      with zero regressions (a word un-vanishing) and zero punctuation
      tokens ever vanishing, and every one reached completion.
    `sw.js` bumped to `rooted-v111`.

116. **"Biblical Fact of the Day" — done (2026-09-17), with real
    verification behind the badge, not just the UI.** The owner's own
    spec asked for a `verificationStatus: "Validated"` field and a
    "🛡️ Verified Source" trust badge on every fact — a real claim made
    to end users, not decoration. Flagged this before building anything:
    this app didn't have a Fact of the Day feature at all yet (no
    `data/daily_facts.json`, no card), so it wasn't actually an update
    to something existing, and the spec named two external sources
    ("OpenBible Geocoding Data," "Berean Standard Bible Text") this app
    has no integration with — shipping a "Validated"/"Verified" label
    over AI-written trivia that hadn't actually been checked against
    anything would have been presenting unverified content as fact-
    checked, the same category of problem this project has avoided
    before (declining the NIV PDF over licensing, checking every Church
    History date via web search before writing it in rather than
    trusting recall — item 90). Confirmed the approach with the owner
    first: hand-curate a small real batch, each fact checked against
    data this app already has and can be verified against directly,
    rather than against the two named external sources (neither is
    genuinely the basis for any of these facts, so per the owner's own
    "cite only where genuinely relevant" answer, neither is cited).
    - **`data/daily_facts.json`** — 10 facts, same flat-array shape and
      "hand-written editorial content, not part of the Bible-content
      curation pipeline" status as `word_of_the_day.json`/
      `church_history.json` (no `pipeline/curation/` source, no
      `build_*.py` step — edit this file directly). Every fact's
      `scriptureRef` was checked by directly querying this app's own
      `data/verses.json` (the real WEB corpus) for that exact reference
      and confirming the fact's claim against the actual returned verse
      text — not recalled from memory. Three facts (Ruth's, Rahab's, and
      Joseph's genealogies) also cross-check against already-curated
      `Character`/`Connection` data (the Joseph→Jesus adoptive-father
      connection added in item 112); one (the "younger son" pattern)
      cross-checks against the existing `motif_younger_son_chosen`,
      already 5 real instances deep in `data/motifs.json`. Two facts
      (Methuselah's age, the longest/shortest chapters) intentionally
      have no linked CTA at all — no curated character/story fits them,
      and forcing one would mean pointing at a destination that doesn't
      genuinely represent the fact, so they get none, matching Word of
      the Day's own "just don't show the chip" precedent for a verse
      that isn't in the curated library yet.
    - **`factOfTheDay()`** — identical date-seeded rotation shape to
      `wordOfTheDay()`; `renderFactOfTheDayCard()` on Home, positioned
      after Church History, before Unreached of the Day.
    - **`factLinkTarget(fact)`** resolves whichever one of
      `linkedCharacterId`/`linkedStoryId`/`linkedMotifId`/`linkedVerseId`
      a fact has set to a real action/label pair — a character routes to
      the existing Family Tree feature (item 110/111, reusing
      `familyTree`'s own `{id}` param unchanged), a story/motif/verse
      route to their own existing detail screens. No new navigation
      machinery — every destination already existed.
    - **This app's first bottom-sheet drawer.** Church History and
      Unreached of the Day both deliberately used a full screen instead
      of a modal, since the app otherwise has zero overlay components
      (documented reasoning in item 90). A single fact is lighter,
      secondary content than either of those — a quick peek-then-
      dismiss genuinely suits it better than a full navigation, so this
      one earns the new pattern rather than defaulting past the owner's
      explicit "bottom drawer" ask the way the full-screen precedent
      would have. `renderFactDrawer()` (backdrop + sheet, both
      `position:fixed`, above the bottom nav's own z-index), state
      `factDrawerOpen` (a fact id or `null`) rendered as part of
      `renderHome()`'s own output. Reset on every bottom-nav tap (not
      just the drawer's own close button or its CTA actions) so it can't
      silently reappear if the user switches tabs and later returns to
      Home with it still logically "open."
    - **The card and drawer use this app's existing dark-theme tokens
      throughout** (`--paper-raised`, `--gold-deep`, etc.) — NOT the
      separate bronze/obsidian palette the three new Practice challenge
      types introduced (items 113-115). No exact hex was given for this
      card's own surface the way it was for those, so "dark obsidian
      design system" reads here as "this app's existing v3 dark theme,"
      not a request for a third, subtly-different dark palette. The one
      literal, scoped exception is the "Verified Source" badge's
      emerald (`#10B981`) — a real, distinct trust signal worth standing
      out visually, same reasoning as every other exact-hex spec this
      session being scoped to its own classes rather than folded into
      shared tokens.
    - Emoji in the spec text (🛡️, 📖) were replaced with the existing
      Tabler icon font (`ti-shield-check`, `ti-book-2`), consistent with
      the app-wide emoji-removal decision (item 107).
    `sw.js` bumped to `rooted-v112` (`data/daily_facts.json` added to
    the precache list alongside the other two Home-editorial data
    files).

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
