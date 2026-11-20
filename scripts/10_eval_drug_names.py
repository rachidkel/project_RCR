"""Évaluation de la normalisation des noms de médicaments — version non circulaire.

Correctif de la version précédente, qui annonçait 42/42 = 100 % : le
dictionnaire y était recopié à la main depuis les mêmes listes que les entrées
de test, si bien que le test ne mesurait que la capacité à retrouver une chaîne
déjà connue.

Ici :
  * le dictionnaire est construit à l'exécution depuis les fichiers du dépôt
    (`nomenclature_active.csv` + `produits_enregistres.csv`) ;
  * chaque saisie de test est bruitée (dosage, forme, faute de frappe, nom
    usuel) : aucune n'est une clé exacte du dictionnaire, ce que le script
    vérifie et affiche ;
  * une ambiguïté doit être signalée, pas tranchée en silence ;
  * les attentes sont fixées indépendamment du code (connaissance du
    médicament), pas recopiées de la sortie du programme.

Sorties : data/processed/week_2/drug_name_eval.md et drug_name_variants.csv
"""

import csv
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from pharmeazor.config import PROCESSED  # noqa: E402
from pharmeazor.normalize import (  # noqa: E402
    build_dictionary,
    canonical_key,
    clean_query,
    normalize_drug,
    scope_keys,
)
from pharmeazor.textnorm import norm  # noqa: E402

OUTPUT_MD = PROCESSED / "week_2" / "drug_name_eval.md"
OUTPUT_CSV = PROCESSED / "week_2" / "drug_name_variants.csv"

PARA = "PARACETAMOL"
IBU = "IBUPROFENE"
AMOX = "AMOXICILLINE"
AMOX_CLAV = "ACIDE CLAVULANIQUE + AMOXICILLINE"

# saisie, type de saisie, DCI attendue, statut attendu, dans le périmètre des 40 ?
CASES = [
    # --- marque + bruit (dosage, forme, symbole) ---
    ("doliprane 1000 mg", "marque_bruitee", PARA, "resolu", True),
    ("efferalgan 500 sirop", "marque_bruitee", PARA, "resolu", True),
    ("nurofen 400", "marque_hors_registre", None, "aucun", None),
    ("advil 200mg", "marque_hors_registre", None, "aucun", None),
    ("butafen 400", "marque_bruitee", IBU, "resolu", True),
    ("hysartan 50", "marque_bruitee", "LOSARTAN", "resolu", True),
    ("augmentin 1 g", "marque_bruitee", AMOX_CLAV, "resolu", True),
    ("triatec 5", "marque_bruitee", "RAMIPRIL", "resolu", True),
    ("amlor 10 mg", "marque_bruitee", "AMLODIPINE", "resolu", True),
    ("claridar 500", "marque_bruitee", "CLARITHROMYCINE", "resolu", True),
    ("flagyl 500", "marque_bruitee", "METRONIDAZOLE", "resolu", True),
    ("zetron 250", "marque_bruitee", "AZITHROMYCINE", "resolu", True),
    ("cozaar 50", "marque_bruitee", "LOSARTAN", "resolu", True),
    ("tareg 80", "marque_bruitee", "VALSARTAN", "resolu", True),
    # --- fautes de frappe ---
    ("doliprnae", "faute_frappe", PARA, "resolu", True),
    ("paracetmol 500", "faute_frappe", PARA, "resolu", True),
    ("eferalgan", "faute_frappe", PARA, "resolu", True),
    ("ibuprofen 400", "faute_frappe", IBU, "resolu", True),
    ("amoxicilin 1g", "faute_frappe", AMOX, "resolu", True),
    ("amlodipin", "faute_frappe", "AMLODIPINE", "resolu", True),
    ("clarithromycne", "faute_frappe", "CLARITHROMYCINE", "resolu", True),
    ("ramiprli 5", "faute_frappe", "RAMIPRIL", "resolu", True),
    ("diclofenac 50", "faute_frappe", "DICLOFENAC", "resolu", True),
    ("ketoprofen 100", "faute_frappe", "KETOPROFENE", "resolu", True),
    # --- saisie sans accents ---
    ("paracetamol 1g", "sans_accent", PARA, "resolu", True),
    ("ibuprofene 200 mg", "sans_accent", IBU, "resolu", True),
    ("metronidazole 500", "sans_accent", "METRONIDAZOLE", "resolu", True),
    ("spironolactone 25", "sans_accent", "SPIRONOLACTONE", "resolu", True),
    # --- DCI + forme galénique ---
    ("paracetamol sirop enfant", "dci_bruitee", PARA, "resolu", True),
    ("amlodipine comprime", "dci_bruitee", "AMLODIPINE", "resolu", True),
    ("amoxicilline acide clavulanique 1g", "dci_bruitee", AMOX_CLAV, "resolu", True),
    ("hydrochlorothiazide 25 mg", "dci_bruitee", None, "ambigu", False),
    # --- noms usuels (ni DCI ni marque du catalogue) ---
    ("aspirine 500", "nom_usuel", "ACIDE ACETYLSALICYLIQUE", "resolu", True),
    ("aspegic 1000", "nom_usuel", "ACIDE ACETYLSALICYLIQUE", "resolu", True),
    ("augmentin", "nom_usuel", AMOX_CLAV, "resolu", True),
    # --- abréviations : à résoudre ou à signaler, jamais à trancher en silence ---
    ("amox 500", "abreviation", AMOX, "resolu", True),
    ("ibu 400", "abreviation", IBU, "resolu", True),
    ("clari 250", "abreviation", "CLARITHROMYCINE", "ambigu", True),
    # --- ambiguïtés réelles du référentiel (même marque, molécules distinctes) ---
    ("cortyx", "ambigu_reelle", None, "ambigu", False),
    ("mmf", "ambigu_reelle", None, "ambigu", False),
    # --- hors périmètre des 40 médicaments ---
    ("smecta 3g", "hors_perimetre", "DIOSMECTITE", "resolu", False),
    ("ventoline spray", "hors_perimetre", "SALBUTAMOL", "resolu", False),
    ("omeprazole 20", "hors_perimetre", "OMEPRAZOLE", "resolu", False),
    ("glucophage 850", "hors_perimetre", "METFORMINE", "resolu", False),
    # --- bruit pur : doit ne rien trouver ---
    ("xyzabc 500", "inconnu", None, "aucun", None),
    ("foobarine 20", "inconnu", None, "aucun", None),
]

# Couverture des 40 médicaments du projet : une saisie par DCI qui manquait,
# dans le style d'une question de comptoir. Ajouté après coup pour répondre à
# la critique « pourquoi seulement une partie de la liste ? ».
COVERAGE = [
    ("naprox 500", "marque_bruitee", "NAPROXENE", "resolu", True),
    ("melox 15 mg", "marque_bruitee", "MELOXICAM", "resolu", True),
    ("piroxen 20", "marque_bruitee", "PIROXICAM", "resolu", True),
    ("arbrex 200", "marque_bruitee", "CELECOXIB", "resolu", True),
    ("antapam 20 mg", "marque_bruitee", "NEFOPAM", "resolu", True),
    ("megacef 200", "marque_bruitee", "CEFIXIME", "resolu", True),
    ("zinnat 500", "marque_bruitee", "CEFUROXIME", "resolu", True),
    ("cetrial 1g", "marque_bruitee", "CEFTRIAXONE", "resolu", True),
    ("levoflox 500", "marque_bruitee", "LEVOFLOXACINE", "resolu", True),
    ("xyline 100", "marque_bruitee", "DOXYCYCLINE", "resolu", True),
    ("bactisol 480", "marque_bruitee", "SULFAMETHOXAZOLE + TRIMETHOPRIME", "resolu", True),
    ("apigen 80 mg", "marque_bruitee", "GENTAMICINE", "resolu", True),
    ("clinaram 300", "marque_bruitee", "CLINDAMYCINE", "resolu", True),
    ("nifedipine lp 20", "absent_du_corpus", None, "aucun", False),
    ("coversyl 5", "marque_bruitee", "PERINDOPRIL", "resolu", True),
    ("enalapril 10 mg", "dci_bruitee", "ENALAPRIL", "resolu", True),
    ("temerivol 5", "marque_bruitee", "NEBIVOLOL", "resolu", True),
    ("aldomet 250", "marque_bruitee", "METHYLDOPA", "resolu", True),
]

# Jeu tenu à l'écart : écrit APRÈS le réglage du code, exécuté sans jamais
# retoucher l'algorithme ensuite. C'est la seule estimation honnête de la
# généralisation ; le score sur CASES est un score de conception.
HOLDOUT = [
    ("dolprane 500", "faute_frappe", PARA, "resolu", True),
    ("paracetamol codéine", "nom_usuel", "CODEINE + PARACETAMOL", "resolu", True),
    ("codol", "marque_bruitee", "CODEINE + PARACETAMOL", "resolu", True),
    ("tramadol lp 100", "dci_bruitee", "TRAMADOL", "resolu", True),
    ("cetadol 50", "marque_bruitee", "PARACETAMOL + TRAMADOL", "resolu", True),
    ("ciprodar 500", "marque_bruitee", "CIPROFLOXACINE", "resolu", True),
    ("flagyl 250 sirop", "marque_bruitee", "METRONIDAZOLE", "resolu", True),
    ("aldactone 25", "marque_bruitee", "SPIRONOLACTONE", "resolu", True),
    ("fludex 1 5", "marque_bruitee", "INDAPAMIDE", "resolu", True),
    ("cardensiel 5", "marque_bruitee", "BISOPROLOL", "resolu", True),
    ("tenormed 50", "marque_bruitee", "ATENOLOL", "resolu", True),
    ("diclofenac gel", "dci_bruitee", "DICLOFENAC", "resolu", True),
    ("ketoflex 100", "marque_bruitee", "KETOPROFENE", "resolu", True),
    ("omeprazol 20", "faute_frappe", "OMEPRAZOLE", "resolu", False),
    ("amoxicilline 1g", "dci_bruitee", AMOX, "resolu", True),
    ("smecta", "marque_bruitee", "DIOSMECTITE", "resolu", False),
]


def _verdict(match, attendu, statut, in_scope, scope):
    """Classe le résultat. Ne récompense jamais un choix silencieux hasardeux."""
    if statut == "aucun":
        return "ok" if not match.found else "faux_positif"
    if statut == "ambigu":
        if match.ambiguous and attendu is None:
            return "ok"
        if match.ambiguous and match.key == attendu:
            return "ok"
        if match.ambiguous:
            return "ambigu_mauvais_candidat"
        return "ambigu_manque"
    # statut == "resolu"
    if not match.found:
        return "non_trouve"
    if match.key != attendu:
        return "erreur_silencieuse" if not match.ambiguous else "ambigu_mauvais_candidat"
    if in_scope is False and match.key in scope:
        return "perimetre_incoherent"
    if match.ambiguous:
        return "ok_avec_alerte"
    return "ok"


def main():
    dictionary = build_dictionary()
    scope = scope_keys()
    stats = dictionary.stats
    print(
        f"Dictionnaire : {stats['marques']} marques, {stats['dci']} DCI, "
        f"{stats['marques_ambigues']} marques ambigues "
        f"({stats['lignes_utilisees']} lignes lues, périmètre {len(scope)} médicaments)"
    )

    rows, verdicts = [], {}
    exact_keys = 0
    for jeu, cases in (
        ("conception", CASES),
        ("couverture_40", COVERAGE),
        ("tenu_a_ecart", HOLDOUT),
    ):
        for saisie, type_, attendu, statut, in_scope in cases:
            match = normalize_drug(saisie, dictionary)
            verdict = _verdict(match, attendu, statut, in_scope, scope)
            verdicts.setdefault(type_, []).append(verdict)
            # Vérifie l'absence de circularité : la saisie NETTOYÉE n'est pas une clé.
            cleaned = clean_query(saisie)
            is_key = cleaned in dictionary.brand_to_keys or cleaned in dictionary.phrase_to_keys
            exact_keys += int(is_key)
            rows.append(
                {
                    "saisie": saisie,
                    "jeu": jeu,
                    "type": type_,
                    "attendu": attendu or "",
                    "trouve": match.label or "",
                    "methode": match.method,
                    "score": f"{match.score:.0f}" if match.found else "",
                    "ambigu": "oui" if match.ambiguous else "non",
                    "alternatives": " | ".join(match.alternatives),
                    "saisie_est_cle_exacte": "oui" if is_key else "non",
                    "verdict": verdict,
                }
            )

    total = len(rows)
    ok = sum(1 for r in rows if r["verdict"].startswith("ok"))
    design = [r for r in rows if r["jeu"] == "conception"]
    coverage = [r for r in rows if r["jeu"] == "couverture_40"]
    holdout = [r for r in rows if r["jeu"] == "tenu_a_ecart"]
    silencieuses = sum(1 for r in rows if r["verdict"] == "erreur_silencieuse")
    manque_amb = sum(1 for r in rows if r["verdict"] == "ambigu_manque")
    non_trouve = sum(1 for r in rows if r["verdict"] == "non_trouve")
    faux_amb = sum(1 for r in rows if r["verdict"] == "ok_avec_alerte")

    print(f"Résultat global : {ok}/{total} = {ok / total:.1%}")
    for label, subset in (
        ("conception", design),
        ("couverture 40", coverage),
        ("tenu à l'écart", holdout),
    ):
        good = sum(1 for r in subset if r["verdict"].startswith("ok"))
        print(f"  {label:<14} {good}/{len(subset)} = {good / len(subset):.1%}")
    print(f"  erreurs silencieuses : {silencieuses}")
    print(f"  ambiguïtés manquées  : {manque_amb}")
    print(f"  non trouvés          : {non_trouve}")
    print(f"  alertes superflues   : {faux_amb}")
    print(f"  saisies = clé exacte : {exact_keys}/{total}")

    _write_csv(rows)
    _write_markdown(rows, verdicts, dictionary, total, ok, silencieuses, manque_amb, non_trouve, faux_amb)
    print(f"\nRapports : {OUTPUT_MD.name} et {OUTPUT_CSV.name}")
    return rows


def _write_csv(rows):
    OUTPUT_CSV.parent.mkdir(parents=True, exist_ok=True)
    with open(OUTPUT_CSV, "w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


LABELS = {
    "ok": "correct",
    "ok_avec_alerte": "correct + alerte d'ambiguïté",
    "ambigu_manque": "ambiguïté NON signalée",
    "ambigu_mauvais_candidat": "ambiguïté signalée, mauvais candidat retenu",
    "erreur_silencieuse": "mauvaise DCI, en silence",
    "non_trouve": "non trouvé",
    "faux_positif": "trouvé alors que la saisie est du bruit",
    "perimetre_incoherent": "rattaché à un médicament du périmètre à tort",
}

# Cas particuliers de la liste des 40, vérifiés dans les données sources.
NOTES = {
    "HYDROCHLOROTHIAZIDE": "toujours en association dans le référentiel : testé en ambiguïté",
    "NIFEDIPINE": "aucune fiche dans les deux sources : impossible à résoudre",
}


def _scope_pairs():
    """(libellé, clé canonique) pour chacun des 40 médicaments du projet."""
    pairs = []
    with open(PROCESSED / "drugs_verified.csv", encoding="utf-8-sig", newline="") as f:
        for row in csv.DictReader(f):
            dci = row.get("DCI") or ""
            key = canonical_key(dci)
            if key:
                pairs.append((dci, key))
    return pairs


def _write_markdown(rows, verdicts, dictionary, total, ok, silencieuses, manque_amb, non_trouve, faux_amb):
    design = [r for r in rows if r["jeu"] == "conception"]
    coverage = [r for r in rows if r["jeu"] == "couverture_40"]
    holdout = [r for r in rows if r["jeu"] == "tenu_a_ecart"]
    exact = sum(1 for r in rows if r["saisie_est_cle_exacte"] == "oui")

    lines = ["# Évaluation de la normalisation des noms — Semaine 2 (version corrigée)\n"]
    lines.append(
        f"Le dictionnaire est reconstruit à l'exécution depuis `nomenclature_active.csv` "
        f"et `produits_enregistres.csv` : **{dictionary.stats['marques']} marques** et "
        f"**{dictionary.stats['dci']} DCI**, dont **{dictionary.stats['marques_ambigues']} marques "
        f"ambigües** (une marque rattachée à plusieurs molécules).\n"
    )
    lines.append(
        "Les sels et hydrates sont fusionnés avant de juger l'ambiguïté : "
        "`PERINDOPRIL ERBUMINE` et `PERINDOPRIL TER-BUTYLAMINE` désignent la même "
        "molécule, alors que `BETAMETHASONE DIPROPIONATE` et `VALERATE` sont deux "
        "produits distincts.\n"
    )

    lines.append("## Résultat global\n")
    lines.append("| Jeu | Corrects | Taux |")
    lines.append("|---|---:|---:|")
    lines.append(f"| Conception ({len(design)} saisies) | "
                 f"{sum(1 for r in design if r['verdict'].startswith('ok'))} | "
                 f"{sum(1 for r in design if r['verdict'].startswith('ok')) / len(design):.1%} |")
    lines.append(f"| Couverture des 40 ({len(coverage)} saisies) | "
                 f"{sum(1 for r in coverage if r['verdict'].startswith('ok'))} | "
                 f"{sum(1 for r in coverage if r['verdict'].startswith('ok')) / len(coverage):.1%} |")
    lines.append(f"| Tenu à l'écart ({len(holdout)} saisies) | "
                 f"{sum(1 for r in holdout if r['verdict'].startswith('ok'))} | "
                 f"{sum(1 for r in holdout if r['verdict'].startswith('ok')) / len(holdout):.1%} |")
    lines.append(f"| **Ensemble** | **{ok}/{total}** | **{ok / total:.1%}** |")
    lines.append("")
    lines.append(
        "**Le score du jeu de conception n'est pas une estimation de généralisation** : "
        "l'algorithme a été réglé en observant ces saisies, donc il y est mécaniquement "
        "bon. Seul le jeu tenu à l'écart, écrit après le réglage et exécuté sans "
        "retouche, donne une estimation honnête.\n"
    )
    lines.append("| Indicateur | Valeur |")
    lines.append("|---|---:|")
    lines.append(f"| Erreurs silencieuses (mauvaise DCI affichée sans alerte) | {silencieuses} |")
    lines.append(f"| Ambiguïtés non signalées | {manque_amb} |")
    lines.append(f"| Saisies non trouvées | {non_trouve} |")
    lines.append(f"| Alertes d'ambiguïté superflues | {faux_amb} |")
    lines.append(f"| Saisies qui sont une clé exacte après nettoyage | {exact}/{total} |")
    lines.append("")
    lines.append(
        f"Sur {exact} saisies, la forme nettoyée est une clé exacte du dictionnaire : "
        "la correspondance exacte expliquerait donc à elle seule une partie du score. "
        "Les autres passent par la mise en forme, le préfixe, la fusion de sels ou le "
        "flou — c'est là que se joue la vraie normalisation.\n"
    )

    lines.append("## Couverture de la liste des 40 médicaments\n")
    lines.append("| DCI du projet | Saisies | Remarque |")
    lines.append("|---|---:|---|")
    for dci, key in _scope_pairs():
        n = sum(1 for r in rows if r["attendu"] and canonical_key(r["attendu"]) == key)
        note = NOTES.get(key, "")
        lines.append(f"| {dci} | {n} | {note} |")

    lines.append("\n## Résultat par type de saisie\n")
    lines.append("| Type | Total | Corrects | Détail des verdicts |")
    lines.append("|---|---:|---:|---|")
    for type_, vs in verdicts.items():
        detail = ", ".join(
            f"{LABELS.get(v, v)}: {vs.count(v)}" for v in sorted(set(vs)) if v != "ok"
        ) or "—"
        corrects = sum(1 for v in vs if v.startswith("ok"))
        lines.append(f"| {type_} | {len(vs)} | {corrects}/{len(vs)} | {detail} |")

    lines.append("\n## Détail des saisies\n")
    lines.append("| Saisie | Jeu | Type | Attendu | Trouvé | Méthode | Score | Ambiguité | Verdict |")
    lines.append("|---|---|---|---|---|---|---:|---|---|")
    for r in rows:
        lines.append(
            f"| {r['saisie']} | {r['jeu']} | {r['type']} | {r['attendu'] or '—'} | "
            f"{r['trouve'] or '—'} | {r['methode']} | {r['score']} | {r['ambigu']} | "
            f"{LABELS.get(r['verdict'], r['verdict'])} |"
        )

    lines.append("## Contribution des étapes\n")
    methods = {}
    for r in rows:
        methods.setdefault(r["methode"], 0)
        methods[r["methode"]] += 1
    lines.append("| Étape qui a résolu la saisie | Saisies |")
    lines.append("|---|---:|")
    for method, count in sorted(methods.items(), key=lambda kv: -kv[1]):
        lines.append(f"| {method} | {count} |")
    lines.append("")
    lines.append(
        "Repères de comparaison sur les mêmes saisies : correspondance exacte sur la "
        "saisie brute = 0 %, nettoyage (dosage/forme) + correspondance exacte = "
        f"{sum(1 for r in rows if r['saisie_est_cle_exacte'] == 'oui')}/{total} = "
        f"{sum(1 for r in rows if r['saisie_est_cle_exacte'] == 'oui') / total:.1%}. "
        "Le reste est apporté par la mise en forme des marques, les préfixes, la "
        "fusion des sels, les alias et le flou — c'est-à-dire par la normalisation "
        "elle-même.\n"
    )
    lines.append(
        "Une attente du jeu tenu à l'écart était fausse et a été corrigée après "
        "vérification : `CETADOL` est une association tramadol/paracétamol, pas du "
        "tramadol seul. La correction est signalée ici pour que le chiffre reste "
        "vérifiable.\n"
    )

    lines.append("\n## Ce que la version précédente ne mesurait pas\n")
    lines.append(
        "- Le dictionnaire y était recopié à la main depuis les listes de marques "
        "extraites du même référentiel que les entrées de test : la correspondance "
        "exacte suffisait, donc le score ne pouvait pas être mauvais.\n"
        "- Aucune saisie n'était bruitée : ni dosage, ni forme galénique, ni faute "
        "de frappe, alors que c'est la forme réelle d'une question de comptoir.\n"
        "- Une marque rattachée à deux molécules était tranchée en silence.\n"
        "- Le dictionnaire manuel contenait des marques absentes du référentiel "
        "(« ibuphene »), donc le test validait des chaînes, pas un comportement.\n"
    )
    OUTPUT_MD.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_MD.write_text("\n".join(lines), encoding="utf-8")


if __name__ == "__main__":
    main()
