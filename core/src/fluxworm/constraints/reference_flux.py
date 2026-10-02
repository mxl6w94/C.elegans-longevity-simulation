"""Computes a per-reaction wild-type reference flux capacity via FVA, used
as the scaling base for transcriptomics-derived constraints instead of the
model's own (often uninformative) bound.

Why this exists: the first real run of this pipeline against the actual
iCEL1314 model and GSE52340 data produced a null result -- growth and every
individual reaction flux came out numerically identical to WT for all four
mutant genotypes. This was diagnosed directly (not assumed): forcing
several of the rescaled, flux-carrying reactions to a hard knockout (bounds
fixed to zero) does substantially change growth for some of them, proving
the FBA and constraint-application machinery work correctly. The actual
cause is that iCEL1314 uses a generic placeholder bound of +-1000 on nearly
every reaction, while the flux magnitudes this model actually uses at
optimal growth are three to six orders of magnitude smaller (~1e-3 to
1e-6). A realistic microarray fold-change (this pipeline's evidence
threshold is 1.5-fold; clipped scores top out at 10x by default) multiplied
against 1000 can never shrink that bound down to where it would constrain a
~0.001-magnitude flux.

The fix: instead of scaling the reaction's literal (placeholder) bound,
scale a per-reaction *reference capacity* derived from flux variability
analysis (FVA) on the unconstrained wild-type model at a high fraction of
optimal growth (default 0.9 -- the range of flux each reaction could carry
while the network still achieves at least 90% of max WT growth). This
grounds the scaling in a magnitude the model actually uses, while still
allowing headroom for a mutant's rerouted flux to exceed the WT range when
an upregulated gene's score pushes it there.

This is a deliberate deviation from the originally approved formula (which
scaled the reaction's own model bound directly) -- made only after the null
result was diagnosed, and only with explicit sign-off, since it changes the
substance of the pipeline's output. It remains within the same E-Flux
framework: still a continuous, GPR-weighted, fold-change-referenced scaling
of a reaction's allowed flux range, just against a more meaningful baseline
than an arbitrary big-M constant. A reaction with FVA range {0, 0} at this
fraction of optimum (never used in any near-optimal WT solution) gets a
small epsilon floor rather than a hard-locked zero, so genotype-specific
rerouting through a WT-unused reaction remains possible rather than
permanently forbidden.
"""

from __future__ import annotations

import cobra
import pandas as pd
from cobra.flux_analysis import flux_variability_analysis


def compute_wt_reference_capacities(
    model: cobra.Model,
    fraction_of_optimum: float = 0.9,
    epsilon: float = 1e-6,
) -> pd.Series:
    """Return a Series indexed by reaction_id with a positive reference
    flux magnitude per reaction: max(|FVA min|, |FVA max|, epsilon).

    Run once against the unconstrained wild-type model; the same reference
    capacities are reused as the scaling base for every mutant genotype.
    """
    fva = flux_variability_analysis(model, fraction_of_optimum=fraction_of_optimum)
    reference = fva[["minimum", "maximum"]].abs().max(axis=1)
    reference = reference.clip(lower=epsilon)
    reference.name = "reference_capacity"
    return reference
