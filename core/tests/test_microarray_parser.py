from pathlib import Path

from fluxworm.io.microarray_parser import parse_expression_matrix, parse_sample_headers

FIXTURE = Path(__file__).parent / "fixtures" / "mini_series_matrix.txt.gz"


def test_parse_sample_headers_recovers_genotype_column():
    headers = parse_sample_headers(FIXTURE)
    assert len(headers) == 6
    assert "characteristics_genotype" in headers.columns
    assert set(headers["characteristics_genotype"]) == {"wild type", "mutX"}
    assert (headers["characteristics_genotype"] == "wild type").sum() == 3
    assert (headers["characteristics_genotype"] == "mutX").sum() == 3


def test_parse_expression_matrix_shape_and_values():
    matrix = parse_expression_matrix(FIXTURE)
    assert matrix.shape == (4, 6)
    assert "geneA.1P00001" in matrix.index
    assert matrix.loc["geneA.1P00001", "GSM4"] == 10.0
