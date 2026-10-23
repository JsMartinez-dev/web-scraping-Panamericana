"""Genera la relación entre precio y longitud de la descripción."""

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
    data[
        ["precio_cop", "longitud_descripcion", "categoria_principal"]
    ].to_csv(POWER_BI_DIR / "precio_vs_descripcion.csv", index=False)

    figure, axis = plt.subplots(figsize=(10, 6))
    for index, (category, group) in enumerate(
        data.groupby("categoria_principal")
    ):
        axis.scatter(
            group["longitud_descripcion"],
            group["precio_cop"],
            s=28,
            alpha=0.65,
            color=COLORS[index % len(COLORS)],
            label=category,
        )
    axis.set_title("Precio frente a longitud de la descripción")
    axis.set_xlabel("Longitud de la descripción (caracteres)")
    axis.set_ylabel("Precio (COP)")
    axis.ticklabel_format(style="plain", axis="y")
    axis.legend(title="Categoría", fontsize="small")
    apply_dashboard_style(axis)
    axis.grid(axis="both", color="#E4E9F2", linewidth=0.8)
    figure.tight_layout()
    figure.savefig(RESULTS_DIR / "04_precio_vs_descripcion.png", dpi=150)
    plt.close(figure)


if __name__ == "__main__":
    main()
