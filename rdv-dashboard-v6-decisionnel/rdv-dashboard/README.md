# RDV Intelligence — V5

Dashboard Streamlit de pilotage décisionnel des rendez-vous.

## Finalité métier

Le dashboard ne se limite pas à afficher des graphiques. Il organise l'information
selon le cycle de décision :

1. **Vue d'ensemble** → détecter les écarts
2. **Performance agents** → cibler l'investigation / le coaching
3. **Analyse RDV** → repérer les créneaux sensibles
4. **Annulations + NLP** → identifier les causes dominantes et proposer des leviers
5. **Prédiction XGBoost** → prioriser les prochains RDV à risque
6. **Qualité des données** → contrôler la fiabilité avant interprétation
7. **Fiches & RDV** → revenir au niveau opérationnel

## Modèles intégrés

- XGBoost : probabilité d'annulation d'un RDV à venir.
- BERTopic : regroupement des commentaires de RDV annulés.
- `noms_motifs.json` : traduction des topics en catégories métier.

## Principe important

Les prédictions et alertes sont des **aides à la décision**, pas des décisions automatiques.
Le dashboard rend également visibles les RDV non scorables et les limites méthodologiques.

## Lancer

```bash
streamlit run app.py
```

Ou :

```bash
docker compose up --build
```
