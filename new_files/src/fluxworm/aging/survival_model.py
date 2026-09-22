"""An explicitly illustrative link from a genotype's FBA flux profile to a
Gompertz survival curve.

*** THIS MODULE DOES NOT PREDICT OR VALIDATE C. ELEGANS LIFESPAN. ***

FBA is a steady-state method; it has no mechanism for representing a
time-dependent process like aging. Everything in this module is a
deliberately simple, clearly-labeled proxy layered on top of the FBA
results, built only to qualitatively reproduce the known ordering from
Chen et al. 2013 (WT shortest-lived < single mutants < daf-2;rsks-1 double
mutant longest-lived, with the daf-16;daf-2;rsks-1 triple mutant partially
reverting toward WT because daf-16 is required for the longevity effect).
It has no predictive validity for any genotype whose ranking is not already
known, and every output of this module is labeled "Illustrative Aging Proxy
(Not Validated)".

Method:

1. Composite score per genotype:
       Z = biomass_weight * (growth_m / growth_WT)
         + stress_weight  * (2.0 - stress_flux_m / stress_flux_WT)
   where stress_flux is total absolute flux through the keyword-tagged
   "lipid_metabolism" reaction group (see
   `fluxworm.analysis.subsystem_summary`).

   The (2.0 - ratio) form, rather than the ratio directly, is a sign choice
   calibrated post-hoc against the real pipeline output, exactly as
   documented below for the Gompertz rate constant: the first real run
   showed daf-2 and daf-2;rsks-1 (the genotypes reported as longer-lived in
   Chen et al. 2013) had *reduced* flux through lipid/fatty-acid-tagged
   reactions relative to WT, not increased -- directionally consistent with
   the literature's report that these mutants increase fat storage via
   *reduced* fatty acid oxidation/turnover. A direct positive ratio term
   would therefore have scored the longer-lived mutants as metabolically
   *less* favorable, inverting the intended ranking. (2.0 - ratio) makes a
   below-WT lipid-pathway flux score above the WT baseline of 1.0 instead,
   which is what "reduced turnover is treated as favorable for the
   illustrative longevity score" requires. This is stated plainly because
   it is a real, consequential modeling choice, not an implementation
   detail: it only reflects the *direction* observed in this one dataset
   and reaction-tagging heuristic, not a general biological law, and a
   different dataset or subsystem definition could reasonably flip it back.

2. Per-genotype Gompertz rate constant: C_m = C_WT / Z_m (higher Z -> slower
   assumed aging rate). This inverse relationship, and the specific
   weights, are a chosen functional form fit to reproduce the qualitative
   ranking above -- not derived from any mechanistic aging theory.

3. Gompertz survival curve: S(t) = exp(-(B/C) * (exp(C*t) - 1)), evaluated
   over an arbitrary dimensionless time axis (not calibrated to real days).
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd


@dataclass
class AgingProxyResult:
    genotype: str
    composite_score_z: float
    gompertz_c: float


def composite_score(
    growth_ratio: float,
    stress_flux_ratio: float,
    biomass_weight: float,
    stress_weight: float,
) -> float:
    # See module docstring for why the stress term is (2.0 - ratio) rather
    # than the ratio itself: a reduced lipid-pathway flux ratio (< 1) is
    # treated as favorable, matching what was observed for the longer-lived
    # genotypes in this pipeline's real output.
    return biomass_weight * growth_ratio + stress_weight * (2.0 - stress_flux_ratio)


def gompertz_rate_constant(z_score: float, wt_gompertz_c: float) -> float:
    if z_score <= 0:
        raise ValueError(f"Composite score Z must be positive to invert into a Gompertz rate constant, got {z_score}")
    return wt_gompertz_c / z_score


def gompertz_survival(t: np.ndarray, gompertz_b: float, gompertz_c: float) -> np.ndarray:
    return np.exp(-(gompertz_b / gompertz_c) * (np.exp(gompertz_c * t) - 1.0))


def build_aging_proxies(
    growth_by_genotype: dict[str, float],
    stress_flux_by_genotype: dict[str, float],
    reference_genotype: str,
    biomass_weight: float,
    stress_weight: float,
    wt_gompertz_c: float,
) -> dict[str, AgingProxyResult]:
    wt_growth = growth_by_genotype[reference_genotype]
    wt_stress = stress_flux_by_genotype[reference_genotype]

    proxies: dict[str, AgingProxyResult] = {}
    for genotype in growth_by_genotype:
        growth_ratio = growth_by_genotype[genotype] / wt_growth if wt_growth else np.nan
        stress_ratio = stress_flux_by_genotype[genotype] / wt_stress if wt_stress else np.nan
        z = composite_score(growth_ratio, stress_ratio, biomass_weight, stress_weight)
        c = gompertz_rate_constant(z, wt_gompertz_c) if genotype != reference_genotype else wt_gompertz_c
        proxies[genotype] = AgingProxyResult(genotype=genotype, composite_score_z=z, gompertz_c=c)
    return proxies


def survival_curves_table(proxies: dict[str, AgingProxyResult], gompertz_b: float, t_max: float = 50.0, n_points: int = 200) -> pd.DataFrame:
    t = np.linspace(0, t_max, n_points)
    data = {"t": t}
    for genotype, proxy in proxies.items():
        data[genotype] = gompertz_survival(t, gompertz_b, proxy.gompertz_c)
    return pd.DataFrame(data)
