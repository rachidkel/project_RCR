Projet RCR : Pharmeazor


# 1. Mission du Système
Le projet vise à construire un assistant intelligent et fiable destiné aux pharmaciens d'officine. Le système ne se substitue pas au professionnel de santé et ne fait ni diagnostic ni prescription. Ses rôles principaux sont :
- Collecter et structurer des données officielles et professionnelles.
- Normaliser les noms (DCI, codes ATC, noms commerciaux).
- Détecter et réconcilier les contradictions entre sources (en privilégiant l'autorité officielle supérieure).
- Répondre aux requêtes complexes en citant rigoureusement ses sources et en vérifiant de manière déterministe chaque chiffre affiché.
# 2. Question-Test Multi-Étapes
Pour évaluer le système, nous avons défini une question complexe croisant plusieurs contraintes cliniques et pharmacologiques :

# Question  
 Pour un patient hypertendu âgé qui prend déjà régulièrement de l'Amlodipine, est-il possible de lui associer de l'Ibuprofène pour traiter des douleurs articulaires ? Quel est le niveau d'interaction documenté, quelles sont les précautions ou contre-indications spécifiques, quelle est la posologie maximale recommandée, et que disent les sources officielles à ce sujet ?