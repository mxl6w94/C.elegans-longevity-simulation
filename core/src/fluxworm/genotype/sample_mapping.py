"""Resolves each GSE52340 sample (GSM accession) to one of the 5 study genotypes.

The original truncated project script never reached this step. Rather than
guess a genotype from free-text sample titles (e.g. "daf-2 rsks-1-7"), this
module uses the GEO-curated "!Sample_characteristics_ch1" field tagged
"genotype: ..." -- verified directly against the real file to contain exactly
five clean, unambiguous values: "wild type", "rsks-1", "daf-2",
"daf-2 rsks-1", "daf-16; daf-2 rsks-1". No regex classification of sample
titles is needed or used.

A hard invariant is enforced (not just logged): the parsed sample counts per
genotype must exactly match `config.expected_counts` (verified once against
the real file: 9/9/9/10/10, summing to 47). Any mismatch -- a different GEO
file, a corrupted download, a future re-run against an updated series matrix
-- raises immediately rather than silently proceeding with a wrong grouping.
"""

from __future__ import annotations

import pandas as pd

from fluxworm.config import PipelineConfig


def build_genotype_map(sample_headers: pd.DataFrame, config: PipelineConfig) -> pd.Series:
    """Return a Series indexed by GSM accession with genotype label values."""
    if "characteristics_genotype" not in sample_headers.columns:
        raise KeyError(
            "No 'characteristics_genotype' column found after parsing sample headers. "
            f"Available columns: {list(sample_headers.columns)}"
        )

    genotype = sample_headers["characteristics_genotype"]

    observed_counts = genotype.value_counts().to_dict()
    expected = config.expected_counts
    if observed_counts != expected:
        raise ValueError(
            "Parsed genotype sample counts do not match the expected counts "
            "verified against the real GSE52340 file. "
            f"Expected: {expected}. Observed: {observed_counts}. "
            "This likely means a different or corrupted series matrix file was supplied."
        )

    return genotype


def samples_for_genotype(genotype_map: pd.Series, genotype: str) -> list[str]:
    return genotype_map.index[genotype_map == genotype].tolist()
