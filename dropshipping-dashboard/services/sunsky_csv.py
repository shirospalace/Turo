"""Import products from a Sunsky-Online bulk CSV export.

Sunsky's exact export column names vary by account/version, so this maps a
set of common header aliases (case-insensitive) onto our generic Product
fields rather than assuming one fixed schema. Unrecognized columns are
ignored; missing required fields (title) cause that row to be skipped.
"""
import csv
import io

HEADER_ALIASES = {
    "title": ["title", "product name", "product title", "name"],
    "sunsky_sku": ["sku", "product sku", "item sku", "product id", "spu"],
    "source_url": ["url", "product url", "product link", "link"],
    "cost": ["price", "cost", "unit price", "wholesale price"],
    "weight_g": ["weight", "weight(g)", "weight_g", "weight (g)"],
    "warehouse_location": ["warehouse", "warehouse location", "ship from"],
    "images": ["image", "image url", "images", "main image"],
}

WAREHOUSE_ALIASES = {
    "china": "CN",
    "cn": "CN",
    "hong kong": "HK",
    "hk": "HK",
    "usa": "US",
    "us": "US",
    "united states": "US",
    "eu": "EU-UK",
    "uk": "EU-UK",
    "eu/uk": "EU-UK",
    "uae": "UAE",
}


def _normalize_header(h):
    return (h or "").strip().lower()


def _build_column_map(fieldnames):
    """Map our internal field name -> actual CSV column name present."""
    normalized = {_normalize_header(f): f for f in (fieldnames or [])}
    column_map = {}
    for field, aliases in HEADER_ALIASES.items():
        for alias in aliases:
            if alias in normalized:
                column_map[field] = normalized[alias]
                break
    return column_map


def _to_float(value, default=0.0):
    try:
        return float(str(value).replace("$", "").replace(",", "").strip())
    except (TypeError, ValueError):
        return default


def parse_sunsky_csv(file_bytes: bytes):
    """Returns (rows, warnings). rows are dicts ready to construct Product objects."""
    text = file_bytes.decode("utf-8-sig", errors="replace")
    reader = csv.DictReader(io.StringIO(text))
    column_map = _build_column_map(reader.fieldnames)

    warnings = []
    if "title" not in column_map:
        warnings.append(
            "No recognizable title/product-name column found — file may not be a Sunsky export."
        )

    rows = []
    for i, raw_row in enumerate(reader, start=2):  # header is row 1
        title = raw_row.get(column_map.get("title", ""), "").strip()
        if not title:
            warnings.append(f"Row {i}: skipped (missing title)")
            continue

        warehouse_raw = raw_row.get(column_map.get("warehouse_location", ""), "").strip().lower()
        warehouse = WAREHOUSE_ALIASES.get(warehouse_raw, "CN")

        image_raw = raw_row.get(column_map.get("images", ""), "").strip()
        images = [u.strip() for u in image_raw.split(",") if u.strip()] if image_raw else []

        rows.append(
            {
                "title": title,
                "sunsky_sku": raw_row.get(column_map.get("sunsky_sku", ""), "").strip(),
                "source_url": raw_row.get(column_map.get("source_url", ""), "").strip(),
                "cost": _to_float(raw_row.get(column_map.get("cost", ""), 0)),
                "weight_g": _to_float(raw_row.get(column_map.get("weight_g", ""), 0)),
                "warehouse_location": warehouse,
                "images": images,
            }
        )

    return rows, warnings
