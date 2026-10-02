"""Maps GSE52340 NimbleGen probe IDs to iCEL1314 WormBase gene IDs.

The original plan for this module assumed we would need to download an
external Affymetrix platform annotation table (GPL200) to bridge probe IDs
to gene IDs. Two facts, verified directly against the real files before
writing this module, made that unnecessary:

1. GSE52340's platform is GPL17925, a NimbleGen 12-plex array, not
   Affymetrix. Its probe IDs are literally "<WormBase sequence name>P<probe
   index>" (e.g. "F35H10.4P00123" = gene F35H10.4, probe 123) -- the gene
   identity is already encoded in the probe ID string.
2. iCEL1314's own SBML annotations already carry each gene's WormBase
   sequence name as a KEGG cross-reference, e.g. gene WBGene00006914 has
   `annotation["kegg.genes"] == "CELE_F35H10.4"`. Stripping the "CELE_"
   prefix recovers the same sequence name used in the probe IDs.

So probe-to-gene mapping is done entirely from data already in this
project's two files, with no network dependency and no separate annotation
file to source, version, or go stale.

Caveat (documented, not silently absorbed): only ~787 of iCEL1314's 1,314
genes have a sequence name that is actually present among the array's
probed genes (verified by direct set intersection against the real data).
The remainder either lack a "kegg.genes" annotation in the SBML (13 genes)
or simply were not represented/probed on this particular array. Those genes
receive no expression evidence and are left at a neutral score (see
`fluxworm.constraints.flux_constraint_builder`), not silently treated as
downregulated.
"""

from __future__ import annotations

import re

import cobra
import pandas as pd

_PROBE_SUFFIX_RE = re.compile(r"^(?P<seqname>.+)P\d+$")


def build_wbgene_to_seqname(model: cobra.Model) -> dict[str, str]:
    """Return {WBGene ID: WormBase sequence name} for every model gene that
    carries a KEGG genes cross-reference in its SBML annotation.
    """
    mapping: dict[str, str] = {}
    for gene in model.genes:
        kegg_id = gene.annotation.get("kegg.genes")
        if not kegg_id:
            continue
        # cobrapy returns a bare string for a single RDF cross-reference but
        # a list when a gene carries more than one kegg.genes annotation;
        # the first entry is used in that case.
        if isinstance(kegg_id, list):
            kegg_id = kegg_id[0]
        seqname = kegg_id[len("CELE_"):] if kegg_id.startswith("CELE_") else kegg_id
        mapping[gene.id] = seqname
    return mapping


def aggregate_probes_to_genes(
    expression_matrix: pd.DataFrame,
    wbgene_to_seqname: dict[str, str],
) -> pd.DataFrame:
    """Collapse the probe x sample matrix to a WBGene x sample matrix.

    Each probe row is assigned to a gene by stripping its trailing
    "P<digits>" suffix to recover the sequence name, then joining against
    `wbgene_to_seqname`. Genes with multiple probes are aggregated by mean
    (a probe-level replicate average, not a statistical claim about which
    probe is "correct").
    """
    seqname_to_wbgene: dict[str, str] = {}
    for wbgene, seqname in wbgene_to_seqname.items():
        seqname_to_wbgene.setdefault(seqname, wbgene)

    probe_seqnames = expression_matrix.index.to_series().str.extract(_PROBE_SUFFIX_RE)["seqname"]
    gene_ids = probe_seqnames.map(seqname_to_wbgene)

    matched = expression_matrix.loc[gene_ids.notna()].copy()
    matched["_wbgene"] = gene_ids[gene_ids.notna()].values

    gene_matrix = matched.groupby("_wbgene").mean(numeric_only=True)
    gene_matrix.index.name = "gene_id"
    return gene_matrix
