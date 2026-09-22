"""Parses the GSE52340 GEO series-matrix file (NimbleGen microarray, GPL17925).

Two things live in this one gzip file and must be parsed differently:

1. Sample metadata: lines beginning with "!Sample_..." -- one field per line,
   one value per sample (47 tab-separated, quoted values). This is where
   genotype-per-sample lives and it is NOT reachable via a plain
   ``pandas.read_csv(..., comment="!")`` call, because that call is exactly
   what discards these lines. The old project code
   (old_files/fluxworm_flux_balance_analysis.py) read the expression table
   this way and never went back to parse the metadata rows -- the genotype
   grouping was never implemented. This module's `parse_sample_headers`
   fills that gap.

2. The expression matrix itself: a probe-by-sample table of already
   log2-scale, presumably quantile/RMA-normalized NimbleGen intensities
   (values in the 6-14 range in this file), delimited by
   "!series_matrix_table_begin" / "!series_matrix_table_end" markers.

Row IDs in the expression matrix (e.g. "2L52.1P00168") are NimbleGen probe
IDs of the form ``<WormBase sequence name><P><probe index>`` -- see
`fluxworm.io.probe_annotation` for how these are matched back to iCEL1314
gene IDs without needing any external platform annotation download.
"""

from __future__ import annotations

import csv
import gzip
from pathlib import Path

import pandas as pd

_SAMPLE_PREFIX = "!Sample_"
_TABLE_BEGIN = "!series_matrix_table_begin"
_TABLE_END = "!series_matrix_table_end"


def parse_sample_headers(series_matrix_path: str | Path) -> pd.DataFrame:
    """Return a DataFrame indexed by GSM accession with one column per
    "!Sample_*" metadata field. Repeated "!Sample_characteristics_ch1" rows
    (GEO allows several, one per characteristic dimension) are split into
    separate columns named "characteristics_<key>", where <key> is parsed
    from the common "key: value" text of that row (e.g. "genotype",
    "phenotype", "genetic background").
    """
    series_matrix_path = Path(series_matrix_path)
    rows: dict[str, list[str]] = {}
    characteristics_rows: list[list[str]] = []

    with gzip.open(series_matrix_path, "rt", encoding="latin-1") as f:
        for line in f:
            if not line.startswith(_SAMPLE_PREFIX):
                continue
            fields = next(csv.reader([line], delimiter="\t"))
            field_name, values = fields[0], fields[1:]
            if field_name == "!Sample_characteristics_ch1":
                characteristics_rows.append(values)
            else:
                rows[field_name.lstrip("!")] = values

    n_samples = len(rows["Sample_geo_accession"])

    for values in characteristics_rows:
        if len(values) != n_samples:
            raise ValueError("A !Sample_characteristics_ch1 row has a different length than the sample count")
        keys = {v.split(":", 1)[0].strip() for v in values}
        if len(keys) != 1:
            raise ValueError(f"Expected one characteristic key per row, found {keys}")
        key = next(iter(keys)).lower().replace(" ", "_")
        rows[f"characteristics_{key}"] = [v.split(":", 1)[1].strip() for v in values]

    df = pd.DataFrame(rows)
    df = df.set_index("Sample_geo_accession")
    df.index.name = "geo_accession"
    return df


def parse_expression_matrix(series_matrix_path: str | Path) -> pd.DataFrame:
    """Return the probe x sample expression matrix (probes as rows, GSM
    accessions as columns), read directly from between the
    series_matrix_table_begin/end markers.
    """
    series_matrix_path = Path(series_matrix_path)
    with gzip.open(series_matrix_path, "rt", encoding="latin-1") as f:
        lines = []
        in_table = False
        for line in f:
            if line.startswith(_TABLE_BEGIN):
                in_table = True
                continue
            if line.startswith(_TABLE_END):
                break
            if in_table:
                lines.append(line)

    from io import StringIO

    df = pd.read_csv(StringIO("".join(lines)), sep="\t", index_col=0)
    df.index.name = "probe_id"
    return df
