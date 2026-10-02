"""CLI entry point: python scripts\\run_pipeline.py [path/to/config.yaml]

Adds ../src to sys.path so this runs without requiring `pip install -e .`.
"""

from __future__ import annotations

import sys
from pathlib import Path

_SRC = Path(__file__).resolve().parents[1] / "src"
sys.path.insert(0, str(_SRC))

from fluxworm.pipeline import main  # noqa: E402

if __name__ == "__main__":
    default_config = Path(__file__).resolve().parents[1] / "config" / "config.yaml"
    config_path = sys.argv[1] if len(sys.argv) > 1 else default_config
    main(config_path)
