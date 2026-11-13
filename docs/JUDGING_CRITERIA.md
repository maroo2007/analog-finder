# Judging criteria

From *What Makes a Strong Project? NASA Space Apps Cairo 2026, Judging
Guidelines for Participants* (IEEE Young Professionals Egypt), handed to
participants on 13 November 2026. The PDF names the Cairo event as
**13 to 14 November 2026, Sewedy University of Technology (SUT)**.

Projects are judged on five criteria.

## 1. Impact: make a difference

- Address a meaningful real-world problem.
- Explain who could benefit from your solution and how.
- Show the potential positive impact on people, science, society, Earth or
  space exploration.

*Ask yourself: why does this project matter, and who will benefit from it?*

## 2. Creativity: think outside the box

- Bring an original idea or a fresh perspective to an existing problem.
- Introduce an innovative approach or improve an existing solution.
- Use available technologies and resources in meaningful and inventive ways.

*Ask yourself: what makes our solution different or innovative?*

## 3. Validity: build a feasible solution

- Base the solution on sound scientific and technical principles.
- Make sure it can realistically work.
- Demonstrate how it works through evidence, testing, a prototype, a model or
  a demonstration, where applicable.
- Support claims with reliable information and results.

*Ask yourself: does our solution actually work, and can we justify how it
works?*

## 4. Relevance: solve the right challenge

- Clearly address the objectives of the selected NASA challenge.
- Use relevant NASA data and resources meaningfully.
- Show how NASA data contributes to the approach and supports the solution.
- Make sure the project responds to the actual problem in the challenge.

*Ask yourself: does our project genuinely solve the selected challenge, and
how does NASA data contribute to it?*

## 5. Presentation: tell your story

- Clearly explain the problem and why it matters.
- Describe the solution and how it works.
- Present the approach, methodology and results in an organized way.
- Use clear visuals, demonstrations, prototypes or supporting materials.
- Communicate the project's value and potential impact effectively.

*Ask yourself: can someone understand our problem, solution and its
importance through our presentation and submitted materials?*

**Remember:** a strong project is not just a creative idea. It should address
a meaningful problem, offer a relevant and feasible solution, make meaningful
use of NASA resources, demonstrate its potential value and communicate it
clearly.

## How submission and judging work (Cairo guide book, page 19)

Translated from the Arabic of the participants' guide book.

- **There is no live pitching.** Every team, on-site or virtual, is judged
  on its demo, which is **one** of:
  - **a video of 30 seconds** that explains the idea quickly and in an
    inspiring way, or
  - **exactly 7 slides**: the challenge, the solution, why it matters, and
    how it is built.
- Judges are experts in different fields. Each judges the projects that fit
  their expertise, with the same criteria NASA uses worldwide (above).
- **Upload twice, on time:**
  1. the local Cairo form: the video link, the slides, and any links such as
     GitHub or the project website;
  2. then the same files on the official NASA Space Apps website, to enter
     global judging.
- The guide's advice: split the work from the first moment, watch the clock,
  keep the idea clear, and make the video enjoyable for someone who is not a
  specialist.

What this means for us: judges see the 30 second video or the 7 slides
first, not a live demo, so those are the main deliverable. The website and
the repository count only as links, which judges must be able to open.

## Before submitting

- [ ] Selected and addressed a NASA challenge.
- [ ] Meaningfully incorporated relevant NASA Open Data and Resources.
- [ ] Developed a clear and feasible proposed solution.
- [ ] Prepared the required project description and supporting materials.
- [ ] Checked that all submitted links are accessible.
- [ ] Followed the official submission instructions, including the AI-use
      disclosure and content requirements.

---

## Where we stand (13 November 2026)

Our own reading of the project against each criterion, from the code and
`HANDOFF.md`. Update it as gaps close.

| Criterion | What we have | What is missing |
|---|---|---|
| Impact | Mission teams train at a handful of analogs (Atacama, Haughton, Death Valley); a data-driven search can find more, including nearer and cheaper ones such as Egypt's Eastern Desert. | Say who benefits in one sentence on the first slide. Reverse mode (nearest good twin to a city) is the feature that shows it, and it is not built. |
| Creativity | Searches all of a continent instead of hand-picking sites; matches against NASA's own 38 Mars Exploration Zones and 9 Artemis regions; same 463 m pixel and averaging on all three worlds. | Image engine (DINOv2) is optional and not started. |
| Validity | Blind validation: V1 sends 92.5% of Mars matches to Atacama and Death Valley without being told about them; Nile Delta control; the failed percentile method is documented; known-answer tests (Olympus Mons, Shackleton depth). Moon limits stated honestly. | Known-analog rank chart (`figures/known_analogs_rank.png`) not built; Earth grid covers Africa only, so the known analogs cannot appear as matches yet. |
| Relevance | NASA data throughout: MOLA, TES and THEMIS (Mars), LOLA (Moon), MODIS (Earth); NASA's own target sites. Copernicus DEM (ESA) is also on the challenge list. | Diviner is named on the challenge page and not used. List every NASA source on the project page (`docs/CHALLENGE_RESOURCES.md`). |
| Presentation | Validation charts in `figures/`; website data in `web/public/data/`. | Neither the 30 second video nor the 7 slides exist yet, and these are what judges see. No website yet (submitted as a link only). |

Two checklist items need action:

- **Links must be accessible.** The GitHub repository is private
  (`HANDOFF.md` section 3). Make it public, or submit a link judges can open,
  before submitting.
- **AI-use disclosure.** Much of the code was written with Claude Code. Read
  the official submission instructions for what the disclosure must say.
