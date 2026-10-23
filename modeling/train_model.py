"""Entrena y evalúa un modelo de regresión para el precio de productos."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import joblib
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import RandomForestRegressor
from sklearn.impute import SimpleImputer
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder


ROOT = Path(__file__).resolve().parents[1]
DATA_PATH = ROOT / "data" / "processed" / "panamericana_products_clean.csv"
RESULTS_DIR = ROOT / "results" / "modeling"
MODEL_PATH = RESULTS_DIR / "random_forest_price_pipeline.joblib"
METRICS_PATH = RESULTS_DIR / "metrics.json"
PREDICTIONS_PATH = RESULTS_DIR / "test_predictions.csv"
IMPORTANCES_PATH = RESULTS_DIR / "feature_importances.csv"

TARGET = "precio_cop"
CATEGORICAL_FEATURES = [
    "marca",
    "categoria_principal",
    "subcategoria",
    "disponibilidad",
]
NUMERIC_FEATURES = [
    "longitud_descripcion",
    "longitud_nombre",
    "palabras_nombre",
]
FEATURES = CATEGORICAL_FEATURES + NUMERIC_FEATURES


def build_pipeline(
    n_estimators: int,
    max_depth: int | None,
    min_samples_leaf: int,
    max_features: int | float | str | None,
    random_state: int,
) -> Pipeline:
    categorical_pipeline = Pipeline(
        steps=[
            ("imputer", SimpleImputer(strategy="most_frequent")),
            (
                "one_hot",
                OneHotEncoder(handle_unknown="ignore", sparse_output=True),
            ),
        ]
    )
    numeric_pipeline = Pipeline(
        steps=[("imputer", SimpleImputer(strategy="median"))]
    )
    preprocessor = ColumnTransformer(
        transformers=[
            ("categorical", categorical_pipeline, CATEGORICAL_FEATURES),
            ("numeric", numeric_pipeline, NUMERIC_FEATURES),
        ]
    )
    model = RandomForestRegressor(
        n_estimators=n_estimators,
        max_depth=max_depth,
        min_samples_leaf=min_samples_leaf,
        max_features=max_features,
        random_state=random_state,
        n_jobs=-1,
    )
    return Pipeline(
        steps=[("preprocessor", preprocessor), ("model", model)]
    )


def calculate_metrics(
    actual: pd.Series, predicted: pd.Series, baseline: pd.Series
) -> dict[str, float]:
    return {
        "mae": float(mean_absolute_error(actual, predicted)),
        "rmse": float(mean_squared_error(actual, predicted) ** 0.5),
        "r2": float(r2_score(actual, predicted)),
        "baseline_mae": float(mean_absolute_error(actual, baseline)),
        "baseline_rmse": float(mean_squared_error(actual, baseline) ** 0.5),
        "baseline_r2": float(r2_score(actual, baseline)),
    }


def parse_max_features(value: str) -> int | float | str | None:
    """Convierte max_features desde texto al tipo aceptado por sklearn."""
    normalized = value.strip().lower()
    if normalized == "none":
        return None
    if normalized in {"sqrt", "log2"}:
        return normalized
    try:
        number = float(normalized)
    except ValueError as error:
        raise argparse.ArgumentTypeError(
            "max_features debe ser none, sqrt, log2, un entero o un decimal."
        ) from error
    if number <= 0:
        raise argparse.ArgumentTypeError("max_features debe ser mayor que cero.")
    return int(number) if number.is_integer() else number


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Entrena Random Forest y guarda sus métricas y predicciones."
    )
    parser.add_argument(
        "--n-estimators",
        type=int,
        default=300,
        help="Cantidad de árboles (predeterminado: 300).",
    )
    parser.add_argument(
        "--max-depth",
        type=int,
        default=12,
        help="Profundidad máxima; usa 0 para dejarla ilimitada.",
    )
    parser.add_argument(
        "--min-samples-leaf",
        type=int,
        default=2,
        help="Mínimo de registros en cada hoja (predeterminado: 2).",
    )
    parser.add_argument(
        "--max-features",
        type=parse_max_features,
        default="sqrt",
        help="Variables por división: sqrt, log2, none, entero o decimal.",
    )
    parser.add_argument(
        "--test-size",
        type=float,
        default=0.2,
        help="Proporción del conjunto de prueba (predeterminado: 0.2).",
    )
    parser.add_argument(
        "--random-state",
        type=int,
        default=42,
        help="Semilla para reproducibilidad (predeterminado: 42).",
    )
    args = parser.parse_args()
    if args.n_estimators < 1:
        parser.error("--n-estimators debe ser mayor que cero.")
    if args.max_depth is not None and args.max_depth < 0:
        parser.error("--max-depth no puede ser negativo.")
    if args.min_samples_leaf < 1:
        parser.error("--min-samples-leaf debe ser mayor que cero.")
    if not 0 < args.test_size < 1:
        parser.error("--test-size debe estar entre 0 y 1.")
    if args.max_depth == 0:
        args.max_depth = None
    return args


def main() -> None:
    args = parse_args()
    data = pd.read_csv(DATA_PATH, dtype={"sku": "string"})
    missing = set(FEATURES + [TARGET]) - set(data.columns)
    if missing:
        raise ValueError(f"Faltan columnas requeridas: {sorted(missing)}")

    data = data[["nombre"] + FEATURES + [TARGET]].dropna().copy()
    X = data[FEATURES]
    y = data[TARGET].astype(float)
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=args.test_size, random_state=args.random_state
    )

    pipeline = build_pipeline(
        n_estimators=args.n_estimators,
        max_depth=args.max_depth,
        min_samples_leaf=args.min_samples_leaf,
        max_features=args.max_features,
        random_state=args.random_state,
    )
    pipeline.fit(X_train, y_train)
    predictions = pipeline.predict(X_test)
    baseline_predictions = pd.Series(
        y_train.median(), index=y_test.index, dtype=float
    )
    metrics = calculate_metrics(
        y_test,
        pd.Series(predictions, index=y_test.index),
        baseline_predictions,
    )
    metrics.update(
        {
            "registros_totales": int(len(data)),
            "registros_entrenamiento": int(len(X_train)),
            "registros_prueba": int(len(X_test)),
            "modelo": "RandomForestRegressor",
            "semilla": args.random_state,
            "hiperparametros": {
                "n_estimators": args.n_estimators,
                "max_depth": args.max_depth,
                "min_samples_leaf": args.min_samples_leaf,
                "max_features": args.max_features,
                "test_size": args.test_size,
            },
            "variables_predictoras": FEATURES,
            "variable_objetivo": TARGET,
        }
    )

    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    joblib.dump(pipeline, MODEL_PATH)
    METRICS_PATH.write_text(
        json.dumps(metrics, ensure_ascii=False, indent=2), encoding="utf-8"
    )

    prediction_table = X_test.copy()
    prediction_table.insert(
        0,
        "nombre",
        data.loc[X_test.index, "nombre"],
    )
    prediction_table["precio_real"] = y_test
    prediction_table["precio_predicho"] = predictions
    prediction_table["error_absoluto"] = (
        prediction_table["precio_real"] - prediction_table["precio_predicho"]
    ).abs()
    prediction_table.to_csv(PREDICTIONS_PATH, index=False, encoding="utf-8")

    preprocessor = pipeline.named_steps["preprocessor"]
    model = pipeline.named_steps["model"]
    feature_names = preprocessor.get_feature_names_out()
    pd.DataFrame(
        {"variable": feature_names, "importancia": model.feature_importances_}
    ).sort_values("importancia", ascending=False).to_csv(
        IMPORTANCES_PATH, index=False, encoding="utf-8"
    )

    print(json.dumps(metrics, ensure_ascii=False, indent=2))
    print(f"Modelo: {MODEL_PATH}")
    print(f"Predicciones: {PREDICTIONS_PATH}")


if __name__ == "__main__":
    main()
