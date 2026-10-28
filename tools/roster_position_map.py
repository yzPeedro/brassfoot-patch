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
    1: ("lateral direito", "lateral esquerdo", "lateral", "ala direito", "ala esquerdo", "right back", "left back", "fullback", "right wing back", "left wing back", "wing back"),
    2: ("zagueiro", "zagueiro central", "defensor central", "defesa central", "centre back", "center back"),
    3: ("volante", "meia central", "meia atacante", "meio campista", "meio campo",
        "meia", "trinco", "medio central", "medio ofensivo", "central midfield",
        "attacking midfield", "defensive midfield", "midfielder", "left midfield", "right midfield", "central midfielder", "attacking midfielder", "defensive midfielder"),
    4: ("centroavante", "ponta esquerda", "ponta direita", "atacante", "ponta de lanca",
        "centre forward", "center forward", "left forward", "right forward", "striker", "forward", "attacker", "left winger", "right winger", "winger", "second striker", "secondary striker"),
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


def resolve_positions(primary: str, secondary=()) -> int:
    """Prefer the specific primary role; resolve broad groups from alternatives.

    A fullback who can also play as a winger remains a fullback. A primary winger
    is a forward. Side and preferred foot are never inferred from one another.
    """
    primary = normalize(primary)
    broad = {"defender", "midfielder", "forward", "attacker"}
    alternatives = [normalize(x) for x in secondary if x]
    labels = alternatives + [primary] if primary in broad else [primary] + alternatives
    for label in labels:
        try:
            return brasfoot_code(label)
        except ValueError:
            continue
    raise ValueError(f"Posições sem detalhe suficiente: {labels!r}")


def position_flank(label: str) -> str | None:
    """Only an explicitly sided position supplies flank, never preferred foot."""
    label = normalize(label)
    if "left" in label or "esquerd" in label:
        return "left"
    if "right" in label or "direit" in label:
        return "right"
    return None


def display_player_name(full_name: str) -> str:
    """The product's two-word rule, keeping the complete source name elsewhere."""
    return " ".join(full_name.split()[:2])


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
