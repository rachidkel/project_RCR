
"""Build the Pharmeazor knowledge graph from the L1 lexicon
and the ANSM thesaurus.
"""

import json
import sys
import re
from pathlib import Path
from collections import defaultdict

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from pharmeazor.graph import KnowledgeGraph


LEXICON_PATH = (
    ROOT / "data" / "processed" / "week_3" / "lexicon.json"
)

THESAURUS_PATH = (
    ROOT / "data" / "interim" / "thesaurus"
    / "interactions_medicamenteuses.json"
)

OUTPUT_PATH = (
    ROOT / "data" / "processed" / "week_3"
    / "knowledge_graph.json"
)


def load_json(path):
    if not path.exists():
        raise FileNotFoundError(f"File not found: {path}")

    with path.open("r", encoding="utf-8") as file:
        return json.load(file)


def normalize(value):
    return KnowledgeGraph._normalize(value)


def split_values(value):
    """Convert strings or lists into normalized terms."""
    if not value:
        return []

    if isinstance(value, list):
        values = value
    elif isinstance(value, str):
        values = re.split(r"[;,\n|]", value)
    else:
        return []

    return [
        normalize(item)
        for item in values
        if isinstance(item, str) and normalize(item)
    ]


def build_graph():
    print("\nLoading project data...")

    lexicon = load_json(LEXICON_PATH)
    thesaurus = load_json(THESAURUS_PATH)

    if not isinstance(lexicon, dict):
        raise TypeError("The lexicon must be a JSON dictionary.")

    if not isinstance(thesaurus, list):
        raise TypeError("The Thesaurus must be a JSON list.")

    classes_data = lexicon.get("classes", {})
    aliases_data = lexicon.get("aliases", {})

    if not isinstance(classes_data, dict):
        raise TypeError("The lexicon classes field must be a dictionary.")

    if not isinstance(aliases_data, dict):
        raise TypeError("The lexicon aliases field must be a dictionary.")

    kg = KnowledgeGraph()

    # Maps aliases to their canonical DCI or class.
    dci_aliases = {}
    class_aliases = {}

    class_names = set()
    dci_names = set()

    # --------------------------------------------------
    # 1. BUILD THERAPEUTIC CLASSES AND MEMBERS
    # --------------------------------------------------

    print("Building therapeutic classes and memberships...")

    for class_name, information in classes_data.items():
        class_id = normalize(class_name)

        if not class_id:
            continue

        if not isinstance(information, dict):
            information = {}

        class_names.add(class_id)

        kg.add_entity(
            class_id,
            "class",
            label=class_id,
        )

        members = split_values(information.get("members", []))

        for member in members:
            if not member:
                continue

            dci_names.add(member)

            kg.add_entity(member, "dci", label=member)
            kg.add_relation(member, class_id, "member_of")

        # Aliases defined directly inside the class dictionary.
        for alias in split_values(information.get("aliases", [])):
            if alias and alias != class_id:
                class_aliases[alias] = class_id

    # --------------------------------------------------
    # 2. BUILD DCI ALIASES AND CLASS ALIASES
    # --------------------------------------------------

    print("Building aliases...")

    for alias_name, information in aliases_data.items():
        if not isinstance(information, dict):
            continue

        alias = normalize(alias_name)
        dci = normalize(information.get("dci"))
        classes = split_values(information.get("classes", []))

        if not alias:
            continue

        if dci:
            dci_names.add(dci)

            kg.add_entity(dci, "dci", label=dci)

            if alias != dci:
                kg.add_entity(alias, "alias", label=alias)
                kg.add_relation(alias, dci, "alias_of")
                dci_aliases[alias] = dci

            for class_name in classes:
                if not class_name:
                    continue

                class_names.add(class_name)

                kg.add_entity(
                    class_name,
                    "class",
                    label=class_name,
                )
                kg.add_relation(dci, class_name, "member_of")

        elif classes:
            # An alias may refer to one or several classes.
            kg.add_entity(alias, "alias", label=alias)

            for class_name in classes:
                class_names.add(class_name)

                kg.add_entity(
                    class_name,
                    "class",
                    label=class_name,
                )
                kg.add_relation(alias, class_name, "alias_of")
                class_aliases[alias] = class_name

    # --------------------------------------------------
    # 3. RESOLVE CLASS ALIASES
    # --------------------------------------------------

    def resolve_class(value):
        value = normalize(value)

        if value in class_names:
            return value

        return class_aliases.get(value)

    def resolve_dci(value):
        value = normalize(value)
        return dci_aliases.get(value, value)

    # --------------------------------------------------
    # 4. READ ANSM THESAURUS
    # --------------------------------------------------

    print("Building ANSM interactions...")

    source_name = "ANSM THESAURUS"

    kg.add_entity(
        source_name,
        "source",
        label=source_name,
    )

    interaction_count = 0
    class_membership_count = 0

    for fiche_index, fiche in enumerate(thesaurus, start=1):
        if not isinstance(fiche, dict):
            continue

        principal_raw = fiche.get("substance_principale", "")
        principal = normalize(principal_raw)

        if not principal:
            continue

        # A fiche with members describes a class.
        members = split_values(fiche.get("membres", ""))

        principal_class = resolve_class(principal)

        if principal_class or members:
            principal = principal_class or principal

            kg.add_entity(
                principal,
                "class",
                label=principal,
            )

            class_names.add(principal)

            # Build membership relations from the thesaurus too.
            for member in members:
                member = resolve_dci(member)

                if not member:
                    continue

                kg.add_entity(member, "dci", label=member)

                kg.add_relation(
                    member,
                    principal,
                    "member_of",
                )

                class_membership_count += 1

        else:
            principal = resolve_dci(principal)

            kg.add_entity(
                principal,
                "dci",
                label=principal,
            )

        # Retain the documentary metadata.
        if fiche.get("voir_aussi"):
            kg.graph.nodes[principal]["voir_aussi"] = (
                fiche["voir_aussi"]
            )

        if fiche.get("membres"):
            kg.graph.nodes[principal]["membres"] = (
                fiche["membres"]
            )

        fiche_interactions = fiche.get("interactions", [])

        if not isinstance(fiche_interactions, list):
            continue

        for interaction_index, interaction in enumerate(
            fiche_interactions,
            start=1,
        ):
            if not isinstance(interaction, dict):
                continue

            target_raw = interaction.get("substance_cible", "")
            target = normalize(target_raw)

            if not target:
                continue

            # Resolve target to its canonical class or DCI.
            target_class = resolve_class(target)

            if target_class:
                target = target_class
                target_type = "class"
            elif target in class_names:
                target_type = "class"
            else:
                target = resolve_dci(target)
                target_type = "dci"

            level = interaction.get("niveau", "")
            description = interaction.get("description", "")

            interaction_id = (
                f"INTERACTION_{fiche_index}_{interaction_index}"
            )

            kg.add_entity(
                interaction_id,
                "interaction",
                label=f"{principal} - {target}",
                level=level,
                description=description,
            )

            # Link interaction to its principal entity.
            kg.add_relation(
                interaction_id,
                principal,
                "involves",
                role="principal",
            )

            # Link interaction to its target entity.
            kg.add_entity(
                target,
                target_type,
                label=target,
            )

            kg.add_relation(
                interaction_id,
                target,
                "involves",
                role="target",
            )

            # Link interaction to its documentary source.
            kg.add_relation(
                interaction_id,
                source_name,
                "documented_in",
            )

            interaction_count += 1

    # --------------------------------------------------
    # 5. SAVE GRAPH
    # --------------------------------------------------

    OUTPUT_PATH.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    kg.save(OUTPUT_PATH)

    # --------------------------------------------------
    # 6. DISPLAY STATISTICS
    # --------------------------------------------------

    statistics = kg.stats()

    print("\n" + "=" * 55)
    print("PHARMEAZOR KNOWLEDGE GRAPH")
    print("=" * 55)

    print("Therapeutic classes:", len(class_names))
    print("DCI nodes:", len(dci_names))
    print("DCI-class memberships:", sum(
        1
        for _, _, data in kg.graph.edges(data=True)
        if data.get("relation") == "member_of"
    ))
    print("Thesaurus membership records:", class_membership_count)
    print("ANSM interaction records:", interaction_count)

    print("\nGraph statistics:")
    print(json.dumps(
        statistics,
        indent=4,
        ensure_ascii=False,
    ))

    print("\nGraph saved to:")
    print(OUTPUT_PATH)

    print("\nBuild completed successfully.")

    return kg


if __name__ == "__main__":
    build_graph()
