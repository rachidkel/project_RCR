# Note de conformité : Arrêt de la collecte automatisée de l'ANPP et politique de consultation manuelle

**Date d'émission** : 21 novembre 2026  
**Auteur** : Mohamed Ali BAGHRICHE (pour l'équipe Pharmeazor)  
**Destinataire** : Équipe enseignante du projet RCR  
**Statut** : Appliqué immédiatement — Priorité Haute  

---

## 1. Décision et retrait immédiat

Conformément à la consigne formelle formulée par l'enseignant le 21/11/2026 à 12:23 (*« Alerte : Collecte automatisée de l'ANPP (rcp.anpp.dz) : la règle est la collecte manuelle uniquement, à appliquer dès maintenant »*) :

1. **Arrêt immédiat** de tout processus de collecte automatisée ou scriptée sur la plateforme `rcp.anpp.dz`.
2. **Retrait complet du dépôt** du script de collecte automatisée `scripts/14_collect_anpp.py` (suppression enregistrée dans Git).
3. **Passage exclusif à la collecte manuelle** pour tout ajout documentaire futur concernant l'ANPP.

---

## 2. Historique et traçabilité de l'opération ponctuelle

Pour des raisons de transparence et d'audit académique, les paramètres de l'unique exécution passée sont consignés ci-dessous :

- **Date d'exécution** : Samedi 21 novembre 2026 entre 05h00 et 06h00 (CET).
- **Protocole utilisé** : Émulation du flux Livewire/CSRF avec requêtes séquentielles HTTP POST.
- **Cadence appliquée** : Pause stricte de temporisation de **3,0 secondes** entre chaque requête pour éviter toute surcharge d'infrastructure.
- **Périmètre ciblé** : Exclusivement les molécules du projet (40 médicaments).
- **Volume collecté** : **33 RCP officiels** au format PDF (représentant 307 rubriques cliniques extraites dans `data/processed/anpp/`).
- **Aucune tentative d'évasion** : Le `robots.txt` officiel de `rcp.anpp.dz` (autorisant la consultation publique) a été respecté, aucun contournement de contrôle d'accès ou de sécurité n'a eu lieu.

---

## 3. Règle de conservation des données collectées (Usage d'étude exclusif)

Pour les 33 documents RCP déjà présents dans le dépôt :
- **Usage d'étude académique strict** : Ces documents et extraits sont conservés uniquement en local et dans l'environnement du projet pour servir de vérité terrain (*ground truth*) à l'évaluation du système de questions-réponses médicales.
- **Conservation des passages utiles au test** : Seules les rubriques pertinentes (4.1 indications, 4.2 posologies, 4.3 contre-indications, 4.8 effets indésirables) sont exploitées pour le banc d'essai.
- **Interdiction formelle de republication** : Aucun fichier PDF ni texte intégral brut ne fera l'objet d'une republication, d'une redistribution commerciale ou d'un hébergement sur une plateforme tierce non autorisée.

---

## 4. Politique pour les semaines à venir (Semaine 3 et suivantes)

- Toute nouvelle notice ou mise à jour de RCP de l'ANPP sera obligatoirement téléchargée **manuellement par un membre de l'équipe**, via le navigateur web standard, fichier par fichier.
- Le fichier source portera dans ses métadonnées le nom de l'opérateur humain, l'URL de la page consultée et la date exacte de consultation.
