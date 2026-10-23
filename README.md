# Projet PFA — Pilotage décisionnel des rendez-vous

Projet de fin d'année : dashboard Streamlit pour analyser les rendez-vous, comprendre les annulations (NLP / BERTopic) et estimer le risque d'annulation (XGBoost).

**Dépôt :** [Nouhaa660/Projet-pfa](https://github.com/Nouhaa660/Projet-pfa)

## Contenu du dépôt

| Fichier / dossier | Rôle |
| --- | --- |
| `DataCLean (1).ipynb` | Nettoyage et préparation des données |
| `nlp_bertopic_ameliore (2).ipynb` | Topics BERTopic sur les motifs d'annulation |
| `prediction_ameliorée.ipynb` | Modèle de prédiction (XGBoost) |
| `rdv-dashboard-v6-decisionnel/rdv-dashboard/` | Application Streamlit (dashboard) |

## Pages du dashboard

1. **Vue d'ensemble** — détecter les écarts
2. **Performance agents** — cibler le coaching
3. **Analyse RDV** — repérer les créneaux sensibles
4. **Annulations + NLP** — causes dominantes et leviers
5. **Prédiction XGBoost** — prioriser les RDV à risque
6. **Qualité des données** — contrôler la fiabilité des indicateurs

Les scores et alertes sont des **aides à la décision**, pas des décisions automatiques.

## Lancer le dashboard

```bash
cd rdv-dashboard-v6-decisionnel/rdv-dashboard
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
streamlit run app.py
```

Avec Docker :

```bash
cd rdv-dashboard-v6-decisionnel/rdv-dashboard
docker compose up --build
```

## Configuration (secrets)

Copier `.streamlit/secrets.toml.example` vers `.streamlit/secrets.toml` et renseigner la connexion (non versionnée).
