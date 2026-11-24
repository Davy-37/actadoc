# Métriques mesurées

Valeurs mesurées, avec leur date et leur protocole. Une case vide correspond à une métrique pas encore mesurée.

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

## Corpus synthétique

Composition du corpus sur lequel les blocs suivants sont évalués. Les tableaux sont produits par `scripts/corpus_stats.py` ; relancer la commande après toute modification d'un générateur.

Measured on 2026-11-24: 200 documents per type, corpus seed 42, Faker 40.63.0. Command: `python scripts/corpus_stats.py --n 200 --seed 42`.

| Type | Documents | Words (min / mean / max) | PDF pages (min / mean / max) | Entities |
|---|---|---|---|---|
| `lease` | 200 | 174 / 179.0 / 184 | 1 / 1.0 / 1 | 1800 |
| `sale_agreement` | 200 | 166 / 169.8 / 177 | 1 / 1.0 / 1 | 1800 |
| `energy_certificate` | 200 | 90 / 94.0 / 99 | 1 / 1.0 / 1 | 1400 |

| Entity type | `lease` | `sale_agreement` | `energy_certificate` | Total |
|---|---|---|---|---|
| `party` | 400 | 400 | 400 | 1200 |
| `amount` | 600 | 400 | 400 | 1400 |
| `date` | 400 | 400 | 400 | 1200 |
| `cadastral_reference` | 0 | 200 | 0 | 200 |
| `surface` | 200 | 200 | 200 | 600 |
| `termination_clause` | 200 | 200 | 0 | 400 |

| DPE class | A | B | C | D | E | F | G |
|---|---|---|---|---|---|---|---|
| Certificates | 3 | 8 | 33 | 27 | 33 | 49 | 47 |
| Share | 2% | 4% | 16% | 14% | 16% | 24% | 24% |

Share of scanned pages that get each operation (`clean`: none):

| Operation | `light` | `medium` | `heavy` |
|---|---|---|---|
| `rotate` | 100% | 100% | 100% |
| `fold` | 0% | 52% | 100% |
| `stamp` | 0% | 51% | 100% |
| `lighting` | 100% | 100% | 100% |
| `blur` | 0% | 48% | 100% |
| `noise` | 100% | 100% | 100% |
| `jpeg` | 100% | 100% | 100% |

Lecture :

- **Une page par document** : aucun document ne dépasse une page A4. Les actes réels en font souvent plusieurs ; voir [LIMITATIONS.md](LIMITATIONS.md).
- **Types d'entités déséquilibrés** : les références cadastrales n'existent que dans les compromis de vente (200 occurrences, contre 1 400 montants). Le F1 d'extraction sera donc publié par type d'entité, pas seulement en moyenne.
- **Classes DPE** : 48 % de F et G, contre environ 17 % dans le parc français ; distribution non réaliste, connue (voir LIMITATIONS.md).
- **Dégradations** : rotation, éclairage, bruit et JPEG touchent toutes les pages dès le niveau `light` (avec des amplitudes croissantes) ; pli, tampon et flou distinguent `medium` (environ une page sur deux) de `heavy` (toutes les pages).

## Arbitrage fournisseurs LLM

| Fournisseur | Coût / doc | Latence p95 | Confidentialité | Conformité schéma |
|---|---|---|---|---|
| API propriétaire | | | données sortantes — incompatible RGPD sur pièces notariales | |
| Auto-hébergé (Ollama) | | | données locales | |
