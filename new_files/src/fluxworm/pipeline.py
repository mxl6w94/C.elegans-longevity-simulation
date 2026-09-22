"""End-to-end orchestration: model + microarray -> per-genotype constrained
FBA -> comparison tables, figures, and an illustrative aging proxy.

Run via `scripts/run_pipeline.py`. See new_files/README.md and the approved
architecture document for the full biological/mathematical rationale behind
each step; this module just wires the pieces together and writes outputs to
disk under `config.results_dir`.
"""

from __future__ import annotations

import logging
from pathlib import Path

from fluxworm.aging.survival_model import build_aging_proxies, survival_curves_table
from fluxworm.analysis.flux_comparison import flux_fold_change_vs_wt, flux_table, growth_comparison_table
from fluxworm.analysis.subsystem_summary import functional_group_reroute_summary, tag_reactions_by_keyword
from fluxworm.config import PipelineConfig, load_config
from fluxworm.constraints.flux_constraint_builder import build_reaction_bounds, gene_scores_from_de
from fluxworm.constraints.reference_flux import compute_wt_reference_capacities
from fluxworm.expression.differential_expression import differential_expression_all_genotypes
from fluxworm.fba.runner import run_all_genotypes
from fluxworm.genotype.sample_mapping import build_genotype_map
from fluxworm.io.microarray_parser import parse_expression_matrix, parse_sample_headers
from fluxworm.io.model_loader import load_model, wild_type_sanity_check
from fluxworm.io.probe_annotation import aggregate_probes_to_genes, build_wbgene_to_seqname
from fluxworm.viz.plots import plot_functional_group_heatmap, plot_growth_comparison, plot_survival_curves

logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")
logger = logging.getLogger(__name__)


def run_pipeline(config: PipelineConfig) -> None:
    config.results_dir.mkdir(parents=True, exist_ok=True)

    logger.info("Loading iCEL1314 model from %s", config.model_xml)
    model = load_model(config.model_xml, config.biomass_reaction)
    wt_growth_unconstrained = wild_type_sanity_check(model)
    logger.info("Unconstrained WT growth flux: %.6f", wt_growth_unconstrained)

    logger.info("Parsing GSE52340 series matrix from %s", config.series_matrix)
    sample_headers = parse_sample_headers(config.series_matrix)
    genotype_map = build_genotype_map(sample_headers, config)
    genotype_map.to_csv(config.results_dir / "genotype_map.csv")
    logger.info("Genotype counts: %s", genotype_map.value_counts().to_dict())

    expression_matrix = parse_expression_matrix(config.series_matrix)
    wbgene_to_seqname = build_wbgene_to_seqname(model)
    gene_matrix = aggregate_probes_to_genes(expression_matrix, wbgene_to_seqname)
    logger.info(
        "Matched %d of %d model genes to array probes (%d unmapped)",
        gene_matrix.shape[0],
        len(wbgene_to_seqname),
        len(wbgene_to_seqname) - gene_matrix.shape[0],
    )

    de_by_genotype = differential_expression_all_genotypes(
        gene_matrix,
        genotype_map,
        config.reference_genotype,
        config.mutant_genotypes,
        config.log2fc_threshold,
        config.qvalue_threshold,
    )
    for genotype, de_table in de_by_genotype.items():
        de_table.to_csv(config.results_dir / f"de_{_safe_name(genotype)}_vs_wt.csv")
        logger.info("%s: %d genes with expression evidence", genotype, int(de_table["evidence"].sum()))

    logger.info("Computing wild-type reference flux capacities via FVA (fraction_of_optimum=0.9)...")
    reference_capacities = compute_wt_reference_capacities(model, fraction_of_optimum=0.9)
    reference_capacities.to_csv(config.results_dir / "wt_reference_capacities.csv")

    bounds_by_genotype = {}
    for genotype, de_table in de_by_genotype.items():
        gene_scores = gene_scores_from_de(de_table, config.min_scale, config.max_scale)
        bounds_table = build_reaction_bounds(model, gene_scores, reference_capacities=reference_capacities)
        bounds_table.to_csv(config.results_dir / f"constraints_{_safe_name(genotype)}.csv")
        bounds_by_genotype[genotype] = bounds_table

    fba_results = run_all_genotypes(model, config.reference_genotype, bounds_by_genotype)

    growth_table = growth_comparison_table(fba_results, config.reference_genotype)
    growth_table.to_csv(config.results_dir / "growth_comparison.csv")
    logger.info("Growth comparison:\n%s", growth_table)

    flux_df = flux_table(fba_results)
    flux_df.to_csv(config.results_dir / "flux_table.csv")
    fold_change_df = flux_fold_change_vs_wt(flux_df, config.reference_genotype)

    keyword_groups = {"lipid_metabolism": config.stress_subsystem_keywords}
    reaction_tags = tag_reactions_by_keyword(model, keyword_groups)
    reroute_summary = functional_group_reroute_summary(fold_change_df, reaction_tags)
    reroute_summary.to_csv(config.results_dir / "functional_group_reroute_summary.csv")

    stress_reactions = reaction_tags.index[reaction_tags == "lipid_metabolism"]
    stress_flux_by_genotype = flux_df.loc[flux_df.index.intersection(stress_reactions)].abs().sum().to_dict()
    growth_by_genotype = growth_table["biomass_flux"].to_dict()

    proxies = build_aging_proxies(
        growth_by_genotype,
        stress_flux_by_genotype,
        config.reference_genotype,
        config.biomass_weight,
        config.stress_weight,
        config.wt_gompertz_C,
    )
    survival_table = survival_curves_table(proxies, config.gompertz_B)
    survival_table.to_csv(config.results_dir / "survival_curves_illustrative.csv")

    plot_growth_comparison(growth_table, config.results_dir / "growth_comparison.png")
    plot_functional_group_heatmap(reroute_summary, config.results_dir / "functional_group_reroute_heatmap.png")
    plot_survival_curves(survival_table, config.results_dir / "survival_curves_illustrative.png")

    logger.info("Pipeline complete. Results written to %s", config.results_dir)


def _safe_name(genotype: str) -> str:
    return genotype.replace(";", "").replace(" ", "_")


def main(config_path: str | Path) -> None:
    config = load_config(config_path)
    run_pipeline(config)


if __name__ == "__main__":
    import sys

    main(sys.argv[1] if len(sys.argv) > 1 else Path(__file__).resolve().parents[2] / "config" / "config.yaml")
