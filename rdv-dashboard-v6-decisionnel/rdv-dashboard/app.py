import streamlit as st
from pathlib import Path

st.set_page_config(
    page_title="NEXTHORIZON · RDV Intelligence",
    page_icon="🔷",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Logo EN HAUT de la sidebar (au-dessus de la navigation Streamlit)
LOGO = Path("assets/nexthorizon_logo.png")
if LOGO.exists():
    try:
        st.logo(str(LOGO), size="large")
    except TypeError:
        try:
            st.logo(str(LOGO))
        except Exception:
            pass

pages = [
    st.Page("pages/01_vue_ensemble.py", title="Vue d'ensemble", icon="🔷", default=True),
    st.Page("pages/02_performance_agents.py", title="Performance agents", icon="🔹"),
    st.Page("pages/03_analyse_rdv.py", title="Analyse des RDV", icon="🔹"),
    st.Page("pages/04_annulations.py", title="Annulations & NLP", icon="🔹"),
    st.Page("pages/05_qualite_donnees.py", title="Qualité des données", icon="🔹"),
]

pg = st.navigation(pages)
pg.run()
