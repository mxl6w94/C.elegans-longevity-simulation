import cobra
import numpy as np
import pandas as pd

from fluxworm.constraints.flux_constraint_builder import build_reaction_bounds, gene_scores_from_de


def _toy_model() -> cobra.Model:
    model = cobra.Model("toy")
    m1 = cobra.Metabolite("m1", compartment="c")
    m2 = cobra.Metabolite("m2", compartment="c")

    r_gpr = cobra.Reaction("R_GPR", lower_bound=-100, upper_bound=100)
    r_gpr.add_metabolites({m1: -1, m2: 1})
    r_gpr.gene_reaction_rule = "geneA"

    r_no_gpr = cobra.Reaction("R_NOGPR", lower_bound=-50, upper_bound=50)
    r_no_gpr.add_metabolites({m2: -1, m1: 1})

    model.add_reactions([r_gpr, r_no_gpr])
    return model


def test_unscaled_reactions_keep_original_bounds():
    model = _toy_model()
    bounds = build_reaction_bounds(model, gene_scores={"geneA": 2.0})
    row = bounds.loc["R_NOGPR"]
    assert row["new_lb"] == row["original_lb"] == -50
    assert row["new_ub"] == row["original_ub"] == 50
    assert np.isnan(row["score"])


def test_scaling_preserves_sign_and_magnitude():
    model = _toy_model()
    bounds = build_reaction_bounds(model, gene_scores={"geneA": 2.0})
    row = bounds.loc["R_GPR"]
    assert row["new_lb"] == -200
    assert row["new_ub"] == 200


def test_reference_capacities_override_model_bound():
    # R_GPR's model bound is +-100, but if a much smaller reference capacity
    # is supplied (e.g. from WT FVA), scaling should use that instead --
    # this is the fix for the null-result diagnosis: iCEL1314's model
    # bounds are placeholders too loose for realistic fold-changes to bind.
    model = _toy_model()
    reference_capacities = pd.Series({"R_GPR": 0.002, "R_NOGPR": 999.0})
    bounds = build_reaction_bounds(model, gene_scores={"geneA": 2.0}, reference_capacities=reference_capacities)
    row = bounds.loc["R_GPR"]
    assert row["new_lb"] == -0.004
    assert row["new_ub"] == 0.004
    # R_NOGPR has no GPR, so it must stay at its original bounds regardless
    # of any reference capacity supplied for it.
    row_nogpr = bounds.loc["R_NOGPR"]
    assert row_nogpr["new_lb"] == row_nogpr["original_lb"] == -50
    assert row_nogpr["new_ub"] == row_nogpr["original_ub"] == 50


def test_gene_scores_from_de_clips_and_filters_by_evidence():
    de_table = pd.DataFrame(
        {
            "log2fc": [10.0, 0.1, -1.0],
            "pvalue": [0.001, 0.9, 0.001],
            "qvalue": [0.001, 0.9, 0.001],
            "evidence": [True, False, True],
        },
        index=["gene_up_extreme", "gene_flat", "gene_down"],
    )
    scores = gene_scores_from_de(de_table, min_scale=0.1, max_scale=10.0)
    assert scores["gene_up_extreme"] == 10.0  # clipped from 2**10
    assert "gene_flat" not in scores  # no evidence -> not in dict, treated as neutral downstream
    assert scores["gene_down"] == 0.5  # 2**-1
