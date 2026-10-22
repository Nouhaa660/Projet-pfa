"""
Widgets de filtre réutilisables. Chaque fonction affiche le selectbox
Streamlit ET retourne directement le DataFrame déjà filtré, pour que les
pages puissent écrire `df = filtre_agent(df)` sans logique supplémentaire.
"""

import pandas as pd
import streamlit as st


def filtre_agent(df: pd.DataFrame, key: str = "filtre_agent") -> pd.DataFrame:
    if "agent" not in df.columns:
        return df
    options = ["Tous"] + sorted(df["agent"].dropna().unique().tolist())
    choix = st.selectbox("Agent", options, key=key)
    return df if choix == "Tous" else df[df["agent"] == choix]


def filtre_type_fiche(df: pd.DataFrame, key: str = "filtre_type_fiche") -> pd.DataFrame:
    if "type_fiche" not in df.columns:
        return df
    options = ["Tous"] + sorted(df["type_fiche"].dropna().unique().tolist())
    choix = st.selectbox("Type de fiche", options, key=key)
    return df if choix == "Tous" else df[df["type_fiche"] == choix]


def filtre_statut(df: pd.DataFrame, key: str = "filtre_statut") -> pd.DataFrame:
    if "status" not in df.columns:
        return df
    options = ["Tous"] + sorted(df["status"].dropna().unique().tolist())
    choix = st.selectbox("Statut", options, key=key)
    return df if choix == "Tous" else df[df["status"] == choix]
