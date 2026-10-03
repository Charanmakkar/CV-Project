"""Compile the IEEEtran preliminary report into the repository root."""

from __future__ import annotations

import shutil
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BUILD = ROOT / "docs" / ".latex-build"
STEM = "Computer_Vision_Autonomous_Patrol_Preliminary_Report"


def main() -> Path:
    if shutil.which("pdflatex") is None:
        raise RuntimeError("pdflatex was not found. Install a LaTeX distribution with IEEEtran.")
    BUILD.mkdir(parents=True, exist_ok=True)
    command = ["pdflatex", "-disable-installer", "-interaction=nonstopmode", "-halt-on-error",
               f"-output-directory={BUILD}", f"{STEM}.tex"]
    for pass_number in (1, 2):
        result = subprocess.run(command, cwd=ROOT, capture_output=True, text=True,
                                stdin=subprocess.DEVNULL, timeout=90)
        if result.returncode:
            log = BUILD / f"{STEM}.log"
            raise RuntimeError(f"LaTeX pass {pass_number} failed. Inspect {log}.\n"
                               f"{result.stdout[-1800:]}\n{result.stderr[-600:]}")
    output = ROOT / f"{STEM}.pdf"
    shutil.copyfile(BUILD / output.name, output)
    return output


if __name__ == "__main__":
    print(main())
