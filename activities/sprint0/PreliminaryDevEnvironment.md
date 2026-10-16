# C. elegans Longevity Simulator: Preliminary Scope and Technology Stack

Sprint 0 · @Tyler Bullard

The preliminary scope is 18 features (8 critical, 6 important, 4 useful). The proposed stack is HTML/CSS/JavaScript with Chart.js on the front end, Python with Flask behind a REST JSON API, and SQLite for saved predictions.

The project is a web tool for researchers and students. A user picks genes from a curated list and sees a predicted C. elegans lifespan, a growth rate and a picture of the worm at a chosen age. The Python pipeline (`core/`, the fluxworm package) produces the predictions through transcriptomics-constrained flux balance analysis (FBA).&#32;

## 1. Preliminary scope: feature list

1. The user opens the web application in a browser. (Critical)
2. The user selects one or more genes from the curated gene list, or selects the wild-type baseline (no mutations) as its own option. (Critical)
3. The user submits the gene selection to request a prediction. (Critical)
4. The system displays the predicted life expectancy for the selected genes. (Critical)
5. The system displays the predicted growth rate for the selected genes. (Critical)
6. The user views the predicted survival curve as a graph. (Critical)
7. The user selects an age within the predicted lifespan and views an image of the worm at that age. (Critical)
8. The system displays an error message when input is invalid: no gene selected, an unsupported gene combination, an age outside the lifespan range, or the server being unreachable. (Critical)
9. The user toggles a selected gene on or off and sees the prediction update against the wild-type baseline. (Important)
10. The user reads a short description of what each gene in the curated list does. (Important)
11. The user downloads the prediction results (survival curve, growth rate, flux table) as CSV files. (Important)
12. The user saves a prediction and retrieves it later. (Important)
13. The system reports when the model finds no feasible solution for the selected genes. (Important)
14. The researcher compares predicted lifespans against observed historical lifespan data to measure accuracy. (Important)
15. The user searches the gene list by name or identifier. (Useful)
16. The user changes the selected age and the worm image updates in place. (Useful)
17. The system displays a predicted body size or weight for the worm. (Useful)
18. The user shares a saved prediction with others through a link. (Useful)

## 2. Preliminary Development Stack

| Layer | Technology in use | Where |
| --- | --- | --- |
| Language | Python 3.11+&#32; | `core/`, `web/` |
| Metabolic modeling | COBRApy 0.29+ with the GLPK solver | `core/src/fluxworm/fba` |
| Data handling and statistics | pandas, NumPy, SciPy, statsmodels | `core/src/fluxworm/expression` |
| Plots | matplotlib (static PNGs) | `core/src/fluxworm/viz` |
| Configuration | YAML (PyYAML) | `core/config/config.yaml` |
| Model and data | iCEL1314 SBML model; GEO microarray GSE52340 (47 samples) | `fluxworm_iCEL_models/`, `master_data_set/` |
| Results | CSV and PNG files written by the pipeline | `core/results/` |
| Tests | pytest, 19 unit tests | `core/tests/` |
| Environment | venv created by `launcher.py` / `.bat` / `.sh` | `core/` |
| Web prototype | Flask with a Jinja template, reading the result CSVs | `web/app.py` |
| Version control and docs hosting | Git, GitHub, GitHub Pages (the primer) | `github.com/mxl6w94` |

The pipeline only covers the five genotypes in the dataset (wild type, rsks-1, daf-2, daf-2;rsks-1, daf-16;daf-2;rsks-1). Predictions are precomputed for those combinations and served on each click.

## 3. Evaluation criteria

The chart below separates criteria for a successful project into several categories, each given a weight percentage.

| Criterion | Weight | What it means for this project |
| --- | --- | --- |
| Integration | 25% | Works directly with the Python pipeline, COBRApy and the CSV results, with no translation layer |
| Team experience and learning curve | 20% | The team already knows it, or can learn it within a few weeks |
| Delivery time | 15% | Gets critical features 1 to 8 working inside the semester |
| Community support | 15% | Documentation, tutorials, maintained packages, answers on Stack Overflow (or other help forums) |
| Scalability | 10% | Handles more genes, more users and a more complex interface later |
| Security | 10% | Input validation, escaping, protection against common web attacks, safe storage |
| Cost | 5% | Free to develop with and cheap or free to host |

Each option is scored 1 (poor) to 5 (excellent) on each criterion. The weighted total is out of 100 --> score/5 × weight, summed across all criteria. The scores are judgement calls for our team.

## 4. Frontend

**Choice: HTML, CSS and JavaScript (ES6+) on Jinja templates, with Chart.js for the survival curve. No JavaScript framework.**&#32;

| Criterion (weight) | HTML/CSS/JS + Jinja + Chart.js | Vue 3 | React&#32; |
| --- | --- | --- | --- |
| Integration (25%) | 5 | 4 | 3 |
| Team experience (20%) | 5 | 3 | 3 |
| Delivery time (15%) | 5 | 4 | 3 |
| Community support (15%) | 4 | 4 | 5 |
| Scalability (10%) | 3 | 4 | 5 |
| Security (10%) | 4 | 4 | 4 |
| Cost (5%) | 5 | 5 | 5 |
| **Weighted total** | **91** | **77** | **74** |

The interface has three views: a gene selector, a results page with a graph and figures, and the worm viewer for visuals. Flask serves the Jinja templates directly, and a small bit of JavaScript calls the REST API so results update without reloading the page. Jinja escapes output automatically, which covers the most common injection risk. A very important point.

React is the stronger option if the interface grows a lot, for example a side-by-side comparison dashboard. If that happens, the REST API in section 5 lets a React front end replace the templates without changing the back end. Given time constraints, the React learning curve, and a less-complex situation, the Flask/Jinja approach was chosen with no Javascript frontend framework. 

## 5. Backend and API

**Choice: Python with Flask, exposing a REST API that returns JSON.**  The back end has to be Python, because the prediction engine is COBRApy, and that is a Python library.

| Criterion (weight) | Python + Flask | Python + FastAPI | Python + Django |
| --- | --- | --- | --- |
| Integration (25%) | 5 | 5 | 4 |
| Team experience (20%) | 5 | 4 | 2 |
| Delivery time (15%) | 5 | 4 | 3 |
| Community support (15%) | 5 | 4 | 5 |
| Scalability (10%) | 3 | 4 | 4 |
| Security (10%) | 3 | 4 | 5 |
| Cost (5%) | 5 | 5 | 5 |
| **Weighted total** | **92** | **86** | **75** |

Flask wins on integration and delivery time. A working prototype already exists in `web/app.py`, and Flask imports the fluxworm package directly. FastAPI is a close second, with built-in request validation and automatic API documentation. Our team could switch if validation becomes a burden. Its async support doesn't help much here, because FBA work is seemingly CPU-bound. Django brings an admin site and a built-in ORM the project may not need.&#32;

The requirements interview suggested running the model in the browser. Pyodide can run Python in the browser, but that path is unproven for COBRApy and its GLPK solver. It would also stop the precomputed results from being reused.

**API approach: REST over HTTP, with JSON bodies.** Planned API routes are:

| Method and path | Purpose |
| --- | --- |
| `GET /api/genes` | Curated gene list with descriptions |
| `POST /api/predictions` | Run or look up a prediction for a gene set |
| `GET /api/predictions/<id>` | Fetch a saved prediction |
| `GET /api/predictions/<id>/survival` | Survival curve points for the graph |
| `GET /api/predictions/<id>/worm?age=<t>` | Worm image for an age, or 400 if out of range |
| `GET /api/predictions/<id>/export.csv` | CSV download |

GraphQL was an alternative. It suits clients that need flexible queries across many related objects, but these six fixed endpoints don't need that, and REST is simpler to test. Given time constraints and simplicity, REST was chosen.

## 6. Database

**Choice: a relational database, SQLite, accessed through SQLAlchemy.** SQLite scores 88 against 84 for PostgreSQL. A move to PostgreSQL is planned if the app is hosted for many users.

| Criterion (weight) | SQLite (relational) | PostgreSQL (relational) | Flat CSV/JSON files (current) |
| --- | --- | --- | --- |
| Integration (25%) | 5 | 4 | 5 |
| Team experience (20%) | 4 | 4 | 5 |
| Delivery time (15%) | 5 | 3 | 4 |
| Community support (15%) | 5 | 5 | 3 |
| Scalability (10%) | 3 | 5 | 1 |
| Security (10%) | 3 | 5 | 2 |
| Cost (5%) | 5 | 4 | 5 |
| **Weighted total** | **88** | **84** | **77** |

The data has a fixed shape: genes, genotypes, predictions, survival-curve points and saved runs, linked by IDs. That suits relational tables better than documents, which rules out something like MongoDB. SQLite ships with Python and stores everything in one file, with no server to install. That keeps setup the same on every dev machine. SQLAlchemy can easily turn into a PostgreSQL implementation later --> mostly a change of connection string.

Flat files work for the pipeline output today, but they can't safely handle saved predictions or concurrent users. The pipeline will keep writing CSVs, and a small import script will load them into the database. This could change??

## 7. Additional tools

Testing extends the pytest suite the pipeline already has. CI runs on GitHub Actions, because the repository is already on GitHub. Very easy to manage.

| Area | Choice | Alternatives considered | Why |
| --- | --- | --- | --- |
| Unit and API tests | pytest + Flask test client | unittest | Already used for the 19 pipeline tests. The Flask test client calls the API without starting a server. |
| Acceptance tests | pytest-bdd | behave | The user stories are written as Given/When/Then, so each scenario can become a test almost word for word. |
| End-to-end browser tests | Playwright (Python) | Selenium, Cypress | Tests the real pages for features in CI. Cypress would bring in a JavaScript test stack. |
| CI/CD | GitHub Actions | GitLab CI, Jenkins | Free for this repository, configured in a YAML file in the repo, and runs tests on every push and pull request. Jenkins needs a server to maintain, I think. |
| Hosting | AWS&#32; | a university VM?? | Free or low-cost Python hosting that deploys from GitHub. |
| Production server | EC2 Instance | PythonAnywhere | Flask's built-in server is for development only. |
| Containers (optional) | Docker | none | Pins the solver and Python versions so the hosted app matches the team dev machines. |
| Documentation | Markdown in the repo, GitHub Pages | none | The primer is already published on GitHub Pages. |

## 8. Final stack and development environment

The final stack keeps everything in Python except the browser code. This fits our team's experience level, the existing pipeline, and a one-semester timeline.

| Component | Final choice |
| --- | --- |
| Frontend language | HTML5, CSS3, JavaScript (ES6+) |
| Frontend framework | None. Jinja templates, plus Chart.js for graphs |
| Backend language | Python 3.11 |
| Backend framework | Flask rendering + pipeline logic |
| API | REST, JSON over HTTP |
| Database | Relational: SQLite through SQLAlchemy, with PostgreSQL if hosted at scale |
| Modeling engine | fluxworm pipeline (COBRApy + GLPK), results precomputed per genotype |
| Testing | pytest, Flask test client, pytest-bdd, Playwright |
| CI/CD | GitHub Actions, deploying to AWS EC2 instance |
| Supporting tools | Git and GitHub, Docker??, GitHub Pages |

This combination ranked high in comparison. It also removes a major delivery risk: translating between languages. The REST API and SQLAlchemy keep the way open for React or PostgreSQL later without a huge rewrite.

**Proposed development environment**

- **Operating system:** Windows 11 (the team's current machines). macOS and Linux are also supported through `launcher.sh`.
- **Editor:** Visual Studio Code or Zed editor with the Python, Pylance, and Jinja extensions.
- **Python:** 3.11+, in a per-project virtual environment (`.venv`) that `launcher.py` creates.
- **Local server:** `flask --app app run --debug` from `web/`, at http://127.0.0.1:5000.
- **Browsers:** Chrome or Firefox, using their developer tools.
- **Version control:** Git, with one branch per feature, pull requests reviewed by a second team member before merging to `main`.
- **Environments:** development (each team member have their own machines), test (GitHub Actions configurations) and production (AWS EC2, deployed from `main`).
