# Product

<!-- impeccable:product-schema 1 -->

## Platform

web

## Stack

Vite + vanilla JS (confirmed 2026-11-13). Two static pages, `index.html` (the
story) and `explorer.html` (the Twin Finder), built to `dist/` with no server.
three.js for every globe and 3D scene (one WebGL canvas), GSAP + ScrollTrigger
for pinned, scroll-scrubbed scenes, Lenis for smooth scrolling. Fonts are
self-hosted so the demo works offline. Deploy host: undecided; any static host
serving `dist/` works.

## Users

Primary: **NASA Space Apps Challenge 2026 judges**, arriving cold, giving the
project a few minutes, often on a laptop, judging relevance to the challenge
*Identify Earth Locations that Analog the Permanent Moon Base Locations and
Mars*. They need to grasp the idea from the story fast, believe the method,
then open the Twin Finder and see real matches for real NASA sites.

Secondary: the curious public with no planetary-science background, and
analog-site researchers or mission planners who might use the Twin Finder as a
real lookup tool.

## Product Purpose

Planetary Twin Finder finds places on Earth whose terrain best matches NASA's
own proposed landing and base sites on Mars and the Moon. Astronauts rehearse
at a few Earth analog sites chosen mostly by experience; this project searches
the whole dry surface of Earth with one shared measuring method instead.
Success for the hackathon: a judge understands the idea, trusts the method,
and finds the matches convincing and honestly qualified.

## Positioning

Every patch of ground on Earth, Mars and the Moon gets the same profile
(slope, roughness, relief, brightness, at the same 463 m pixel and 9 km tile),
and the data, not experience, ranks the closest twins. The method was
blind-tested: without being told about them, it sends most Mars matches to the
places NASA already trains (Atacama and Death Valley). It is built from open
NASA and ESA data, by a student team in Cairo whose own country, Egypt, holds
Jezero crater's closest twin.

## Operating Context

- Shown live at the hackathon (14 to 15 November 2026) and reviewed by judges
  from 16 November, alongside a YouTube video and the GitHub repository.
- Two surfaces: a long scroll story that explains the project scene by scene
  and ends on a launch button, and the Twin Finder, an interactive tool. A
  fixed button opens the Twin Finder from anywhere in the story.
- Twin Finder workflow: pick Mars or the Moon, click a target site on a 3D
  globe, see its 25 closest Earth twins as numbered pins and a list, open a
  twin card (two shaded relief images, rank, score, per-feature closeness,
  what matches best and worst, the gravity/air/radiation caveat, Google Maps
  link). An Egypt tab lists the best Egyptian tile per target.

## Capabilities and Constraints

- **Targets:** Mars, NASA's 38 candidate human Exploration Zones. Moon, the
  nine Artemis III candidate regions of October 2024 (Artemis III is now an
  Earth-orbit test flight; the first landing is Artemis IV).
- **Matching (method V1):** terrain (mean slope, slope spread shown as
  "Roughness", relief) plus absolute albedo ("Brightness"), after a
  Mars-possible filter on Earth (NDVI below 0.15, under 5% permanent water,
  under 50% permanent ice). Heat is not a matching feature.
- **Moon is terrain only**, with its own scaler. Moon scores are low (best 5
  to 33) and not comparable with Mars scores; always show the rank first and
  say why scores are low.
- **Data lives in `web/public/data/`** and the site must read whatever is
  there: `targets.json` (features, targets), `matches/<id>.json` (top 25
  twins at least 25 km apart), `egypt.json`, `likeness.json` and its PNG
  maps, `shade/{mars,moon,earth}/` relief images. Today it covers Africa only
  (130,060 places). When `feature/americas` merges, the same files gain
  `continent`, `rank_continent`, `of_continent`, more `maps` in
  `likeness.json`, and `of` becomes 148,925. Code must fall back gracefully
  (for example `rank_continent ?? rank`) and never hardcode a count or a
  closeness value that the data provides.
- **Competition rule:** no NASA logos anywhere. Writing "NASA" in text is
  fine.
- **Performance:** one renderer, textures at most 4096 x 2048, rendering paused
  when the tab is hidden, aim for 60 fps on a laptop, works at 390 px wide.
- **Input:** mouse wheel, trackpad, touch and keyboard all work.
- **Assets:** only public domain or clearly open-licensed (Blue Marble, Viking
  Mars mosaic, MOLA, LROC colour, LOLA, Natural Earth). No 3D models needed.
  Any missing asset is requested from the team, never improvised.
- **Undecided:** deploy host; GitHub, YouTube and Method link URLs for the
  footer; the exact "How we used AI" line.

## Brand Commitments

- Name: **Planetary Twin Finder**. Team: **Team Duplica**, Egyptian Chinese
  University, Cairo. Event line: `NASA Space Apps 2026 · Team Duplica · Cairo`.
- **World colours are fixed:** Mars `#e0703a`, Moon `#c4c9d1`, Earth `#5aa9e6`.
  Everything else in the palette is open.
- All copy, the storyboard order, and each scene's motion idea are pinned in
  `docs/WEBSITE_SPEC.md` section 3; the Twin Finder layout in section 4.
- Voice: plain, short, confident, honest about limits. Uppercase display
  lines are part of the storyboard.

## Evidence on Hand

- Jezero crater's #1 twin in Africa: Egypt's Eastern Desert, 25.13°N,
  34.54°E (`matches/jezero.json`), with per-feature closeness in the file.
- Phase 1 blind validation (2026-10-10): 73% of Mars matches went to Atacama
  and Death Valley on elevation alone; with V1 (terrain + albedo) it is
  92.5%. Figures in `figures/validation_*.png`.
- Moon's closest twins are volcanic mountains in Chad.
- Datasets used: MOLA, TES, LRO LOLA, MODIS, Copernicus DEM, JRC Water, USGS.
- Shaded relief pairs for every target (`shade/`), a Mars-likeness map of
  Africa (`likeness.png`).
- **Absent, must not be fabricated:** testimonials, endorsements, partner or
  customer logos, usage numbers, press, any claim of NASA involvement or
  approval.

## Product Principles

1. **The data speaks.** Every number shown comes from `web/public/data/` or
   the HANDOFF; nothing is rounded into a better story.
2. **Honest twins.** Every match says what doesn't match, and the Moon is
   shown as harder, with ranks rather than flattering scores.
3. **Cold-start clarity.** A judge with no background understands the idea in
   the first few scenes and can reach a real match in one click.
4. **Same ruler everywhere.** Mars, Moon and Earth are treated identically;
   the interface should make that shared measure visible.
5. **Works on the day.** Offline-capable, fast, robust to missing or newer
   data; a working page beats a half animation.

## Accessibility & Inclusion

Respect `prefers-reduced-motion`: replace scrubbed animation with simple fades
and stop the globes spinning. Full keyboard operation of both pages, including
the chapter bar and globe target selection. Body text 18 to 22 px.
