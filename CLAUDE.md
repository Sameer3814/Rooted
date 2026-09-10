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
- Explore **Bible characters and stories** and how they connect — family
  trees, "who else lived at this time," parallel/foreshadowing stories,
  cultural context (the content was Old-Testament-only through
  2026-09-10; the New Testament curation started the same day, owner's
  direction, and follows the same additive design)
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
- `index.html` — the entire frontend (vanilla JS, no framework, no build
  step). Screens: Home, Browse (search/drill the full corpus), Verse
  detail, Topics, Topic detail, People (grouped by era), Character detail
  (life timeline, family, stories, pattern badges), Stories list,
  Story detail (related stories, pattern badges), Patterns list,
  Pattern detail, Add Verse, Add Character, Practice (four challenge
  types: fill-in-blank, scramble, self-graded progressive reveal, and
  self-graded verse ladder),
  and **Settings** (gear icon, top-right of Home) — the account bar for
  optional cloud sync and the "Your data" export/import card live here,
  not on Home. They started on Home (2026-09-08) and were moved the same
  day on direct feedback: sync/backup controls are occasional-use, and
  were pushing the actual daily-use content (due-today stats, the
  Practice button) below the fold. Lesson for anything added later in
  this vein — account/settings-shaped features default to Settings, not
  Home, unless there's a specific reason a control needs daily visibility.
- **Streaks and brand mastery labels — done (2026-09-08), relabeled
  2026-09-09.** First of the Tier 1 engagement features. Home's stat row
  gained a "day streak" card — a pure derived view over
  `VerseProgress.history[]`, no new storage. `VerseProgress.status` now
  always displays through brand labels — plant-growth emoji stages as of
  the 2026-09-09 pass: 🌱 Seedling → 🌿 Sprouting → 🌳 Rooted → 👑
  Flourishing (superseded the original 2026-09-08 text-only naming,
  where "Rooted" was the *learning* tier and "Mastered" was plain text —
  see DATA_MODEL.md §32). Every verse card now shows its stage tag, not
  just mastered/due ones. (A practice-activity heatmap shipped alongside
  the original pass, then got pulled the next day on feedback — see
  known gaps.) See DATA_MODEL.md §7/§27/§32.
- **People search — done (2026-09-09).** Live-filter search on the
  People screen, matching by name or role, mirroring Browse's existing
  debounced-search pattern exactly (own `#people-results` subtree, own
  `peopleQuery` state) rather than inventing a new one. See
  DATA_MODEL.md §30.
- **`settings.dailyGoal` UI — done (2026-09-09).** A 5/10/15/20/25 preset
  picker on Settings, reusing the existing `.segmented` chip component
  (the same one Home's challenge-type picker uses) instead of a
  free-typed number input. See DATA_MODEL.md §7/§31.
- **Dynamic/tactile UX pass — done (2026-09-09).** "Feel like Duolingo,
  keep warm storybook." Springy `scale(.96)` press feedback on every
  tappable surface (one shared CSS rule); a daily-goal progress ring on
  Home (`renderGoalRing()`, no new storage); a rewritten session-complete
  screen — slide-up entrance, bounced-in icon, staggered animated stats,
  a small CSS-only spark burst (no `<canvas>`, no per-frame JS); and
  `playSfx()`/`hapticBuzz()` — synthesized Web Audio tones + vibration,
  gated by one new "Sound & haptics" toggle on Settings (default on).
  Also caught and fixed a real latent bug while rewriting the completion
  screen: a background render (e.g. cloud sync landing) between finishing
  a session and tapping "Done" used to silently reset the shown tally to
  "0/0 correct." A full `prefers-reduced-motion` override disables the
  new animations. See DATA_MODEL.md §32 for everything, including the
  mastery-label relabel this pass also did (noted above).
- `manifest.json` + `sw.js` — installable PWA (add-to-homescreen, offline
  shell caching).
- `icon.png` — placeholder app icon (simple generated shape, not final art).
- **Live deployment, hosting, and cloud sync — done (2026-09-06).** The
  frontend still has zero build step, but the *repo* now does (see below):
  - Hosted on **Azure Static Web Apps (Free tier)**:
    https://calm-mushroom-0ebd30c10.6.azurestaticapps.net — auto-deploys on
    every push to `master` via `.github/workflows/azure-static-web-apps-
    calm-mushroom-0ebd30c10.yml` (Azure-generated, don't rename/regenerate
    without updating the API location it points at). `staticwebapp.config.json`
    blocks `/.git/*` and `/pipeline/.cache/*`, sets `sw.js` to `no-cache`
    so PWA updates roll out immediately, and gates `/api/*` to signed-in
    users.
  - `api/` — the app's first backend: an Azure Functions app (Node.js,
    v4 programming model — this folder *does* have a build step,
    `npm install`, handled by Azure's deploy action; the static frontend
    doesn't). One endpoint, `GET/POST /api/sync` (`api/src/functions/sync.js`),
    backed by **Azure Cosmos DB for NoSQL (Free tier — free forever, not a
    trial)**, one document per signed-in user. See DATA_MODEL.md §7.1 for
    the full design (merge strategy, security boundary, why sign-in is
    optional).
  - Auth is **GitHub**, via Static Web Apps' built-in pre-configured
    provider (`/.auth/login/github` — zero OAuth-app registration). Chosen
    for zero setup, explicitly not locked in — switching providers later
    is supported by the platform, though note each provider yields a
    different `userId` for the same person (§7.1), so it's not seamless
    account migration.
  - GitHub repo: https://github.com/Sameer3814/Rooted (public). Pushes
    from this session go over a dedicated SSH deploy key
    (`~/.ssh/rooted_github_personal`, host alias `github-personal`) set up
    specifically so a work laptop's GitHub Desktop (signed into a work
    account) never needs to touch this personal project.
- `data/starter-pack.json` — the curated seed content the app loads on
  first run: **1,293 verses** — the entire Old Testament plus the New
  Testament as it's curated (started 2026-09-10; see `DEFAULT_BOOKS` in
  `parse_books.py` for the exact book list, "Known gaps" item 9 for how
  the NT is being approached, and DATA_MODEL.md §8 for the full,
  current per-book/per-era breakdown of everything below — this section
  intentionally stopped enumerating every book by name once the count
  made that unsustainable to keep current) — across **38 topics**
  (topics linked to related topics), plus **161 characters** with real
  relationships (father of, wife of, brother of, successor of, servant
  of, worked alongside, raised, etc. — see Connection, below). Note:
  fictional figures inside Jesus's parables (the good Samaritan, the
  prodigal son, etc.) do **not** get Character records — only real,
  named/identifiable people do, same as every OT figure.
- `data/characters.json` — the same 161 characters, standalone. Generated
  from the same curation as the starter pack, but not read by the app.
- `data/verses.json` — the **full** parsed corpus: the entire Old
  Testament plus the New Testament books curated so far (26,923 verses,
  WEB translation, public domain), matching `DEFAULT_BOOKS` in
  `parse_books.py`. Lazily fetched by the Browse screen the first time
  it's opened, never at boot. It is *reference material*, kept separate
  from the user's library — adding a verse from Browse copies it into
  the user's overlay. Only the 1,293 seed verses are topic-tagged; the
  rest of the corpus isn't yet.
- `data/stories.json` — 16 eras, **236 stories and 528 life events**.
  All 12 OT eras plus the New Testament's `era_birth_of_jesus` and
  `era_jesus_ministry` so far (see DATA_MODEL.md §8 for what's in each
  era — kept current there, not duplicated here). Loaded at boot (it's
  small). Drives the character life timeline, the Stories screens,
  People-grouped-by-era, and "appears alongside".
- `data/motifs.json` — **20** recurring biblical patterns, each with real
  instances in the current content, not force-fit onto single
  occurrences (see DATA_MODEL.md §8 for the newest). Loaded at boot.
  Drives the Patterns screens and the "Pattern" badges on Character,
  Story, and Verse detail pages.
- `data/connections.json` — 135 generic Connection edges (Design
  philosophy #4): family relationships, motif instances (`motif` →
  `story` / `character` / `verse`), and story↔story links
  (`"parallels"`, `"contrasts with"`). Loaded at boot.
- `pipeline/` — regenerates everything in `data/`. See `pipeline/README.md`.
  - `parse_books.py` — WEB Bible JSON (`TehShrike/world-english-bible`,
    public domain / CC0) → `data/verses.json`. Handles prose books
    (Genesis-style "paragraph text") and poetic books (Psalms-style "line
    text" grouped by verse). Knows all 66 book slugs; `--all` does the
    whole Bible. All 39 Old Testament books are in the default set
    (curated as of 2026-09-10), plus the New Testament books curated so
    far — Matthew, Mark, Luke, John as of the birth-of-Jesus pass.
    `DEFAULT_BOOKS` should only grow to match what's actually curated,
    not what's merely been read (see `pipeline/README.md`'s lessons for
    why — this bit the wisdom-books pass once already).
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

Style: **warm storybook.** Rounded cards, warm gold/sage/tan accent
palette on a cream background, Fraunces (serif) for verse text and
headings, Inter (sans) for UI text, Tabler icon font for
placeholder "portraits" until real character illustrations exist.
Two other directions (minimal/modern, rich/classical) were shown and
explicitly rejected in favor of this one.

**Visual system v2 — done (2026-09-09), refined same day (v2.1).** The
direction above is unchanged; this was an execution pass, not a
redirection, in response to "doesn't look like a polished app in the
market... looks basic." Surface elevation replaced hard 1px borders
(soft `box-shadow`, pure-white card fills on a warm linen `#F3EFE6`
ground — deepened once more in the v2.1 follow-up), the accent palette
collapsed from four colors to three clear roles (gold = action/urgency,
sage = progress/mastery, tan = plain metadata — **plum is retired**, not
recolored), book/people/**topics** lists became borderless
hairline-divided rows instead of full cards, character and story detail
pages open on a real hero header instead of a cramped 56px icon box, and
the bottom nav now floats as a frosted, rounded overlay instead of a
flush bottom bar (its `padding-bottom` clearance was under-sized in v2
and clipped content on a real device — fixed in v2.1). Full rationale,
every token's exact value, and which call sites changed: see
DATA_MODEL.md §29.

## Known gaps / not-yet-built (in likely priority order)

The full schema for all of the below (including the not-yet-built
entities) is designed in `DATA_MODEL.md`; §8 there is the current→target
migration checklist. Approach agreed with the owner (2026-09-03): design
the whole data model up front, then build in vertical slices — do **not**
hand-curate all the content before building.

1. More challenge types. Four built (`CHALLENGE_TYPES` in `index.html`,
   `DATA_MODEL.md` §3): fill-in-blank, scramble, self-graded
   `challenge_first_letters`, and self-graded `challenge_verse_ladder`
   (progressive word-stripping across 5 stages, 2026-09-09 — a Tier 1
   engagement feature), with a Home picker persisted to `rooted-settings`.
   Next: reference↔text matching (`challenge_reference_match`, next Tier 1
   item), then matching/ordering (`challenge_story_order`,
   `challenge_character_match`).
2. Real character portrait illustrations in the warm-storybook style
   (currently icon placeholders); `Media` entity designed, not built.
3. ~~**Expanding beyond Genesis to other OT books, in canonical
   order.**~~ **Done — the entire Old Testament is curated
   (2026-09-10).** Owner's direction, 2026-09-04: work through the rest
   of the OT in Bible book order (Ruth stayed where it landed earlier).
   Built one book (or small book-group) at a time — Exodus, Leviticus,
   Numbers, Deuteronomy, Joshua, Judges, 1–2 Samuel, 1–2 Kings, 1–2
   Chronicles (scoped to Chronicles-*unique* material since it retells
   Samuel–Kings — DATA_MODEL.md §8.24), Ezra/Nehemiah (genuinely new
   narrative — §8.25), Esther (own era, `era_esther`, placed by Bible
   order rather than strict chronology — §8.26) — closing out the
   historical narrative books — then, in one continuous push
   (2026-09-10, owner's direction: finish the rest in one go): Job (own
   era, `era_job`, since it's undated and outside Israel's own history —
   §8.27), Proverbs/Ecclesiastes/Song of Solomon (light
   verses-and-topics pass, no narrative), Isaiah, Jeremiah/Lamentations,
   Ezekiel, Daniel (§§8.36–8.39 respectively — each reused an *existing*
   era by story-level date rather than inventing new ones, and extended
   existing stories instead of duplicating retold material, e.g. Isaiah
   36-39 / 2 Kings 18-20), and finally the Twelve — Hosea, Joel, Amos,
   Obadiah, Jonah, Micah, Nahum, Habakkuk, Zephaniah, Haggai, Zechariah,
   Malachi (§8.40) — closing the book. `DEFAULT_BOOKS` in
   `parse_books.py` now lists all 39 OT books; `data/verses.json` is the
   complete Old Testament (23,145 verses). Full per-book detail is in
   the "Done" changelog below and DATA_MODEL.md §8, items 18–39.
   Repeatable playbook for any future canon expansion (era → characters
   → stories/events → verses/topics → connections/motifs for
   narrative-heavy stretches; lighter verses-and-topics-first for
   law/oracle/wisdom-heavy ones, established with Leviticus).
4. ~~A UI for `settings.dailyGoal`.~~ **Done (2026-09-09).** A 5/10/15/20/25
   preset picker on the Settings screen, reusing the existing `.segmented`
   chip component. See DATA_MODEL.md §7/§31.
5. ~~`Motif` entity, and story→story Connections (foreshadows/parallels).~~
   **Done (2026-09-04).** 5 motifs, each with 3 real instances — see
   `data/motifs.json` above. Only one story↔story Connection so far
   (`"parallels"`); more will accumulate as content grows.
6. ~~**JSON export/import for local backup.**~~ **Done (2026-09-08).**
   Two buttons on Home's new "Your data" card (same card group as the
   account bar, since there's still no dedicated Settings screen — the
   challenge-type picker is the only other settings surface). Export
   downloads `rooted-backup-<date>.json` — `{app, exportedAt, content,
   progress, settings}`, the exact same shape as the cloud sync document
   (`exportBundle()`/`downloadExport()` in `index.html`). Import
   (`validateImportBundle()`/`importFromFile()`) reads a file, validates
   it leniently (accepts any subset of `content`/`progress`/`settings`,
   rejects anything with none of them or a corrupted field), confirms
   with the user since it's a destructive local overwrite, then replaces
   local state and re-renders. Works with zero sign-in — the whole point
   was covering the anonymous case cloud sync doesn't.
7. **Per-field sync merge**, if whole-bundle last-write-wins (§7.1) ever
   turns out to lose real data in practice — e.g. practicing offline on
   two devices before either syncs. Not built because it hasn't been a
   real problem yet, not because it's hard to imagine.
8. **Practice-activity heatmap — built, then removed (2026-09-08 →
   2026-09-09).** Shipped on Home alongside the streak card, pulled the
   next day on direct feedback (didn't land well there). Not dead — the
   owner floated a future **profile screen** as where it might belong
   instead, which ties into the bigger not-yet-started accounts/guest-mode
   direction (see the `rooted-product-vision` memory — this doesn't have
   a CLAUDE.md section of its own yet since none of that's been designed).
   `practiceCountsByDay()` (DATA_MODEL.md §7) is still there and is the
   data source to reuse if/when this comes back — just `renderHeatmap()`
   and its CSS were deleted.
9. **Expanding into the New Testament — started 2026-09-10, owner's
   direction, immediately after the OT was finished.** The WEB source
   covers the whole 66-book Bible (verified: `parse_books.py --books
   matthew` downloads and parses cleanly from the same
   `TehShrike/world-english-bible` source, same public-domain status as
   the OT — no licensing change needed). The real work
   here is a genuinely new design decision the OT never had to make:
   **how to handle four Gospels that each retell the same life.**
   Decided, extending the project's existing "extend, don't clone"
   rule (Chronicles/Kings, Isaiah 36-39/2 Kings 18-20, Haggai-
   Zechariah/Ezra) rather than inventing a new principle for it:
   - **"The life of Jesus" is one unified chronological narrative**,
     not four separate retellings. Each event gets **one** Story, drawn
     from whichever Gospel(s) tell it most fully — `primaryReference`
     cites every Gospel that carries the event (e.g. the feeding of the
     five thousand cites all four), and curated verses can be pulled
     from more than one Gospel's account of the same event when each
     contributes something distinctive.
   - **Each Gospel's genuinely unique material still gets its own
     Story** — this is where each Gospel's real distinctiveness shows
     up, not lost by harmonizing. Luke alone has the fullest nativity,
     the prodigal son, the good Samaritan, Zacchaeus, the Emmaus road.
     Matthew alone has the magi, the fullest Sermon on the Mount, the
     Great Commission. John alone has Cana, Nicodemus, the woman at the
     well, Lazarus, the "I am" statements, foot-washing, doubting
     Thomas. Mark, the earliest and most concise Gospel, contributes
     almost no unique narrative of its own — that's expected, not a
     gap to fill artificially; its distinctiveness is pace and
     compression, not unique content.
   - **One Character record per person regardless of how many Gospels
     mention them** — Jesus, Peter, the Twelve, Mary, and so on are
     never duplicated per Gospel, same as any OT figure who appears in
     both Kings and Chronicles.
   - **New eras**, since none of the OT eras fit: `era_birth_of_jesus`,
     `era_jesus_ministry`, `era_passion_and_resurrection` (Jesus's life,
     roughly the Gospels' own three-act shape), then `era_early_church`
     for Acts.
   - **Epistles get the light verses-and-topics treatment** established
     with Leviticus/Proverbs — they're letters, not narrative, so no
     Story records for most of them (a few have real autobiographical
     narrative worth a Story, decided case by case as each is curated).
   - **Revelation** gets a light Story for John's own framing vision
     (the same treatment as Ezekiel's or Daniel's call/vision
     narratives), then verses-and-topics for the rest, since most of
     the book isn't narrated action in the Story sense.
   **Progress: the Gospels and Acts are both fully curated.** All four
   Gospels: the birth of Jesus, his whole ministry, and the complete
   Passion and Resurrection narrative. Acts: Pentecost and the early
   church's founding, Stephen's martyrdom, Saul's conversion, Peter and
   Cornelius, Paul's missionary journeys, the Jerusalem council, and
   his arrest, shipwreck, and two years preaching freely under house
   arrest in Rome — the note Acts itself ends on. **All 21 epistles are
   now done** (light verses-and-topics treatment, per item 9's design
   note — none has narrative): Romans through Jude. **Revelation is the
   last book left.** Full detail in DATA_MODEL.md §8, items 41
   onward, as each
   installment lands (that's now the authoritative running log —
   this file's own "Done" changelog below stops narrating every NT
   installment in full prose, to stay sustainable across what's a much
   larger body of work than the OT already was).

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
making Connection generic back on 2026-09-04 was for. Then the book of
Ruth: `era_judges`, 5 characters, 5 stories, 19 life events, 19 verses,
1 topic (`topic_loyalty`), and a 6th motif that reaches back into Genesis
(`motif_famine_and_a_foreign_land` — Jacob's move to Egypt and Naomi's to
Moab are the same shape). Then the rest of Exodus (5-40): 9 more stories
(plagues, Passover, the Red Sea, the song of the sea, manna and water,
Amalek, Sinai, the golden calf, the tabernacle glory), 2 new characters
(Pharaoh, Joshua — Joshua deliberately introduced early since he becomes
central later), 34 verses, and a 7th motif connecting Abraham's plea for
Sodom to Moses' plea for Israel after the golden calf
(`motif_intercession_for_others`). Then Leviticus, with book order now
canonical going forward (owner's direction) — chose Story treatment for
its few real narrative incidents (ordination of Aaron, Nadab and Abihu,
the blasphemer) over a verses-only pass, plus 19 verses across the legal
material and 2 new topics (`topic_holiness`, `topic_love` — "love your
neighbor as yourself" is from here, not the New Testament) and 2 new
characters (Nadab, Abihu). The ordination and Nadab-and-Abihu stories got
their first `"contrasts with"` story↔story Connection — the same fire from
Yahweh that accepts one offering kills two sons for another, days apart.
Then Numbers: 7 stories (Miriam and Aaron oppose Moses, the twelve spies,
Korah's rebellion, water from the rock a second time, the deaths of Miriam
and Aaron, the bronze serpent, Balaam's donkey), 4 new characters (Caleb,
Korah, Eleazar, Balaam), 28 verses including the Aaronic blessing
(Numbers 6:24-26) and the messianic "a star will come out of Jacob"
(24:17), and 2 new motifs that each span multiple books — grumbling in
the wilderness (Exodus's manna alongside Numbers' rock and bronze
serpent) and presuming on what is holy (Leviticus's Nadab and Abihu
alongside Numbers' Korah). No new topics needed. Then Deuteronomy: 2
stories (Moses commissions Joshua; Moses views the land from Nebo and
dies), 19 verses including the Shema (6:4-5) and "man does not live by
bread alone" (8:3), no new characters or topics, a new `"successor of"`
Connection (Joshua/Moses), and a 4th instance of `motif_gods_reassurance`
in Deuteronomy 31:23 — the same "I will be with you" said at Joshua's
commissioning that Isaac and Jacob heard generations earlier. Also
corrected `era_exodus`'s display text ("The Exodus begins" / "in Egypt"),
which had quietly gone stale as Leviticus, Numbers, and now Deuteronomy —
40 years later, at the Jordan — all got folded into the same era id
without the name and summary being updated to match. Then the book of
Joshua: a new era, `era_conquest`, and 9 stories — taking charge, Rahab
and the spies, crossing the Jordan, the fall of Jericho, Achan's sin,
the Gibeonite deception, the sun standing still, Caleb finally
receiving Hebron 45 years after he first believed Israel could take the
land, and Joshua's farewell ("as for me and my house, we will serve
Yahweh"). 2 new characters (Rahab, Achan). A 5th instance of
`motif_gods_reassurance` (Joshua 1:5, "as I was with Moses, so I will be
with you") and a new motif, `motif_foreign_woman_of_faith`, connecting
Rahab to Ruth — two foreign women with no claim on Israel who choose it
anyway, and both end up ancestors of David. Then the book of Judges: 6
stories (Ehud and Eglon; Deborah, Barak, and Jael; Gideon and the three
hundred; Jephthah's vow; Samson's birth; Samson and Delilah), all inside
the existing `era_judges` rather than a new one — refreshed that era's
summary at the same time, since it had only ever described Ruth. 10 new
characters, 34 verses, no new topics. A new motif,
`motif_who_am_i_reluctant_call`, ties Moses at the burning bush to Gideon
at the wine press — both told they're being sent, both immediately
arguing they're the wrong person for it. That motif's instances attach to
verses rather than stories, which surfaced a real gap: verse-attached
motif instances had no badge anywhere in the app. Fixed by wiring
`renderMotifBadges` into Verse detail the same way it already worked on
Character and Story pages. Then 1 Samuel: a new era, `era_united_kingdom`,
and 10 stories — Hannah's prayer and Samuel given to Eli, Samuel's call
and Eli's death when the ark is captured, Israel demanding a king, Saul's
rejection for disobedience ("to obey is better than sacrifice"), David
anointed while still a shepherd, David and Goliath, David and Jonathan's
covenant, Saul hunting David through the wilderness (who spares him
twice), the witch of Endor, and the deaths of Saul and Jonathan at
Gilboa. 7 new characters (Hannah, Eli, Samuel, Saul, David, Goliath,
Jonathan), 38 verses, 1 new topic (`topic_obedience`). David becomes the
4th instance of `motif_younger_son_chosen` (youngest of Jesse's sons,
same shape as Isaac, Jacob, and Joseph), and Saul's "am I not a
Benjamite, of the smallest of the tribes... my family the least" (1
Samuel 9:21) becomes a 3rd instance of `motif_who_am_i_reluctant_call`,
alongside Moses and Gideon. Then 2 Samuel, staying inside the same
`era_united_kingdom`: David's lament for Saul and Jonathan ("how the
mighty have fallen"), his kingship over a united Israel and capture of
Jerusalem, bringing the ark up while Michal despises him for dancing
before it, God's covenant promising his throne established forever,
kindness to Jonathan's crippled son Mephibosheth, his sin with Bathsheba
and the killing of her husband Uriah, Nathan's confrontation ("you are
the man"), the rape of Tamar and Absalom's revenge on Amnon, and
Absalom's rebellion ending in his death and David's grief ("O Absalom,
my son, my son!"). 9 new characters (Michal, Bathsheba, Uriah, Nathan,
Absalom, Tamar, Amnon, Mephibosheth, Joab), 39 verses, no new topics —
the existing 32 covered adultery, repentance, betrayal, and sorrow
without needing more. A new motif, `motif_prophet_confronts_the_king`,
connects Samuel's rebuke of Saul to Nathan's rebuke of David — the same
shape of a prophet telling a compromised king the truth to his face,
recognized only once a second real instance existed. Then 1 Kings: a new
era, `era_divided_kingdom` (the united-kingdom era stays as-is for
Solomon's reign, since it's still the same period as David's). 12
stories — Solomon crowned over his older brother Adonijah, asking for
wisdom instead of riches, judging between two women over a baby,
building and dedicating the temple, the queen of Sheba testing him with
hard questions, his downfall into idolatry through his foreign wives,
the kingdom splitting when Rehoboam rejects the elders' counsel and
Jeroboam leads ten tribes away, Jeroboam's golden calves at Dan and
Bethel, Elijah fed by ravens and sustaining a widow's household through
famine, his contest with 450 prophets of Baal on Mount Carmel, his
flight to Horeb and the still small voice, and his confrontation with
Ahab after Jezebel has Naboth killed for his vineyard. 10 new characters
(Solomon, Adonijah, the queen of Sheba, Rehoboam, Jeroboam, Elijah, the
widow of Zarephath, Ahab, Jezebel, Naboth) — the most in a single pass so
far. 40 verses, 1 new topic (`topic_idolatry` — golden calves and Baal
worship needed it, nothing existing fit). No new motifs: Solomon becomes
`motif_younger_son_chosen`'s 5th instance (crowned over his older
brother Adonijah), and Elijah confronting Ahab over Naboth becomes
`motif_prophet_confronts_the_king`'s 3rd, alongside Samuel/Saul and
Nathan/David. Then 2 Kings: Elijah is taken up and Elisha takes his
mantle; most of the book is Elisha's quiet miracles (the widow's oil,
raising the Shunammite's son, healing Naaman while Gehazi's greed earns
him the leprosy, the chariots of fire, the siege of Samaria lifted),
then Jehu ending the house of Ahab and Jezebel, the northern kingdom
carried off by Assyria, Hezekiah's prayer against Sennacherib and his
added fifteen years, Josiah's rediscovery of the law and last reforms,
and finally the fall of Jerusalem and the exile to Babylon. A new era,
`era_exile`, holds that last story (the monarchy ends there). 12 new
characters (Elisha, Naaman, Gehazi, the Shunammite woman, Jehu,
Hezekiah, Sennacherib, Isaiah, Josiah, Huldah, Nebuchadnezzar,
Zedekiah), 57 verses, 1 new topic (`topic_prayer` — Hezekiah's prayers
model it and there was already a lot of prayer content to gather). One
new motif, `motif_prophet_raises_a_dead_child` (Elijah and the widow of
Zarephath's son; Elisha and the Shunammite's), and a 6th instance of
`motif_gods_reassurance` ("those who are with us are more than those who
are with them"). Two new relationship kinds: `"successor of"` reused for
Elisha/Elijah, and a first `"servant of"` (Gehazi/Elisha). Also brought
`motif_gods_reassurance`'s `exampleReferences` up to date — it had
listed only its first three since Deuteronomy and Joshua added instances
without touching the display list. Then 1–2 Chronicles, done as one
pass. Chronicles retells Samuel–Kings from a temple-and-Judah angle, so
rather than duplicate stories, the curation added 11 new stories only
for Chronicles-*unique* material — David gathering materials and
charging Solomon, David's "all things come from you" prayer, the census
and the threshing floor of Ornan becoming the temple site, and the kings
of Judah that Kings barely mentions: Abijah winning by reliance on
Yahweh, Asa's early trust and late failure, Jehoshaphat sending singers
ahead of the army, Joash restoring the temple then having the priest
Zechariah stoned, Uzziah struck with leprosy for forcing his way into
the temple, Hezekiah's great Passover, Manasseh's repentance in a
Babylonian prison, and the decree of Cyrus that ends Chronicles on the
road home. 9 new characters (Abijah, Asa, Jehoshaphat, Joash, Jehoiada,
Zechariah son of Jehoiada, Uzziah, Manasseh, Cyrus), 50 verses, 1 new
topic (`topic_seeking_god` — "if you seek him he will be found by you"
is a Chronicles refrain and anchors ~6 verses already). Six family
edges filled in the Davidic line of Judah (Rehoboam→Abijah→Asa→
Jehoshaphat, Hezekiah→Manasseh, Jehoiada→Zechariah, Jehoiada raised
Joash). Two new motifs — `motif_stand_still_and_see` (Exodus 14 and
2 Chronicles 20 told in nearly identical words; the badge now also shows
on the existing Red Sea story) and `motif_pride_before_the_fall`
(Rehoboam and Uzziah) — plus a 4th instance of
`motif_prophet_confronts_the_king` (Zechariah/Joash, the one where the
king kills the messenger instead of repenting). The famous 2 Chronicles
7:14 ("if my people…") and 7:1 (fire at the dedication) were added to
the existing 1 Kings temple story rather than a new one. Then Ezra and
Nehemiah, done as one pass — the first genuinely new narrative since
Chronicles started retelling. A new era, `era_return_from_exile`, holds
12 stories: Zerubbabel and the priest Jeshua lead the first return and
rebuild the altar despite fear of the surrounding peoples, then lay the
temple's foundation to a mix of weeping and shouting; local adversaries
get the work halted by royal decree for years; Haggai and Zechariah spur
a second start, Darius confirms Cyrus's decree, and the temple is
finished and dedicated. A generation later Ezra leads a second return
to teach the law, then confronts the people's intermarriage with a
public confession. Nehemiah, cupbearer in Susa, weeps on hearing the
walls lie broken, gets the king's leave, and inspects the ruins by
night; Sanballat mocks and conspires against the rebuilding, so
Nehemiah arms half the workers while the other half builds; he
separately confronts the nobles over usury against the poor; the wall
is finished in 52 days despite Sanballat's repeated traps. Ezra then
reads the law aloud to the whole assembly — the people weep until told
the day is holy, "the joy of Yahweh is your strength," and keep the
Feast of Booths with the greatest gladness since Joshua's day, then
confess corporately and seal a written covenant. Nehemiah's final
chapter has him return to purge the temple of Tobiah, restore the
Levites, and enforce the Sabbath and marriage law — closing on his own
refrain, "Remember me, my God, for good." 5 new characters (Zerubbabel,
Jeshua, Ezra, Nehemiah, Sanballat), 34 new verses, no new topics (the
existing 35 — prayer, repentance, scripture, justice, faithfulness,
seeking God — covered the material without strain). A new
`"worked alongside"` symmetric relationship connects Zerubbabel/Jeshua
and Ezra/Nehemiah, and a new motif, `motif_the_forgotten_law_rediscovered`,
ties Josiah's rediscovery of the Book of the Law (2 Kings 22) to Ezra's
public reading of it (Nehemiah 8) — the same shape of a forgotten law
found, met first with grief, then renewed covenant. Then Esther — its
own era, `era_esther`, for the Jews who stayed in the Persian diaspora
rather than returning to Jerusalem, a genuinely distinct group and
setting from Ezra/Nehemiah's Judah-centered narrative. 8 stories: Vashti
deposed for refusing the king's summons; Esther crowned queen without
revealing she's a Jew, and Mordecai's uncovered assassination plot;
Haman's promotion, Mordecai's refusal to bow, and the empire-wide decree
to destroy the Jews; Mordecai's plea ("who knows if you haven't come to
the kingdom for such a time as this?") and Esther's answer ("if I
perish, I perish"); Esther's banquet, Haman's gallows built for
Mordecai, and Mordecai's unplanned honor that same night; Haman exposed
and hanged on his own gallows; the decree reversed and Mordecai
promoted; and the Jews' deliverance and the establishing of Purim. 5 new
characters (Esther, Mordecai, Haman, Ahasuerus, Vashti), 23 new verses,
no new topics. Two new relationship instances of the existing
`"husband of"` type (Ahasuerus/Esther, Ahasuerus/Vashti) and a first use
of `"raised"` outside Eli/Samuel and Jehoiada/Joash (Mordecai/Esther). A
new motif, `motif_hidden_identity_saves_the_people`, connects Joseph
revealing himself to his brothers to Esther revealing she is a Jew to
save her people — the same shape of a Hebrew concealed in a foreign
court, revealed at exactly the moment it can save their people. Then
the Wisdom books, done as one pass. Job got its own new era, `era_job`
— undated and set outside Israel's own history (the land of Uz), so it
doesn't belong in any existing era. 4 stories following the book's real
narrative frame: Job tested (loses his children, wealth, and health in
a single day at Satan's challenge, refuses to curse God); Job's
complaint and his friends' answers (Eliphaz leads the argument that his
suffering must be deserved; Job protests his innocence across many
chapters, at one point declaring "I know that my Redeemer lives"); God
answers out of the whirlwind (no explanation for the suffering, just an
overwhelming display of creation Job can't explain or control — he
repents not because he understands but because he has now seen God);
and Job restored (double what he had before, ten more children, a long
life). 2 new characters (Job, Eliphaz). Proverbs, Ecclesiastes, and
Song of Solomon got the lighter verses-and-topics treatment established
with Leviticus — no narrative to build stories from. 3 new topics:
`topic_anger` (explicitly named in this file's own "vision" section as
an example practice topic, and heavily represented in Proverbs —
"a gentle answer turns away wrath"), `topic_friendship` ("a friend
loves at all times," "iron sharpens iron"), and `topic_speech` ("death
and life are in the power of the tongue"). 72 new curated verses total
across the four books (14 Job, 37 Proverbs, 14 Ecclesiastes, 7 Song of
Solomon). Then Isaiah: no new era or characters — `char_isaiah` already
existed (from the 2 Kings pass), and his one real narrative moment, the
call vision ("Holy, holy, holy... here am I, send me," Isaiah 6), slots
into the existing `era_divided_kingdom`. The rest is 39 curated verses
across Isaiah's judgment and comfort oracles — no new topics needed.
Isaiah 36-39 (Hezekiah and Sennacherib) is nearly word-for-word 2 Kings
18-20, already curated there, so it wasn't duplicated. Then
Jeremiah/Lamentations: 4 new characters (Jeremiah, Baruch, Ebed-Melech,
Gedaliah) and 6 new stories — his call (a 4th instance of
`motif_who_am_i_reluctant_call`), the potter's house and the temple
sermon that nearly got him killed, Baruch's scroll burned and rewritten,
being lowered into a cistern to die and rescued by Ebed-Melech,
Gedaliah's brief governorship and assassination, and the remnant
forcing Jeremiah to Egypt against his own counsel. Split across
`era_divided_kingdom` (pre-fall) and `era_exile` (fall and aftermath)
by each story's own date, not one era per character. 19 new curated
verses. Lamentations added 6 more, one folded into the existing
`story_fall_of_jerusalem` rather than a new story. Then Ezekiel: 1 new
character and 3 new stories, all fitting the existing `era_exile` —
his call vision, the symbolic acts (besieging a tile of Jerusalem,
lying bound on his side, forbidden to mourn his wife), and the valley
of dry bones. 18 new curated verses, no new topics or motifs. Then
Daniel: 6 new characters (Daniel, Shadrach, Meshach, Abednego,
Belshazzar, Darius the Mede) and 6 new stories, all in `era_exile` —
the king's food, Nebuchadnezzar's statue dream, the fiery furnace,
Nebuchadnezzar's madness, the writing on the wall, and the lions' den.
26 new curated verses, no new topics. One new motif,
`motif_faithful_defiance_delivered`, connects the furnace and the
lions' den — refuse the king's command, be sentenced to die, and be
delivered in a way that makes the king himself acknowledge God. Then
the Twelve — Hosea through Malachi — done as one final pass, closing
out the entire Old Testament. No new eras: every book fit either
`era_divided_kingdom` (Hosea, Amos, Jonah — all roughly contemporary
with Jeroboam II, before Israel's fall) or `era_return_from_exile`
(Haggai and Zechariah, whose own books are literally about the temple's
rebuilding). 4 new stories: Hosea's marriage to Gomer as a living
picture of Israel's unfaithfulness; Amos confronting the priest
Amaziah after refusing to stop prophesying; Jonah fleeing and being
swallowed by a fish; Jonah resenting Nineveh's repentance. 6 new
characters (Hosea, Gomer, Amos, Jonah, Haggai, Zechariah — distinct
from the priest Zechariah stoned under Joash). Haggai's and
Zechariah's own verses were folded into the *existing*
`story_temple_completed` rather than new stories, since their books are
about that same event. 60 new curated verses across all twelve books,
no new topics. Two new motifs: `motif_gracious_and_merciful_formula`
connects the same description of Yahweh — "gracious and merciful, slow
to anger" — recurring almost word-for-word from Exodus 34:6 (already
curated) through Nehemiah's confession (already curated) to Joel's call
to repentance to Jonah's own complaint that God is too merciful for
comfort; `motif_trust_beyond_understanding` connects Job and Habakkuk,
both ending not with their questions answered but with a fuller sight
of God turning them from demanding answers to worship anyway.

**With this, all 39 books of the Old Testament are curated** — 949
seed verses, 124 characters, 178 stories, 408 life events, 20 motifs,
and 135 connections, built one book at a time across this project's
life, from Genesis's first pass through this final push through the
Twelve. The owner asked the same day to continue straight into the New
Testament — see "Known gaps" item 9 below, and DATA_MODEL.md §8 items
41+ for that work as it lands. The WEB source
(`TehShrike/world-english-bible`) covers the full 66-book Bible, so no
translation/licensing change was needed to start it; the era/timeline
model does need real new design for the NT's different shape (four
Gospels retelling the same life, then letters rather than narrative) —
see item 9's opening note for the approach taken.

**New Testament, installment 1: the birth of Jesus.** A new era,
`era_birth_of_jesus` (order 13). 6 stories: Gabriel's two announcements
(to Zacharias, then to Mary — one story, since Luke tells them as one
interleaved unit ending in Mary's visit to Elizabeth and her
Magnificat); John the Baptist's birth (Zacharias's speech restored, his
prophecy over his son); Jesus's birth in Bethlehem; his presentation at
the temple (Simeon and Anna); the wise men and the flight to Egypt
(Matthew's unique material, including his own account of the
annunciation to Joseph); and the boy Jesus found teaching in the temple
at twelve. 6 new characters: Jesus, Mary, Joseph (id
`char_joseph_husband_of_mary` — the id `char_joseph` was already taken
by Genesis's Joseph; caught by a real build failure the first time
through, "two life events at sequenceInLife 10/20/30/40", since Genesis
Joseph's own ids like `event_joseph_dreams` don't collide but the
generic id itself did), John the Baptist, Zacharias, Elizabeth. 22
curated verses, no new topics. Jesus's and John the Baptist's `eraId`
is set to `era_birth_of_jesus` for now (the only NT era that exists
yet) and will move to `era_jesus_ministry` once that era exists next —
same pattern as any OT character whose `eraId` reflects where their
arc is centered, not merely the first story they appear in.

## Source data provenance

WEB Bible text: parsed from the `TehShrike/world-english-bible` GitHub
repository (public domain / CC0 JSON). If re-pulling or updating this
data, re-verify the source is still public domain before reproducing
verse text in bulk — this reasoning does NOT extend to copyrighted
translations (see NIV note above).
