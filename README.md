# C.elegans-longevity-simulation

primer link:

https://mxl6w94.github.io/C.elegans-longevity-simulation/PRIMER.html

### Datasets
  
Listed in master_data_set/GSE52340_series_matrix.txt.gz

- information about the datasets [here](https://www.ncbi.nlm.nih.gov/geo/query/acc.cgi?acc=GSE52340)

### Features

Preliminary scope, numbered in priority order. Format: [Actor performs a specific action] (Priority).

The preliminary scope is 18 features (8 critical, 6 important, 4 useful). The proposed stack is HTML/CSS/JavaScript with Chart.js on the front end, Python with Flask behind a REST JSON API, and SQLite for saved predictions.

The project is a web tool for researchers and students. A user picks genes from a curated list and sees a predicted C. elegans lifespan, a growth rate and a picture of the worm at a chosen age. The Python pipeline (`core/`, the fluxworm package) produces the predictions through transcriptomics-constrained flux balance analysis (FBA).&#32;

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


### Running the app

The project has two parts. You only need the first one to use the website.

- **`web/`** is the Flask website. It reads precomputed results from `core/results/`, which are already in the repository.
- **`core/`** is the modeling pipeline that produces those results. Run it only if you change the model, the data or the settings in `core/config/config.yaml`.

#### Requirements

- [Python](https://www.python.org/downloads/) 3.11 or newer. On Windows, tick **"Add python.exe to PATH"** in the installer.
- [Git](https://git-scm.com/downloads)
- A web browser

Check your Python version with `python --version` (Windows) or `python3 --version` (macOS/Linux).

#### 1. Get the code

```
git clone https://github.com/mxl6w94/C.elegans-longevity-simulation.git
cd C.elegans-longevity-simulation
```

#### 2. Set up the website (first time only)

Windows (Command Prompt):

```
cd web
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

macOS / Linux:

```
cd web
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

This creates a private Python environment in `web/.venv` and installs Flask and pandas into it. The `.venv` folder is ignored by Git, so each person creates their own.

#### 3. Run the website

From the `web` folder, with the environment active (your prompt starts with `(.venv)`):

```
flask --app app run --debug
```

Open <http://127.0.0.1:5000> in your browser. `--debug` reloads the server when you save a file. Press `Ctrl+C` in the terminal to stop it.

Next time, you only need to activate the environment and run the server:

```
cd web
.venv\Scripts\activate          (Windows)
source .venv/bin/activate       (macOS/Linux)
flask --app app run --debug
```

#### 4. Re-run the modeling pipeline (optional)

The launcher in `core/` creates its own environment, installs the scientific packages (COBRApy, SciPy and others) and runs the pipeline. The first run takes a few minutes.

```
cd core
python launcher.py                 # run the pipeline
python launcher.py --tests         # run the pipeline, then the test suite
python launcher.py --tests-only    # run only the tests
```

On Windows you can also double-click `core\launcher.bat`. On macOS/Linux, run `chmod +x launcher.sh` once, then `./launcher.sh`.

New results are written to `core/results/`. Restart the website to pick them up. See [`core/README.md`](core/README.md) for how the pipeline works.

#### Troubleshooting

| Problem | Fix |
| --- | --- |
| `'flask' is not recognized` or `command not found: flask` | The environment isn't active. Run the activate command from step 2 again. |
| PowerShell says running scripts is disabled when activating | Use Command Prompt instead, or run `Set-ExecutionPolicy -Scope CurrentUser RemoteSigned` once in PowerShell. |
| `pip install` fails on pandas or numpy | Your Python is older than 3.11. Install a newer version and recreate `.venv`. |
| `Address already in use` / port 5000 busy | Run on another port: `flask --app app run --debug --port 5001`. On macOS, AirPlay Receiver also uses port 5000. |
| `FileNotFoundError` for a file in `core/results` | Run the pipeline once (step 4) to regenerate the results. |
| First pipeline run on Windows fails with `DLL load failed ... Application Control policy` | Windows Smart App Control is checking the new SciPy files. Run the launcher again; it passes on the second try. |
