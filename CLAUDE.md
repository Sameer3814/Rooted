# Rooted — Scripture Study App

A personal project: a mobile-first Bible study companion — exploring how
characters, stories, topics, and cultural context connect to each other,
with verse memorization as one part of that, not the app's whole identity.
It started as a memorization-first tool (fill-in-blank, scramble, speed
recall, progressive reveal) and deliberately outgrew that framing on
2026-09-14, once the "deep study" character/story curation made the rest of
the app substantial enough to lead with — see "Known gaps" item 10 for that
whole curation effort, and item 78 for the Home redesign this identity
shift actually required (short version: memorization moved to its own
Practice tab; Home fronts Verse of the Day and, once configured, mission
content instead).

This file is context for whoever (human or Claude) picks this project up
next. Read it before making structural changes.

**`DATA_MODEL.md`** holds the full schema for every entity — including the
vision features not yet built. Read it before changing any data shape, and
update it in the same pass as any schema/data change (this applies to all
`.md` docs: keep them in sync with the code).

## The vision (long-term, bigger than current code)

The owner's goal was never just verse memorization — it's a study companion,
and since 2026-09-14 the app's own front door (Home) actually reflects that
rather than leading with practice:

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
  step). **4-Pillar bottom nav as of 2026-09-16 (item 109, owner-
  specified architecture)**: **Home** (editorial front door as of
  2026-09-14, reordered 2026-09-17 per item 117 — a greeting + streak
  header, then in order: Verse of the Day, Unreached of the Day, the
  Biblical Fact of the Day (item 116), Story of the Day, Word of the Day,
  and one practice link when verses are due; "This Day in Church
  History" was retired and deleted the same day as the reorder — see
  item 117; no progress dashboard, no practice session UI — see items
  78 and 82), **Practice** (due-today stats, a linear daily-goal
  progress bar, a 2x3 exercise-mode grid, the full verse library, and
  five real challenge types plus a "Mix & Match" random-per-verse mode
  — Tap Builder, First-Letter Sprint, Progressive Vanish, Clause
  Connect, and Reference Match (items 113/114/115/118/119/120) — the
  original four (fill-in-blank, scramble, progressive reveal, verse
  ladder) were fully retired 2026-09-17, item 114; also the entry point
  for Add Verse/Add Character, via a small
  `+` next to "Your verses"), **Discover** (hub tab — Read the
  Bible/Browse, Verse detail, Topics, Topic detail, People grouped by
  era, Character detail (life timeline, family, stories, pattern
  badges), Stories list, Story detail (related stories, pattern badges)
  — all pre-existing screens, just regrouped under one front door), and
  **Study** (the "deep theological suite" pillar — a 3-card hub of
  Patterns, Timeline, and Family Tree, items 109-112; Timeline walks
  the whole Bible in canonical order, Family Tree is a real SVG node-
  graph built from the `Connection` entity; an interlinear/Strong's view
  and commentaries are still unbuilt — see Known Gaps). And
  **Settings** (gear icon, top-right of Home) — the account bar for
  optional cloud sync and the "Your data" export/import card live here,
  not on Home. They started on Home (2026-09-08) and were moved the same
  day on direct feedback: sync/backup controls are occasional-use, and
  were pushing the actual daily-use content below the fold. Lesson for
  anything added later in this vein — account/settings-shaped features
  default to Settings, not Home, unless there's a specific reason a
  control needs daily visibility. (That "daily-use content" framing is
  itself now historical — item 78 moved the daily-use practice content
  off Home entirely, onto its own tab, for an unrelated reason: Home
  stopped being the memorization tool's front door at all.)
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
- **Stories search — done (2026-09-14).** Same pattern again, this time
  on the Stories screen (matching title/reference/summary) — own
  `#stories-results` subtree, own `storiesQuery` state. Now the third
  screen (People, Topics, Stories) using this exact debounced-search
  shape. See DATA_MODEL.md §8, item 87.
- **Character carousel + swipe-to-go-back — done (2026-09-15).** A
  first swipe-only version (Character Detail's swipe-left meant "next
  character," overriding swipe-back on that one screen) was revised the
  same day on direct feedback — blind gestures with no visible hint they
  existed, and an inconsistent meaning per screen. Now: visible
  left/right arrow buttons overlaid on the character's portrait page
  through the full cast (same order the People list shows them), and
  swipe-to-go-back works identically on every screen with no exception,
  found generically via whatever `.back-btn` is currently on screen so
  it reuses each screen's own back-nav action, falling back to Browse's
  breadcrumb trail (`.crumbs`) where no `.back-btn` exists. Three real
  bugs fixed the same day from direct device testing: the carousel
  arrows were chaining the back button through visited characters
  instead of returning to the true entry point (fixed with a dedicated
  `char-carousel-nav` action that preserves the original `from`), swipe
  wasn't registering on a real device at all (missing
  `touch-action:pan-y` on `.app` let the browser cancel the gesture as a
  scroll), and the gesture direction itself was wrong — the owner's own
  original ask said "swipe left," corrected on testing to swipe RIGHT,
  matching the standard mobile edge-swipe-back convention. See
  DATA_MODEL.md §8, items 102-104.
- **Story illustration pipeline — a 6-story style test, not yet wired
  into the app — done (2026-09-15).** A deliberately separate, free
  toolchain from the character-portrait work: **SDXL on Colab's
  free-tier T4 GPU**, not Gemini, since the owner didn't want more API
  spend. New: `pipeline/colab_story_art_sdxl.ipynb` (runs entirely on
  Colab), `pipeline/curation/story_art_settings.json` (6 stories so
  far), `pipeline/import_story_art.py` (resizes Colab's downloaded
  output into `media/stories/` and a new `data/story_illustrations.json`
  manifest — same manifest-not-Media-entity shortcut as character
  portraits). Two-machine workflow, unlike the Gemini pipeline: generate
  in Colab, download the zip, unzip into the new gitignored
  `pipeline/.storyart_incoming/`, then run the import script. **First
  attempt failed** — plain SDXL base has no reliable default lean
  toward the target style at all (generic fantasy art, one monochrome
  stock-photo result, one armored giant rendered as a sci-fi robot).
  Fixed with a verified, well-adopted community LoRA (CivitAI's "Pixar
  Style (SDXL)," 200K+ downloads, 575 reviews — not a guess) plus
  expanded negative prompts and two rewritten scene descriptions
  targeting the exact failures seen. **Superseded (2026-09-16) — see
  below.** After two more real version-pin fixes got the notebook
  actually running, the resulting batch showed the LoRA landed the
  target style well on character-centered scenes (David and Goliath,
  Feeding the 5,000, the lions' den) but not on landscape/atmosphere-
  heavy ones (Creation, the Flood, the Crucifixion's wide vista), which
  kept reading as generic realistic matte-painting. Owner's call: stop
  fighting LoRA inconsistency for free and switch story art back to
  Gemini. See DATA_MODEL.md §8, items 105-106.
- **Story art: switched back to Gemini — done (2026-09-16).** New
  `pipeline/generate_story_art.py`, structured like
  `generate_character_art.py` (same `.env.local` key, same endpoint/
  response shape) but with a fully wired `--batch` (that script's own
  `--batch` is still a stub) that generates, resizes to 960px-wide JPEG,
  and updates `data/story_illustrations.json` in one step — no Colab
  two-machine import dance needed since Gemini runs synchronously.
  Reuses the existing `pipeline/curation/story_art_settings.json` scene
  descriptions as-is; only the renderer changed, not the content. The
  Colab notebook and its supporting files are kept as historical record,
  not deleted. **First batch run 2026-09-17 — see below.** See
  DATA_MODEL.md §8, item 108.
- **First real story-art batch run + wired into the app — done
  (2026-09-17).** The owner added Gemini billing credits and asked for
  a sample batch first, "then continue from there." Ran `--test` on the
  6 stories that already had a curated scene description (Creation, the
  Flood, feeding the 5,000, David and Goliath, the crucifixion, the
  lions' den — deliberately the same 6 the abandoned SDXL/Colab
  experiment used, so there was a known baseline and two known failure
  modes — landscape scenes reading as realistic matte paintings,
  Goliath rendered as a robot — to check were actually fixed). Reviewed
  all 6 directly: both failure modes are gone. Ran `--batch` on the same
  6 for real — `media/stories/*.jpg` + `data/story_illustrations.json`
  (a flat manifest, same shortcut as `data/character_portraits.json`,
  item 91). This app had no code reading that manifest at all before
  now (unlike the character one) — added `loadStoryIllustrations()`/
  `storyIllustrationUrl()` (mirrors the character-portrait pair
  exactly) and wired it into Home's Story of the Day card and a new
  wide `.story-hero-photo` banner on Story Detail's hero; the Stories
  list stayed plain text for this pass, since it never had a thumbnail
  slot to begin with. The other ~318 stories still show their existing
  fallback — this is a first sample, not the whole set; scaling up
  needs a real scene description written into
  `pipeline/curation/story_art_settings.json` per story before
  `--test`/`--batch` will generate for it (curated, not auto-generated
  from the story's own summary — same discipline as everything else
  narrative in this app). See DATA_MODEL.md §8, item 125.
- **Story-art quality/accuracy fix — done (2026-09-17), same day.** The
  owner reviewed the first batch and flagged two real problems: style
  was inconsistent story-to-story (feeding-the-5000/crucifixion looked
  richly rendered, the other 4 read flatter, closer to a
  children's-storybook illustration), and story_crucifixion's prompt
  said "three crosses" without ever naming who was on the other two —
  the model rendered Jesus's cross alone. Sharpened
  `generate_story_art.py`'s `STYLE_SUFFIX` to name the specific
  rendering qualities the good outputs actually had and explicitly rule
  out the flatter look seen (a real bias on model variance, not a
  guaranteed fix). Rewrote all 6 scene descriptions in
  `pipeline/curation/story_art_settings.json`, each cross-checked
  against that story's own curated summary/characters first —
  `story_crucifixion` now explicitly places two named criminals on
  either side of Jesus's cross, grounded in the story's own already-
  curated "crucified between two criminals" summary and its existing
  `char_penitent_thief`. Re-ran `--test`, reviewed all 6 (crucifixion
  now correct), then `--batch` to regenerate and overwrite the
  committed files. See DATA_MODEL.md §8, item 126.
- **Second story-art batch + bigger discovery thumbnails — done
  (2026-09-17), same day.** 10 more stories curated and generated
  (Adam and Eve, the Tower of Babel, crossing the Red Sea, the burning
  bush, the covenant at Sinai, Jonah and the fish, Elijah taken up,
  Jesus walking on water, the nativity, the empty tomb) — same
  discipline as items 125-126, every scene description cross-checked
  against that story's own curated summary/characters first (e.g. Adam
  and Eve are explicitly "modestly concealed by garden foliage... not
  shown nude," a deliberate call given this app's family audience).
  `--test` reviewed before `--batch`, same as every batch so far.
  `data/story_illustrations.json` now has 16 ids; no app-code changes
  needed since item 125's manifest-driven wiring already picks up any
  id present generically. Also: `.discovery-thumb-box`/`.discovery-
  thumb` (shared by Home's Story of the Day and Unreached of the Day
  cards) bumped 88x68 -> 104x80, owner's own framing being "that will
  capture the user's attention" — both cards grew together since they
  share the class. See DATA_MODEL.md §8, item 127.
- **Story Detail: full-bleed hero banner + prev/next carousel — done
  (2026-09-17), same day.** The hero image now reaches the actual
  screen edges (`.story-hero-image-container`, negative margins
  canceling `.app`'s own padding), fades into the page background via a
  bottom gradient, and the details card overlaps that fade with its own
  negative top margin so the seam reads as one surface. A frosted
  circular back button now floats on the artwork instead of sitting in
  its own row above it. Every story gets this treatment, not just the
  16 with real generated art (items 125-127) — `placeholderArt(s.id)`
  fills in for the other 308, same "real photo later, placeholder now,
  identical layout either way" pattern already used for Home's VOTD/
  Unreached cards. Also added prev/next story arrows (not in the
  original spec, requested alongside it) — mirrors the character
  carousel exactly (`allCharactersOrdered()`/`adjacentCharacter()`,
  items 102-104) but ordered by each story's own `canonicalOrder`
  (`allStoriesOrdered()`/`adjacentStory()`), the same "walk the Bible in
  sequence" ordering Timeline already uses. See DATA_MODEL.md §8, item
  128.
- **4-Pillar navigation — done (2026-09-16), owner-specified
  architecture.** Bottom nav collapsed from 6 tabs to 4 — Home and
  Practice unchanged; a new **Discover** hub screen
  (`renderDiscover()`) fronts the existing Browse/Topics/People/Stories
  screens (unmodified, just regrouped). **Study** originally routed
  straight to Patterns as a provisional stopgap (see the next bullet for
  why that changed the same day). People's old "Stories" and "Patterns"
  quick-cards were removed (now peer top-level destinations of their
  own). "Add" lost its own tab entirely — moved to a small `+` next to
  Practice's "Your verses", since adding your own verse/person is a
  library-management action and Practice already owns "your verses."
  Icons and type scale already satisfied the spec (items 85, 107); the
  given palette values were confirmed as describing the existing v3
  dark tokens loosely, not a new palette, so no token values changed.
  See DATA_MODEL.md §8, item 109.
- **Timelines & Family Trees added to Study — done (2026-09-16), same
  day as the above.** The owner asked for these sourced from "The Bible
  Project Open Resources and Wikidata Biblical Graph Queries" — neither
  was actually used (Bible Project has no queryable dataset for this;
  Wikidata's crowd-sourced genealogy data would cut against this
  project's whole hand-curated-from-Scripture discipline, same
  reasoning as the NIV-PDF rejection). Built entirely from data already
  curated here instead. **Timeline** (`renderTimeline()`) is every Era
  in canonical order with its Stories, reusing the per-character "Their
  life" section's own `.timeline` CSS. **Family Tree** is a real
  hand-rolled SVG node-link graph (not a flat list — offered as the
  lower-effort option, the owner chose the harder graph) —
  `familyGraph()`/`layoutFamilyGraph()` build a bounded (±2 generations)
  layered layout from the existing `Connection` entity's core
  blood/marriage relationship types only; `renderFamilyTree()` renders
  it with tap-to-re-center navigation; `wireFamilyTreePanZoom()` adds
  hand-rolled drag-pan and wheel/pinch-zoom, since this app has no
  existing graph/canvas component and no third-party JS library
  anywhere to reuse. Verified against real data before shipping: most
  characters (188 of 267) have zero curated family connections and
  correctly show an honest empty state rather than a crash; well-
  connected figures like David/Jacob/Isaac render real multi-generation
  trees. This is also why Study now gets a proper 3-card hub
  (`renderStudy()`: Patterns/Timeline/Family Tree) instead of the
  "route straight to Patterns" stopgap from the bullet above. See
  DATA_MODEL.md §8, item 110.
- **Family Tree rendering overhaul — done (2026-09-16), same day.** A
  full hex-exact visual spec replaced the first-pass plain-SVG tree
  with a hybrid render: an absolutely-positioned, `pointer-events:none`
  SVG draws only curved parent→child Bezier connectors
  (`familyTreeBezier()`), while the nodes themselves are real HTML
  avatar cards (image, name, role) layered on top — closer to what the
  spec's own CSS (`object-fit`, `transition`, `box-shadow`) actually
  describes than approximating it in raw SVG. `layoutFamilyGraph()` was
  rewritten to genuinely center a child under its parent's average X
  (an only child lands exactly beneath its parent — re-verified against
  real data, zero overlaps, Ham→Canaan lands at the identical X as the
  spec's own worked example) rather than the original per-row insertion
  order. The tree's card/connector colors are a distinct warm-bronze
  palette scoped only to this feature's own CSS classes, not a change
  to the app's shared v3 dark tokens. See DATA_MODEL.md §8, item 111.
- **Family Tree feedback pass — done (2026-09-16), same day.** Swipe-
  right-to-go-back is now disabled specifically on the rendered tree
  (it was fighting the pan gesture); the picker now only lists people
  with a real curated family, as "`{Name}'s Family`" cards, instead of
  all 267 characters (`hasFamilyTree()`/`renderFamilyCard()`); and
  seven real family-connection gaps named by the owner (Jesus's family
  specifically) were filled using facts already implicit in these
  characters' own curated bios — Mary/Joseph→Jesus (Joseph as
  "adoptive father," not biological, matching Jesus's own "conceived by
  the Holy Spirit" framing), Zacharias/Elizabeth→John the Baptist, and
  Peter/Andrew as brothers — all using characters that already existed,
  no new Character records added. `data/connections.json` is now 150
  edges (was 143). See DATA_MODEL.md §8, item 112.
- **Tap Builder challenge type — done (2026-09-17).** A fifth
  `ChallengeType`, `challenge_tap_builder` (word-tile bank: tap bank
  tiles to fill blanks in a verse, tap a placed tile to return it to the
  bank) — the owner's spec mapped almost exactly onto the existing
  pluggable interface, needing only two small backward-compatible
  additions to it: `canCheck(state)` (disables the generic Check button
  until every blank is filled) and `autoAdvanceMs` (auto-advances to the
  next verse ~600ms after a correct answer, still alongside the normal
  Continue button as a fallback). Distractor words are drawn from
  `data.verses` (always in memory) rather than the lazily-fetched full
  corpus, so the exercise stays genuinely offline-first. Its own dark-
  obsidian/bronze component palette is scoped to its own CSS classes
  only, same reasoning as the Family Tree feature (item 111) — no
  shared app tokens changed. Verified by simulating 30 real verses
  played "perfectly" before shipping (all graded correct, no crashes),
  not just read over. See DATA_MODEL.md §8, item 113.
- **Retired the original four ChallengeTypes; added First-Letter Sprint
  — done (2026-09-17), same day.** Direct owner request: "get rid of the
  older exercises and keep the new ones." Deleted fill-in-blank,
  scramble, `challenge_first_letters`, and `challenge_verse_ladder`
  along with their dead-code support (`hintWord()`, `.blank`/`.chip`/
  `.scramble-*` CSS); every stored/default `challengeTypeId` fallback
  now points at `challenge_tap_builder`, and a returning user with a
  stale stored id already degrades cleanly via the existing
  not-found guard. New: `challenge_first_letter_sprint`, a real-time
  typing drill — type each word's first letter to reveal it and race to
  the end, with a live timer and a "Completed in Xs! (Y WPM)" toast.
  Driven by actual keystrokes, not taps: a new `practiceKeyInput()` /
  `practiceInteractWith()` (refactored out of `practiceInteract()`)
  entry point feeds a hidden, always-focused `<input>`'s keystrokes into
  the same `interact()`/finalize machinery every other type already
  uses. The live countdown updates a `#sprint-timer` span directly via
  `setInterval` rather than through the normal `render()` cycle, since
  re-rendering every 100ms would fight keystroke-driven renders and
  keep stealing the hidden input's focus — same reasoning
  `wireTimelineDrag()` already established for drag gestures. Verified
  by simulating 40 real curated verses typed letter-perfect before
  shipping (all completed and graded correct), plus a deliberate wrong-
  keypress test. **Real-device follow-up, same day**: the mobile
  keyboard closed after every keystroke, because each one went through
  this app's normal full `render()` (destroys and recreates the hidden
  `<input>`). Fixed by patching only the sentence box's own `innerHTML`
  directly per keystroke (`sprintTokensHTML()`, shared with `render()`'s
  initial markup) and never touching the `<input>` until the sprint
  actually completes; added an always-visible "Keyboard not showing?
  Tap here." fallback, since a mobile browser won't reopen a dismissed
  keyboard from a `setTimeout`-driven `.focus()` (i.e. after
  `autoAdvanceMs`) the way it will from a real tap. This is now a
  documented exception to the app's normal "`render()` rebuilds
  everything" model — see DATA_MODEL.md §8, item 114's addendum before
  touching this challenge type again. **A second real-device report,
  same day**: fixing the keyboard-closing bug surfaced that the page
  was also scrolling the verse out of view on every keystroke — the
  hidden input was `position:absolute` right after the sentence box in
  the document, so each keystroke's height change moved the still-
  focused input, and the browser kept re-scrolling to chase it. Fixed
  by pinning the input `position:fixed` to the viewport (plus
  `font-size:16px`, closing off iOS Safari's separate auto-zoom-on-focus
  trigger for the same category of bug).
- **Practice hero overhaul: linear progress bar, 2x3 mode grid, Mix &
  Match — done (2026-09-17).** Replaced the circular goal ring with a
  full-width linear "DAILY GOAL … N of M completed (P%)" bar
  (`renderPracticeProgressBar()`), and the horizontally-scrolling
  challenge-type picker with a 2x3 grid of mode tiles
  (`renderChallengeGrid()`, five new icon paths — `layers`, `zap`,
  `eye-off`, `align-left`, `bookmark` — added to the existing
  `icon()`/`ICON_PATHS` system). The grid's 6th tile, "Mix & Match," is
  a genuine new practice mode, not just a label — it picks a different
  random real `ChallengeType` per verse instead of one fixed type for
  the whole session, via a sentinel `challengeTypeId`
  (`MIX_MATCH_ID`) that's deliberately not a `CHALLENGE_TYPES` key.
  That required a real small architecture change: every practice-queue
  item now carries its own `challengeTypeId` (set once at
  `startPractice()`), and every place that used to read
  `challengeType(session.challengeTypeId)` — render, check, interact,
  the Sprint/Clause-Connect wire functions, and practice-history
  logging — now reads it off the current item instead, so a mixed
  session's history correctly records which type each verse actually
  used. See DATA_MODEL.md §8, item 120.
- **Reference Match challenge type — done (2026-09-17).** A fifth
  `ChallengeType` — a 4-option multiple choice, 1 correct against 3
  distractors preferring the same book, then the same testament (a new
  `NT_BOOKS` lookup, since `Verse` has no stored testament field), then
  anything else in the library, drawn from `data.verses` for the same
  offline-first reason Tap Builder's own distractors are (item 113).
  Each round randomly picks one of two formats — quote shown, pick the
  reference; or reference shown, pick the quote — and a single tap both
  answers and finalizes (`interact()` sets `state.checked` itself, like
  Progressive Vanish's "complete" tap, rather than the generic `check()`
  path). The first type whose *wrong* path also auto-advances, not just
  its correct one — added a real second interface field,
  `autoAdvanceMsWrong`, to `CHALLENGE_TYPES` (600ms correct, 1500ms
  wrong, long enough to actually read the revealed correct card) rather
  than special-casing it, and wired both shared finalize paths
  (`checkPractice()`, `practiceInteractWith()`) to use it. The verse
  reference is deliberately withheld from the screen's own ref line
  while this type is active — one of its two formats is literally
  asking the user to name it, so showing it up top would spoil the
  answer. Verified by simulating all 1,812 curated verses through
  build+perfect-play before shipping — every one produces exactly 4
  valid options and grades correctly. See DATA_MODEL.md §8, item 119.
- **Clause Connect challenge type — done (2026-09-17).** A fourth
  `ChallengeType` — a verse splits into 3-5 clauses
  (`splitIntoClauses()`, punctuation/connecting-word split with a
  fixed-word-count fallback for short verses), scrambles them, and the
  user reorders them back into sequence. Two input methods: tap-to-swap
  through the normal `interact()` dispatch, and grip-handle dragging —
  wired with the same pointer-event reordering `wireTimelineDrag()`
  already uses for the Timeline screen, not the owner's originally-named
  HTML5 Drag-and-Drop API, which has no real touch support and wouldn't
  work on a phone at all. A wrong "Check Order" tap shakes the list and
  highlights misordered cards in red without finalizing the attempt —
  the user can keep fixing it and re-check, unlike Tap Builder's
  one-shot grading — implemented by routing "Check Order" through
  `controls()`/`interact()` rather than the generic `check()` path, so
  only a fully-correct order ever reaches `recordPractice`. One real fix
  to the owner's own spec caught before shipping: its split regex used a
  capturing group around the connecting words, which JS's `.split()`
  would've left behind as stray extra clause fragments — switched to
  non-capturing. Verified by simulating all 1,812 curated verses through
  a full scramble→fix→check cycle (zero crashes, including verses too
  short to split into more than one clause, like "Jesus wept.", which
  correctly resolve as a trivial win rather than erroring). See
  DATA_MODEL.md §8, item 118.
- **Progressive Vanish challenge type — done (2026-09-17).** A third
  `ChallengeType`, self-graded like First-Letter Sprint but pure taps
  (no keyboard, so none of that type's real-device mobile bugs apply).
  Reveals a verse in full, then climbs 5 stages vanishing an additional
  20% of its (non-punctuation) words each time — a fixed random order
  decided at build time guarantees a word never un-vanishes once hidden,
  the same idea the retired `challenge_verse_ladder` used, reused under
  new naming/UI rather than being a sign the retirement (above) didn't
  happen. Tapping any individual blank reveals it for 1.5s (a real
  `setTimeout`, guarded against a superseded peek's timer firing late);
  "Hold to Peek" (reveal everything while pressed) is deliberately kept
  entirely outside the `interact()`/`render()` cycle — a plain CSS class
  toggled directly on press/release, since there's nothing to score
  about a peek and a full re-render would make holding feel laggy.
  Verified by simulating 30 real curated verses stage-climbing through
  all 5 steps before shipping — exact 20/40/60/80/100% word counts, zero
  regressions, zero punctuation tokens ever vanishing. See DATA_MODEL.md
  §8, item 115.
- **"Biblical Fact of the Day" — done (2026-09-17).** A brand-new Home
  card (not an update to something existing — flagged that up front),
  with a real verification pass behind its "Verified Source" badge
  rather than a decorative label: every one of the 10 facts in the new
  `data/daily_facts.json` was checked against this app's own real WEB
  verse text (and, for three of them, already-curated Character/
  Connection/Motif data) before being marked validated — the spec's
  named external sources (OpenBible Geocoding Data, Berean Standard
  Bible Text) aren't actually the basis for any of these facts, so
  neither is cited. Tapping the card opens this app's first bottom-sheet
  drawer (`renderFactDrawer()`) — a deliberate, reasoned exception to
  the existing full-screen-detail precedent (Church History, Unreached
  of the Day), since a single fact is lighter content that suits a
  quick peek-then-dismiss better. Its one CTA
  (`factLinkTarget()`) routes to whichever existing screen actually fits
  — Family Tree for a genealogy fact, a Story/Pattern/Verse detail page
  otherwise — no new navigation destinations, and two facts with no
  genuine fit get no CTA at all rather than a forced one. Card and
  drawer use this app's existing dark-theme tokens, not the separate
  bronze palette the three new Practice challenge types introduced;
  only the badge's emerald is a literal, scoped exact-hex exception.
  See DATA_MODEL.md §8, item 116.
- **Practice screen overhaul + app-wide emoji removal — done
  (2026-09-16).** Practice's landing screen got a `.practice-hero-card`
  (goal ring + challenge-type picker + a full-width "Start Practice
  Session (N Verses)" CTA, `renderPracticeHero()`), a one-line compact
  stats strip replacing the old 4-box grid (`renderPracticeStatsStrip()`),
  and sticky All/Due Today/Mastered filter tabs
  (`renderPracticeFilterTabs()`, new `practiceFilter` state). Verse
  cards' topic tags became soft lowercase hashtag pills (`.tag--pill`,
  `hashtagify()`) — a new scoped class, not a change to `.tag` itself
  (item 85 stays intact) — and mastery now shows as a 4-segment bar in
  each card's corner (`renderMasteryBar()`) instead of an uppercase tag.
  Separately: the only real emoji anywhere in the file (`MASTERY_LABELS`,
  🌱🌿🌳👑) were replaced with plain text, and a small inline-SVG icon
  system (`icon(name, size)`, real Lucide path data, `.app-icon` CSS)
  replaced the Tabler icon-font glyphs on the streak badge, Verse-of-
  the-Day, Word-of-the-Day/Church-History eyebrows, and the practice
  buttons — the bottom-nav icon and per-topic `TOPIC_ICONS` were left
  as-is, out of scope. See DATA_MODEL.md §8, item 107.
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
    users — with one named exception, `/api/unreached-of-the-day`, carved
    out as `allowedRoles: ["anonymous"]` *above* that wildcard rule, since
    Home shows that card to every visitor, signed in or not.
  - `api/` — the app's backend: an Azure Functions app (Node.js,
    v4 programming model — this folder *does* have a build step,
    `npm install`, handled by Azure's deploy action; the static frontend
    doesn't). Two endpoints: `GET/POST /api/sync` (`api/src/functions/sync.js`),
    backed by **Azure Cosmos DB for NoSQL (Free tier — free forever, not a
    trial)**, one document per signed-in user (see DATA_MODEL.md §7.1 for
    the full design — merge strategy, security boundary, why sign-in is
    optional); and `GET /api/unreached-of-the-day`
    (`api/src/functions/unreached.js`, added 2026-09-14), a thin proxy to
    the free [Joshua Project API](https://joshuaproject.net/api/v2) for
    Home's Unreached of the Day card — proxied rather than called directly
    from the browser so the API key (a `JOSHUA_PROJECT_API_KEY` Function
    App setting, **not yet set** — the card just silently doesn't show
    until it is) never ships in client-side JS, and so an unconfirmed CORS
    question on Joshua Project's side never becomes the app's problem. See
    DATA_MODEL.md §8, item 78.
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
  first run: **1,648 verses** — the entire Bible, Old and New Testament,
  is curated (finished 2026-09-10; see `DEFAULT_BOOKS` in
  `parse_books.py` for the full 66-book list, "Known gaps" item 9 for how
  the NT was approached, item 10 for the "deep study" supporting-cast
  expansion now underway, and DATA_MODEL.md §8 for the full,
  current per-book/per-era breakdown of everything below — this section
  intentionally stopped enumerating every book by name once the count
  made that unsustainable to keep current) — across **38 topics**
  (topics linked to related topics), plus **254 characters** with real
  relationships (father of, wife of, brother of, successor of, servant
  of, worked alongside, raised, etc. — see Connection, below). Note:
  fictional figures inside Jesus's parables (the good Samaritan, the
  prodigal son, etc.) do **not** get Character records — only real,
  named/identifiable people do, same as every OT figure.
- `data/characters.json` — the same 254 characters, standalone. Generated
  from the same curation as the starter pack, but not read by the app.
- `data/verses.json` — the **full** parsed corpus: the entire 66-book
  Bible (31,098 verses, WEB translation, public domain), matching
  `DEFAULT_BOOKS` in `parse_books.py`. Lazily fetched by the Browse
  screen the first time it's opened, never at boot. It is *reference
  material*, kept separate from the user's library — adding a verse
  from Browse copies it into the user's overlay. Only the 1,648 seed
  verses are topic-tagged; the rest of the corpus isn't yet.
- `data/stories.json` — 16 eras, **284 stories and 730 life events**,
  covering the whole Bible (see DATA_MODEL.md §8 for what's in each
  era — kept current there, not duplicated here). Loaded at boot (it's
  small). Drives the character life timeline, the Stories screens,
  People-grouped-by-era, and "appears alongside".
- `data/motifs.json` — **20** recurring biblical patterns, each with real
  instances in the current content, not force-fit onto single
  occurrences (see DATA_MODEL.md §8 for the newest). Loaded at boot.
  Drives the Patterns screens and the "Pattern" badges on Character,
  Story, and Verse detail pages.
- `data/connections.json` — 150 generic Connection edges (Design
  philosophy #4): family relationships, motif instances (`motif` →
  `story` / `character` / `verse`), and story↔story links
  (`"parallels"`, `"contrasts with"`). Loaded at boot.
- `data/word_of_the_day.json` and `data/daily_facts.json` — two Home
  cards' seed content: 13 curated Hebrew/Greek words (item 90) and 10
  verified Bible facts (item 116, 2026-09-17) respectively. (A third
  file, `data/church_history.json`, existed briefly for a "This Day in
  Church History" card — retired and deleted the same day the facts
  card shipped, item 117.) Both loaded at boot. **Not** part of the
  Bible-content curation pipeline below — hand-written editorial
  content, not Scripture text, so there's no `pipeline/curation/`
  source or `build_*.py` step for either; edit these files directly.
  Every fact in
  `daily_facts.json` was checked against this app's own real WEB verse
  text (and, where relevant, already-curated Character/Connection/Motif
  data) before being marked `"verificationStatus": "Validated"` — that
  label is load-bearing, shown to users as a "Verified Source" badge,
  so it's earned per-fact, not decorative.
- `pipeline/` — regenerates everything else in `data/`. See `pipeline/README.md`.
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

**Superseded 2026-09-10 — see v3 below.** The original style, kept here
for history: **warm storybook** — rounded cards, warm gold/sage/tan
accent palette on a cream background, Fraunces (serif) for verse text
and headings, Inter (sans) for UI text, Tabler icon font for
placeholder "portraits" until real character illustrations exist. Two
other directions (minimal/modern, rich/classical) were shown and
explicitly rejected in favor of this one, back when the app was first
being designed.

**Visual system v2 — done (2026-09-09), refined same day (v2.1).** The
warm-storybook direction was unchanged; this was an execution pass, not
a redirection, in response to "doesn't look like a polished app in the
market... looks basic." Surface elevation replaced hard 1px borders
(soft `box-shadow`, pure-white card fills on a warm linen `#F3EFE6`
ground — deepened once more in the v2.1 follow-up), the accent palette
collapsed from four colors to three clear roles (gold = action/urgency,
sage = progress/mastery, tan = plain metadata — plum retired, not
recolored), book/people/topics lists became borderless hairline-divided
rows instead of full cards, character and story detail pages opened on
a real hero header instead of a cramped 56px icon box, and the bottom
nav floated as a frosted, rounded overlay instead of a flush bottom bar
(**reversed 2026-09-17, item 121** — direct owner request moved it back
to a flush, edge-to-edge glassmorphism bar; see below).
Full rationale and every token's v2 value: DATA_MODEL.md §29.

**Visual system v3 — modern dark theme, done (2026-09-10).** Direct
owner request after the whole Bible was curated: a dark background
"like the YouVersion app" — inspired by it, not a copy — meant as a
first pass to spark further design ideas, with more design work planned
later. **Full swap, not a toggle** (the whole app is dark now, no
light/dark setting), and **Fraunces is dropped entirely** — the owner
chose an all-sans look over keeping the serif for verse text, so
Inter now carries everything, headings and stat numbers using weight
(700/800) and tightened letter-spacing for hierarchy instead of a
serif/sans contrast. Because every color already ran through the same
~15 CSS custom properties (v2's own design), the swap was almost
entirely new `:root` values, not new markup: `--paper` (page) → near-
true-black `#08090B`, `--paper-raised` (cards) → `#18191D`, `--ink` →
soft white `#F5F4F1`, and the gold/sage/tan accent triad re-picked (not
just inverted) for dark-background contrast and pushed more saturated
after an owner "darker and punchier" pass — gold `#F5AC1F`, green
`#1FE07F`, tan shifted from a light-mode brown to a cooler blue-gray
`#9FB0C3` since brown reads muddy on near-black. Wash tokens
(chip/badge backgrounds) changed shape too — solid light pastel hex →
low-alpha `rgba()` tints, since a solid pastel chip looks like a mistake
on a dark page. Cards/hero/stat-cards/back-btn each gained a subtle
`1px` hairline border alongside their box-shadow, since shadow alone
stops reading as elevation once the page itself is already dark. `icon.
png` is now visually mismatched against the new dark chrome — a known
gap, out of scope for this CSS-only pass.

**Topics screen → colorful card grid, done (2026-09-10).** Same v3
effort, next round: the owner shared an actual YouVersion screenshot
(its Discover tab) and asked what to borrow from it. Of five things
named (true-black ground, per-topic color coding, a neutral active-nav
pill, a home quick-action tile row, bold type), the owner picked the
colorful per-topic grid to build now — Topics went from plain rows to
a 2-column grid of solid-colored cards, one hand-picked icon and one
color per topic (a client-side hash + lookup table, `TOPIC_PALETTE`/
`TOPIC_ICONS` in `index.html`, not a `Topic` schema change). Verified
this time by actually running it locally and having the owner look at
it in a browser — the first real UI verification loop this project has
had, not just a markup/CSS-source read. Two more follow-ups landed the
same day: a search bar on Topics (mirroring People's own search
pattern exactly), and topic detail pages themed in that topic's own
color — done by locally overriding which color the existing "gold"
accent role points to for that one screen, so every component that
already reads `--gold`/`--gold-deep`/`--gold-wash` (verse-card refs,
the practice button, related-topic tags) picks it up for free, with
zero changes to any shared component. `Mastered`/`Due today` tags on
the same verse cards deliberately keep their normal sage/tan color —
re-theming those into the topic's color would blend away meaning the
three-role accent system (§29) still relies on. Full rationale, every
exact token value across all three passes, and the component-level
fixes beyond simple recolors: DATA_MODEL.md §8, items 62-64.

**Type scale — done (2026-09-14).** App-wide, not just Home this time: a
shared set of CSS custom properties (`--text-xs` 12px through `--text-2xl`
28px, plus `--text-primary`/`--text-secondary`/`--text-accent` and
`--font-sans`/`--font-display`) now backs eyebrows/badges, card/section
titles, body copy, scripture text, screen headings, and nav/CTA text
across every screen — replacing a decade of one-off per-component font
sizes. Two deliberate deviations from a literal token-everywhere pass,
both to protect meaning the app already depends on: verse status badges
(`.tag`) got the new size/weight/caps treatment but kept their existing
gold/sage/tan per-variant colors rather than one accent color (that
three-way split is rule 3's meaning, not decoration); `.topic-card .meta`
(verse counts) similarly kept white-on-opacity instead of the gold
`--text-accent`, since topic cards render on arbitrary saturated
per-topic colors where gold text wouldn't stay legible against all of
them. One real, flagged (not silent) product decision: Fraunces — scoped
to the Verse of the Day card only as of item 82 ("nothing else
references the family") — is now also used by `.verse-card .text` and
`.practice-verse`, on the owner's explicit instruction this time,
covering Home/Verse Detail/Practice as asked. Full writeup: DATA_MODEL.md
§8, item 85.

**Visual system v5 — bold white accent, done (2026-09-17).** Direct
owner request: didn't like the amber/gold accent, wanted something like
"bold white" instead. `--gold`/`--gold-deep`/`--gold-wash`/
`--gold-shadow` (and `--text-accent`, now a true alias of `--gold-deep`
rather than a separately-hardcoded near-duplicate hex) changed value —
token *names* were kept, so every one of the ~65 places that already
referenced them picked up the new look automatically, same "swap the
tokens" approach the original v3 gold pass used against v2. The one
color that was specifically tuned to pair with the old amber (`.btn.
primary`'s dark button text) was updated to match, rather than left
looking muddy against white. Per-topic color theming (items 62-64) is
unaffected — it already reassigns these same properties per topic at
render time. Same request also brightened Verse of the Day's background
photo (its dark overlay gradient was meaningfully lightened) and moved
its text off the italic Fraunces serif onto the app's own Inter sans —
the very last place in the app still using that serif at all. Full
writeup: DATA_MODEL.md §8, item 117.

**Bottom nav → transparent glassmorphism bar, done (2026-09-17),
revised hours later same day.** Direct owner request, and a real
reversal of v2's own decision above (flagged there, not silent):
`.navbar` moved back from a floating, inset, rounded pill to a flush,
edge-to-edge bar (`position:fixed;left:0;right:0;bottom:0`), with a
glassmorphism treatment — `rgba(20,18,16,.75)` background,
`backdrop-filter:blur(16px)`, a flat `border-top` instead of an
all-around border + shadow. Its active-tab color became bronze
(`#C69255`, matching the Practice challenge-types' own palette), and
the same request re-themed the Practice hero's "Start Practice Session"
CTA and the item-120 exercise-mode tiles to the same bronze. Full
writeup: DATA_MODEL.md §8, item 121. **Superseded the same day (item
122)** — the owner shared an actual screenshot of YouVersion's own
bottom nav ("I want the nav bar to look like this") plus "our theme for
the app is black and white": the bar's shape moved *back* to the
floating rounded pill (keeping item 121's blur, dropping its flush
geometry), and its bronze color — on the nav, the CTA, and the mode
tiles — reverted to the shared `--gold`/`--gold-deep` tokens (white).
The active tab is now a real color inversion matching the screenshot,
not a color swap: the dot chip goes solid white
(`background:var(--gold-deep)`), and its icon glyph flips to near-black
(`#141210`) specifically once it's sitting on that white chip — a new,
more specific selector (`.navitem.active .dot i`) than this app's usual
"recolor icon and label together" active-state pattern. Each individual
challenge type's own long-established bronze in-session palette (items
113-119) and the progress bar's own separate bronze spec (item 120)
were deliberately left alone — neither was shown or named in this
request. Full writeup: DATA_MODEL.md §8, item 122.

**Black and white only, app-wide — done (2026-09-17), same day as
items 121-122. Standing design direction going forward, not a one-off
pass — read this before adding any new color anywhere in the app.**
Owner's own words: "get rid of any other color theme in the entire app
and just stick with black and white for every element unless I
specifically tell you. This is a recent choice I made." Also asked the
floating nav specifically be turned up to "as transparent as possible"
— background alpha `.82`→`.3`, blur `16px`→`24px`.

Converted to grayscale: `--sage`/`--tan` (were green/blue-gray, the
"progress" and "metadata" roles of §29's three-role accent system — same
token names, same roles, just no longer color-coded, so every existing
reader picked it up for free), the Home streak badge (was an orange/red
flame gradient, now a solid white chip), the Fact of the Day's "Verified
Source" badge (was emerald — a decorative trust badge, not a game
state), every remaining literal bronze hex in the file (the Practice
progress bar/mode-tile grid, all five challenge types' own long-standing
in-session bronze palettes, and the Family Tree's bronze accents — items
110-121), and — the biggest single reversal in this pass — the colorful
per-topic grid from items 62-64, `TOPIC_PALETTE`'s 12 hues now 12 dark
grays (kept dark enough for `.topic-card`'s hardcoded white text to stay
legible). `topicAccentVars()` (the per-topic page-theming mechanism those
items also built) is now a no-op — re-theming a page to a grayscale
"accent" would either be indistinguishable from the app's default white
or a low-contrast dark wash, so Topic Detail pages now just use the
shared default tokens like everywhere else.

**Deliberately left alone — read as functional state, not decorative
theme, and this app's own genuine correct/wrong or error signal, not a
brand color choice**: `--danger`/`--danger-wash` (real form/validation
error text) and the hardcoded `#10B981`/`#EF4444` correct/wrong pairs
used across all five challenge types' own check states. If the owner
ever wants those gone too, that's a separate, explicit ask — "unless I
specifically tell you" is the standing rule for anything not covered
here. Full writeup: DATA_MODEL.md §8, item 123.

**Nav bar: precise glassmorphism capsule re-spec, done (2026-09-17),
same day as items 121-123 — a refinement of the same idea, not another
reversal.** A real structural change this time: the active tab now
highlights the *whole* button (icon + label together, full pill height,
`rgba(255,255,255,.14)` background) rather than the small icon-only
`.dot` chip every earlier pass used — `.dot` stays in the markup as a
pure flex-centering wrapper, no longer carrying its own background.
Container centering moved to `left:50%;transform:translateX(-50%)` with
a fixed `width:calc(100% - 32px);max-width:400px;height:68px`, and
`saturate(180%)` was added alongside the blur. Full writeup:
DATA_MODEL.md §8, item 124.

## Known gaps / not-yet-built (in likely priority order)

The full schema for all of the below (including the not-yet-built
entities) is designed in `DATA_MODEL.md`; §8 there is the current→target
migration checklist. Approach agreed with the owner (2026-09-03): design
the whole data model up front, then build in vertical slices — do **not**
hand-curate all the content before building.

1. More challenge types. **The original four (fill-in-blank, scramble,
   `challenge_first_letters`, `challenge_verse_ladder`) were retired
   2026-09-17 on direct owner request** ("get rid of the older
   exercises") — see item 114. `CHALLENGE_TYPES` (`index.html`,
   `DATA_MODEL.md` §3) now holds five:
   `challenge_tap_builder` (word-tile bank — auto-graded, auto-advances
   on a correct answer), `challenge_first_letter_sprint` ("First-Letter
   Sprint" — a real-time speed-typing drill, the first challenge type
   driven by actual keystrokes rather than taps),
   `challenge_progressive_vanish` ("Progressive Vanish" — a 5-stage
   reveal-then-recall climb, self-graded like Sprint but pure taps, item
   115), `challenge_clause_connect` ("Clause Connect" — split a
   verse into 3-5 clauses, scramble them, drag or tap-to-swap back into
   order, item 118), and `challenge_reference_match` ("Reference Match"
   — 4-option multiple choice, quote↔reference, added 2026-09-17, item
   119, the first type whose wrong path also auto-advances via the new
   `autoAdvanceMsWrong` interface field), with a picker (a 2x3 grid as
   of item 120, was a horizontally-scrolling `.segmented` row before
   that) persisted to `rooted-settings`. Next: matching/ordering
   (`challenge_story_order`, `challenge_character_match`). A 6th
   Practice-hero tile, **Mix & Match**, isn't a real `ChallengeType` at
   all — a sentinel `challengeTypeId` (`MIX_MATCH_ID` = `'mix_match'`,
   not a `CHALLENGE_TYPES` key) that resolves to a different random real
   type per verse at session-build time. Adding it required each
   practice-queue item to carry its own `challengeTypeId` rather than
   the whole session sharing one — see item 120.
2. ~~Real character portrait illustrations (currently icon placeholders).~~
   **Done — full coverage reached 2026-09-15**, after eleven batches
   generated over the course of that one day. All 267 characters in
   the starter pack now have a real generated portrait (stylized
   3D-animation style, a story-appropriate background per character,
   and — since the third batch — an explicit expression matched to
   whether their own arc is positive, negative, or neutral, after
   Paul's original portrait read unhappy despite his story ending in
   triumph), wired into both small avatars and Character Detail's
   hero. `data/character_portraits.json` holds 267 unique ids, each
   with a matching file in `media/characters/` — verified by script.
   The one earlier scope choice worth remembering: none of the first
   49 portraits, generated before the expression rule landed, were
   retroactively redone (deliberate, not an oversight — see item 93).
   Full batch-by-batch history: DATA_MODEL.md §8, items 91-101.

   Still not the full `Media` entity from design philosophy #3 — a
   flat manifest keyed by character id, rather than a proper linked
   entity with its own fields (art style, alt text, multiple
   images/variants, attribution). That was a reasonable shortcut while
   the batch was partial and still finding its own conventions
   (settings, expressions, description-overrides); now that coverage
   is complete and the conventions are stable, it's worth a real look
   at whether promoting to `Media` pays for itself — mainly if a
   second image variant per character (a dark-mode-tuned version, an
   alternate pose, a different art style entirely) becomes a real,
   not speculative, need. Observation only — not built as part of this
   batch.
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
   arrest in Rome — the note Acts itself ends on. All 21 epistles are
   done (light verses-and-topics treatment, per item 9's design
   note — none has narrative): Romans through Jude. **Revelation is
   now curated too — a Story for John's vision on Patmos (same
   treatment as Ezekiel's/Daniel's call narratives), then
   verses-and-topics for the seven letters, the throne room, the
   judgments, and the new heaven and new earth. The entire 66-book
   Bible is now fully curated.** Full detail in DATA_MODEL.md §8, items
   41 onward (that's the authoritative running log — this file's own
   "Done" changelog below stopped narrating every NT installment in
   full prose partway through, to stay sustainable across what's a
   much larger body of work than the OT already was).
10. **"Deep study" supporting-cast expansion — started 2026-09-11,
    owner's direction, right after the whole Bible was first curated.**
    Every book so far only got its *major* figures and events — the
    owner wants the app to go deeper: capture the supporting characters
    who genuinely move a story forward even when they're not headline
    names (Abner, Ittai, Ahithophel, the wise woman of Abel — not just
    David, Absalom, Nathan). The bar is narrative importance, not a
    mention-count threshold — a character who drives a real plot turn
    qualifies even if the raw name-frequency across the corpus is low.
    This is explicitly a long-haul, multi-session project, worked the
    same additive way the whole-Bible curation was: one book or
    supporting-cast cluster at a time, same pipeline discipline (real
    WEB text, one-off curation script, all four builders, `--check`,
    docs, `sw.js` bump). First pass: 2 Samuel's civil-war/rebellion
    supporting cast (Abner, Asahel, Abishai, Ahithophel, Hushai, Ittai,
    Shimei, Amasa, Sheba, the wise woman of Abel) — 10 new characters,
    6 new stories, all inside the existing `era_united_kingdom` era, no
    new topics needed. **Second pass (2026-09-11): Paul's circle** — a
    much bigger gap than expected, since almost none of it was curated
    at all, not even Timothy or Titus despite epistles addressed to
    them by name. 10 new characters (Priscilla, Aquila, Apollos, Lydia,
    John Mark, Timothy, Titus, Onesimus, Philemon, Demas), 8 new
    stories, all inside the existing `era_early_church`, no new topics
    needed — including 3 new life events on already-curated characters
    (Barnabas, Paul ×2) where the new material was genuinely also a
    beat in *their* own story, not just the new character's (e.g.
    Barnabas splitting from Paul over a second chance for John Mark).
    **Lesson learned the hard way, caught by the owner checking Paul's
    own page after that batch:** a new story needs the *existing*
    major character tagged too whenever they're genuinely present in
    the scene, not just the new minor character it's "about" —
    `characterStories()` shows a story only where its `characterIds`
    says to, silently, so an untagged major character never surfaces
    an error, the story just never shows up on their page. Both this
    pass (3 of 8 stories missing `char_paul`) and the previous one (all
    6 of 2 Samuel's new stories missing `char_david`, despite every one
    centering on a decision he makes) had the same gap, fixed together
    once found — see DATA_MODEL.md §8, item 69, and the checklist added
    to `pipeline/README.md`'s lessons-learned section.

    **Third pass, and the biggest yet (2026-09-11): Genesis's supporting
    cast.** Only the direct patriarchal line (Abraham through Joseph)
    had ever been curated — Jacob's other eleven sons, both
    concubine-wives, Dinah, Judah's daughter-in-law Tamar, Laban,
    Potiphar and his wife, Abraham's servant, and the prison cupbearer
    and baker were never touched at all. 16 new characters (Reuben,
    Simeon, Levi, Judah, Benjamin, Bilhah, Zilpah, Dinah, Shechem,
    Tamar, Laban, Potiphar, Potiphar's wife, Abraham's servant, the
    cupbearer, the baker), all inside the existing `era_patriarchs`.
    This pass leaned harder on **extending existing Stories** than
    adding new ones — six already-curated Genesis stories (Rebekah at
    the well, Jacob/Rachel/Leah, Joseph sold, Joseph and Potiphar,
    Joseph interprets dreams, Jacob blesses his sons) got the new
    characters folded directly in, since the supporting cast was
    always part of those same scenes; four genuinely new stories
    (Dinah and Shechem, Reuben and Bilhah, Judah and Tamar, the
    brothers' return for Benjamin) cover material with no existing
    Story at all. Applied item 69's lesson throughout from the start
    this time rather than fixing it after the fact — every story lists
    every major existing character genuinely present (Jacob tagged on
    Dinah's story and Reuben's, Joseph tagged on the brothers'-return
    story), each with their own new life event too.

    **Fourth pass (2026-09-11): spanning three books at once** — 1
    Samuel (Nabal, Abigail, Doeg, Ahimelech, Abiathar, Achish — David's
    fugitive years under Saul), Exodus (Jethro, Shiphrah, Puah), and
    Numbers (Phinehas, and Zelophehad's five individually-named
    daughters — Mahlah, Noah, Hoglah, Milcah, Tirzah — whose petition
    for their father's inheritance actually changes Israel's
    inheritance law on the spot). 15 new characters, 7 new stories.
    Same discipline as pass 3: David, Saul, and Moses are each tagged
    and given new life events on every one of these stories they're
    genuinely present for, applied from the start rather than
    discovered as a bug afterward.

    **Fifth pass (2026-09-11): the Gospels' supporting cast.** The
    individual, personal healing/interaction stories — as opposed to
    the big "nature miracles" (storm, walking on water, feeding the
    5000) already curated — had never been given their own characters
    or Stories at all: Bartimaeus, Jairus and the woman with the issue
    of blood (interwoven in one episode), the centurion of Capernaum,
    the widow of Nain, Malchus (the arrest), the centurion at the
    cross, Simon the Pharisee and the forgiven woman who anoints
    Jesus's feet, Joanna and Susanna (the named women who financially
    supported the ministry), the man born blind, the paralytic lowered
    through a roof, and Simon the leper (host of the anointing at
    Bethany). 14 new characters, 9 new stories, plus Malchus and the
    centurion at the cross folded into two already-existing stories
    (`story_betrayal_and_arrest`, `story_crucifixion`) rather than
    duplicated. `char_jesus` — already carrying 39 life events, one for
    nearly every existing Gospel story — got 9 more, one per new story
    he's the one acting in; `char_peter` got one for cutting off
    Malchus's ear. No new topics.

    **Sixth pass (2026-09-11): four books at once again** — Job
    (Bildad, Zophar, Elihu, and Job's wife — only Eliphaz had ever been
    curated, despite Bildad and Zophar each getting a full chapter of
    dialogue and Elihu a young fourth voice Yahweh never rebukes), 1
    Kings (Obadiah, who hid a hundred prophets from Jezebel; Micaiah,
    the one prophet Ahab openly hates for telling him the truth),
    Esther (Hegai, Zeresh, Harbonah — the supporting cast around the
    gallows Haman built for Mordecai and was hanged on himself), and
    Acts (Ananias and Sapphira; Simon Magus and Philip the evangelist;
    Rhoda, the servant girl who's so overjoyed at Peter's prison escape
    she forgets to let him in; Eutychus, raised after falling from a
    third-floor window). 15 new characters, 6 new stories, 7 existing
    ones extended. Same discipline: Job, Elijah, Ahab, Jehoshaphat,
    Esther, Haman, Peter, and Paul are each tagged and given matching
    new life events on every story they're genuinely part of.

    **Seventh pass (2026-09-12): Genesis, Numbers, Judges, and 2
    Kings.** Melchizedek (Genesis's one-scene king-priest who blesses
    Abram and receives the Bible's first tithe), the recurring
    "Abimelech king of Gerar" role appearing with both Abraham and,
    a generation later, Isaac, Balak (Balaam's employer, furious when
    the curse he paid for becomes a blessing), Judges' first judge
    Othniel and the one-verse deliverer Shamgar, a second, much darker
    Abimelech — Gideon's own son, who kills his seventy brothers and
    makes himself king before dying by a millstone — the four "minor
    judges" (Tola, Jair, Ibzan, Elon, Abdon), and Athaliah's six-year
    usurpation with Jehosheba's rescue of the infant Joash (folded into
    the *existing* `story_joash_and_zechariah`, which already spanned
    his whole reign, rather than a duplicate new Story). 13 new
    characters, 7 new stories, 2 existing ones extended. Abraham,
    Sarah, Isaac, and Rebekah are each tagged and given a matching new
    life event on the Abimelech stories they're part of.

    **Eighth pass (2026-09-14): a Gospel/Acts content-audit gap-fill,**
    not a supporting-cast pass in the usual sense but the same
    pipeline discipline applied to well-known *major* episodes the
    owner found were simply never curated at all, despite their verse
    text already sitting in `data/verses.json`. Highest priority, named
    directly by the owner: John 21's breakfast on the shore and Peter's
    threefold restoration ("feed my sheep"), tagging both Jesus and
    Peter. Individual healings/encounters never given their own Story:
    the Gerasene demoniac ("Legion"), the pool of Bethesda, the ten
    lepers (the one who returns is a Samaritan), the Syrophoenician/
    Canaanite woman's daughter, and Mary and Martha (both sisters
    already existed as characters from the Lazarus curation, so this
    reused them rather than inventing new ones). Feeding the four
    thousand, curated as genuinely distinct from the already-curated
    five thousand — no forced Connection between them, per the owner's
    own instruction. The widow's offering, needing this pass's one new
    topic, `topic_generosity`. The death of John the Baptist — two new
    characters, Herod Antipas and Herodias, connected by a real
    "husband of"/"wife of" fact from the text; his eraId was already
    `era_jesus_ministry`, so no era move was needed; Jesus is
    deliberately *not* tagged on this one, since he isn't in the scene.
    Five more parables as Stories, matching the prodigal-son/
    good-Samaritan precedent: the lost sheep and lost coin (one Story
    for both), the rich man and Lazarus (a different, fictional
    Lazarus from Bethany's — no Character record, same as every other
    parable figure), and all three Matthew 25 parables (talents, ten
    virgins, sheep and goats) — placed in the Passion-week era, not
    general ministry, since Matthew 25 is the Olivet Discourse,
    delivered the Tuesday before the crucifixion. In Acts: Dorcas/
    Tabitha raised by Peter, the Ephesus riot (Demetrius the
    silversmith), and Paul's farewell to the Ephesian elders. The one
    real gap this pass caught and fixed rather than just filled:
    `story_pauls_arrest` had quietly compressed Paul's arrest *and* his
    years of trials before Felix, Festus, and Agrippa into a single
    5-verse story — split into a properly scoped arrest story plus a
    new `story_pauls_trials` with three new characters (Felix, Festus,
    Agrippa) tagged alongside Paul. The one genuinely new judgment call
    this pass required: John 2's temple cleansing (start of ministry)
    and the Synoptics' temple cleansing (Passion week, the day after
    the triumphal entry) are curated as two distinct events, not one
    story told by different Gospels — unlike the feeding of the five
    thousand or Isaiah 36-39/2 Kings 18-20, nothing in either account
    signals the other Gospel's moment, and driving traders back out of
    a temple that drifted back into commerce, years apart, is a
    plausible repeated action, not a duplicate telling. 20 new stories,
    7 new characters, 54 new curated verses, 1 new topic, 1 new
    connection, no new eras.

    **Ninth pass (2026-09-15): a second content-gap audit, verified
    against the data before curating, not guessed.** The first audit
    (eighth pass, above) covered the Gospels and Acts; this one found
    more real gaps in Genesis and, again, Acts. In Genesis: the Tower
    of Babel (no named individuals, so no new characters — Genesis
    11:1-9 never has one), Noah's drunkenness and the curse of Canaan
    (four new characters — Ham, Shem, Japheth, Canaan — each
    individually blessed or cursed by name, the same bar Jacob's
    twelve sons cleared), and Enoch's four terse genealogy-formula
    verses ("he walked with God... he was not found, for God took
    him") — a real judgment call, decided *against* a Story (unlike
    Melchizedek, which kept its Story on similarly few verses because
    it's an actual scene with dialogue and action), so Enoch got just
    the two verses and a new character, no Story. In Acts: Paul and
    Barnabas mistaken for gods and Paul stoned at Lystra (Acts
    14:8-20) — a real compression gap, same shape as the eighth pass's
    Paul's-trials fix: `story_pauls_first_missionary_journey` cited
    Acts 13:1-14:28 but carried only 2 verses, so Lystra got its own
    properly-scoped story alongside it, not instead of it. The
    choosing of the seven (Acts 6:1-6) — Stephen and Philip the
    evangelist both already existed and got new life events, but the
    other five named men (Prochorus, Nicanor, Timon, Parmenas,
    Nicolaus) didn't clear this project's narrative-importance bar the
    way Zelophehad's five daughters did (the daughters individually
    petition Moses and change inheritance law; these five are named
    once and never act again) — so no new Character records for them,
    a deliberate, consistent call rather than an oversight. And the
    death of Herod Agrippa I (Acts 12:20-23, struck down and eaten by
    worms for accepting a crowd's worship) — verified as a genuinely
    different person from the already-curated Herod Antipas (his
    uncle, not the same man who killed John the Baptist), with a new
    "nephew of" connection linking them explicitly so the two Herods
    stay distinct in the data the way the two Josephs and two
    Zechariahs already do. 9 new stories, 6 new characters, 47 new
    curated verses, 5 new connections, no new topics, no new eras.

    See DATA_MODEL.md §8, items 65-67, 70-74, 86, and 88, for the full
    writeup and the reasoning behind which figures made the cut each
    pass.

    **"People in this book" — done (2026-09-12), redesigned same day.**
    As the per-book cast list got genuinely rich (2 Samuel alone now has
    22 named people), the owner asked for a way to open a book on the
    Browse screen and see everyone tagged in it. First version was a
    pill list inline above the chapter grid; direct feedback asked for
    a proper tab instead — tapped into its own screen, people listed in
    the order they appear through the book (not alphabetically), and
    back navigation returning to that same screen rather than the
    generic People list. That last part needed a real fix rather than
    a one-off: `open-character` now always carries `from: view` the
    same way `open-verse`/`open-story`/`open-motif` already did, so
    Character detail's back button returns to wherever the user
    actually came from everywhere it's used, not just from this one
    screen. No new `Character.book` field either version — a character
    routinely spans several books (Moses, Exodus-Deuteronomy; David,
    Samuel-Kings-Chronicles), so membership is derived at render time
    from `data.verses` instead of forcing a false one-book choice. See
    DATA_MODEL.md §8, item 75.

    **Fix (2026-09-12):** Cain, Abel, and Lot — real characters with
    real Stories since the project's very first pass — never showed up
    in "People in Genesis." 15 characters project-wide have zero verses
    individually tagged to them (their scene's verse got tagged to a
    co-star instead); `charactersInBook()` only read verse tags, so it
    missed all of them. Fixed by also crediting every character in a
    Story's `characterIds` whenever that Story has a curated verse in
    the requested book, not just whoever the verse itself named. One of
    the 15, Hagar, needed an actual content fix — both her Stories had
    sat with empty `verseIds` since their original curation, so nothing
    existed for either signal to find; added 8 real verses to fill them
    in. See DATA_MODEL.md §8, item 76.

    **Third content-gap audit, batch fill — done (2026-09-15).** Not
    the supporting-cast passes above, but the same "find a real, verified
    gap and fill it" discipline applied a third time (after items 86 and
    88's Gospel/Acts and whole-Bible audits) — 11 new stories, zero new
    characters, 63 new curated verses, 4 new life events: six more Gospel
    episodes in `era_jesus_ministry` (the woman caught in adultery, Jesus
    rejected at Nazareth, the sending of the twelve, the sending of the
    seventy-two, and — decided as two genuinely distinct parables rather
    than one story told twice, given how much Matthew's king/armies/
    wedding-clothes version diverges from Luke's simpler dinner-party one
    — the wedding banquet in `era_passion_and_resurrection` and the great
    feast in `era_jesus_ministry`); Aaron's rod budding (Numbers 17)
    folded into the existing `story_korahs_rebellion` as a direct
    continuation, not cloned; Elisha's floating ax head (2 Kings 6:1-7) —
    the real gap, since checking first showed the blinded army half of
    that chapter was already curated; and the Levite's concubine and the
    war against Benjamin (Judges 19-21), curated directly and factually
    across three Stories at the text's own scene breaks, per the owner's
    explicit direction that this material belongs in the app. No new
    characters anywhere in this batch — every gap turned out to involve
    either unnamed figures or people already curated (including
    `char_phinehas`, tagged on the Benjamite war for standing before the
    ark, the same "tag the existing major character too" discipline as
    items 66-67). Full writeup, including the verse-selection judgment
    call on the Judges material: DATA_MODEL.md §8, item 89.
11. **Home redesign / identity shift — done (2026-09-14).** Memorization
    moved off Home entirely onto its own new Practice tab; Home is now
    Verse of the Day plus Unreached of the Day. The owner set
    `JOSHUA_PROJECT_API_KEY` the same day — verified live against the
    deployed endpoint, real data flowing (a real people group, correct
    fields, a working photo). That photo prompted an immediate
    same-day addition: the card was originally text-only, but since
    Joshua Project already includes a photo URL for free with every
    response, `renderUnreachedCard()` now shows it as a 160px banner
    above the text. Full writeup: DATA_MODEL.md §8, item 78. The card's
    photo and layout were then iterated twice more the same day on direct
    feedback (detail page + crop fix, then a hand-sketched side-by-side
    redesign — items 79-80), and Home gained two more editorial pieces
    plus one deliberate, subtle exception the same day: `verse-of-the-day.js`
    and `verse-image.js` (new Azure Functions, proxying YouVersion's
    Platform API for the verse text and Unsplash for a separately-sourced
    background photo, both server-side-key-only like Joshua Project), a
    Motif Spotlight card surfacing the curated Patterns on Home, and
    `renderPracticeNudge()` — one quiet text line ("N verses due for
    practice") shown only when something's due, the one intentional
    exception to item 78's "no practice on Home" rule, built to the
    owner's explicit "keep it subtle" brief rather than the button
    originally sketched. Needs `YOUVERSION_APP_KEY` and
    `UNSPLASH_ACCESS_KEY` set in Azure Portal (both cards just render
    without their remote content until then, same fail-quiet pattern as
    Joshua Project). Full writeup: DATA_MODEL.md §8, item 81. That
    version ("doesn't look good") was replaced the same day by a full,
    hand-specified redesign (item 82): a greeting/streak header
    (`renderHomeHeader()`, streak badge back on Home — an explicit
    reversal of item 81's choice to leave it off, this time by direct
    request, not silently), the Verse of the Day card rebuilt as a
    full-bleed `.votd-hero` with Fraunces serif text over a photo/
    placeholder background, Unreached of the Day and a new Story of the
    Day sharing one `.discovery-card` row format (text left, rectangular
    thumbnail right), and `renderPracticeNudge()` restyled into a
    higher-contrast "Practice N of M due verses" pill. Motif Spotlight
    is gone (not in the new spec). `placeholderArt()` (new) generates a
    hue-seeded inline-SVG placeholder image with zero external
    dependency, standing in for Unsplash/story-illustration photos until
    those exist. The bottom-nav "People" tab is now labeled **Study**
    (same route, since it already held People/Stories/Patterns). Full
    writeup: DATA_MODEL.md §8, item 82. That same day, the owner supplied
    two real photos to use in place of `placeholderArt()`'s generated
    SVGs specifically for the VOTD hero and Story of the Day thumbnail —
    resized/compressed with Pillow before committing (the source mountain
    photo was ~4MB at 5760×3840) to `media/home/votd-placeholder.jpg` and
    `media/home/story-placeholder.jpg`, precached in `sw.js`. Unreached of
    the Day's own fallback still uses `placeholderArt()` — no supplied
    photo exists for that slot. Full writeup: DATA_MODEL.md §8, item 83.
    A same-day CSS polish pass (item 84) then applied exact spec'd values
    across the VOTD hero (background position, radius/border, label/ref
    color), its frosted-glass "Read chapter" CTA, the shared discovery-
    card thumbnails (now pinned to 88×68/14px radius), and a new, larger
    `.home-settings-btn` scoped to Home's own settings button (not a
    global `.back-btn` change). Full writeup: DATA_MODEL.md §8, item 84.
    Then, after two rounds of content-gap curation on 2026-09-15 (see
    item 10 above), two more Home cards: **Word of the Day** (a curated
    Hebrew/Greek term with its Strong's id, meaning, and linked verses —
    `data/word_of_the_day.json`, 13 entries) and **This Day in Church
    History** (`data/church_history.json`, keyed by local `MM-DD`, 13
    verified dated entries plus a `"default"` fallback). Both are new,
    separate seed datasets, not part of the Bible-content curation
    pipeline (`pipeline/curation/*.json`) — they're editorial content in
    the same vein as Verse/Unreached/Story of the Day, not Scripture
    text. Every church-history date was checked via web search before
    being written in, not recalled from memory — presenting a wrong date
    as historical fact would be a real problem for an educational
    feature. Two deliberate deviations from the literal request, both
    documented rather than silent: the card surface uses the existing
    `var(--paper-raised)` token instead of a new literal hex (avoids two
    near-identical "dark card" shades on the same feed), and Church
    History's detail view is a normal full screen (matching Unreached of
    the Day's own detail page) rather than a new bottom-sheet modal —
    this app has no modal/overlay component anywhere else. Full writeup:
    DATA_MODEL.md §8, item 90.
12. **The Study pillar's "deep theological suite" — partially built.**
    Architecture committed 2026-09-16 (item 109); Timeline and Family
    Tree shipped the same day (item 110, in a proper `renderStudy()`
    hub alongside Patterns — see the "Done" bullet above). Two real
    features are still needed to fully match the "deep theological
    suite" framing the owner specified:
    - **Interlinear/Strong's view** — original-language word data
      (Hebrew/Greek, Strong's numbers, definitions) tied to individual
      verses. `data/word_of_the_day.json` (item 90) is the closest
      existing thing — 13 hand-curated words, editorial content, not a
      per-verse interlinear. A real version needs per-verse-per-word
      Strong's tagging across the corpus, which is a genuinely large
      new curation effort, not a small schema addition.
    - **Commentaries** — theological/historical commentary text tied to
      verses, stories, or characters. No entity for this exists in
      DATA_MODEL.md at all yet; needs its own schema design (most
      likely its own linked entity, per design philosophy #3's
      precedent with Media, rather than embedding commentary text
      directly on Verse/Story/Character) before any content work starts.

    The "interactive connection node graph" item from the original
    architecture note is effectively superseded by the Family Tree
    feature (item 110) — same underlying `Connection` entity, same
    SVG/pan-zoom shape, just scoped to the core family relationship
    types rather than every connection kind (motif instances,
    story↔story links, etc.). A future generalized "explore any
    connection" graph (not just family) is still a real, separate
    possible feature, but Family Tree covers the specific ask that
    prompted this item.

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
