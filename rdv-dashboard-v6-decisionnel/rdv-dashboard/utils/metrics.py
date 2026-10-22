"""
Calculs métier réutilisables entre les pages : KPIs globaux, performance des
agents, détection d'alertes automatiques.

Ce module ne fait aucun accès base de données ni rendu Streamlit — il prend
des DataFrames en entrée et retourne des dicts/DataFrames/listes en sortie.
"""

import pandas as pd

ORDRE_JOURS = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
NOMS_JOURS_FR = {
    "Monday": "Lundi", "Tuesday": "Mardi", "Wednesday": "Mercredi",
    "Thursday": "Jeudi", "Friday": "Vendredi", "Saturday": "Samedi", "Sunday": "Dimanche",
}


def kpis_globaux(df: pd.DataFrame) -> dict:
    """KPIs globaux affichés en haut de la Vue d'ensemble."""
    total = len(df)
    confirmes = (df["status"] == "Confirmé").sum() if "status" in df.columns else 0
    annules = (df["status"] == "Annulé").sum() if "status" in df.columns else 0
    agents = df["agent"].nunique() if "agent" in df.columns else 0
    return {
        "total_rdv": total,
        "nb_confirmes": confirmes,
        "nb_annules": annules,
        "taux_confirmation": (confirmes / total * 100) if total else 0.0,
        "taux_annulation": (annules / total * 100) if total else 0.0,
        "nb_agents": agents,
    }


def performance_agents(df: pd.DataFrame, volume_min: int = 5) -> pd.DataFrame:
    """
    Tableau de performance par agent : volume, confirmés, annulés, taux de
    confirmation, + colonne 'significatif' (volume >= volume_min) pour que
    les pages puissent exclure les petits échantillons du classement.
    """
    if "agent" not in df.columns or "status" not in df.columns:
        return pd.DataFrame()

    perf = (
        df.groupby("agent")
        .agg(
            RDV=("agent", "size"),
            Confirmés=("status", lambda s: (s == "Confirmé").sum()),
            Annulés=("status", lambda s: (s == "Annulé").sum()),
        )
        .reset_index()
    )
    perf["Taux confirmation"] = (perf["Confirmés"] / perf["RDV"] * 100).round(1)
    perf["significatif"] = perf["RDV"] >= volume_min
    return perf.sort_values("Taux confirmation", ascending=False)


def _taux_annulation_par_jour(df: pd.DataFrame, colonne_date: str = "date_rdv") -> pd.Series:
    d = df.copy()
    d[colonne_date] = pd.to_datetime(d[colonne_date], errors="coerce")
    d["est_annule"] = d["status"] == "Annulé"
    d["jour_semaine"] = d[colonne_date].dt.day_name()
    par_jour = d.groupby("jour_semaine")["est_annule"].mean().reindex(ORDRE_JOURS) * 100
    par_jour.index = [NOMS_JOURS_FR[j] for j in par_jour.index]
    return par_jour


def detecter_alertes(df: pd.DataFrame, colonne_date: str = "date_rdv") -> list:
    """
    Détecte automatiquement des signaux pour le bloc "Points d'attention" :
    évolution du taux d'annulation, agents hors norme, jour à risque.
    """
    alertes = []
    if "status" not in df.columns:
        return alertes

    d = df.copy()
    d[colonne_date] = pd.to_datetime(d[colonne_date], errors="coerce")
    taux_annulation_global = (d["status"] == "Annulé").mean() * 100

    # --- Évolution mois courant vs mois précédent ---
    d["mois"] = d[colonne_date].dt.to_period("M")
    mois_dispo = sorted(d["mois"].dropna().unique())
    if len(mois_dispo) >= 2:
        mois_actuel, mois_precedent = mois_dispo[-1], mois_dispo[-2]
        taux_actuel = (d[d["mois"] == mois_actuel]["status"] == "Annulé").mean() * 100
        taux_prec = (d[d["mois"] == mois_precedent]["status"] == "Annulé").mean() * 100
        ecart = taux_actuel - taux_prec
        if ecart >= 5:
            alertes.append(
                f"⚠️ Le taux d'annulation a augmenté de **{ecart:.1f} points** "
                f"par rapport au mois précédent ({taux_prec:.1f}% → {taux_actuel:.1f}%)."
            )

    # --- Agents avec un taux d'annulation nettement au-dessus de la moyenne ---
    if "agent" in d.columns and taux_annulation_global:
        par_agent = d.groupby("agent")["status"].apply(lambda s: (s == "Annulé").mean() * 100)
        volumes = d.groupby("agent").size()
        agents_a_signaler = par_agent[
            (par_agent - taux_annulation_global >= 15) & (volumes[par_agent.index] >= 10)
        ]
        for agent_nom, taux in agents_a_signaler.sort_values(ascending=False).items():
            alertes.append(
                f"⚠️ L'agent **{agent_nom}** a un taux d'annulation de **{taux:.1f}%**, "
                f"nettement au-dessus de la moyenne ({taux_annulation_global:.1f}%)."
            )

    # --- Jour de la semaine à risque ---
    par_jour = _taux_annulation_par_jour(d, colonne_date)
    if not par_jour.empty and (par_jour.max() - par_jour.mean() >= 10):
        jour_pire = par_jour.idxmax()
        alertes.append(
            f"⚠️ Les rendez-vous pris le **{jour_pire}** présentent un taux "
            f"d'annulation plus élevé que la moyenne ({par_jour.max():.1f}% contre "
            f"{par_jour.mean():.1f}% en moyenne)."
        )

    return alertes
