"""Matplotlib figures for the pipeline report. Saved as PNG files into
config.results_dir by fluxworm.pipeline.
"""

from __future__ import annotations

from pathlib import Path

import matplotlib
import matplotlib.pyplot as plt
import pandas as pd

matplotlib.use("Agg")


def plot_growth_comparison(growth_table: pd.DataFrame, out_path: str | Path) -> None:
    fig, ax = plt.subplots(figsize=(7, 4.5))
    growth_table["biomass_flux"].plot(kind="bar", ax=ax, color="#4C72B0")
    ax.set_ylabel("Biomass flux (BIO0010, model units)")
    ax.set_title("Constrained FBA growth flux by genotype")
    ax.set_xlabel("")
    plt.xticks(rotation=30, ha="right")
    fig.tight_layout()
    fig.savefig(out_path, dpi=150)
    plt.close(fig)


def plot_functional_group_heatmap(reroute_summary: pd.DataFrame, out_path: str | Path) -> None:
    fig, ax = plt.subplots(figsize=(7, max(3, 0.4 * len(reroute_summary))))
    im = ax.imshow(reroute_summary.values, aspect="auto", cmap="viridis")
    ax.set_xticks(range(len(reroute_summary.columns)))
    ax.set_xticklabels(reroute_summary.columns, rotation=30, ha="right")
    ax.set_yticks(range(len(reroute_summary.index)))
    ax.set_yticklabels(reroute_summary.index)
    ax.set_title("Mean |flux fold-change vs WT| by keyword-derived functional group\n(heuristic tag, not a curated subsystem)")
    fig.colorbar(im, ax=ax, label="mean |fold-change|")
    fig.tight_layout()
    fig.savefig(out_path, dpi=150)
    plt.close(fig)


def plot_survival_curves(survival_table: pd.DataFrame, out_path: str | Path) -> None:
    fig, ax = plt.subplots(figsize=(7, 4.5))
    for genotype in survival_table.columns:
        if genotype == "t":
            continue
        ax.plot(survival_table["t"], survival_table[genotype], label=genotype)
    ax.set_xlabel("Model time (arbitrary units, not calibrated to days)")
    ax.set_ylabel("Survival probability")
    ax.set_title("Illustrative Aging Proxy (Not Validated)\nGompertz survival curves derived from FBA flux signature")
    ax.legend(fontsize=8)
    fig.tight_layout()
    fig.savefig(out_path, dpi=150)
    plt.close(fig)
