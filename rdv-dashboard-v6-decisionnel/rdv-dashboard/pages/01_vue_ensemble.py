import streamlit as st
import pandas as pd

from utils.supabase import get_rendez_vous
from utils.ui import bootstrap_page, page_header, section, kpi_card, insight
from utils.charts import (
    chart_evolution_mensuelle,
    chart_repartition_statuts,
    chart_taux_annulation_agents,
)
from utils.preprocessing import filtrer_agents_valides

bootstrap_page()

page_header(
    "01 · Pilotage",
    "Vue d'ensemble",
    "Volumes, confirmations, annulations et signaux opérationnels.",
)

with st.spinner("Chargement des données..."):
    try:
        df = get_rendez_vous(columns=[
            "agent", "status", "date_rdv", "date_appel", "type_fiche"
        ])
    except Exception as e:
        st.error(f"Erreur : {e}")
        st.stop()

if df.empty:
    st.warning("Aucune donnée disponible")
    st.stop()

df["status"] = df["status"].astype(str).str.strip()
df["date_rdv"] = pd.to_datetime(df["date_rdv"], errors="coerce")
df = df[df["status"].isin(["Confirmé", "Annulé"])].copy()
df = filtrer_agents_valides(df, "agent")

if df.empty:
    st.warning("Aucun RDV avec statut Confirmé ou Annulé")
    st.stop()

total = len(df)
confirmes = int((df["status"] == "Confirmé").sum())
annules = int((df["status"] == "Annulé").sum())
taux_confirmation = (confirmes / total * 100) if total else 0
taux_annulation = (annules / total * 100) if total else 0
nb_agents = df["agent"].nunique()

k1, k2, k3, k4, k5 = st.columns(5)
with k1:
    kpi_card("RDV analysés", f"{total:,}".replace(",", " "))
with k2:
    kpi_card("Confirmés", f"{confirmes:,}".replace(",", " "), f"{taux_confirmation:.1f}%")
with k3:
    kpi_card("Annulés", f"{annules:,}".replace(",", " "), f"{taux_annulation:.1f}%")
with k4:
    kpi_card("Taux annulation", f"{taux_annulation:.1f} %")
with k5:
    kpi_card("Agents", str(nb_agents))

section("Activité", "Évolution mensuelle et structure des statuts.")

c1, c2 = st.columns([1.55, 1], gap="medium")
with c1:
    st.plotly_chart(
        chart_evolution_mensuelle(df),
        use_container_width=True,
        config={"displayModeBar": False},
    )
with c2:
    st.plotly_chart(
        chart_repartition_statuts(df),
        use_container_width=True,
        config={"displayModeBar": False},
    )

insight(
    f"Sur le périmètre, le taux d'annulation s'établit à {taux_annulation:.1f}% "
    f"({annules} / {total}). Prioriser l'analyse des motifs et des agents hors norme."
)

section("Signaux agents", "Top agents par taux d'annulation (indicatif, volume ≥ 5).")

agent_df = (
    df.groupby("agent")
    .agg(
        rdv=("status", "size"),
        annules=("status", lambda x: (x == "Annulé").sum()),
        confirmes=("status", lambda x: (x == "Confirmé").sum()),
    )
    .reset_index()
)
agent_df["taux_annulation"] = agent_df["annules"] / agent_df["rdv"] * 100
agent_df = agent_df[agent_df["rdv"] >= 5].sort_values("taux_annulation", ascending=False)

if not agent_df.empty:
    st.plotly_chart(
        chart_taux_annulation_agents(agent_df.head(12)),
        use_container_width=True,
        config={"displayModeBar": False},
    )
else:
    st.info("Pas assez de volume agent pour un classement.")

section("Points d'attention")
global_rate = taux_annulation
agent_alerts = agent_df[
    (agent_df["rdv"] >= 10) & (agent_df["taux_annulation"] >= global_rate + 10)
]

if not agent_alerts.empty:
    for _, row in agent_alerts.head(5).iterrows():
        st.markdown(
            f"""<div class="inspect-card">
            <span class="name">{row['agent']}</span>
            <span class="meta">{row['taux_annulation']:.1f}% · {int(row['rdv'])} RDV</span>
            </div>""",
            unsafe_allow_html=True,
        )
else:
    st.markdown(
        """<div class="success-card">Aucun signal majeur sur ce périmètre.</div>""",
        unsafe_allow_html=True,
    )
