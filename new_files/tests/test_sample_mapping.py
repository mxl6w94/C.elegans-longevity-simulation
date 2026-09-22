from pathlib import Path

import pytest

from fluxworm.config import PipelineConfig
from fluxworm.genotype.sample_mapping import build_genotype_map, samples_for_genotype
from fluxworm.io.microarray_parser import parse_sample_headers

FIXTURE = Path(__file__).parent / "fixtures" / "mini_series_matrix.txt.gz"


def _fixture_config(expected_counts):
    return PipelineConfig(
        data_dir=Path("."),
        model_xml=Path("."),
        series_matrix=FIXTURE,
        results_dir=Path("."),
        reference_genotype="wild type",
        mutant_genotypes=["mutX"],
        expected_counts=expected_counts,
        log2fc_threshold=0.585,
        qvalue_threshold=0.05,
        min_scale=0.1,
        max_scale=10.0,
        biomass_reaction="BIO0010",
        solver=None,
        stress_subsystem_keywords=["lipid"],
        biomass_weight=0.5,
        stress_weight=0.5,
        gompertz_B=0.01,
        wt_gompertz_C=0.10,
    )


def test_build_genotype_map_matches_expected_counts():
    headers = parse_sample_headers(FIXTURE)
    config = _fixture_config({"wild type": 3, "mutX": 3})
    genotype_map = build_genotype_map(headers, config)
    assert len(genotype_map) == 6
    assert len(samples_for_genotype(genotype_map, "wild type")) == 3
    assert len(samples_for_genotype(genotype_map, "mutX")) == 3


def test_build_genotype_map_raises_on_count_mismatch():
    headers = parse_sample_headers(FIXTURE)
    config = _fixture_config({"wild type": 4, "mutX": 2})
    with pytest.raises(ValueError):
        build_genotype_map(headers, config)
