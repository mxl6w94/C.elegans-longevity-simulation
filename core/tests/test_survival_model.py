import numpy as np

from fluxworm.aging.survival_model import build_aging_proxies, gompertz_survival, survival_curves_table


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


def test_higher_composite_score_yields_longer_illustrative_survival():
    growth = {"wild type": 10.0, "long_lived_mutant": 10.0}
    # Reduced lipid-pathway flux (ratio < 1) is treated as favorable -- see
    # survival_model's module docstring for why (matches the direction
    # observed for daf-2/daf-2;rsks-1 in this pipeline's real output).
    stress = {"wild type": 1.0, "long_lived_mutant": 0.5}

    proxies = build_aging_proxies(
        growth, stress, reference_genotype="wild type",
        biomass_weight=0.5, stress_weight=0.5, wt_gompertz_c=0.1,
    )
    assert proxies["long_lived_mutant"].composite_score_z > proxies["wild type"].composite_score_z
    assert proxies["long_lived_mutant"].gompertz_c < proxies["wild type"].gompertz_c

    table = survival_curves_table(proxies, gompertz_b=0.01)
    assert table["long_lived_mutant"].iloc[-1] > table["wild type"].iloc[-1]
