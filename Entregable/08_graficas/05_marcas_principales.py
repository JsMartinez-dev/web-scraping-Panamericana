"""Genera las marcas con más productos y su precio mediano."""

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
        data.groupby("marca", as_index=False)
        .agg(
            cantidad_productos=("precio_cop", "count"),
            precio_mediano=("precio_cop", "median"),
        )
        .sort_values(["cantidad_productos", "marca"], ascending=[False, True])
        .head(15)
        .sort_values("cantidad_productos")
    )
    summary.to_csv(POWER_BI_DIR / "marcas_principales.csv", index=False)

    figure, axis = plt.subplots(figsize=(10, 7))
    bars = axis.barh(
        summary["marca"],
        summary["cantidad_productos"],
        color=COLORS[4],
    )
    axis.set_title("Marcas con más productos en la muestra")
    axis.set_xlabel("Cantidad de productos")
    axis.set_ylabel("Marca")
    axis.bar_label(bars, padding=4, color="#1B2438")
    apply_dashboard_style(axis)
    figure.tight_layout()
    figure.savefig(RESULTS_DIR / "05_marcas_principales.png", dpi=150)
    plt.close(figure)


if __name__ == "__main__":
    main()
