#!/usr/bin/env python3
"""Strict, review-oriented 365Scores position labels -> Brasfoot 22/23 codes.

No 365Scores scraping, API calls or network access in this module.
Unknown/generic roles must be reviewed rather than silently guessed.
"""
from __future__ import annotations

import re
import unicodedata

_POSITIONS = {
    0: ("goleiro", "guarda redes", "goalkeeper"),
    1: ("lateral direito", "lateral esquerdo", "lateral", "ala direito", "ala esquerdo", "right back", "left back", "fullback"),
    2: ("zagueiro", "zagueiro central", "defensor central", "defesa central", "centre back", "center back"),
    3: ("volante", "meia central", "meia atacante", "meio campista", "meio campo",
        "meia", "trinco", "medio central", "medio ofensivo", "central midfield",
        "attacking midfield", "defensive midfield", "midfielder"),
    4: ("centroavante", "ponta esquerda", "ponta direita", "atacante", "ponta de lanca",
        "centre forward", "center forward", "left forward", "right forward", "striker"),
}


def normalize(value: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError("Posição ausente")
    clean = unicodedata.normalize("NFD", value.casefold())
    clean = "".join(c for c in clean if unicodedata.category(c) != "Mn")
    return re.sub(r"\s+", " ", re.sub(r"[^a-z ]+", " ", clean)).strip()


def brasfoot_code(position_label: str) -> int:
    label = normalize(position_label)
    for code, aliases in _POSITIONS.items():
        if label in aliases:
            return code
    raise ValueError(f"Posição ambígua ou desconhecida: {position_label!r}; exige revisão manual")


def validate_source_url(url: str) -> str:
    """Accept only public 365Scores team squad pages as *references* (not data feeds)."""
    if not isinstance(url, str):
        raise ValueError("URL inválida")
    pattern = r"https://www\.365scores\.com/(?:pt-br|pt|en-us|en-uk|football)/?football/team/"
    # Locale-less URLs begin with /football/team; localized URLs with /<locale>/football/team.
    regex = r"\Ahttps://www\.365scores\.com/(?:pt-br/|pt/|en-us/|en-uk/)?football/team/[a-z0-9-]+-\d+/squad\Z"
    if not re.fullmatch(regex, url, re.ASCII):
        raise ValueError("URL de plantel não reconhecida")
    return url
