"""Diagnostic: dump the raw GSE52340 !Sample_* header fields to a CSV for
human review. This is how the exact genotype label text used by
`fluxworm.genotype.sample_mapping` ("wild type", "rsks-1", "daf-2",
"daf-2 rsks-1", "daf-16; daf-2 rsks-1") was originally confirmed -- it
cannot be guessed from the truncated old project code, which never reached
this parsing step.

Usage: python scripts\\inspect_series_matrix_headers.py [path/to/config.yaml]
"""

from __future__ import annotations

import sys
from pathlib import Path

_SRC = Path(__file__).resolve().parents[1] / "src"
sys.path.insert(0, str(_SRC))

from fluxworm.config import load_config  # noqa: E402
from fluxworm.io.microarray_parser import parse_sample_headers  # noqa: E402

if __name__ == "__main__":
    default_config = Path(__file__).resolve().parents[1] / "config" / "config.yaml"
    config_path = sys.argv[1] if len(sys.argv) > 1 else default_config
    config = load_config(config_path)

    headers = parse_sample_headers(config.series_matrix)
    out_path = Path(__file__).resolve().parents[1] / "config" / "sample_genotype_map.csv"
    headers.to_csv(out_path)
    print(f"Wrote {len(headers)} sample rows to {out_path}")
    if "characteristics_genotype" in headers.columns:
        print(headers["characteristics_genotype"].value_counts())
