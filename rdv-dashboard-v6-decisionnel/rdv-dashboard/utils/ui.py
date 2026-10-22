"""
Design system NEXTHORIZON — dashboard RDV Intelligence.
Palette bleue compacte, indicative, orientée décision.
"""

from __future__ import annotations

from pathlib import Path

import streamlit as st

# --- Brand colors (logo NEXTHORIZON) ---
BLUE = "#2563EB"
BLUE_DARK = "#1D4ED8"
BLUE_SOFT = "#DBEAFE"
BLUE_MID = "#60A5FA"
NAVY = "#0F172A"
INK = "#1E293B"
MUTED = "#64748B"
BORDER = "#E2E8F0"
BG = "#F1F5F9"
WHITE = "#FFFFFF"
GREEN = "#059669"
AMBER = "#D97706"
RED = "#DC2626"

LOGO_PATH = Path(__file__).resolve().parent.parent / "assets" / "nexthorizon_logo.png"


def inject_global_style():
    """Thème global clair, compact, professionnel."""
    st.markdown(
        f"""
        <style>
        @import url('https://fonts.googleapis.com/css2?family=IBM+Plex+Sans:wght@400;500;600;700&display=swap');

        html, body, [class*="css"] {{
            font-family: 'IBM Plex Sans', 'Segoe UI', sans-serif;
        }}

        :root {{
            --nh-blue: {BLUE};
            --nh-navy: {NAVY};
            --nh-ink: {INK};
            --nh-muted: {MUTED};
            --nh-border: {BORDER};
            --nh-bg: {BG};
        }}

        #MainMenu, footer {{ visibility: hidden; }}

        .stApp {{ background: var(--nh-bg); }}
        [data-testid="stHeader"] {{
            background: rgba(241,245,249,.92);
            border-bottom: 1px solid {BORDER};
        }}

        [data-testid="stSidebar"] {{
            background: {WHITE} !important;
            border-right: 1px solid {BORDER};
        }}
        [data-testid="stSidebar"] [data-testid="stMarkdownContainer"] p {{
            color: {MUTED};
            font-size: .84rem;
        }}

        .block-container {{
            max-width: 1360px;
            padding-top: 1.1rem;
            padding-bottom: 2rem;
            padding-left: 1.6rem;
            padding-right: 1.6rem;
        }}

        h1 {{
            color: var(--nh-navy) !important;
            font-size: 1.55rem !important;
            font-weight: 700 !important;
            letter-spacing: -.02em;
            margin-bottom: .2rem !important;
        }}
        h2, h3 {{
            color: var(--nh-ink) !important;
            font-weight: 650 !important;
            letter-spacing: -.01em;
        }}

        .nh-brand-bar {{
            display: flex;
            align-items: center;
            gap: 12px;
            margin-bottom: 10px;
        }}
        .nh-brand-sub {{
            color: {MUTED};
            font-size: .72rem;
            font-weight: 600;
            letter-spacing: .08em;
            text-transform: uppercase;
        }}

        .page-kicker {{
            color: {BLUE};
            font-size: .72rem;
            font-weight: 700;
            letter-spacing: .11em;
            text-transform: uppercase;
            margin-bottom: .18rem;
        }}
        .page-subtitle {{
            color: {MUTED};
            font-size: .88rem;
            margin-bottom: .85rem;
            line-height: 1.35;
        }}
        .section-title {{
            color: var(--nh-ink);
            font-size: .95rem;
            font-weight: 700;
            margin: 1rem 0 .15rem;
        }}
        .section-note {{
            color: {MUTED};
            font-size: .8rem;
            margin-bottom: .55rem;
        }}

        .card {{
            background: {WHITE};
            border: 1px solid {BORDER};
            border-radius: 12px;
            padding: 12px 14px;
            box-shadow: 0 1px 2px rgba(15,23,42,.03);
        }}
        .kpi-card {{ min-height: 88px; border-top: 3px solid {BLUE}; }}
        .kpi-label {{
            color: {MUTED};
            font-size: .68rem;
            font-weight: 700;
            text-transform: uppercase;
            letter-spacing: .05em;
        }}
        .kpi-value {{
            color: {NAVY};
            font-size: 1.45rem;
            line-height: 1.1;
            font-weight: 730;
            margin-top: 6px;
        }}
        .kpi-hint {{ color: #94A3B8; font-size: .72rem; margin-top: 4px; }}

        .insight {{
            margin-top: 8px;
            padding: 9px 11px;
            border-left: 3px solid {BLUE};
            background: {BLUE_SOFT};
            color: {INK};
            border-radius: 0 8px 8px 0;
            font-size: .82rem;
        }}

        div[data-testid="stMetric"] {{
            background: {WHITE};
            border: 1px solid {BORDER};
            border-radius: 12px;
            border-top: 3px solid {BLUE};
            padding: 10px 12px;
            box-shadow: 0 1px 2px rgba(15,23,42,.03);
        }}
        div[data-testid="stMetricLabel"] {{ color: {MUTED}; font-size: .72rem; }}
        div[data-testid="stMetricValue"] {{ color: {NAVY}; font-size: 1.35rem; }}
        div[data-testid="stMetricDelta"] {{ font-size: .75rem; }}

        div[data-testid="stPlotlyChart"] {{
            background: {WHITE};
            border: 1px solid {BORDER};
            border-radius: 8px;
            padding: 2px 4px 0;
            box-shadow: none;
        }}
        div[data-testid="stDataFrame"] {{
            border: 1px solid {BORDER};
            border-radius: 10px;
            overflow: hidden;
            background: {WHITE};
        }}
        div[data-testid="stExpander"] {{
            border: 1px solid {BORDER};
            border-radius: 10px;
            background: {WHITE};
        }}

        .filter-box {{
            background: {WHITE};
            border: 1px solid {BORDER};
            border-radius: 10px;
            padding: 8px 10px 2px;
            margin-bottom: 10px;
        }}

        .alert-card {{
            background: #FFFBEB;
            border: 1px solid #FDE68A;
            border-left: 3px solid {AMBER};
            border-radius: 8px;
            padding: 9px 11px;
            color: #92400E;
            margin-bottom: 6px;
            font-size: .84rem;
        }}
        .success-card {{
            background: #ECFDF5;
            border: 1px solid #A7F3D0;
            border-left: 3px solid {GREEN};
            border-radius: 8px;
            padding: 9px 11px;
            color: #065F46;
            font-size: .84rem;
        }}

        /* Agents à investiguer — blocs bleus concis */
        .inspect-card {{
            background: #FFFFFF;
            border: 1px solid {BORDER};
            border-left: 3px solid {BLUE};
            border-radius: 6px;
            padding: 8px 12px;
            margin-bottom: 6px;
            color: {INK};
            font-size: .82rem;
            line-height: 1.35;
            display: flex;
            align-items: baseline;
            justify-content: space-between;
            gap: 12px;
        }}
        .inspect-card .name {{
            font-weight: 650;
            color: {NAVY};
        }}
        .inspect-card .meta {{
            color: {MUTED};
            font-size: .78rem;
            white-space: nowrap;
        }}

        hr {{ border-color: {BORDER} !important; margin: .7rem 0 !important; }}

        /* Tags multiselect : bleu NEXTHORIZON (plus de rouge) */
        span[data-baseweb="tag"],
        [data-baseweb="tag"] {{
            background-color: {BLUE} !important;
            color: #FFFFFF !important;
            border-radius: 6px !important;
            border: none !important;
        }}
        span[data-baseweb="tag"] span,
        [data-baseweb="tag"] span {{
            color: #FFFFFF !important;
        }}
        span[data-baseweb="tag"] svg,
        [data-baseweb="tag"] svg {{
            fill: #FFFFFF !important;
        }}

        /* Inputs / select focus bleu */
        div[data-baseweb="select"] > div {{
            border-color: {BORDER} !important;
            background: #FFFFFF !important;
        }}
        div[data-baseweb="select"] > div:hover {{
            border-color: {BLUE_MID} !important;
        }}

        /* ---------- Sidebar NEXTHORIZON ---------- */
        [data-testid="stSidebar"] {{
            background: #FFFFFF !important;
            border-right: 1px solid {BORDER};
            min-width: 272px !important;
        }}
        [data-testid="stSidebar"] > div:first-child {{
            padding-top: 0.6rem;
        }}

        /* Logo en haut — plus grand */
        [data-testid="stSidebarHeader"],
        [data-testid="stLogo"] {{
            padding: 10px 14px 6px 14px !important;
        }}
        [data-testid="stLogo"] {{
            height: auto !important;
        }}
        [data-testid="stLogo"] img,
        [data-testid="stSidebar"] [data-testid="stLogo"] img {{
            height: 48px !important;
            max-height: 48px !important;
            width: auto !important;
            max-width: 210px !important;
            object-fit: contain !important;
        }}

        /* Masquer le gros logo collé en bas (ancien render) */
        [data-testid="stSidebarUserContent"] img {{
            display: none !important;
        }}

        /* Navigation */
        [data-testid="stSidebarNav"] {{
            padding: 4px 10px 8px 10px !important;
        }}
        [data-testid="stSidebarNav"] ul {{
            gap: 2px;
        }}
        [data-testid="stSidebarNav"] a {{
            border-radius: 8px !important;
            padding: 0.48rem 0.7rem !important;
            font-size: 0.9rem !important;
            color: {INK} !important;
            font-weight: 500 !important;
            border-left: 3px solid transparent !important;
            margin-bottom: 2px !important;
        }}
        [data-testid="stSidebarNav"] a:hover {{
            background: #F1F5F9 !important;
            color: {BLUE_DARK} !important;
        }}
        [data-testid="stSidebarNav"] a[aria-current="page"] {{
            background: {BLUE_SOFT} !important;
            color: {BLUE_DARK} !important;
            font-weight: 650 !important;
            border-left: 3px solid {BLUE} !important;
        }}

        /* Pied de sidebar discret */
        .nh-side-footer {{
            margin-top: 18px;
            padding: 12px 4px 4px 4px;
            border-top: 1px solid {BORDER};
        }}
        .nh-side-footer .label {{
            color: {BLUE};
            font-size: 0.68rem;
            font-weight: 700;
            letter-spacing: 0.08em;
            text-transform: uppercase;
        }}
        .nh-side-footer .hint {{
            color: {MUTED};
            font-size: 0.75rem;
            margin-top: 4px;
            line-height: 1.35;
        }}
        </style>
        """,
        unsafe_allow_html=True,
    )


def render_brand():
    """Pied de sidebar discret — le logo est déjà en haut via st.logo()."""
    with st.sidebar:
        st.markdown(
            """
            <div class="nh-side-footer">
                <div class="label">RDV Intelligence</div>
                <div class="hint">Pilotage &amp; aide à la décision</div>
            </div>
            """,
            unsafe_allow_html=True,
        )


def bootstrap_page():
    """À appeler en tête de chaque page."""
    inject_global_style()
    render_brand()


def page_header(kicker: str, title: str, subtitle: str = ""):
    st.markdown(f'<div class="page-kicker">{kicker}</div>', unsafe_allow_html=True)
    st.title(title)
    if subtitle:
        st.markdown(f'<div class="page-subtitle">{subtitle}</div>', unsafe_allow_html=True)


def section(title: str, note: str = ""):
    st.markdown(f'<div class="section-title">{title}</div>', unsafe_allow_html=True)
    if note:
        st.markdown(f'<div class="section-note">{note}</div>', unsafe_allow_html=True)


def kpi_card(label: str, value: str, hint: str = ""):
    hint_html = f'<div class="kpi-hint">{hint}</div>' if hint else ""
    st.markdown(
        f'<div class="card kpi-card"><div class="kpi-label">{label}</div>'
        f'<div class="kpi-value">{value}</div>{hint_html}</div>',
        unsafe_allow_html=True,
    )


def insight(text: str):
    st.markdown(
        f'<div class="insight"><strong>Lecture :</strong> {text}</div>',
        unsafe_allow_html=True,
    )


def filter_box_start():
    st.markdown('<div class="filter-box">', unsafe_allow_html=True)


def filter_box_end():
    st.markdown("</div>", unsafe_allow_html=True)
