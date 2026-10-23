"""Genera la distribución de precios y su tabla para Power BI."""

import matplotlib.pyplot as plt

from analysis.common import (
    BACKGROUND,
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
    data[["precio_cop"]].to_csv(
        POWER_BI_DIR / "precios_para_power_bi.csv", index=False
    )

    figure, axis = plt.subplots(figsize=(10, 6))
    axis.hist(
        data["precio_cop"],
        bins=30,
        color=COLORS[0],
        edgecolor=BACKGROUND,
        alpha=0.9,
    )
    axis.set_title("Distribución de precios de productos")
    axis.set_xlabel("Precio (COP)")
    axis.set_ylabel("Cantidad de productos")
    axis.ticklabel_format(style="plain", axis="x")
    apply_dashboard_style(axis)
    figure.tight_layout()
    figure.savefig(RESULTS_DIR / "01_distribucion_precios.png", dpi=150)
    plt.close(figure)


if __name__ == "__main__":
    main()
