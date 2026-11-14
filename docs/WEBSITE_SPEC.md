# Website spec: Planetary Twin Finder

Written 13 November 2026 (updated the same day for Impeccable) from a screen recording of a reference site the team
likes (a satellite company's scroll-story page). We take its **structure and
motion**: pinned full-screen scenes, a 3D globe that changes with the scroll,
huge uppercase headlines, a chapter progress bar and a fixed call to action.
We do **not** take its code, text, images, 3D models or logos. Every word,
number and image here is ours and comes from `web/public/data/` or the HANDOFF.
No NASA logos anywhere (competition rule); writing "NASA" in text is fine.

The site has two parts:

1. **The story** (`index.html`): one long scroll page that explains the
   whole project, scene by scene, for someone who has never heard of it.
2. **The Twin Finder** (`explorer.html`): the working interface. The story
   ends on a big button that opens it, and a small fixed button opens it from
   anywhere.

---

## 0. Design tool: Impeccable (required)

Build the website with the **Impeccable** skill:
https://github.com/pbakaus/impeccable (Apache 2.0, version 4.9.0 at the time
of writing). It stops the site looking AI-made: it has a design playbook for
new pages, a quality floor, and a detector with 62 rules that flags AI tells
(overused fonts, eyebrow labels above headings, gradient text, cards in
cards, glass for decoration and so on).

- **Install** for this project only, for Claude Code, with the design hook:
  `npx impeccable install --providers=claude --scope=project`, and accept the
  hook. Reload Claude Code. (Or the plugin: `/plugin marketplace add
  pbakaus/impeccable`.) The installer also downloads an engine binary into
  `~/.impeccable/bin/`; check where it comes from before running it, as
  CLAUDE.md says for every installer.
- **Start** with `/impeccable init`, so it writes `PRODUCT.md` from this
  spec, HANDOFF.md and the code. Then build the story page as new work
  (Persuade mode) and the Twin Finder as Operate mode.
- **Finish** with `/impeccable audit` and `/impeccable polish` on both pages,
  and run `npx impeccable detect http://localhost:5173` before deploying.
- Commit the files it adds (`PRODUCT.md`, `DESIGN.md`, `.impeccable/`
  config, the skill under `.claude/`) like any other code, on the website
  branch. Nothing secret goes in them.

### What this spec pins, and what Impeccable decides

When this spec and Impeccable disagree, follow this table:

| This spec decides (pinned) | Impeccable decides |
|---|---|
| All **content**: every sentence, number, name, image and data file. Only our own work, from `web/public/data/` and HANDOFF.md. Nothing invented. | **Typography**: display and body faces, sizes, weights, case, spacing. The Inter Tight / Inter idea below is only a starting point; Impeccable flags Inter as overused, so let it pick. |
| The **storyboard**: the scenes in section 3, their order, and the motion idea of each (pinned scroll scenes, the globe changing, the tile stack, the rank counter) | **Shapes and components**: buttons, panels, cards, bars, the chapter indicator, icon style, borders, radii, shadows |
| The two pages and the link between them (story → Twin Finder) | **Layout details**: spacing, grid, composition inside each scene |
| The **world colours**: Mars `#e0703a`, Moon `#c4c9d1`, Earth `#5aa9e6` | Every other colour: ground, accents, text greys (keep the world colours recognisable) |
| Honesty rules: Moon shows rank, limits stated, no NASA logos, credits | Anything on its "refuse" list that this table doesn't pin |

So: **no eyebrow or kicker labels above headings** (Impeccable bans them),
even where the scene text below mentions one; fold that line into the
heading or the body. No gradient text, no decorative glass.

The reference site is near-black with one bright blue accent. Impeccable
lists "near-black with one neon accent and glowing edges" as a common AI
look. The **structure and motion** of the reference are pinned; its exact
palette is not. Let Impeccable choose a ground and accent that fit the
planetary subject.

## 1. Look and feel (starting point, not pinned)

| Element | Starting idea |
|---|---|
| Background | dark, with a faint star field |
| World colours (pinned) | Mars `#e0703a`, Moon `#c4c9d1`, Earth `#5aa9e6` |
| Headlines | very large, bold, tight, uppercase in the reference |
| Body | readable, 18 to 22 px |
| Numbers | very large for counters, tabular figures |

Self-host every font so the demo works offline.

**Always on screen** (after the hero):

- **Fixed button**, bottom right: `LAUNCH THE TWIN FINDER ↗`, small uppercase
  text plus a square arrow icon, links to `explorer.html`.
- **Chapter bar**, bottom centre: a row of small segments, one per scene, that
  fill with blue as you scroll. The current chapter shows its name in the
  segment (`PROBLEM`, `METHOD`, `PROOF`, `EGYPT`, `MOON`, `LIMITS`). Clicking a
  segment scrolls to that chapter.
- **Header** (hero only, then hides on scroll down and shows on scroll up):
  logo text, links `Story`, `Twin Finder`, `Egypt`, `Method`.

---

## 2. Tech

- **Vite** + vanilla JS (or React if the team prefers), static build, no
  server. Deploy the `dist/` folder.
- **three.js** for every globe and 3D scene. One WebGL canvas fixed behind
  the page; each scene changes what it shows.
- **GSAP + ScrollTrigger** for pinned scenes and scroll-scrubbed timelines
  (GSAP and all its plugins are free to use).
- **Lenis** for smooth scrolling, wired to ScrollTrigger.
- Everything works with the mouse wheel, trackpad, touch and the keyboard.
  Respect `prefers-reduced-motion`: replace scrubbed animation with simple
  fades and stop the globes spinning.
- Phone: scenes still pin, text sizes drop, globes shrink and sit behind the
  text. Test at 390 px wide.
- Performance: one renderer, textures at most 4096 x 2048, pause rendering
  when the tab is hidden, aim for 60 fps on a laptop.

### Textures (all public domain or open)

| Globe | Texture | Source |
|---|---|---|
| Earth | Blue Marble colour map | NASA Visible Earth |
| Earth "dotted" look | points sampled on land only | built from a land mask (Natural Earth, public domain) |
| Mars | colour mosaic `web/public/img/mars.jpg` (Viking), plus MOLA elevation as a bump map | NASA/JPL/USGS |
| Moon | LROC colour map `lroc_color_2k.jpg`, and the LOLA elevation as a bump map | NASA SVS CGI Moon Kit (svs.gsfc.nasa.gov/4720) |

Credit each one on the About section and in `credits`.

### 3D models: none needed

- **Planets** are spheres with real textures and bump maps (above). No model
  makes them better.
- **The tile stack** (scene 7) is built from our own data: the Jezero tile's
  elevation as a three.js height field, split into four layers. That is more
  honest and more on-topic than any downloaded model.
- **Optional extra, only if time is left:** a Perseverance rover model in the
  Jezero scene. NASA publishes it free (public domain) on its 3D resources
  site. Use a GLB under 10 MB and credit it.
- **If you need any asset you can't make or download yourself**, stop and
  tell the user exactly what: what it is, the format (GLB, PNG, JPG), the
  size, and that it must be public domain or CC0. The user will get it.
  Never use an asset with an unclear licence.

---

## 3. The story, scene by scene

Each scene is pinned for roughly one to two screen heights of scrolling, with
the animation scrubbed to the scroll. Times in brackets are where the same
kind of moment happens in the reference recording.

### Scene 1 — Hero (reference 0 to 3 s)
- Left: headline `FIND MARS ON EARTH`, and a short line under it (not
  above): `NASA Space Apps 2026 · Team Duplica · Cairo`.
- Right: a large slowly turning **Mars** globe with a soft orange rim light.
- On scroll: the headline slides up and fades; the camera drifts down so the
  globe's edge becomes a curved horizon at the bottom of the screen.

### Scene 2 — The problem (4 to 5 s)
- One sentence that **fills from grey to white word by word** as you scroll:
  "Astronauts rehearse Mars and Moon missions at a few places on Earth, chosen
  mostly by experience, not by searching the whole planet."
- The dark planet edge stays on the right.

### Scene 3 — Our idea (6 s)
- Same word-by-word fill:
  "We give every patch of ground on Earth, Mars and the Moon the same profile,
  and let the data find the closest twins."
- The globe turns into **Earth drawn as glowing dots** (land points only).

### Scene 4 — Two steps (7 to 9 s)
- The dotted Earth sits in the centre. `PICK` appears on the left with small
  text `A SITE ON MARS OR THE MOON`; `MATCH` on the right with `ITS TWINS ON
  EARTH`.
- Then both fade and a centred line appears: `ACROSS 130,060 PLACES`, with a
  thin blue bar that fills left to right as you scroll.

### Scene 5 — Three worlds, one ruler (10 to 12 s)
- The dotted Earth fills in with the real Blue Marble texture.
- Headline `THREE WORLDS. ONE RULER.`
- Small Mars and Moon globes slide in either side, so all three are on screen.
- The chapter bar appears here.

### Scene 6 — Step 1, pick (13 to 14 s)
- Zoom into a **flat Mars map** (`mars.jpg`) filling the screen, slightly
  darkened. Top left: `PICK A TARGET` (a step number is fine here: the two steps are a real sequence).
- A side panel on the right, titled `SELECT A WORLD`, with two tabs
  (`MARS · 38 ZONES`, `MOON · 9 REGIONS`) and a grid of target thumbnails
  (shaded relief from `web/public/data/shade/mars/`).
- The Jezero tile is highlighted.

### Scene 7 — How a tile is measured (15 to 19 s)
The reference shows an exploding wireframe satellite. Ours is an **exploding
stack of terrain tiles**:
- A 3D wireframe square of terrain (a height field from the Jezero tile,
  drawn as blue lines) floats on a dark grid.
- Step by step, it separates into four stacked layers, each labelled as it
  separates: `SLOPE`, `ROUGHNESS`, `RELIEF`, `BRIGHTNESS`.
- Text on the left changes with each step:
  1. "Every world cut into 9 km tiles at the same 463 m pixel size"
  2. "Four numbers per tile: slope, roughness, relief, brightness"
  3. "On Earth, anything with plants, water or ice is removed"
- The chapter bar moves from `METHOD` step 1 to 3.

### Scene 8 — Step 2, match (20 s)
- The tile stack flies off. `MATCH ITS TWINS ON EARTH`, top
  right. Earth rises as a horizon at the bottom.

### Scene 9 — The Twin Finder (21 to 24 s)
- Headline `THE TWIN FINDER`.
- A screenshot (or live mini version) of `explorer.html` appears tilted in 3D
  over the globe, and turns flat as you scroll.
- Three captions, one at a time, alternating left and right:
  1. "Click any site on Mars or the Moon"
  2. "See its closest places on Earth, ranked"
  3. "Read why they match, and why they don't"

### Scene 10 — Three promises (25 to 27 s)
The dotted globe again, big word on one side, small blue line under it:
- `BLIND-TESTED` / `92.5% FOUND NASA'S OWN TRAINING SITES`
- `OPEN DATA` / `NASA AND ESA, FREE FOR ANYONE`
- `HONEST` / `EVERY MATCH SAYS WHAT DOESN'T MATCH`

### Scene 11 — Egypt (28 to 32 s)
- Headline `JEZERO ↔ EGYPT`.
- The two shaded relief images (`shade/mars/jezero.webp`,
  `shade/earth/jezero_1.webp`) sit side by side, tilted in 3D, then flatten.
- Four closeness bars fill as you scroll: Slope 97%, Roughness 99%, Relief
  100%, Brightness 99% (from `matches/jezero.json`).
- Caption: "Jezero crater, where Perseverance landed. Its closest twin in all
  of Africa is in Egypt's Eastern Desert, 25.13°N, 34.54°E."

### Scene 12 — The counter (33 to 38 s)
The reference rolls a cost number down. Ours rolls a **rank**:
- The line `Jezero's closest twin in Africa` sits under the number, not above it.
- A giant number rolls from `130,060` down to `#1` as you scroll, digits
  flipping like an odometer. Under it: `RANK AMONG DRY PLACES IN AFRICA`.
- Left small text: "Every Mars-possible place in Africa, ranked against the
  same crater." Right: a mini scale with `EGYPT` at the top.
- **Use the per-continent rank** (`rank_continent`), so it stays true after
  the Americas are added.

### Scene 13 — The Moon is harder (no direct reference)
- The Moon globe turns to show the south pole; the nine Artemis regions light
  up as small outlines.
- Headline `THE MOON IS HARDER`. Text: "The lunar south pole is rougher than
  almost any dry land in Africa. Its closest twins are volcanic mountains in
  Chad. We show the rank and say plainly how far off it still is."

### Scene 14 — What Earth can't copy
- Three words appear one by one over a dark horizon: `GRAVITY`, `AIR`,
  `RADIATION`, then "No place on Earth copies these."

### Scene 15 — Call to action (39 s)
- Headline `FIND YOUR TWIN`, under it a solid blue button
  `LAUNCH THE TWIN FINDER` → `explorer.html`.

### Scene 16 — Numbers (40 s)
- Three big counters that count up when
  they enter: `38` NASA MARS ZONES, `9` ARTEMIS REGIONS, `130,060` PLACES
  SCORED (update when the Americas are in).

### Scene 17 — Built on open data (41 to 42 s)
- The reference shows a grid of customer logos. **We show no logos.** A grid
  of text cells with dataset names instead: `MOLA`, `TES`, `LRO LOLA`,
  `MODIS`, `COPERNICUS DEM`, `JRC WATER`, `USGS`, and a last highlighted cell
  `YOUR SITE?` that links to the Twin Finder.

### Scene 18 — Footer (43 to 45 s)
- Team Duplica, Egyptian Chinese University, Cairo. Links: GitHub, the
  YouTube video, Method. Credits line for all images and data. "How we used
  AI" line.

---

## 4. The Twin Finder (`explorer.html`)

Same look. The design canvas "Explorer" artboard is the layout reference:

- Header with a `MARS | MOON` switch.
- Left: a **3D globe** of the chosen world (three.js, drag to turn, scroll to
  zoom), with the targets as clickable markers. Mars: 38 zones. Moon: 9
  regions, camera starting over the south pole.
- Right: **Earth globe** (or a flat map, if time is short) with the 25 twins
  of the selected target as numbered pins; a list underneath.
- Clicking a pin opens the **twin card**: the two shaded relief images, the
  rank (`#1 of N` and the continent rank), the score, one bar per feature
  (`closeness`), what matches well and what is weakest (computed from the
  bars), the fixed line about gravity, air and radiation, and
  "Open in Google Maps".
- For the Moon, show the rank first and a note that Moon scores are low
  because the pole is far rougher than dry land on Earth.
- An `Egypt` tab listing the best Egyptian tile per target (`egypt.json`).

Raycast clicks on a globe: convert the hit point to latitude and longitude,
and pick the nearest target within a few degrees.

---

## 5. Build order (hackathon time is short)

1. Static skeleton: all scenes as plain sections with the final text, fixed
   button, chapter bar. Deploy it. (A working page beats a half animation.)
2. The globe canvas: Mars hero, dotted Earth, Blue Marble Earth, Moon.
3. ScrollTrigger timelines, scene by scene, in order.
4. `explorer.html` with flat maps first, then globes.
5. The tile-stack scene (7) and the odometer (12) last; they are the most
   work. If time runs out, replace 7 with four layered images and 12 with a
   simple count-up.

Check every number shown against `web/public/data/` before submitting.
