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
