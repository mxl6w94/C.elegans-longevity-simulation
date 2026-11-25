from pathlib import Path

import numpy as np
import pandas as pd
from flask import Flask, jsonify, render_template, request

RESULTS = Path(__file__).resolve().parent.parent / "core" / "results"
REFERENCE_DATA = Path(__file__).resolve().parent.parent / "core" / "data" / "lifespan_reference.csv"

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
# Lifespans measured in the lab (see core/data/lifespan_reference.csv for sources)
reference = pd.read_csv(REFERENCE_DATA, index_col="genotype")


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


GRID_POINTS = 600         # points on the shared time axis sent to the page


def measured_change_pct(genotype):
    """Measured mean lifespan change vs wild type in percent, or None if not reported."""
    if genotype not in reference.index:
        return None
    value = reference.loc[genotype, "mean_lifespan_change_pct"]
    return None if pd.isna(value) else float(value)


def reference_source():
    """Citation for the measured values (all rows currently share one source)."""
    row = reference.loc[WILD_TYPE]
    return {
        "label": str(row["source"]),
        "doi": str(row["doi"]),
        "url": f"https://doi.org/{row['doi']}",
        "temperature_c": float(row["temperature_c"]),
    }


def curve_payload():
    """Everything the time-lapse chart needs, built once at startup.

    Time is relative to wild type: 1.0 = the wild-type mean lifespan. Each
    genotype gets two curves on the same time grid:

    * measured: the wild-type curve stretched in time by the genotype's measured
      mean lifespan ratio (temporal scaling, Stroustrup et al. 2016). None when
      the lab value is not in lifespan_reference.csv.
    * model: the pipeline's prediction from core/results (wild-type curve
      rescaled by the genotype's constrained-FBA growth capacity).
    """
    t_model = survival["t"].to_numpy()
    wt_model = survival[WILD_TYPE].to_numpy()
    genotypes = [c for c in survival.columns if c != "t"]
    wt_median, wt_mean = median_lifespan(WILD_TYPE), mean_lifespan(WILD_TYPE)
    t_rel = t_model / wt_mean  # model time -> multiples of the wild-type mean

    ratios = {g: 1.0 + pct / 100.0 for g in genotypes if (pct := measured_change_pct(g)) is not None}

    # The grid runs until the longest-lived measured worm has (almost) died out
    nearly_gone = np.nonzero(wt_model < 0.001)[0]
    wt_end = t_rel[nearly_gone[0]] if nearly_gone.size else t_rel[-1]
    # ... and until every model curve has died out too
    model_end = max(
        (t_rel[np.nonzero(survival[g].to_numpy() >= 0.001)[0][-1]] for g in genotypes), default=wt_end
    )
    grid = np.linspace(0.0, max(wt_end * max(ratios.values(), default=1.0), model_end), GRID_POINTS)

    def on_grid(curve, stretch=1.0):
        return np.interp(grid / stretch, t_rel, curve, right=0.0)

    data = {
        "t": [round(float(x), 5) for x in grid],
        "time_unit": "multiples of the wild-type mean lifespan",
        "reference": WILD_TYPE,
        "source": reference_source(),
        "genotypes": {},
    }
    for g in genotypes:
        model = on_grid(survival[g].to_numpy())
        median, mean = median_lifespan(g), mean_lifespan(g)
        pct = measured_change_pct(g)
        data["genotypes"][g] = {
            "name": DISPLAY_NAMES.get(g, g),
            "color_var": COLORS.get(g, "--primary-color"),
            "measured_pct": pct,
            "measured": None if pct is None else [round(float(x), 6) for x in on_grid(wt_model, ratios[g])],
            "model": [round(float(x), 6) for x in model],
            "model_median_pct": (median / wt_median - 1.0) * 100.0,
            "model_mean_pct": (mean / wt_mean - 1.0) * 100.0,
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
            growth_ratio = float(growth.loc[genotype, "fold_change_vs_wt"])
            summary = CURVES["genotypes"][genotype]
            measured_pct = summary["measured_pct"]
            model_pct = summary["model_mean_pct"]
            model_ratio = 1.0 + model_pct / 100.0
            # Model lifespan relative to the measured one: -20 means the model is 20% too low
            model_error_pct = None
            if measured_pct is not None:
                model_error_pct = (model_ratio / (1.0 + measured_pct / 100.0) - 1.0) * 100.0
            result = {
                "genotype": genotype,
                "name": DISPLAY_NAMES[genotype],
                "color_var": COLORS[genotype],
                "is_wild_type": genotype == WILD_TYPE,
                "measured_pct": measured_pct,
                "measured_ratio": None if measured_pct is None else 1.0 + measured_pct / 100.0,
                "measured_note": str(reference.loc[genotype, "notes"]) if genotype in reference.index else "",
                "model_pct": model_pct,
                "model_ratio": model_ratio,
                "model_flat": abs(model_pct) < 0.05,
                "model_error_pct": model_error_pct,
                "growth": growth_ratio,
                "growth_pct": summary["growth_pct"],
                "gene_count": len(picked),
            }
    return render_template(
        "index.html", options=OPTIONS, picked=picked, result=result, error=error, source=CURVES["source"]
    )


@app.route("/api/curves")
def api_curves():
    """Survival curves and summary numbers for every genotype, as JSON."""
    return jsonify(CURVES)
