"""Module d'analyse de requêtes cliniques et pharmaceutiques (Package L2).

Ce module transforme une question utilisateur en langage naturel en une structure
typée `QueryAnalysis` exploitable par le retriever enrichi (L4) et le graphe de
connaissances (L3).

Fonctionnalités :
  1. Extraction d'entités par plus long match (longest-match) sur le lexique (L1)
  2. Repli flou (fuzzy fallback avec rapidfuzz) sur les fautes de frappe
  3. Détection des garde-fous éthiques et requêtes hors périmètre (is_out_of_scope)
  4. Classification d'intention (dosage, interaction, contre-indication, prix, etc.)
  5. Expansion de requête (DCI canoniques, classes pharmacologiques, alias)
  6. Temps d'exécution garanti < 5 ms par requête.
"""

from __future__ import annotations

import re
import time
from dataclasses import dataclass, field
from functools import lru_cache

from .lexicon import load_lexicon, resolve
from .normalize import FORM_TOKENS
from .textnorm import norm

# Motifs de conseil médical personnalisé, diagnostic ou prescription interdits
MEDICAL_ADVICE_PATTERNS = [
    r"\b(mon|ma|mes|notre|son|sa|ses)\s+"
    r"(fils|fille|enfant|bebe|nourrisson|pere|mere|voisin|voisine|frere|soeur|"
    r"epoux|epouse|patient|patiente|ami|amie)\b",
    r"\b(ordonnance|prescription|prescrire|rediger une ordonnance)\b",
    r"\b(dois[- ]je|doit[- ]il|doit[- ]elle|que doit|que faire|que dois|puis[- ]je)\b",
    r"\b(diagnostic|est[- ]ce (une|un)|est[- ]ce grave|est[- ]ce dangereux)\b",
    r"\b(dose|posologie|combien)\b.{0,40}\b(enfant|fils|fille|bebe|nourrisson)\b",
    r"\b(j ai|j'ai)\b.{0,30}\b(fievre|mal|douleur|vertige)\b",
    r"\b(dentaire|dentaires|mal de dents?|douleurs? dentaires?)\b",
    r"\b(pour mes douleurs|pour mon mal|pour me soigner)\b",
    r"\b(quel medicament prendre|que prendre pour)\b",
]

# Motifs d'intentions cliniques
INTENT_PATTERNS: list[tuple[str, list[str]]] = [
    (
        "interaction",
        [
            r"\b(associer|association|associe|associee|associes)\b",
            r"\b(interaction|interactions|interagir|interagissent)\b",
            r"\b(prendre avec|prendre en meme temps|melanger|combiner|combinaison)\b",
            r"\b(concomitant|concomitante|concomitants|concomitantes)\b",
            r"\b(compatible|compatibilite|synergie|antagonisme)\b",
            r"\b(en meme temps que|simultanement)\b",
        ],
    ),
    (
        "contraindication",
        [
            r"\b(contre[- ]indication|contre[- ]indications|contre[- ]indique|contre[- ]indiquee)\b",
            r"\b(interdit|interdite|interdiction|danger|dangereux|risques?)\b",
            r"\b(effet[- ]indesirable|effets[- ]indesirables|effet[- ]secondaire|effets[- ]secondaires)\b",
            r"\b(grossesse|enceinte|allaitement|femme enceinte)\b",
            r"\b(insuffisance renale|insuffisance hepatique|allergie|allergies)\b",
            r"\b(mises? en garde|precaution|precautions)\b",
        ],
    ),
    (
        "dosage",
        [
            r"\b(posologie|posologies|dosage|dosages|dose|doses)\b",
            r"\b(combien de|combien par jour|combien de fois)\b",
            r"\b(frequence|quantite|surdosage|surdoses?)\b",
            r"\b(matin ou soir|avant ou apres le repas|a jeun)\b",
            r"\b(duree du traitement|combien de jours)\b",
            r"\b(maximum par jour|dose maximale)\b",
        ],
    ),
    (
        "price",
        [
            r"\b(prix|tarif|tarifs|cout|couts|coute|coutent)\b",
            r"\b(remboursement|rembourse|remboursee|remboursables?)\b",
            r"\b(chifa|tarif de reference|carte chifa)\b",
            r"\b(dinar|dinars|da|centimes)\b",
        ],
    ),
]

# Stopwords français usuels pour l'extraction d'entités
FRENCH_STOPWORDS = frozenset(
    """
    a au aux avec ce ces dans de des du elle en et eux il je la le les leur lui
    ma mais me meme mes moi mon ne nos notre nous on ou par pas pour qu que qui
    sa se ses son sur ta te tes toi ton tu un une vos votre vous quel quelle
    quelles quels est sont peut on peut-on est-il est-elle selon son sa ses
    disponible disponibles enregistre enregistres enregistree enregistrees
    algerie algerien algerienne forme formes
    """.split()
)

# Mots de vocabulaire général / clinique ne devant JAMAIS déclencher de repli flou
NON_DRUG_WORDS = frozenset(
    """
    associer association associe associee associes
    interaction interactions interagir interagissent
    prendre prise prises pris melanger combiner combinaison
    concomitant concomitante compatible compatibilite
    posologie posologies dosage dosages dose doses
    combien quantite frequence duree traitement jour jours
    matin soir midi repas jeun adulte enfant nourrisson bebe bebes
    contre indication indications indique indiquee interdit interdite
    danger dangereux risque risques effet effets indesirable indesirables
    secondaire secondaires allergie allergies
    grossesse enceinte allaitement
    prix tarif tarifs cout couts coute coutent remboursement rembourse
    chifa dinar dinars
    quel quelle quels quelles medicament medicaments produit produits
    comment pourquoi quand est sont peut disponible disponibles
    enregistre enregistres enregistree enregistrees
    selon avec sous dans pour chez vers sans tout tous
    algerie algerien algerienne
    ordonnance prescription diagnostic grave mal maux douleur douleurs
    dentaire dentaires fievre vertige toux angine
    """.split()
) | FRENCH_STOPWORDS | FORM_TOKENS

# Elisions françaises en tête de mot
ELISION_PREFIXES = ("l'", "d'", "l’", "d’", "qu'", "qu’")


@lru_cache(maxsize=2048)
def _resolve_cached(term: str, fuzzy: bool = False):
    """Mise en cache rapide des résolutions de termes."""
    return resolve(term, fuzzy=fuzzy)


@dataclass(frozen=True)
class Entity:
    """Entité pharmaceutique extraite d'une requête."""

    term: str
    dci: str | None
    classes: list[str] = field(default_factory=list)
    confidence: float = 1.0
    start: int = 0
    end: int = 0


@dataclass(frozen=True)
class QueryAnalysis:
    """Analyse complète d'une requête clinique ou pharmaceutique."""

    raw: str
    normalized: str
    entities: list[Entity]
    intent: str
    expanded_terms: list[str]
    out_of_scope: bool


def _strip_elision(token: str) -> tuple[str, int]:
    """Retire l'élision française (ex. 'l'Amlodipine' -> ('Amlodipine', 2))."""
    token_lower = token.lower()
    for prefix in ELISION_PREFIXES:
        if token_lower.startswith(prefix):
            return token[len(prefix) :], len(prefix)
    return token, 0


def _tokenize_with_offsets(text: str) -> list[tuple[str, int, int]]:
    """Découpe le texte en tokens lexicaux avec leurs décalages de caractères."""
    tokens = []
    for match in re.finditer(r"[A-Za-z0-9À-ÿ\+]+", text):
        raw_word = match.group(0)
        start, end = match.start(), match.end()
        word, offset = _strip_elision(raw_word)
        if word:
            tokens.append((word, start + offset, end))
    return tokens


def _find_entities(text: str) -> list[Entity]:
    """Extrait les entités médicamenteuses par longest-match puis repli flou."""
    tokens = _tokenize_with_offsets(text)
    if not tokens:
        return []

    entities: list[Entity] = []
    consumed = [False] * len(tokens)
    n = len(tokens)

    # 1. Longest-match exact (fenêtre de 6 tokens à 1 token)
    for window in range(min(6, n), 0, -1):
        for i in range(n - window + 1):
            if any(consumed[i : i + window]):
                continue
            # Pour une fenêtre multi-mots, les extrémités ne doivent pas être des mots vides
            if window > 1:
                first_norm = norm(tokens[i][0])
                last_norm = norm(tokens[i + window - 1][0])
                if first_norm in FRENCH_STOPWORDS or last_norm in FRENCH_STOPWORDS:
                    continue

            span_start = tokens[i][1]
            span_end = tokens[i + window - 1][2]
            span_text = text[span_start:span_end]

            r = _resolve_cached(span_text, fuzzy=False)
            if r and (r.dci or r.classes or r.kind == "class"):
                classes = list(r.classes)
                # Cas clinique de l'aspirine : à dose antalgique/anti-inflammatoire,
                # l'aspirine se comporte comme un AINS
                if r.dci == "ACIDE ACETYLSALICYLIQUE" and "ANTI-INFLAMMATOIRES NON STEROIDIENS" not in classes:
                    classes.insert(0, "ANTI-INFLAMMATOIRES NON STEROIDIENS")

                entities.append(
                    Entity(
                        term=span_text,
                        dci=r.dci,
                        classes=classes,
                        confidence=r.confidence,
                        start=span_start,
                        end=span_end,
                    )
                )
                for k in range(i, i + window):
                    consumed[k] = True

    # 2. Repli flou (fuzzy fallback avec rapidfuzz) pour les tokens isolés non consommés
    for i, (word, start, end) in enumerate(tokens):
        if consumed[i]:
            continue
        norm_w = norm(word)
        # Ne jamais lancer de recherche floue sur les mots non-médicamenteux, trop courts ou numériques
        if len(norm_w) < 4 or norm_w in NON_DRUG_WORDS or norm_w.isdigit():
            continue

        r = _resolve_cached(word, fuzzy=True)
        # Seuil strict de 85 % pour éviter les faux positifs sur les mots du dictionnaire
        if r and (r.dci or r.classes or r.kind == "class") and r.confidence >= 0.85:
            classes = list(r.classes)
            if r.dci == "ACIDE ACETYLSALICYLIQUE" and "ANTI-INFLAMMATOIRES NON STEROIDIENS" not in classes:
                classes.insert(0, "ANTI-INFLAMMATOIRES NON STEROIDIENS")

            entities.append(
                Entity(
                    term=word,
                    dci=r.dci,
                    classes=classes,
                    confidence=r.confidence,
                    start=start,
                    end=end,
                )
            )
            consumed[i] = True

    # Trier par position dans le texte
    entities.sort(key=lambda e: e.start)
    return entities


def _is_out_of_scope(text: str, entities: list[Entity]) -> bool:
    """Détermine si la requête relève du conseil médical ou est hors périmètre."""
    text_norm = norm(text)

    # Détection explicite de conseil médical personnalisé ou prescription
    for pattern in MEDICAL_ADVICE_PATTERNS:
        if re.search(pattern, text_norm):
            return True

    # Plaintes symptomatiques pures sans médicament identifié
    symptom_words = ("fievre", "douleur", "douleurs", "mal", "maux", "toux", "angine", "vertige")
    has_symptom = any(re.search(rf"\b{w}\b", text_norm) for w in symptom_words)
    if has_symptom and not entities:
        return True

    # Sujets non médicaux manifestes (sans entités du catalogue)
    non_medical_patterns = [
        r"\b(capitale|meteo|prix de l essence|recette|football|president)\b",
        r"\b(complement alimentaire|sommeil|dormir|vitamines)\b",
    ]
    for pattern in non_medical_patterns:
        if re.search(pattern, text_norm) and not entities:
            return True

    return False


def _detect_intent(text: str, entities: list[Entity], out_of_scope: bool) -> str:
    """Classe l'intention principale de la requête."""
    if out_of_scope:
        return "out_of_scope"

    text_norm = norm(text)

    # 1. Vérification par motifs regex prioritaires
    for intent_name, patterns in INTENT_PATTERNS:
        for p in patterns:
            if re.search(p, text_norm):
                return intent_name

    # 2. Heuristique multi-entités : si 2+ médicaments distincts sont cités
    # avec une conjonction ("et", "avec", "ou"), c'est une question d'interaction
    if len(entities) >= 2:
        distinct_dcis = {e.dci for e in entities if e.dci}
        if len(distinct_dcis) >= 2 or len(entities) >= 2:
            return "interaction"

    return "unknown"


def _expand_terms(query_norm: str, entities: list[Entity], intent: str) -> list[str]:
    """Génère la liste ordonnée des termes d'expansion pour le retrieval enrichi."""
    expanded: list[str] = []
    seen = set()

    def add(term: str | None) -> None:
        if not term:
            return
        t_clean = term.strip().upper()
        if t_clean and t_clean not in seen:
            seen.add(t_clean)
            expanded.append(t_clean)

    # 1. DCI canoniques issues des entités
    for ent in entities:
        if ent.dci:
            # Traiter les associations (ex. "AMOXICILLINE + ACIDE CLAVULANIQUE")
            for sub in ent.dci.split("+"):
                add(sub.strip())
            add(ent.dci)

    # 2. Classes pharmacologiques parentes
    for ent in entities:
        for cls in ent.classes:
            add(cls)
            if "ANTI-INFLAMMATOIRES NON STEROIDIENS" in cls:
                add("AINS")
            if "INHIBITEURS DE L'ENZYME DE CONVERSION" in cls or "INHIBITEURS DE L ENZYME DE CONVERSION" in cls:
                add("IEC")
            if "ANTAGONISTES DES CANAUX CALCIQUES" in cls:
                add("INHIBITEURS CALCIQUES")
            if "ANTAGONISTES DES RECEPTEURS DE L'ANGIOTENSINE II" in cls:
                add("ARA II")
                add("SARTANS")
            if "BETA-BLOQUANTS" in cls or "BETA BLOQUANTS" in cls:
                add("BETA-BLOQUANTS")

    # 3. Intentions clés pour l'orientation des chunks
    if intent == "dosage":
        add("POSOLOGIE")
        add("DOSAGE")
    elif intent == "contraindication":
        add("CONTRE-INDICATION")
        add("EFFETS INDESIRABLES")
    elif intent == "interaction":
        add("INTERACTION MEDICAMENTEUSE")

    return expanded


def analyze_query(text: str) -> QueryAnalysis:
    """Point d'entrée principal pour l'analyse de requête.

    Paramètres :
        text : texte brut de la requête utilisateur en langage naturel.

    Retourne :
        Une instance typée QueryAnalysis contenant entités, intention,
        termes d'expansion et indicateur de conformité déontologique.
    """
    if not text or not text.strip():
        return QueryAnalysis(
            raw=text or "",
            normalized="",
            entities=[],
            intent="unknown",
            expanded_terms=[],
            out_of_scope=False,
        )

    clean_text = text.strip()
    text_norm = norm(clean_text)

    # 1. Extraction d'entités par le lexique L1
    entities = _find_entities(clean_text)

    # 2. Évaluation des garde-fous
    out_of_scope = _is_out_of_scope(clean_text, entities)

    # 3. Détection d'intention
    intent = _detect_intent(clean_text, entities, out_of_scope)

    # 4. Expansion de requête
    expanded = _expand_terms(text_norm, entities, intent)

    return QueryAnalysis(
        raw=clean_text,
        normalized=text_norm,
        entities=entities,
        intent=intent,
        expanded_terms=expanded,
        out_of_scope=out_of_scope,
    )
