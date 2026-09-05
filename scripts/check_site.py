#!/usr/bin/env python3
"""Controlli statici del sito pubblico generato."""

from __future__ import annotations

import json
import re
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import unquote, urlparse


ROOT = Path(__file__).resolve().parents[1]
PROHIBITED = (
    "50 €",
    "500 €",
    "buy.stripe.com",
    "agrismartappemoweb",
    "conformità garantita",
    "completamente a norma",
    "sostituisce il consulente",
    "elimina ogni errore",
    "intelligenza artificiale normativa",
    "azienda agricola de carli",
    "gianfranco",
    "+39 339 384 7035",
)
FORBIDDEN_QUERY_KEYS = {"company_id", "tenant_id", "plan_id", "price_id"}


class PageParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.hrefs: list[str] = []
        self.sources: list[str] = []
        self.h1_count = 0
        self.missing_alt: list[str] = []
        self.has_viewport = False
        self.has_description = False
        self.has_main = False
        self.has_lang = False

    def handle_starttag(self, tag: str, attrs) -> None:
        values = dict(attrs)
        if tag == "html":
            self.has_lang = values.get("lang") == "it"
        elif tag == "meta":
            if values.get("name") == "viewport":
                self.has_viewport = True
            if values.get("name") == "description" and values.get("content"):
                self.has_description = True
        elif tag == "main":
            self.has_main = True
        elif tag == "h1":
            self.h1_count += 1
        elif tag == "a" and values.get("href"):
            self.hrefs.append(values["href"])
        elif tag in {"img", "script"} and values.get("src"):
            self.sources.append(values["src"])
            if tag == "img" and "alt" not in values:
                self.missing_alt.append(values["src"])
        elif tag == "link" and values.get("href"):
            self.sources.append(values["href"])


def local_target(raw: str) -> Path | None:
    parsed = urlparse(raw)
    if parsed.scheme or raw.startswith(("#", "//")):
        return None
    path = unquote(parsed.path)
    if not path:
        return None
    target = ROOT / path.lstrip("/")
    if path.endswith("/"):
        target /= "index.html"
    return target


def main() -> None:
    pages = json.loads((ROOT / "site" / "pages.json").read_text(encoding="utf-8"))
    expected = {
        ROOT / "index.html" if not page["slug"] else ROOT / page["slug"] / "index.html"
        for page in pages
    }
    failures: list[str] = []

    for page in sorted(expected):
        if not page.exists():
            failures.append(f"pagina mancante: {page.relative_to(ROOT)}")
            continue
        text = page.read_text(encoding="utf-8")
        parser = PageParser()
        parser.feed(text)

        if not parser.has_lang:
            failures.append(f"{page}: lingua italiana assente")
        if not parser.has_viewport:
            failures.append(f"{page}: viewport assente")
        if not parser.has_description:
            failures.append(f"{page}: description assente")
        if not parser.has_main:
            failures.append(f"{page}: main assente")
        if parser.h1_count != 1:
            failures.append(f"{page}: trovati {parser.h1_count} h1")
        if parser.missing_alt:
            failures.append(f"{page}: immagini senza alt {parser.missing_alt}")

        lowered = text.lower()
        for phrase in PROHIBITED:
            if phrase.lower() in lowered:
                failures.append(f"{page}: contenuto vietato {phrase!r}")

        for raw in parser.hrefs:
            parsed = urlparse(raw)
            query_keys = {item.split("=", 1)[0] for item in parsed.query.split("&") if item}
            forbidden = query_keys & FORBIDDEN_QUERY_KEYS
            if forbidden:
                failures.append(f"{page}: parametri vietati {sorted(forbidden)}")

        for raw in parser.hrefs + parser.sources:
            target = local_target(raw)
            if target is not None and not target.exists():
                failures.append(f"{page}: collegamento interrotto {raw}")

    css = (ROOT / "assets" / "site.css").read_text(encoding="utf-8")
    if "@media (min-width: 900px)" not in css:
        failures.append("breakpoint desktop assente")
    if "prefers-reduced-motion" not in css:
        failures.append("supporto movimento ridotto assente")

    if failures:
        raise SystemExit("\n".join(failures))
    print(f"site_checks=ok pages={len(expected)}")


if __name__ == "__main__":
    main()
