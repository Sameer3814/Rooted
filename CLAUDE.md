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
  Screens: Home, Verse detail, Topics, Topic detail, Characters,
  Character detail, Add Verse, Add Character, Practice (fill-in-blank
  only so far).
- `manifest.json` + `sw.js` — installable PWA (add-to-homescreen, offline
  shell caching).
- `icon.png` — placeholder app icon (simple generated shape, not final art).
- `data/starter-pack.json` — the curated seed content the app loads on
  first run: 17 verses (Genesis + Psalms, WEB translation) tagged with
  topics and linked to characters, plus 10 Genesis characters with real
  relationships (father of, wife of, brother of, etc.).
- `data/characters.json` — same 10 Genesis characters, standalone.
- `data/verses.json` — the **full** parsed Genesis + Psalms corpus (~3,994
  verses, WEB translation, public domain). This is NOT loaded into the app
  yet — it's proof the import pipeline scales, waiting on topic tagging,
  UI for browsing at that scale (search/pagination), before it's wired in.
The import pipeline that produced `verses.json` and `starter-pack.json` is
**not currently in the repo** (`pipeline/parse_books.py` +
`pipeline/build_starter_pack.py` existed at one point but were never
committed). If the corpus needs regenerating or extending, the pipeline
has to be rewritten:
- `parse_books.py` — parsed raw WEB Bible JSON (from the
  `TehShrike/world-english-bible` GitHub repo, public domain / CC0) into
  our verse schema. Handled both prose books (Genesis-style "paragraph
  text") and poetic books (Psalms-style "line text" grouped by verse).
- `build_starter_pack.py` — picked specific verse IDs out of the full
  parsed corpus, attached topics/character links by hand, wrote
  `starter-pack.json`.

User data (verses/characters the user adds, and all practice progress) is
stored separately via the in-app persistence API (`window.storage`,
personal/non-shared) — never mixed into the seed/starter-pack files.

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
4. **Connections should eventually be a generic entity** —
   `{ fromId, fromType, toId, toType, relationship, notes }` — rather than
   relationship arrays embedded separately in Character and Story. The
   current `characters.json` uses an embedded `relationships[]` array as
   a shortcut for the MVP; if a `Story` or `Topic-to-Topic` connection
   system gets built, prefer migrating to the generic Connection shape
   rather than adding more embedded arrays.
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

1. Split content from user-state in storage, and drop the `progress` stub
   from the seed files (`DATA_MODEL.md` §8.1). Currently everything is one
   `rooted-app-data` blob.
2. More challenge types beyond fill-in-blank — first factor the existing
   one into the pluggable ChallengeType interface (`DATA_MODEL.md` §3),
   then add scramble / progressive reveal / matching / ordering.
3. Rebuild the `pipeline/` scripts (gone from the repo) and add structured
   `book`/`chapter`/`verse` fields to the Verse schema.
4. Wiring the full `verses.json` corpus into the app (needs search/browse
   UI, since dumping ~4,000 verses into one list is not usable as-is).
5. Topic tagging at scale for the full corpus (currently only the 17
   starter verses are tagged).
6. `Story` / `Era` / `LifeEvent` entities — needed for the character
   timeline/"highlights of their life" feature and parallel-story
   connections.
7. The generic `Connection` entity (Design philosophy #4) — migrate
   `Character.relationships[]` to it first.
8. Real character portrait illustrations in the warm-storybook style
   (currently icon placeholders); `Media` entity designed, not built.
9. Expanding character/relationship data beyond Genesis to other OT books.
10. `data/characters.json` is currently dead weight (duplicates the
    characters embedded in `starter-pack.json`) — wire it in or delete it.

## Source data provenance

WEB Bible text: parsed from the `TehShrike/world-english-bible` GitHub
repository (public domain / CC0 JSON). If re-pulling or updating this
data, re-verify the source is still public domain before reproducing
verse text in bulk — this reasoning does NOT extend to copyrighted
translations (see NIV note above).
