# Rapport Hebdomadaire - Semaine 1 (13/11)

## 1. Ce qui a avancé (faits précis)
- **Mission & Question-test** : Rédigées dans `mission_QST.md`.
- **Liste des 40 médicaments** : 39/40 vérifiés dans la nomenclature officielle (MIPH).
- **Thésaurus ANSM** : 801 substances et 2561 interactions parsées et nettoyées dans un fichier JSON structuré.
- **Test LLM seul** : 5 questions testées (Directe, Croisée, Contexte, Piège, Hors périmètre) sur `gpt-oss-120b`.

## 2. Ce qui bloque
- Aucun blocage technique majeur. La collecte du Thésaurus a généré quelques artefacts (50 entrées) qui seront filtrés en Semaine 2.

## 3. Prochaines étapes (Semaine 2)
- Découpage des documents (chunking).
- Calcul des embeddings (BGE-M3) et création de la base FAISS.
- Comparaison BM25 vs Recherche sémantique.

## 4. Résultats du Test LLM Seul (Preuve d'hallucination)
| Question | A inventé un chiffre ? | A cité une source ? | A refusé (hors périmètre) ? |
|---|---|---|---|
| Q1 (Paracétamol) | Oui (doses sans source) | Non | Non |
| Q2 (Ibuprofène+Aspirine) | Oui (doses inventées) | Non | Non |
| Q3 (Amlodipine+Ibuprofène) | Oui (+2 à +5 mmHg) | Oui (Fausses sources) | Non |
| Q4 (Conflit de doses) | Oui (exemple inventé) | Non | Non |
| Q5 (Douleurs dentaires) | - | - | **ÉCHEC (A donné un conseil)** |

## 5. Contribution des membres
- **[Membre 1]** : Parsing Nomenclature et vérification des 40 médicaments.
- **[Membre 2]** : Parsing Thésaurus ANSM, test LLM, documentation.
- *(Ajoutez vos noms)*

## 6. Outils IA utilisés cette semaine
- **Groq / openai/gpt-oss-120b** : Test du modèle seul (6 requêtes au total, dont 1 de test de connexion). Aucune donnée sensible envoyée.