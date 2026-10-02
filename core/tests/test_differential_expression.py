import numpy as np
import pandas as pd
import pytest

from fluxworm.expression.differential_expression import differential_expression


def test_differential_expression_recovers_known_fold_change():
    rng = np.random.default_rng(0)
    wt_samples = [f"wt{i}" for i in range(9)]
    mut_samples = [f"mut{i}" for i in range(9)]

    # gene_up: mutant mean = wt mean + 2 (log2fc = 2), tight noise -> should be significant
    # gene_flat: no difference -> should not be significant
    gene_matrix = pd.DataFrame(
        {
            **{s: [10.0 + rng.normal(0, 0.1)] for s in wt_samples},
            **{s: [12.0 + rng.normal(0, 0.1)] for s in mut_samples},
        },
        index=["gene_up"],
    )
    flat_row = pd.DataFrame(
        {**{s: [10.0 + rng.normal(0, 0.1)] for s in wt_samples}, **{s: [10.0 + rng.normal(0, 0.1)] for s in mut_samples}},
        index=["gene_flat"],
    )
    gene_matrix = pd.concat([gene_matrix, flat_row])

    result = differential_expression(gene_matrix, wt_samples, mut_samples, log2fc_threshold=0.585, qvalue_threshold=0.05)

    assert result.loc["gene_up", "log2fc"] == pytest.approx(2.0, abs=0.3)
    assert result.loc["gene_up", "evidence"]
    assert not result.loc["gene_flat", "evidence"]
