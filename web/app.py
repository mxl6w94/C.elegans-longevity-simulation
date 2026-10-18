from pathlib import Path

import numpy as np
import pandas as pd
from flask import Flask, render_template, request

RESULTS = Path(__file__).resolve().parent.parent / "core" / "results"

WILD_TYPE = "wild type"

# Options shown on the page, in order, with a plain-language hint for each.
OPTIONS = [
    (WILD_TYPE, "Wild type", "A normal worm with no changed genes. Every other worm is compared with this one."),
    ("daf-2", "daf-2", "Senses insulin-like signals. Worms with a weakened daf-2 are known to live longer."),
    ("rsks-1", "rsks-1", "Helps set how fast the worm grows based on food. Changing it slows growth."),
    ("daf-16", "daf-16", "Turns on the worm's protective genes. Worms need it for daf-2's life-extending effect."),
]

# Gene combinations the dataset covers, mapped to the pipeline's genotype names.
# Wild type is the empty set: no genes changed.
GENOTYPES = {
    frozenset(): WILD_TYPE,
    frozenset({"rsks-1"}): "rsks-1",
    frozenset({"daf-2"}): "daf-2",
    frozenset({"daf-2", "rsks-1"}): "daf-2 rsks-1",
    frozenset({"daf-16", "daf-2", "rsks-1"}): "daf-16; daf-2 rsks-1",
}

DISPLAY_NAMES = {
    WILD_TYPE: "Wild type (normal worm)",
    "rsks-1": "rsks-1",
    "daf-2": "daf-2",
    "daf-2 rsks-1": "daf-2 + rsks-1",
    "daf-16; daf-2 rsks-1": "daf-16 + daf-2 + rsks-1",
}

ERROR_NOTHING = "Select at least one gene, or choose Wild type."
ERROR_WT_MIXED = "Wild type means no genes are changed, so it can't be combined with other genes."
ERROR_UNKNOWN = ("That combination isn't in the dataset. You can choose wild type, daf-2, rsks-1, "
                 "daf-2 with rsks-1, or all three genes.")

app = Flask(__name__)
survival = pd.read_csv(RESULTS / "survival_curves_illustrative.csv", index_col=0)
growth = pd.read_csv(RESULTS / "growth_comparison.csv", index_col="genotype")


def median_lifespan(genotype):
    """Age at which half the worms are gone, interpolated between curve points."""
    t = survival["t"].to_numpy()
    s = survival[genotype].to_numpy()
    below = np.nonzero(s <= 0.5)[0]
    if below.size == 0:
        return None
    i = below[0]
    if i == 0:
        return float(t[0])
    # Linear interpolation between the last point above 0.5 and the first at/below it
    t0, t1, s0, s1 = t[i - 1], t[i], s[i - 1], s[i]
    return float(t0 + (s0 - 0.5) * (t1 - t0) / (s0 - s1))


def resolve_genotype(picked):
    """Return (genotype, error) for the set of options the user ticked."""
    if not picked:
        return None, ERROR_NOTHING
    if WILD_TYPE in picked and len(picked) > 1:
        return None, ERROR_WT_MIXED
    genotype = GENOTYPES.get(frozenset(picked - {WILD_TYPE}))
    if genotype is None:
        return None, ERROR_UNKNOWN
    return genotype, None


@app.route("/", methods=["GET", "POST"])
def index():
    result = error = None
    picked = set()
    if request.method == "POST":
        picked = set(request.form.getlist("genes"))
        genotype, error = resolve_genotype(picked)
        if genotype:
            median = median_lifespan(genotype)
            wt_median = median_lifespan(WILD_TYPE)
            growth_ratio = float(growth.loc[genotype, "fold_change_vs_wt"])
            result = {
                "genotype": genotype,
                "name": DISPLAY_NAMES[genotype],
                "is_wild_type": genotype == WILD_TYPE,
                "median": median,
                "median_diff": median - wt_median,
                "growth": growth_ratio,
                "gene_count": len(picked),
                "matches_wild_type": genotype != WILD_TYPE and abs(growth_ratio - 1.0) < 1e-6,
            }
    return render_template("index.html", options=OPTIONS, picked=picked, result=result, error=error)
