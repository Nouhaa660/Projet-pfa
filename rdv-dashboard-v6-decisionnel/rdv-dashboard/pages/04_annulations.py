import json
from pathlib import Path

import pandas as pd
import streamlit as st

from utils.supabase import get_rendez_vous
from utils.prediction import predict_cancellation_reasons
from utils.decision import cancellation_motif_actions
from utils.charts import (
    chart_motifs_repartition,
    chart_motifs_evolution
)
from utils.ui import (
    bootstrap_page,
    page_header,
    section,
    kpi_card,
    insight
)

bootstrap_page()

page_header(
    "04 · Cancellation intelligence",
    "Comprendre les annulations",
    "Identifier les motifs qui pèsent réellement dans les annulations "
    "et fournir une base factuelle pour l'investigation opérationnelle."
)

MAPPING_PATH = Path("models/noms_motifs.json")
TOPICS_DETAILS_PATH = Path("models/topics_bertopic_details.csv")


@st.cache_data(show_spinner=False)
def load_motif_mapping():
    if not MAPPING_PATH.exists():
        return {"-1": "Non classé"}
    try:
        return {
            str(k): str(v).strip()
            for k, v in json.loads(
                MAPPING_PATH.read_text(encoding="utf-8")
            ).items()
        }
    except Exception:
        return {"-1": "Non classé"}


@st.cache_data(show_spinner=False)
def load_topics_details(mapping: dict) -> pd.DataFrame:
    if not TOPICS_DETAILS_PATH.exists():
        return pd.DataFrame(
            [{"Topic ID": k, "Motif": v} for k, v in mapping.items()]
        )
    details = pd.read_csv(TOPICS_DETAILS_PATH)
    details["Topic"] = details["Topic"].astype(str)
    details["Motif métier"] = details["Topic"].map(
        lambda t: mapping.get(t, "Non classé")
    )
    cols = [c for c in ["Topic", "Motif métier", "Count", "keywords"] if c in details.columns]
    out = details[cols].rename(columns={
        "Topic": "Topic ID",
        "Count": "Volume entraînement",
        "keywords": "Mots-clés BERTopic",
    })
    return out.sort_values(
        "Topic ID",
        key=lambda s: s.map(
            lambda x: int(x) if str(x).lstrip("-").isdigit() else 999
        ),
    ).reset_index(drop=True)


mapping = load_motif_mapping()
referentiel = load_topics_details(mapping)

with st.expander("Référentiel des motifs NLP", expanded=False):
    st.caption(
        "Mapping Topic ID → motif métier + volumes / mots-clés BERTopic."
    )
    st.dataframe(referentiel, use_container_width=True, hide_index=True)

with st.spinner("Chargement des annulations..."):
    try:
        df = get_rendez_vous(
            columns=["agent", "date_rdv", "commentaire", "status"],
            where="status = 'Annulé'",
            order_by="date_rdv DESC",
            limit=1500
        )
    except Exception as e:
        st.error(f"Impossible de charger les données : {e}")
        st.stop()

if df.empty:
    st.info("Aucune annulation disponible.")
    st.stop()

with st.spinner("Classification NLP des commentaires..."):
    df["motif"] = predict_cancellation_reasons(
        df["commentaire"].fillna("").tolist()
    )

# ============================================================
# INDICATEURS
# ============================================================

non_classes = int((df["motif"] == "Non classé").sum())
nb_motifs = df["motif"].nunique()
taux_non_classes = (non_classes / len(df) * 100) if len(df) > 0 else 0

recap = cancellation_motif_actions(df)

# ============================================================
# KPI
# ============================================================

st.markdown("### Indicateurs clés")
c1, c2, c3 = st.columns(3)

with c1:
    kpi_card(
        "Annulations analysées",
        f"{len(df):,}".replace(",", " "),
        "Échantillon NLP"
    )

with c2:
    kpi_card(
        "Motifs identifiés",
        str(nb_motifs),
        "Catégories observées"
    )

with c3:
    kpi_card(
        "Non classés",
        f"{taux_non_classes:.1f} %",
        "Commentaires sans catégorie exploitable"
    )

# ============================================================
# RÉPARTITION DES MOTIFS
# ============================================================

section(
    "Répartition des motifs",
    "Les catégories correspondent au référentiel métier défini "
    "dans le pipeline NLP. Elles permettent de comprendre les "
    "raisons déclarées dans les commentaires."
)

# ============================================================
# TABLEAU SYNTHÈSE
# ============================================================

if not recap.empty:
    st.dataframe(
        recap,
        use_container_width=True,
        hide_index=True,
        column_config={
            "Motif": st.column_config.TextColumn("Motif", width="large"),
            "Part": st.column_config.NumberColumn("Part", format="%.1f %%")
        }
    )

    top = recap.iloc[0]
    insight(
        f"Le motif dominant est « {top['Motif']} » "
        f"avec {top['Part']:.1f}% des annulations analysées. "
        "Il constitue le premier sujet à investiguer dans "
        "l'analyse opérationnelle."
    )
else:
    st.info("Aucun motif exploitable dans le périmètre analysé.")

# ============================================================
# VISUALISATION
# ============================================================

st.markdown("#### Visualisation des motifs")
c1, c2 = st.columns([1.1, 1], gap="large")

# ------------------------------------------------------------
# RÉPARTITION
# ------------------------------------------------------------
with c1:
    fig_repartition = chart_motifs_repartition(df)
    if fig_repartition is not None:
        st.plotly_chart(
            fig_repartition,
            use_container_width=True,
            config={"displayModeBar": False}
        )
    else:
        st.info("Répartition des motifs indisponible.")

# ------------------------------------------------------------
# ÉVOLUTION
# ------------------------------------------------------------
with c2:
    fig_evolution = chart_motifs_evolution(df)
    if fig_evolution is not None:
        st.plotly_chart(
            fig_evolution,
            use_container_width=True,
            config={"displayModeBar": False}
        )
    else:
        st.info("Évolution des motifs indisponible.")

# ============================================================
# ANALYSE TERRAIN
# ============================================================

section(
    "Analyse terrain",
    "Sélectionner un motif pour examiner les commentaires "
    "qui le composent et identifier le contexte opérationnel."
)

# ============================================================
# SÉLECTION DU MOTIF
# ============================================================

motifs_disponibles = sorted(df["motif"].dropna().unique())

if motifs_disponibles:
    motif = st.selectbox("Motif à examiner", motifs_disponibles)
    df_motif = df[df["motif"] == motif].copy()

    # --------------------------------------------------------
    # MINI KPI DU MOTIF SÉLECTIONNÉ
    # --------------------------------------------------------
    nb_motif = len(df_motif)
    part_motif = (nb_motif / len(df) * 100) if len(df) > 0 else 0

    mc1, mc2 = st.columns(2)

    with mc1:
        kpi_card(
            "Annulations du motif",
            f"{nb_motif:,}".replace(",", " "),
            "Commentaires classifiés"
        )

    with mc2:
        kpi_card(
            "Part des annulations",
            f"{part_motif:.1f} %",
            "Dans le périmètre analysé"
        )

    # --------------------------------------------------------
    # COMMENTAIRES (COMPLÉTÉ)
    # --------------------------------------------------------
    colonnes_exemple = [
        c for c in ["agent", "date_rdv", "commentaire"]
        if c in df_motif.columns  # <-- CORRIGÉ : Syntaxe finalisée
    ]

    st.markdown("#### Extraits des commentaires")
    st.dataframe(
        df_motif[colonnes_exemple],
        use_container_width=True,
        hide_index=True
    )

