import streamlit as st
import pandas as pd

from utils.supabase import get_rendez_vous
from utils.charts import (
    chart_taux_par_jour,
    chart_taux_par_heure,
    chart_taux_par_mois
)
from utils.ui import (
    bootstrap_page,
    page_header,
    section,
    kpi_card,
    insight
)


# ============================================================
# HEADER
# ============================================================

bootstrap_page()

page_header(
    "03 · RDV analytics",
    "Analyse des rendez-vous",
    "Identifier les moments et périodes associés à une fréquence "
    "d’annulation plus élevée."
)


# ============================================================
# CHARGEMENT DES DONNÉES
# ============================================================

with st.spinner("Chargement des données..."):

    try:

        df = get_rendez_vous(
            columns=[
                "status",
                "date_rdv",
                "heure_rdv"
            ]
        )

    except Exception as e:

        st.error(
            f"Impossible de charger les données : {e}"
        )

        st.stop()


# ============================================================
# CONTRÔLES
# ============================================================

if df.empty or "status" not in df.columns:

    st.info(
        "Données insuffisantes pour cette analyse."
    )

    st.stop()


# ============================================================
# NETTOYAGE
# ============================================================

df["status"] = (
    df["status"]
    .astype(str)
    .str.strip()
)

df["date_rdv"] = pd.to_datetime(
    df["date_rdv"],
    errors="coerce"
)

# On conserve uniquement les deux statuts métier
df = df[
    df["status"].isin(
        ["Confirmé", "Annulé"]
    )
].copy()

if df.empty:

    st.info(
        "Aucun rendez-vous Confirmé ou Annulé disponible."
    )

    st.stop()


# ============================================================
# KPI
# ============================================================

total = len(df)

annulations = (
    df["status"]
    .eq("Annulé")
    .sum()
)

taux_annulation = (
    annulations / total * 100
    if total > 0
    else 0
)


# ============================================================
# INDICATEURS CLÉS
# ============================================================

st.markdown("### Indicateurs clés")

kpi_columns = st.columns(3)

kpis = [
    (
        "RDV analysés",
        f"{total:,}".replace(",", " "),
        "Périmètre chargé"
    ),
    (
        "Annulations",
        f"{annulations:,}".replace(",", " "),
        "Statut Annulé"
    ),
    (
        "Taux d'annulation",
        f"{taux_annulation:.1f} %",
        "Sur le périmètre"
    )
]

for col, (label, value, description) in zip(
    kpi_columns,
    kpis
):

    with col:

        kpi_card(
            label,
            value,
            description
        )


# ============================================================
# ANALYSE TEMPORELLE
# ============================================================

section(
    "Analyse temporelle",
    "Trois angles complémentaires pour repérer les créneaux sensibles."
)


# ============================================================
# JOUR / HEURE
# ============================================================

c1, c2 = st.columns(
    [1, 1],
    gap="large"
)


# ------------------------------------------------------------
# JOUR DE LA SEMAINE
# ------------------------------------------------------------

with c1:

    st.markdown("#### 📅 Annulations par jour")

    fig_jour = chart_taux_par_jour(df)

    if fig_jour is not None:

        st.plotly_chart(
            fig_jour,
            use_container_width=True,
            config={
                "displayModeBar": False
            }
        )

        insight(
            "Le jour de la semaine met en évidence les écarts "
            "de comportement entre créneaux récurrents."
        )

    else:

        st.info(
            "Analyse par jour indisponible."
        )


# ------------------------------------------------------------
# HEURE
# ------------------------------------------------------------

with c2:

    st.markdown("#### 🕐 Annulations par heure")

    fig_heure = chart_taux_par_heure(df)

    if fig_heure is None:

        st.info(
            "Analyse horaire indisponible : "
            "heure_rdv absente ou non exploitable."
        )

    else:

        st.plotly_chart(
            fig_heure,
            use_container_width=True,
            config={
                "displayModeBar": False
            }
        )

        insight(
            "Les heures présentant un taux supérieur au niveau "
            "global méritent une surveillance opérationnelle."
        )


# ============================================================
# EVOLUTION MENSUELLE
# ============================================================

st.markdown("#### 📈 Évolution mensuelle")

fig_mois = chart_taux_par_mois(df)

if fig_mois is not None:

    st.plotly_chart(
        fig_mois,
        use_container_width=True,
        config={
            "displayModeBar": False
        }
    )

    insight(
        "L'évolution mensuelle permet de détecter une dérive "
        "progressive ou une amélioration du taux d'annulation."
    )

else:

    st.info(
        "Analyse mensuelle indisponible."
    )


# ============================================================
# DECISION OPERATIONNELLE
# ============================================================

section(
    "Décision opérationnelle",
    "Repérer les créneaux qui méritent une action de "
    "reconfirmation ou une investigation."
)


# ============================================================
# ANALYSE PAR JOUR
# ============================================================

d = df.copy()

d["est_annule"] = (
    d["status"] == "Annulé"
)

d["jour"] = (
    d["date_rdv"]
    .dt.day_name()
)

jour_stats = (
    d.dropna(subset=["jour"])
     .groupby("jour")
     .agg(
         rdv=("est_annule", "size"),
         annulations=("est_annule", "sum")
     )
)

if not jour_stats.empty:

    jour_stats["taux_annulation"] = (
        jour_stats["annulations"]
        / jour_stats["rdv"]
        * 100
    )

    jour_stats = jour_stats.sort_values(
        "taux_annulation",
        ascending=False
    )

    jour_a_surveiller = (
        jour_stats.index[0]
    )

    taux_jour = (
        jour_stats.iloc[0]["taux_annulation"]
    )

    volume_jour = (
        int(jour_stats.iloc[0]["rdv"])
    )


    
# ============================================================
# NOTE METHODOLOGIQUE
# ============================================================

st.caption(
    "Les taux présentés sont descriptifs : ils permettent "
    "d'identifier des créneaux à surveiller, mais ne permettent "
    "pas à eux seuls d'expliquer la cause des annulations."
)