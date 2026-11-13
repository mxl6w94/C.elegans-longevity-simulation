import numpy as np
import pytest

from fluxworm.aging.survival_model import (
    build_aging_proxies,
    gompertz_survival,
    lifespan_scale,
    survival_curves_table,
)


def _mean_lifespan(t, s):
    return float(np.sum((s[1:] + s[:-1]) * np.diff(t)) / 2.0)


def test_gompertz_survival_starts_at_one_and_decreases():
    t = np.linspace(0, 50, 100)
    s = gompertz_survival(t, gompertz_b=0.01, gompertz_c=0.1)
    assert s[0] == 1.0
    assert np.all(np.diff(s) <= 0)


def test_higher_rate_constant_shortens_half_survival_time():
    t = np.linspace(0, 100, 1000)
    s_slow = gompertz_survival(t, gompertz_b=0.01, gompertz_c=0.05)
    s_fast = gompertz_survival(t, gompertz_b=0.01, gompertz_c=0.2)

    t_half_slow = t[np.searchsorted(-s_slow, -0.5)]
    t_half_fast = t[np.searchsorted(-s_fast, -0.5)]
    assert t_half_fast < t_half_slow


def test_lifespan_scale_is_inverse_growth_by_default():
    assert lifespan_scale(1.0) == 1.0
    assert lifespan_scale(0.5) == pytest.approx(2.0)
    assert lifespan_scale(0.5, exponent=2.0) == pytest.approx(4.0)


def test_lifespan_scale_is_capped_and_rejects_no_growth():
    assert lifespan_scale(0.001, max_scale=10.0) == 10.0
    with pytest.raises(ValueError):
        lifespan_scale(0.0)


def test_lower_growth_capacity_gives_longer_life_and_wild_type_is_baseline():
    proxies = build_aging_proxies({"wild type": 10.0, "slow_grower": 5.0, "same": 10.0}, "wild type")
    assert proxies["wild type"].lifespan_scale == 1.0
    assert proxies["same"].lifespan_scale == pytest.approx(1.0)
    assert proxies["slow_grower"].lifespan_scale == pytest.approx(2.0)


def test_survival_curve_is_wild_type_curve_stretched_in_time():
    """Temporal scaling: mean lifespan scales by exactly the lifespan scale."""
    proxies = build_aging_proxies({"wild type": 10.0, "slow_grower": 4.0}, "wild type")
    table = survival_curves_table(proxies, gompertz_b=0.01, wt_gompertz_c=0.1, n_points=4000)
    t = table["t"].to_numpy()
    wt_mean = _mean_lifespan(t, table["wild type"].to_numpy())
    mutant_mean = _mean_lifespan(t, table["slow_grower"].to_numpy())
    assert mutant_mean / wt_mean == pytest.approx(2.5, rel=1e-3)
    # every curve has died out by the end of the table
    assert table["slow_grower"].iloc[-1] < 1e-3
