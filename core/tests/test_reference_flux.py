import cobra

from fluxworm.constraints.reference_flux import compute_wt_reference_capacities


def _toy_model() -> cobra.Model:
    model = cobra.Model("toy")
    a = cobra.Metabolite("A", compartment="c")

    ex_a = cobra.Reaction("EX_A", lower_bound=0, upper_bound=1000)
    ex_a.add_metabolites({a: 1})

    bio = cobra.Reaction("BIO", lower_bound=0, upper_bound=1000)
    bio.add_metabolites({a: -1})

    # Never carries flux in any solution (disconnected sink with no supply
    # other than A, which BIO already fully consumes) -- exercises the
    # epsilon floor for WT-unused reactions.
    b = cobra.Metabolite("B", compartment="c")
    unused = cobra.Reaction("UNUSED", lower_bound=0, upper_bound=1000)
    unused.add_metabolites({b: -1})

    model.add_reactions([ex_a, bio, unused])
    model.objective = "BIO"
    return model


def test_reference_capacity_reflects_actual_flux_magnitude_not_model_bound():
    model = _toy_model()
    ref = compute_wt_reference_capacities(model, fraction_of_optimum=0.9)
    # EX_A/BIO both carry flux ~1000 at optimum -> reference should track that,
    # not some arbitrarily different value.
    assert ref["BIO"] > 100
    assert ref["EX_A"] > 100


def test_unused_reaction_gets_epsilon_floor_not_locked_to_exact_zero():
    model = _toy_model()
    ref = compute_wt_reference_capacities(model, fraction_of_optimum=0.9, epsilon=1e-6)
    assert ref["UNUSED"] == 1e-6
