"""Utilidades compartidas para las gráficas exploratorias."""

from pathlib import Path

import pandas as pd


COLORS = [
    "#0A7BFF",
    "#D97706",
    "#0E9F8E",
    "#E5484D",
    "#7C5CFA",
    "#A0522D",
    "#9AA3B2",
]
BACKGROUND = "#FFFFFF"
FOREGROUND = "#1B2438"
LABEL_COLOR = "#5B6B86"
GRID_COLOR = "#E4E9F2"

ROOT = Path(__file__).resolve().parents[1]
DATA_PATH = ROOT / "data" / "processed" / "panamericana_products_clean.csv"
RESULTS_DIR = ROOT / "results" / "figures"
POWER_BI_DIR = ROOT / "results" / "power_bi"


def load_data() -> pd.DataFrame:
    """Carga el dataset limpio con tipos explícitos."""
    return pd.read_csv(DATA_PATH, dtype={"sku": "string"})


def prepare_output_dirs() -> None:
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    POWER_BI_DIR.mkdir(parents=True, exist_ok=True)


def apply_dashboard_style(axis) -> None:
    """Aplica el tema visual común del Dashboard Panamericana."""
    axis.set_facecolor(BACKGROUND)
    axis.title.set_color(FOREGROUND)
    axis.xaxis.label.set_color(LABEL_COLOR)
    axis.yaxis.label.set_color(LABEL_COLOR)
    axis.tick_params(axis="both", colors=LABEL_COLOR)
    axis.grid(axis="y", color=GRID_COLOR, linewidth=0.8)
    axis.set_axisbelow(True)
    for spine in axis.spines.values():
        spine.set_visible(False)
