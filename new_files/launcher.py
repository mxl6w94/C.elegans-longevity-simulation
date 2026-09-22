#!/usr/bin/env python3
"""fluxworm launcher.

Sets up an isolated virtual environment, installs dependencies, and runs
the pipeline. Pure standard library -- works on any machine with Python
3.10+ installed (Windows, macOS, Linux), no prior setup required.

Usage:
    python launcher.py                 # run the full pipeline
    python launcher.py --tests         # run the pipeline, then the test suite
    python launcher.py --tests-only    # run only the test suite
    python launcher.py --no-venv       # use the current interpreter instead of a venv
    python launcher.py -- config\\my_config.yaml   # pass a custom config path through

On Windows you can also just double-click launcher.bat.
On macOS/Linux, double-click or run ./launcher.sh (after `chmod +x launcher.sh`).
"""

from __future__ import annotations

import argparse
import platform
import subprocess
import sys
import venv
from pathlib import Path

ROOT = Path(__file__).resolve().parent
VENV_DIR = ROOT / ".venv"
REQUIREMENTS = ROOT / "requirements.txt"
RUN_PIPELINE = ROOT / "scripts" / "run_pipeline.py"
TESTS_DIR = ROOT / "tests"

# Expected relative to the project root (one level above new_files/), per
# config\config.yaml's `data_dir: "../.."`. Only used for a friendly
# preflight warning -- the pipeline itself is the source of truth.
DATA_FILES = [
    ROOT.parent / "fluxworm_iCEL_models" / "iCEL1314.xml",
    ROOT.parent / "master_data_set" / "GSE52340_series_matrix.txt.gz",
]

MIN_PYTHON = (3, 10)


def venv_python(venv_dir: Path) -> Path:
    if platform.system() == "Windows":
        return venv_dir / "Scripts" / "python.exe"
    return venv_dir / "bin" / "python"


def check_python_version() -> None:
    if sys.version_info < MIN_PYTHON:
        got = ".".join(map(str, sys.version_info[:3]))
        want = ".".join(map(str, MIN_PYTHON))
        sys.exit(
            f"[launcher] Python {want}+ is required, found {got}. "
            "Install a newer Python from https://python.org and try again."
        )


def ensure_venv() -> Path:
    py = venv_python(VENV_DIR)
    if not py.exists():
        print(f"[launcher] creating virtual environment at {VENV_DIR}")
        venv.EnvBuilder(with_pip=True).create(VENV_DIR)
    return py


def check_data_files() -> None:
    missing = [p for p in DATA_FILES if not p.exists()]
    if missing:
        print("[launcher] WARNING: expected data file(s) not found:")
        for m in missing:
            print(f"    {m}")
        print(
            "[launcher] fluxworm_iCEL_models\\ and master_data_set\\ must sit next to "
            "new_files\\ (i.e. keep this folder's location relative to the project root "
            "intact), or set the FLUXWORM_DATA_DIR environment variable to point at the "
            "data location."
        )


def run(cmd: list[str]) -> None:
    print(f"[launcher] running: {' '.join(cmd)}")
    subprocess.run(cmd, check=True)


def main() -> None:
    parser = argparse.ArgumentParser(description="fluxworm launcher")
    parser.add_argument("--tests", action="store_true", help="also run the test suite after the pipeline")
    parser.add_argument("--tests-only", action="store_true", help="run only the test suite, skip the pipeline")
    parser.add_argument("--no-venv", action="store_true", help="use the current Python interpreter instead of creating a venv")
    parser.add_argument("pipeline_args", nargs="*", help="extra arguments passed through to run_pipeline.py (e.g. a config path)")
    args = parser.parse_args()

    check_python_version()

    py = Path(sys.executable) if args.no_venv else ensure_venv()

    print(f"[launcher] installing dependencies from {REQUIREMENTS.name}")
    run([str(py), "-m", "pip", "install", "-q", "--upgrade", "pip"])
    run([str(py), "-m", "pip", "install", "-q", "-r", str(REQUIREMENTS)])

    if not args.tests_only:
        check_data_files()
        run([str(py), str(RUN_PIPELINE), *args.pipeline_args])
        print(f"[launcher] done. Results written to {ROOT / 'results'}")

    if args.tests or args.tests_only:
        run([str(py), "-m", "pytest", str(TESTS_DIR), "-v"])


if __name__ == "__main__":
    try:
        main()
    except subprocess.CalledProcessError as exc:
        sys.exit(f"[launcher] command failed with exit code {exc.returncode}")
    except KeyboardInterrupt:
        sys.exit("[launcher] interrupted")
