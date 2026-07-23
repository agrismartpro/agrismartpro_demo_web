#!/usr/bin/env python3
"""Genera il sito statico AgriSmartPro senza dipendenze esterne."""

from __future__ import annotations

import html
import json
import shutil
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SITE = ROOT / "site"
CONTENT = SITE / "content"
TEMPLATES = SITE / "templates"


def load_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def replace(template: str, values: dict[str, str]) -> str:
    rendered = template
    for key, value in values.items():
        rendered = rendered.replace("{{" + key + "}}", value)
    if "{{" in rendered or "}}" in rendered:
        raise ValueError("Segnaposto non risolto nel template")
    return rendered


def build_auth_links(config: dict) -> str:
    links: list[str] = []
    if config.get("app_login_url"):
        links.append(
            f'<a class="nav-login" href="{html.escape(config["app_login_url"], quote=True)}">Accedi</a>'
        )
    if config.get("app_registration_url"):
        links.append(
            f'<a class="button button-small" href="{html.escape(config["app_registration_url"], quote=True)}">Registrati</a>'
        )
    return "\n".join(links)


def build() -> None:
    config = load_json(ROOT / "site_config.json")
    pages = load_json(SITE / "pages.json")
    base = (TEMPLATES / "base.html").read_text(encoding="utf-8")
    header = replace(
        (TEMPLATES / "header.html").read_text(encoding="utf-8"),
        {"AUTH_LINKS": build_auth_links(config)},
    )
    footer = (TEMPLATES / "footer.html").read_text(encoding="utf-8")

    for page in pages:
        source = CONTENT / page["source"]
        if not source.exists():
            continue
        slug = page["slug"]
        output = ROOT / "index.html" if not slug else ROOT / slug / "index.html"
        output.parent.mkdir(parents=True, exist_ok=True)
        canonical = config["site_url"].rstrip("/") + ("/" if not slug else f"/{slug}/")
        rendered = replace(
            base,
            {
                "TITLE": html.escape(page["title"]),
                "DESCRIPTION": html.escape(page["description"], quote=True),
                "CANONICAL_URL": html.escape(canonical, quote=True),
                "SITE_URL": html.escape(config["site_url"].rstrip("/"), quote=True),
                "HEADER": header,
                "CONTENT": source.read_text(encoding="utf-8"),
                "FOOTER": footer,
            },
        )
        output.write_text(rendered, encoding="utf-8")

    for old in ("caratteristiche", "pricing"):
        stale = ROOT / old
        if stale.exists() and stale.is_dir():
            shutil.rmtree(stale)


if __name__ == "__main__":
    build()
