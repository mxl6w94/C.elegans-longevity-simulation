import pandas as pd
import pytest

from fluxworm.aging.survival_model import build_aging_proxies
from fluxworm.aging.validation import load_lifespan_reference, validate_against_reference


def test_reference_file_drops_genotypes_without_a_number(tmp_path):
    path = tmp_path / "ref.csv"
    path.write_text("genotype,mean_lifespan_change_pct\nwild type,0\nlong,150\nunknown,\n")
    measured = load_lifespan_reference(path)
    assert measured["long"] == pytest.approx(2.5)
    assert "unknown" not in measured.index


def test_validation_reports_error_and_fitted_exponent():
    proxies = build_aging_proxies({"wild type": 1.0, "a": 0.5, "b": 0.25}, "wild type")
    # Lab lifespans that follow lifespan = growth^-2 exactly
    measured = pd.Series({"wild type": 1.0, "a": 4.0, "b": 16.0})
    table, summary = validate_against_reference(proxies, measured, "wild type")

    assert list(table.index) == ["a", "b"]
    assert table.loc["a", "predicted_scale"] == pytest.approx(2.0)
    assert table.loc["a", "error_pct"] == pytest.approx(-50.0)
    assert summary["fitted_exponent"] == pytest.approx(2.0)
    assert summary["fitted_exponent_loo_mean_abs_error_pct"] == pytest.approx(0.0, abs=1e-9)
