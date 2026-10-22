"""
Calculs pour la page Qualité des données —
complétude, doublons, valeurs manquantes, fraîcheur, colonnes critiques.
"""

from __future__ import annotations

import pandas as pd

# Colonnes métier prioritaires pour le pilotage
COLONNES_CRITIQUES = [
    "agent",
    "status",
    "date_rdv",
    "date_appel",
    "commentaire",
    "type_fiche",
    "confirmateur",
]


def resume_qualite(df: pd.DataFrame) -> dict:
    nb_lignes = len(df)
    nb_doublons = int(df.duplicated().sum())
    taux_nulls_global = (
        df.isna().sum().sum() / (nb_lignes * len(df.columns)) * 100
        if nb_lignes and len(df.columns)
        else 0.0
    )
    return {
        "nb_lignes": nb_lignes,
        "nb_doublons": nb_doublons,
        "taux_nulls_global": round(float(taux_nulls_global), 1),
        "nb_colonnes": len(df.columns),
    }


def completude_par_colonne(df: pd.DataFrame) -> pd.DataFrame:
    completude = (
        ((1 - df.isna().mean()) * 100)
        .round(1)
        .sort_values(ascending=True)
        .reset_index()
    )
    completude.columns = ["Colonne", "Complétude (%)"]
    completude["Manquants"] = (
        df[completude["Colonne"].tolist()].isna().sum().values
    )
    return completude


def colonnes_sous_seuil(completude_df: pd.DataFrame, seuil: float = 85.0) -> pd.DataFrame:
    if completude_df is None or completude_df.empty:
        return pd.DataFrame()
    return completude_df[completude_df["Complétude (%)"] < seuil].copy()


def completude_colonnes_critiques(df: pd.DataFrame) -> pd.DataFrame:
    cols = [c for c in COLONNES_CRITIQUES if c in df.columns]
    if not cols:
        return pd.DataFrame(columns=["Colonne", "Complétude (%)", "Manquants", "Statut"])
    rows = []
    for c in cols:
        rate = (1 - df[c].isna().mean()) * 100
        missing = int(df[c].isna().sum())
        rows.append({
            "Colonne": c,
            "Complétude (%)": round(rate, 1),
            "Manquants": missing,
            "Statut": "OK" if rate >= 90 else ("Fragile" if rate >= 70 else "Critique"),
        })
    return pd.DataFrame(rows)


def derniere_donnee_connue(df: pd.DataFrame, colonne_date: str = "date_appel"):
    """Proxy de fraîcheur (pas un timestamp de sync dédié)."""
    candidates = [colonne_date, "date_rdv", "created_at", "updated_at"]
    for col in candidates:
        if col not in df.columns:
            continue
        d = pd.to_datetime(df[col], errors="coerce")
        if d.notna().any():
            return d.max(), col
    return None, None


def score_qualite(df: pd.DataFrame) -> dict:
    """Score 0–100 indicatif pour le feu décisionnel."""
    r = resume_qualite(df)
    crit = completude_colonnes_critiques(df)

    score = 100.0
    # Pénalités
    score -= min(40.0, r["taux_nulls_global"] * 2)
    score -= min(25.0, r["nb_doublons"] * 0.5)
    if not crit.empty:
        mean_crit = float(crit["Complétude (%)"].mean())
        score -= max(0.0, (95 - mean_crit) * 0.8)

    score = max(0.0, min(100.0, round(score, 1)))
    if score >= 85:
        niveau = "Bon"
    elif score >= 70:
        niveau = "Acceptable"
    else:
        niveau = "Insuffisant"

    return {"score": score, "niveau": niveau, **r}
