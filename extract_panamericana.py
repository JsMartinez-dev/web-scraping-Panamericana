

from __future__ import annotations

import argparse
import csv
import html
import json
import logging
import time
from datetime import date
from pathlib import Path
from typing import Any
from urllib.parse import urlparse
from xml.etree import ElementTree

import requests
from bs4 import BeautifulSoup


DEFAULT_SITEMAP_URL = "https://www.panamericana.com.co/sitemap/product-0.xml"
DEFAULT_OUTPUT = Path("data/raw/panamericana_products.csv")
REQUEST_TIMEOUT = 30
USER_AGENT = "AcademicWebScraper/1.0"

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
LOGGER = logging.getLogger(__name__)


def get_product_urls(session: requests.Session, sitemap_url: str, limit: int) -> list[str]:
    """Obtiene URLs únicas de producto desde un sitemap público."""
    response = session.get(sitemap_url, timeout=REQUEST_TIMEOUT)
    response.raise_for_status()

    root = ElementTree.fromstring(response.content)
    urls: list[str] = []
    seen: set[str] = set()
    namespace = {"sitemap": "http://www.sitemaps.org/schemas/sitemap/0.9"}

    for location in root.findall("sitemap:url/sitemap:loc", namespace):
        if location.text is None:
            continue
        url = location.text.strip()
        parsed = urlparse(url)
        if parsed.scheme not in {"http", "https"}:
            continue
        if url in seen:
            continue
        seen.add(url)
        urls.append(url)
        if len(urls) == limit:
            break

    return urls


def first_json_ld_product(soup: BeautifulSoup) -> dict[str, Any] | None:
    """Devuelve el primer bloque JSON-LD cuyo tipo sea Product."""
    for script in soup.select('script[type="application/ld+json"]'):
        if not script.string:
            continue
        try:
            payload = json.loads(script.string)
        except json.JSONDecodeError:
            LOGGER.warning("Se ignoró un bloque JSON-LD inválido.")
            continue

        candidates = payload if isinstance(payload, list) else [payload]
        for candidate in candidates:
            if not isinstance(candidate, dict):
                continue
            product_type = candidate.get("@type")
            if product_type == "Product" or (
                isinstance(product_type, list) and "Product" in product_type
            ):
                return candidate
    return None


def extract_categories(soup: BeautifulSoup) -> dict[str, str | None]:
    """Extrae la jerarquía de categorías desde el breadcrumb del producto."""
    breadcrumb = soup.select_one('[class*="product__breadcrumb"]')
    if breadcrumb is None:
        return {
            "categoria_principal": None,
            "subcategoria": None,
            "ruta_categoria": None,
        }

    categories = [
        " ".join(link.stripped_strings)
        for link in breadcrumb.select("a")
        if " ".join(link.stripped_strings)
    ]
    if not categories:
        return {
            "categoria_principal": None,
            "subcategoria": None,
            "ruta_categoria": None,
        }

    return {
        "categoria_principal": categories[0],
        "subcategoria": categories[-1] if len(categories) > 1 else None,
        "ruta_categoria": " > ".join(categories),
    }


def extract_product(
    session: requests.Session, url: str, extraction_date: str
) -> dict[str, Any] | None:
    """Extrae los campos disponibles del producto indicado."""
    response = session.get(url, timeout=REQUEST_TIMEOUT)
    response.raise_for_status()
    soup = BeautifulSoup(response.text, "html.parser")
    product = first_json_ld_product(soup)
    if product is None:
        LOGGER.warning("No se encontró Product JSON-LD: %s", url)
        return None

    offers = product.get("offers", {})
    first_offer = {}
    if isinstance(offers, dict):
        nested_offers = offers.get("offers", [])
        if isinstance(nested_offers, list) and nested_offers:
            first_offer = nested_offers[0] if isinstance(nested_offers[0], dict) else {}
        else:
            first_offer = offers

    brand = product.get("brand", {})
    brand_name = brand.get("name") if isinstance(brand, dict) else brand
    description = product.get("description", "")
    if isinstance(description, str):
        description = html.unescape(description)
    if isinstance(brand_name, str):
        brand_name = html.unescape(brand_name)
    availability = first_offer.get("availability")
    if isinstance(availability, str):
        availability = availability.rsplit("/", maxsplit=1)[-1]
    categories = extract_categories(soup)

    return {
        "url": url,
        "nombre": product.get("name"),
        "marca": brand_name,
        **categories,
        "sku": product.get("sku"),
        "precio_cop": first_offer.get("price"),
        "disponibilidad": availability,
        "longitud_descripcion": len(description) if isinstance(description, str) else None,
        "fecha_extraccion": extraction_date,
    }


def save_csv(records: list[dict[str, Any]], output_path: Path) -> None:
    """Guarda registros con columnas consistentes y crea su carpeta."""
    if not records:
        raise ValueError("No hay registros válidos para guardar.")

    output_path.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = list(records[0])
    with output_path.open("w", encoding="utf-8", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(records)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--limit", type=int, default=20, help="Máximo de productos.")
    parser.add_argument("--delay", type=float, default=1.0, help="Pausa entre páginas.")
    parser.add_argument("--sitemap", default=DEFAULT_SITEMAP_URL)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args()

    if args.limit < 1:
        parser.error("--limit debe ser mayor que cero.")
    if args.delay < 0:
        parser.error("--delay no puede ser negativo.")

    session = requests.Session()
    session.headers.update({"User-Agent": USER_AGENT, "Accept": "text/html"})
    extraction_date = date.today().isoformat()

    try:
        urls = get_product_urls(session, args.sitemap, args.limit)
    except (requests.RequestException, ElementTree.ParseError) as error:
        LOGGER.error("No se pudo leer el sitemap: %s", error)
        raise SystemExit(1) from error

    records: list[dict[str, Any]] = []
    for index, url in enumerate(urls):
        try:
            record = extract_product(session, url, extraction_date)
        except requests.RequestException as error:
            LOGGER.error("Error HTTP en %s: %s", url, error)
            record = None
        if record is not None:
            records.append(record)
        if index < len(urls) - 1:
            time.sleep(args.delay)

    try:
        save_csv(records, args.output)
    except (OSError, ValueError) as error:
        LOGGER.error("No se pudo guardar el CSV: %s", error)
        raise SystemExit(1) from error

    LOGGER.info("Registros guardados: %d en %s", len(records), args.output)


if __name__ == "__main__":
    main()
