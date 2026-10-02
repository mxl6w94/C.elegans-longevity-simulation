import logging

import cobra
import pandas as pd

from fluxworm.fba.runner import run_all_genotypes


def _toy_model() -> cobra.Model:
    model = cobra.Model("toy")
    a = cobra.Metabolite("A", compartment="c")

    ex_a = cobra.Reaction("EX_A", lower_bound=0, upper_bound=10)
    ex_a.add_metabolites({a: 1})
    ex_a.gene_reaction_rule = "upGene"

    bio = cobra.Reaction("BIO", lower_bound=0, upper_bound=1000)
    bio.add_metabolites({a: -1})

    # Unused at baseline (bounds allow zero flux); the "extreme scaling" test
    # below forces this reaction to a fixed flux that exceeds EX_A's supply
    # capacity, producing genuine LP infeasibility rather than a bounds
    # ValueError -- exercising the runner's non-optimal-status handling path.
    maint = cobra.Reaction("MAINT", lower_bound=0, upper_bound=1000)
    maint.add_metabolites({a: -1})

    model.add_reactions([ex_a, bio, maint])
    model.objective = "BIO"
    return model


def _bounds_table(reaction_id, original_lb, original_ub, new_lb, new_ub):
    return pd.DataFrame(
        {
            "original_lb": [original_lb],
            "original_ub": [original_ub],
            "score": [float("nan")],
            "new_lb": [new_lb],
            "new_ub": [new_ub],
        },
        index=[reaction_id],
    )


def test_wt_and_moderate_scaling_are_optimal():
    model = _toy_model()
    moderate = _bounds_table("EX_A", 0.0, 10.0, 0.0, 5.0)
    results = run_all_genotypes(model, "wild type", {"moderate_mutant": moderate})
    assert results["wild type"].status == "optimal"
    assert results["wild type"].objective_value == 10.0
    assert results["moderate_mutant"].status == "optimal"
    assert results["moderate_mutant"].objective_value == 5.0


def test_extreme_scaling_logs_warning_and_does_not_crash(caplog):
    model = _toy_model()
    # MAINT forced to a fixed flux of 15, exceeding EX_A's max supply of 10
    # -> genuinely infeasible LP, not just a low-growth optimum.
    infeasible = _bounds_table("MAINT", 0.0, 1000.0, 15.0, 15.0)
    with caplog.at_level(logging.WARNING):
        results = run_all_genotypes(model, "wild type", {"broken_mutant": infeasible})

    assert results["wild type"].status == "optimal"
    assert results["broken_mutant"].status != "optimal"
    assert results["broken_mutant"].objective_value is None
    assert any("did not reach optimality" in record.message for record in caplog.records)
