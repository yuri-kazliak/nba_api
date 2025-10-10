"""Helper scripts for project tooling."""

from __future__ import annotations

import subprocess
import sys


def run_checks() -> int:
    """Run Ruff, MyPy, and Pytest sequentially."""

    commands = [
        [sys.executable, "-m", "ruff", "format", "src", "tests"],
        [sys.executable, "-m", "ruff", "check", "src", "tests"],
        [sys.executable, "-m", "mypy", "src", "tests"],
        [sys.executable, "-m", "pytest"],
    ]

    for cmd in commands:
        result = subprocess.run(cmd, check=False)
        if result.returncode != 0:
            return result.returncode

    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(run_checks())
