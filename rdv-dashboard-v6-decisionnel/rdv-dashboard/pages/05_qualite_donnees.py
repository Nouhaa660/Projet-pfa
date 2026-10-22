import pandas as pd
import streamlit as st

from utils.supabase import get_rendez_vous
from utils.data_quality import (
    resume_qualite,
    completude_par_colonne,
    colonnes_sous_seuil,
    completude_colonnes_critiques,
    derniere_donnee_connue,
    score_qualite,
)
from utils.charts import chart_completude
from utils.ui import bootstrap_page, page_header, section, kpi_card, insight

bootstrap_page()

page_header(
    "05 · Data quality",
    "Qualité des données",
    "Contrôler la fiabilité du référentiel avant toute décision.",
)

with st.spinner("Analyse de la table rendez_vous..."):
    try:
        df = get_rendez_vous()
    except Exception as e:
        st.error(f"Impossible de charger les données : {e}")
        st.stop()

if df is None or df.empty:
    st.info("La table rendez_vous est vide ou indisponible.")
    st.stop()

# --- Calculs ---
r = resume_qualite(df)
sq = score_qualite(df)
completude = completude_par_colonne(df)
critiques = completude_colonnes_critiques(df)
faibles = colonnes_sous_seuil(completude, seuil=85)
date_fraicheur, col_fraicheur = derniere_donnee_connue(df)

nb_lignes = r["nb_lignes"]
nb_doublons = r["nb_doublons"]
taux_nulls = r["taux_nulls_global"]
nb_colonnes = r["nb_colonnes"]

# --- KPI ---
k1, k2, k3, k4, k5 = st.columns(5)
with k1:
    kpi_card("Score qualité", f"{sq['score']:.0f}/100", sq["niveau"])
with k2:
    kpi_card("Lignes", f"{nb_lignes:,}".replace(",", " "), "Volume chargé")
with k3:
    kpi_card("Doublons", f"{nb_doublons:,}".replace(",", " "), "Lignes dupliquées")
with k4:
    kpi_card("Nulls globaux", f"{taux_nulls:.1f} %", "Toutes colonnes")
with k5:
    kpi_card("Colonnes", str(nb_colonnes), "Schéma observé")

# --- Feu décisionnel + fraîcheur ---
section("État décisionnel", "Lecture rapide avant d'interpréter les autres pages.")

c_left, c_right = st.columns([1.2, 1], gap="medium")

with c_left:
    if sq["niveau"] == "Bon":
        st.markdown(
            f"""<div class="success-card">
            <strong>Qualité compatible avec le pilotage</strong><br>
            Score {sq['score']:.0f}/100 — nulls {taux_nulls:.1f} %,
            {nb_doublons} doublon(s).
            </div>""",
            unsafe_allow_html=True,
        )
    elif sq["niveau"] == "Acceptable":
        st.markdown(
            f"""<div class="alert-card">
            <strong>Qualité acceptable avec réserves</strong><br>
            Score {sq['score']:.0f}/100 — vérifier les colonnes critiques
            avant toute décision sensible.
            </div>""",
            unsafe_allow_html=True,
        )
    else:
        st.markdown(
            f"""<div class="alert-card">
            <strong>Prudence avant décision</strong><br>
            Score {sq['score']:.0f}/100 — anomalies de qualité détectées
            (nulls / doublons / colonnes critiques).
            </div>""",
            unsafe_allow_html=True,
        )

with c_right:
    if date_fraicheur is not None:
        try:
            date_fmt = date_fraicheur.strftime("%d/%m/%Y")
        except Exception:
            date_fmt = str(date_fraicheur)
        st.markdown(
            f"""<div class="card">
            <div class="kpi-label">Fraîcheur (proxy)</div>
            <div class="kpi-value" style="font-size:1.35rem;">{date_fmt}</div>
            <div class="kpi-hint">Colonne : {col_fraicheur} — pas un timestamp de sync</div>
            </div>""",
            unsafe_allow_html=True,
        )
    else:
        st.markdown(
            """<div class="alert-card">
            <strong>Fraîcheur non disponible</strong><br>
            Aucune date exploitable (date_appel / date_rdv).
            </div>""",
            unsafe_allow_html=True,
        )

# --- Colonnes critiques ---
section(
    "Colonnes critiques",
    "Champs indispensables au pilotage (agents, statuts, dates, motifs).",
)

if not critiques.empty:
    st.dataframe(
        critiques,
        use_container_width=True,
        hide_index=True,
        column_config={
            "Complétude (%)": st.column_config.ProgressColumn(
                "Complétude (%)",
                min_value=0,
                max_value=100,
                format="%.1f %%",
            ),
            "Manquants": st.column_config.NumberColumn("Manquants"),
            "Statut": st.column_config.TextColumn("Statut"),
        },
    )
    n_bad = int((critiques["Statut"] != "OK").sum())
    if n_bad:
        insight(
            f"{n_bad} colonne(s) critique(s) sous le seuil de 90 % de complétude. "
            "Prioriser la saisie ou le pipeline d'alimentation sur ces champs."
        )
    else:
        insight("Toutes les colonnes critiques dépassent 90 % de complétude.")
else:
    st.info("Aucune colonne critique trouvée dans le schéma actuel.")

# --- Complétude globale ---
section(
    "Complétude par colonne",
    "Vue d'ensemble du schéma — focus sur les colonnes les moins renseignées.",
)

if not completude.empty:
    # Afficher les 20 colonnes les moins renseignées
    worst = completude.head(20)
    st.plotly_chart(
        chart_completude(worst),
        use_container_width=True,
        config={"displayModeBar": False},
    )

    if not faibles.empty:
        st.markdown(f"**{len(faibles)} colonne(s) sous 85 % de complétude**")
        st.dataframe(
            faibles,
            use_container_width=True,
            hide_index=True,
            height=min(280, 40 + len(faibles) * 28),
        )
    else:
        st.markdown(
            """<div class="success-card">Aucune colonne sous le seuil de 85 %.</div>""",
            unsafe_allow_html=True,
        )
else:
    st.info("Complétude non calculable.")

# --- Détail schéma ---
with st.expander("Schéma complet (toutes les colonnes)", expanded=False):
    st.dataframe(
        completude.sort_values("Complétude (%)", ascending=False),
        use_container_width=True,
        hide_index=True,
        height=360,
    )

st.caption(
    "Le score qualité est indicatif (nulls, doublons, colonnes critiques). "
    "Il ne remplace pas un SLA de synchronisation dédié."
)
