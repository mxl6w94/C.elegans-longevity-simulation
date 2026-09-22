"""Loads the iCEL1314 genome-scale metabolic model and sanity-checks it.

Biological rationale: iCEL1314 (Yilmaz & Walhout, 2016, Cell Systems) is a
curated reconstruction of every known C. elegans metabolic reaction, with
genes attached via Gene-Protein-Reaction (GPR) boolean rules. It is the
substrate every downstream step in this pipeline operates on. Loading it
correctly and confirming the objective reaction is present is the one
precondition the rest of the pipeline assumes without re-checking.

Known caveat: as distributed in this project, iCEL1314's SBML file carries
no subsystem/pathway annotation (no <notes> SUBSYSTEM field and no SBML
"groups" package) for any reaction -- `reaction.subsystem` is always empty.
`fluxworm.analysis.subsystem_summary` therefore uses a heuristic keyword tag
derived from `reaction.name` instead of a true curated subsystem, and this
is documented there and must not be mistaken for pathway ground truth.
"""

from __future__ import annotations

from pathlib import Path

import cobra


def load_model(model_xml: str | Path, biomass_reaction: str) -> cobra.Model:
    """Load the SBML model and verify the expected biomass objective exists.

    Raises FileNotFoundError / KeyError early and loudly rather than letting
    a missing file or renamed objective reaction surface later as a
    confusing infeasible-FBA result.
    """
    model_xml = Path(model_xml)
    if not model_xml.exists():
        raise FileNotFoundError(f"iCEL1314 model not found at {model_xml}")

    model = cobra.io.read_sbml_model(str(model_xml))

    if biomass_reaction not in model.reactions:
        raise KeyError(
            f"Expected biomass reaction '{biomass_reaction}' not found in model. "
            f"Available reaction IDs starting with 'BIO': "
            f"{[r.id for r in model.reactions if r.id.startswith('BIO')]}"
        )

    model.objective = biomass_reaction
    return model


def wild_type_sanity_check(model: cobra.Model) -> float:
    """Run unconstrained FBA and return the growth (biomass) flux.

    A near-zero or infeasible result here means the model itself is broken
    (wrong objective, degenerate bounds) -- this must be checked before any
    genotype-specific constraints are layered on, so failures aren't
    mistakenly attributed to the transcriptomics constraint step later.
    """
    solution = model.optimize()
    if solution.status != "optimal":
        raise RuntimeError(f"Unconstrained wild-type FBA did not reach optimality: {solution.status}")
    if solution.objective_value <= 0:
        raise RuntimeError(f"Unconstrained wild-type FBA returned non-positive growth: {solution.objective_value}")
    return solution.objective_value
