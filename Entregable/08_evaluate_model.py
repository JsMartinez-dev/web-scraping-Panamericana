"""Genera métricas, tablas y gráficas de evaluación del modelo."""

from __future__ import annotations

import json
from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
MODEL_RESULTS = ROOT / "results" / "modeling"
FIGURES_DIR = ROOT / "results" / "evaluation"
POWER_BI_DIR = ROOT / "results" / "power_bi"

COLORS = ["#0A7BFF", "#D97706", "#0E9F8E", "#E5484D"]
BACKGROUND = "#FFFFFF"
FOREGROUND = "#1B2438"
LABEL_COLOR = "#5B6B86"
GRID_COLOR = "#E4E9F2"


def style_axis(axis) -> None:
    axis.set_facecolor(BACKGROUND)
    axis.title.set_color(FOREGROUND)
    axis.xaxis.label.set_color(LABEL_COLOR)
    axis.yaxis.label.set_color(LABEL_COLOR)
    axis.tick_params(axis="both", colors=LABEL_COLOR)
    axis.grid(color=GRID_COLOR, linewidth=0.8)
    axis.set_axisbelow(True)
    for spine in axis.spines.values():
        spine.set_visible(False)


def main() -> None:
    predictions = pd.read_csv(MODEL_RESULTS / "test_predictions.csv")
    metrics = json.loads(
        (MODEL_RESULTS / "metrics.json").read_text(encoding="utf-8")
    )
    predictions["error_firmado"] = (
        predictions["precio_real"] - predictions["precio_predicho"]
    )
    predictions["error_porcentual"] = (
        predictions["error_firmado"] / predictions["precio_real"] * 100
    )
    predictions["acierto_modelo"] = predictions["error_absoluto"] <= metrics["mae"]

    FIGURES_DIR.mkdir(parents=True, exist_ok=True)
    POWER_BI_DIR.mkdir(parents=True, exist_ok=True)
    predictions.to_csv(
        POWER_BI_DIR / "predicciones_evaluacion.csv",
        index=False,
        encoding="utf-8",
    )
    pd.DataFrame(
        {
            "modelo": ["Línea base", "Random Forest"],
            "mae": [metrics["baseline_mae"], metrics["mae"]],
            "rmse": [metrics["baseline_rmse"], metrics["rmse"]],
            "r2": [metrics["baseline_r2"], metrics["r2"]],
        }
    ).to_csv(
        POWER_BI_DIR / "comparacion_modelos.csv",
        index=False,
        encoding="utf-8",
    )

    figure, axis = plt.subplots(figsize=(8, 7), facecolor=BACKGROUND)
    axis.scatter(
        predictions["precio_real"],
        predictions["precio_predicho"],
        color=COLORS[0],
        alpha=0.7,
        edgecolors=BACKGROUND,
    )
    limits = [
        min(predictions["precio_real"].min(), predictions["precio_predicho"].min()),
        max(predictions["precio_real"].max(), predictions["precio_predicho"].max()),
    ]
    axis.plot(limits, limits, "--", color=COLORS[3], label="Predicción perfecta")
    axis.set_title("Precios reales frente a precios predichos")
    axis.set_xlabel("Precio real (COP)")
    axis.set_ylabel("Precio predicho (COP)")
    axis.ticklabel_format(style="plain")
    axis.legend()
    style_axis(axis)
    figure.tight_layout()
    figure.savefig(FIGURES_DIR / "01_reales_vs_predichos.png", dpi=150)
    plt.close(figure)

    figure, axis = plt.subplots(figsize=(10, 6), facecolor=BACKGROUND)
    axis.hist(
        predictions["error_firmado"],
        bins=25,
        color=COLORS[1],
        edgecolor=BACKGROUND,
    )
    axis.axvline(0, color=FOREGROUND, linewidth=1.5)
    axis.set_title("Distribución de errores de predicción")
    axis.set_xlabel("Error firmado: real - predicho (COP)")
    axis.set_ylabel("Cantidad de productos")
    axis.ticklabel_format(style="plain", axis="x")
    style_axis(axis)
    figure.tight_layout()
    figure.savefig(FIGURES_DIR / "02_distribucion_errores.png", dpi=150)
    plt.close(figure)

    worst = predictions.nlargest(15, "error_absoluto").sort_values("error_absoluto")
    figure, axis = plt.subplots(figsize=(10, 7), facecolor=BACKGROUND)
    axis.barh(
        worst["nombre"].str.slice(0, 35),
        worst["error_absoluto"],
        color=COLORS[3],
    )
    axis.set_title("Mayores errores absolutos")
    axis.set_xlabel("Error absoluto (COP)")
    axis.set_ylabel("Producto")
    axis.ticklabel_format(style="plain", axis="x")
    style_axis(axis)
    figure.tight_layout()
    figure.savefig(FIGURES_DIR / "03_mayores_errores.png", dpi=150)
    plt.close(figure)

    importances = pd.read_csv(MODEL_RESULTS / "feature_importances.csv")
    top_importances = importances.head(15).sort_values("importancia")
    figure, axis = plt.subplots(figsize=(10, 7), facecolor=BACKGROUND)
    axis.barh(
        top_importances["variable"],
        top_importances["importancia"],
        color=COLORS[2],
    )
    axis.set_title("Variables más importantes del modelo")
    axis.set_xlabel("Importancia")
    axis.set_ylabel("Variable")
    style_axis(axis)
    figure.tight_layout()
    figure.savefig(FIGURES_DIR / "04_importancia_variables.png", dpi=150)
    plt.close(figure)

    print(f"Predicciones evaluadas: {len(predictions)}")
    print(f"Gráficas generadas en: {FIGURES_DIR}")


if __name__ == "__main__":
    main()
