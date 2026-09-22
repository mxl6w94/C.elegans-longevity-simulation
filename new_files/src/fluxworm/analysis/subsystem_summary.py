"""Groups reactions into coarse functional tags and summarizes flux rerouting
by tag, per genotype.

IMPORTANT DEVIATION FROM THE ORIGINAL PLAN, verified directly against the
model file before writing this module: iCEL1314 as distributed here carries
**no subsystem or pathway annotation whatsoever** -- `reaction.subsystem` is
an empty string for all 2,230 reactions, and there is no SBML "groups"
package data either. The originally planned "subsystem-level flux rerouting
summary" therefore cannot use curated pathway membership.

What this module does instead: it derives a coarse functional tag per
reaction by keyword-matching the reaction's free-text `name` field (e.g. a
name containing "fatty acid" or "lipid" gets tagged "lipid_metabolism").
This is a heuristic label for grouping and reporting, NOT an official
subsystem/pathway assignment -- it will misclassify or fail to tag many
reactions and must not be cited in any manuscript text as pathway-level
evidence. It exists to give a human-readable, low-resolution view of where
flux changes concentrate, and it is also what
`fluxworm.aging.survival_model` uses to compute a genotype's "stress flux"
proxy for the lipid/fatty-acid-metabolism keyword group specifically (see
that module's docstring for why this subsystem was chosen: daf-2/rsks-1
mutants are known from the literature to shift metabolism toward fat
storage).
"""

from __future__ import annotations

import cobra
import pandas as pd


def tag_reactions_by_keyword(model: cobra.Model, keyword_groups: dict[str, list[str]]) -> pd.Series:
    """Return a Series indexed by reaction_id with a functional tag string
    (or "untagged") based on case-insensitive substring matches of
    `reaction.name` against each keyword group's keyword list. The first
    matching group wins; group iteration order therefore matters if a name
    could match more than one group's keywords.
    """
    tags = {}
    for rxn in model.reactions:
        name_lower = (rxn.name or "").lower()
        tag = "untagged"
        for group_name, keywords in keyword_groups.items():
            if any(kw.lower() in name_lower for kw in keywords):
                tag = group_name
                break
        tags[rxn.id] = tag
    return pd.Series(tags, name="functional_tag")


def functional_group_reroute_summary(
    flux_fold_change: pd.DataFrame,
    reaction_tags: pd.Series,
) -> pd.DataFrame:
    """Median |fold-change vs WT| per functional tag, per mutant genotype.

    Median rather than mean: even with an epsilon floor on the fold-change
    denominator (see `flux_comparison.flux_fold_change_vs_wt`), a handful of
    reactions with a genuinely near-zero WT flux can produce enormous
    individual fold-change values that would otherwise dominate a group
    mean and misrepresent the group's typical reroute magnitude.

    Ranking this table (descending) surfaces which keyword-derived
    functional groups show the largest typical flux reroute -- a
    hypothesis-generating signal, not a validated pathway-level finding.
    """
    joined = flux_fold_change.join(reaction_tags, how="inner")
    return joined.groupby("functional_tag").median(numeric_only=True).sort_values(
        by=list(flux_fold_change.columns), ascending=False
    )
