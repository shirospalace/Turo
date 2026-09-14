"""Generates copy-paste-ready listing drafts per marketplace.

These are starting drafts, not final copy — you review/edit everything
before it goes live (nothing here auto-publishes). Each marketplace has
different length limits and conventions, so the same product produces
different shaped output per platform:

  Amazon: keyword-front-loaded title (<=200 chars), 5 bullet points, description
  eBay:   short title (<=80 chars), item-specifics-style bullets, description
  Etsy:   descriptive title (<=140 chars), up to 13 tags (<=20 chars each), description
"""

WAREHOUSE_SHIP_NOTE = {
    "US": "Ships from a US warehouse — fast domestic delivery (~3 days).",
    "HK": "Ships from Hong Kong — typically 1-2 weeks to the US.",
    "CN": "Ships from China — typically 1-3+ weeks to the US.",
    "EU-UK": "Ships from an EU/UK warehouse — fast delivery within that region.",
    "UAE": "Ships from a UAE warehouse — fast delivery within that region.",
}


def _truncate(text: str, limit: int) -> str:
    return text if len(text) <= limit else text[: limit - 1].rstrip() + "…"


def _base_description(product) -> str:
    desc = (product.description or "").strip()
    if not desc:
        desc = f"{product.title} — [add material, dimensions, color, and standout features here]."
    return desc


def generate_amazon(product, target_price: float) -> dict:
    title = _truncate(f"{product.title} - {product.category.name if product.category else ''}".strip(" -"), 200)
    bullets = [
        f"[BENEFIT] {product.title} — describe the #1 reason to buy",
        "[MATERIAL/QUALITY] Add material, construction, and durability details",
        "[SIZE/FIT] Add dimensions or capacity",
        "[USE CASE] Everyday use, travel, gifting, etc.",
        "[CARE/WARRANTY] Care instructions or satisfaction guarantee",
    ]
    body = _base_description(product) + "\n\n" + "\n".join(f"• {b}" for b in bullets)
    return {"title": title, "body": body, "tags": [], "price": target_price}


def generate_ebay(product, target_price: float) -> dict:
    title = _truncate(product.title, 80)
    ship_note = WAREHOUSE_SHIP_NOTE.get(product.warehouse_location, "")
    specifics = [
        "Brand: [add]",
        "Material: [add]",
        "Color: [add]",
        "Style: [add]",
        f"Condition: New",
    ]
    body = (
        _base_description(product)
        + "\n\nItem specifics:\n"
        + "\n".join(f"- {s}" for s in specifics)
        + (f"\n\nShipping: {ship_note}" if ship_note else "")
    )
    return {"title": title, "body": body, "tags": [], "price": target_price}


def generate_etsy(product, target_price: float) -> dict:
    title = _truncate(product.title, 140)
    base_tags = [product.category.name.lower() if product.category else "accessory", "gift", "handbag", "purse"]
    tags = [_truncate(t, 20) for t in base_tags][:13]
    body = _base_description(product) + "\n\nMaterials: [add]\nStyle: [add]\n"
    return {"title": title, "body": body, "tags": tags, "price": target_price}


GENERATORS = {
    "amazon": generate_amazon,
    "ebay": generate_ebay,
    "etsy": generate_etsy,
}


def generate_draft(product, marketplace: str, target_price: float) -> dict:
    fn = GENERATORS.get(marketplace)
    if not fn:
        raise ValueError(f"Unknown marketplace '{marketplace}'")
    return fn(product, target_price)
