"""Genera la comparación de precios entre categorías."""

import matplotlib.pyplot as plt

from analysis.common import (
    COLORS,
    POWER_BI_DIR,
    RESULTS_DIR,
    apply_dashboard_style,
    load_data,
    prepare_output_dirs,
)


def main() -> None:
    prepare_output_dirs()
    data = load_data()
    summary = (
        data.groupby("categoria_principal", as_index=False)["precio_cop"]
        .agg(
            cantidad_productos="count",
            precio_mediano="median",
            precio_promedio="mean",
            precio_minimo="min",
            precio_maximo="max",
        )
        .sort_values("precio_mediano", ascending=False)
    )
    summary.to_csv(POWER_BI_DIR / "resumen_precios_categoria.csv", index=False)

    ordered_categories = summary["categoria_principal"].tolist()
    values = [
        data.loc[data["categoria_principal"] == category, "precio_cop"]
        for category in ordered_categories
    ]
    figure, axis = plt.subplots(figsize=(12, 7))
    boxplot = axis.boxplot(
        values,
        tick_labels=ordered_categories,
        showfliers=False,
        patch_artist=True,
        medianprops={"color": "#1B2438", "linewidth": 2},
        whiskerprops={"color": "#5B6B86"},
        capprops={"color": "#5B6B86"},
    )
    for index, box in enumerate(boxplot["boxes"]):
        box.set_facecolor(COLORS[index % len(COLORS)])
        box.set_alpha(0.8)
    axis.set_title("Distribución de precios por categoría")
    axis.set_xlabel("Categoría")
    axis.set_ylabel("Precio (COP)")
    axis.tick_params(axis="x", rotation=35)
    axis.ticklabel_format(style="plain", axis="y")
    apply_dashboard_style(axis)
    figure.tight_layout()
    figure.savefig(RESULTS_DIR / "03_precios_por_categoria.png", dpi=150)
    plt.close(figure)


if __name__ == "__main__":
    main()
