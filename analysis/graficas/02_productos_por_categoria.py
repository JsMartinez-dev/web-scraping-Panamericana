"""Genera el conteo de productos por categoría."""

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
        data["categoria_principal"]
        .value_counts()
        .rename_axis("categoria_principal")
        .reset_index(name="cantidad_productos")
    )
    summary.to_csv(POWER_BI_DIR / "productos_por_categoria.csv", index=False)

    plot_data = summary.sort_values("cantidad_productos")
    figure, axis = plt.subplots(figsize=(10, 6))
    bars = axis.barh(
        plot_data["categoria_principal"],
        plot_data["cantidad_productos"],
        color=COLORS[2],
    )
    axis.set_title("Cantidad de productos por categoría")
    axis.set_xlabel("Cantidad de productos")
    axis.set_ylabel("Categoría")
    axis.bar_label(bars, padding=4, color="#1B2438")
    apply_dashboard_style(axis)
    figure.tight_layout()
    figure.savefig(RESULTS_DIR / "02_productos_por_categoria.png", dpi=150)
    plt.close(figure)


if __name__ == "__main__":
    main()
