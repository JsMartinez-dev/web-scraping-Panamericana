## Predecir el precio de un producto a partir de su categoría, marca, disponibilidad, descuento y características publicadas.


### extract
    Extrae una muestra de productos públicos de PLa extracción usa únicamente URLs públicas del sitemap de productos y el
    JSON-LD publicado en cada página. No consulta las rutas bloqueadas por
    robots.txt, como búsquedas, API, cuentas o checkout.
    
Set-Location '.\scraping'; ..\.venv\Scripts\python.exe -m py_compile extract_panamericana.py; ..\.venv\Scripts\python.exe extract_panamericana.py --limit 5000 --delay 0.2
