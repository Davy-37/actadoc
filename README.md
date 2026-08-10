# ACTADOC — Intelligence documentaire (OCR · NLP · RAG)

Plateforme d'analyse de documents immobiliers et juridiques français : ingestion d'un PDF hétérogène, extraction d'information structurée, classification avec score de confiance calibré, détection d'anomalies, interrogation du corpus en langage naturel avec citation systématique des sources.

**Projet phare** du portfolio — absorbe le périmètre RAG initialement prévu en [02-rag-agent-ai-engineer](../02-rag-agent-ai-engineer/).
**Fenêtre d'exécution :** 11 août → 5 octobre 2026 (8 semaines, ~100 h).

---

## Périmètre gelé

| Dimension | Décision |
|---|---|
| Documents | Bail d'habitation · Compromis de vente · DPE |
| Entités | Parties · Montants · Dates · Références cadastrales · Surfaces · Clauses résolutoires |
| Langue | Français uniquement |
| Volume | 200 documents synthétiques + 50 réels annotés |
| Hors périmètre | Signature électronique · Multilingue · Fine-tuning de LLM · Agents autonomes · UI élaborée |

Tout élargissement est reporté après le 5 octobre. Un retard se rattrape en réduisant le périmètre de la semaine concernée, jamais en doublant la charge de la suivante.

---

## Vérité terrain

Le corpus est **généré synthétiquement à étiquettes natives** : gabarits dérivés de modèles publics (service-public.fr, Judilibre, Légifrance, open data ADEME, DVF), remplissage Faker en localisation `fr_FR`, rendu PDF, puis dégradation délibérée pour simuler la numérisation (rotation faible angle, bruit gaussien, compression JPEG, variation d'éclairage, tampons, pliures).

La valeur insérée *est* la valeur à extraire : annotation parfaite, coût nul, régénération reproductible à graine fixée.

**Contrainte méthodologique.** L'écart de performance entre corpus synthétique et corpus réel est mesuré et publié dans [METRICS.md](METRICS.md), jamais dissimulé.

---

## Architecture

```
PDF → routage (natif / scan)
    → prétraitement OpenCV → OCR          [ingestion]
    → classification 3 classes + calibration  [classification]
    → NER 6 types + abstention             [extraction]
    → chunking → embeddings → pgvector     [retrieval]
    → reranking cross-encoder → citations  [retrieval]
    → orchestration LLM + sortie contrainte [llm]
    → règles de cohérence, forensique PDF   [anomalies]
    → FastAPI conteneurisée                 [api]
```

**Arbitrage pgvector plutôt qu'une base vectorielle dédiée :** une structure en phase de lancement n'a pas intérêt à exploiter deux systèmes de persistance quand un seul suffit au volume. PostgreSQL 16 + extension pgvector, index HNSW.

---

## Structure

```
src/actadoc/
  generation/      S1 — gabarits, Faker, rendu PDF, dégradation
  ingestion/       S2 — routage, prétraitement, OCR
  classification/  S3 — TF-IDF/LogReg puis CamemBERT
  extraction/      S4 — NER token-classification, calibration, abstention
  retrieval/       S5-S6 — chunking, embeddings, pgvector, reranking
  llm/             S7 — orchestration multi-fournisseurs, sorties Pydantic
  anomalies/       S8 — cohérence inter-pièces, hachage perceptuel, forensique
  api/             S8 — FastAPI
evaluation/        jeux d'éval : 50 questions RAG, hallucinations, docs altérés
data/              non versionné — raw/ synthetic/ real/
docker/  scripts/  tests/  docs/
```

`data/` est ignoré par Git. `scripts/generate_corpus.py` doit permettre de le reconstruire intégralement.

---

## Phases

| Sem. | Période | Objectif | Métrique produite |
|---|---|---|---|
| 1 | 11–17 août | Corpus synthétique dégradé | Distribution des entités, taux de dégradation |
| 2 | 18–24 août | PDF → texte fiable | **CER / WER avant et après prétraitement** |
| 3 | 25–31 août | Classification 3 classes | Exactitude TF-IDF vs CamemBERT, F1 macro, coût |
| 4 | 1–7 sept. | NER + confiance calibrée | **F1 par entité, ECE avant/après, erreur à 90 % de couverture** |
| 5 | 8–14 sept. | Recherche vectorielle | **Recall@5, MRR, latence par stratégie de chunking** |
| 6 | 15–21 sept. | Reranking + citations | **Gain Recall/MRR du reranking, surcoût latence** |
| 7 | 22–28 sept. | Génération fiable | **Conformité schéma, abstention hors corpus, coût/latence/confidentialité par fournisseur** |
| 8 | 29 sept.–5 oct. | Anomalies + industrialisation | **Précision/rappel sur docs altérés, latence bout-en-bout** |

Détail complet dans le plan de montée en compétence. Avancement dans [JOURNAL.md](JOURNAL.md), résultats dans [METRICS.md](METRICS.md).

**Règle :** une semaine sans chiffre mesuré est une semaine perdue. Une case vide de `METRICS.md` n'est jamais comblée par une estimation.

---

## Stack

Python 3.11 · Faker · WeasyPrint · OpenCV · pdfplumber · PyMuPDF · docTR · Tesseract · scikit-learn · PyTorch · Hugging Face Transformers (CamemBERT) · spaCy · MLflow · PostgreSQL 16 + pgvector · sentence-transformers · bge-reranker · LlamaIndex · Ollama · Pydantic · pypdf · imagehash · datasketch · FastAPI · Docker

---

## Limites connues

Tenues à jour publiquement dans [LIMITATIONS.md](LIMITATIONS.md) — ce qui ne marche pas, ce qui n'a pas été testé, ce qui a été simplifié.

Non revendiqué et non couvert par ce projet : fine-tuning de LLM (LoRA/QLoRA), mise en production à l'échelle sous charge réelle, expertise métier notariale ou juridique, agents autonomes, multilingue.

**Vérification de licence requise** avant tout usage revendiqué des modèles de compréhension documentaire type LayoutLM / Donut : plusieurs sont diffusés sous licence non commerciale.
