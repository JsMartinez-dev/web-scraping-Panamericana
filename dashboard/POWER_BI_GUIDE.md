# Informe de Power BI: Dashboard Panamericana

## Carga de tablas

Desde **Obtener datos > Texto/CSV**, carga estas tablas:

| Nombre recomendado | Archivo |
|---|---|
| `Productos` | `data/processed/panamericana_products_clean.csv` |
| `Predicciones` | `results/power_bi/predicciones_evaluacion.csv` |
| `ComparacionModelos` | `results/power_bi/comparacion_modelos.csv` |
| `ImportanciaVariables` | `results/modeling/feature_importances.csv` |

Las tablas de `productos_por_categoria.csv`, `resumen_precios_categoria.csv`,
`marcas_principales.csv`, `precio_vs_descripcion.csv` y
`precios_para_power_bi.csv` son resúmenes opcionales. No es necesario
cargarlas si los visuales se construyen directamente con `Productos`.

## Tema

Importa `Dashboard Panamericana.json` desde:

**Vista > Temas > Examinar temas**

El tema usa fondo de página `#F0F3F8`, tarjetas blancas, texto `#1B2438`
y la paleta azul, naranja, turquesa, rojo, morado, marrón y gris definida
en el archivo JSON.

## Página 1: resumen comercial

Usa la tabla `Productos`.

- Tarjeta: `Total productos`.
- Tarjeta: `Precio mediano`.
- Tarjeta: `Precio promedio`.
- Tarjeta: `Precio máximo`.
- Barras: `categoria_principal` y `Total productos`.
- Columnas: `categoria_principal` y `Precio mediano`.
- Segmentadores: `categoria_principal`, `subcategoria`, `marca`,
  `disponibilidad`.

## Página 2: precios y catálogo

Usa la tabla `Productos`.

- Histograma o columnas por intervalos: `precio_cop`.
- Dispersión: eje X `longitud_descripcion`, eje Y `precio_cop`,
  leyenda `categoria_principal`.
- Barras: `marca` y `Total productos`; aplicar filtro Top 15.
- Tabla de detalle: `nombre`, `marca`, `categoria_principal`,
  `precio_cop`, `disponibilidad`.

## Página 3: evaluación del modelo

Usa `Predicciones`, `ComparacionModelos` e `ImportanciaVariables`.

- Dispersión: eje X `precio_real`, eje Y `precio_predicho`.
- Columnas: eje `modelo`, valores `mae`, `rmse` o `r2`.
- Barras: `variable` y `importancia`, orden descendente.
- Tabla de errores: `nombre`, `precio_real`, `precio_predicho`,
  `error_absoluto`, `error_porcentual`.
- Tarjeta: `Error absoluto promedio`.

## Relaciones

No es necesario crear relaciones para el diseño inicial: `Productos` se usa
en las páginas descriptivas y `Predicciones` en la página de evaluación.
Las tablas resumen son independientes y pueden omitirse.

## Actualización reproducible

Desde la carpeta `scraping`, ejecuta:

```powershell
..\.venv\Scripts\python.exe cleaning\prepare_data.py
..\.venv\Scripts\python.exe analysis\run_eda.py
..\.venv\Scripts\python.exe modeling\train_model.py
..\.venv\Scripts\python.exe evaluation\evaluate_model.py
```

Después, en Power BI selecciona **Actualizar**. El archivo `.pbix` debe
guardarse fuera de las carpetas de datos generados y entregarse junto con
este proyecto.
