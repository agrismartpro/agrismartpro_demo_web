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


def build_pilot_request_link(config: dict) -> str:
    """Expose only the contact channel, never an application entry point."""
    return (
        f'<a class="nav-login" href="{html.escape(config["pilot_request_url"], quote=True)}" '
        'title="Richiedi informazioni sul programma pilota">'
        'Richiedi accesso al programma pilota</a>'
    )


def build_plan_cards(config: dict) -> str:
    cards: list[str] = []
    for plan in config["plans"]:
        cards.append(
            "\n".join(
                [
                    '<article class="plan-card">',
                    f'  <p class="eyebrow">{html.escape(plan["status"])}</p>',
                    f'  <h2>{html.escape(plan["name"])}</h2>',
                    f'  <p>{html.escape(plan["description"])}</p>',
                    f'  <a class="text-link" href="{html.escape(plan["cta_url"], quote=True)}">{html.escape(plan["cta_label"])} <span aria-hidden="true">→</span></a>',
                    "</article>",
                ]
            )
        )
    return "\n".join(cards)


def build() -> None:
    config = load_json(ROOT / "site_config.json")
    pages = load_json(SITE / "pages.json")
    base = (TEMPLATES / "base.html").read_text(encoding="utf-8")
    header = replace(
        (TEMPLATES / "header.html").read_text(encoding="utf-8"),
        {"AUTH_LINKS": build_pilot_request_link(config)},
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
        content = replace(
            source.read_text(encoding="utf-8"),
            {
                "DEMO_REQUEST_URL": html.escape(config["demo_request_url"], quote=True),
                "PILOT_REQUEST_URL": html.escape(config["pilot_request_url"], quote=True),
                "CONTACT_EMAIL": html.escape(config["contact_email"]),
                "PLAN_CARDS": build_plan_cards(config),
            },
        )
        rendered = replace(
            base,
            {
                "TITLE": html.escape(page["title"]),
                "DESCRIPTION": html.escape(page["description"], quote=True),
                "CANONICAL_URL": html.escape(canonical, quote=True),
                "SITE_URL": html.escape(config["site_url"].rstrip("/"), quote=True),
                "HEADER": header,
                "CONTENT": content,
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
