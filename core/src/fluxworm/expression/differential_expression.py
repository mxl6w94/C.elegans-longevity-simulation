"""Per-gene differential expression, each mutant genotype vs. wild type.

Biological rationale: since daf-2/rsks-1/daf-16 cannot be represented
directly in iCEL1314, this is the step that actually captures "what does
each mutation do metabolically" -- the transcriptional footprint each
mutation leaves on iCEL1314's real metabolic genes, measured against the
same-experiment wild-type samples (removing batch/array effects common to
both).

Method: for each gene present in the aggregated gene x sample expression
matrix (see `fluxworm.io.probe_annotation.aggregate_probes_to_genes`), and
each mutant genotype, compute:

    log2FC = mean(mutant samples) - mean(WT samples)     [already log2-scale]
    p-value = Welch's t-test (unequal variance; group sizes are 9 vs 9/10)
    q-value = Benjamini-Hochberg FDR correction across all genes tested
              for that genotype comparison

A gene counts as having "expression evidence" only if BOTH
|log2FC| > log2fc_threshold AND q < qvalue_threshold (both from config).
Genes without evidence are not dropped from the output table -- they are
carried through with evidence=False so that
`fluxworm.constraints.flux_constraint_builder` can leave their associated
reactions at a neutral (unscaled) bound, rather than let expression noise
silently perturb the model.

Caveat: n=9-10 per group is a small sample for microarray differential
expression -- this limits statistical power and inflates the false
negative/positive rate at the single-gene level (see the architecture
document's Limitations section). This is a real constraint of the source
dataset, not a bug in this analysis.
"""

from __future__ import annotations

import numpy as np
import pandas as pd
from scipy import stats
from statsmodels.stats.multitest import multipletests


def differential_expression(
    gene_matrix: pd.DataFrame,
    wt_samples: list[str],
    mutant_samples: list[str],
    log2fc_threshold: float,
    qvalue_threshold: float,
) -> pd.DataFrame:
    """Return a DataFrame indexed by gene_id with columns:
    log2fc, pvalue, qvalue, evidence (bool).
    """
    wt = gene_matrix[wt_samples]
    mut = gene_matrix[mutant_samples]

    log2fc = mut.mean(axis=1) - wt.mean(axis=1)

    t_stat, p_value = stats.ttest_ind(mut.values, wt.values, axis=1, equal_var=False)
    p_value = np.nan_to_num(p_value, nan=1.0)

    _, q_value, _, _ = multipletests(p_value, method="fdr_bh")

    evidence = (log2fc.abs() > log2fc_threshold) & (q_value < qvalue_threshold)

    return pd.DataFrame(
        {
            "log2fc": log2fc.values,
            "pvalue": p_value,
            "qvalue": q_value,
            "evidence": evidence.values,
        },
        index=gene_matrix.index,
    )


def differential_expression_all_genotypes(
    gene_matrix: pd.DataFrame,
    genotype_map: pd.Series,
    reference_genotype: str,
    mutant_genotypes: list[str],
    log2fc_threshold: float,
    qvalue_threshold: float,
) -> dict[str, pd.DataFrame]:
    wt_samples = genotype_map.index[genotype_map == reference_genotype].tolist()
    results = {}
    for genotype in mutant_genotypes:
        mutant_samples = genotype_map.index[genotype_map == genotype].tolist()
        results[genotype] = differential_expression(
            gene_matrix, wt_samples, mutant_samples, log2fc_threshold, qvalue_threshold
        )
    return results
