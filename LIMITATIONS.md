# Limites connues

Limites connues du projet, mises à jour à chaque bloc.

## Par conception

- Corpus majoritairement synthétique. L'écart avec le corpus réel (50 documents annotés) est mesuré dans [METRICS.md](METRICS.md) ; il constitue la limite principale du projet.
- Français uniquement, 3 types de documents, 6 types d'entités.
- Aucune donnée réelle sensible : les documents « réels » sont des pièces publiques ou anonymisées.
- Volume de l'ordre de la centaine de documents. Aucune conclusion sur le passage à l'échelle.

## Non testé

_(à compléter au fil des blocs)_

## Simplifications assumées

- **Condition suspensive étiquetée `termination_clause`** : dans les compromis de vente, la condition suspensive de prêt (la vente ne naît pas si le prêt est refusé) partage l'étiquette des clauses résolutoires (fin d'un contrat existant). Le modèle ne distingue donc pas ces deux mécanismes juridiques.
- **Compromis de vente limités aux appartements en copropriété** : la surface Carrez n'est obligatoire que pour les lots de copropriété ; les maisons, sans surface Carrez, ne sont pas générées.
- **Distribution des classes DPE non réaliste** : consommation et émissions sont tirées uniformément, d'où environ 48 % de classes F et G sur 200 documents, contre environ 17 % dans le parc français. Ce corpus sert à évaluer l'extraction ; ses proportions ne décrivent pas le parc.
- **Classe, consommation et émissions du DPE non étiquetées** : elles ne font pas partie des 6 types d'entités ; elles servent aux contrôles de cohérence (anomalies), pas à l'extraction.
- **Coûts annuels du DPE simplifiés** : un prix unique de 0,12 € par kWh d'énergie primaire, sans distinguer les énergies (électricité, gaz, fioul).
- **Mise en page unique et sobre** : pas de tableaux, logos, signatures manuscrites ni annexes. Les documents réels sont visuellement plus variés.
- **Documents d'une seule page** : les 600 documents mesurés tiennent sur une page A4 (voir [METRICS.md](METRICS.md)). Le découpage en pages, les en-têtes répétés et les entités coupées entre deux pages ne sont pas testés.
- **Types d'entités déséquilibrés** : 200 références cadastrales (compromis de vente uniquement) contre 1 400 montants ; une moyenne du F1 masquerait la classe rare.
- **Scans simulés simples** : une seule couche de gris (pas de couleur, donc un tampon rouge devient gris), tampons dessinés avec une police OpenCV sans accents, plis rectilignes, pas de taches, de pages coupées ni d'agrafes. Le réalisme doit être vérifié sur le corpus réel (#6) ; l'écart d'OCR synthétique/réel sera mesuré dans METRICS.md.
- **Niveaux de dégradation définis par le projet** : `light`, `medium`, `heavy` sont des réglages choisis à la main pour comparer des résultats entre eux ; ils ne correspondent à aucune norme de qualité de scan.
- **Octets des PDF reproductibles sur une même machine seulement** : les polices viennent du système, donc deux machines produisent des PDF différents (mise en page, glyphes). Le texte et la vérité terrain, eux, sont identiques.

## Hors périmètre — non revendiqué

Fine-tuning de LLM (LoRA / QLoRA) · exploitation en production sous charge réelle · expertise métier notariale, juridique ou financière · agents autonomes et orchestration multi-agents · multilingue.
