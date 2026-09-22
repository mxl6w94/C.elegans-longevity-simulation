"""fluxworm: transcriptomics-constrained FBA pipeline for C. elegans daf-2/rsks-1 longevity.

See new_files/README.md and the architecture document this package implements
(the plan approved before any code here was written) for the full biological
and mathematical rationale. In short: daf-2 and rsks-1 are insulin/IGF-1 and
TOR/S6K signaling genes absent from the iCEL1314 metabolic reconstruction, so
their effect is modeled indirectly, via differential expression of iCEL1314's
actual metabolic genes (from the GSE52340 microarray dataset) mapped onto
reaction flux bounds (a fold-change-referenced E-Flux-style scaling), rather
than as a literal COBRApy gene knockout.
"""

__version__ = "0.1.0"
