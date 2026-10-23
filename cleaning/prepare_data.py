"""Limpia el dataset extraído y genera artefactos reproducibles."""

from __future__ import annotations

import json
from pathlib import Path

import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
RAW_PATH = ROOT / "data" / "raw" / "panamericana_products.csv"
PROCESSED_DIR = ROOT / "data" / "processed"
OUTPUT_PATH = PROCESSED_DIR / "panamericana_products_clean.csv"
QUALITY_PATH = PROCESSED_DIR / "quality_report.json"
DICTIONARY_PATH = PROCESSED_DIR / "data_dictionary.csv"

REQUIRED_COLUMNS = {
    "url",
    "nombre",
    "marca",
    "categoria_principal",
    "subcategoria",
    "ruta_categoria",
    "sku",
    "precio_cop",
    "disponibilidad",
    "longitud_descripcion",
    "fecha_extraccion",
}


def normalize_text(value: object) -> str:
    """Convierte texto nulo a cadena vacía y elimina espacios sobrantes."""
    return " ".join(str(value).split()) if pd.notna(value) else ""


def build_quality_report(
    raw: pd.DataFrame,
    clean: pd.DataFrame,
    removed_invalid_price: int,
    removed_duplicates: int,
) -> dict[str, object]:
    """Construye un reporte de calidad antes y después de la limpieza."""
    return {
        "filas_originales": int(len(raw)),
        "filas_finales": int(len(clean)),
        "filas_eliminadas": int(len(raw) - len(clean)),
        "filas_eliminadas_precio_invalido": removed_invalid_price,
        "filas_eliminadas_duplicadas": removed_duplicates,
        "columnas_finales": list(clean.columns),
        "nulos_por_columna": {
            column: int(value) for column, value in clean.isna().sum().items()
        },
        "urls_unicas": int(clean["url"].nunique()),
        "skus_unicos": int(clean["sku"].nunique()),
        "categorias": {
            str(key): int(value)
            for key, value in clean["categoria_principal"].value_counts().items()
        },
        "precio_cop": {
            "minimo": int(clean["precio_cop"].min()),
            "mediana": float(clean["precio_cop"].median()),
            "promedio": float(clean["precio_cop"].mean()),
            "maximo": int(clean["precio_cop"].max()),
        },
    }


def create_data_dictionary() -> pd.DataFrame:
    """Describe las columnas del dataset procesado."""
    rows = [
        ("url", "texto", "URL pública del producto; identificador, no predictor."),
        ("nombre", "texto", "Nombre publicado del producto."),
        ("marca", "categórica", "Marca publicada del producto."),
        ("categoria_principal", "categórica", "Primera categoría del breadcrumb."),
        ("subcategoria", "categórica", "Última subcategoría del breadcrumb."),
        ("ruta_categoria", "texto", "Jerarquía completa de categorías."),
        ("sku", "texto", "Código del producto conservado como texto."),
        ("precio_cop", "entero", "Variable objetivo: precio en pesos colombianos."),
        ("disponibilidad", "categórica", "Estado de disponibilidad publicado."),
        ("longitud_descripcion", "entero", "Cantidad de caracteres de la descripción."),
        ("fecha_extraccion", "fecha", "Fecha en que se obtuvo el registro."),
        ("longitud_nombre", "entero", "Cantidad de caracteres del nombre."),
        ("palabras_nombre", "entero", "Cantidad de palabras del nombre."),
    ]
    return pd.DataFrame(rows, columns=["columna", "tipo", "descripcion"])


def prepare_dataset() -> None:
    if not RAW_PATH.exists():
        raise FileNotFoundError(f"No existe el dataset original: {RAW_PATH}")

    raw = pd.read_csv(RAW_PATH, dtype={"sku": "string"})
    missing_columns = REQUIRED_COLUMNS - set(raw.columns)
    if missing_columns:
        raise ValueError(f"Faltan columnas obligatorias: {sorted(missing_columns)}")

    clean = raw.copy()
    text_columns = [
        "url",
        "nombre",
        "marca",
        "categoria_principal",
        "subcategoria",
        "ruta_categoria",
        "disponibilidad",
    ]
    for column in text_columns:
        clean[column] = clean[column].map(normalize_text)

    clean["sku"] = clean["sku"].astype("string").str.strip().str.zfill(8)
    clean["precio_cop"] = pd.to_numeric(clean["precio_cop"], errors="coerce")
    clean["longitud_descripcion"] = pd.to_numeric(
        clean["longitud_descripcion"], errors="coerce"
    )
    clean["fecha_extraccion"] = pd.to_datetime(
        clean["fecha_extraccion"], errors="coerce"
    )

    required_for_model = [
        "nombre",
        "marca",
        "categoria_principal",
        "subcategoria",
        "sku",
        "precio_cop",
    ]
    
    invalid_required = clean[required_for_model].eq("").any(axis=1)
    invalid_required |= clean[required_for_model].isna().any(axis=1)
    invalid_price = clean["precio_cop"].isna() | (clean["precio_cop"] <= 0)
    removed_invalid_price = int((invalid_required | invalid_price).sum())
    clean = clean.loc[~(invalid_required | invalid_price)].copy()

    before_duplicates = len(clean)
    clean = clean.drop_duplicates(subset=["url"], keep="first")
    clean = clean.drop_duplicates(subset=["sku"], keep="first")
    removed_duplicates = int(before_duplicates - len(clean))

    clean["precio_cop"] = clean["precio_cop"].astype("int64")
    clean["longitud_descripcion"] = clean["longitud_descripcion"].astype("int64")
    clean["longitud_nombre"] = clean["nombre"].str.len().astype("int64")
    clean["palabras_nombre"] = clean["nombre"].str.split().str.len().astype("int64")
    clean["fecha_extraccion"] = clean["fecha_extraccion"].dt.strftime("%Y-%m-%d")

    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    clean.to_csv(OUTPUT_PATH, index=False, encoding="utf-8")
    QUALITY_PATH.write_text(
        json.dumps(
            build_quality_report(
                raw, clean, removed_invalid_price, removed_duplicates
            ),
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )
    create_data_dictionary().to_csv(
        DICTIONARY_PATH, index=False, encoding="utf-8"
    )

    print(f"Dataset limpio: {len(clean)} filas")
    print(f"Archivo: {OUTPUT_PATH}")
    print(f"Reporte: {QUALITY_PATH}")
    print(f"Diccionario: {DICTIONARY_PATH}")


if __name__ == "__main__":
    prepare_dataset()
