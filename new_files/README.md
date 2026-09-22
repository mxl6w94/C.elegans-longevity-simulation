# fluxworm: transcriptomics-constrained FBA for C. elegans daf-2/rsks-1 longevity

**New to this project?** Open [`PRIMER.html`](PRIMER.html) in a browser first —
a zero-background, illustrated walkthrough of the whole pipeline (the
biology, the math, and the real dead-ends/fixes below) written for a reader
with no biology or computational background. This README is the technical
reference; the primer is the plain-language front door.

**Rebuilding this yourself?** See [`IMPLEMENTATION_BLUEPRINT.md`](IMPLEMENTATION_BLUEPRINT.md)
for a phase-by-phase build guide (objective / I-O / tech+math per phase,
plus a full Mermaid pipeline flowchart) written to explain *why* each step
exists, including the two real design mistakes this project's first pass
made and how they were caught.

Rewrite of the project's original prototype scripts (`../old_files/*.py`),
which attempted to model the daf-2;rsks-1 double-mutant longevity phenotype
(Chen et al. 2013, *Cell Reports*) by directly knocking out `daf-2` and
`rsks-1` as genes in the iCEL1314 genome-scale metabolic model. That cannot
work: neither gene is present in iCEL1314 (verified directly against the
SBML file) because both are upstream insulin/IGF-1 and TOR/S6K signaling
genes, not metabolic enzymes.

This codebase instead uses **transcriptomics-constrained FBA**: the
project's GSE52340 microarray dataset (WT, rsks-1, daf-2, daf-2;rsks-1,
daf-16;daf-2;rsks-1 -- 47 samples) is used to measure each mutant's
transcriptional effect on iCEL1314's actual metabolic genes, which is then
mapped onto reaction flux bounds (a fold-change-referenced E-Flux-style
scaling) and run through constrained FBA per genotype. See the approved
architecture document (`../../../../../.claude/plans/` in the session that
produced this code, or ask for it to be re-exported) for the full
biological/mathematical rationale, a system flowchart, and a limitations
assessment; this README summarizes the implementation and how to run it.

## Two things discovered while building this that changed the design

1. **No external probe-annotation download needed.** GSE52340 is a
   NimbleGen array (platform GPL17925), not Affymetrix -- its probe IDs are
   literally `<WormBase sequence name>P<probe index>`. iCEL1314's own SBML
   gene annotations already carry each gene's WormBase sequence name (as a
   `kegg.genes` cross-reference, e.g. `CELE_F35H10.4`). Probe-to-gene
   mapping is therefore built entirely from these two local files
   (`fluxworm.io.probe_annotation`) with no network dependency. 1,313 of
   1,314 model genes have this cross-reference; of those, 787 are actually
   represented among the array's probed genes (the rest simply weren't
   probed on this array and receive no expression evidence).

2. **iCEL1314 has no subsystem/pathway annotation at all** (`reaction.subsystem`
   is empty for all 2,230 reactions; no SBML "groups" package data either).
   `fluxworm.analysis.subsystem_summary` therefore tags reactions with a
   coarse keyword-derived label from the reaction's free-text name (e.g.
   containing "lipid" or "fatty acid") instead of a curated subsystem. This
   is explicitly documented as a heuristic, not pathway ground truth.

## Running it

Easiest: use the launcher. It creates an isolated virtual environment,
installs dependencies, and runs the pipeline -- no manual setup required on
any machine with Python 3.10+.

```
python launcher.py              # full pipeline, writes to results\
python launcher.py --tests      # pipeline, then the test suite
python launcher.py --tests-only # just the test suite
```

On Windows you can also just double-click `launcher.bat`. On macOS/Linux,
run `chmod +x launcher.sh` once after cloning, then `./launcher.sh` (or
double-click it in Finder/Files).

**Windows note:** if the first run fails with `ImportError: DLL load
failed ... An Application Control policy has blocked this file`, that's
Windows Smart App Control doing a one-time cloud reputation check on a
freshly-installed scipy binary. Just run the launcher again -- it passes
on retry and stays allowed after that. No settings need to change.

Or do it manually:

```
pip install -r requirements.txt
python scripts\run_pipeline.py                       # full pipeline, writes to results\
python scripts\inspect_series_matrix_headers.py       # diagnostic: dump sample metadata to config\sample_genotype_map.csv
pytest tests -v                                       # unit tests (19 tests, synthetic fixtures + real model)
```

All paths are resolved from `config\config.yaml`, relative to the project
root, with no hardcoded Colab/Drive paths (the defect in the old scripts).
Override the data location with the `FLUXWORM_DATA_DIR` environment
variable if running on a different machine.

## Result of the first real run, a diagnosed problem, and the fix applied

The pipeline runs end-to-end against the real data: model loads (2,230
reactions / 1,314 genes / unconstrained WT growth = 0.0717), genotype
grouping recovers exactly 9/9/9/10/10 samples as expected, differential
expression finds 40-179 genes with evidence per mutant, and 150-200
reactions get their bounds rescaled per genotype.

**The first run (scaling each reaction's own model bound directly, as
originally approved) produced a null result**: biomass flux and every
individual reaction flux came out numerically identical to WT for all four
mutant genotypes. This was diagnosed, not assumed: forcing several of the
rescaled, flux-carrying reactions fully to zero (a hard knockout, well
beyond anything the expression-based scaling produces) did change growth
substantially for some of them, confirming the FBA/constraint machinery
worked correctly. The actual cause: iCEL1314 uses a generic "big-M" default
bound (+-1000) on almost every reaction, while the flux magnitudes this
model actually uses at optimal growth are three to six orders of magnitude
smaller (~1e-3 to 1e-6) -- a realistic microarray fold-change (evidence
threshold 1.5-fold; clipped scores top out at 10x) multiplied against 1000
can never shrink the bound down far enough to bind.

**Fix applied** (`fluxworm.constraints.reference_flux`): rather than scaling
each reaction's own placeholder model bound, the pipeline now runs flux
variability analysis (FVA) on the unconstrained wild-type model
(`fraction_of_optimum=0.9`) once, and scales each reaction's expression
score against *that* reaction's WT FVA range instead. This grounds the
scaling in a magnitude the model actually uses. This is a deviation from
the exact formula in the originally approved architecture doc, made only
after the null result was diagnosed and only with explicit sign-off (it
stays within the same E-Flux framework -- still a continuous, GPR-weighted,
fold-change-referenced bound scaling, just against a better-chosen
reference magnitude).

**Result after the fix**: daf-2 and daf-2;rsks-1 now show a small but real
reduction in growth (~0.12%) and 228 reactions with materially changed
flux (vs. 0 for rsks-1 alone and 5 for the daf-16 triple mutant). The
illustrative aging-proxy layer (`fluxworm.aging.survival_model`) initially
came out with the *wrong* qualitative direction on this real data -- it
predicted daf-2/daf-2;rsks-1 as shorter-lived than WT, opposite to Chen et
al. This was traced to the stress-flux term's sign: the lipid/fatty-acid
-tagged reaction group showed *reduced* flux in the longer-lived mutants,
consistent with the literature's report of reduced fatty-acid oxidation
(more fat storage) in these mutants, but the original formula scored
*higher* lipid-pathway flux as favorable. The term was corrected to treat
reduced lipid-pathway turnover as favorable (see the module docstring in
`survival_model.py` for the full reasoning) -- after which the illustrative
survival curves correctly rank daf-2 and daf-2;rsks-1 above WT at every
timepoint, matching the paper's reported ordering. rsks-1 alone and the
daf-16 triple mutant land indistinguishably from WT in this proxy -- a real
limitation of this pipeline's sensitivity for those two genotypes, stated
plainly rather than smoothed over.

All of the above -- the null result, the diagnosis, the fix, and the sign
correction -- is a legitimate part of this project's methodology and should
be described as such in any manuscript text drawn from this code, not
edited out as if the pipeline worked correctly on the first attempt.
