from pathlib import Path

import pandas as pd
from flask import Flask, render_template, request

from matplotlib.figure import Figure
import base64
from io import BytesIO
import numpy as np

RESULTS = Path(__file__).resolve().parent.parent / "core" / "results"

# Checkbox combinations
# Only these five exist in the dataset.
GENOTYPES = {
    frozenset(): "wild type",
    frozenset({"rsks-1"}): "rsks-1",
    frozenset({"daf-2"}): "daf-2",
    frozenset({"daf-2", "rsks-1"}): "daf-2 rsks-1",
    frozenset({"daf-16", "daf-2", "rsks-1"}): "daf-16; daf-2 rsks-1",
}

app = Flask(__name__)
survival = pd.read_csv(RESULTS / "survival_curves_illustrative.csv", index_col=0)
growth = pd.read_csv(RESULTS / "growth_comparison.csv", index_col="genotype")


def median_lifespan(genotype):
    """First time point where half the worms are gone."""
    below = survival.loc[survival[genotype] <= 0.5, "t"]
    return float(below.iloc[0]) if not below.empty else None


def worm_graph(l_span, g_rate):
    """ 
    * Worm lifespan graph function
    * Use the median lifespan and growth rate to create a graph
    """
    X = np.linspace(0, l_span, 200)
    y = X*g_rate
    fig = Figure()
    ax = fig.subplots()
    ax.plot(X, y)
    buf = BytesIO()
    fig.savefig(buf, format="png")
    buf.seek(0)
    w_graph = base64.b64encode(buf.read()).decode('utf-8')
    return w_graph


@app.route("/", methods=["GET", "POST"])
def index():
    result = error = None
    if request.method == "POST":
        picked = frozenset(request.form.getlist("genes"))
        genotype = GENOTYPES.get(picked)
        if genotype is None:
            error = "That gene combination isn't in the dataset."
        else:
            result = {
                "genotype": genotype,
                "median": median_lifespan(genotype),
                "growth": growth.loc[genotype, "fold_change_vs_wt"],
                "graph": worm_graph(median_lifespan(genotype), growth.loc[genotype, "fold_change_vs_wt"]),
            }
    return render_template("index.html", result=result, error=error)
