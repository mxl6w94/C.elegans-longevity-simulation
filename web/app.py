from pathlib import Path

import numpy as np
import pandas as pd
from flask import Flask, jsonify, render_template, request

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

# Each genotype's color is a CSS variable (see static/css/main.css), so the
# high-contrast palette switches with the light/dark theme.
COLORS = {
    WILD_TYPE: "--g-wild-type",
    "rsks-1": "--g-rsks-1",
    "daf-2": "--g-daf-2",
    "daf-2 rsks-1": "--g-daf-2-rsks-1",
    "daf-16; daf-2 rsks-1": "--g-triple",
}

ERROR_NOTHING = "Select at least one gene, or choose Wild type."
ERROR_WT_MIXED = "Wild type means no genes are changed, so it can't be combined with other genes."
ERROR_UNKNOWN = ("That combination isn't in the dataset. You can choose wild type, daf-2, rsks-1, "
                 "daf-2 with rsks-1, or all three genes.")

app = Flask(__name__)
app.json.sort_keys = False  # keep genotypes in the pipeline's order (wild type first)
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


def mean_lifespan(genotype):
    """Area under the survival curve: the expected lifespan in model time."""
    t = survival["t"].to_numpy()
    s = survival[genotype].to_numpy()
    return float(np.sum((s[1:] + s[:-1]) * np.diff(t)) / 2.0)


DIFF_MIN_SURVIVAL = 0.01  # stop the difference line when <1% of wild-type worms are alive


def curve_payload():
    """Everything the time-lapse chart needs, built once from the pipeline CSVs."""
    t = survival["t"].to_numpy()
    wt = survival[WILD_TYPE].to_numpy()
    genotypes = [c for c in survival.columns if c != "t"]
    wt_median, wt_mean = median_lifespan(WILD_TYPE), mean_lifespan(WILD_TYPE)

    data = {
        "t": [round(float(x), 6) for x in t],
        "reference": WILD_TYPE,
        "diff_min_survival": DIFF_MIN_SURVIVAL,
        "genotypes": {},
    }
    for g in genotypes:
        s = survival[g].to_numpy()
        # % change in survival vs wild type at each time point. Once fewer than
        # 1% of wild-type worms are alive, the ratio is a percentage of almost
        # nothing and swings wildly, so those points are sent as null.
        with np.errstate(divide="ignore", invalid="ignore"):
            diff = np.where(wt >= DIFF_MIN_SURVIVAL, (s / wt - 1.0) * 100.0, np.nan)
        median, mean = median_lifespan(g), mean_lifespan(g)
        data["genotypes"][g] = {
            "name": DISPLAY_NAMES.get(g, g),
            "color_var": COLORS.get(g, "--primary-color"),
            "survival": [float(x) for x in s],
            "diff_pct": [None if np.isnan(x) else float(x) for x in diff],
            "median": median,
            "mean": mean,
            "median_pct": (median / wt_median - 1.0) * 100.0,
            "mean_pct": (mean / wt_mean - 1.0) * 100.0,
            "growth_pct": (float(growth.loc[g, "fold_change_vs_wt"]) - 1.0) * 100.0,
        }
    return data


CURVES = curve_payload()


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
            summary = CURVES["genotypes"][genotype]
            result = {
                "genotype": genotype,
                "name": DISPLAY_NAMES[genotype],
                "color_var": COLORS[genotype],
                "mean": summary["mean"],
                "median_pct": summary["median_pct"],
                "mean_pct": summary["mean_pct"],
                "growth_pct": summary["growth_pct"],
                "is_wild_type": genotype == WILD_TYPE,
                "median": median,
                "median_diff": median - wt_median,
                "growth": growth_ratio,
                "gene_count": len(picked),
                "matches_wild_type": genotype != WILD_TYPE and abs(growth_ratio - 1.0) < 1e-6,
            }
    return render_template("index.html", options=OPTIONS, picked=picked, result=result, error=error)


@app.route("/api/curves")
def api_curves():
    """Survival curves and summary numbers for every genotype, as JSON."""
    return jsonify(CURVES)
