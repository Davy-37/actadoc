# Métriques mesurées

Une case vide n'est jamais comblée par une estimation. Une métrique non mesurée n'existe pas et ne figure sur aucun document de candidature.

| Bloc | Métrique | Valeur | Date | Protocole |
|---|---|---|---|---|
| OCR | CER sans prétraitement | | | |
| OCR | CER avec prétraitement | | | |
| OCR | Gain relatif du prétraitement | | | |
| Classification | Exactitude, référence TF-IDF | | | |
| Classification | Exactitude, CamemBERT affiné | | | |
| Classification | F1 macro du modèle retenu | | | |
| Confiance | ECE avant recalage | | | |
| Confiance | ECE après recalage | | | |
| Confiance | Taux d'erreur à 90 % de couverture | | | |
| Extraction | F1 moyen sur 6 types d'entités | | | |
| Extraction | Écart synthétique / réel | | | |
| RAG | Recall@5 sans reranking | | | |
| RAG | Recall@5 avec reranking | | | |
| RAG | Latence de recherche p95 | | | |
| LLM | Conformité au schéma structuré | | | |
| LLM | Abstention correcte hors corpus | | | |
| LLM | Coût par document, API propriétaire | | | |
| LLM | Coût par document, auto-hébergé | | | |
| Anomalies | Précision / rappel sur docs altérés | | | |
| Système | Latence bout-en-bout par document | | | |

## Arbitrage fournisseurs LLM

| Fournisseur | Coût / doc | Latence p95 | Confidentialité | Conformité schéma |
|---|---|---|---|---|
| API propriétaire | | | données sortantes — incompatible RGPD sur pièces notariales | |
| Auto-hébergé (Ollama) | | | données locales | |
