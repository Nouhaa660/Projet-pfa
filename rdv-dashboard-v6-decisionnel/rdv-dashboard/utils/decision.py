import pandas as pd
import numpy as np


# ============================================================
# PREPARATION DES STATUTS
# ============================================================

def prepare_status(df):
    """
    Garde uniquement les RDV ayant un statut exploitable.
    """
    if df is None or df.empty:
        return pd.DataFrame()

    d = df.copy()

    if "status" in d.columns:
        d["status"] = d["status"].astype(str).str.strip()

        d = d[
            d["status"].isin(["Confirmé", "Annulé"])
        ].copy()

    return d


# ============================================================
# KPI DECISION
# ============================================================

def decision_kpis(df):
    """
    Calcule les KPI principaux :
    - nombre total de RDV
    - annulés
    - confirmés
    - taux d'annulation
    - taux de confirmation
    """

    d = prepare_status(df)

    if d.empty or "status" not in d.columns:
        return {
            "total": 0,
            "annules": 0,
            "confirmes": 0,
            "taux_annulation": 0.0,
            "taux_confirmation": 0.0,
        }

    total = len(d)

    ann = int(
        (d["status"] == "Annulé").sum()
    )

    conf = int(
        (d["status"] == "Confirmé").sum()
    )

    return {
        "total": total,
        "annules": ann,
        "confirmes": conf,
        "taux_annulation": round(
            ann / total * 100, 1
        ) if total else 0.0,
        "taux_confirmation": round(
            conf / total * 100, 1
        ) if total else 0.0,
    }


# ============================================================
# RISQUE DES RDV A VENIR
# ============================================================

def upcoming_risk_summary(df):
    """
    Résume les scores de risque disponibles.

    Seuils :
    - Faible : < 0.30
    - Moyen  : 0.30 à < 0.60
    - Élevé  : >= 0.60
    """

    if (
        df is None
        or df.empty
        or "risque" not in df.columns
    ):
        return {
            "scored": 0,
            "high": 0,
            "medium": 0,
            "expected": 0.0,
        }

    d = df.copy()

    # Conversion robuste en numérique
    d["risque"] = pd.to_numeric(
        d["risque"],
        errors="coerce"
    )

    # Garde uniquement les scores valides
    d = d.dropna(subset=["risque"]).copy()

    # Sécurité : le risque doit être entre 0 et 1
    d = d[
        d["risque"].between(0, 1)
    ].copy()

    if d.empty:
        return {
            "scored": 0,
            "high": 0,
            "medium": 0,
            "expected": 0.0,
        }

    return {
        "scored": len(d),

        "high": int(
            (d["risque"] >= 0.60).sum()
        ),

        "medium": int(
            (
                (d["risque"] >= 0.30)
                & (d["risque"] < 0.60)
            ).sum()
        ),

        # Somme des probabilités = nombre attendu
        # de rendez-vous annulés
        "expected": round(
            float(d["risque"].sum()),
            2
        ),
    }


# ============================================================
# TABLE D'ACTIONS
# ============================================================

def build_action_table(risk_df):
    """
    Construit une table opérationnelle à partir
    des scores de risque.
    """

    if (
        risk_df is None
        or risk_df.empty
        or "risque" not in risk_df.columns
    ):
        return pd.DataFrame()

    d = risk_df.copy()

    # Conversion numérique
    d["risque"] = pd.to_numeric(
        d["risque"],
        errors="coerce"
    )

    d = d.dropna(subset=["risque"]).copy()

    # Garder les probabilités valides
    d = d[
        d["risque"].between(0, 1)
    ].copy()

    if d.empty:
        return pd.DataFrame()

    # --------------------------------------------------------
    # PRIORITE
    # --------------------------------------------------------

    d["priorite"] = pd.cut(
        d["risque"],
        bins=[-0.001, 0.30, 0.60, 1.001],
        labels=[
            "Faible",
            "Moyenne",
            "Élevée"
        ],
        include_lowest=True
    )

    # --------------------------------------------------------
    # ACTION
    # --------------------------------------------------------

    def get_action(p):
        if p >= 0.60:
            return "Confirmer / rappeler"

        if p >= 0.30:
            return "Vérifier le RDV"

        return "Suivi normal"

    d["action"] = d["risque"].apply(
        get_action
    )

    # --------------------------------------------------------
    # COLONNES AFFICHÉES
    # --------------------------------------------------------

    preferred_cols = [
        "agent",
        "confirmateur",
        "date_rdv",
        "heure_rdv",
        "type_fiche",
        "risque",
        "priorite",
        "action",
    ]

    cols = [
        c for c in preferred_cols
        if c in d.columns
    ]

    # Si aucune colonne métier n'est disponible
    if not cols:
        return d.sort_values(
            "risque",
            ascending=False
        )

    return (
        d[cols]
        .sort_values(
            "risque",
            ascending=False
        )
        .reset_index(drop=True)
    )


# ============================================================
# MOTIFS D'ANNULATION
# ============================================================

def cancellation_motif_actions(
    df,
    motif_col="motif"
):
    """
    Résumé descriptif des motifs d'annulation.

    Les catégories proviennent du pipeline NLP.
    Cette fonction ne crée pas de nouvelle interprétation
    métier des motifs.
    """

    if (
        df is None
        or df.empty
        or motif_col not in df.columns
    ):
        return pd.DataFrame()

    r = (
        df[motif_col]
        .fillna("Non classé")
        .astype(str)
        .str.strip()
        .replace("", "Non classé")
        .value_counts()
        .rename("Annulations")
        .reset_index()
    )

    r.columns = [
        "Motif",
        "Annulations"
    ]

    total = r["Annulations"].sum()

    if total > 0:
        r["Part"] = (
            r["Annulations"]
            / total
            * 100
        ).round(1)
    else:
        r["Part"] = 0.0

    return r


# ============================================================
# DIAGNOSTIC DES AGENTS
# ============================================================

def agent_diagnostic(
    df,
    min_volume=10
):
    """
    Analyse descriptive des taux d'annulation
    par agent.

    Un agent n'est signalé que si :
    - son volume atteint min_volume
    - son taux est suffisamment éloigné du taux global
    """

    d = prepare_status(df)

    if (
        d.empty
        or "agent" not in d.columns
    ):
        return pd.DataFrame()

    # Nettoyage agent
    d["agent"] = (
        d["agent"]
        .fillna("Non renseigné")
        .astype(str)
        .str.strip()
    )

    # --------------------------------------------------------
    # AGRÉGATION
    # --------------------------------------------------------

    g = (
        d.groupby("agent")
        .agg(
            RDV=("status", "size"),

            Confirmés=(
                "status",
                lambda s: (
                    s == "Confirmé"
                ).sum()
            ),

            Annulés=(
                "status",
                lambda s: (
                    s == "Annulé"
                ).sum()
            ),
        )
        .reset_index()
    )

    # --------------------------------------------------------
    # TAUX
    # --------------------------------------------------------

    g["Taux annulation"] = (
        g["Annulés"]
        / g["RDV"]
        * 100
    ).round(1)

    g["Taux confirmation"] = (
        g["Confirmés"]
        / g["RDV"]
        * 100
    ).round(1)

    # --------------------------------------------------------
    # VOLUME
    # --------------------------------------------------------

    g["volume_suffisant"] = (
        g["RDV"] >= min_volume
    )

    # --------------------------------------------------------
    # TAUX GLOBAL
    # --------------------------------------------------------

    global_rate = (
        d["status"]
        .eq("Annulé")
        .mean()
        * 100
    )

    g["écart_vs_global"] = (
        g["Taux annulation"]
        - global_rate
    ).round(1)

    # --------------------------------------------------------
    # SIGNAL
    # --------------------------------------------------------

    def get_signal(row):

        if (
            row["volume_suffisant"]
            and row["écart_vs_global"] >= 10
        ):
            return "À investiguer"

        if (
            row["volume_suffisant"]
            and row["écart_vs_global"] <= -10
        ):
            return "Performance favorable"

        return "Dans la norme"

    g["signal"] = g.apply(
        get_signal,
        axis=1
    )

    # --------------------------------------------------------
    # TRI
    # --------------------------------------------------------

    signal_order = {
        "À investiguer": 0,
        "Dans la norme": 1,
        "Performance favorable": 2,
    }

    g["_signal_order"] = (
        g["signal"]
        .map(signal_order)
        .fillna(99)
    )

    g = (
        g.sort_values(
            [
                "_signal_order",
                "Taux annulation"
            ],
            ascending=[
                True,
                False
            ]
        )
        .drop(
            columns="_signal_order"
        )
        .reset_index(drop=True)
    )

    return g
