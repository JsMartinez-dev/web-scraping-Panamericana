"""Ejecuta todas las gráficas exploratorias."""

import runpy
import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
SCRIPTS_DIR = Path(__file__).parent / "graficas"
SCRIPTS = sorted(SCRIPTS_DIR.glob("[0-9][0-9]_*.py"))


def main() -> None:
    sys.path.insert(0, str(PROJECT_ROOT))
    for script in SCRIPTS:
        runpy.run_path(str(script), run_name="__main__")


if __name__ == "__main__":
    main()
