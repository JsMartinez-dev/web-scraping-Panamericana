# Guion de presentación: análisis de productos de Panamericana

## 1. Presentación general del proyecto

### Qué decir

> Mi proyecto aplica un flujo completo de ciencia de datos sobre productos
> publicados en la tienda web de Panamericana Colombia. El proceso comienza
> con web scraping, continúa con la limpieza y el análisis exploratorio, y
> termina con un modelo de regresión que predice el precio de un producto.
> Los resultados se presentan en un informe interactivo de Power BI.

El problema predictivo es:

> Predecir el precio de un producto de Panamericana usando información pública
> como marca, categoría, subcategoría, disponibilidad y características
> textuales del producto.

- Tipo de problema: **regresión supervisada**.
- Variable objetivo: `precio_cop`.
- Fuente: [Panamericana](https://www.panamericana.com.co/).
- Registros extraídos y válidos: **388**.
- Registros de entrenamiento: **310**.
- Registros de prueba: **78**.

La variable objetivo es numérica y representa un precio en pesos colombianos,
por eso no se trata de clasificación. Una clasificación respondería preguntas
como “¿pertenece a tecnología?”, mientras que aquí se estima un número.

---

## 2. Archivos que se entregan

| Archivo | Función |
|---|---|
| `01_panamericana_products.csv` | Datos originales extraídos del sitio |
| `02_panamericana_products_clean.csv` | Datos limpios utilizados por el modelo |
| `03_predicciones_evaluacion_random_forest.csv` | Precios reales, predichos y errores |
| `04_extract_panamericana.py` | Código de web scraping |
| `05_prepare_data.py` | Código de limpieza y preparación |
| `06_metrics.json` | Métricas y configuración del modelo |
| `07_train_model.py` | Código de entrenamiento y evaluación |
| `08_evaluate_model.py` | Código de gráficas y tablas de evaluación |
| `08_graficas/` | Scripts de gráficas exploratorias |
| `10_Archivo_powerbi_Panamericana_Juan_Martinez.pbix` | Informe interactivo |
| `09_GUION_PRESENTACION.md` | Este guion |

El archivo `03_predicciones_evaluacion_random_forest.csv` tiene 78 filas de
prueba más el encabezado. Los dos archivos de productos tienen 388 filas más
el encabezado.

---

## 3. Web scraping

### Qué decir

> Elegí Panamericana porque es un sitio real de comercio electrónico, tiene
> páginas públicas de productos, un sitemap de productos y datos útiles como
> nombre, marca, categoría, precio y disponibilidad. La extracción se hizo
> únicamente sobre páginas públicas y no utilizó autenticación, CAPTCHA,
> carrito, checkout ni API privada.

El archivo responsable es:

`04_extract_panamericana.py`

### Funciones del scraper

#### `get_product_urls(session, sitemap_url, limit)`

Lee un sitemap individual y devuelve una lista de URLs de productos.

Pasos:

1. Realiza una solicitud HTTP con `session.get`.
2. Aplica un tiempo máximo de espera.
3. Comprueba errores HTTP con `raise_for_status`.
4. Interpreta el XML con `ElementTree`.
5. Busca las etiquetas `loc`.
6. Verifica que las URLs sean HTTP o HTTPS.
7. Evita duplicados mediante un conjunto `set`.
8. Respeta el límite solicitado.

#### `get_product_sitemap_urls(session, sitemap_index_url)`

Lee el índice general `sitemap.xml` y localiza los sitemaps cuyo nombre
corresponde a productos. Esto permite no depender exclusivamente de
`product-0.xml`.

#### `get_urls_from_source(session, source_url, limit)`

Decide si la fuente recibida es un sitemap individual o el índice general.
Luego combina los sitemaps de productos hasta alcanzar el límite de URLs.

#### `first_json_ld_product(soup)`

Busca en el HTML los bloques:

```html
<script type="application/ld+json">
```

Después:

1. Convierte el contenido JSON a un diccionario.
2. Ignora bloques JSON inválidos y registra una advertencia.
3. Revisa el campo `@type`.
4. Devuelve el primer objeto cuyo tipo sea `Product`.

El uso de JSON-LD es más estable que depender solamente de clases visuales
que pueden cambiar en el diseño de la página.

#### `extract_categories(soup)`

Busca el breadcrumb de producto mediante:

```css
[class*="product__breadcrumb"]
```

Extrae los enlaces de la ruta y obtiene:

- `categoria_principal`: primera categoría;
- `subcategoria`: última categoría;
- `ruta_categoria`: jerarquía completa separada por `>`.

Ejemplo:

```text
Libros > Literatura > Literatura hispanoamericana
```

#### `extract_product(session, url, extraction_date)`

Descarga una página y combina los datos del JSON-LD con las categorías del
breadcrumb. Obtiene:

- URL;
- nombre;
- marca;
- categorías;
- SKU;
- precio en COP;
- disponibilidad;
- longitud de la descripción;
- fecha de extracción.

También normaliza entidades HTML como `&amp;` y convierte una disponibilidad
como `http://schema.org/InStock` en `InStock`.

#### `save_csv(records, output_path)`

Crea la carpeta de destino, define las columnas con base en el primer registro
y escribe los datos en formato CSV con codificación UTF-8.

#### `main()`

Es el punto de entrada del programa. Configura argumentos como:

- `--limit`: cantidad máxima de productos;
- `--delay`: pausa entre solicitudes;
- `--sitemap`: fuente de URLs;
- `--output`: archivo CSV de salida.

También captura errores HTTP, registra advertencias y guarda checkpoints
después de cada producto válido para reducir la pérdida de datos si una
ejecución se interrumpe.

### Por qué algunos productos no aparecen

No todas las URLs del sitemap contienen necesariamente un bloque `Product`
válido en el momento de la extracción. También pueden producirse errores
temporales o timeouts. Es preferible descartar esos registros y reportarlo,
en lugar de inventar valores.

---

## 4. Dataset original y limpieza

### Qué decir

> El archivo original conserva la información tal como fue extraída. No lo
> reemplazo durante la limpieza porque necesito mantener la trazabilidad.
> Luego genero una segunda versión procesada que será utilizada por el
> análisis y el modelo.

El archivo de limpieza es:

`05_prepare_data.py`

### Funciones de limpieza

#### `normalize_text(value)`

Convierte valores nulos en texto vacío y elimina espacios repetidos o
innecesarios.

#### `build_quality_report(raw, clean, ...)`

Construye un reporte con:

- filas originales;
- filas finales;
- filas eliminadas;
- nulos;
- URLs únicas;
- SKU únicos;
- distribución por categoría;
- mínimo, mediana, promedio y máximo del precio.

#### `create_data_dictionary()`

Crea un diccionario de datos que explica el nombre, tipo y significado de cada
columna.

#### `prepare_dataset()`

Ejecuta el flujo completo:

1. Carga el CSV original.
2. Comprueba que existan las columnas obligatorias.
3. Normaliza las columnas de texto.
4. Conserva `sku` como texto y rellena con ceros a la izquierda.
5. Convierte `precio_cop` a número.
6. Convierte la fecha.
7. Detecta valores faltantes en variables importantes.
8. Elimina precios nulos o menores o iguales a cero.
9. Elimina duplicados por URL y SKU.
10. Calcula `longitud_nombre`.
11. Calcula `palabras_nombre`.
12. Guarda el dataset limpio, el reporte y el diccionario.

### Resultado de la limpieza

En este caso:

- filas originales: 388;
- filas finales: 388;
- filas eliminadas: 0;
- nulos finales: 0;
- URLs únicas: 388;
- SKU únicos: 388.

No eliminar filas solo por ser caras. Un precio alto puede ser un valor
atípico real y se debe analizar, no borrar automáticamente.

---

## 5. Variables utilizadas

### Variable objetivo

```text
precio_cop
```

Es el valor que el modelo intenta predecir.

### Variables predictoras

```text
marca
categoria_principal
subcategoria
disponibilidad
longitud_descripcion
longitud_nombre
palabras_nombre
```

Las cuatro primeras son categóricas. Las tres últimas son numéricas.

No se utilizan `url` ni `sku` como predictores porque son identificadores.
Usarlos podría hacer que el modelo memorice productos en vez de aprender
patrones generalizables.

---

## 6. Análisis exploratorio y gráficas

### Qué decir

> Antes de entrenar el modelo revisé la distribución de los datos. Esto
> permite conocer la composición de la muestra, detectar precios extremos y
> observar diferencias entre categorías y marcas.

Los scripts están en `08_graficas/`.

### `01_distribucion_precios.py`

Utiliza `precio_cop` y genera un histograma. El eje horizontal representa el
precio y el eje vertical la cantidad de productos.

Sirve para observar concentración, dispersión y valores extremos.

### `02_productos_por_categoria.py`

Agrupa por `categoria_principal` y cuenta productos mediante SKU únicos.
Permite saber si la muestra está equilibrada.

En la muestra predominan:

- Libros: 146;
- Tecnología: 110;
- Arte y Manualidades: 57.

Las categorías con muy pocos productos deben interpretarse con precaución.

### `03_precios_por_categoria.py`

Agrupa los precios por categoría y genera diagramas de caja. La caja resume
la distribución central y los bigotes muestran su variación.

La mediana es especialmente útil porque el promedio puede aumentar mucho por
productos tecnológicos costosos.

### `04_precio_vs_descripcion.py`

Usa `longitud_descripcion` en X y `precio_cop` en Y. El color representa la
categoría.

La gráfica muestra asociación, no causalidad. No se puede afirmar que una
descripción larga cause un precio mayor.

### `05_marcas_principales.py`

Cuenta los SKU por marca y muestra las 15 marcas con mayor presencia. La
gráfica describe la muestra extraída; no representa necesariamente todo el
catálogo de Panamericana.

---

## 7. Selección del modelo

### Qué decir

> Elegí Random Forest Regressor porque el objetivo es numérico, el conjunto
> es pequeño y las relaciones entre categoría, marca, subcategoría y precio
> probablemente no son completamente lineales. Random Forest puede capturar
> relaciones no lineales sin exigir una transformación compleja de los datos.

También se creó una línea base que siempre predice la mediana del precio.
Ningún modelo debe evaluarse sin compararlo con una referencia sencilla.

Ventajas de Random Forest en este proyecto:

- funciona con relaciones no lineales;
- no exige normalizar las variables numéricas;
- permite medir importancia de variables;
- es rápido con 388 registros;
- combina muchos árboles para reducir la variabilidad de un solo árbol.

Limitaciones:

- puede sobreajustarse si los árboles son demasiado complejos;
- las importancias no implican causalidad;
- requiere codificar las categorías;
- no resuelve la falta de información que no fue publicada.

---

## 8. Entrenamiento del modelo

El archivo es:

`07_train_model.py`

### Funciones principales

#### `build_pipeline(...)`

Crea un pipeline de scikit-learn con dos etapas:

1. `ColumnTransformer` para procesar variables;
2. `RandomForestRegressor` para entrenar el modelo.

Para las categorías utiliza:

```python
OneHotEncoder(handle_unknown="ignore")
```

Esto convierte cada categoría en columnas binarias y evita que una categoría
nueva provoque un error durante la predicción.

Para variables numéricas utiliza imputación por mediana si fuera necesario.

#### `calculate_metrics(actual, predicted, baseline)`

Calcula MAE, RMSE y R² tanto para Random Forest como para la línea base.

#### `parse_max_features(value)`

Permite convertir desde la terminal valores como `sqrt`, `log2`, `none`,
enteros o decimales.

#### `parse_args()`

Permite modificar hiperparámetros sin editar el código:

- `n_estimators`: cantidad de árboles;
- `max_depth`: profundidad máxima;
- `min_samples_leaf`: mínimo de muestras por hoja;
- `max_features`: variables examinadas por división;
- `test_size`: proporción de prueba;
- `random_state`: semilla reproducible.

#### `main()`

Realiza el entrenamiento:

1. Carga el dataset limpio.
2. Comprueba las columnas.
3. Separa predictores y objetivo.
4. Divide 80 % para entrenamiento y 20 % para prueba.
5. Ajusta el pipeline solo con entrenamiento.
6. Predice el conjunto de prueba.
7. Calcula las métricas.
8. Guarda el pipeline `.joblib`.
9. Guarda métricas, predicciones e importancias.

La semilla `42` permite repetir la misma división y obtener resultados
comparables.

### Hiperparámetros utilizados

```text
n_estimators = 300
max_depth = 12
min_samples_leaf = 2
max_features = sqrt
test_size = 0.2
random_state = 42
```

---

## 9. Significado de las métricas

En el enunciado se pueden escribir por error nombres como “RMA” o “RMSA”.
En este proyecto las métricas correctas son **MAE, RMSE y R²**.

### MAE: Mean Absolute Error

En español: error absoluto medio.

Fórmula:

```text
MAE = promedio(|precio_real - precio_predicho|)
```

Indica cuántos pesos se equivoca el modelo en promedio, sin importar si se
equivoca por encima o por debajo.

Ventaja: es fácil de interpretar y no exagera tanto los errores extremos.

Resultado:

```text
Random Forest: $54.199,75 COP
Línea base:    $47.407,69 COP
```

En MAE la línea base fue ligeramente mejor.

### RMSE: Root Mean Squared Error

En español: raíz del error cuadrático medio.

Fórmula:

```text
RMSE = raíz(promedio((precio_real - precio_predicho)^2))
```

También está expresado en pesos, pero penaliza más los errores grandes porque
los eleva al cuadrado.

Resultado:

```text
Random Forest: $98.447,05 COP
Línea base:    $116.276,11 COP
```

Random Forest fue mejor en RMSE. Esto significa que maneja mejor los errores
extremos que la predicción constante de la mediana.

### R²: coeficiente de determinación

Fórmula:

```text
R² = 1 - error_del_modelo / error_de_predecir_la_media
```

Interpretación:

- `1`: ajuste perfecto;
- `0`: no mejora frente a predecir la media;
- menor que `0`: peor que la referencia;
- `0,221`: el modelo explica aproximadamente el 22,1 % de la variación
  observada en este conjunto de prueba.

Resultado:

```text
Random Forest: 0,221
Línea base:   -0,086
```

R² no significa que el modelo acierte el 22,1 % de los productos. Es una
medida de variabilidad explicada, no un porcentaje de aciertos.

### Por qué se reportan varias métricas

Una sola métrica puede dar una visión incompleta:

- MAE comunica el error típico en pesos;
- RMSE muestra el efecto de errores extremos;
- R² indica cuánta variabilidad explica el modelo.

En este caso, reportar las tres permite explicar que Random Forest mejora RMSE
y R², pero no MAE.

---

## 10. Resultados del modelo

El resultado guardado en `06_metrics.json` es:

| Métrica | Línea base | Random Forest |
|---|---:|---:|
| MAE | $47.407,69 | $54.199,75 |
| RMSE | $116.276,11 | $98.447,05 |
| R² | -0,086 | 0,221 |

### Qué decir

> El modelo no debe presentarse como un predictor comercial perfecto. Random
> Forest supera a la línea base en RMSE y R², pero no en MAE. Esto indica que
> reduce mejor los errores grandes, aunque la predicción de la mediana todavía
> tiene menor error absoluto promedio en esta división.

El conjunto de prueba tiene 78 productos. Los precios reales y predichos están
en:

`03_predicciones_evaluacion_random_forest.csv`

El archivo de evaluación también permite calcular:

- error absoluto;
- error firmado;
- error porcentual;
- productos con errores mayores.

---

## 11. Evaluación y gráficas de predicción

El archivo es:

`08_evaluate_model.py`

### Qué hace

1. Carga las predicciones.
2. Carga las métricas.
3. Calcula el error firmado.
4. Calcula el error porcentual.
5. Marca si el error está por debajo del MAE.
6. Guarda una tabla para Power BI.
7. Guarda la comparación entre línea base y Random Forest.
8. Genera cuatro gráficas.

### Gráficas

#### Reales frente a predichos

Si los puntos se acercan a la diagonal, las predicciones se parecen a los
valores reales.

#### Distribución de errores

Permite observar si el modelo tiende a sobreestimar o subestimar.

#### Mayores errores absolutos

Permite identificar productos difíciles de predecir y explicar valores
atípicos.

#### Importancia de variables

Muestra qué columnas contribuyeron más a las decisiones del bosque. Esta
importancia es predictiva, no causal.

---

## 12. Power BI

### Qué decir

> Power BI integra los resultados en un informe interactivo. El usuario puede
> filtrar productos por categoría, subcategoría, marca y disponibilidad, y
> también revisar el comportamiento del modelo mediante las predicciones y
> sus errores.

El archivo entregado es:

`10_Archivo_powerbi_Panamericana_Juan_Martinez.pbix`

### Páginas recomendadas

#### Página de catálogo

- total de productos;
- precio promedio;
- precio mediano;
- precio máximo;
- productos por categoría;
- filtros por categoría, marca y disponibilidad.

#### Página de análisis

- distribución de precios;
- precio por categoría;
- marcas principales;
- precio frente a longitud de descripción;
- tabla de productos.

#### Página de evaluación

- precio real frente a precio predicho;
- MAE, RMSE y R²;
- comparación con línea base;
- importancia de variables;
- tabla de errores.

### Tablas utilizadas

- `01_panamericana_products.csv`: evidencia de extracción;
- `02_panamericana_products_clean.csv`: catálogo limpio;
- `03_predicciones_evaluacion_random_forest.csv`: evaluación;
- `06_metrics.json`: valores de métricas.

---

## 13. Limitaciones y conclusiones

### Limitaciones

1. La muestra tiene 388 productos, no todo el catálogo.
2. Las categorías no están equilibradas.
3. Libros y tecnología concentran muchos registros.
4. Algunos precios son muy superiores al precio típico.
5. Los precios y la disponibilidad pueden cambiar.
6. La extracción corresponde a una fecha concreta.
7. El modelo no dispone de variables como material, tamaño, promoción o costo
   de envío si no fueron publicados en el JSON-LD.
8. El resultado es académico y exploratorio, no una herramienta comercial.

### Conclusión para decir

> El proyecto demuestra un flujo reproducible de web scraping, preparación de
> datos, análisis exploratorio, entrenamiento y evaluación de un modelo de
> machine learning. Random Forest obtuvo R² positivo y menor RMSE que la línea
> base, pero el MAE fue ligeramente mayor. Por eso, la conclusión no es que el
> modelo sea perfecto, sino que encuentra señales útiles en las categorías,
> marcas y características de los productos, aunque todavía está limitado por
> el tamaño y la heterogeneidad del dataset.

---

## 14. Demostración sugerida

1. Abrir `01_panamericana_products.csv` y explicar que es el resultado bruto.
2. Mostrar `02_panamericana_products_clean.csv`.
3. Abrir `04_extract_panamericana.py` y explicar el sitemap y JSON-LD.
4. Abrir `05_prepare_data.py` y explicar las validaciones.
5. Mostrar una gráfica exploratoria.
6. Abrir `07_train_model.py` y explicar la división de datos y el pipeline.
7. Mostrar `06_metrics.json`.
8. Explicar MAE, RMSE y R² con la tabla comparativa.
9. Abrir `03_predicciones_evaluacion_random_forest.csv`.
10. Mostrar en Power BI el catálogo y sus filtros.
11. Mostrar la página de evaluación.
12. Cerrar con limitaciones y conclusiones.

## 15. Respuestas breves a preguntas posibles

### ¿Por qué es regresión?

Porque `precio_cop` es un valor numérico continuo que se desea estimar.

### ¿Por qué no usar SKU?

Porque identifica productos, pero no es una característica generalizable del
producto. Podría causar memorización.

### ¿Por qué usar One-Hot Encoding?

Porque los modelos no pueden utilizar directamente textos como “Libros” o
“Tecnología”. One-Hot Encoding representa cada categoría mediante variables
binarias.

### ¿Por qué comparar con una línea base?

Para comprobar que el modelo aporta valor frente a una estrategia sencilla.

### ¿El R² de 0,221 significa 22,1 % de aciertos?

No. Significa que el modelo explica aproximadamente el 22,1 % de la
variabilidad del precio en los datos de prueba.

### ¿Por qué el MAE de Random Forest es peor?

Porque el conjunto contiene precios muy dispersos y categorías con pocos
ejemplos. La línea base de la mediana puede ser competitiva para el error
absoluto típico, mientras que Random Forest reduce mejor algunos errores
extremos, lo que se refleja en RMSE.

### ¿Qué se mejoraría en el futuro?

Extraer más productos de forma controlada, recoger más variables del producto,
equilibrar categorías, probar transformación logarítmica del precio y evaluar
con validación cruzada.
