# Limites connues

Document public et tenu à jour. Une faiblesse annoncée par l'auteur vaut mieux que la même faiblesse découverte par un recruteur technique.

## Par conception

- Corpus majoritairement synthétique. L'écart avec le corpus réel (50 documents annotés) est mesuré dans [METRICS.md](METRICS.md) ; il constitue la limite principale du projet.
- Français uniquement, 3 types de documents, 6 types d'entités.
- Aucune donnée réelle sensible : les documents « réels » sont des pièces publiques ou anonymisées.
- Volume de l'ordre de la centaine de documents. Aucune conclusion sur le passage à l'échelle.

## Non testé

_(à remplir au fil des semaines)_

## Simplifications assumées

- **Condition suspensive étiquetée `termination_clause`** : dans les compromis de vente, la condition suspensive de prêt (la vente ne naît pas si le prêt est refusé) partage l'étiquette des clauses résolutoires (fin d'un contrat existant). Le modèle ne distingue donc pas ces deux mécanismes juridiques.
- **Compromis de vente limités aux appartements en copropriété** : la surface Carrez n'est obligatoire que pour les lots de copropriété ; les maisons, sans surface Carrez, ne sont pas générées.
- **Documents en texte seul pour l'instant** : rendu PDF et dégradation de scan à venir (#2).

## Hors périmètre — non revendiqué

Fine-tuning de LLM (LoRA / QLoRA) · exploitation en production sous charge réelle · expertise métier notariale, juridique ou financière · agents autonomes et orchestration multi-agents · multilingue.
