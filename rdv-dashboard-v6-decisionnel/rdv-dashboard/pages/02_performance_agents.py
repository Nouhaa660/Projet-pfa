import pandas as pd
import streamlit as st

from utils.supabase import get_rendez_vous
from utils.preprocessing import filtrer_agents_valides
from utils.ui import bootstrap_page, page_header, section, kpi_card, insight
from utils.charts import chart_performance_agents

bootstrap_page()

page_header(
    "02 · Opérations",
    "Performance agents",
    "Comparer volumes, taux d'annulation et écarts vs benchmark (≥10 RDV).",
)

with st.spinner("Chargement..."):
    try:
        df = get_rendez_vous(columns=["agent", "status", "type_fiche", "date_rdv"])
    except Exception as e:
        st.error(f"Erreur : {e}")
        st.stop()

if df.empty:
    st.info("Aucune donnée disponible")
    st.stop()

df["date_rdv"] = pd.to_datetime(df["date_rdv"], errors="coerce")
df["status"] = df["status"].astype(str).str.strip()

# Retirer FEUILLE 16, tirets, vides, artefacts Excel, etc.
df = filtrer_agents_valides(df, "agent")
if df.empty:
    st.warning("Aucun agent exploitable après nettoyage des noms.")
    st.stop()

f1, f2, f3 = st.columns(3)
selected_agents = sorted(df["agent"].dropna().astype(str).unique().tolist())
with f1:
    agent_filter = st.multiselect(
        "Agents",
        selected_agents,
        default=[],
        placeholder="Tous les agents",
        key="agent_select",
    )
    if agent_filter:
        df = df[df["agent"].isin(agent_filter)]

selected_types = (
    sorted(df["type_fiche"].dropna().astype(str).unique().tolist())
    if "type_fiche" in df.columns else []
)
with f2:
    if selected_types:
        type_filter = st.multiselect(
            "Type de fiche",
            selected_types,
            default=[],
            placeholder="Tous les types",
            key="type_select",
        )
        if type_filter:
            df = df[df["type_fiche"].isin(type_filter)]

with f3:
    periode = st.selectbox(
        "Période", ["Tout l'historique", "30 derniers jours", "90 derniers jours"]
    )
    if periode == "30 derniers jours":
        df = df[df.date_rdv >= pd.Timestamp.now() - pd.Timedelta(days=30)]
    elif periode == "90 derniers jours":
        df = df[df.date_rdv >= pd.Timestamp.now() - pd.Timedelta(days=90)]

if df.empty:
    st.info("Aucune donnée pour ces filtres")
    st.stop()

global_rate = (df["status"] == "Annulé").mean() * 100

diag = (
    df.groupby("agent")
    .agg(
        RDV=("status", "size"),
        Confirmés=("status", lambda x: (x == "Confirmé").sum()),
        Annulés=("status", lambda x: (x == "Annulé").sum()),
    )
    .reset_index()
)
diag["Taux confirmation"] = diag["Confirmés"] / diag["RDV"] * 100
diag["Taux annulation"] = diag["Annulés"] / diag["RDV"] * 100
diag["Écart vs global"] = diag["Taux annulation"] - global_rate


def signal_func(row):
    if row["RDV"] < 10:
        return "Volume insuffisant"
    if row["Écart vs global"] >= 10:
        return "À investiguer"
    if row["Écart vs global"] <= -10:
        return "Favorable"
    return "Dans la norme"


diag["Signal"] = diag.apply(signal_func, axis=1)

# Analyse décisionnelle : agents avec volume minimum
diag_signifiant = diag[diag["RDV"] >= 10].copy()

a_investir = int((diag["Signal"] == "À investiguer").sum())
favorables = int((diag["Signal"] == "Favorable").sum())

c1, c2, c3, c4 = st.columns(4)
with c1:
    kpi_card("RDV analysés", f"{len(df):,}".replace(",", " "))
with c2:
    kpi_card("Taux global", f"{global_rate:.1f} %")
with c3:
    kpi_card("À investiguer", str(a_investir))
with c4:
    kpi_card("Favorables", str(favorables))

section(
    "Classement par taux d'annulation",
    "Agents avec ≥10 RDV. Rouge = au-dessus du taux global (+10 pts), "
    "vert = sous le global (−10 pts), bleu = dans la norme.",
)

fig = chart_performance_agents(diag_signifiant, global_rate, min_rdv=10, max_rows=15)
if fig is not None:
    st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})
    top = diag_signifiant.sort_values("Taux annulation", ascending=False).iloc[0]
    insight(
        f"Le taux global d'annulation est de {global_rate:.1f}%. "
        f"Le plus élevé parmi les volumes significatifs : "
        f"{top['agent']} à {top['Taux annulation']:.1f}% "
        f"({int(top['RDV'])} RDV)."
    )
else:
    st.info("Pas assez d'agents avec ≥10 RDV pour un classement significatif.")

section(
    "Tableau de décision",
    "Signal visible si ≥10 RDV et écart ≥ ±10 pts vs taux global.",
)

display_diag = (
    diag[["agent", "RDV", "Confirmés", "Annulés", "Taux annulation", "Écart vs global", "Signal"]]
    .sort_values(["Signal", "Taux annulation"], ascending=[True, False])
)

# Ordre métier des signaux
signal_order = {
    "À investiguer": 0,
    "Dans la norme": 1,
    "Favorable": 2,
    "Volume insuffisant": 3,
}
display_diag = display_diag.assign(
    _ord=display_diag["Signal"].map(signal_order)
).sort_values(["_ord", "Taux annulation"], ascending=[True, False]).drop(columns="_ord")

st.dataframe(
    display_diag.style.format({
        "Taux annulation": "{:.1f}%",
        "Écart vs global": "{:+.1f}",
    }),
    use_container_width=True,
    hide_index=True,
    height=320,
)

section("Agents à investiguer")
alerts = diag[diag["Signal"] == "À investiguer"].sort_values(
    "Taux annulation", ascending=False
)
if not alerts.empty:
    for _, row in alerts.head(5).iterrows():
        st.markdown(
            f"""<div class="inspect-card">
            <span class="name">{row['agent']}</span>
            <span class="meta">{row['Taux annulation']:.1f}% · {row['Écart vs global']:+.1f} pts · {int(row['RDV'])} RDV</span>
            </div>""",
            unsafe_allow_html=True,
        )
else:
    st.markdown(
        """<div class="success-card">Aucun agent au-dessus du seuil sur ce périmètre.</div>""",
        unsafe_allow_html=True,
    )

st.caption(
    "Noms non significatifs (ex. FEUILLE 16, tirets) exclus. "
    "Les petits volumes peuvent créer des écarts non significatifs."
)
