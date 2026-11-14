---
version: 1
slug: "web-explorer-html"
primary_target: "web/explorer.html"
related_targets: ["web/index.html"]
---

# Twin Finder (web/explorer.html)

Mode: Operate. Inherits the story page's world (see web/index.html brief).
Task: pick Mars or the Moon, pick a target, read its 25 Earth twins, open a
twin card. Layout pinned in docs/WEBSITE_SPEC.md section 4: MARS | MOON switch
in the header, target world on the left, Earth with numbered pins and a list on
the right, twin card with two relief images, rank (#1 of N, continent rank),
score, one closeness bar per feature, best and weakest feature, the gravity /
air / radiation line, Open in Google Maps. Moon shows rank first with the note
on low scores. Egypt tab from egypt.json. Flat maps first, globes after.

States: loading data, data missing for a target, no continent rank yet
(Africa-only data), keyboard selection of targets and twins, narrow screens.
