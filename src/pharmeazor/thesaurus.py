"""Recherche exacte dans le Thésaurus ANSM.

Le Thésaurus est une base **structurée** : une substance (ou une classe) et la
liste de ses interactions, chacune avec une cible, un niveau de risque et une
conduite à tenir. La recherche vectorielle n'a donc pas de sens ici : elle
rapproche des textes qui se ressemblent au lieu de vérifier une paire
substance ↔ substance. On fait un **lookup exact** :

1. on repère dans la question les substances et classes connues (noms exacts,
   alias usuels comme « aspirine » ou « AINS », et appartenance aux classes via
   le champ `membres`) ;
2. on cherche la paire dans les deux sens ;
3. on renvoie les interactions telles quelles, avec leur `chunk_id` de corpus.

Les embeddings restent réservés aux textes de notices (RCP ANPP, EMA) et aux
catalogues, où la formulation libre justifie une recherche sémantique.
"""
from __future__ import annotations

import json
import re
from dataclasses import dataclass
from pathlib import Path

from .config import INTERIM
from .textnorm import norm

THESAURUS_JSON = INTERIM / "thesaurus" / "interactions_medicamenteuses.json"

# Alias grand public -> substance ou classe du Thésaurus (clés normalisées).
# Les DCI et les marques sont déjà couvertes par les titres et `membres` ;
# ces alias ne servent qu'aux mots que le Thésaurus n'écrit pas ainsi.
ALIASES = {
    "aspirine": "acide acetylsalicylique",
    "ibuprofene": "anti inflammatoires non steroidiens",
    "anti inflammatoire": "anti inflammatoires non steroidiens",
    "anti inflammatoires": "anti inflammatoires non steroidiens",
    "ains": "anti inflammatoires non steroidiens",
    "a i n s": "anti inflammatoires non steroidiens",
    "iec": "inhibiteurs de l enzyme de conversion",
    "inhibiteur de l enzyme de conversion": "inhibiteurs de l enzyme de conversion",
    "anticoagulant": "anticoagulants oraux",
    "anticoagulants": "anticoagulants oraux",
    "beta bloquant": "beta bloquants sauf esmolol y compris collyres",
    "beta bloquants": "beta bloquants sauf esmolol y compris collyres",
    "diuretique": "diuretiques",
    "diuretiques": "diuretiques",
    "calcium": "calcium",
}

# Niveaux du Thésaurus, du plus grave au plus léger.
LEVEL_ORDER = {
    "contre indication": 0,
    "association deconseillee": 1,
    "association déconseillée": 1,
    "precaution d emploi": 2,
    "précaution d'emploi": 2,
    "a prendre en compte": 3,
    "à prendre en compte": 3,
}


@dataclass(frozen=True)
class Interaction:
    chunk_id: str
    substance: str
    target: str
    level: str
    description: str
    main_key: str
    target_key: str


class ThesaurusLookup:
    """Index exact du Thésaurus, aligné sur les `chunk_id` du corpus."""

    def __init__(self, path: Path = THESAURUS_JSON):
        self.path = Path(path)
        self.blocks = (
            json.loads(self.path.read_text(encoding="utf-8")) if self.path.exists() else []
        )
        self.by_key: dict[str, dict] = {}
        self.member_classes: dict[str, list[str]] = {}
        self.interactions: list[Interaction] = []

        for bloc_idx, bloc in enumerate(self.blocks):
            name = (bloc.get("substance_principale") or "").strip()
            key = norm(name)
            if not key:
                continue
            self.by_key[key] = bloc
            for member in (bloc.get("membres") or "").split(","):
                member_key = norm(member)
                if member_key:
                    self.member_classes.setdefault(member_key, []).append(key)
            for idx, interaction in enumerate(bloc.get("interactions", [])):
                target = (interaction.get("substance_cible") or "").strip()
                self.interactions.append(
                    Interaction(
                        chunk_id=f"thesaurus:{key}:{bloc_idx}:{idx}",
                        substance=name,
                        target=target,
                        level=(interaction.get("niveau") or "").strip(),
                        description=(interaction.get("description") or "").strip(),
                        main_key=key,
                        target_key=norm(target),
                    )
                )

        self.phrases: list[tuple[str, str]] = [(key, key) for key in self.by_key]
        for alias, target in ALIASES.items():
            if target in self.by_key:
                self.phrases.append((norm(alias), target))
        # Les phrases les plus longues d'abord : « sels de calcium » avant « calcium ».
        self.phrases.sort(key=lambda item: -len(item[0]))

    # ---------- résolution des mentions ----------
    def find_mentions(self, query: str) -> list[tuple[str, str]]:
        """Renvoie les (phrase reconnue, clé de bloc) présents dans la question."""
        text = norm(query)
        occupied: list[tuple[int, int]] = []
        found: list[tuple[str, str]] = []
        for phrase, target in self.phrases:
            pattern = rf"(?<![a-z0-9]){re.escape(phrase)}(?![a-z0-9])"
            for match in re.finditer(pattern, text):
                span = match.span()
                if any(start < span[1] and span[0] < end for start, end in occupied):
                    continue
                occupied.append(span)
                if target not in (item[1] for item in found):
                    found.append((phrase, target))
        return found

    def _candidate_blocks(self, key: str) -> list[str]:
        blocks = [key] if key in self.by_key else []
        for class_key in self.member_classes.get(key, []):
            if class_key not in blocks:
                blocks.append(class_key)
        return blocks

    # ---------- lookup ----------
    def lookup(self, query: str) -> list[Interaction]:
        mentions = self.find_mentions(query)
        if not mentions:
            return []

        candidates = [self._candidate_blocks(target) for _, target in mentions]
        if len(mentions) >= 2:
            results = []
            for left in candidates[0]:
                for right in candidates[1]:
                    for interaction in self.interactions:
                        if interaction.main_key == left and interaction.target_key == right:
                            results.append(interaction)
            # Une paire peut être décrite dans l'autre sens : on complète.
            for left in candidates[0]:
                for right in candidates[1]:
                    for interaction in self.interactions:
                        if interaction.main_key == right and interaction.target_key == left:
                            results.append(interaction)
        else:
            results = [
                interaction
                for interaction in self.interactions
                if interaction.main_key in candidates[0]
            ]

        seen, unique = set(), []
        for interaction in results:
            if interaction.chunk_id in seen:
                continue
            seen.add(interaction.chunk_id)
            unique.append(interaction)
        unique.sort(
            key=lambda item: (
                LEVEL_ORDER.get(norm(item.level), 9),
                norm(item.substance),
                norm(item.target),
            )
        )
        return unique

    def lookup_chunk_ids(self, query: str, k: int = 10) -> list[str]:
        return [interaction.chunk_id for interaction in self.lookup(query)[:k]]


def load_lookup(path: Path = THESAURUS_JSON) -> ThesaurusLookup:
    return ThesaurusLookup(path)
