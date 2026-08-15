#!/usr/bin/env python3
"""business.py — HEER business registry.

HEER can operate multiple businesses. Each business has its own data root,
vault, and intelligence. This module is the single source of truth for
business definitions and the current active business (in-memory per session).

Businesses are defined in businesses.json at the project root. The default
business is the existing AI agency (backward compatible).

Run:  python3 -m agent.business
"""

import json
import os
import re

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CONFIG_PATH = os.path.join(BASE, "businesses.json")

# In-memory active business (per session). Defaults to the first enabled
# business, which is the AI agency for backward compatibility.
_CURRENT_ID = None


def _default_businesses():
    """Fallback registry if businesses.json is missing or invalid."""
    return [
        {
            "id": "ai_agency",
            "name": "AI Agency",
            "type": "AI Services",
            "data_root": "data/demo",
            "icon": "◈",
            "color": "#4d9fff",
            "tagline": "Intelligence That Executes",
            "enabled": True,
            "default": True,
        }
    ]


def _load_config():
    try:
        with open(CONFIG_PATH, "r", encoding="utf-8") as f:
            cfg = json.load(f)
        businesses = cfg.get("businesses", [])
        if not businesses:
            return _default_businesses()
        return businesses
    except (FileNotFoundError, json.JSONDecodeError):
        return _default_businesses()


def list_businesses():
    """All enabled businesses, with the default first."""
    businesses = [b for b in _load_config() if b.get("enabled", True)]
    businesses.sort(key=lambda b: (0 if b.get("default") else 1, b.get("name", "")))
    return businesses


def get_business(business_id):
    """Return a business by id, or None."""
    for b in _load_config():
        if b.get("id") == business_id and b.get("enabled", True):
            return b
    return None


def _normalize(text):
    """Normalize a business name/id for fuzzy matching.

    "Sip & Slice" -> "sip_and_slice", "sip and slice" -> "sip_and_slice".
    """
    t = (text or "").strip().lower()
    t = t.replace("&", " and ")
    t = re.sub(r"[^a-z0-9]+", "_", t).strip("_")
    return t


def find_business(query):
    """Find a business by id, name, or a normalized fuzzy match. Returns None if not found."""
    q = (query or "").strip()
    if not q:
        return None
    nq = _normalize(q)
    for b in _load_config():
        if not b.get("enabled", True):
            continue
        if b.get("id") == q or b.get("name", "").lower() == q.lower():
            return b
        if nq and _normalize(b.get("id")) == nq:
            return b
        if nq and _normalize(b.get("name")) == nq:
            return b
    return None


def current_business():
    """Return the active business dict."""
    global _CURRENT_ID
    if _CURRENT_ID is None:
        businesses = list_businesses()
        if not businesses:
            return None
        _CURRENT_ID = businesses[0]["id"]
    b = get_business(_CURRENT_ID)
    if b is None:
        # Fall back to the first business if the active one was removed.
        businesses = list_businesses()
        if businesses:
            _CURRENT_ID = businesses[0]["id"]
            return businesses[0]
        return None
    return b


def switch_business(business_id):
    """Switch the active business. Returns the new business or None.

    Accepts an exact id, a name, or a natural-language variant
    (e.g. "sip and slice" matches "Sip & Slice" / "sip_and_slice").
    """
    global _CURRENT_ID
    b = find_business(business_id)
    if b is None:
        return None
    _CURRENT_ID = b["id"]
    return b


def business_data_root(business_id=None):
    """Resolve a business's data root to an absolute path.

    The root may be relative to the project base (e.g. "data/demo") or
    absolute. In demo mode, demo businesses resolve under data/demo_businesses/
    unless they specify their own root.
    """
    from . import data

    b = get_business(business_id) if business_id else current_business()
    if b is None:
        return None
    root = b.get("data_root", "")
    if not root:
        return None
    if os.path.isabs(root):
        return root
    return os.path.join(BASE, root)


def _save_config(businesses):
    """Persist the full business list back to businesses.json."""
    with open(CONFIG_PATH, "w", encoding="utf-8") as f:
        json.dump({"businesses": businesses}, f, indent=2, ensure_ascii=False)


def add_business(name, business_type="", data_root="", icon="🏢", color="#4d9fff",
                 tagline="", enabled=True):
    """Add a new business to the registry.

    Returns the new business dict, or None if the id/name already exists.
    """
    businesses = _load_config()
    slug = re.sub(r"[^a-z0-9]+", "_", (name or "").strip().lower()).strip("_")
    if not slug:
        return None
    # Ensure unique id
    base_slug = slug
    n = 2
    while any(b.get("id") == slug for b in businesses):
        slug = f"{base_slug}_{n}"
        n += 1
    if not data_root:
        data_root = f"data/demo_businesses/{slug}"
    new_b = {
        "id": slug,
        "name": (name or "").strip(),
        "type": (business_type or "").strip(),
        "data_root": data_root,
        "icon": icon or "🏢",
        "color": color or "#4d9fff",
        "tagline": (tagline or "").strip(),
        "enabled": True,
        "default": False,
    }
    businesses.append(new_b)
    _save_config(businesses)
    return new_b


def update_business(business_id, **fields):
    """Update fields on an existing business. Returns the updated dict or None."""
    businesses = _load_config()
    for i, b in enumerate(businesses):
        if b.get("id") == business_id:
            for key in ("name", "type", "data_root", "icon", "color", "tagline", "enabled"):
                if key in fields and fields[key] is not None:
                    b[key] = fields[key]
            businesses[i] = b
            _save_config(businesses)
            return b
    return None


def main():
    import sys
    if len(sys.argv) > 1 and sys.argv[1] == "switch":
        b = switch_business(sys.argv[2])
        print(json.dumps(b, indent=2, ensure_ascii=False) if b else "Business not found.")
        return
    print(json.dumps({
        "current": current_business(),
        "businesses": list_businesses(),
    }, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()