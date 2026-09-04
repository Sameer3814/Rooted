# Rooted — Scripture Memory App

A personal project: a mobile-first app to memorize scripture through fun,
challenge-based practice (fill-in-blank, scramble, speed recall, progressive
reveal) — and eventually a much bigger tool for exploring how Bible
characters, stories, topics, and cultural context connect to each other.

This file is context for whoever (human or Claude) picks this project up
next. Read it before making structural changes.

**`DATA_MODEL.md`** holds the full schema for every entity — including the
vision features not yet built. Read it before changing any data shape, and
update it in the same pass as any schema/data change (this applies to all
`.md` docs: keep them in sync with the code).

## The vision (long-term, bigger than current code)

The owner's goal isn't just verse memorization — it's a study companion:

- Memorize verses through active, game-like challenges (not passive reading)
- Practice by **topic** (anger, greed, lust, forgiveness...), where topics
  connect to each other (greed relates to contentment, envy, etc.), not a
  flat tag list
- Explore **Old Testament characters and stories** and how they connect —
  family trees, "who else lived at this time," parallel/foreshadowing
  stories, cultural context
- A **person search / deep-dive view**: search a character, see life
  highlights as a timeline, contemporaries, and parallel stories happening
  at the same time
- A **warm, polished, illustrated UI** — this is meant to be genuinely fun
  and visually pleasant to use daily, not a bare-bones flashcard tool
- Eventually: pattern-recognition challenges (recurring biblical motifs —
  younger-son-chosen, exile-and-return, etc.), a personal "discovery
  journal" of connections the user notices themselves, and difficulty/depth
  layers (Sunday-school vs. seminary depth)

None of that is fully built yet. What exists now is a working MVP slice.
The schema was deliberately designed so all of the above can be added
**additively** — see "Design philosophy" below before changing it.

## Current state (what's actually built)

- `DATA_MODEL.md` — the full entity schema (design pass; covers built and
  not-yet-built entities). Not code, but load-bearing documentation.
- `index.html` — the entire app (vanilla JS, no framework, no build step).
  Screens: Home, Browse (search/drill the full corpus), Verse detail,
  Topics, Topic detail, People (grouped by era), Character detail
  (life timeline, family, stories, pattern badges), Stories list,
  Story detail (related stories, pattern badges), Patterns list,
  Pattern detail, Add Verse, Add Character, Practice (three challenge
  types: fill-in-blank, scramble, and self-graded progressive reveal).
- `manifest.json` + `sw.js` — installable PWA (add-to-homescreen, offline
  shell caching).
- `icon.png` — placeholder app icon (simple generated shape, not final art).
- `data/starter-pack.json` — the curated seed content the app loads on
  first run: **247 verses** (Genesis, Psalms and Exodus 2-4, WEB
  translation) across **28 topics** (topics linked to related topics),
  plus **23 characters** (17 Genesis, 6 early Exodus) with real
  relationships (father of, wife of, brother of, etc. — see Connection,
  below).
- `data/characters.json` — the same 23 characters, standalone. Generated
  from the same curation as the starter pack, but not read by the app.
- `data/verses.json` — the **full** parsed corpus: Genesis, Psalms, and
  Exodus (5,207 verses, WEB translation, public domain). Lazily fetched by
  the Browse screen the first time it's opened, never at boot. It is
  *reference material*, kept separate from the user's library — adding a
  verse from Browse copies it into the user's overlay. Only the 247 seed
  verses are topic-tagged; the rest of the corpus isn't yet.
- `data/stories.json` — 4 eras, 36 stories and 105 life events (Genesis
  plus Moses' early life in Exodus). Loaded at boot (it's small). Drives
  the character life timeline, the Stories screens, People-grouped-by-era,
  and "appears alongside".
- `data/motifs.json` — 5 recurring biblical patterns (younger son chosen,
  meeting a spouse at a well, "I am with you", the deceiver deceived, a
  child's life threatened and delivered), each with 3 real instances in
  the current content — not force-fit onto single occurrences. Loaded at
  boot. Drives the Patterns screens and the "Pattern" badges on Character
  and Story pages.
- `data/connections.json` — 50 generic Connection edges (Design philosophy
  #4): family relationships, motif instances (`motif` → `story` /
  `character` / `verse`), and the first story↔story link (`"parallels"`).
  Loaded at boot.
- `pipeline/` — regenerates everything in `data/`. See `pipeline/README.md`.
  - `parse_books.py` — WEB Bible JSON (`TehShrike/world-english-bible`,
    public domain / CC0) → `data/verses.json`. Handles prose books
    (Genesis-style "paragraph text") and poetic books (Psalms-style "line
    text" grouped by verse). Knows all 66 book slugs; `--all` does the
    whole Bible.
  - `build_starter_pack.py` — joins `pipeline/curation/starter_pack.json`
    (hand-picked verse ids + topic/character links + the Topic and
    Character records) against the corpus → `data/starter-pack.json` and
    `data/characters.json`. Validates every cross-reference.
  - `build_stories.py` — `pipeline/curation/stories.json` →
    `data/stories.json`. Validates every era/story/character/participant/
    topic/verse reference and every `sequenceInLife`.
  - `build_motifs.py` — `pipeline/curation/motifs.json` →
    `data/motifs.json`. Requires >=2 `exampleReferences` per motif — one
    occurrence is just a fact about that story, not a pattern.
  - `build_connections.py` — `pipeline/curation/connections.json` →
    `data/connections.json`. Requires `inverse` or `symmetric` on every
    edge so a reverse view is never silently missing; rejects the same
    fact stored twice. Run after build_stories.py and build_motifs.py —
    it validates against their output.
  - `tag_verses.py` — curation aid that **writes nothing**: surfaces
    candidate verses per topic from `curation/topic_lexicon.json` so a
    human can hand-pick. Topic tags are curated, never generated —
    auto-tagging the corpus was considered and rejected (keyword matching
    can't read metaphor; "fear of Yahweh" is reverence, not anxiety).

**`data/*.json` is generated — never hand-edit it.** Verse text lives only
in the corpus; the curation file holds selection and links, not a copy of
the text.

User data is stored separately via the in-app persistence API
(`window.storage`, personal/non-shared), under two keys, never mixed into
the seed files:
- `rooted-content` — verses/topics/characters the user adds or edits, as an
  overlay merged over the seed by id at load. Only written once the user
  changes something.
- `rooted-progress` — a `verseId → VerseProgress` map (status, review
  schedule, practice history).
A pre-split `rooted-app-data` blob (content + progress together) is
migrated once on first boot, then ignored. See DATA_MODEL.md §5, §7, §8.1.

## Translation and copyright — important, don't undo this

- Core dataset is the **World English Bible (WEB)** — public domain, free
  to use in full. This was a deliberate choice.
- The user asked about using the **NIV** from a PDF they'd provide. That
  was declined: NIV is copyrighted by Biblica, and bulk-embedding full
  text into an app's local database requires a license from Biblica
  regardless of personal-use intent. If NIV support becomes a real
  requirement, the path is Biblica's official licensing/API program, not
  scraping or reproducing text from a PDF.
- If multiple translations are added later, keep translation as a field on
  Verse (already there) rather than assuming WEB everywhere in code.

## Design philosophy (read before changing the data model)

Decided deliberately, in order to make future features additive rather
than requiring rewrites. `DATA_MODEL.md` turns these principles into
concrete per-entity schemas — this section is the "why," that file is
the "what."

1. **Open strings over hardcoded enums.** `Character.roles`,
   relationship `type` strings, etc. are free-form data, not fixed code
   enums. New roles/relationship kinds should just be new data.
2. **Generic `metadata` bag** on entities for speculative future fields —
   use it before adding a first-class schema field for something unproven.
3. **Media is a separate linked entity**, not embedded fields on
   Character/Story — so art style, multiple images, dark-mode variants,
   etc. can be added without touching content.
4. **Connections are a generic entity** —
   `{ fromType, fromId, relationship, toType, toId, symmetric|inverse, notes }`
   — rather than relationship arrays embedded separately per entity type.
   **Live since 2026-09-04** (`data/connections.json`, `pipeline/curation/
   connections.json`, `build_connections.py`): `Character.relationships[]`
   was the MVP shortcut this was always meant to replace. Now also carries
   Motif instances (`motif` → `story`/`character`/`verse`) and the first
   `Story`-to-`Story` link (`"parallels"`). A future `Topic`-to-`Topic`
   connection system goes here too — don't add another embedded array.
5. **Challenge types should be pluggable**, described by data
   (`appliesToEntityTypes`, etc.) rather than a hardcoded switch — only
   fill-in-blank exists right now; when adding scramble/speed
   recall/progressive reveal/matching, look for a shared generator
   pattern rather than one-off functions per type.
6. **Progress/user-state is always separate from content.** Never mix
   `progress` tracking into the same object identity as shared/seed
   content in a way that would make resetting progress destroy content.
7. **IDs are stable, type-prefixed strings** (`char_david`,
   `verse_genesis_1_1`), not auto-increment numbers — this matters once
   bulk-imported data and hand-curated data need to merge without
   collisions.

## Visual direction — decided, don't relitigate without asking

Style: **warm storybook.** Rounded cards, warm gold/sage/plum accent
palette on a cream background, Fraunces (serif) for verse text and
headings, Inter (sans) for UI text, Tabler icon font for
placeholder "portraits" until real character illustrations exist.
Two other directions (minimal/modern, rich/classical) were shown and
explicitly rejected in favor of this one.

## Known gaps / not-yet-built (in likely priority order)

The full schema for all of the below (including the not-yet-built
entities) is designed in `DATA_MODEL.md`; §8 there is the current→target
migration checklist. Approach agreed with the owner (2026-09-03): design
the whole data model up front, then build in vertical slices — do **not**
hand-curate all the content before building.

1. More challenge types. Three built (`CHALLENGE_TYPES` in `index.html`,
   `DATA_MODEL.md` §3): fill-in-blank, scramble, and self-graded
   `challenge_first_letters`, with a Home picker persisted to
   `rooted-settings`. Next: matching / ordering (`challenge_story_order`,
   `challenge_character_match`).
2. Real character portrait illustrations in the warm-storybook style
   (currently icon placeholders); `Media` entity designed, not built.
3. ~~Expanding character/relationship data beyond Genesis to other OT
   books.~~ **Started (2026-09-04).** Moses' early life (Exodus 2-4): era,
   6 characters, 4 stories, 20 life events, 8 connections, 17 verses,
   1 new topic (`topic_deliverance`). `parse_books.py --all` makes the
   text side trivial for any further book; the curation/content side is
   still real work per book.
4. A UI for `settings.dailyGoal` (currently a fixed default of 10).
5. ~~`Motif` entity, and story→story Connections (foreshadows/parallels).~~
   **Done (2026-09-04).** 5 motifs, each with 3 real instances — see
   `data/motifs.json` above. Only one story↔story Connection so far
   (`"parallels"`); more will accumulate as content grows.

**Done (2026-09-03):** content/user-state storage split + `progress`
removed from seed files (`DATA_MODEL.md` §8.1); structured
`book`/`chapter`/`verse` fields (§8.2); pluggable ChallengeType interface +
fill-in-blank factored in + `challenge_scramble` added, with a persisted
Home picker (§8.5); `window.storage`→localStorage fallback for local dev;
`pipeline/` rebuilt (§8.7); Browse screen wiring the full corpus into the
app (§8.8); topic tagging at scale — 17→230 seed verses, 15→27 topics
(§8.9).

**Done (2026-09-04):** `Story`/`Era`/`LifeEvent` — eras, stories, life
events, character life timelines, Story screens, People grouped by era,
`Character.era`→`eraId` (§8.3, §8.10). `Character.roles` rewritten so they
actually distinguish people — three men all reading "patriarch" told the
reader nothing. The generic `Connection` entity (§8.4) — replaced 51
embedded `relationships[]` entries with directed edges (most facts had
been stored twice, once per direction); the migration's validation also
caught a real gap in the old data (Abraham→Hagar had no reverse entry) and
fixed it for free. Content expanded beyond Genesis for the first time —
Moses' early life (Exodus 2-4): new era, 6 characters, 4 stories, 20 life
events, 8 connections, 17 verses, 1 new topic (`topic_deliverance`); the
full corpus now also includes Exodus (5,207 verses total). Then a third
challenge type, `challenge_first_letters` — first letters shown, tap
Reveal, self-grade Got it / Missed it. Needed two small, backward-compatible
additions to the ChallengeType interface (`controls()` for a non-Check
action area, `interact()` allowed to finalize grading itself) —
self-grading doesn't fit the "one auto-graded tap" shape fill-in-blank
and scramble share. Then the `Motif` entity — 5 patterns, each with 3 real
instances (not force-fit onto single occurrences; the builder rejects
motifs with fewer), plus the first story↔story Connection. Both fell out
of `connectionsFor()` with zero new query machinery, which is exactly what
making Connection generic back on 2026-09-04 was for.

## Source data provenance

WEB Bible text: parsed from the `TehShrike/world-english-bible` GitHub
repository (public domain / CC0 JSON). If re-pulling or updating this
data, re-verify the source is still public domain before reproducing
verse text in bulk — this reasoning does NOT extend to copyrighted
translations (see NIV note above).
