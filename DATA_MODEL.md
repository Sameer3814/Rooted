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

### Character — *live* (17 Genesis characters)
```json
{
  "id": "char_jacob",
  "name": "Jacob",
  "alsoKnownAs": ["Israel"],
  "roles": ["renamed Israel", "father of the twelve tribes"],
  "eraId": "era_patriarchs",
  "summary": "Isaac and Rebekah's younger twin...",
  "relationships": [{ "characterId": "char_esau", "type": "brother of" }],
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
- `relationships[]` is still an embedded array; it **moves to Connection**
  eventually. This is the textbook case for the generic entity: the links are
  typed ("son of"), directional, browsable in their own right, and will grow
  notes. See §8.4.
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
  inserted without renumbering. Not a claim about exact dates.
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

### Motif — *planned*
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
  "verse"`, `relationship: "instance of"`. No separate MotifInstance entity;
  this is the deliberate demonstration of the generic-Connection pattern.

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

### Connection — *planned* (the generic relationship entity)
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
- `fromType` / `toType` are entity-type strings: `character`, `story`, `verse`,
  `topic`, `motif`, `era`.
- What belongs in Connection: anything typed with a label, anything carrying
  `notes`, anything the user browses as a relationship itself, motif instances,
  story→story (foreshadows / parallels / fulfilled by), typed topic→topic.
- What stays an embedded id array: plain membership/tagging lookups the UI does
  constantly — `Verse.topicIds`, `Verse.characterIds`, `Story.verseIds`,
  `Character.storyIds`, etc.

---

## 3. Challenge system — *partial* (interface + 2 types: fill-in-blank, scramble)

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
  build, render, check, score, /* interact? */   // the interface below
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
| `score(state)` | → number 0..1 (fraction correct). Called after `check`. |
| `interact(state, ds)` | *optional.* Handles a tap on an element the type rendered with `data-action="practice-interact"` (`ds` = that element's `dataset`). Mutates `state`; the flow re-renders. Used by scramble for tap-to-place; unused by fill-in-blank (native inputs). |

Session shape: `{ challengeTypeId, queue:[{verseId, state}], index, results:[{verseId, allCorrect, score}] }`.
`startPractice(verseIds, challengeTypeId)` — `challengeTypeId` defaults to
`settings.challengeTypeId` (persisted to `rooted-settings`; chosen via the
segmented picker on Home, shown whenever ≥2 verse types are `enabled`).

**challenge_scramble** — words become tappable chips; tap to place in order,
tap a placed chip to return it. For verses longer than `config.maxWords` (14)
only a random contiguous window is scrambled and the rest shown as fixed
context, so long verses stay playable.

Planned types (all `appliesToEntityTypes: ["verse"]` unless noted):
`challenge_fill_blank` (built), `challenge_scramble` (built),
`challenge_first_letters` (progressive reveal), `challenge_type_it_out`,
`challenge_reference_match`, `challenge_story_order` (`["story"]`),
`challenge_character_match` (`["character"]`). Adding one = a new registry
entry, nothing else.

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
| `data/starter-pack.json` | curated first-run seed: 230 verses + 27 topics + 11 characters | loaded on first run; **generated** by `build_starter_pack.py` |
| `pipeline/curation/starter_pack.json` | the hand-curation behind the above | verse ids + topic/character links + the Topic and Character records; **never** verse text |
| `pipeline/curation/topic_lexicon.json` | keyword hints per topic | input to `tag_verses.py` only; never becomes tags |
| `data/verses.json` | full parsed WEB corpus (3,994 verses, Genesis + Psalms) | **generated** by `parse_books.py`; lazily fetched by the Browse screen on first open, then held in memory (`corpus`) |
| `data/characters.json` | standalone Genesis characters | **generated** by `build_starter_pack.py` from the same curation; not read by the app |
| `data/stories.json` | 3 eras, 32 stories, 85 life events | **generated** by `build_stories.py`; loaded at boot (small) |
| `data/motifs.json` | *planned* | Motif seed |
| `data/connections.json` | *planned* | Connection seed (incl. migrated character relationships) |
| `media/` | *planned* | illustration assets referenced by Media entities |
| `window.storage: rooted-content` | user overlay `{ verses, topics, characters }` | **done** — merged over seed by id at load (`mergeContent`); only written once the user adds/edits something |
| `window.storage: rooted-progress` | map of `verseId → VerseProgress` | **done** — §7 |
| `window.storage: rooted-sessions` | practice session log | planned — optional / trimmable |
| `window.storage: rooted-journal` | discovery journal entries | planned — §7 |
| `window.storage: rooted-settings` | preferences (`challengeTypeId` so far; depth, goals planned) | *partial* — §7, `saveSettings()` |
| `window.storage: rooted-app-data` | pre-split single blob | legacy — migrated once on boot by `migrateLegacy`, then ignored |

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
  interval ladder already in `scheduleNext`).
- Stored as a map keyed by `verseId` under `rooted-progress`. A verse with no
  entry is treated as `new`.

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
  pulls (`practiceQueue`), so the 230-verse seed doesn't all come due at once on
  a fresh install. No UI to change it yet; Home shows "Practice 10 of 230 due".
- `activeDepth` — planned (§4).

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
4. **`Character.relationships[]` → Connection.** Create `data/connections.json`,
   move the ~20 embedded edges, add `symmetric` / `inverse`. Update the
   character detail screen to read Connections.
5. ~~**Factor fill-in-blank into the ChallengeType interface** (§3) before adding
   scramble.~~ **Done (2026-09-03).** `CHALLENGE_TYPES` registry;
   `buildBlanks`/hardcoded practice flow replaced by `build/render/check/score`.
   Also fixed: typed answers no longer vanish from the blanks after "Check".
   Then **`challenge_scramble` added** as a second registry entry (2026-09-03)
   — validated the interface: only new code was the registry entry, the
   optional `interact` hook, a `set-challenge` action, and the Home picker.
   Introduced `rooted-settings` (§7) for the persisted type choice.
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

10. ~~**`Story` / `Era` / `LifeEvent` entities.**~~ **Done (2026-09-04).**
    3 eras, 32 stories, 85 life events. Character detail now leads with a
    **timeline** ("Their life"), then Family (the `relationships[]` data, which
    had never been rendered), Stories, Key verses, "Appears alongside"
    (co-occurrence) and "Also in <era>". New Story detail screen and a Stories
    list grouped by era, reached from People. See §9.

9. **Topic tagging at scale.** **Done (2026-09-03).** Seed grew from 17 verses /
   15 topics to **230 verses / 27 topics / 270 tag assignments**, every topic
   carrying 6–14 hand-picked verses, every Topic now with a real `description`
   and populated `relatedTopicIds` (the topic-to-topic graph the vision asks
   for). Approach: `tag_verses.py` surfaces candidates from a keyword lexicon,
   a human picks — see §6. Genesis verses also gained `characterIds`, so
   character detail pages went from 0–2 verses to up to 18.

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
| "Appears alongside" | shared `LifeEvent.participantIds` / `Story.characterIds` — real co-occurrence, not an era guess |
| "Also in <era>" | `Character.eraId`, and only for people *not* already listed above |
| A topic's verses | `Verse.topicIds` |
| Verses due today | `rooted-progress` + `isDue`, capped by `settings.dailyGoal` |

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
