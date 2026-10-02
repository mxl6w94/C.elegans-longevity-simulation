"""Pipeline configuration loading and path resolution.

Deliberately avoids any hardcoded Google Colab / Drive paths (the defect in
the original old_files/*.py scripts, which pointed at
"/content/drive/MyDrive/..." and could never run outside that one author's
Colab session). All paths are resolved relative to a configurable data
directory, overridable via the FLUXWORM_DATA_DIR environment variable so the
pipeline runs unmodified on any machine that has a copy of the project data.
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml


@dataclass(frozen=True)
class PipelineConfig:
    data_dir: Path
    model_xml: Path
    series_matrix: Path
    results_dir: Path
    reference_genotype: str
    mutant_genotypes: list[str]
    expected_counts: dict[str, int]
    log2fc_threshold: float
    qvalue_threshold: float
    min_scale: float
    max_scale: float
    biomass_reaction: str
    solver: str | None
    stress_subsystem_keywords: list[str]
    biomass_weight: float
    stress_weight: float
    gompertz_B: float
    wt_gompertz_C: float

    @property
    def all_genotypes(self) -> list[str]:
        return [self.reference_genotype, *self.mutant_genotypes]


def load_config(config_path: str | Path) -> PipelineConfig:
    config_path = Path(config_path).resolve()
    with open(config_path, "r", encoding="utf-8") as f:
        raw: dict[str, Any] = yaml.safe_load(f)

    env_override = os.environ.get("FLUXWORM_DATA_DIR")
    data_dir = Path(env_override) if env_override else (config_path.parent / raw["data_dir"])
    data_dir = data_dir.resolve()

    paths = raw["paths"]
    genotypes = raw["genotypes"]
    de = raw["differential_expression"]
    constraints = raw["constraints"]
    fba = raw["fba"]
    aging = raw["aging"]

    return PipelineConfig(
        data_dir=data_dir,
        model_xml=(data_dir / paths["model_xml"]).resolve(),
        series_matrix=(data_dir / paths["series_matrix"]).resolve(),
        results_dir=(data_dir / paths["results_dir"]).resolve(),
        reference_genotype=genotypes["reference"],
        mutant_genotypes=list(genotypes["mutants"]),
        expected_counts=dict(genotypes["expected_counts"]),
        log2fc_threshold=float(de["log2fc_threshold"]),
        qvalue_threshold=float(de["qvalue_threshold"]),
        min_scale=float(constraints["min_scale"]),
        max_scale=float(constraints["max_scale"]),
        biomass_reaction=fba["biomass_reaction"],
        solver=fba.get("solver"),
        stress_subsystem_keywords=list(aging["stress_subsystem_keywords"]),
        biomass_weight=float(aging["biomass_weight"]),
        stress_weight=float(aging["stress_weight"]),
        gompertz_B=float(aging["gompertz_B"]),
        wt_gompertz_C=float(aging["wt_gompertz_C"]),
    )
