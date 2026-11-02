# Sprint 2 Log: Website
### *Tyler Bullard*

Changes to the Flask web app (`web/`) during Sprint 2, in changelog form. Desktop prediction viewer changes (`core/viewer/`) are in a different log.

## Commits on `main`

| Date | Commit | Author | Summary |
| --- | --- | --- | --- |
| 2026-11-01 | `bd48054` | Tyler Bullard | Added the time-lapse script and the bundled Chart.js library |
| 2026-11-01 | `940830c` | Tyler Bullard | Dashboard layout, summary tiles, `/api/curves` endpoint, high-contrast colors |

## Added

- **Time-lapse survival graph** (`web/static/scripts/timelapse.js`). After a prediction, the survival curve draws itself across model time with a moving time marker. Controls: play, pause and replay, a time slider, speed (0.5×, 1×, 2×, 4×), and a "Show all worm types" option.
- **Two graph views.** "Survival" shows the share of worms alive over time. "Difference from normal worm" shows the percent change compared with wild type, because the raw survival lines almost overlap.
- **Worm population panels.** 100 worm icons for the selected worm and 100 for wild type, fading out as the model predicts each one has died. Worms die in the same order in both panels, so the two can be compared worm by worm. A counter under each panel shows the exact percent alive and the gap in percentage points.
- **`GET /api/curves` endpoint** (`web/app.py`). Returns the time axis plus, for each genotype: the survival curve, the difference from wild type, median and mean lifespan, their percent change compared with wild type, growth change, and the genotype's color variable. Built once at startup from the pipeline CSVs.
- **Mean lifespan** (`mean_lifespan()`), the area under the survival curve, shown next to the median.
- **Chart.js 4.6.1** (MIT license), bundled in `web/static/vendor/chart.umd.min.js` so the graph works without an internet connection or outside CDN.
- **Dashboard layout** (`web/templates/index.html`). A header with a one-line description; a left sidebar with the gene form, the "How does this work?" and "What do the results mean?" sections and the model note; and a right panel with the results and graph. The sidebar stays in place on desktop while the page scrolls.
- **Summary tiles** for median lifespan, mean lifespan and growth compared with a normal worm. Each shows its change compared with wild type: ▲ green for longer life, ▼ red for shorter, and neutral for growth.
- **Empty state.** Before the first prediction, the right panel shows "Your results will appear here" instead of blank space.
- **Reduced-motion support.** Users whose system is set to reduce motion see the finished graph without animation and can scrub through it.

## Changed

- **Color scheme** (`web/static/css/main.css`). Each worm type now has a high-contrast, colorblind-safe color stored as a CSS variable (`--g-wild-type`, `--g-rsks-1`, `--g-daf-2`, `--g-daf-2-rsks-1`, `--g-triple`), with separate light and dark versions. Every color is at least 4.3:1 against its background. Wild type is also drawn dashed, so it doesn't rely on color alone.
- **The selected worm's color carries across the page**: the name marker, tile edges, graph line and worm icons.
- **Stronger borders and gray text** in both themes so panels and captions read more clearly.
- **Genotype colors in `app.py`** are now CSS variable names instead of hex codes, so the graph recolors itself when the theme switches.
- **JSON key order.** `app.json.sort_keys = False` keeps genotypes in the pipeline's order (wild type first) instead of alphabetical.
- **Worm panels lay out as 20 × 5** on wide screens, so the graph, both populations and the controls fit on one laptop screen.
- **Phones and tablets** (900 px wide or less) get a single column with the controls first.
- **"What do the results mean?"** now explains mean lifespan.

## Fixed

- **Misleading tail in the difference view.** The line used to climb to +7.6% near the end of the time axis, when almost no worms were left. It now stops once 99% of wild-type worms have died (model time 38.4), and the caption explains why.
- **Odd axis labels** (such as +8.512% and −0.912%) in the difference view. The axis now uses rounded bounds.
- **Missing changes after a stash.** The 3:24 PM stash on November 1 held the `app.py`, `main.css` and `index.html` changes, so `bd48054` shipped the new script without the page and server code it needs. The three files were restored from the stash and committed in `940830c`.

## Documentation

- **Security Architecture and Testing Plan** (`activities/sprint2/Security_Architecture_and_Testing_Plan.md`, diagram in `security_architecture.png`). Covers the AWS EC2 hosting design, controls for path traversal, XSS and SQL injection, the test cases, the server hardening checklist and the testing round for Sprint 3.

## Verification

- Checked in Chromium in light and dark mode, at 1440 px and 390 px wide: no console errors, no sideways scrolling on phones.
- Lifespan and growth numbers match the desktop prediction viewer. For example, daf-2 median lifespan is +0.069% and growth is −0.117% compared with wild type.
- Security baseline run against this version (details in the plan): 11 path traversal variants all returned 404; XSS and SQL-style payloads were never echoed back; `pip-audit` and `bandit` found nothing.

## Known issues (from the security plan)

| ID | Issue | Planned fix |
| --- | --- | --- |
| F1 | README runs the app with `flask --debug`, which must never reach a public server | Gunicorn with debug off on EC2; README note |
| F2 | No security headers | `after_request` hook and Nginx headers |
| F3 | No request size limit | `MAX_CONTENT_LENGTH` and Nginx `client_max_body_size` |
| F4 | `timelapse.js` builds the worm panels with `innerHTML` | Switch to `createElement` and `textContent` |
| F6 | Inline `--accent` style forces a weaker Content-Security-Policy | One CSS class per genotype |

## Not yet merged

- `53bd299` (caleb3572, 2026-10-18), "added placeholders for a graph and worm visuals", is on `Development-Branch-1`, not `main`. It adds a matplotlib graph in `app.py`, a placeholder worm image (`web/static/C_E_IMG.jpg`) and `matplotlib` in `requirements.txt`. It overlaps with the new Chart.js graph and worm panels, so the team should decide what to keep before merging. The worm image could be reused for feature 7 (worm image at a selected age).
