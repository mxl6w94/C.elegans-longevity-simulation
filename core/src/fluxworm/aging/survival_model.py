"""Links a genotype's constrained-FBA growth capacity to a survival curve.

*** THIS IS A SIMPLE SCALING MODEL, NOT A VALIDATED LIFESPAN PREDICTOR. ***
Its error against measured lifespans is reported by
`fluxworm.aging.validation` every time the pipeline runs.

Method (restructured; see "What changed" below):

1. Lifespan scale. Each genotype gets one number, how many times longer it
   lives than wild type:

       scale = (growth_m / growth_WT) ** (-lifespan_exponent)

   With the default exponent of 1, lifespan is inversely proportional to
   the genotype's maximum growth (biosynthetic) capacity. This encodes the
   growth/longevity trade-off: reduced insulin/IGF-1 or TOR signaling lowers
   anabolic capacity and extends life. It is an assumption of this model,
   not something FBA derives. The exponent is NOT fitted to the lifespan
   data by default; `validation.py` reports what a fitted value would be.

2. Temporal scaling. The genotype's survival curve is the wild-type
   Gompertz curve stretched in time by that scale:

       S_m(t) = S_WT(t / scale),   S_WT(t) = exp(-(B/C) * (exp(C*t) - 1))

   Stroustrup et al. 2016 (Nature) found that C. elegans survival curves
   under many interventions, including insulin-signaling mutants, differ by
   a time rescaling only. Stretching time is the same as dividing both
   Gompertz constants by the scale.

   The time axis is arbitrary model units, not days.

What changed, and why:

The first version combined growth and lipid-pathway flux into a score
Z = w1 * growth_ratio + w2 * (2 - lipid_ratio) and set C = C_WT / Z. Three
problems showed up when its output was compared with the measured lifespans
(Chen et al. 2013: rsks-1 +20%, daf-2 +169%, daf-2 rsks-1 +454%):

* The growth term had the wrong sign for these mutants. Lower growth
  capacity lowered Z, which shortened predicted life, while the long-lived
  mutants are the ones with reduced growth capacity.
* The lipid term's sign had been flipped after the first run to recover
  the known ranking, so it could not count as a prediction.
* Changing only C altered the curve's shape instead of rescaling time, and
  a ~0.1% change in Z gave a ~0.07% change in lifespan against measured
  changes of 20% to 454%.

Limits that remain (see validation output): the scale is capped at
`max_scale`, because a reaction constraint that nearly abolishes growth
would otherwise predict an unbounded lifespan when it should predict a sick
or dead worm. The model applies to expression-derived constraints in viable
genotypes, not to lethal knockouts.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd


@dataclass
class AgingProxyResult:
    genotype: str
    growth_ratio: float
    lifespan_scale: float  # predicted lifespan as a multiple of wild type


def lifespan_scale(growth_ratio: float, exponent: float = 1.0, max_scale: float = 10.0) -> float:
    """Predicted lifespan as a multiple of wild type for a given growth ratio."""
    if not np.isfinite(growth_ratio) or growth_ratio <= 0:
        raise ValueError(
            f"Growth ratio must be positive to derive a lifespan scale, got {growth_ratio}. "
            "A genotype with no growth is not viable; no lifespan is predicted for it."
        )
    return float(min(growth_ratio ** (-exponent), max_scale))


def gompertz_survival(t: np.ndarray, gompertz_b: float, gompertz_c: float, scale: float = 1.0) -> np.ndarray:
    """Gompertz survival, optionally stretched in time by `scale`."""
    return np.exp(-(gompertz_b / gompertz_c) * (np.exp(gompertz_c * np.asarray(t) / scale) - 1.0))


def build_aging_proxies(
    growth_by_genotype: dict[str, float],
    reference_genotype: str,
    lifespan_exponent: float = 1.0,
    max_scale: float = 10.0,
) -> dict[str, AgingProxyResult]:
    wt_growth = growth_by_genotype[reference_genotype]
    if not wt_growth or wt_growth <= 0:
        raise ValueError(f"Wild-type growth must be positive, got {wt_growth}")

    proxies: dict[str, AgingProxyResult] = {}
    for genotype, growth in growth_by_genotype.items():
        ratio = growth / wt_growth
        scale = 1.0 if genotype == reference_genotype else lifespan_scale(ratio, lifespan_exponent, max_scale)
        proxies[genotype] = AgingProxyResult(genotype=genotype, growth_ratio=ratio, lifespan_scale=scale)
    return proxies


def survival_curves_table(
    proxies: dict[str, AgingProxyResult],
    gompertz_b: float,
    wt_gompertz_c: float,
    t_max: float | None = None,
    n_points: int = 400,
) -> pd.DataFrame:
    """Survival curve per genotype on a shared time axis.

    `t_max` defaults to 50 model-time units (where the wild-type curve has
    died out) times the largest lifespan scale, so every curve reaches zero.
    """
    if t_max is None:
        t_max = 50.0 * max(p.lifespan_scale for p in proxies.values())
    t = np.linspace(0, t_max, n_points)
    data = {"t": t}
    for genotype, proxy in proxies.items():
        data[genotype] = gompertz_survival(t, gompertz_b, wt_gompertz_c, proxy.lifespan_scale)
    return pd.DataFrame(data)
